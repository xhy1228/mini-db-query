# -*- coding: utf-8 -*-
"""
Setup API - Database Configuration

Deploy first, configure database later
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import json
import logging
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)
router = APIRouter(tags=["setup"])


class DatabaseConfig(BaseModel):
    """数据库配置请求"""
    host: str
    port: int = 3306
    user: str
    password: str
    db_name: str


class DatabaseConfigResponse(BaseModel):
    """数据库配置响应"""
    success: bool
    message: str
    connection_info: Optional[dict] = None


class TestConnectionResponse(BaseModel):
    """测试连接响应"""
    success: bool
    message: str
    version: Optional[str] = None


def build_database_url(config_dict: dict) -> str:
    """构建数据库URL，对密码进行URL编码"""
    password = config_dict.get('password', '')
    # 对密码进行URL编码，处理特殊字符
    encoded_password = quote_plus(password)
    return f"mysql+pymysql://{config_dict['user']}:{encoded_password}@{config_dict['host']}:{config_dict['port']}/{config_dict['db_name']}?charset=utf8mb4"


def get_encrypted_config() -> Optional[dict]:
    """获取加密存储的配置"""
    env_file = os.path.join(os.path.dirname(__file__), '..', '.env')
    if not os.path.exists(env_file):
        return None
    
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('ENCRYPTED_DB_CONFIG='):
                try:
                    # 读取加密配置
                    encrypted_str = line.split('=', 1)[1].strip()
                    if not encrypted_str:
                        return None
                    
                    from core.security import decrypt_password
                    # 解密
                    decrypted = decrypt_password(encrypted_str)
                    return json.loads(decrypted)
                except Exception as e:
                    logger.error(f"解密配置失败: {e}")
                    return None
    return None


def save_encrypted_config(config_dict: dict) -> bool:
    """保存加密配置"""
    try:
        from core.security import encrypt_password
        
        env_file = os.path.join(os.path.dirname(__file__), '..', '.env')
        
        # 读取现有配置
        existing_lines = []
        if os.path.exists(env_file):
            with open(env_file, 'r', encoding='utf-8') as f:
                existing_lines = f.readlines()
        
        # 加密配置
        config_json = json.dumps(config_dict, ensure_ascii=False)
        encrypted = encrypt_password(config_json)
        
        # 更新配置
        new_lines = []
        config_saved = False
        
        for line in existing_lines:
            if line.startswith('ENCRYPTED_DB_CONFIG='):
                new_lines.append(f'ENCRYPTED_DB_CONFIG={encrypted}\n')
                config_saved = True
            elif line.startswith('DATABASE_URL='):
                # 保留旧的 DATABASE_URL 但不推荐使用
                new_lines.append(f'# {line}')
            else:
                new_lines.append(line)
        
        if not config_saved:
            new_lines.append(f'ENCRYPTED_DB_CONFIG={encrypted}\n')
        
        # 写入文件
        with open(env_file, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        return True
    except Exception as e:
        logger.error(f"保存加密配置失败: {e}")
        return False


@router.get("/setup/status")
async def get_setup_status():
    """获取配置状态"""
    # 尝试读取加密配置
    config_dict = get_encrypted_config()
    
    if config_dict:
        try:
            # 构建连接URL测试
            database_url = build_database_url(config_dict)
            
            from sqlalchemy import create_engine, text
            engine = create_engine(database_url)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT VERSION()"))
                version = result.scalar()
                
                # 检查表是否存在
                result = conn.execute(text("SHOW TABLES LIKE 'users'"))
                tables_initialized = result.fetchone() is not None
                
                # 返回配置信息（隐藏密码）
                return {
                    "configured": True,
                    "connected": True,
                    "tables_initialized": tables_initialized,
                    "mysql_version": version,
                    "mysql_info": {
                        "host": config_dict.get('host'),
                        "port": config_dict.get('port'),
                        "user": config_dict.get('user'),
                        "db_name": config_dict.get('db_name')
                    }
                }
        except Exception as e:
            return {
                "configured": True,
                "connected": False,
                "tables_initialized": False,
                "error": str(e),
                "mysql_info": {
                    "host": config_dict.get('host'),
                    "port": config_dict.get('port'),
                    "user": config_dict.get('user'),
                    "db_name": config_dict.get('db_name')
                }
            }
    
    return {
        "configured": False,
        "connected": False,
        "tables_initialized": False
    }


@router.post("/setup/test", response_model=TestConnectionResponse)
async def test_database_connection(config: DatabaseConfig):
    """测试数据库连接"""
    try:
        from sqlalchemy import create_engine, text
        
        # 使用URL编码构建连接字符串
        config_dict = config.model_dump()
        database_url = build_database_url(config_dict)
        
        engine = create_engine(database_url, connect_args={"connect_timeout": 5})
        with engine.connect() as conn:
            result = conn.execute(text("SELECT VERSION()"))
            version = result.scalar()
            
            return TestConnectionResponse(
                success=True,
                message="Connection successful",
                version=version
            )
            
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return TestConnectionResponse(
            success=False,
            message=f"Connection failed: {str(e)}"
        )


@router.post("/setup/save", response_model=DatabaseConfigResponse)
async def save_database_config(config: DatabaseConfig):
    """保存数据库配置（加密存储）"""
    try:
        # 测试连接
        config_dict = config.model_dump()
        database_url = build_database_url(config_dict)
        
        from sqlalchemy import create_engine, text
        engine = create_engine(database_url, connect_args={"connect_timeout": 5})
        with engine.connect() as conn:
            result = conn.execute(text("SELECT VERSION()"))
            version = result.scalar()
        
        # 加密保存配置
        if not save_encrypted_config(config_dict):
            raise Exception("Failed to save encrypted config")
        
        # 更新当前配置
        from core.config import Settings
        global settings
        settings = Settings()
        
        return DatabaseConfigResponse(
            success=True,
            message="Configuration saved successfully (encrypted)",
            connection_info={
                "host": config.host,
                "port": config.port,
                "db_name": config.db_name,
                "mysql_version": version
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to save database config: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to save config: {str(e)}")


@router.post("/setup/check-tables")
async def check_tables():
    """检查数据库表是否已初始化"""
    config_dict = get_encrypted_config()
    
    if not config_dict:
        return {"initialized": False, "error": "Database not configured"}
    
    try:
        database_url = build_database_url(config_dict)
        from sqlalchemy import create_engine, text
        engine = create_engine(database_url)
        with engine.connect() as conn:
            # 检查关键表
            required_tables = ['users', 'schools', 'database_configs', 'query_templates']
            existing_tables = []
            
            for table in required_tables:
                result = conn.execute(text(f"SHOW TABLES LIKE '{table}'"))
                if result.fetchone():
                    existing_tables.append(table)
            
            return {
                "initialized": len(existing_tables) >= len(required_tables),
                "existing_tables": existing_tables,
                "required_tables": required_tables
            }
            
    except Exception as e:
        return {"initialized": False, "error": str(e)}

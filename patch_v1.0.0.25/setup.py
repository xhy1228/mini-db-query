# -*- coding: utf-8 -*-
"""
Setup API - Database Configuration

Deploy first, configure database later
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import re
import logging

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


@router.get("/setup/status")
async def get_setup_status():
    """获取配置状态"""
    from core.config import settings
    
    configured = bool(settings.DATABASE_URL and settings.DATABASE_URL.strip())
    
    if configured:
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(settings.DATABASE_URL)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT VERSION()"))
                version = result.scalar()
                
                # 检查表是否存在
                result = conn.execute(text("SHOW TABLES LIKE 'users'"))
                tables_initialized = result.fetchone() is not None
                
                return {
                    "configured": True,
                    "connected": True,
                    "tables_initialized": tables_initialized,
                    "mysql_version": version,
                    "mysql_info": settings.mysql_info
                }
        except Exception as e:
            return {
                "configured": True,
                "connected": False,
                "tables_initialized": False,
                "error": str(e),
                "mysql_info": settings.mysql_info
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
        
        database_url = f"mysql+pymysql://{config.user}:{config.password}@{config.host}:{config.port}/{config.db_name}?charset=utf8mb4"
        
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
    """保存数据库配置"""
    try:
        # 测试连接
        database_url = f"mysql+pymysql://{config.user}:{config.password}@{config.host}:{config.port}/{config.db_name}?charset=utf8mb4"
        
        from sqlalchemy import create_engine, text
        engine = create_engine(database_url, connect_args={"connect_timeout": 5})
        with engine.connect() as conn:
            result = conn.execute(text("SELECT VERSION()"))
            version = result.scalar()
        
        # 保存配置到 .env 文件
        env_file = os.path.join(os.path.dirname(__file__), '..', '.env')
        
        # 读取现有配置
        existing_lines = []
        if os.path.exists(env_file):
            with open(env_file, 'r', encoding='utf-8') as f:
                existing_lines = f.readlines()
        
        # 更新 DATABASE_URL
        new_lines = []
        database_url_set = False
        
        for line in existing_lines:
            if line.startswith('DATABASE_URL='):
                new_lines.append(f'DATABASE_URL={database_url}\n')
                database_url_set = True
            else:
                new_lines.append(line)
        
        if not database_url_set:
            new_lines.append(f'DATABASE_URL={database_url}\n')
        
        # 写入文件
        with open(env_file, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        # 更新当前配置
        from core.config import Settings
        global settings
        settings = Settings()
        
        return DatabaseConfigResponse(
            success=True,
            message="Configuration saved successfully",
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
    from core.config import settings
    
    if not settings.DATABASE_URL:
        return {"initialized": False, "error": "Database not configured"}
    
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(settings.DATABASE_URL)
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

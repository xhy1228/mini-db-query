# -*- coding: utf-8 -*-
"""
多源数据查询小程序版 - 数据库会话管理

Deploy first, configure database later
"""

import os
import sys
import logging
import json
from urllib.parse import quote_plus
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator, Optional

logger = logging.getLogger(__name__)

# 全局变量
engine = None
SessionLocal = None
DATABASE_URL = None
MYSQL_INFO = {}


def _get_encrypted_config() -> Optional[dict]:
    """获取加密存储的配置"""
    env_file = os.path.join(os.path.dirname(__file__), '..', '.env')
    if not os.path.exists(env_file):
        return None
    
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('ENCRYPTED_DB_CONFIG='):
                    encrypted_str = line.split('=', 1)[1].strip()
                    if not encrypted_str:
                        return None
                    
                    try:
                        from core.security import decrypt_password
                        decrypted = decrypt_password(encrypted_str)
                        return json.loads(decrypted)
                    except Exception as e:
                        logger.error(f"解密配置失败: {e}")
                        return None
    except Exception as e:
        logger.error(f"读取配置文件失败: {e}")
    
    return None


def build_database_url_from_config(config_dict: dict) -> str:
    """从配置字典构建数据库URL"""
    password = config_dict.get('password', '')
    encoded_password = quote_plus(password)
    return f"mysql+pymysql://{config_dict['user']}:{encoded_password}@{config_dict['host']}:{config_dict['port']}/{config_dict['db_name']}?charset=utf8mb4"


def reload_engine(new_url: str, mysql_info: dict) -> bool:
    """重新加载数据库引擎"""
    global engine, SessionLocal
    
    logger.info(f"Reloading database engine with: {mysql_info.get('host')}:{mysql_info.get('port')}/{mysql_info.get('db_name')}")
    
    # 关闭旧连接
    if engine:
        try:
            engine.dispose()
        except:
            pass
    
    try:
        engine = create_engine(
            new_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True,
            echo=False,
            connect_args={'charset': 'utf8mb4'}
        )
        
        # 测试连接
        with engine.connect() as conn:
            result = conn.execute(text("SELECT VERSION()"))
            version = result.scalar()
            logger.info(f"MySQL reconnected: {version}")
        
        # 创建会话工厂
        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
        
        # 更新全局变量
        global DATABASE_URL, MYSQL_INFO
        DATABASE_URL = new_url
        MYSQL_INFO = mysql_info
        
        logger.info("Database engine reloaded successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to reload database engine: {e}")
        engine = None
        SessionLocal = None
        return False
    
    return None


def _build_database_url(config_dict: dict) -> str:
    """构建数据库URL"""
    password = config_dict.get('password', '')
    encoded_password = quote_plus(password)
    return f"mysql+pymysql://{config_dict['user']}:{encoded_password}@{config_dict['host']}:{config_dict['port']}/{config_dict['db_name']}?charset=utf8mb4"


def _load_config():
    """加载配置"""
    global DATABASE_URL, MYSQL_INFO
    
    # 优先从加密配置读取
    encrypted_config = _get_encrypted_config()
    if encrypted_config:
        DATABASE_URL = _build_database_url(encrypted_config)
        MYSQL_INFO = {
            'user': encrypted_config.get('user', ''),
            'password': '***',  # 隐藏密码
            'host': encrypted_config.get('host', ''),
            'port': encrypted_config.get('port', 3306),
            'db_name': encrypted_config.get('db_name', '')
        }
        logger.info(f"MySQL Configuration (encrypted): {MYSQL_INFO.get('host')}:{MYSQL_INFO.get('port')}/{MYSQL_INFO.get('db_name')}")
        return
    
    # 回退到环境变量
    try:
        from core.config import settings
        DATABASE_URL = settings.DATABASE_URL or ""
    except Exception as e:
        logger.warning(f"Failed to load settings: {e}")
        DATABASE_URL = ""
    
    if DATABASE_URL and DATABASE_URL.startswith('mysql'):
        import re
        pattern = r'mysql\+pymysql://([^:]+):([^@]+)@([^:]+):(\d+)/([^?]+)'
        match = re.match(pattern, DATABASE_URL)
        if match:
            MYSQL_INFO = {
                'user': match.group(1),
                'password': '***',  # 隐藏密码
                'host': match.group(3),
                'port': int(match.group(4)),
                'db_name': match.group(5).split('?')[0]
            }
            logger.info(f"MySQL Configuration: {MYSQL_INFO.get('host')}:{MYSQL_INFO.get('port')}/{MYSQL_INFO.get('db_name')}")


def _create_engine():
    """创建数据库引擎"""
    global engine, SessionLocal
    
    if not DATABASE_URL:
        logger.info("Database not configured. Skipping engine creation.")
        return False
    
    if not DATABASE_URL.startswith('mysql'):
        logger.warning("DATABASE_URL is not MySQL. Skipping.")
        return False
    
    try:
        engine = create_engine(
            DATABASE_URL,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True,
            echo=False,
            connect_args={'charset': 'utf8mb4'}
        )
        
        # 测试连接
        with engine.connect() as conn:
            result = conn.execute(text("SELECT VERSION()"))
            version = result.scalar()
            logger.info(f"MySQL Connected: {version}")
        
        # 创建会话工厂
        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
        
        logger.info("MySQL connection pool created successfully")
        return True
        
    except Exception as e:
        logger.error(f"MySQL connection failed: {e}")
        engine = None
        SessionLocal = None
        return False


# 初始化配置
_load_config()


def is_database_configured() -> bool:
    """检查数据库是否已配置"""
    return bool(DATABASE_URL and DATABASE_URL.strip())


def is_database_connected() -> bool:
    """检查数据库是否已连接"""
    return engine is not None


def get_db_session() -> Generator[Session, None, None]:
    """
    获取数据库会话
    
    用于FastAPI依赖注入
    
    Yields:
        Session: 数据库会话
    """
    if not SessionLocal:
        raise RuntimeError("Database not configured. Please visit /setup to configure.")
    
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db():
    """初始化数据库"""
    if not engine:
        logger.warning("Database engine not available. Skipping initialization.")
        return
    
    try:
        from models.database import init_database, create_default_admin
        
        # 创建表
        init_database(engine)
        logger.info("Database tables created/verified")
        
        # 创建默认管理员
        if SessionLocal:
            session = SessionLocal()
            try:
                create_default_admin(session)
                logger.info("Default admin account verified")
            finally:
                session.close()
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


def check_db_connection() -> bool:
    """
    检查数据库连接是否正常
    
    Returns:
        bool: 连接正常返回True
    """
    if not engine or not SessionLocal:
        return False
    
    try:
        session = SessionLocal()
        session.execute(text("SELECT 1"))
        session.close()
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


def get_db_info() -> dict:
    """
    获取数据库信息
    
    Returns:
        dict: 数据库信息
    """
    info = {
        'configured': bool(DATABASE_URL),
        'connected': engine is not None,
        'type': 'MySQL' if DATABASE_URL and DATABASE_URL.startswith('mysql') else None,
        'host': MYSQL_INFO.get('host'),
        'port': MYSQL_INFO.get('port'),
        'db_name': MYSQL_INFO.get('db_name'),
        'version': None
    }
    
    if engine:
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT VERSION()")).scalar()
                info['version'] = result
        except:
            pass
    
    return info


# 如果配置了数据库，尝试创建引擎
if DATABASE_URL:
    _create_engine()

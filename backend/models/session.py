# -*- coding: utf-8 -*-
"""
多源数据查询小程序版 - 数据库会话管理

支持:
- SQLite (开发环境默认)
- MySQL 8.0.2+ (生产环境推荐)

配置环境变量:
- DATABASE_URL: 数据库连接字符串
  SQLite: sqlite:///./data/mini_db_query.db
  MySQL: mysql+pymysql://user:password@host:port/database?charset=utf8mb4

Author: 飞书百万（AI助手）
"""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator
import logging

from models.database import Base, init_database, create_default_admin


logger = logging.getLogger(__name__)

# 数据目录
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# 数据库配置
DATABASE_URL = os.environ.get('DATABASE_URL', f"sqlite:///{DATA_DIR}/mini_db_query.db")

# 判断数据库类型
IS_MYSQL = DATABASE_URL.startswith('mysql')
IS_SQLITE = DATABASE_URL.startswith('sqlite')

# 创建引擎配置
if IS_MYSQL:
    # MySQL配置
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=3600,  # 1小时回收连接
        pool_pre_ping=True,  # 连接前检查可用性
        echo=False,
        connect_args={
            'charset': 'utf8mb4',
        }
    )
    logger.info(f"MySQL数据库连接池已创建: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")
    
elif IS_SQLITE:
    # SQLite配置
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )
    logger.info(f"SQLite数据库已创建: {DATA_DIR}")
    
else:
    # 其他数据库
    engine = create_engine(DATABASE_URL, echo=False)
    logger.info(f"数据库已连接: {DATABASE_URL.split('://')[0]}://...")


# SQLite WAL模式优化
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """为SQLite连接设置PRAGMA"""
    if IS_SQLITE:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-64000")  # 64MB
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db_session() -> Generator[Session, None, None]:
    """
    获取数据库会话
    
    用于FastAPI依赖注入
    
    Yields:
        Session: 数据库会话
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db():
    """初始化数据库"""
    try:
        # 创建表
        init_database(engine)
        logger.info("数据库表结构初始化完成")
        
        # 创建默认管理员
        session = SessionLocal()
        try:
            create_default_admin(session)
            logger.info("默认管理员账号检查完成")
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


def check_db_connection() -> bool:
    """
    检查数据库连接是否正常
    
    Returns:
        bool: 连接正常返回True
    """
    try:
        session = SessionLocal()
        session.execute("SELECT 1")
        session.close()
        return True
    except Exception as e:
        logger.error(f"数据库连接检查失败: {e}")
        return False


def get_db_info() -> dict:
    """
    获取数据库信息
    
    Returns:
        dict: 数据库信息
    """
    info = {
        'type': 'MySQL' if IS_MYSQL else 'SQLite',
        'url': DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL
    }
    
    if IS_MYSQL:
        try:
            session = SessionLocal()
            result = session.execute("SELECT VERSION()").scalar()
            info['version'] = result
            session.close()
        except:
            pass
    elif IS_SQLITE:
        try:
            session = SessionLocal()
            result = session.execute("SELECT sqlite_version()").scalar()
            info['version'] = result
            session.close()
        except:
            pass
    
    return info

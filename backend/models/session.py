# -*- coding: utf-8 -*-
"""
多源数据查询小程序版 - 数据库会话管理

Author: 飞书百万（AI助手）
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from models.database import Base, init_database, create_default_admin


# 数据库路径
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
os.makedirs(DATA_DIR, exist_ok=True)

DATABASE_URL = os.environ.get('DATABASE_URL', f"sqlite:///{DATA_DIR}/mini_db_query.db")

# 创建引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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
    # 创建表
    init_database(engine)
    
    # 创建默认管理员
    session = SessionLocal()
    try:
        create_default_admin(session)
    finally:
        session.close()

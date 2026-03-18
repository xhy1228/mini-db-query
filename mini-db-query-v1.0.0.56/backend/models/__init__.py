# -*- coding: utf-8 -*-
"""
数据模型包
"""

from .database import (
    Base,
    School,
    DatabaseConfig,
    QueryTemplate,
    User,
    UserSchool,
    QueryLog,
    init_database,
    create_default_admin
)
from .session import get_db_session, init_db, engine, SessionLocal

# 导入 OperationLog（定义在 services/log_service.py）
from services.log_service import OperationLog

__all__ = [
    'Base',
    'School',
    'DatabaseConfig',
    'QueryTemplate',
    'User',
    'UserSchool',
    'QueryLog',
    'OperationLog',
    'init_database',
    'create_default_admin',
    'get_db_session',
    'init_db',
    'engine',
    'SessionLocal'
]

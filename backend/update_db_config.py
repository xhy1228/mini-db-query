# -*- coding: utf-8 -*-
"""
更新数据库配置为SQLite测试数据库
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.session import SessionLocal
from models.database import DatabaseConfig
from core.security import encrypt_password

def update_database_config():
    """更新数据库配置为SQLite"""
    session = SessionLocal()
    
    try:
        # 获取示例学校的数据库配置
        db_config = session.query(DatabaseConfig).filter(
            DatabaseConfig.school_id == 1
        ).first()
        
        if db_config:
            # 更新为SQLite配置
            db_config.db_type = 'SQLite'
            db_config.name = 'SQLite测试数据库'
            db_config.host = ''
            db_config.port = 0
            db_config.username = ''
            db_config.password = ''
            db_config.database = './data/test_query.db'
            db_config.description = 'SQLite测试数据库，包含示例学生、消费、门禁数据'
            
            print("✅ 数据库配置已更新为SQLite")
        else:
            # 创建新的配置
            db_config = DatabaseConfig(
                school_id=1,
                name='SQLite测试数据库',
                db_type='SQLite',
                host='',
                port=0,
                username='',
                password='',
                database='./data/test_query.db',
                description='SQLite测试数据库',
                status='active'
            )
            session.add(db_config)
            print("✅ 创建SQLite数据库配置")
        
        session.commit()
        
    except Exception as e:
        session.rollback()
        print(f"❌ 更新失败: {e}")
        raise
    finally:
        session.close()


if __name__ == '__main__':
    update_database_config()

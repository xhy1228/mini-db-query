# -*- coding: utf-8 -*-
"""
初始化示例数据

创建默认管理员、学校、数据库配置和查询模板
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from models.session import SessionLocal, init_db
from models.database import School, DatabaseConfig, QueryTemplate, User
from core.security import get_password_hash, encrypt_password


def create_sample_data():
    """创建示例数据"""
    session = SessionLocal()
    
    try:
        # 1. 创建默认管理员
        admin = session.query(User).filter(User.phone == 'admin').first()
        if not admin:
            admin = User(
                phone='admin',
                password=get_password_hash('123456'),
                name='超级管理员',
                role='admin',
                status='active'
            )
            session.add(admin)
            print("✅ 创建默认管理员: admin / 123456")
        else:
            print("ℹ️ 管理员已存在")
        
        # 2. 创建示例学校
        school = session.query(School).filter(School.code == 'demo_school').first()
        if not school:
            school = School(
                name='示例学校',
                code='demo_school',
                description='用于演示的示例学校',
                status='active'
            )
            session.add(school)
            session.flush()
            print("✅ 创建示例学校: 示例学校")
        else:
            print("ℹ️ 学校已存在")
        
        # 3. 创建示例数据库配置
        db_config = session.query(DatabaseConfig).filter(
            DatabaseConfig.school_id == school.id
        ).first()
        
        if not db_config:
            db_config = DatabaseConfig(
                school_id=school.id,
                name='示例数据库',
                db_type='MySQL',
                host='localhost',
                port=3306,
                username='root',
                password=encrypt_password('your_password'),  # 请修改为实际密码
                database='test_db',
                description='示例MySQL数据库',
                status='active'
            )
            session.add(db_config)
            print("✅ 创建示例数据库配置")
            print("⚠️ 请修改数据库连接信息！")
        else:
            print("ℹ️ 数据库配置已存在")
        
        # 4. 创建示例查询模板
        templates_data = [
            {
                'category': 'student',
                'category_name': '学生业务',
                'category_icon': '🎓',
                'name': '学生信息查询',
                'description': '根据姓名或学号查询学生基本信息',
                'sql_template': 'SELECT CUSTNAME as 姓名, STUDENTID as 学号, CLASSNAME as 班级, CARDCODE as 卡号 FROM CARD_CUSTOMERS WHERE 1=1',
                'fields': [
                    {'id': 'name', 'label': '姓名', 'column': 'CUSTNAME', 'type': 'text', 'operator': 'LIKE'},
                    {'id': 'student_id', 'label': '学号', 'column': 'STUDENTID', 'type': 'text', 'operator': '='}
                ],
                'time_field': None,
                'default_limit': 100
            },
            {
                'category': 'consume',
                'category_name': '消费业务',
                'category_icon': '💰',
                'name': '消费明细查询',
                'description': '查询消费流水明细记录',
                'sql_template': 'SELECT TRATIME as 交易时间, CARDCODE as 卡号, TRAMONEY as 金额, TRATYPE as 类型, OPERNAME as 终端 FROM DATA_CARD_CONSUME WHERE 1=1',
                'fields': [
                    {'id': 'card_code', 'label': '卡号', 'column': 'CARDCODE', 'type': 'text', 'operator': '='}
                ],
                'time_field': 'TRATIME',
                'default_limit': 500
            },
            {
                'category': 'access',
                'category_name': '门禁业务',
                'category_icon': '🚪',
                'name': '门禁记录查询',
                'description': '查询门禁进出记录',
                'sql_template': 'SELECT RECORDTIME as 时间, USERNAME as 姓名, DOORNAME as 门禁, INOUTTYPE as 进出 FROM ACCESS_INOUT_RECORD WHERE 1=1',
                'fields': [
                    {'id': 'username', 'label': '姓名', 'column': 'USERNAME', 'type': 'text', 'operator': 'LIKE'}
                ],
                'time_field': 'RECORDTIME',
                'default_limit': 500
            }
        ]
        
        for t_data in templates_data:
            existing = session.query(QueryTemplate).filter(
                QueryTemplate.school_id == school.id,
                QueryTemplate.name == t_data['name']
            ).first()
            
            if not existing:
                template = QueryTemplate(
                    school_id=school.id,
                    category=t_data['category'],
                    category_name=t_data['category_name'],
                    category_icon=t_data['category_icon'],
                    name=t_data['name'],
                    description=t_data['description'],
                    sql_template=t_data['sql_template'],
                    fields=t_data['fields'],
                    time_field=t_data['time_field'],
                    default_limit=t_data['default_limit'],
                    status='active'
                )
                session.add(template)
                print(f"✅ 创建查询模板: {t_data['name']}")
            else:
                print(f"ℹ️ 查询模板已存在: {t_data['name']}")
        
        session.commit()
        print("\n🎉 示例数据创建完成！")
        
    except Exception as e:
        session.rollback()
        print(f"❌ 创建示例数据失败: {e}")
        raise
    finally:
        session.close()


if __name__ == '__main__':
    print("=" * 50)
    print("初始化数据库和示例数据")
    print("=" * 50)
    
    # 初始化数据库
    init_db()
    print("✅ 数据库表初始化完成")
    
    # 创建示例数据
    create_sample_data()

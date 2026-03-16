# -*- coding: utf-8 -*-
"""
多源数据查询小程序版 - 数据库初始化脚本

Author: 飞书百万（AI助手）
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.database import Base, init_database, create_default_admin, School, DatabaseConfig, QueryTemplate, User, UserSchool
from core.security import get_password_hash
from core.config import settings


def init_db():
    """初始化数据库"""
    print("=" * 50)
    print("多源数据查询小程序版 - 数据库初始化")
    print("=" * 50)
    
    # 创建SQLite数据库
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'mini_db_query.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    database_url = f"sqlite:///{db_path}"
    print(f"\n数据库路径: {db_path}")
    
    # 创建引擎
    engine = create_engine(database_url, echo=True)
    
    # 创建表
    print("\n创建数据库表...")
    init_database(engine)
    print("✅ 数据库表创建完成")
    
    # 创建会话
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # 创建默认超级管理员
    print("\n创建超级管理员...")
    admin = create_default_admin(session)
    print(f"✅ 超级管理员创建完成")
    print(f"   账号: admin")
    print(f"   密码: 123456")
    
    # 创建示例学校
    print("\n创建示例学校...")
    school1 = School(
        name="示例学校A",
        code="SCHOOL_A",
        description="示例学校A的数据库查询系统"
    )
    school2 = School(
        name="示例学校B", 
        code="SCHOOL_B",
        description="示例学校B的数据库查询系统"
    )
    session.add_all([school1, school2])
    session.commit()
    print(f"✅ 创建学校: {school1.name}, {school2.name}")
    
    # 创建示例数据库配置
    print("\n创建示例数据库配置...")
    db_config1 = DatabaseConfig(
        school_id=school1.id,
        name="一卡通数据库",
        db_type="Oracle",
        host="localhost",
        port=1521,
        username="system",
        password=get_password_hash("password"),  # 实际应存储加密的明文
        service_name="ORCL",
        description="一卡通系统Oracle数据库"
    )
    db_config2 = DatabaseConfig(
        school_id=school1.id,
        name="微信系统数据库",
        db_type="MySQL",
        host="localhost",
        port=3306,
        username="root",
        password=get_password_hash("password"),
        database="wechat_db",
        description="微信系统MySQL数据库"
    )
    session.add_all([db_config1, db_config2])
    session.commit()
    print(f"✅ 创建数据库配置: {db_config1.name}, {db_config2.name}")
    
    # 创建示例查询模板
    print("\n创建示例查询模板...")
    template1 = QueryTemplate(
        school_id=school1.id,
        category="student",
        category_name="学生业务",
        category_icon="🎓",
        name="学生信息查询",
        description="查询学生基本信息",
        sql_template="SELECT CUSTNAME as 姓名, STUDENTID as 学号, IDCARD as 身份证号 FROM CARD_CUSTOMERS",
        fields=[
            {"id": "name", "label": "姓名", "column": "CUSTNAME", "type": "text", "operator": "LIKE"},
            {"id": "student_id", "label": "学号", "column": "STUDENTID", "type": "text", "operator": "="}
        ],
        default_limit=100
    )
    template2 = QueryTemplate(
        school_id=school1.id,
        category="consume",
        category_name="消费业务",
        category_icon="💰",
        name="消费明细查询",
        description="查询消费流水明细",
        sql_template="SELECT CARDID as 卡号, TRANAMT as 金额, TRATIME as 时间 FROM DATA_CARD_CONSUME",
        fields=[
            {"id": "card_id", "label": "卡号", "column": "CARDID", "type": "text", "operator": "="}
        ],
        time_field="TRATIME",
        default_limit=500
    )
    template3 = QueryTemplate(
        school_id=school1.id,
        category="access",
        category_name="门禁业务",
        category_icon="🚪",
        name="门禁记录查询",
        description="查询门禁进出记录",
        sql_template="SELECT CARDID as 卡号, INOUTTIME as 时间, DEVICENAME as 设备 FROM ACCESS_INOUT_RECORD",
        fields=[
            {"id": "card_id", "label": "卡号", "column": "CARDID", "type": "text", "operator": "="}
        ],
        time_field="INOUTTIME",
        default_limit=500
    )
    session.add_all([template1, template2, template3])
    session.commit()
    print(f"✅ 创建查询模板: {template1.name}, {template2.name}, {template3.name}")
    
    # 创建示例用户
    print("\n创建示例用户...")
    user1 = User(
        phone="13800138000",
        password=get_password_hash("123456"),
        name="张三",
        id_card=get_password_hash("110101199001011234"),
        role="user",
        status="active"
    )
    user2 = User(
        phone="13900139000",
        password=get_password_hash("654321"),
        name="李四",
        id_card=get_password_hash("110101199002021234"),
        role="user",
        status="active"
    )
    session.add_all([user1, user2])
    session.commit()
    print(f"✅ 创建用户: {user1.name}({user1.phone}), {user2.name}({user2.phone})")
    
    # 分配用户权限
    print("\n分配用户权限...")
    perm1 = UserSchool(user_id=user1.id, school_id=school1.id, permissions=["query"])
    perm2 = UserSchool(user_id=user2.id, school_id=school1.id, permissions=["query"])
    perm3 = UserSchool(user_id=user2.id, school_id=school2.id, permissions=["query"])
    session.add_all([perm1, perm2, perm3])
    session.commit()
    print(f"✅ 用户 {user1.name} 授权学校: {school1.name}")
    print(f"✅ 用户 {user2.name} 授权学校: {school1.name}, {school2.name}")
    
    session.close()
    
    print("\n" + "=" * 50)
    print("✅ 数据库初始化完成！")
    print("=" * 50)
    print("\n默认账号信息:")
    print("- 超级管理员: admin / 123456")
    print("- 示例用户1: 13800138000 / 123456")
    print("- 示例用户2: 13900139000 / 654321")
    print("\n")


if __name__ == "__main__":
    init_db()

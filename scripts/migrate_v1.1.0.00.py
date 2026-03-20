#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mini DB Query - 数据结构优化迁移脚本
Version: v1.1.0.00
用途: 将 query_templates.fields JSON 数据迁移到 query_fields 独立表
"""

import json
import sys
sys.path.insert(0, '/root/projects/mini-db-query/backend')

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import sessionmaker, declarative_base
from models.database import Base, QueryTemplate, QueryField, TemplateCategory


def migrate_fields(session):
    """迁移查询条件到独立表"""
    print("开始迁移查询条件数据...")
    
    templates = session.query(QueryTemplate).all()
    migrated = 0
    
    for template in templates:
        if not template.fields:
            continue
            
        try:
            fields = template.fields if isinstance(template.fields, list) else json.loads(template.fields)
            
            for idx, field in enumerate(fields):
                # 检查是否已存在
                existing = session.query(QueryField).filter_by(
                    template_id=template.id,
                    field_key=field.get('id', f'field_{idx}')
                ).first()
                
                if existing:
                    continue
                
                # 创建新的查询条件记录
                query_field = QueryField(
                    template_id=template.id,
                    field_key=field.get('id', f'field_{idx}'),
                    field_label=field.get('label', ''),
                    field_type=field.get('type', 'text'),
                    db_column=field.get('column', ''),
                    operator=field.get('operator', '='),
                    default_value=field.get('default'),
                    options=json.dumps(field.get('options')) if field.get('options') else None,
                    required=1 if field.get('required') else 0,
                    sort_order=idx,
                    placeholder=field.get('placeholder')
                )
                session.add(query_field)
                migrated += 1
                
        except Exception as e:
            print(f"  模板 {template.id} 迁移失败: {e}")
            continue
    
    session.commit()
    print(f"✅ 成功迁移 {migrated} 条查询条件")


def link_database_config(session):
    """关联模板和数据库配置"""
    print("开始关联数据库配置...")
    
    # 根据配置名称匹配 (从 query_templates.json 的 db_config 字段)
    templates = session.query(QueryTemplate).filter(QueryTemplate.database_id.is_(None)).all()
    
    for template in templates:
        # 这里根据实际业务逻辑匹配
        # 示例: 根据模板名称或 SQL 内容推断数据库类型
        if 'DATA_CARD_CONSUME' in template.sql_template or 'DATA_ONLINE_CASH' in template.sql_template:
            # 一卡通 Oracle
            from models.database import DatabaseConfig
            db_config = session.query(DatabaseConfig).filter(
                DatabaseConfig.school_id == template.school_id,
                DatabaseConfig.name.like('%一卡通%')
            ).first()
            
            if db_config:
                template.database_id = db_config.id
                print(f"  模板 {template.id} 关联到数据库 {db_config.id}")
    
    session.commit()
    print("✅ 数据库配置关联完成")


def main():
    """主函数"""
    print("=" * 50)
    print("Mini DB Query - 数据迁移脚本 v1.1.0.00")
    print("=" * 50)
    
    # 数据库连接
    DB_URL = "mysql+pymysql://root:123456@localhost:3306/mini_db_query?charset=utf8mb4"
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        migrate_fields(session)
        link_database_config(session)
        print("\n✅ 所有迁移任务完成!")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        session.close()


if __name__ == '__main__':
    main()

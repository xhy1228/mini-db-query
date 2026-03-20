#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mini DB Query - 数据结构优化完整迁移脚本
Version: v1.1.0.00

用途: 执行数据库结构升级和数据迁移
运行方式: cd /root/projects/mini-db-query/backend && python scripts/migrate_v1.1.0.py
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, '/root/projects/mini-db-query/backend')

import json
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


def get_db_url():
    """获取数据库连接URL"""
    try:
        from core.config import settings
        return settings.DATABASE_URL
    except:
        # 默认配置
        return "mysql+pymysql://root:123456@localhost:3306/mini_db_query?charset=utf8mb4"


def run_sql_upgrade(engine):
    """执行 SQL 升级脚本"""
    print("\n" + "=" * 50)
    print("Step 1: 执行数据库结构升级...")
    print("=" * 50)
    
    sql_file = '/root/projects/mini-db-query/scripts/upgrade_v1.1.0.00.sql'
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # 分割 SQL 语句
    statements = sql_content.split(';')
    
    with engine.connect() as conn:
        for stmt in statements:
            stmt = stmt.strip()
            if stmt and not stmt.startswith('--'):
                try:
                    conn.execute(text(stmt))
                except Exception as e:
                    # 忽略 "已存在" 类型的错误
                    if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                        print(f"  ⚠️  跳过: {str(e)[:50]}")
                    else:
                        print(f"  ❌ 错误: {e}")
        
        conn.commit()
    
    print("✅ 数据库结构升级完成")


def migrate_categories(session, engine):
    """迁移业务大类数据"""
    print("\n" + "=" * 50)
    print("Step 2: 迁移业务大类数据...")
    print("=" * 50)
    
    # 从 query_templates 中提取业务大类
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT DISTINCT 
                school_id, 
                category AS code, 
                MAX(category_name) AS name, 
                MAX(category_icon) AS icon,
                MIN(id) as min_id
            FROM query_templates 
            GROUP BY school_id, category
            ORDER BY school_id, min_id
        """))
        
        categories = result.fetchall()
    
    migrated = 0
    for cat in categories:
        school_id, code, name, icon, _ = cat
        
        # 检查是否已存在
        existing = session.execute(text("""
            SELECT id FROM template_categories 
            WHERE school_id = :school_id AND code = :code
        """), {"school_id": school_id, "code": code}).fetchone()
        
        if existing:
            continue
        
        # 确定排序
        sort_order = {'student': 1, 'consume': 2, 'access': 3, 'wechat': 4}.get(code, 5)
        
        # 插入新记录
        session.execute(text("""
            INSERT INTO template_categories (school_id, code, name, icon, sort_order, status)
            VALUES (:school_id, :code, :name, :icon, :sort_order, 'active')
        """), {
            "school_id": school_id,
            "code": code,
            "name": name or code,
            "icon": icon,
            "sort_order": sort_order
        })
        migrated += 1
    
    session.commit()
    print(f"✅ 成功迁移 {migrated} 个业务大类")


def update_template_categories(session, engine):
    """更新模板表的业务大类关联"""
    print("\n" + "=" * 50)
    print("Step 3: 更新模板表关联...")
    print("=" * 50)
    
    result = session.execute(text("""
        UPDATE query_templates t
        JOIN template_categories c ON t.school_id = c.school_id AND t.category = c.code
        SET t.category_id = c.id
        WHERE t.category_id IS NULL
    """))
    
    session.commit()
    print(f"✅ 更新了 {result.rowcount} 个模板的分类关联")


def migrate_fields(session, engine):
    """迁移查询条件数据"""
    print("\n" + "=" * 50)
    print("Step 4: 迁移查询条件数据...")
    print("=" * 50)
    
    # 获取所有模板及其 fields JSON
    result = session.execute(text("""
        SELECT id, fields FROM query_templates 
        WHERE fields IS NOT NULL AND fields != 'null' AND fields != '[]'
    """))
    
    templates = result.fetchall()
    
    migrated = 0
    for template_id, fields_json in templates:
        if not fields_json:
            continue
        
        try:
            fields = json.loads(fields_json) if isinstance(fields_json, str) else fields_json
            
            for idx, field in enumerate(fields):
                field_key = field.get('id', f'field_{idx}')
                
                # 检查是否已存在
                existing = session.execute(text("""
                    SELECT id FROM query_fields 
                    WHERE template_id = :template_id AND field_key = :field_key
                """), {"template_id": template_id, "field_key": field_key}).fetchone()
                
                if existing:
                    continue
                
                # 插入新记录
                session.execute(text("""
                    INSERT INTO query_fields 
                    (template_id, field_key, field_label, field_type, db_column, operator, 
                     default_value, required, sort_order, placeholder)
                    VALUES 
                    (:template_id, :field_key, :field_label, :field_type, :db_column, :operator,
                     :default_value, :required, :sort_order, :placeholder)
                """), {
                    "template_id": template_id,
                    "field_key": field_key,
                    "field_label": field.get('label', ''),
                    "field_type": field.get('type', 'text'),
                    "db_column": field.get('column', ''),
                    "operator": field.get('operator', '='),
                    "default_value": field.get('default'),
                    "required": 1 if field.get('required') else 0,
                    "sort_order": idx,
                    "placeholder": field.get('placeholder')
                })
                migrated += 1
                
        except Exception as e:
            print(f"  ⚠️  模板 {template_id} 迁移失败: {e}")
            continue
    
    session.commit()
    print(f"✅ 成功迁移 {migrated} 个查询条件")


def verify_migration(engine):
    """验证迁移结果"""
    print("\n" + "=" * 50)
    print("Step 5: 验证迁移结果...")
    print("=" * 50)
    
    with engine.connect() as conn:
        # 检查业务大类表
        result = conn.execute(text("SELECT COUNT(*) FROM template_categories"))
        cat_count = result.scalar()
        print(f"  业务大类表记录数: {cat_count}")
        
        # 检查查询条件表
        result = conn.execute(text("SELECT COUNT(*) FROM query_fields"))
        field_count = result.scalar()
        print(f"  查询条件表记录数: {field_count}")
        
        # 检查模板关联
        result = conn.execute(text("SELECT COUNT(*) FROM query_templates WHERE category_id IS NOT NULL"))
        linked_count = result.scalar()
        print(f"  已关联分类的模板数: {linked_count}")
        
        # 检查新表
        result = conn.execute(text("SHOW TABLES LIKE 'template_categories'"))
        if result.fetchone():
            print("  ✅ template_categories 表已创建")
        
        result = conn.execute(text("SHOW TABLES LIKE 'query_fields'"))
        if result.fetchone():
            print("  ✅ query_fields 表已创建")
        
        result = conn.execute(text("SHOW TABLES LIKE 'query_template_history'"))
        if result.fetchone():
            print("  ✅ query_template_history 表已创建")
        
        result = conn.execute(text("SHOW TABLES LIKE 'template_permissions'"))
        if result.fetchone():
            print("  ✅ template_permissions 表已创建")
    
    print("\n✅ 迁移验证完成")


def main():
    """主函数"""
    print("=" * 60)
    print(" Mini DB Query - 数据结构优化迁移脚本 v1.1.0.00")
    print("=" * 60)
    print(f" 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 数据库连接
    db_url = get_db_url()
    print(f"\n数据库连接: {db_url[:50]}...")
    
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        run_sql_upgrade(engine)
        migrate_categories(session, engine)
        update_template_categories(session, engine)
        migrate_fields(session, engine)
        verify_migration(engine)
        
        print("\n" + "=" * 60)
        print(" ✅ 所有迁移任务完成!")
        print("=" * 60)
        
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

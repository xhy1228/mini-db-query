#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
多源数据查询小程序版 - MySQL数据库初始化脚本

功能:
1. 检查MySQL连接
2. 创建数据库(如果不存在)
3. 执行数据库架构脚本
4. 创建默认管理员账号

使用方法:
    python init_mysql_db.py --host localhost --port 3306 --user root --password your_password

Author: 飞书百万（AI助手）
"""

import os
import sys
import argparse
import pymysql
from pymysql import Error
from pathlib import Path


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='MySQL数据库初始化')
    parser.add_argument('--host', default='localhost', help='MySQL主机地址')
    parser.add_argument('--port', type=int, default=3306, help='MySQL端口')
    parser.add_argument('--user', default='root', help='MySQL用户名')
    parser.add_argument('--password', default='', help='MySQL密码')
    parser.add_argument('--database', default='mini_db_query', help='数据库名称')
    parser.add_argument('--admin-password', default='123456', help='管理员密码')
    parser.add_argument('--charset', default='utf8mb4', help='字符集')
    return parser.parse_args()


def create_connection(host, port, user, password, database=None):
    """创建MySQL连接"""
    try:
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    except Error as e:
        print(f"❌ 连接MySQL失败: {e}")
        return None


def execute_sql_file(cursor, sql_file):
    """执行SQL文件"""
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # 分割SQL语句(处理存储过程中的DELIMITER)
    statements = []
    current_statement = []
    in_delimiter = False
    custom_delimiter = ';'
    
    for line in sql_content.split('\n'):
        stripped = line.strip()
        
        # 处理DELIMITER变化
        if stripped.upper().startswith('DELIMITER'):
            parts = stripped.split()
            if len(parts) > 1:
                custom_delimiter = parts[1]
                if custom_delimiter != ';':
                    in_delimiter = True
                else:
                    in_delimiter = False
            continue
        
        current_statement.append(line)
        
        # 检查语句结束
        if in_delimiter:
            if custom_delimiter in stripped:
                stmt = '\n'.join(current_statement)
                if stmt.strip() and not stmt.strip().startswith('--'):
                    statements.append(stmt.replace(custom_delimiter, ';'))
                current_statement = []
        else:
            if stripped.endswith(';'):
                stmt = '\n'.join(current_statement)
                if stmt.strip() and not stmt.strip().startswith('--'):
                    statements.append(stmt)
                current_statement = []
    
    # 执行所有语句
    for stmt in statements:
        stmt = stmt.strip()
        if not stmt or stmt.startswith('--'):
            continue
        try:
            cursor.execute(stmt)
        except Error as e:
            # 忽略某些非致命错误
            if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                print(f"⚠️  跳过: {str(e)[:100]}")
            else:
                print(f"❌ 执行SQL失败: {str(e)[:200]}")
                print(f"   SQL: {stmt[:200]}...")


def init_database(args):
    """初始化数据库"""
    print("=" * 60)
    print("🚀 MySQL 数据库初始化工具")
    print("=" * 60)
    
    # Step 1: 连接MySQL服务器(不指定数据库)
    print(f"\n📡 连接MySQL服务器 {args.host}:{args.port}...")
    conn = create_connection(args.host, args.port, args.user, args.password)
    if not conn:
        sys.exit(1)
    
    cursor = conn.cursor()
    
    # Step 2: 创建数据库(如果不存在)
    print(f"📦 检查数据库 '{args.database}'...")
    cursor.execute(f"""
        CREATE DATABASE IF NOT EXISTS `{args.database}` 
        DEFAULT CHARACTER SET {args.charset} 
        DEFAULT COLLATE {args.charset}_unicode_ci
    """)
    print(f"✅ 数据库 '{args.database}' 已就绪")
    
    # Step 3: 切换到目标数据库
    cursor.execute(f"USE `{args.database}`")
    
    # Step 4: 执行数据库架构脚本
    schema_file = Path(__file__).parent.parent / 'database' / 'mysql_schema.sql'
    if schema_file.exists():
        print(f"\n📜 执行数据库架构脚本: {schema_file}")
        execute_sql_file(cursor, schema_file)
        print("✅ 数据库表结构创建完成")
    else:
        print(f"⚠️  未找到架构文件: {schema_file}")
        print("   将创建基本表结构...")
        # 创建基本表
        create_basic_tables(cursor)
    
    # Step 5: 创建默认管理员账号
    print(f"\n👤 创建默认管理员账号...")
    create_admin_user(cursor, args.admin_password)
    
    # Step 6: 验证
    print("\n🔍 验证数据库结构...")
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    print(f"✅ 已创建 {len(tables)} 个表:")
    for table in tables:
        table_name = list(table.values())[0]
        print(f"   - {table_name}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print("🎉 MySQL数据库初始化完成!")
    print("=" * 60)
    print(f"\n数据库连接信息:")
    print(f"  主机: {args.host}")
    print(f"  端口: {args.port}")
    print(f"  数据库: {args.database}")
    print(f"  字符集: {args.charset}")
    print(f"\n默认管理员账号:")
    print(f"  手机号: admin")
    print(f"  密码: {args.admin_password}")
    print(f"\n请妥善保管管理员密码!")


def create_basic_tables(cursor):
    """创建基本表结构"""
    tables = [
        """
        CREATE TABLE IF NOT EXISTS schools (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            code VARCHAR(50) NOT NULL UNIQUE,
            description TEXT,
            status VARCHAR(20) DEFAULT 'active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            phone VARCHAR(20) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            name VARCHAR(100) NOT NULL,
            id_card VARCHAR(255),
            role VARCHAR(20) DEFAULT 'user',
            status VARCHAR(20) DEFAULT 'active',
            last_login DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS database_configs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            school_id INT NOT NULL,
            name VARCHAR(100) NOT NULL,
            db_type VARCHAR(50) NOT NULL,
            host VARCHAR(255) NOT NULL,
            port INT NOT NULL,
            username VARCHAR(100) NOT NULL,
            password TEXT NOT NULL,
            database VARCHAR(100),
            service_name VARCHAR(100),
            driver VARCHAR(100),
            description TEXT,
            status VARCHAR(20) DEFAULT 'active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS query_templates (
            id INT AUTO_INCREMENT PRIMARY KEY,
            school_id INT NOT NULL,
            category VARCHAR(50) NOT NULL,
            category_name VARCHAR(100),
            category_icon VARCHAR(20),
            name VARCHAR(100) NOT NULL,
            description TEXT,
            sql_template TEXT NOT NULL,
            fields JSON,
            time_field VARCHAR(100),
            default_limit INT DEFAULT 500,
            status VARCHAR(20) DEFAULT 'active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS query_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            school_id INT,
            template_id INT,
            query_name VARCHAR(200),
            query_params JSON,
            sql_executed TEXT,
            result_count INT DEFAULT 0,
            query_time INT,
            status VARCHAR(20) DEFAULT 'success',
            error_message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    ]
    
    for sql in tables:
        try:
            cursor.execute(sql)
        except Error as e:
            print(f"⚠️  创建表失败: {e}")


def create_admin_user(cursor, password):
    """创建默认管理员用户"""
    from passlib.context import CryptContext
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed_password = pwd_context.hash(password)
    
    # 检查管理员是否存在
    cursor.execute("SELECT id FROM users WHERE phone = 'admin'")
    admin = cursor.fetchone()
    
    if admin:
        # 更新密码
        cursor.execute(
            "UPDATE users SET password = %s WHERE phone = 'admin'",
            (hashed_password,)
        )
        print("✅ 管理员密码已更新")
    else:
        # 创建管理员
        cursor.execute(
            """
            INSERT INTO users (phone, password, name, role, status)
            VALUES (%s, %s, %s, %s, %s)
            """,
            ('admin', hashed_password, '超级管理员', 'admin', 'active')
        )
        print("✅ 管理员账号已创建")


if __name__ == '__main__':
    args = parse_args()
    init_database(args)

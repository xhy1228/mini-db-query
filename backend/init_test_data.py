# -*- coding: utf-8 -*-
"""
初始化测试数据库

创建SQLite测试数据库并填充示例数据
"""

import sqlite3
import os
from datetime import datetime, timedelta
import random

def create_test_database():
    """创建测试数据库"""
    db_path = './data/test_query.db'
    
    # 删除旧数据库
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 创建学生表
    cursor.execute('''
        CREATE TABLE CARD_CUSTOMERS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            CUSTNAME TEXT,
            STUDENTID TEXT,
            CLASSNAME TEXT,
            CARDCODE TEXT,
            STATUS TEXT DEFAULT 'active'
        )
    ''')
    
    # 创建消费记录表
    cursor.execute('''
        CREATE TABLE DATA_CARD_CONSUME (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            TRATIME TEXT,
            CARDCODE TEXT,
            TRAMONEY REAL,
            TRATYPE TEXT,
            OPERNAME TEXT
        )
    ''')
    
    # 创建门禁记录表
    cursor.execute('''
        CREATE TABLE ACCESS_INOUT_RECORD (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            RECORDTIME TEXT,
            USERNAME TEXT,
            DOORNAME TEXT,
            INOUTTYPE TEXT
        )
    ''')
    
    # 插入学生数据
    students = [
        ('张三', '2023001', '计算机2301班', 'C001'),
        ('李四', '2023002', '计算机2301班', 'C002'),
        ('王五', '2023003', '计算机2301班', 'C003'),
        ('赵六', '2023004', '计算机2302班', 'C004'),
        ('钱七', '2023005', '计算机2302班', 'C005'),
        ('孙八', '2023006', '软件工程2301班', 'C006'),
        ('周九', '2023007', '软件工程2301班', 'C007'),
        ('吴十', '2023008', '软件工程2301班', 'C008'),
    ]
    
    cursor.executemany(
        'INSERT INTO CARD_CUSTOMERS (CUSTNAME, STUDENTID, CLASSNAME, CARDCODE) VALUES (?, ?, ?, ?)',
        students
    )
    
    # 插入消费记录
    base_time = datetime.now() - timedelta(days=30)
    consume_types = ['食堂消费', '超市购物', '图书馆打印', '洗澡']
    terminals = ['一食堂', '二食堂', '校园超市', '图书馆', '宿舍楼']
    
    for i in range(100):
        tr_time = base_time + timedelta(hours=random.randint(0, 720))
        card_code = f'C{random.randint(1, 8):03d}'
        money = round(random.uniform(1, 50), 2)
        tra_type = random.choice(consume_types)
        terminal = random.choice(terminals)
        
        cursor.execute(
            'INSERT INTO DATA_CARD_CONSUME (TRATIME, CARDCODE, TRAMONEY, TRATYPE, OPERNAME) VALUES (?, ?, ?, ?, ?)',
            (tr_time.strftime('%Y-%m-%d %H:%M:%S'), card_code, money, tra_type, terminal)
        )
    
    # 插入门禁记录
    doors = ['南门', '北门', '东门', '图书馆大门', '实验楼']
    inout_types = ['进', '出']
    names = ['张三', '李四', '王五', '赵六', '钱七']
    
    for i in range(100):
        rec_time = base_time + timedelta(hours=random.randint(0, 720))
        name = random.choice(names)
        door = random.choice(doors)
        inout = random.choice(inout_types)
        
        cursor.execute(
            'INSERT INTO ACCESS_INOUT_RECORD (RECORDTIME, USERNAME, DOORNAME, INOUTTYPE) VALUES (?, ?, ?, ?)',
            (rec_time.strftime('%Y-%m-%d %H:%M:%S'), name, door, inout)
        )
    
    conn.commit()
    conn.close()
    
    print(f"✅ 测试数据库创建成功: {db_path}")
    return db_path


if __name__ == '__main__':
    create_test_database()

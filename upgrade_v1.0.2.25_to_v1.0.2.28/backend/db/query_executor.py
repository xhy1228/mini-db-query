# -*- coding: utf-8 -*-

"""
多源数据查询助手 —— 查询执行器模块

Author: 飞书百万（AI助手）
模块作用：根据用户输入的查询语句，通过已连接的数据库连接器执行查询，
并返回查询结果。该模块是数据库交互的核心，为上层 GUI 提供数据获取能力。
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date, time as datetime_time
from decimal import Decimal

from sqlalchemy import text

# 设置模块日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def serialize_value(value):
    """序列化单个值，处理日期时间和特殊类型"""
    if value is None:
        return None
    if isinstance(value, (datetime, date, datetime_time)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, bytes):
        # 尝试解码为字符串
        try:
            return value.decode('utf-8')
        except:
            return str(value)
    return value


def serialize_row(row_dict: dict) -> dict:
    """序列化一行数据，处理所有特殊类型"""
    return {k: serialize_value(v) for k, v in row_dict.items()}


class QueryExecutor:
    """查询执行器类，负责执行查询并返回结果"""
    
    def __init__(self, connector):
        """
        :param connector: 数据库连接器实例，必须实现 get_connection() 方法
        """
        self.connector = connector
        
    def execute_query(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """
        执行传入的 SQL 查询语句，并返回结果集（列表形式，每行为字典）
        :param query: 用户输入的 SQL 查询语句
        :return: 查询结果（列表，每个元素为字典形式的行数据），查询失败时返回 None
        """
        if not query or not query.strip():
            logger.warning("查询语句为空或仅包含空格，将不执行。")
            return None
        
        try:
            engine = self.connector.get_connection()
            if not engine:
                logger.error("数据库连接未建立，无法执行查询。")
                return None
            
            with engine.connect() as conn:
                logger.info(f"正在执行查询: {query[:50]}...")
                result = conn.execute(text(query))
                
                if result.returns_rows:
                    # 获取列名
                    columns = list(result.keys())
                    # 获取所有行数据
                    rows = result.fetchall()
                    
                    # 将每行数据转换为字典（列名: 值），并序列化特殊类型
                    data = [
                        serialize_row(dict(zip(columns, row))) 
                        for row in rows
                    ] if columns and rows else []
                    
                    logger.info(f"查询执行成功，返回 {len(data)} 行数据。")
                    return data
                else:
                    logger.info("查询执行成功，无返回数据。")
                    return []
            
        except Exception as e:
            logger.error(f"查询执行失败: {e}")
            raise


# 示例用法
# if __name__ == '__main__':
#     from src.db.connector import get_connector
#     sample_config = {
#         'db_type': 'MySQL',
#         'host': '127.0.0.1',
#         'port': 3306,
#         'username': 'root',
#         'password': 'password',
#         'database': 'test_db'
#     }
#     connector = get_connector('MySQL', sample_config)
#     if connector.connect():
#         executor = QueryExecutor(connector)
#         result = executor.execute_query("SELECT * FROM your_table LIMIT 5")
#         if result:
#             print("查询结果:", result)
#         connector.close()

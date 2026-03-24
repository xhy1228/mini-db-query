# -*- coding: utf-8 -*-

"""
多源数据查询助手 —— 查询执行器模块

Author: 飞书百万（AI助手）
模块作用：根据用户输入的查询语句，通过已连接的数据库连接器执行查询，
并返回查询结果。该模块是数据库交互的核心，为上层 GUI 提供数据获取能力。
"""

import logging
import signal
from typing import List, Dict, Any, Optional
from datetime import datetime, date, time as datetime_time
from decimal import Decimal

from sqlalchemy import text

# 查询超时设置（秒）
QUERY_TIMEOUT = 30
# 查询结果缓存 TTL（秒）
QUERY_CACHE_TTL = 300  # 5分钟

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
    
    def __init__(self, connector, timeout: int = None):
        """
        :param connector: 数据库连接器实例，必须实现 get_connection() 方法
        :param timeout: 查询超时时间（秒），默认使用 QUERY_TIMEOUT
        """
        self.connector = connector
        self.timeout = timeout or QUERY_TIMEOUT
        
    def execute_query(self, query: str, timeout: int = None) -> Optional[List[Dict[str, Any]]]:
        """
        执行传入的 SQL 查询语句，并返回结果集（列表形式，每行为字典）
        :param query: 用户输入的 SQL 查询语句
        :param timeout: 查询超时时间（秒），默认使用实例超时时间
        :return: 查询结果（列表，每个元素为字典形式的行数据），查询失败时返回 None
        """
        if not query or not query.strip():
            logger.warning("查询语句为空或仅包含空格，将不执行。")
            return None
        
        actual_timeout = timeout or self.timeout
        start_time = datetime.now()
        
        try:
            engine = self.connector.get_connection()
            if not engine:
                logger.error("数据库连接未建立，无法执行查询。")
                return None
            
            with engine.connect() as conn:
                # 设置查询超时
                # MySQL: SET SESSION max_execution_time
                # PostgreSQL: SET statement_timeout
                # SQL Server: SET LOCK_TIMEOUT
                dialect = str(engine.dialect.name).lower() if hasattr(engine, 'dialect') else ''
                
                try:
                    if dialect == 'mysql':
                        # MySQL 使用 max_execution_time (毫秒)
                        conn.execute(text(f"SET SESSION max_execution_time = {actual_timeout * 1000}"))
                    elif dialect == 'postgresql':
                        # PostgreSQL 使用 statement_timeout (毫秒)
                        conn.execute(text(f"SET statement_timeout = {actual_timeout * 1000}"))
                    elif dialect == 'mssql':
                        # SQL Server 使用 LOCK_TIMEOUT (毫秒)
                        conn.execute(text(f"SET LOCK_TIMEOUT {actual_timeout * 1000}"))
                    # Oracle 的超时需要在连接字符串中设置
                except Exception as timeout_err:
                    logger.warning(f"设置查询超时失败（将继续执行）: {timeout_err}")
                
                logger.info(f"正在执行查询 (超时: {actual_timeout}s): {query[:50]}...")
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
                    
                    elapsed = (datetime.now() - start_time).total_seconds()
                    logger.info(f"查询执行成功，返回 {len(data)} 行数据，耗时 {elapsed:.2f}s。")
                    return data
                else:
                    logger.info("查询执行成功，无返回数据。")
                    return []
            
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            error_str = str(e).lower()
            
            # 判断是否为超时错误
            if 'timeout' in error_str or 'max_execution_time' in error_str or elapsed >= actual_timeout:
                logger.error(f"查询超时 ({actual_timeout}s): {query[:50]}...")
                raise TimeoutError(f"查询超时，已执行 {elapsed:.1f}s，超过限制 {actual_timeout}s")
            
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

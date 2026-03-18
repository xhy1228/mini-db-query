# -*- coding: utf-8 -*-
"""
SQL Security Validator - SQL安全验证模块

防止SQL注入和危险操作，确保只允许查询语句执行。
"""

import re
import logging
from typing import Tuple, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class SQLSecurityLevel(Enum):
    """SQL安全级别"""
    READ_ONLY = "read_only"          # 只允许SELECT查询
    READ_WRITE = "read_write"        # 允许SELECT/INSERT/UPDATE
    ADMIN = "admin"                  # 管理员级别，允许所有操作


class SQLValidationError(Exception):
    """SQL验证错误"""
    def __init__(self, message: str, error_code: str = "SQL_VALIDATION_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class SQLSecurityValidator:
    """
    SQL安全验证器
    
    功能：
    1. 检测SQL注入攻击
    2. 禁止危险操作（DROP, DELETE, UPDATE, INSERT等）
    3. 限制查询类型（只允许SELECT）
    4. 检测注释注入
    5. 检测多语句执行
    """
    
    # 危险SQL关键字
    DANGEROUS_KEYWORDS = [
        'DROP', 'DELETE', 'UPDATE', 'INSERT', 'TRUNCATE', 
        'ALTER', 'CREATE', 'REPLACE', 'MERGE', 'GRANT', 'REVOKE',
        'EXEC', 'EXECUTE', 'CALL', 'INTO', 'OUTFILE', 'DUMPFILE'
    ]
    
    # SQL注释模式
    COMMENT_PATTERNS = [
        r'--.*$',           # 单行注释 --
        r'/\*.*?\*/',       # 多行注释 /* */
        r'#.*$',            # MySQL注释 #
    ]
    
    # 危险函数
    DANGEROUS_FUNCTIONS = [
        'LOAD_FILE', 'INTO OUTFILE', 'INTO DUMPFILE',
        'BENCHMARK', 'SLEEP', 'PG_SLEEP',
        'XP_CMDSHELL', 'SP_OACREATE', 'SP_OAMETHOD'
    ]
    
    # 允许的查询类型
    ALLOWED_QUERY_TYPES = ['SELECT']
    
    @staticmethod
    def validate(
        sql: str, 
        security_level: SQLSecurityLevel = SQLSecurityLevel.READ_ONLY,
        source: str = "unknown"
    ) -> Tuple[bool, Optional[str]]:
        """
        验证SQL语句安全性
        
        Args:
            sql: SQL语句
            security_level: 安全级别
            source: 来源标识（用于日志）
        
        Returns:
            (is_valid, error_message)
        """
        if not sql or not sql.strip():
            return False, "SQL语句不能为空"
        
        original_sql = sql
        sql_upper = sql.strip().upper()
        
        # 1. 检测注释注入
        is_valid, error = SQLSecurityValidator._check_comments(sql, source)
        if not is_valid:
            return False, error
        
        # 2. 移除注释后再次检查
        sql_no_comments = SQLSecurityValidator._remove_comments(sql)
        sql_upper_no_comments = sql_no_comments.strip().upper()
        
        # 3. 检测多语句执行（分号分隔）
        is_valid, error = SQLSecurityValidator._check_multiple_statements(sql_no_comments, source)
        if not is_valid:
            return False, error
        
        # 4. 根据安全级别检查
        if security_level == SQLSecurityLevel.READ_ONLY:
            # 只读模式：只允许SELECT
            is_valid, error = SQLSecurityValidator._check_read_only(sql_upper_no_comments, source)
            if not is_valid:
                return False, error
        elif security_level == SQLSecurityLevel.READ_WRITE:
            # 读写模式：允许SELECT/INSERT/UPDATE，但禁止其他危险操作
            is_valid, error = SQLSecurityValidator._check_read_write(sql_upper_no_comments, source)
            if not is_valid:
                return False, error
        
        # 5. 检测危险函数
        is_valid, error = SQLSecurityValidator._check_dangerous_functions(sql_upper, source)
        if not is_valid:
            return False, error
        
        # 6. 检测UNION注入
        is_valid, error = SQLSecurityValidator._check_union_injection(sql_upper_no_comments, source)
        if not is_valid:
            return False, error
        
        # 记录验证通过
        logger.info(f"[SQL Validator] Validation passed | Source: {source} | Level: {security_level.value}")
        
        return True, None
    
    @staticmethod
    def _check_comments(sql: str, source: str) -> Tuple[bool, Optional[str]]:
        """检查SQL注释"""
        for pattern in SQLSecurityValidator.COMMENT_PATTERNS:
            matches = re.findall(pattern, sql, re.MULTILINE | re.DOTALL)
            if matches:
                # 允许正常的注释，但不允许可疑的注释模式
                for match in matches:
                    # 检查注释中是否包含危险关键字
                    match_upper = match.upper()
                    for keyword in SQLSecurityValidator.DANGEROUS_KEYWORDS:
                        if keyword in match_upper:
                            logger.warning(
                                f"[SQL Validator] Dangerous keyword in comment detected | "
                                f"Source: {source} | Keyword: {keyword}"
                            )
                            return False, f"SQL注释中包含危险关键字: {keyword}"
        
        return True, None
    
    @staticmethod
    def _remove_comments(sql: str) -> str:
        """移除SQL注释"""
        result = sql
        for pattern in SQLSecurityValidator.COMMENT_PATTERNS:
            result = re.sub(pattern, '', result, flags=re.MULTILINE | re.DOTALL)
        return result
    
    @staticmethod
    def _check_multiple_statements(sql: str, source: str) -> Tuple[bool, Optional[str]]:
        """检查多语句执行"""
        # 简单检查：分号后面是否还有非空白字符
        parts = sql.split(';')
        non_empty_parts = [p.strip() for p in parts if p.strip()]
        
        if len(non_empty_parts) > 1:
            logger.warning(
                f"[SQL Validator] Multiple statements detected | "
                f"Source: {source} | Count: {len(non_empty_parts)}"
            )
            return False, "不允许执行多条SQL语句"
        
        return True, None
    
    @staticmethod
    def _check_read_only(sql_upper: str, source: str) -> Tuple[bool, Optional[str]]:
        """只读模式检查"""
        # 必须以SELECT开头
        if not sql_upper.startswith('SELECT'):
            logger.warning(
                f"[SQL Validator] Non-SELECT statement in READ_ONLY mode | "
                f"Source: {source} | SQL starts with: {sql_upper[:20]}..."
            )
            return False, "只允许执行SELECT查询语句"
        
        # 检查是否包含危险关键字
        for keyword in SQLSecurityValidator.DANGEROUS_KEYWORDS:
            # 使用正则匹配完整单词，避免误判（如 SELECTED 包含 SELECT）
            pattern = r'\b' + keyword + r'\b'
            if re.search(pattern, sql_upper):
                logger.warning(
                    f"[SQL Validator] Dangerous keyword in READ_ONLY mode | "
                    f"Source: {source} | Keyword: {keyword}"
                )
                return False, f"不允许执行包含 {keyword} 的SQL语句"
        
        return True, None
    
    @staticmethod
    def _check_read_write(sql_upper: str, source: str) -> Tuple[bool, Optional[str]]:
        """读写模式检查"""
        # 允许 SELECT, INSERT, UPDATE
        allowed_starts = ['SELECT', 'INSERT', 'UPDATE']
        is_allowed = any(sql_upper.startswith(start) for start in allowed_starts)
        
        if not is_allowed:
            logger.warning(
                f"[SQL Validator] Invalid statement type in READ_WRITE mode | "
                f"Source: {source} | SQL starts with: {sql_upper[:20]}..."
            )
            return False, "只允许执行 SELECT, INSERT, UPDATE 语句"
        
        # 检查危险关键字（排除INSERT/UPDATE）
        dangerous_for_readwrite = [
            'DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 
            'REPLACE', 'MERGE', 'GRANT', 'REVOKE'
        ]
        
        for keyword in dangerous_for_readwrite:
            pattern = r'\b' + keyword + r'\b'
            if re.search(pattern, sql_upper):
                logger.warning(
                    f"[SQL Validator] Dangerous keyword in READ_WRITE mode | "
                    f"Source: {source} | Keyword: {keyword}"
                )
                return False, f"不允许执行包含 {keyword} 的SQL语句"
        
        return True, None
    
    @staticmethod
    def _check_dangerous_functions(sql_upper: str, source: str) -> Tuple[bool, Optional[str]]:
        """检查危险函数"""
        for func in SQLSecurityValidator.DANGEROUS_FUNCTIONS:
            if func in sql_upper:
                logger.warning(
                    f"[SQL Validator] Dangerous function detected | "
                    f"Source: {source} | Function: {func}"
                )
                return False, f"不允许使用危险函数: {func}"
        
        return True, None
    
    @staticmethod
    def _check_union_injection(sql_upper: str, source: str) -> Tuple[bool, Optional[str]]:
        """检查UNION注入"""
        # 检测 UNION SELECT 注入
        union_pattern = r'\bUNION\b.*\bSELECT\b'
        if re.search(union_pattern, sql_upper, re.DOTALL):
            # UNION SELECT 本身不一定是危险的，但需要记录
            logger.info(
                f"[SQL Validator] UNION SELECT detected (allowed but logged) | "
                f"Source: {source}"
            )
        
        return True, None
    
    @staticmethod
    def sanitize_for_log(sql: str, max_length: int = 200) -> str:
        """
        清理SQL用于日志输出（避免敏感信息泄露）
        
        Args:
            sql: SQL语句
            max_length: 最大长度
        
        Returns:
            清理后的SQL
        """
        if not sql:
            return ""
        
        # 移除多余空白
        cleaned = ' '.join(sql.split())
        
        # 截断
        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length] + "..."
        
        return cleaned


def validate_sql_for_miniapp(sql: str, source: str = "miniapp") -> Tuple[bool, Optional[str]]:
    """
    小程序端SQL验证（只读模式）
    
    Args:
        sql: SQL语句
        source: 来源标识
    
    Returns:
        (is_valid, error_message)
    """
    return SQLSecurityValidator.validate(
        sql=sql,
        security_level=SQLSecurityLevel.READ_ONLY,
        source=source
    )


def validate_sql_for_admin(sql: str, source: str = "admin") -> Tuple[bool, Optional[str]]:
    """
    管理端SQL验证（读写模式）
    
    Args:
        sql: SQL语句
        source: 来源标识
    
    Returns:
        (is_valid, error_message)
    """
    return SQLSecurityValidator.validate(
        sql=sql,
        security_level=SQLSecurityLevel.READ_WRITE,
        source=source
    )

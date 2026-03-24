# services/log_cleanup_service.py
# 日志清理服务

import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import and_

logger = logging.getLogger(__name__)


class LogCleanupService:
    """日志清理服务"""
    
    # 默认保留天数
    DEFAULT_RETENTION_DAYS = 30
    
    def __init__(self, db_session):
        self.db = db_session
    
    def cleanup_query_logs(self, days: int = None) -> int:
        """
        清理查询日志
        
        Args:
            days: 保留天数，默认30天
            
        Returns:
            删除的记录数
        """
        days = days or self.DEFAULT_RETENTION_DAYS
        cutoff_date = datetime.now() - timedelta(days=days)
        
        try:
            from models.database import QueryLog
            
            # 删除超过保留期的记录
            deleted = self.db.query(QueryLog).filter(
                QueryLog.created_at < cutoff_date
            ).delete(synchronize_session=False)
            
            self.db.commit()
            
            logger.info(f"[LogCleanup] Deleted {deleted} query logs older than {days} days")
            return deleted
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"[LogCleanup] Failed to cleanup query logs: {e}")
            return 0
    
    def cleanup_operation_logs(self, days: int = None) -> int:
        """
        清理操作日志
        
        Args:
            days: 保留天数，默认30天
            
        Returns:
            删除的记录数
        """
        days = days or self.DEFAULT_RETENTION_DAYS
        cutoff_date = datetime.now() - timedelta(days=days)
        
        try:
            from models.database import OperationLog
            
            deleted = self.db.query(OperationLog).filter(
                OperationLog.created_at < cutoff_date
            ).delete(synchronize_session=False)
            
            self.db.commit()
            
            logger.info(f"[LogCleanup] Deleted {deleted} operation logs older than {days} days")
            return deleted
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"[LogCleanup] Failed to cleanup operation logs: {e}")
            return 0
    
    def cleanup_all(self, days: int = None) -> dict:
        """
        清理所有日志
        
        Returns:
            清理结果统计
        """
        days = days or self.DEFAULT_RETENTION_DAYS
        
        result = {
            'query_logs': self.cleanup_query_logs(days),
            'operation_logs': self.cleanup_operation_logs(days),
            'total': 0
        }
        result['total'] = result['query_logs'] + result['operation_logs']
        
        logger.info(f"[LogCleanup] Total deleted: {result['total']} logs")
        return result
    
    def get_log_stats(self) -> dict:
        """获取日志统计"""
        stats = {}
        
        try:
            from models.database import QueryLog, OperationLog
            
            # 查询日志统计
            stats['query_logs'] = {
                'total': self.db.query(QueryLog).count(),
                'success': self.db.query(QueryLog).filter(QueryLog.status == 'success').count(),
                'failed': self.db.query(QueryLog).filter(QueryLog.status == 'failed').count()
            }
            
            # 操作日志统计
            stats['operation_logs'] = {
                'total': self.db.query(OperationLog).count()
            }
            
            # 计算存储大小(估算)
            from sqlalchemy import func
            query_size = self.db.query(
                func.coalesce(func.sum(func.length(QueryLog.sql_executed)), 0)
            ).scalar() or 0
            
            operation_size = self.db.query(
                func.coalesce(func.sum(func.length(OperationLog.details)), 0)
            ).scalar() or 0
            
            stats['estimated_size_mb'] = round((query_size + operation_size) / 1024 / 1024, 2)
            
        except Exception as e:
            logger.error(f"[LogCleanup] Failed to get stats: {e}")
        
        return stats


def run_auto_cleanup(db_session, days: int = None) -> dict:
    """
    运行自动清理
    
    Args:
        db_session: 数据库会话
        days: 保留天数
        
    Returns:
        清理结果
    """
    service = LogCleanupService(db_session)
    return service.cleanup_all(days)

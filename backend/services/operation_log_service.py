# -*- coding: utf-8 -*-
"""
操作日志服务

用于记录管理员操作审计日志

Author: 飞书百万（AI助手）
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class OperationLogService:
    """操作日志服务"""
    
    # 操作类型
    ACTION_CREATE = 'create'
    ACTION_UPDATE = 'update'
    ACTION_DELETE = 'delete'
    ACTION_QUERY = 'query'
    ACTION_EXPORT = 'export'
    ACTION_LOGIN = 'login'
    ACTION_LOGOUT = 'logout'
    
    # 资源类型
    RESOURCE_SCHOOL = 'school'
    RESOURCE_TEMPLATE = 'template'
    RESOURCE_CONFIG = 'config'
    RESOURCE_USER = 'user'
    RESOURCE_DATABASE = 'database'
    RESOURCE_BINDING = 'binding'
    RESOURCE_FIELD = 'field'
    RESOURCE_CATEGORY = 'category'
    
    @staticmethod
    def create_log(
        db: Session,
        user_id: int,
        username: str,
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        resource_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = 'success',
        error_message: Optional[str] = None
    ) -> Optional[int]:
        """
        创建操作日志
        
        Args:
            db: 数据库会话
            user_id: 操作用户ID
            username: 操作用户名
            action: 操作类型
            resource_type: 资源类型
            resource_id: 资源ID
            resource_name: 资源名称
            details: 操作详情
            ip_address: IP地址
            user_agent: 用户代理
            status: 状态
            error_message: 错误信息
            
        Returns:
            日志ID
        """
        try:
            from models.database import OperationLog
            
            log = OperationLog(
                user_id=user_id,
                username=username,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                resource_name=resource_name,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
                status=status,
                error_message=error_message
            )
            
            db.add(log)
            db.commit()
            
            logger.info(
                f"[OperationLog] User {user_id}({username}) {action} {resource_type}"
                f"{' #' + str(resource_id) if resource_id else ''}"
                f"{' - ' + resource_name if resource_name else ''}"
            )
            
            return log.id
            
        except Exception as e:
            logger.error(f"[OperationLog] Failed to create log: {e}")
            db.rollback()
            return None
    
    @staticmethod
    def get_logs(
        db: Session,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple:
        """
        查询操作日志
        
        Args:
            db: 数据库会话
            user_id: 用户ID过滤
            action: 操作类型过滤
            resource_type: 资源类型过滤
            resource_id: 资源ID过滤
            status: 状态过滤
            start_date: 开始日期
            end_date: 结束日期
            skip: 跳过条数
            limit: 返回条数
            
        Returns:
            (日志列表, 总数)
        """
        try:
            from models.database import OperationLog
            
            query = db.query(OperationLog)
            
            if user_id:
                query = query.filter(OperationLog.user_id == user_id)
            if action:
                query = query.filter(OperationLog.action == action)
            if resource_type:
                query = query.filter(OperationLog.resource_type == resource_type)
            if resource_id:
                query = query.filter(OperationLog.resource_id == resource_id)
            if status:
                query = query.filter(OperationLog.status == status)
            if start_date:
                query = query.filter(OperationLog.created_at >= start_date)
            if end_date:
                query = query.filter(OperationLog.created_at <= end_date)
            
            total = query.count()
            logs = query.order_by(OperationLog.created_at.desc()).offset(skip).limit(limit).all()
            
            return logs, total
            
        except Exception as e:
            logger.error(f"[OperationLog] Failed to get logs: {e}")
            return [], 0
    
    @staticmethod
    def get_user_recent_actions(db: Session, user_id: int, limit: int = 10) -> list:
        """
        获取用户最近操作
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            limit: 返回条数
            
        Returns:
            操作日志列表
        """
        try:
            from models.database import OperationLog
            
            logs = db.query(OperationLog).filter(
                OperationLog.user_id == user_id
            ).order_by(OperationLog.created_at.desc()).limit(limit).all()
            
            return [log.to_dict() for log in logs]
            
        except Exception as e:
            logger.error(f"[OperationLog] Failed to get user actions: {e}")
            return []


# 便捷函数
def log_operation(
    db: Session,
    user_id: int,
    username: str,
    action: str,
    resource_type: str,
    **kwargs
) -> Optional[int]:
    """
    记录操作日志（便捷函数）
    
    用法:
        log_operation(
            db, user_id, username,
            OperationLogService.ACTION_CREATE,
            OperationLogService.RESOURCE_SCHOOL,
            resource_id=school.id,
            resource_name=school.name,
            details={'key': 'value'}
        )
    """
    return OperationLogService.create_log(
        db, user_id, username, action, resource_type, **kwargs
    )

# -*- coding: utf-8 -*-
"""
Operation Log Module - Database storage for operation logs
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, func
from sqlalchemy.orm import Session

from models.database import Base, QueryLog


class OperationLog(Base):
    """Operation log model for database"""
    __tablename__ = "operation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    username = Column(String(50), nullable=True)
    action = Column(String(50), nullable=False)  # login, query, export, config, etc.
    resource_type = Column(String(50), nullable=True)  # user, database, query, school
    resource_id = Column(String(100), nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    status = Column(String(20), default="success")  # success, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "status": self.status,
            "error_message": self.error_message,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }


class LogService:
    """Service for managing operation logs"""
    
    @staticmethod
    def create_operation_log(
        db: Session,
        action: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> OperationLog:
        """Create a new operation log"""
        log = OperationLog(
            user_id=user_id,
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            error_message=error_message
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
    
    @staticmethod
    def create_query_log(
        db: Session,
        query_type: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        database_id: Optional[int] = None,
        database_name: Optional[str] = None,
        sql_content: Optional[str] = None,
        parameters: Optional[dict] = None,
        result_count: Optional[int] = None,
        execution_time_ms: Optional[int] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> QueryLog:
        """Create a new query log"""
        log = QueryLog(
            user_id=user_id,
            username=username,
            query_type=query_type,
            database_id=database_id,
            database_name=database_name,
            sql_content=sql_content,
            parameters=parameters,
            result_count=result_count,
            execution_time_ms=execution_time_ms,
            status=status,
            error_message=error_message,
            ip_address=ip_address
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
    
    @staticmethod
    def get_operation_logs(
        db: Session,
        skip: int = 0,
        limit: int = 50,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[OperationLog]:
        """Get operation logs with filters"""
        query = db.query(OperationLog)
        
        if user_id:
            query = query.filter(OperationLog.user_id == user_id)
        if action:
            query = query.filter(OperationLog.action == action)
        if start_date:
            query = query.filter(OperationLog.created_at >= start_date)
        if end_date:
            query = query.filter(OperationLog.created_at <= end_date)
        
        return query.order_by(OperationLog.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_query_logs(
        db: Session,
        skip: int = 0,
        limit: int = 50,
        user_id: Optional[int] = None,
        database_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[QueryLog]:
        """Get query logs with filters"""
        query = db.query(QueryLog)
        
        if user_id:
            query = query.filter(QueryLog.user_id == user_id)
        if database_id:
            query = query.filter(QueryLog.database_id == database_id)
        if start_date:
            query = query.filter(QueryLog.created_at >= start_date)
        if end_date:
            query = query.filter(QueryLog.created_at <= end_date)
        
        return query.order_by(QueryLog.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_operation_stats(db: Session, days: int = 7) -> dict:
        """Get operation statistics"""
        from datetime import timedelta
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        total_logs = db.query(OperationLog).filter(
            OperationLog.created_at >= start_date
        ).count()
        
        success_logs = db.query(OperationLog).filter(
            OperationLog.created_at >= start_date,
            OperationLog.status == "success"
        ).count()
        
        failed_logs = db.query(OperationLog).filter(
            OperationLog.created_at >= start_date,
            OperationLog.status == "failed"
        ).count()
        
        # Top actions
        top_actions = db.query(
            OperationLog.action,
            func.count(OperationLog.id).label('count')
        ).filter(
            OperationLog.created_at >= start_date
        ).group_by(
            OperationLog.action
        ).order_by(func.count(OperationLog.id).desc()).limit(10).all()
        
        return {
            "total": total_logs,
            "success": success_logs,
            "failed": failed_logs,
            "success_rate": round(success_logs / total_logs * 100, 2) if total_logs > 0 else 0,
            "top_actions": [{"action": a.action, "count": a.count} for a in top_actions]
        }

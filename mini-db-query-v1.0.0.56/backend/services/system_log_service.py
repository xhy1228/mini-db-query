"""
System Log Service - Records system events, performance, and status
"""

import os
import psutil
import platform
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from sqlalchemy.orm import Session

from models.database import Base


class SystemLog(Base):
    """System log model for database"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    log_type = Column(String(50), nullable=False)  # startup, shutdown, error, warning, info, performance
    component = Column(String(50), nullable=False)  # server, database, cache, api
    message = Column(Text, nullable=False)
    details = Column(Text, nullable=True)  # JSON details
    cpu_percent = Column(Float, nullable=True)
    memory_percent = Column(Float, nullable=True)
    disk_percent = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "log_type": self.log_type,
            "component": self.component,
            "message": self.message,
            "details": self.details,
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "disk_percent": self.disk_percent,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }


class SystemLogService:
    """Service for managing system logs"""
    
    @staticmethod
    def get_system_metrics() -> dict:
        """Get current system metrics"""
        try:
            cpu = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:\\').percent
            return {
                "cpu_percent": round(cpu, 2),
                "memory_percent": round(memory, 2),
                "disk_percent": round(disk, 2)
            }
        except:
            return {
                "cpu_percent": 0,
                "memory_percent": 0,
                "disk_percent": 0
            }
    
    @staticmethod
    def create_log(
        db: Session,
        log_type: str,
        component: str,
        message: str,
        details: Optional[str] = None,
        include_metrics: bool = True
    ) -> SystemLog:
        """Create a new system log"""
        metrics = SystemLogService.get_system_metrics() if include_metrics else {}
        
        log = SystemLog(
            log_type=log_type,
            component=component,
            message=message,
            details=details,
            cpu_percent=metrics.get("cpu_percent"),
            memory_percent=metrics.get("memory_percent"),
            disk_percent=metrics.get("disk_percent")
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
    
    @staticmethod
    def log_startup(db: Session):
        """Log system startup"""
        import json
        details = json.dumps({
            "python_version": platform.python_version(),
            "os": f"{platform.system()} {platform.release()}",
            "hostname": platform.node(),
            "timestamp": datetime.utcnow().isoformat()
        })
        return SystemLogService.create_log(
            db=db,
            log_type="startup",
            component="server",
            message="Server started successfully",
            details=details
        )
    
    @staticmethod
    def log_shutdown(db: Session, reason: str = "Normal shutdown"):
        """Log system shutdown"""
        return SystemLogService.create_log(
            db=db,
            log_type="shutdown",
            component="server",
            message=f"Server shutdown: {reason}",
            include_metrics=True
        )
    
    @staticmethod
    def log_error(db: Session, component: str, error_message: str, stack_trace: Optional[str] = None):
        """Log system error"""
        return SystemLogService.create_log(
            db=db,
            log_type="error",
            component=component,
            message=error_message,
            details=stack_trace,
            include_metrics=True
        )
    
    @staticmethod
    def log_warning(db: Session, component: str, message: str, details: Optional[str] = None):
        """Log system warning"""
        return SystemLogService.create_log(
            db=db,
            log_type="warning",
            component=component,
            message=message,
            details=details,
            include_metrics=False
        )
    
    @staticmethod
    def log_info(db: Session, component: str, message: str, details: Optional[str] = None):
        """Log system info"""
        return SystemLogService.create_log(
            db=db,
            log_type="info",
            component=component,
            message=message,
            details=details,
            include_metrics=False
        )
    
    @staticmethod
    def log_performance(db: Session, component: str, metrics: dict):
        """Log performance metrics"""
        import json
        return SystemLogService.create_log(
            db=db,
            log_type="performance",
            component=component,
            message="Performance metrics recorded",
            details=json.dumps(metrics),
            include_metrics=True
        )
    
    @staticmethod
    def get_recent_logs(
        db: Session,
        limit: int = 100,
        log_type: Optional[str] = None,
        component: Optional[str] = None
    ) -> list:
        """Get recent system logs"""
        query = db.query(SystemLog)
        
        if log_type:
            query = query.filter(SystemLog.log_type == log_type)
        if component:
            query = query.filter(SystemLog.component == component)
        
        return query.order_by(SystemLog.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_system_status(db: Session) -> dict:
        """Get current system status"""
        metrics = SystemLogService.get_system_metrics()
        
        # Get last startup time
        last_startup = db.query(SystemLog).filter(
            SystemLog.log_type == "startup"
        ).order_by(SystemLog.created_at.desc()).first()
        
        # Count errors today
        from datetime import date
        today_start = datetime.combine(date.today(), datetime.min.time())
        error_count = db.query(SystemLog).filter(
            SystemLog.log_type == "error",
            SystemLog.created_at >= today_start
        ).count()
        
        return {
            **metrics,
            "last_startup": last_startup.created_at.strftime("%Y-%m-%d %H:%M:%S") if last_startup else None,
            "errors_today": error_count,
            "status": "healthy" if metrics["cpu_percent"] < 90 and metrics["memory_percent"] < 90 else "warning"
        }

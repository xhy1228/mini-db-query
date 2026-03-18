# -*- coding: utf-8 -*-
"""
Logging Middleware - Unified request logging and operation tracking

All API requests are logged with:
- Request ID for tracing
- User info (if authenticated)
- Request parameters
- Response status and time
- Error details (if failed)
"""

import time
import uuid
import json
import logging
from typing import Callable, Optional
from datetime import datetime
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    统一日志中间件
    
    功能：
    1. 为每个请求生成唯一请求ID
    2. 记录请求开始/结束时间
    3. 记录请求参数（敏感信息脱敏）
    4. 记录响应状态和耗时
    5. 错误时记录详细错误信息
    """
    
    # 敏感字段列表（需要脱敏）
    SENSITIVE_FIELDS = ['password', 'pwd', 'secret', 'token', 'key', 'credential']
    
    # 不记录日志的路径（健康检查等）
    SKIP_PATHS = ['/health', '/favicon.ico', '/exports']
    
    # 不记录请求体的路径（文件上传等）
    SKIP_BODY_PATHS = ['/api/user/export', '/api/manage/databases/test']
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 跳过不需要记录的路径
        if any(request.url.path.startswith(p) for p in self.SKIP_PATHS):
            return await call_next(request)
        
        # 生成请求ID
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4())[:8])
        
        # 记录开始时间
        start_time = time.time()
        
        # 获取客户端IP
        client_ip = self._get_client_ip(request)
        
        # 获取请求信息
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)
        
        # 获取请求体（如果需要）
        body_info = None
        if method in ['POST', 'PUT', 'PATCH'] and not any(p in path for p in self.SKIP_BODY_PATHS):
            try:
                body = await request.body()
                if body:
                    body_str = body.decode('utf-8', errors='ignore')
                    try:
                        body_json = json.loads(body_str)
                        body_info = self._mask_sensitive(body_json)
                    except:
                        body_info = body_str[:200]  # 截断
            except:
                pass
        
        # 记录请求开始
        log_data = {
            'request_id': request_id,
            'method': method,
            'path': path,
            'query': query_params if query_params else None,
            'body': body_info,
            'client_ip': client_ip,
            'user_agent': request.headers.get('User-Agent', '')[:100]
        }
        logger.info(f"[{request_id}] >>> {method} {path}")
        
        # 调用下一个处理器
        try:
            response = await call_next(request)
            
            # 计算耗时
            duration_ms = int((time.time() - start_time) * 1000)
            
            # 记录请求完成
            status_code = response.status_code
            status_emoji = '✅' if status_code < 400 else '❌'
            
            logger.info(
                f"[{request_id}] <<< {status_emoji} {method} {path} "
                f"| {status_code} | {duration_ms}ms"
            )
            
            # 添加请求ID到响应头
            response.headers['X-Request-ID'] = request_id
            
            # 如果是错误响应，记录详细信息
            if status_code >= 400:
                logger.warning(
                    f"[{request_id}] Error response: {status_code} | "
                    f"Path: {path} | IP: {client_ip}"
                )
            
            return response
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            
            # 记录异常
            logger.error(
                f"[{request_id}] 💥 {method} {path} | "
                f"Exception: {type(e).__name__}: {str(e)} | "
                f"Duration: {duration_ms}ms | "
                f"IP: {client_ip}",
                exc_info=True
            )
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端真实IP"""
        # 尝试从代理头获取
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        # 直接连接
        if request.client:
            return request.client.host
        
        return 'unknown'
    
    def _mask_sensitive(self, data: dict) -> dict:
        """脱敏敏感字段"""
        if not isinstance(data, dict):
            return data
        
        masked = {}
        for key, value in data.items():
            if any(s in key.lower() for s in self.SENSITIVE_FIELDS):
                masked[key] = '******'
            elif isinstance(value, dict):
                masked[key] = self._mask_sensitive(value)
            elif isinstance(value, list):
                masked[key] = [self._mask_sensitive(v) if isinstance(v, dict) else v for v in value]
            else:
                masked[key] = value
        
        return masked


class OperationLogger:
    """
    操作日志记录器
    
    用于在API中方便地记录操作日志到数据库
    """
    
    @staticmethod
    def log_operation(
        db,
        action: str,
        resource_type: str = None,
        resource_id: str = None,
        details: str = None,
        user_id: int = None,
        username: str = None,
        ip_address: str = None,
        status: str = "success",
        error_message: str = None
    ):
        """
        记录操作日志
        
        Args:
            db: 数据库会话
            action: 操作类型 (login, logout, create_user, update_user, delete_user, 
                           create_school, update_school, delete_school,
                           create_database, update_database, delete_database,
                           create_template, update_template, delete_template,
                           query, export, config_change)
            resource_type: 资源类型 (user, school, database, template, query, system)
            resource_id: 资源ID
            details: 操作详情
            user_id: 用户ID
            username: 用户名
            ip_address: IP地址
            status: 状态 (success, failed)
            error_message: 错误信息
        """
        try:
            from services.log_service import LogService
            LogService.create_operation_log(
                db=db,
                action=action,
                user_id=user_id,
                username=username,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                ip_address=ip_address,
                status=status,
                error_message=error_message
            )
        except Exception as e:
            logger.error(f"Failed to log operation: {e}")
    
    @staticmethod
    def log_login(db, user_id: int, username: str, ip: str, status: str = "success", error: str = None):
        """记录登录"""
        OperationLogger.log_operation(
            db=db,
            action="login",
            resource_type="user",
            resource_id=str(user_id),
            details=f"User {username} logged in",
            user_id=user_id,
            username=username,
            ip_address=ip,
            status=status,
            error_message=error
        )
    
    @staticmethod
    def log_logout(db, user_id: int, username: str, ip: str):
        """记录登出"""
        OperationLogger.log_operation(
            db=db,
            action="logout",
            resource_type="user",
            resource_id=str(user_id),
            details=f"User {username} logged out",
            user_id=user_id,
            username=username,
            ip_address=ip
        )
    
    @staticmethod
    def log_create(db, resource_type: str, resource_id: int, resource_name: str,
                   user_id: int, username: str, ip: str, details: str = None):
        """记录创建操作"""
        OperationLogger.log_operation(
            db=db,
            action=f"create_{resource_type}",
            resource_type=resource_type,
            resource_id=str(resource_id),
            details=details or f"Created {resource_type}: {resource_name}",
            user_id=user_id,
            username=username,
            ip_address=ip
        )
    
    @staticmethod
    def log_update(db, resource_type: str, resource_id: int, resource_name: str,
                   user_id: int, username: str, ip: str, changes: dict = None):
        """记录更新操作"""
        details = f"Updated {resource_type}: {resource_name}"
        if changes:
            details += f" | Changes: {json.dumps(changes, ensure_ascii=False)}"
        
        OperationLogger.log_operation(
            db=db,
            action=f"update_{resource_type}",
            resource_type=resource_type,
            resource_id=str(resource_id),
            details=details,
            user_id=user_id,
            username=username,
            ip_address=ip
        )
    
    @staticmethod
    def log_delete(db, resource_type: str, resource_id: int, resource_name: str,
                   user_id: int, username: str, ip: str):
        """记录删除操作"""
        OperationLogger.log_operation(
            db=db,
            action=f"delete_{resource_type}",
            resource_type=resource_type,
            resource_id=str(resource_id),
            details=f"Deleted {resource_type}: {resource_name}",
            user_id=user_id,
            username=username,
            ip_address=ip
        )
    
    @staticmethod
    def log_export(db, user_id: int, username: str, school_id: int, template_name: str,
                   record_count: int, ip: str, status: str = "success", error: str = None):
        """记录导出操作"""
        OperationLogger.log_operation(
            db=db,
            action="export",
            resource_type="query",
            details=f"Exported {record_count} records from {template_name}",
            user_id=user_id,
            username=username,
            ip_address=ip,
            status=status,
            error_message=error
        )
    
    @staticmethod
    def log_config_change(db, config_key: str, old_value: str, new_value: str,
                          user_id: int, username: str, ip: str):
        """记录配置变更"""
        OperationLogger.log_operation(
            db=db,
            action="config_change",
            resource_type="system",
            resource_id=config_key,
            details=f"Changed {config_key}",
            user_id=user_id,
            username=username,
            ip_address=ip
        )


class SystemLogger:
    """
    系统日志记录器
    
    用于记录系统级别的事件
    """
    
    @staticmethod
    def log_startup(db=None):
        """记录系统启动"""
        logger.info("=" * 60)
        logger.info("System starting up...")
        
        if db:
            try:
                from services.system_log_service import SystemLogService
                SystemLogService.log_startup(db)
                logger.info("System startup logged to database")
            except Exception as e:
                logger.error(f"Failed to log startup: {e}")
    
    @staticmethod
    def log_shutdown(db=None, reason: str = "Normal shutdown"):
        """记录系统关闭"""
        logger.info(f"System shutting down: {reason}")
        
        if db:
            try:
                from services.system_log_service import SystemLogService
                SystemLogService.log_shutdown(db, reason)
            except Exception as e:
                logger.error(f"Failed to log shutdown: {e}")
    
    @staticmethod
    def log_error(db, component: str, error_message: str, stack_trace: str = None):
        """记录系统错误"""
        logger.error(f"[{component}] {error_message}")
        
        if db:
            try:
                from services.system_log_service import SystemLogService
                SystemLogService.log_error(db, component, error_message, stack_trace)
            except Exception as e:
                logger.error(f"Failed to log system error: {e}")
    
    @staticmethod
    def log_warning(db, component: str, message: str, details: str = None):
        """记录系统警告"""
        logger.warning(f"[{component}] {message}")
        
        if db:
            try:
                from services.system_log_service import SystemLogService
                SystemLogService.log_warning(db, component, message, details)
            except Exception as e:
                logger.error(f"Failed to log system warning: {e}")
    
    @staticmethod
    def log_info(db, component: str, message: str, details: str = None):
        """记录系统信息"""
        logger.info(f"[{component}] {message}")
        
        if db:
            try:
                from services.system_log_service import SystemLogService
                SystemLogService.log_info(db, component, message, details)
            except Exception as e:
                logger.error(f"Failed to log system info: {e}")

"""
Rate Limiter Middleware - 已禁用
登录限流功能已移除，不再限制请求频率
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件 - 已禁用，所有请求直接通过"""
    
    async def dispatch(self, request: Request, call_next):
        # 直接放行所有请求，不进行限流
        return await call_next(request)


# 兼容旧代码的函数（空实现）
def reset_rate_limit(ip: str, path: str = None):
    """重置限流 - 空实现"""
    pass


def get_rate_limit_status(ip: str, path: str = None) -> dict:
    """获取限流状态 - 总是返回未限制"""
    return {
        "limited": False,
        "remaining": 999,
        "reset_time": 0
    }

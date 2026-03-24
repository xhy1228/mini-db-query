# core/cache.py
# 简单缓存模块

import time
from typing import Any, Optional, Dict
from threading import Lock
import logging

logger = logging.getLogger(__name__)


class Cache:
    """简单内存缓存"""
    
    def __init__(self, default_ttl: int = 300):
        """
        Args:
            default_ttl: 默认过期时间(秒)，默认5分钟
        """
        self._cache: Dict[str, tuple[Any, float]] = {}
        self._lock = Lock()
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        with self._lock:
            if key not in self._cache:
                return None
            
            value, expire_at = self._cache[key]
            
            # 检查是否过期
            if time.time() > expire_at:
                del self._cache[key]
                return None
            
            return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置缓存"""
        with self._lock:
            expire_at = time.time() + (ttl or self.default_ttl)
            self._cache[key] = (value, expire_at)
    
    def delete(self, key: str):
        """删除缓存"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
    
    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
    
    def cleanup(self):
        """清理过期缓存"""
        with self._lock:
            now = time.time()
            expired_keys = [
                key for key, (_, expire_at) in self._cache.items()
                if now > expire_at
            ]
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.info(f"[Cache] Cleaned up {len(expired_keys)} expired items")
    
    def size(self) -> int:
        """缓存数量"""
        with self._lock:
            return len(self._cache)


# 全局缓存实例
cache = Cache(default_ttl=300)  # 默认5分钟


# 缓存装饰器
def cached(key_prefix: str, ttl: int = 300):
    """缓存装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 生成缓存key
            cache_key = f"{key_prefix}:{args}:{kwargs}"
            
            # 尝试从缓存获取
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"[Cache] Hit: {cache_key}")
                return result
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 存入缓存
            cache.set(cache_key, result, ttl)
            logger.debug(f"[Cache] Set: {cache_key}")
            
            return result
        return wrapper
    return decorator


# 特定缓存实例
class QueryCache:
    """查询结果缓存"""
    
    def __init__(self):
        self.cache = Cache(default_ttl=60)  # 查询缓存1分钟
    
    def get_query_result(self, sql_hash: str) -> Optional[dict]:
        """获取查询结果"""
        return self.cache.get(f"query:{sql_hash}")
    
    def set_query_result(self, sql_hash: str, result: dict, ttl: int = 60):
        """缓存查询结果"""
        self.cache.set(f"query:{sql_hash}", result, ttl)
    
    def invalidate_query(self, sql_hash: str):
        """失效查询缓存"""
        self.cache.delete(f"query:{sql_hash}")
    
    def invalidate_school(self, school_id: int):
        """失效学校相关缓存"""
        # 简单处理：清理所有查询缓存
        self.cache.clear()


query_cache = QueryCache()

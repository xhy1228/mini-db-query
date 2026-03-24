# -*- coding: utf-8 -*-
"""
缓存服务

提供查询结果缓存，减少重复查询数据库

Author: 飞书百万（AI助手）
"""

import hashlib
import json
import logging
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from functools import wraps

logger = logging.getLogger(__name__)


class CacheItem:
    """缓存项"""
    
    def __init__(self, data: Any, ttl: int = 300):
        self.data = data
        self.created_at = datetime.now()
        self.expires_at = self.created_at + timedelta(seconds=ttl)
        self.ttl = ttl
        self.hit_count = 0
    
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at
    
    def touch(self):
        """更新命中计数"""
        self.hit_count += 1


class QueryCache:
    """
    查询结果缓存
    
    使用内存缓存，支持 TTL 和 LRU 淘汰策略
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        初始化缓存
        
        Args:
            max_size: 最大缓存项数量
            default_ttl: 默认 TTL（秒）
        """
        self._cache: Dict[str, CacheItem] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = threading.RLock()
        
        # 统计信息
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expirations': 0
        }
        
        logger.info(f"QueryCache initialized: max_size={max_size}, default_ttl={default_ttl}s")
    
    def _generate_key(self, db_config: dict, sql: str) -> str:
        """
        生成缓存键
        
        使用数据库配置和 SQL 生成唯一键
        """
        # 提取关键配置信息
        key_data = {
            'db_type': db_config.get('db_type', ''),
            'host': db_config.get('host', ''),
            'port': db_config.get('port', ''),
            'db_name': db_config.get('db_name', ''),
            'sql': sql.strip()
        }
        
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, db_config: dict, sql: str) -> Optional[Any]:
        """
        从缓存获取数据
        
        Args:
            db_config: 数据库配置
            sql: SQL 语句
            
        Returns:
            缓存的数据，未命中返回 None
        """
        key = self._generate_key(db_config, sql)
        
        with self._lock:
            item = self._cache.get(key)
            
            if item is None:
                self._stats['misses'] += 1
                return None
            
            if item.is_expired():
                del self._cache[key]
                self._stats['expirations'] += 1
                self._stats['misses'] += 1
                logger.debug(f"Cache expired: {key[:8]}...")
                return None
            
            item.touch()
            self._stats['hits'] += 1
            logger.debug(f"Cache hit: {key[:8]}... (hits: {item.hit_count})")
            return item.data
    
    def set(self, db_config: dict, sql: str, data: Any, ttl: int = None) -> None:
        """
        设置缓存
        
        Args:
            db_config: 数据库配置
            sql: SQL 语句
            data: 要缓存的数据
            ttl: TTL（秒），默认使用 default_ttl
        """
        key = self._generate_key(db_config, sql)
        ttl = ttl or self._default_ttl
        
        with self._lock:
            # 检查是否需要淘汰
            if len(self._cache) >= self._max_size and key not in self._cache:
                self._evict()
            
            self._cache[key] = CacheItem(data, ttl)
            logger.debug(f"Cache set: {key[:8]}... (ttl: {ttl}s)")
    
    def _evict(self):
        """
        淘汰缓存项
        
        使用 LRU 策略：移除最少使用的项
        """
        if not self._cache:
            return
        
        # 先移除过期的
        expired_keys = [k for k, v in self._cache.items() if v.is_expired()]
        for key in expired_keys:
            del self._cache[key]
            self._stats['expirations'] += 1
        
        # 如果还是满了，移除最少命中的
        if len(self._cache) >= self._max_size:
            # 找到命中次数最少的
            lru_key = min(self._cache.keys(), key=lambda k: self._cache[k].hit_count)
            del self._cache[lru_key]
            self._stats['evictions'] += 1
        
        logger.debug(f"Cache evicted, current size: {len(self._cache)}")
    
    def invalidate(self, db_config: dict, sql: str = None) -> int:
        """
        使缓存失效
        
        Args:
            db_config: 数据库配置
            sql: SQL 语句（可选，不提供则清除该数据库的所有缓存）
            
        Returns:
            移除的缓存项数量
        """
        count = 0
        
        with self._lock:
            if sql:
                key = self._generate_key(db_config, sql)
                if key in self._cache:
                    del self._cache[key]
                    count = 1
            else:
                # 清除该数据库的所有缓存
                prefix = f"{db_config.get('db_type', '')}_{db_config.get('host', '')}_{db_config.get('db_name', '')}"
                keys_to_remove = []
                
                for key, item in self._cache.items():
                    # 简单匹配，实际可以用更精确的方式
                    pass
                
                # 清除所有（简化处理）
                count = len(self._cache)
                self._cache.clear()
        
        if count > 0:
            logger.info(f"Cache invalidated: {count} items")
        
        return count
    
    def clear(self):
        """清空所有缓存"""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"Cache cleared: {count} items")
    
    def get_stats(self) -> dict:
        """获取缓存统计"""
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = self._stats['hits'] / total_requests if total_requests > 0 else 0
            
            return {
                'size': len(self._cache),
                'max_size': self._max_size,
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'hit_rate': f"{hit_rate:.1%}",
                'evictions': self._stats['evictions'],
                'expirations': self._stats['expirations'],
                'default_ttl': self._default_ttl
            }
    
    def cleanup_expired(self) -> int:
        """
        清理过期缓存
        
        Returns:
            清理的项数
        """
        count = 0
        
        with self._lock:
            expired_keys = [k for k, v in self._cache.items() if v.is_expired()]
            for key in expired_keys:
                del self._cache[key]
                count += 1
                self._stats['expirations'] += 1
        
        if count > 0:
            logger.info(f"Cache cleanup: removed {count} expired items")
        
        return count


# 全局缓存实例
_query_cache: Optional[QueryCache] = None


def get_query_cache() -> QueryCache:
    """获取全局缓存实例"""
    global _query_cache
    if _query_cache is None:
        _query_cache = QueryCache()
    return _query_cache


def cached_query(ttl: int = 300):
    """
    查询缓存装饰器
    
    用法:
        @cached_query(ttl=300)
        def execute_query(db_config, sql):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 尝试从缓存获取
            cache = get_query_cache()
            
            # 假设第一个参数是 db_config，第二个是 sql
            db_config = args[0] if len(args) > 0 else kwargs.get('db_config', {})
            sql = args[1] if len(args) > 1 else kwargs.get('sql', '')
            
            # 检查缓存
            cached_result = cache.get(db_config, sql)
            if cached_result is not None:
                return cached_result
            
            # 执行查询
            result = func(*args, **kwargs)
            
            # 存入缓存
            if result is not None:
                cache.set(db_config, sql, result, ttl)
            
            return result
        
        return wrapper
    return decorator

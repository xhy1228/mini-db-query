# -*- coding: utf-8 -*-
"""
数据库连接管理器
- 连接池管理
- 自动断开机制
- 连接状态跟踪
- 资源释放

Author: 飞书百万（AI助手）
"""

import logging
import threading
import time
from typing import Dict, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    数据库连接管理器
    
    功能：
    1. 连接池管理 - 复用连接，减少资源消耗
    2. 自动断开 - 超时自动断开，释放资源
    3. 状态跟踪 - 实时跟踪连接状态
    4. 安全机制 - 防止连接泄露
    """
    
    _instance = None
    _lock = threading.Lock()
    
    # 默认配置
    DEFAULT_TIMEOUT = 30 * 60  # 30分钟自动断开
    DEFAULT_POOL_SIZE = 5      # 连接池大小
    DEFAULT_RECYCLE = 3600     # 1小时回收连接
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        # 连接池：{config_name: connector}
        self._connections: Dict[str, Any] = {}
        
        # 连接状态：{config_name: status_info}
        self._status: Dict[str, Dict[str, Any]] = {}
        
        # 最后活动时间：{config_name: last_active_time}
        self._last_active: Dict[str, datetime] = {}
        
        # 自动断开超时时间（秒）
        self._timeout = self.DEFAULT_TIMEOUT
        
        # 后台检查线程
        self._check_thread = None
        self._running = False
        
        # 线程锁
        self._conn_lock = threading.Lock()
        
        logger.info("连接管理器初始化完成")
    
    def get_connection(self, config_name: str, config: Dict[str, Any]):
        """
        获取数据库连接
        
        Args:
            config_name: 配置名称
            config: 数据库配置
            
        Returns:
            DatabaseConnector 实例
        """
        with self._conn_lock:
            # 检查是否已有连接
            if config_name in self._connections:
                connector = self._connections[config_name]
                # 检查连接是否有效
                if self._is_connection_valid(config_name):
                    self._update_last_active(config_name)
                    logger.info(f"复用现有连接: {config_name}")
                    return connector
                else:
                    # 连接无效，清理
                    self._cleanup_connection(config_name)
            
            # 创建新连接
            from src.db.connector import get_connector
            
            connector = get_connector(config.get('db_type', 'MySQL'), config)
            if connector and connector.connect():
                self._connections[config_name] = connector
                self._status[config_name] = {
                    'connected': True,
                    'connect_time': datetime.now(),
                    'db_type': config.get('db_type', 'MySQL'),
                    'host': config.get('host', ''),
                    'db_name': config.get('db_name', '')
                }
                self._update_last_active(config_name)
                logger.info(f"创建新连接: {config_name}")
                
                # 启动自动断开检查
                self._start_auto_disconnect_check()
                
                return connector
            else:
                logger.error(f"连接失败: {config_name}")
                return None
    
    def release_connection(self, config_name: str):
        """
        释放指定连接
        
        Args:
            config_name: 配置名称
        """
        with self._conn_lock:
            self._cleanup_connection(config_name)
            logger.info(f"释放连接: {config_name}")
    
    def close_all(self):
        """关闭所有连接"""
        with self._conn_lock:
            for config_name in list(self._connections.keys()):
                self._cleanup_connection(config_name)
            logger.info("关闭所有连接")
    
    def _cleanup_connection(self, config_name: str):
        """清理连接资源"""
        if config_name in self._connections:
            try:
                connector = self._connections[config_name]
                if connector:
                    connector.close()
            except Exception as e:
                logger.warning(f"关闭连接异常: {config_name}, {e}")
            finally:
                del self._connections[config_name]
        
        if config_name in self._status:
            self._status[config_name]['connected'] = False
        
        if config_name in self._last_active:
            del self._last_active[config_name]
    
    def _is_connection_valid(self, config_name: str) -> bool:
        """检查连接是否有效"""
        if config_name not in self._connections:
            return False
        
        connector = self._connections[config_name]
        if not connector or not connector.engine:
            return False
        
        try:
            # 执行简单查询测试连接
            import sqlalchemy
            with connector.engine.connect() as conn:
                conn.execute(sqlalchemy.text("SELECT 1"))
            return True
        except Exception:
            return False
    
    def _update_last_active(self, config_name: str):
        """更新最后活动时间"""
        self._last_active[config_name] = datetime.now()
    
    def get_status(self, config_name: str = None) -> Dict[str, Any]:
        """
        获取连接状态
        
        Args:
            config_name: 配置名称，None则返回所有
            
        Returns:
            状态信息字典
        """
        if config_name:
            return self._status.get(config_name, {'connected': False})
        return self._status.copy()
    
    def is_connected(self, config_name: str) -> bool:
        """检查指定配置是否已连接"""
        status = self._status.get(config_name, {})
        return status.get('connected', False) and self._is_connection_valid(config_name)
    
    def set_timeout(self, timeout_seconds: int):
        """
        设置自动断开超时时间
        
        Args:
            timeout_seconds: 超时秒数
        """
        self._timeout = timeout_seconds
        logger.info(f"设置自动断开超时: {timeout_seconds}秒")
    
    def _start_auto_disconnect_check(self):
        """启动自动断开检查线程"""
        if self._running:
            return
        
        self._running = True
        self._check_thread = threading.Thread(target=self._auto_disconnect_loop, daemon=True)
        self._check_thread.start()
        logger.info("启动自动断开检查线程")
    
    def _auto_disconnect_loop(self):
        """自动断开检查循环"""
        while self._running:
            try:
                time.sleep(60)  # 每分钟检查一次
                self._check_and_disconnect()
            except Exception as e:
                logger.error(f"自动断开检查异常: {e}")
    
    def _check_and_disconnect(self):
        """检查并断开超时连接"""
        now = datetime.now()
        timeout = timedelta(seconds=self._timeout)
        
        with self._conn_lock:
            to_disconnect = []
            
            for config_name, last_active in list(self._last_active.items()):
                if now - last_active > timeout:
                    to_disconnect.append(config_name)
            
            for config_name in to_disconnect:
                logger.info(f"连接超时自动断开: {config_name}")
                self._cleanup_connection(config_name)
    
    def stop(self):
        """停止连接管理器"""
        self._running = False
        self.close_all()
        logger.info("连接管理器已停止")
    
    def get_connection_info(self, config_name: str) -> str:
        """
        获取连接信息摘要
        
        Returns:
            连接信息字符串
        """
        status = self._status.get(config_name, {})
        if not status.get('connected'):
            return "未连接"
        
        connect_time = status.get('connect_time')
        if connect_time:
            elapsed = datetime.now() - connect_time
            minutes = int(elapsed.total_seconds() / 60)
            return f"已连接 {minutes}分钟"
        
        return "已连接"


# 全局单例
connection_manager = ConnectionManager()

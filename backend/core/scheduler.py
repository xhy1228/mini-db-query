# -*- coding: utf-8 -*-
"""
定时任务调度器

用于日志清理、缓存清理等周期性任务

Author: 飞书百万（AI助手）
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class ScheduledTask:
    """定时任务"""
    
    def __init__(self, name: str, func: Callable, interval_seconds: int, 
                 run_on_start: bool = False):
        """
        Args:
            name: 任务名称
            func: 执行函数
            interval_seconds: 执行间隔（秒）
            run_on_start: 是否在启动时立即执行一次
        """
        self.name = name
        self.func = func
        self.interval_seconds = interval_seconds
        self.run_on_start = run_on_start
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None
        self.run_count = 0
        self.error_count = 0
        self.last_error: Optional[str] = None
    
    def should_run(self) -> bool:
        """检查是否应该执行"""
        if self.last_run is None:
            return True
        
        elapsed = (datetime.now() - self.last_run).total_seconds()
        return elapsed >= self.interval_seconds
    
    def execute(self):
        """执行任务"""
        try:
            logger.info(f"[Scheduler] Running task: {self.name}")
            start_time = time.time()
            
            result = self.func()
            
            elapsed = time.time() - start_time
            self.last_run = datetime.now()
            self.next_run = self.last_run + timedelta(seconds=self.interval_seconds)
            self.run_count += 1
            
            logger.info(f"[Scheduler] Task {self.name} completed in {elapsed:.2f}s, result: {result}")
            
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            logger.error(f"[Scheduler] Task {self.name} failed: {e}", exc_info=True)


class Scheduler:
    """定时任务调度器"""
    
    def __init__(self):
        self._tasks: Dict[str, ScheduledTask] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
    
    def add_task(self, name: str, func: Callable, interval_seconds: int,
                 run_on_start: bool = False) -> None:
        """
        添加定时任务
        
        Args:
            name: 任务名称
            func: 执行函数
            interval_seconds: 执行间隔（秒）
            run_on_start: 是否在启动时立即执行一次
        """
        if name in self._tasks:
            logger.warning(f"[Scheduler] Task {name} already exists, replacing")
        
        self._tasks[name] = ScheduledTask(name, func, interval_seconds, run_on_start)
        logger.info(f"[Scheduler] Task added: {name} (interval: {interval_seconds}s)")
    
    def remove_task(self, name: str) -> bool:
        """移除定时任务"""
        if name in self._tasks:
            del self._tasks[name]
            logger.info(f"[Scheduler] Task removed: {name}")
            return True
        return False
    
    def start(self):
        """启动调度器"""
        if self._running:
            logger.warning("[Scheduler] Already running")
            return
        
        self._running = True
        self._stop_event.clear()
        
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        
        logger.info(f"[Scheduler] Started with {len(self._tasks)} tasks")
        
        # 启动时执行需要立即运行的任务
        for task in self._tasks.values():
            if task.run_on_start:
                threading.Thread(target=task.execute, daemon=True).start()
    
    def stop(self):
        """停止调度器"""
        if not self._running:
            return
        
        self._running = False
        self._stop_event.set()
        
        if self._thread:
            self._thread.join(timeout=5)
        
        logger.info("[Scheduler] Stopped")
    
    def _run_loop(self):
        """主循环"""
        # 检查间隔（秒）
        check_interval = 60
        
        while self._running and not self._stop_event.is_set():
            try:
                self._check_and_run_tasks()
            except Exception as e:
                logger.error(f"[Scheduler] Error in run loop: {e}")
            
            # 等待下一次检查
            self._stop_event.wait(check_interval)
    
    def _check_and_run_tasks(self):
        """检查并执行任务"""
        for task in self._tasks.values():
            if task.should_run():
                # 在独立线程中执行，避免阻塞
                threading.Thread(target=task.execute, daemon=True).start()
    
    def get_status(self) -> dict:
        """获取调度器状态"""
        return {
            'running': self._running,
            'tasks': {
                name: {
                    'interval_seconds': task.interval_seconds,
                    'last_run': task.last_run.isoformat() if task.last_run else None,
                    'next_run': task.next_run.isoformat() if task.next_run else None,
                    'run_count': task.run_count,
                    'error_count': task.error_count,
                    'last_error': task.last_error
                }
                for name, task in self._tasks.items()
            }
        }


# 全局调度器实例
_scheduler: Optional[Scheduler] = None


def get_scheduler() -> Scheduler:
    """获取全局调度器实例"""
    global _scheduler
    if _scheduler is None:
        _scheduler = Scheduler()
    return _scheduler


def start_scheduler():
    """启动调度器并注册默认任务"""
    scheduler = get_scheduler()
    
    # 注册日志清理任务（每天凌晨3点执行）
    # 计算到下一个凌晨3点的秒数
    now = datetime.now()
    next_3am = now.replace(hour=3, minute=0, second=0, microsecond=0)
    if next_3am <= now:
        next_3am += timedelta(days=1)
    initial_delay = (next_3am - now).total_seconds()
    
    # 每24小时执行一次日志清理
    scheduler.add_task(
        name='log_cleanup',
        func=run_log_cleanup,
        interval_seconds=86400,  # 24小时
        run_on_start=False  # 不在启动时执行
    )
    
    # 注册缓存清理任务（每小时执行一次）
    scheduler.add_task(
        name='cache_cleanup',
        func=run_cache_cleanup,
        interval_seconds=3600,  # 1小时
        run_on_start=True
    )
    
    # 启动调度器
    scheduler.start()


def stop_scheduler():
    """停止调度器"""
    global _scheduler
    if _scheduler:
        _scheduler.stop()


def run_log_cleanup() -> dict:
    """
    执行日志清理任务
    
    Returns:
        清理结果
    """
    try:
        from models import get_db_session
        from services.log_cleanup_service import LogCleanupService
        
        db = next(get_db_session())
        try:
            service = LogCleanupService(db)
            result = service.cleanup_all(days=30)  # 保留30天
            
            logger.info(f"[LogCleanup] Cleanup completed: {result}")
            return result
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"[LogCleanup] Cleanup failed: {e}")
        return {'error': str(e)}


def run_cache_cleanup() -> dict:
    """
    执行缓存清理任务
    
    Returns:
        清理结果
    """
    try:
        from services.cache_service import get_query_cache
        
        cache = get_query_cache()
        removed = cache.cleanup_expired()
        
        stats = cache.get_stats()
        
        logger.info(f"[CacheCleanup] Removed {removed} expired items, current stats: {stats}")
        return {
            'removed': removed,
            'stats': stats
        }
        
    except Exception as e:
        logger.error(f"[CacheCleanup] Cleanup failed: {e}")
        return {'error': str(e)}

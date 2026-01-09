"""
同步任务并发限制器
防止大量同步任务占满 Web Worker
"""
import time
import os
from typing import Dict
from threading import Lock
from app.boot import logger


class SyncTaskLimiter:
    """同步任务并发限制器（线程安全）"""
    
    def __init__(self, max_concurrent: int = 10, cleanup_interval: int = 300):
        """
        初始化限制器
        
        Args:
            max_concurrent: 最大并发同步任务数
            cleanup_interval: 清理过期记录的间隔（秒）
        """
        self.max_concurrent = max_concurrent
        self.cleanup_interval = cleanup_interval
        self._tasks: Dict[str, float] = {}  # task_id -> start_time
        self._lock = Lock()
        self._last_cleanup = time.time()
    
    def _cleanup_expired(self, max_age: int = 600):
        """清理超过指定时间的任务记录（默认10分钟）"""
        current_time = time.time()
        
        # 只在间隔时间后才清理
        if current_time - self._last_cleanup < self.cleanup_interval:
            return
        
        with self._lock:
            expired_tasks = [
                task_id for task_id, start_time in self._tasks.items()
                if current_time - start_time > max_age
            ]
            
            for task_id in expired_tasks:
                self._tasks.pop(task_id, None)
            
            if expired_tasks:
                logger.info(f"Cleaned up {len(expired_tasks)} expired sync task records")
            
            self._last_cleanup = current_time
    
    def try_acquire(self, task_id: str) -> bool:
        """
        尝试获取执行权限
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功获取权限
        """
        self._cleanup_expired()
        
        with self._lock:
            # 检查当前并发数
            current_count = len(self._tasks)
            
            if current_count >= self.max_concurrent:
                logger.warning(
                    f"Sync task limit reached: {current_count}/{self.max_concurrent}, "
                    f"rejecting task {task_id}"
                )
                return False
            
            # 记录任务开始时间
            self._tasks[task_id] = time.time()
            logger.debug(f"Sync task {task_id} acquired slot ({current_count + 1}/{self.max_concurrent})")
            return True
    
    def release(self, task_id: str):
        """
        释放执行权限
        
        Args:
            task_id: 任务ID
        """
        with self._lock:
            if task_id in self._tasks:
                elapsed = time.time() - self._tasks[task_id]
                self._tasks.pop(task_id, None)
                logger.debug(f"Sync task {task_id} released slot, took {elapsed:.2f}s")
    
    def get_stats(self) -> Dict:
        """
        获取当前统计信息
        
        Returns:
            dict: 包含当前并发数、最大并发数等信息
        """
        with self._lock:
            current_count = len(self._tasks)
            usage_rate = current_count / self.max_concurrent if self.max_concurrent > 0 else 0
            
            # 根据使用率判断状态
            if usage_rate < 0.8:
                status = "healthy"
            elif usage_rate < 0.95:
                status = "warning"
            else:
                status = "critical"
            
            return {
                "current_concurrent": current_count,
                "max_concurrent": self.max_concurrent,
                "usage_rate": round(usage_rate * 100, 2),  # 转换为百分比
                "status": status,
                "active_task_count": current_count
            }


# 全局实例
# 默认最多 10 个并发同步任务
# 可通过环境变量配置：MAX_SYNC_CONCURRENT
MAX_SYNC_CONCURRENT = int(os.getenv("MAX_SYNC_CONCURRENT", "10"))
sync_task_limiter = SyncTaskLimiter(max_concurrent=MAX_SYNC_CONCURRENT)


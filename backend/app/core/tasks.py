import json
import asyncio
from typing import Callable, Dict
from app.boot import logger
from app.core.redis_pool import RedisPool

# 任务注册表
_TASK_REGISTRY: Dict[str, Callable] = {}

def register_task(name: str):
    """任务注册装饰器"""
    def decorator(func: Callable):
        _TASK_REGISTRY[name] = func
        return func
    return decorator

async def enqueue_task(func_name: str, *args, **kwargs):
    """将任务推入 Redis 队列"""
    payload = {
        "func": func_name,
        "args": args,
        "kwargs": kwargs
    }
    try:
        r = await RedisPool.get_async_redis()
        await r.rpush("sys_task_queue", json.dumps(payload))
        logger.debug(f"[Queue] 已将异步任务 {func_name} 推入队列")
    except Exception as e:
        logger.error(f"[Queue] 异步任务 {func_name} 推入队列失败: {e}")

async def task_worker_loop():
    """异步任务消费 Worker"""
    logger.info("✓ 异步任务队列 Worker 启动成功，监听队列: sys_task_queue")
    while True:
        try:
            r = await RedisPool.get_async_redis()
            # 阻塞读取，超时 5 秒，避免卡死导致应用退出缓慢
            res = await r.blpop("sys_task_queue", timeout=5)
            if not res:
                continue
            
            _, val = res
            payload = json.loads(val)
            func_name = payload.get("func")
            args = payload.get("args", [])
            kwargs = payload.get("kwargs", {})
            
            func = _TASK_REGISTRY.get(func_name)
            if not func:
                logger.error(f"[Worker] 未找到注册的任务函数: {func_name}")
                continue
            
            logger.info(f"[Worker] 开始执行任务: {func_name}")
            start_time = asyncio.get_event_loop().time()
            
            if asyncio.iscoroutinefunction(func):
                await func(*args, **kwargs)
            else:
                from anyio.to_thread import run_sync
                await run_sync(func, *args, **kwargs)
                
            cost = int((asyncio.get_event_loop().time() - start_time) * 1000)
            logger.info(f"✓ [Worker] 任务 {func_name} 执行成功，耗时 {cost}ms")
        except asyncio.CancelledError:
            logger.info("[Worker] 任务队列 Worker 收到停止信号")
            break
        except Exception as e:
            logger.error(f"[Worker] 任务执行过程中出错: {e}")
            await asyncio.sleep(2)

# ─────────────────────────────────────────────────────────────────────────
# 内置任务定义
# ─────────────────────────────────────────────────────────────────────────

@register_task("clean_old_audit_logs")
def clean_old_audit_logs(retention_days: int):
    """自动清理过期审计日志"""
    from app.service import AuditService
    deleted = AuditService.clean_old_logs(retention_days)
    if deleted > 0:
        logger.info(f"[Task] 自动清理过期审计日志已完成，共清理 {deleted} 条记录")

@register_task("send_email")
async def send_email(to_email: str, subject: str, content: str):
    """异步模拟发送邮件"""
    logger.info(f"[Task] 开始向 {to_email} 发送邮件，主题: {subject}...")
    await asyncio.sleep(2.0)  # 模拟网络延时
    logger.info(f"✓ [Task] 邮件成功发送给 {to_email}")

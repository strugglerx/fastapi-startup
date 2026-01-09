"""
访问日志中间件
"""
from fastapi import Request
from app.boot import logger
import time

def setup_access_log(app):
    """设置访问日志中间件"""
    @app.middleware("http")
    async def access_log_middleware(request: Request, call_next):
        start_time = time.time()

        # 记录请求信息
        logger.info(f"➡️  {request.method} {request.url.path}")

        try:
            response = await call_next(request)

            # 计算处理时间
            process_time = (time.time() - start_time) * 1000
            status_code = response.status_code

            # 记录响应信息
            logger.info(f"⬅️  {request.method} {request.url.path} - {status_code} ({process_time:.2f}ms)")

            response.headers["X-Process-Time"] = str(process_time)
            return response

        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            logger.error(f"❌ {request.method} {request.url.path} - Error: {str(e)} ({process_time:.2f}ms)")
            raise

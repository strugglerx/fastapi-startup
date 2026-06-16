import time
from fastapi import FastAPI, Request
from app.boot import logger

_SKIP_LOG_PREFIXES = ("/docs", "/openapi.json", "/redoc", "/doc/", "/health", "/favicon.ico")


def setup_access_log(app: FastAPI):
    @app.middleware("http")
    async def access_log_middleware(request: Request, call_next):
        path = request.url.path
        skip = any(path.startswith(p) for p in _SKIP_LOG_PREFIXES)

        start_time = time.time()

        if not skip:
            logger.info(f"-> {request.method} {path}")

        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000
            response.headers["X-Process-Time"] = f"{process_time:.2f}ms"

            if not skip:
                logger.info(f"<- {request.method} {path} {response.status_code} ({process_time:.2f}ms)")

            return response

        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            logger.error(f"!! {request.method} {path} Error: {e} ({process_time:.2f}ms)")
            raise

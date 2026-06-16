import os
import warnings
from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI

from .config import app_config
from .plugins import setup_cors, setup_stand_response, setup_exception, setup_custom_server
from app.middleware import setup_access_log
from .static import mount_static
from .doc import setup_docs
from .openapi import custom_openapi
from .logger import logger

warnings.filterwarnings("ignore", category=UserWarning, message=".*validate_default.*", module="pydantic")


class ExtendedFastAPI(FastAPI):
    def use(self, plugin: Callable):
        """Vue 风格的 use() —— app.use(setup_cors).use(setup_xxx)"""
        plugin(self)
        return self


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动
    try:
        mount_static(app)
        logger.info("静态资源已挂载到 /")
    except Exception as e:
        logger.error(f"静态资源挂载失败: {e}")

    if os.getenv("APP_ENV") != "production":
        try:
            from app.library.debug import generate_route_md
            generate_route_md(app)
        except Exception as e:
            logger.debug(f"路由文档生成跳过: {e}")

    yield

    # 关闭
    logger.info("应用已关闭")


def create_app() -> FastAPI:
    is_prod = os.getenv("APP_ENV") == "production"

    app = ExtendedFastAPI(
        debug=app_config.debug,
        title="engine",
        version="1.1.0",
        json_as_ascii=False,
        docs_url=None if is_prod else "/docs",
        openapi_url=None if is_prod else "/openapi.json",
        lifespan=lifespan,
    )

    # 内层 → 外层（FastAPI 中间件执行顺序与挂载顺序相反）
    app.use(setup_stand_response)
    app.use(setup_exception)
    app.use(setup_docs)
    app.use(setup_custom_server)
    app.use(setup_access_log)
    app.use(setup_cors)  # 最外层：先处理 OPTIONS / 跨域头

    app.use(lambda a: logger.info(f"所有插件已加载: {a.title}"))

    custom_openapi(app)
    return app

from fastapi import FastAPI
from .config import app_config
from .middleware import setup_cors,setup_stand_response,setup_exception,setup_custom_server
from app.middleware import setup_access_log
from .static import serve_static
from typing import Callable
from .doc import setup_docs
import os
import warnings

# 忽略 llama-index 库中的 Pydantic validate_default 警告（这是第三方库的问题）
warnings.filterwarnings("ignore", category=UserWarning, message=".*validate_default.*", module="pydantic")

class ExtendedFastAPI(FastAPI):
    def use(self, plugin: Callable):
        """
        类Vue的use()方法，用于挂载插件
        用法：app.use(setup_cors)
        """
        plugin(self)
        return self  # 支持链式调用

def create_app() -> FastAPI:
    app = ExtendedFastAPI(
        debug=app_config.debug,
        title="engine",
        version="1.0.0", 
        json_as_ascii=False,
        docs_url=None if os.getenv("APP_ENV") == "production" else "/docs",
        openapi_url=None if os.getenv("APP_ENV") == "production" else "/openapi.json",
    )

    app.use(setup_cors)
    app.use(setup_stand_response)
    app.use(setup_exception)
    app.use(setup_docs)
    app.use(serve_static)
    app.use(setup_custom_server)
    app.use(setup_access_log)
    app.use(lambda app: print(f"所有插件已加载: {app.title}"))
        
    
    return app
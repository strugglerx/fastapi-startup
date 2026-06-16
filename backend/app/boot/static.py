from fastapi import FastAPI
from pathlib import Path
from fastapi.staticfiles import StaticFiles


def mount_static(app: FastAPI) -> None:
    """把前端打包产物挂到根路径。

    必须在所有 include_router 之后调用，否则根路径的 mount 会优先匹配，
    所有 API 都会被 StaticFiles 拦截。本项目由 boot.application.lifespan
    启动阶段调用，那时 main.py 已把全部 router 注册完毕。
    """
    static_dir = Path.cwd() / 'app/public'
    app.mount("/", StaticFiles(directory=str(static_dir)), name="static")

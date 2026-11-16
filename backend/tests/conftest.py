"""测试全局守卫。

两道闸：
1. conftest 由 pytest 保证在所有测试模块 import 之前加载；
2. import app.db 后硬断言 engine 是 SQLite —— 不是就中止整个测试会话，
   绝不可误触外部/生产库。
"""
import os

os.environ["APP_USE_SQLITE"] = "true"

from app.db import engine  # noqa: E402

if engine.url.get_backend_name() != "sqlite":
    raise RuntimeError(
        f"测试拒绝运行：engine 是 {engine.url.get_backend_name()}（{engine.url.host}），"
        "不是 SQLite。检查是否有模块在 conftest 之前 import 了 app.db。"
    )


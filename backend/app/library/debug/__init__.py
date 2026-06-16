from typing import Union
from pathlib import Path

from fastapi import FastAPI

from app.paths import ROUTES_MD_PATH


def generate_route_md(app: FastAPI, filename: Union[str, Path, None] = None):
    """生成路由总览 Markdown。

    默认输出到 backend/routes.md（绝对路径，不受启动 cwd 影响）；
    传入 filename 时按传入路径写入。
    """
    target = Path(filename) if filename else ROUTES_MD_PATH
    with open(target, "w") as f:
        f.write("# 路由文档\n\n| 路径 | 方法 | 名称 |\n|------|------|------|\n")
        for route in app.routes:
            if hasattr(route, "methods"):
                methods = ",".join(route.methods)
                path = route.path
                name = getattr(route, "name", "")
                f.write(f"| `{path}` | {methods} | {name} |\n")

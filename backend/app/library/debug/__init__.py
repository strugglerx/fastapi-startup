from fastapi import FastAPI

def generate_route_md(app: FastAPI, filename: str = "routes.md"):
    with open(filename, "w") as f:
        f.write("# 路由文档\n\n| 路径 | 方法 | 名称 |\n|------|------|------|\n")
        for route in app.routes:
            if hasattr(route, "methods"):
                methods = ",".join(route.methods)
                path = route.path
                name = getattr(route, "name", "")
                f.write(f"| `{path}` | {methods} | {name} |\n")
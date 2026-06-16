from fastapi import FastAPI
from fastapi.responses import FileResponse
from pathlib import Path


def setup_docs(app: FastAPI):
    """注册 RapiDoc 文档页 /doc/rapidoc。

    必须同步注册——项目改用 lifespan= 后，Starlette 会忽略所有
    @app.on_event("startup") 钩子，路由也注册不上。
    """
    docs_dir = Path("./auto_docs")
    docs_dir.mkdir(exist_ok=True)

    rapidoc_html = f"""<!DOCTYPE html>
<html>
<head>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/rapidoc/9.3.8/rapidoc-min.js"></script>
</head>
<body>
    <rapi-doc spec-url="{app.openapi_url}" sort-tags="true" schema-style="table"></rapi-doc>
</body>
</html>"""

    rapidoc_path = docs_dir / "rapidoc.html"
    rapidoc_path.write_text(rapidoc_html)

    @app.get("/doc/rapidoc", include_in_schema=False)
    async def doc():
        return FileResponse(rapidoc_path)

'''
Description: 
Author: Moqi
Date: 2025-07-04 10:49:41
Email: str@li.cm
Github: https://github.com/strugglerx
LastEditors: Moqi
LastEditTime: 2025-07-04 11:27:16
'''
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import json

# 自动生成并挂载三大文档系统
def setup_docs(app: FastAPI):
    # 应用启动时自动设置
    @app.on_event("startup")
    async def on_startup():
        docs_dir = Path("./auto_docs")
        docs_dir.mkdir(exist_ok=True)
        # 3. 自动生成RapiDoc（/rapidoc）
        rapidoc_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/rapidoc/9.3.8/rapidoc-min.js"></script>
        </head>
        <body>
            <rapi-doc spec-url="{app.openapi_url}" sort-tags="true" schema-style="table"  ></rapi-doc>
        </body>
        </html>
        """
        rapidocPath = docs_dir / "rapidoc.html"
        Path(rapidocPath).write_text(rapidoc_html)
        @app.get("/doc/rapidoc", include_in_schema=False)  # 从Swagger文档隐藏
        async def doc():
            return FileResponse(rapidocPath)
        
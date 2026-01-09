'''
Description: 
Author: Moqi
Date: 2025-07-02 22:47:34
Email: str@li.cm
Github: https://github.com/strugglerx
LastEditors: Moqi
LastEditTime: 2025-11-26 11:12:11
'''
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from app.api.v1.deps import allow_local_only

router = APIRouter(tags=["公开接口"])

@router.get("/", include_in_schema=False)  # 从Swagger文档隐藏
async def serve_frontend():
    """返回前端入口文件"""
    return FileResponse("app/public/index.html")

@router.get("/api/health",name="服务健康检查",dependencies=[Depends(allow_local_only)])
async def health_check():
    """服务健康检查接口"""
    return {"status": "ok"}
"""
Hello World 示例接口
Base Scaffold 的入门示例
"""
from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter(tags=["示例"])

@router.get("/hello", summary="Hello World 接口")
async def hello_world() -> Dict[str, Any]:
    """
    Base Scaffold 示例接口

    返回欢迎信息，用于测试API是否正常运行
    """
    return {
        "message": "Hello, base scaffold!",
        "status": "success",
        "version": "1.0.0",
        "docs": "/docs"
    }

@router.get("/ping", summary="健康检查")
async def ping() -> Dict[str, str]:
    """
    简单的健康检查接口
    """
    return {"status": "ok"}

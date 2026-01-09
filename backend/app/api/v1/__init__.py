"""
Base Scaffold API v1 路由
清理后只保留核心功能和示例接口
"""
from fastapi import APIRouter
from . import hello

# 创建主路由
router = APIRouter(prefix="/api/v1")

# 只包含示例接口
router.include_router(hello.router, tags=["示例"])

# 显式导出
__all__ = ["router"]

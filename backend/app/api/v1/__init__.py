from fastapi import APIRouter
from . import hello, user

router = APIRouter(prefix="/api/v1")

router.include_router(hello.router, tags=["示例"])
router.include_router(user.router)

__all__ = ["router"]

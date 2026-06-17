from fastapi import APIRouter
from . import hello, user, auth, admin, me, role

router = APIRouter(prefix="/api/v1")

router.include_router(hello.router, tags=["示例"])
router.include_router(auth.router)
router.include_router(me.router)
router.include_router(admin.router)
router.include_router(role.router)
router.include_router(user.router)  # 兼容旧 /api/v1/user/*，后续可下线

__all__ = ["router"]

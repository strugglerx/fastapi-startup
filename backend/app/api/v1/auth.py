"""认证接口 —— 登录 / 当前用户 / 登出

前端契约对齐：
  POST /api/v1/auth/login   {email, password}  -> {token, user}
  GET  /api/v1/auth/me                          -> user
  POST /api/v1/auth/logout                      -> {ok: true}  (无状态 JWT，no-op)
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.v1.deps import get_current_user, RateLimiter
from app.service import UserService

router = APIRouter(prefix="/auth", tags=["认证"])


class LoginReq(BaseModel):
    email:    str = Field(..., description="email 或 username")
    password: str = Field(..., min_length=1, max_length=128)


@router.post("/login", summary="后台登录", dependencies=[Depends(RateLimiter(limit=10, window=60, name="login"))])
async def login(req: LoginReq):
    return UserService.login(req.email, req.password)


@router.get("/me", summary="当前登录用户")
async def me(user=Depends(get_current_user)):
    return UserService.get_me(user)


@router.post("/logout", summary="登出（无状态 JWT，no-op）")
async def logout():
    return {"ok": True}

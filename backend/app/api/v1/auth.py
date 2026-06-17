"""认证接口 —— 登录 / 当前用户 / 登出 / 找回密码 / Token 续期"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.v1.deps import get_current_user, RateLimiter
from app.service import UserService

router = APIRouter(prefix="/auth", tags=["认证"])


class LoginReq(BaseModel):
    email:    str = Field(..., description="email 或 username")
    password: str = Field(..., min_length=1, max_length=128)


class ForgotPasswordReq(BaseModel):
    email: str = Field(..., max_length=120)


class ResetPasswordReq(BaseModel):
    email:        str = Field(..., max_length=120)
    code:         str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=8, max_length=128)


@router.post("/login", summary="后台登录", dependencies=[Depends(RateLimiter(limit=10, window=60, name="login"))])
async def login(req: LoginReq):
    return UserService.login(req.email, req.password)


@router.get("/me", summary="当前登录用户")
async def me(user=Depends(get_current_user)):
    return UserService.get_me(user)


@router.post("/logout", summary="登出（无状态 JWT，no-op）")
async def logout():
    return {"ok": True}


@router.post(
    "/refresh",
    summary="续期 Token（仅当当前 token 临近过期时换发）",
    dependencies=[Depends(RateLimiter(limit=30, window=60, name="refresh"))],
)
async def refresh(user=Depends(get_current_user)):
    return UserService.refresh_token(user)


@router.post(
    "/forgot-password",
    summary="发送密码重置验证码（SMTP 未配置时返回 503 友好提示）",
    dependencies=[Depends(RateLimiter(limit=5, window=60, name="forgot_password"))],
)
async def forgot_password(req: ForgotPasswordReq):
    return UserService.request_password_reset(req.email)


@router.post(
    "/reset-password",
    summary="用邮箱验证码重置密码",
    dependencies=[Depends(RateLimiter(limit=10, window=60, name="reset_password_public"))],
)
async def reset_password(req: ResetPasswordReq):
    return UserService.confirm_password_reset(req.email, req.code, req.new_password)

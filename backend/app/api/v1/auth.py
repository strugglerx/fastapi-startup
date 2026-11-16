"""认证接口 —— 登录 / 当前用户 / 登出 / 找回密码 / Token 续期

双 token 方案：
  - access  : 短期 JWT（默认 8h），无状态
  - refresh : opaque 随机串（默认 30d），sha256 落库可吊销可 rotate

端点速览：
  /auth/login          —— 登录，返回 access + refresh
  /auth/refresh        —— 旧路径，access 仍未过期时滑动续期（兼容老前端）
  /auth/refresh-token  —— 新路径，access 已过期但 refresh 有效时换发新对（rotate）
  /auth/logout         —— 吊销当前 refresh（如携带）
"""
from typing import Optional

from fastapi import APIRouter, Body, Depends, Request
from pydantic import BaseModel, Field

from app.api.v1.deps import get_current_user, get_current_user_no_err, RateLimiter
from app.service import UserService

router = APIRouter(prefix="/auth", tags=["认证"])


# ─────────────────────────── Pydantic Schemas ───────────────────────────
class LoginReq(BaseModel):
    email:    str = Field(..., description="email 或 username")
    password: str = Field(..., min_length=1, max_length=128)


class ForgotPasswordReq(BaseModel):
    email: str = Field(..., max_length=120)


class ResetPasswordReq(BaseModel):
    email:        str = Field(..., max_length=120)
    code:         str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=8, max_length=128)


class RefreshTokenReq(BaseModel):
    refresh_token: str = Field(..., min_length=10, max_length=256, description="登录时拿到的 refresh_token")


class LogoutReq(BaseModel):
    refresh_token: Optional[str] = Field(default=None, max_length=256)


# ─────────────────────────── Helpers ───────────────────────────
def _client_meta(request: Request) -> dict:
    """从 Request 抽出 ua / ip 元数据，传给 service 落 refresh_tokens 审计字段。

    IP 走 `core.limiter.get_client_ip`：受信代理白名单内才信任 XFF / X-Real-IP，
    否则强制 socket 对端 —— 防止攻击者伪造 header 把登录爆破 / refresh 风控
    打到任意 IP 桶。
    """
    from app.core.limiter import get_client_ip
    ua = (request.headers.get("user-agent") or "")[:255]
    ip = get_client_ip(request)
    if ip == "unknown":
        ip = ""
    return {"ua": ua or None, "client_ip": (ip or "")[:64] or None}


# ─────────────────────────── Routes ───────────────────────────
@router.post(
    "/login",
    summary="后台登录",
    dependencies=[Depends(RateLimiter(limit=10, window=60, name="login"))],
)
async def login(req: LoginReq, request: Request):
    return UserService.login(req.email, req.password, **_client_meta(request))


@router.get("/me", summary="当前登录用户")
async def me(user=Depends(get_current_user)):
    return UserService.get_me(user)


@router.post("/logout", summary="登出 —— 吊销携带的 refresh_token；token 缺失不阻断")
async def logout(
    request: Request,
    req: Optional[LogoutReq] = Body(default=None),
    _user=Depends(get_current_user_no_err),
):
    refresh = req.refresh_token if req else None
    return UserService.revoke_refresh_token(refresh)


@router.post(
    "/refresh",
    summary="滑动续期（旧路径：access 仍有效时换发新 access + 新 refresh）",
    dependencies=[Depends(RateLimiter(limit=30, window=60, name="refresh"))],
)
async def refresh(request: Request, user=Depends(get_current_user)):
    return UserService.refresh_token(user, **_client_meta(request))


@router.post(
    "/refresh-token",
    summary="用 refresh_token 换发新对（access 已过期场景，rotate 旧 refresh）",
    dependencies=[Depends(RateLimiter(limit=30, window=60, name="refresh_token"))],
)
async def refresh_token(req: RefreshTokenReq, request: Request):
    return UserService.refresh_with_refresh_token(req.refresh_token, **_client_meta(request))


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

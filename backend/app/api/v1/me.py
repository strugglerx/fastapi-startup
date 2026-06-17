"""当前用户视角的菜单 / 权限 / 个人资料 / 改密"""
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.v1.deps import require_login, RateLimiter
from app.service import UserService

router = APIRouter(prefix="/me", tags=["当前用户"])


class UpdateProfileReq(BaseModel):
    full_name: Optional[str] = Field(None, max_length=80)
    email:     Optional[str] = Field(None, max_length=120)


class ChangePasswordReq(BaseModel):
    old_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=6, max_length=128)


@router.get("/profile", summary="当前用户资料（alias to /auth/me）")
async def my_profile(user=Depends(require_login)):
    return UserService.get_me(user)


@router.put("/profile", summary="修改自己的资料（full_name / email）")
async def update_my_profile(req: UpdateProfileReq, user=Depends(require_login)):
    return UserService.update_self_profile(
        user.id, full_name=req.full_name, email=req.email,
    )


@router.put(
    "/password",
    summary="修改自己的密码（需提供当前密码）",
    dependencies=[Depends(RateLimiter(limit=5, window=60, name="change_password"))],
)
async def change_my_password(req: ChangePasswordReq, user=Depends(require_login)):
    return UserService.change_password(
        user.id, old_password=req.old_password, new_password=req.new_password,
    )

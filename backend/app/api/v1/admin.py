"""后台管理员 CRUD —— 全部需要管理员权限

role 字段不再硬编码 admin|member，改为 service 层动态查 sys_role。
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.api.v1.deps import get_current_user, require_permission, RateLimiter
from app.service import UserService

router = APIRouter(prefix="/admins", tags=["管理员"])


# code 校验交给 service 层（运行时查 sys_role）
_ROLE_PATTERN = r"^[a-zA-Z0-9_\-]{2,32}$"


class CreateAdminReq(BaseModel):
    username:  str           = Field(..., min_length=3, max_length=50)
    password:  str           = Field(..., min_length=6, max_length=128)
    email:     Optional[str] = Field(None, max_length=120)
    full_name: Optional[str] = Field(None, max_length=80)
    role:      str           = Field("admin", pattern=_ROLE_PATTERN)


class UpdateAdminReq(BaseModel):
    username:  Optional[str]  = Field(None, min_length=3, max_length=50)
    email:     Optional[str]  = Field(None, max_length=120)
    full_name: Optional[str]  = Field(None, max_length=80)
    role:      Optional[str]  = Field(None, pattern=_ROLE_PATTERN)
    is_active: Optional[bool] = None


class ResetPasswordReq(BaseModel):
    new_password: str = Field(..., min_length=6, max_length=128)


@router.get("", summary="账号列表（分页，支持按 role / is_active 过滤）")
async def list_admins(
    page:      int           = Query(1, ge=1),
    size:      int           = Query(20, ge=1, le=100),
    keyword:   Optional[str] = Query(None),
    role:      Optional[str] = Query(None, pattern=_ROLE_PATTERN),
    is_active: Optional[bool] = Query(None),
    _user=Depends(require_permission("system:admin")),
):
    return UserService.list_admins(
        page=page, size=size, keyword=keyword, role=role, is_active=is_active,
    )


@router.post("", summary="创建账号")
async def create_admin(req: CreateAdminReq, _admin=Depends(require_permission("system:admin:create"))):
    return UserService.create_admin(
        username=req.username,
        password=req.password,
        email=req.email,
        full_name=req.full_name,
        role=req.role,
    )


@router.put("/{user_id}", summary="更新账号信息")
async def update_admin(
    user_id: int,
    req: UpdateAdminReq,
    actor=Depends(require_permission("system:admin:update")),
):
    return UserService.update_admin(
        user_id,
        username=req.username,
        email=req.email,
        full_name=req.full_name,
        role=req.role,
        is_active=req.is_active,
        actor=actor,
    )


@router.post(
    "/{user_id}/reset-password",
    summary="重置密码",
    dependencies=[Depends(RateLimiter(limit=10, window=60, name="reset_password"))],
)
async def reset_password(user_id: int, req: ResetPasswordReq, _admin=Depends(require_permission("system:admin:password"))):
    return UserService.reset_password(user_id, req.new_password)


@router.delete(
    "/{user_id}",
    summary="删除账号",
    dependencies=[Depends(RateLimiter(limit=20, window=60, name="delete_admin"))],
)
async def delete_admin(user_id: int, actor=Depends(require_permission("system:admin:delete"))):
    return UserService.delete_admin(user_id, actor=actor)

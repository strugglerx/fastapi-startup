"""
用户接口路由 —— 薄 Controller 示范

约定：
- 不写业务逻辑（DB 查询、规则判断都在 service 层）
- 只做：参数解析 → 调 service → 返回结果
- 鉴权用 Depends；业务异常由 service 抛 APIException，框架自动处理
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.api.v1.deps import get_current_user, require_admin
from app.service import UserService

router = APIRouter(prefix="/user", tags=["用户"])


# ──────────── Pydantic Schemas ────────────
class RegisterReq(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)


class LoginReq(BaseModel):
    username: str
    password: str


# ──────────── Routes ────────────
@router.post("/register", summary="注册新用户")
async def register(req: RegisterReq):
    return UserService.register(req.username, req.password)


@router.post("/login", summary="用户登录")
async def login(req: LoginReq):
    return UserService.login(req.username, req.password)


@router.get("/me", summary="当前登录用户")
async def me(user=Depends(get_current_user)):
    return {"id": user.id, "username": user.username, "fixed": user.fixed}


@router.get("/list", summary="用户列表（仅管理员）")
async def user_list(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    _admin=Depends(require_admin),
):
    return UserService.list_users(page=page, size=size, keyword=keyword)


@router.delete("/{user_id}", summary="删除用户（仅管理员）")
async def delete_user(user_id: int, _admin=Depends(require_admin)):
    return UserService.delete_user(user_id)

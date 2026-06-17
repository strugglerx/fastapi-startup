import os
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, Query, Request
from pydantic import BaseModel, Field, field_validator

from app.api.v1.deps import require_admin, require_login, get_current_user_no_err, is_admin
from app.boot import APIException
from app.service.menu_service import MenuService


router = APIRouter(prefix="/api/menu", tags=["动态菜单"])


class PageMetaReq(BaseModel):
    menuKey: str = Field(..., min_length=1, max_length=128)
    path: str = Field(..., min_length=1, max_length=255)
    component: str = Field(..., min_length=1, max_length=255)
    cacheable: bool = False
    parentKey: Optional[str] = None
    title: Optional[str] = None
    icon: Optional[str] = None
    sort: Optional[int] = None
    hidden: Optional[bool] = None

    @field_validator("component")
    @classmethod
    def validate_component(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("组件路径不能为空")
        if v == "__group__":
            return v
        import re
        if not re.match(r"^[a-zA-Z0-9_\-/]+$", v):
            raise ValueError("组件路径只能包含英文字母、数字、下划线、斜杠和短横线")
        return v


class SyncMenuReq(BaseModel):
    pages: List[PageMetaReq] = Field(default_factory=list)


class RoleGrantsReq(BaseModel):
    role: str = Field(..., min_length=1, max_length=64)
    menuKeys: List[str] = Field(default_factory=list)


async def require_sync_token(
    request: Request,
    authorization: Optional[str] = Header(None),
    token_header: Optional[str] = Header(None, alias="Token"),
):
    expected = os.getenv("SYNC_TOKEN", "")
    token = authorization or ""
    if token.lower().startswith("bearer "):
        token = token[7:]
        
    if expected and token == expected:
        return True
        
    user = await get_current_user_no_err(request, token_header)
    if user and is_admin(user):
        return True
        
    if expected:
        raise APIException("SYNC_TOKEN 无效或需要管理员权限", code=61004, status_code=403)
    else:
        # 如果没有配置 SYNC_TOKEN，但在开发环境之外，也强制需要管理员权限
        if token != "":
            raise APIException("需要管理员权限以执行同步", code=61004, status_code=403)
        return True


@router.get("/list", summary="动态菜单列表")
async def list_menus(include_disabled: bool = Query(False), user=Depends(require_login)):
    if include_disabled and user.role != "admin":
        raise APIException("仅管理员可查看禁用菜单", code=61008, status_code=403)
    return MenuService.list_enabled(user_role=user.role, include_disabled=include_disabled)


@router.get("/role-grants", summary="查询角色的菜单授权")
async def get_role_grants(role: str, _admin=Depends(require_admin)):
    return MenuService.get_role_grants(role)


@router.put("/role-grants", summary="覆盖式设置角色的菜单授权")
async def put_role_grants(req: RoleGrantsReq, _admin=Depends(require_admin)):
    return MenuService.set_role_grants(req.role, req.menuKeys)


@router.post("/sync", summary="同步动态菜单")
async def sync_menus(req: SyncMenuReq, _ok=Depends(require_sync_token)):
    return MenuService.sync([item.model_dump() for item in req.pages])


class UpdateMetaReq(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=128)
    icon: Optional[str] = Field(None, max_length=64)
    parentKey: Optional[str] = Field(None, max_length=128)
    sort: Optional[int] = None
    hidden: Optional[bool] = None


class CreateGroupReq(BaseModel):
    menuKey: str = Field(..., min_length=3, max_length=128)
    title: str = Field(..., min_length=1, max_length=128)
    icon: Optional[str] = Field(None, max_length=64)
    parentKey: Optional[str] = Field(None, max_length=128)
    sort: int = 9999


@router.patch("/{menu_key}", summary="更新菜单运维字段")
async def update_meta(menu_key: str, req: UpdateMetaReq, _admin=Depends(require_admin)):
    fields = req.model_fields_set
    return MenuService.update_meta(
        menu_key,
        title=req.title if "title" in fields else None,
        icon=req.icon if "icon" in fields else None,
        parent_key=req.parentKey if "parentKey" in fields else None,
        sort=req.sort if "sort" in fields else None,
        hidden=req.hidden if "hidden" in fields else None,
    )


@router.post("/groups", summary="新建分组")
async def create_group(req: CreateGroupReq, _admin=Depends(require_admin)):
    return MenuService.create_group(
        menu_key=req.menuKey,
        title=req.title,
        icon=req.icon,
        parent_key=req.parentKey,
        sort=req.sort,
    )


@router.delete("/{id:int}", summary="删除菜单", dependencies=[Depends(require_admin)])
async def delete_menu(id: int):
    return MenuService.delete_menu(id)



class MenuReq(BaseModel):
    menuKey: str = Field(..., min_length=1, max_length=128)
    parentKey: Optional[str] = Field(None, max_length=128)
    title: str = Field(..., min_length=1, max_length=128)
    path: str = Field(..., min_length=1, max_length=255)
    component: str = Field(..., min_length=1, max_length=255)
    icon: Optional[str] = Field(None, max_length=64)
    sort: int = 0
    hidden: bool = False
    cacheable: bool = False
    enabled: bool = True

    @field_validator("component")
    @classmethod
    def validate_component(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("组件路径不能为空")
        if v == "__group__":
            return v
        import re
        if not re.match(r"^[a-zA-Z0-9_\-/]+$", v):
            raise ValueError("组件路径只能包含英文字母、数字、下划线、斜杠和短横线")
        return v


@router.post("/", summary="创建菜单", dependencies=[Depends(require_admin)])
async def create_menu(req: MenuReq):
    return MenuService.create_menu(req.model_dump())


@router.put("/{id:int}", summary="修改菜单", dependencies=[Depends(require_admin)])
async def update_menu(id: int, req: MenuReq):
    return MenuService.update_menu(id, req.model_dump())





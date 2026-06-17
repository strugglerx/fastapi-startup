from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.v1.deps import require_admin
from app.service import RoleService


router = APIRouter(prefix="/role", tags=["角色"])


class CreateRoleReq(BaseModel):
    code: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=64)
    description: Optional[str] = Field(None, max_length=255)
    sort: int = 0


class UpdateRoleReq(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=64)
    description: Optional[str] = Field(None, max_length=255)
    enabled: Optional[bool] = None
    sort: Optional[int] = None


@router.get("", summary="角色列表")
async def list_roles(_admin=Depends(require_admin)):
    return RoleService.list()


@router.post("", summary="新建角色")
async def create_role(req: CreateRoleReq, _admin=Depends(require_admin)):
    return RoleService.create(req.code, req.name, req.description, req.sort)


@router.put("/{id_}", summary="更新角色")
async def update_role(id_: int, req: UpdateRoleReq, _admin=Depends(require_admin)):
    return RoleService.update(
        id_,
        name=req.name,
        description=req.description,
        enabled=req.enabled,
        sort=req.sort,
    )


@router.delete("/{id_}", summary="删除角色")
async def delete_role(id_: int, _admin=Depends(require_admin)):
    RoleService.delete(id_)
    return {"id": id_, "deleted": True}

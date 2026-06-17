from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from app.api.v1.deps import require_permission, require_login
from app.service.dict_service import DictService

router = APIRouter(prefix="/dicts", tags=["数据字典"])

class CreateDictReq(BaseModel):
    code: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=64)
    description: Optional[str] = Field(None, max_length=255)

class UpdateDictReq(BaseModel):
    name: Optional[str] = Field(None, max_length=64)
    description: Optional[str] = Field(None, max_length=255)
    enabled: Optional[bool] = None

class CreateDictItemReq(BaseModel):
    label: str = Field(..., min_length=1, max_length=128)
    value: str = Field(..., min_length=1, max_length=128)
    sort: int = Field(0)

class UpdateDictItemReq(BaseModel):
    label: Optional[str] = Field(None, max_length=128)
    value: Optional[str] = Field(None, max_length=128)
    sort: Optional[int] = None
    enabled: Optional[bool] = None

@router.get("", summary="获取所有字典列表")
async def list_dicts(_user=Depends(require_permission("system:dict:list"))):
    return DictService.list_dicts()

@router.post("", summary="创建字典分类")
async def create_dict(req: CreateDictReq, _user=Depends(require_permission("system:dict:update"))):
    return DictService.create_dict(req.code, req.name, req.description)

@router.put("/{dict_id}", summary="更新字典分类")
async def update_dict(dict_id: int, req: UpdateDictReq, _user=Depends(require_permission("system:dict:update"))):
    return DictService.update_dict(dict_id, name=req.name, description=req.description, enabled=req.enabled)

@router.delete("/{dict_id}", summary="删除字典分类")
async def delete_dict(dict_id: int, _user=Depends(require_permission("system:dict:update"))):
    DictService.delete_dict(dict_id)
    return {"success": True}

@router.get("/{dict_code}/items", summary="获取字典明细项列表")
async def list_items(dict_code: str, _user=Depends(require_permission("system:dict:list"))):
    return DictService.list_items(dict_code)

@router.post("/{dict_code}/items", summary="创建字典明细项")
async def create_item(dict_code: str, req: CreateDictItemReq, _user=Depends(require_permission("system:dict:update"))):
    return DictService.create_item(dict_code, req.label, req.value, req.sort)

@router.put("/items/{item_id}", summary="更新字典明细项")
async def update_item(item_id: int, req: UpdateDictItemReq, _user=Depends(require_permission("system:dict:update"))):
    return DictService.update_item(item_id, label=req.label, value=req.value, sort=req.sort, enabled=req.enabled)

@router.delete("/items/{item_id}", summary="删除字典明细项")
async def delete_item(item_id: int, _user=Depends(require_permission("system:dict:update"))):
    DictService.delete_item(item_id)
    return {"success": True}

@router.get("/options/{dict_code}", summary="获取字典下拉选项（全登录用户可用）")
async def get_options(dict_code: str, _user=Depends(require_login)):
    return DictService.get_dict_options(dict_code)

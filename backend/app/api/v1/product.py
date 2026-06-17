from fastapi import APIRouter, Depends, Query, Request
from app.api.v1.deps import get_current_user, require_permission
from app.service.product_service import ProductService
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter(prefix="/product", tags=["产品管理"])

class ProductCreate(BaseModel):
    name: str = Field(..., description='产品名称')
    price: float = Field(..., description='产品单价')
    status: int = Field(..., description='状态')
    description: str = Field(..., description='描述')

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, description='产品名称')
    price: Optional[float] = Field(None, description='产品单价')
    status: Optional[int] = Field(None, description='状态')
    description: Optional[str] = Field(None, description='描述')

@router.get("", summary="获取产品管理列表")
async def get_list(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1),
    name: Optional[str] = Query(None, description='产品名称'),
    price: Optional[float] = Query(None, description='产品单价'),
    status: Optional[int] = Query(None, description='状态'),
    description: Optional[str] = Query(None, description='描述'),
    user = Depends(get_current_user)
):
    filters = {{
        "name": name,
        "price": price,
        "status": status,
        "description": description,
    }}
    rows, total = ProductService.get_list(page=page, size=size, **filters)
    return {"list": rows, "total": total}

@router.post("", summary="新建产品管理", dependencies=[Depends(require_permission("system:product:create"))])
async def create(req: ProductCreate, request: Request, user = Depends(get_current_user)):
    return ProductService.create(req.model_dump(), user_id=user.id)

@router.put("/{id}", summary="更新产品管理", dependencies=[Depends(require_permission("system:product:update"))])
async def update(id: int, req: ProductUpdate):
    return ProductService.update(id, req.model_dump(exclude_unset=True))

@router.delete("/{id}", summary="删除产品管理", dependencies=[Depends(require_permission("system:product:delete"))])
async def delete(id: int):
    ProductService.delete(id)
    return {"success": True}

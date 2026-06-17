from typing import List, Optional, Tuple
from sqlalchemy import desc
import sqlalchemy as sa
from app.db import SessionLocal, SysProduct
from app.boot import APIException

class ProductService:
    @classmethod
    def get_list(cls, page: int = 1, size: int = 10, **filters) -> Tuple[List[SysProduct], int]:
        with SessionLocal() as db:
            q = db.query(SysProduct)
            for k, v in filters.items():
                if v is not None and v != "":
                    if hasattr(SysProduct, k):
                        col = getattr(SysProduct, k)
                        if isinstance(col.type, (sa.String, sa.Text)):
                            q = q.filter(col.like(f"%{v}%"))
                        else:
                            q = q.filter(col == v)
            total = q.count()
            rows = q.order_by(desc(SysProduct.id)).offset((page - 1) * size).limit(size).all()
            return rows, total

    @classmethod
    def create(cls, data: dict, user_id: Optional[int] = None) -> SysProduct:
        with SessionLocal() as db:
            row = SysProduct(**data)
            if user_id:
                row.created_by = user_id
            db.add(row)
            db.commit()
            db.refresh(row)
            return row

    @classmethod
    def update(cls, id: int, data: dict) -> SysProduct:
        with SessionLocal() as db:
            row = db.query(SysProduct).filter(SysProduct.id == id).first()
            if not row:
                raise APIException(msg="记录不存在", code=404, status_code=404)
            for k, v in data.items():
                if hasattr(row, k):
                    setattr(row, k, v)
            db.commit()
            db.refresh(row)
            return row

    @classmethod
    def delete(cls, id: int) -> bool:
        with SessionLocal() as db:
            row = db.query(SysProduct).filter(SysProduct.id == id).first()
            if not row:
                raise APIException(msg="记录不存在", code=404, status_code=404)
            db.delete(row)
            db.commit()
            return True

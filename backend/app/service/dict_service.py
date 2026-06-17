from typing import Optional, List, Dict, Any
from sqlalchemy import desc
from app.db import SessionLocal, SysDict, SysDictItem
from app.boot import APIException

class DictService:
    @classmethod
    def list_dicts(cls) -> List[dict]:
        with SessionLocal() as db:
            rows = db.query(SysDict).order_by(SysDict.id.desc()).all()
            return [
                {
                    "id": r.id,
                    "code": r.code,
                    "name": r.name,
                    "description": r.description,
                    "enabled": bool(r.enabled),
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ]

    @classmethod
    def create_dict(cls, code: str, name: str, description: Optional[str] = None) -> dict:
        code = (code or "").strip()
        name = (name or "").strip()
        if not code or not name:
            raise APIException("编码和名称不能为空", code=400, status_code=400)
            
        with SessionLocal() as db:
            existing = db.query(SysDict).filter(SysDict.code == code).first()
            if existing:
                raise APIException(f"字典编码 {code} 已存在", code=400, status_code=400)
                
            row = SysDict(
                code=code,
                name=name,
                description=description,
                enabled=True
            )
            db.add(row)
            db.commit()
            db.refresh(row)
            return {
                "id": row.id,
                "code": row.code,
                "name": row.name,
                "description": row.description,
                "enabled": bool(row.enabled)
            }

    @classmethod
    def update_dict(cls, dict_id: int, name: Optional[str] = None, description: Optional[str] = None, enabled: Optional[bool] = None) -> dict:
        with SessionLocal() as db:
            row = db.query(SysDict).filter(SysDict.id == dict_id).first()
            if not row:
                raise APIException("字典分类不存在", code=404, status_code=404)
                
            if name is not None:
                row.name = name.strip()
            if description is not None:
                row.description = description.strip()
            if enabled is not None:
                row.enabled = bool(enabled)
                
            db.commit()
            db.refresh(row)
            return {
                "id": row.id,
                "code": row.code,
                "name": row.name,
                "description": row.description,
                "enabled": bool(row.enabled)
            }

    @classmethod
    def delete_dict(cls, dict_id: int):
        with SessionLocal() as db:
            row = db.query(SysDict).filter(SysDict.id == dict_id).first()
            if not row:
                raise APIException("字典分类不存在", code=404, status_code=404)
                
            try:
                # 删除分类下的所有项
                db.query(SysDictItem).filter(SysDictItem.dict_code == row.code).delete(synchronize_session=False)
                db.delete(row)
                db.commit()
            except Exception as e:
                db.rollback()
                raise e

    # ─────────────────────────────────────────────────────────────────────────
    # 字典项 (Dict Items) CRUD
    # ─────────────────────────────────────────────────────────────────────────

    @classmethod
    def list_items(cls, dict_code: str) -> List[dict]:
        with SessionLocal() as db:
            rows = db.query(SysDictItem).filter(SysDictItem.dict_code == dict_code).order_by(SysDictItem.sort.asc(), SysDictItem.id.asc()).all()
            return [
                {
                    "id": r.id,
                    "dict_code": r.dict_code,
                    "label": r.label,
                    "value": r.value,
                    "sort": r.sort,
                    "enabled": bool(r.enabled),
                }
                for r in rows
            ]

    @classmethod
    def create_item(cls, dict_code: str, label: str, value: str, sort: int = 0) -> dict:
        dict_code = (dict_code or "").strip()
        label = (label or "").strip()
        value = (value or "").strip()
        if not dict_code or not label or not value:
            raise APIException("参数不完整", code=400, status_code=400)
            
        with SessionLocal() as db:
            existing = db.query(SysDictItem).filter(
                SysDictItem.dict_code == dict_code,
                SysDictItem.value == value
            ).first()
            if existing:
                raise APIException(f"字典项值 {value} 已存在", code=400, status_code=400)
                
            row = SysDictItem(
                dict_code=dict_code,
                label=label,
                value=value,
                sort=sort,
                enabled=True
            )
            db.add(row)
            db.commit()
            db.refresh(row)
            return {
                "id": row.id,
                "dict_code": row.dict_code,
                "label": row.label,
                "value": row.value,
                "sort": row.sort,
                "enabled": bool(row.enabled)
            }

    @classmethod
    def update_item(cls, item_id: int, label: Optional[str] = None, value: Optional[str] = None, sort: Optional[int] = None, enabled: Optional[bool] = None) -> dict:
        with SessionLocal() as db:
            row = db.query(SysDictItem).filter(SysDictItem.id == item_id).first()
            if not row:
                raise APIException("字典项不存在", code=404, status_code=404)
                
            if label is not None:
                row.label = label.strip()
            if value is not None:
                # 检查同一 code 下 value 是否冲突
                if value.strip() != row.value:
                    existing = db.query(SysDictItem).filter(
                        SysDictItem.dict_code == row.dict_code,
                        SysDictItem.value == value.strip(),
                        SysDictItem.id != item_id
                    ).first()
                    if existing:
                        raise APIException(f"字典项值 {value} 已存在", code=400, status_code=400)
                    row.value = value.strip()
            if sort is not None:
                row.sort = int(sort)
            if enabled is not None:
                row.enabled = bool(enabled)
                
            db.commit()
            db.refresh(row)
            return {
                "id": row.id,
                "dict_code": row.dict_code,
                "label": row.label,
                "value": row.value,
                "sort": row.sort,
                "enabled": bool(row.enabled)
            }

    @classmethod
    def delete_item(cls, item_id: int):
        with SessionLocal() as db:
            row = db.query(SysDictItem).filter(SysDictItem.id == item_id).first()
            if not row:
                raise APIException("字典项不存在", code=404, status_code=404)
            db.delete(row)
            db.commit()

    @classmethod
    def get_dict_options(cls, dict_code: str) -> List[dict]:
        """为前端下拉组件快速获取启用的字典项"""
        with SessionLocal() as db:
            # 首先确认字典分类是启用状态
            dict_cat = db.query(SysDict).filter(SysDict.code == dict_code, SysDict.enabled == True).first()
            if not dict_cat:
                return []
                
            rows = db.query(SysDictItem).filter(
                SysDictItem.dict_code == dict_code,
                SysDictItem.enabled == True
            ).order_by(SysDictItem.sort.asc(), SysDictItem.id.asc()).all()
            
            return [{"label": r.label, "value": r.value} for r in rows]

"""角色 Service —— sys_role CRUD + active code cache."""
import re
import time
from typing import Optional, Set, Tuple

from sqlalchemy import func

from app.boot import APIException
from app.db import SessionLocal, SysRole, SysRoleMenu, User


ROLE_CODE_RE = re.compile(r"^[a-z][a-z0-9_-]*$")
_active_codes_cache: Optional[Tuple[float, Set[str]]] = None


def _role_to_dict(row: SysRole, *, user_count: int = 0, grants_count: int = 0) -> dict:
    return {
        "id": row.id,
        "code": row.code,
        "name": row.name,
        "description": row.description,
        "enabled": bool(row.enabled),
        "builtin": bool(row.builtin),
        "sort": row.sort or 0,
        "user_count": user_count,
        "grants_count": grants_count,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


class RoleService:
    @classmethod
    def _validate_code(cls, code: str) -> str:
        code = (code or "").strip()
        if not code or len(code) > 64 or not ROLE_CODE_RE.match(code):
            raise APIException("角色 code 格式不正确", code=20012, status_code=400)
        return code

    @classmethod
    def _validate_name(cls, name: str) -> str:
        name = (name or "").strip()
        if not name:
            raise APIException("角色名称不能为空", code=20013, status_code=400)
        return name

    @classmethod
    def list(cls) -> list[dict]:
        with SessionLocal() as db:
            roles = db.query(SysRole).order_by(SysRole.sort.asc(), SysRole.id.asc()).all()
            codes = [row.code for row in roles]
            user_counts = dict(
                db.query(User.role, func.count(User.id))
                .filter(User.deleted_at.is_(None), User.role.in_(codes))
                .group_by(User.role)
                .all()
            ) if codes else {}
            grants_counts = dict(
                db.query(SysRoleMenu.role, func.count(SysRoleMenu.id))
                .filter(SysRoleMenu.role.in_(codes))
                .group_by(SysRoleMenu.role)
                .all()
            ) if codes else {}
            return [
                _role_to_dict(row, user_count=user_counts.get(row.code, 0), grants_count=grants_counts.get(row.code, 0))
                for row in roles
            ]

    @classmethod
    def get(cls, id_: int) -> dict:
        with SessionLocal() as db:
            row = db.query(SysRole).filter(SysRole.id == id_).first()
            if not row:
                raise APIException("角色不存在", code=20014, status_code=404)
            user_count = db.query(User).filter(User.deleted_at.is_(None), User.role == row.code).count()
            grants_count = db.query(SysRoleMenu).filter(SysRoleMenu.role == row.code).count()
            return _role_to_dict(row, user_count=user_count, grants_count=grants_count)

    @classmethod
    def get_by_code(cls, code: str) -> Optional[dict]:
        code = (code or "").strip()
        if not code:
            return None
        with SessionLocal() as db:
            row = db.query(SysRole).filter(SysRole.code == code).first()
            if not row:
                return None
            user_count = db.query(User).filter(User.deleted_at.is_(None), User.role == row.code).count()
            grants_count = db.query(SysRoleMenu).filter(SysRoleMenu.role == row.code).count()
            return _role_to_dict(row, user_count=user_count, grants_count=grants_count)

    @classmethod
    def create(cls, code, name, description=None, sort=0) -> dict:
        code = cls._validate_code(code)
        name = cls._validate_name(name)
        with SessionLocal() as db:
            if db.query(SysRole).filter(SysRole.code == code).first():
                raise APIException("角色 code 已存在", code=20011, status_code=400)
            row = SysRole(
                code=code,
                name=name,
                description=(description or "").strip() or None,
                enabled=True,
                builtin=False,
                sort=int(sort or 0),
            )
            db.add(row)
            db.commit()
            db.refresh(row)
            cls.invalidate_cache()
            return _role_to_dict(row)

    @classmethod
    def update(cls, id_, *, name=None, description=None, enabled=None, sort=None) -> dict:
        with SessionLocal() as db:
            row = db.query(SysRole).filter(SysRole.id == id_).first()
            if not row:
                raise APIException("角色不存在", code=20014, status_code=404)
            if row.builtin and enabled is False:
                raise APIException("内置角色不可停用", code=20015, status_code=400)
            if name is not None:
                row.name = cls._validate_name(name)
            if description is not None:
                row.description = description.strip() or None
            if enabled is not None:
                row.enabled = bool(enabled)
            if sort is not None:
                row.sort = int(sort)
            db.commit()
            db.refresh(row)
            cls.invalidate_cache()
            return _role_to_dict(row)

    @classmethod
    def delete(cls, id_) -> None:
        with SessionLocal() as db:
            row = db.query(SysRole).filter(SysRole.id == id_).first()
            if not row:
                raise APIException("角色不存在", code=20014, status_code=404)
            if row.builtin:
                raise APIException("内置角色不可删除", code=20016, status_code=400)
            used_count = db.query(User).filter(User.deleted_at.is_(None), User.role == row.code).count()
            if used_count:
                raise APIException("请先迁移用户", code=20017, status_code=400)
            try:
                db.query(SysRoleMenu).filter(SysRoleMenu.role == row.code).delete(synchronize_session=False)
                row.enabled = False
                db.commit()
            except Exception:
                db.rollback()
                raise
            cls.invalidate_cache()

    @classmethod
    def ensure_seed_roles(cls) -> None:
        seeds = [
            ("admin", "管理员", "拥有全部菜单与配置权", True, True, 0),
            ("member", "成员", "默认成员账号", True, True, 10),
        ]
        with SessionLocal() as db:
            changed = False
            for code, name, description, enabled, builtin, sort in seeds:
                row = db.query(SysRole).filter(SysRole.code == code).first()
                if row:
                    row.name = name
                    row.description = description
                    row.enabled = enabled
                    row.builtin = builtin
                    row.sort = sort
                else:
                    db.add(SysRole(
                        code=code,
                        name=name,
                        description=description,
                        enabled=enabled,
                        builtin=builtin,
                        sort=sort,
                    ))
                changed = True
            if changed:
                db.commit()
        cls.invalidate_cache()

    @classmethod
    def get_active_codes(cls) -> set[str]:
        global _active_codes_cache
        now = time.monotonic()
        if _active_codes_cache and now - _active_codes_cache[0] < 60:
            return set(_active_codes_cache[1]) | {"admin"}
        with SessionLocal() as db:
            codes = {
                row.code
                for row in db.query(SysRole.code).filter(SysRole.enabled == True).all()  # noqa: E712
            }
        codes.add("admin")
        _active_codes_cache = (now, codes)
        return set(codes)

    @classmethod
    def invalidate_cache(cls):
        global _active_codes_cache
        _active_codes_cache = None

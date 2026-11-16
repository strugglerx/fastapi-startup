"""管理员账号 CRUD mixin + 终端用户注册 + legacy 别名（list_users / delete_user）。"""
from datetime import datetime
from typing import Optional

from sqlalchemy import or_

from app.boot import APIException
from app.core.security import get_password_hash, validate_password_strength
from app.db import SessionLocal, User
from app.service.role_service import RoleService

from ._helpers import _normalize_email, _user_to_dict


class _AdminCrudMixin:

    # ── 终端用户注册（保留旧接口；后台管理员请用 create_admin）──
    @classmethod
    def register(cls, username: str, password: str) -> dict:
        username = (username or "").strip()
        if len(username) < 3:
            raise APIException("用户名至少 3 个字符", code=10001)
        validate_password_strength(password)

        with SessionLocal() as db:
            if db.query(User).filter(User.username == username, User.deleted_at.is_(None)).first():
                raise APIException("用户名已存在", code=10003)

            # 释放已软删除账号的唯一约束冲突
            sd_users = db.query(User).filter(User.username == username, User.deleted_at.isnot(None)).all()
            for sdu in sd_users:
                ts = int(sdu.deleted_at.timestamp()) if sdu.deleted_at else int(datetime.now().timestamp())
                suffix = f"_del_{ts}_{sdu.id}"
                sdu.username = f"{sdu.username[:50 - len(suffix)]}{suffix}"

            user = User(
                username=username,
                hashed_password=get_password_hash(password),
                role="member",
                fixed=False,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return _user_to_dict(user)

    # ── 管理员 CRUD ──
    @classmethod
    def create_admin(
        cls,
        *,
        username: str,
        password: str,
        email: Optional[str] = None,
        full_name: Optional[str] = None,
        role: str = "admin",
    ) -> dict:
        username = (username or "").strip()
        if len(username) < 3:
            raise APIException("用户名至少 3 个字符", code=10001, status_code=400)
        validate_password_strength(password)
        if role not in RoleService.get_active_codes():
            raise APIException("角色不存在或已停用", code=10007, status_code=400)

        email_norm = _normalize_email(email)

        with SessionLocal() as db:
            if db.query(User).filter(User.username == username, User.deleted_at.is_(None)).first():
                raise APIException("用户名已存在", code=10003, status_code=409)
            if email_norm and db.query(User).filter(User.email == email_norm, User.deleted_at.is_(None)).first():
                raise APIException("邮箱已存在", code=10008, status_code=409)

            # 释放已软删除账号的唯一约束冲突
            sd_users = db.query(User).filter(User.username == username, User.deleted_at.isnot(None)).all()
            for sdu in sd_users:
                ts = int(sdu.deleted_at.timestamp()) if sdu.deleted_at else int(datetime.now().timestamp())
                suffix = f"_del_{ts}_{sdu.id}"
                sdu.username = f"{sdu.username[:50 - len(suffix)]}{suffix}"

            if email_norm:
                sd_emails = db.query(User).filter(User.email == email_norm, User.deleted_at.isnot(None)).all()
                for sde in sd_emails:
                    ts = int(sde.deleted_at.timestamp()) if sde.deleted_at else int(datetime.now().timestamp())
                    suffix = f"_del_{ts}_{sde.id}"
                    sde.email = f"{sde.email[:120 - len(suffix)]}{suffix}"

            u = User(
                username=username,
                email=email_norm,
                full_name=(full_name or "").strip() or None,
                role=role,
                hashed_password=get_password_hash(password),
                fixed=False,
                is_active=True,
            )
            db.add(u)
            db.commit()
            db.refresh(u)
            return _user_to_dict(u)

    @classmethod
    def list_admins(
        cls,
        page: int = 1,
        size: int = 20,
        keyword: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> dict:
        page = max(1, page)
        size = max(1, min(size, 100))

        with SessionLocal() as db:
            q = db.query(User).filter(User.deleted_at.is_(None))
            if role:
                q = q.filter(User.role == role)
            if is_active is not None:
                q = q.filter(User.is_active == is_active)
            if keyword:
                kw = f"%{keyword.strip()}%"
                q = q.filter(or_(User.email.ilike(kw), User.username.ilike(kw)))

            total = q.count()
            rows = q.order_by(User.id.desc()).offset((page - 1) * size).limit(size).all()
            return {
                "total": total,
                "page":  page,
                "size":  size,
                "items": [_user_to_dict(u) for u in rows],
            }

    @classmethod
    def update_admin(
        cls,
        user_id: int,
        *,
        username: Optional[str] = None,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        actor: Optional[User] = None,
    ) -> dict:
        with SessionLocal() as db:
            u = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
            if not u:
                raise APIException("账号不存在", code=10005, status_code=404)

            if username is not None:
                username = username.strip()
                if len(username) < 3:
                    raise APIException("用户名至少 3 个字符", code=10001, status_code=400)
                dup = db.query(User).filter(User.username == username, User.id != u.id, User.deleted_at.is_(None)).first()
                if dup:
                    raise APIException("用户名已存在", code=10003, status_code=409)
                
                # 释放已软删除账号的唯一约束冲突
                sd_users = db.query(User).filter(User.username == username, User.id != u.id, User.deleted_at.isnot(None)).all()
                for sdu in sd_users:
                    ts = int(sdu.deleted_at.timestamp()) if sdu.deleted_at else int(datetime.now().timestamp())
                    suffix = f"_del_{ts}_{sdu.id}"
                    sdu.username = f"{sdu.username[:50 - len(suffix)]}{suffix}"
                
                u.username = username
            if full_name is not None:
                u.full_name = full_name.strip() or None
            if email is not None:
                email_norm = _normalize_email(email)
                if email_norm:
                    dup = db.query(User).filter(User.email == email_norm, User.id != u.id, User.deleted_at.is_(None)).first()
                    if dup:
                        raise APIException("邮箱已被占用", code=10008, status_code=409)
                    
                    # 释放已软删除账号的唯一约束冲突
                    sd_emails = db.query(User).filter(User.email == email_norm, User.id != u.id, User.deleted_at.isnot(None)).all()
                    for sde in sd_emails:
                        ts = int(sde.deleted_at.timestamp()) if sde.deleted_at else int(datetime.now().timestamp())
                        suffix = f"_del_{ts}_{sde.id}"
                        sde.email = f"{sde.email[:120 - len(suffix)]}{suffix}"
                u.email = email_norm
            if role is not None:
                if role not in RoleService.get_active_codes():
                    raise APIException("角色不存在或已停用", code=10007, status_code=400)
                if u.fixed and role != "admin":
                    raise APIException("种子管理员不可降级", code=10009, status_code=403)
                if actor and actor.id == u.id and role != "admin":
                    raise APIException("不能取消自己的管理员角色", code=10010, status_code=403)
                u.role = role
            if is_active is not None:
                if u.fixed and not is_active:
                    raise APIException("种子管理员不可禁用", code=10013, status_code=403)
                if actor and actor.id == u.id and not is_active:
                    raise APIException("不能禁用自己", code=10014, status_code=403)
                u.is_active = bool(is_active)

            db.commit()
            db.refresh(u)
            return _user_to_dict(u)

    @classmethod
    def reset_password(cls, user_id: int, new_password: str, actor: Optional[User] = None) -> dict:
        validate_password_strength(new_password)
        with SessionLocal() as db:
            u = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
            if not u:
                raise APIException("账号不存在", code=10005, status_code=404)
            # 仅允许：改自己 / 改非 admin 用户；禁止 admin 互改密码（含 fixed admin）
            if actor and actor.id != u.id and (u.role == "admin" or u.fixed):
                raise APIException("不能修改其他管理员的密码", code=10013, status_code=403)
            u.hashed_password = get_password_hash(new_password)
            db.commit()
            return {"id": user_id, "password_reset": True}

    @classmethod
    def delete_admin(cls, user_id: int, actor: Optional[User] = None) -> dict:
        with SessionLocal() as db:
            u = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
            if not u:
                raise APIException("账号不存在", code=10005, status_code=404)
            if u.fixed:
                raise APIException("禁止删除种子管理员", code=10006, status_code=403)
            if actor and actor.id == u.id:
                raise APIException("不能删除自己", code=10011, status_code=403)
            
            now = datetime.now()
            u.deleted_at = now
            # 释放唯一键约束
            ts = int(now.timestamp())
            suffix = f"_del_{ts}_{u.id}"
            u.username = f"{u.username[:50 - len(suffix)]}{suffix}"
            if u.email:
                u.email = f"{u.email[:120 - len(suffix)]}{suffix}"
                
            db.commit()
            return {"id": user_id, "deleted": True}

    # ── legacy 别名 ──
    @classmethod
    def list_users(cls, page: int = 1, size: int = 20, keyword: Optional[str] = None) -> dict:
        return cls.list_admins(page=page, size=size, keyword=keyword)

    @classmethod
    def delete_user(cls, user_id: int) -> dict:
        return cls.delete_admin(user_id)

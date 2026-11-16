"""用户自身资料 mixin：get_me / update_self_profile / change_password。"""
from typing import Optional

from app.boot import APIException
from app.core.security import get_password_hash, validate_password_strength, verify_password
from app.db import SessionLocal, User

from ._helpers import _normalize_email, _user_to_dict


class _MeMixin:

    @classmethod
    def get_me(cls, user: User) -> dict:
        from app.db import SysRoleMenu
        with SessionLocal() as db:
            fresh = db.query(User).filter(User.id == user.id).first()
            u = fresh or user

            if u.role == "admin" or u.fixed:
                perms = ["*"]
            else:
                grants = db.query(SysRoleMenu.menu_key).filter(SysRoleMenu.role == u.role).all()
                perms = [row.menu_key for row in grants]

            return _user_to_dict(u, permissions=perms)

    @classmethod
    def update_self_profile(
        cls,
        user_id: int,
        *,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
    ) -> dict:
        """用户改自己的资料（不能改 role / is_active / username）"""
        with SessionLocal() as db:
            u = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
            if not u:
                raise APIException("账号不存在", code=10005, status_code=404)
            if full_name is not None:
                u.full_name = full_name.strip() or None
            if email is not None:
                email_norm = _normalize_email(email)
                if email_norm:
                    dup = db.query(User).filter(User.email == email_norm, User.id != u.id).first()
                    if dup:
                        raise APIException("邮箱已被占用", code=10008, status_code=409)
                u.email = email_norm
            db.commit()
            db.refresh(u)
            return _user_to_dict(u)

    @classmethod
    def change_password(
        cls,
        user_id: int,
        old_password: str,
        new_password: str,
    ) -> dict:
        """用户改自己的密码：先验旧密"""
        if not old_password:
            raise APIException("请输入当前密码", code=10015, status_code=400)
        validate_password_strength(new_password)
        if old_password == new_password:
            raise APIException("新密码不能与旧密码相同", code=10016, status_code=400)
        with SessionLocal() as db:
            u = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
            if not u:
                raise APIException("账号不存在", code=10005, status_code=404)
            if not verify_password(old_password, u.hashed_password):
                raise APIException("当前密码错误", code=10017, status_code=400)
            u.hashed_password = get_password_hash(new_password)
            db.commit()
            return {"id": user_id, "password_changed": True}

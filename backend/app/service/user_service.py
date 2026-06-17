"""用户 & 管理员 Service —— 后台账号、登录、CRUD"""
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import or_

from app.boot import APIException, jwt_config
from app.core.jwt import create_access_token
from app.core.security import get_password_hash, verify_password
from app.db import SessionLocal, User
from app.service.role_service import RoleService


# ────────────────────────────────────────────────────────────────────
# 序列化辅助
# ────────────────────────────────────────────────────────────────────
def _user_to_dict(u: User, permissions: list = None) -> dict:
    """前端契约：含 id / email / username / full_name / role / fixed / is_active"""
    res = {
        "id":         u.id,
        "email":      u.email,
        "username":   u.username,
        "full_name":  u.full_name,
        "role":       u.role or "member",
        "fixed":      bool(u.fixed),
        "is_active":  True if u.is_active is None else bool(u.is_active),
        "last_login": u.last_login.isoformat() if u.last_login else None,
        "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
        "created_at": u.created_at.isoformat() if u.created_at else None,
    }
    if permissions is not None:
        res["permissions"] = permissions
    return res


def _normalize_email(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    return s.strip().lower() or None


class UserService:
    """无状态服务：所有方法均为类方法。"""

    # ──────────────────────────────────────────
    # 登录（前端契约：POST /api/v1/auth/login {email, password}）
    #   identifier 既支持 email 也支持 username（前端不带 @ 时拼 @local）
    # ──────────────────────────────────────────
    @classmethod
    def login(cls, identifier: str, password: str) -> dict:
        identifier = (identifier or "").strip()
        if not identifier or not password:
            raise APIException("账号或密码不能为空", code=10001, status_code=400)

        with SessionLocal() as db:
            email_norm = _normalize_email(identifier)
            # email 命中优先，username 兜底
            user = (
                db.query(User)
                .filter(
                    User.deleted_at.is_(None),
                    or_(User.email == email_norm, User.username == identifier),
                )
                .first()
            )
            if not user or not verify_password(password, user.hashed_password):
                raise APIException("账号或密码错误", code=10004, status_code=401)

            # is_active 校验（fixed admin 不会被禁，所以无关）
            if user.is_active is False and not user.fixed:
                raise APIException("账号已停用，请联系管理员", code=10012, status_code=403)

            now = datetime.now()
            user.last_login = now
            user.last_login_at = now
            db.commit()
            db.refresh(user)

            token = create_access_token(
                subject=f"{user.id}_{int(bool(user.fixed))}",
                expires_delta=timedelta(minutes=jwt_config.expire_minutes),
            )
            
            # 获取用户权限列表
            from app.db import SysRoleMenu
            if user.role == "admin" or user.fixed:
                perms = ["*"]
            else:
                with SessionLocal() as db:
                    grants = db.query(SysRoleMenu.menu_key).filter(SysRoleMenu.role == user.role).all()
                    perms = [row.menu_key for row in grants]

            # 同时支持前端裸 token 字段 + 标准 access_token
            return {
                "token":        token,
                "access_token": token,
                "token_type":   "bearer",
                "expires_in":   jwt_config.expire_minutes * 60,
                "user":         _user_to_dict(user, permissions=perms),
            }

    # ──────────────────────────────────────────
    # 当前用户信息 + 自助资料/改密
    # ──────────────────────────────────────────
    @classmethod
    def get_me(cls, user: User) -> dict:
        from app.db import SysRoleMenu
        with SessionLocal() as db:
            fresh = db.query(User).filter(User.id == user.id).first()
            u = fresh or user
            
            # 获取用户权限列表
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
        if len(new_password) < 6:
            raise APIException("新密码至少 6 个字符", code=10002, status_code=400)
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

    # ──────────────────────────────────────────
    # 注册（保留：终端用户场景；后台管理员请用 create_admin）
    # ──────────────────────────────────────────
    @classmethod
    def register(cls, username: str, password: str) -> dict:
        username = (username or "").strip()
        if len(username) < 3:
            raise APIException("用户名至少 3 个字符", code=10001)
        if len(password) < 6:
            raise APIException("密码至少 6 个字符", code=10002)

        with SessionLocal() as db:
            if db.query(User).filter(User.username == username).first():
                raise APIException("用户名已存在", code=10003)

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

    # ──────────────────────────────────────────
    # 管理员 CRUD
    # ──────────────────────────────────────────
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
        if len(password) < 6:
            raise APIException("密码至少 6 个字符", code=10002, status_code=400)
        if role not in RoleService.get_active_codes():
            raise APIException("角色不存在或已停用", code=10007, status_code=400)

        email_norm = _normalize_email(email)

        with SessionLocal() as db:
            if db.query(User).filter(User.username == username).first():
                raise APIException("用户名已存在", code=10003, status_code=409)
            if email_norm and db.query(User).filter(User.email == email_norm).first():
                raise APIException("邮箱已存在", code=10008, status_code=409)

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
                dup = db.query(User).filter(User.username == username, User.id != u.id).first()
                if dup:
                    raise APIException("用户名已存在", code=10003, status_code=409)
                u.username = username
            if full_name is not None:
                u.full_name = full_name.strip() or None
            if email is not None:
                email_norm = _normalize_email(email)
                if email_norm:
                    dup = db.query(User).filter(User.email == email_norm, User.id != u.id).first()
                    if dup:
                        raise APIException("邮箱已被占用", code=10008, status_code=409)
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
    def reset_password(cls, user_id: int, new_password: str) -> dict:
        if len(new_password) < 6:
            raise APIException("密码至少 6 个字符", code=10002, status_code=400)
        with SessionLocal() as db:
            u = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
            if not u:
                raise APIException("账号不存在", code=10005, status_code=404)
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
            u.deleted_at = datetime.now()
            db.commit()
            return {"id": user_id, "deleted": True}

    # ──────────────────────────────────────────
    # 启动 seed：保证至少有一个种子管理员
    # ──────────────────────────────────────────
    SEED_EMAIL    = "admin@local"
    SEED_USERNAME = "admin"
    SEED_PASSWORD = "admin123"

    @classmethod
    def ensure_seed_admin(cls) -> dict:
        """启动时 upsert 种子管理员：admin@local / admin123 / role=admin / fixed=True。

        - 若已存在（按 email 或 username 命中）：补齐 role/fixed 字段，密码不动
        - 若不存在：创建
        返回 {"created": bool, "email": ...}
        """
        with SessionLocal() as db:
            existing = (
                db.query(User)
                .filter(
                    User.deleted_at.is_(None),
                    or_(User.email == cls.SEED_EMAIL, User.username == cls.SEED_USERNAME),
                )
                .first()
            )
            if existing:
                changed = False
                if existing.role != "admin":
                    existing.role = "admin"; changed = True
                if not existing.fixed:
                    existing.fixed = True;  changed = True
                if not existing.email:
                    existing.email = cls.SEED_EMAIL; changed = True
                if changed:
                    db.commit()
                return {"created": False, "email": existing.email or cls.SEED_EMAIL}

            u = User(
                username=cls.SEED_USERNAME,
                email=cls.SEED_EMAIL,
                full_name="系统管理员",
                role="admin",
                fixed=True,
                hashed_password=get_password_hash(cls.SEED_PASSWORD),
            )
            db.add(u)
            db.commit()
            return {"created": True, "email": cls.SEED_EMAIL}

    # ──────────────────────────────────────────
    # 兼容：旧 list_users / delete_user（其它测试还在引用）
    # ──────────────────────────────────────────
    @classmethod
    def list_users(cls, page: int = 1, size: int = 20, keyword: Optional[str] = None) -> dict:
        return cls.list_admins(page=page, size=size, keyword=keyword)

    @classmethod
    def delete_user(cls, user_id: int) -> dict:
        return cls.delete_admin(user_id)

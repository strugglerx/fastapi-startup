"""用户业务 Service —— 注册 / 登录 / 列表 / 删除"""
from datetime import datetime, timedelta
from typing import Optional

from app.boot import APIException, jwt_config
from app.core.jwt import create_access_token
from app.core.security import get_password_hash, verify_password
from app.db import SessionLocal, User


class UserService:
    """无状态服务：所有方法均为类方法，调用即用，无需实例化。"""

    # ──────────────────────────────────────────
    # 注册
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
                fixed=False,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            return {"id": user.id, "username": user.username}

    # ──────────────────────────────────────────
    # 登录（颁发 JWT）
    # ──────────────────────────────────────────
    @classmethod
    def login(cls, username: str, password: str) -> dict:
        with SessionLocal() as db:
            user = (
                db.query(User)
                .filter(User.username == username.strip(), User.deleted_at.is_(None))
                .first()
            )
            if not user or not verify_password(password, user.hashed_password):
                raise APIException("用户名或密码错误", code=10004)

            user.last_login = datetime.now()
            db.commit()

            token = create_access_token(
                subject=f"{user.id}_{int(user.fixed)}",
                expires_delta=timedelta(minutes=jwt_config.expire_minutes),
            )
            return {
                "access_token": token,
                "token_type": "bearer",
                "expires_in": jwt_config.expire_minutes * 60,
                "user": {"id": user.id, "username": user.username, "fixed": user.fixed},
            }

    # ──────────────────────────────────────────
    # 列表（分页）
    # ──────────────────────────────────────────
    @classmethod
    def list_users(cls, page: int = 1, size: int = 20, keyword: Optional[str] = None) -> dict:
        page = max(1, page)
        size = max(1, min(size, 100))

        with SessionLocal() as db:
            q = db.query(User).filter(User.deleted_at.is_(None))
            if keyword:
                q = q.filter(User.username.like(f"%{keyword.strip()}%"))

            total = q.count()
            rows = q.order_by(User.id.desc()).offset((page - 1) * size).limit(size).all()

            return {
                "total": total,
                "page": page,
                "size": size,
                "items": [
                    {
                        "id": u.id,
                        "username": u.username,
                        "fixed": u.fixed,
                        "last_login": u.last_login.isoformat() if u.last_login else None,
                        "created_at": u.created_at.isoformat() if u.created_at else None,
                    }
                    for u in rows
                ],
            }

    # ──────────────────────────────────────────
    # 删除（软删，禁止删管理员）
    # ──────────────────────────────────────────
    @classmethod
    def delete_user(cls, user_id: int) -> dict:
        with SessionLocal() as db:
            user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
            if not user:
                raise APIException("用户不存在", code=10005)
            if user.fixed:
                raise APIException("禁止删除管理员账户", code=10006)

            user.deleted_at = datetime.now()
            db.commit()
            return {"id": user_id, "deleted": True}

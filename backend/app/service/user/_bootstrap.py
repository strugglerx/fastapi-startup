"""启动 lifespan 钩子：种子管理员 upsert。"""
from sqlalchemy import or_

from app.boot.config import seed_admin_config
from app.core.security import get_password_hash
from app.db import SessionLocal, User


class _BootstrapMixin:

    @classmethod
    def _seed_email(cls) -> str:
        return seed_admin_config.email or "admin@local"

    @classmethod
    def _seed_username(cls) -> str:
        return seed_admin_config.username or "admin"

    @classmethod
    def ensure_seed_admin(cls) -> dict:
        """启动时 upsert 种子管理员。

        凭证全部来自 env（SEED_ADMIN_EMAIL / SEED_ADMIN_USERNAME / SEED_ADMIN_PASSWORD）。
        - SEED_ADMIN_PASSWORD 未设置 → 跳过创建，避免代码里硬编码默认密码被密钥扫描标红 / 被弱口令利用。
        - 若管理员已存在：仅补齐 role/fixed/email 字段，密码不动。
        - 若不存在且 env 已配置：用 env 凭证创建。

        返回 {"created": bool, "email": ..., "skipped": bool}
        """
        email = cls._seed_email()
        username = cls._seed_username()

        with SessionLocal() as db:
            existing = (
                db.query(User)
                .filter(
                    User.deleted_at.is_(None),
                    or_(User.email == email, User.username == username),
                )
                .first()
            )
            if existing:
                changed = False
                if existing.role != "admin":
                    existing.role = "admin"; changed = True
                if not existing.fixed:
                    existing.fixed = True; changed = True
                if not existing.email:
                    existing.email = email; changed = True
                if changed:
                    db.commit()
                return {"created": False, "skipped": False, "email": existing.email or email}

            if not seed_admin_config.is_configured:
                return {"created": False, "skipped": True, "email": email}

            u = User(
                username=username,
                email=email,
                full_name="系统管理员",
                role="admin",
                fixed=True,
                hashed_password=get_password_hash(seed_admin_config.password),
            )
            db.add(u)
            db.commit()
            return {"created": True, "skipped": False, "email": email}

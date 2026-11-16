"""鉴权 mixin：login / refresh_token / refresh_with_refresh_token / revoke_refresh_token。"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import or_

from app.boot import APIException, jwt_config
from app.core.jwt import create_access_token
from app.core.security import verify_password
from app.db import RefreshToken, SessionLocal, User

from ._helpers import (
    _check_login_lock,
    _clear_login_fail,
    _hash_refresh,
    _issue_tokens,
    _load_user_perms,
    _normalize_email,
    _record_login_fail,
    _user_to_dict,
)


class _AuthMixin:

    @classmethod
    def login(
        cls,
        identifier: str,
        password: str,
        *,
        ua: Optional[str] = None,
        client_ip: Optional[str] = None,
    ) -> dict:
        identifier = (identifier or "").strip()
        if not identifier or not password:
            raise APIException("账号或密码不能为空", code=10001, status_code=400)

        _check_login_lock(identifier)

        with SessionLocal() as db:
            email_norm = _normalize_email(identifier)
            user = (
                db.query(User)
                .filter(
                    User.deleted_at.is_(None),
                    or_(User.email == email_norm, User.username == identifier),
                )
                .first()
            )
            if not user or not verify_password(password, user.hashed_password):
                _record_login_fail(identifier)
                raise APIException("账号或密码错误", code=10004, status_code=401)

            if user.is_active is False and not user.fixed:
                raise APIException("账号已停用，请联系管理员", code=10012, status_code=403)

            _clear_login_fail(identifier)

            now = datetime.now()
            user.last_login = now
            user.last_login_at = now

            resp = _issue_tokens(db, user, ua=ua, client_ip=client_ip)
            db.commit()
            db.refresh(user)

        resp["user"] = _user_to_dict(user, permissions=_load_user_perms(user))
        return resp

    @classmethod
    def refresh_token(
        cls,
        user: User,
        *,
        ua: Optional[str] = None,
        client_ip: Optional[str] = None,
    ) -> dict:
        """access 滑动续期：旧 access 仍有效时调用，只换发新 access。

        ⚠ 故意不签新 refresh：这条路径不知道客户端当前用的是哪个 refresh，
        若每次都签新 refresh 入库又不吊销旧的，并发 / 多 tab 会产生孤儿
        refresh 堆积。需要 rotate 请走 /refresh-token。
        """
        token = create_access_token(
            subject=f"{user.id}_{int(bool(user.fixed))}",
            expires_delta=timedelta(minutes=jwt_config.expire_minutes),
        )
        return {
            "token":        token,
            "access_token": token,
            "token_type":   "bearer",
            "expires_in":   jwt_config.expire_minutes * 60,
        }

    @classmethod
    def refresh_with_refresh_token(
        cls,
        refresh_str: str,
        *,
        ua: Optional[str] = None,
        client_ip: Optional[str] = None,
    ) -> dict:
        """用 refresh_token 换发新的 access + 新的 refresh（rotate，旧的吊销）。
        失败语义统一抛 401，让前端按"重新登录"处理。
        """
        if not refresh_str or not isinstance(refresh_str, str):
            raise APIException("缺少 refresh_token", code=401, status_code=401)
        h = _hash_refresh(refresh_str.strip())
        now = datetime.now(timezone.utc)

        with SessionLocal() as db:
            row = db.query(RefreshToken).filter(RefreshToken.token_hash == h).first()
            if not row:
                raise APIException("refresh_token 无效", code=401, status_code=401)
            if row.revoked_at is not None:
                raise APIException("refresh_token 已吊销，请重新登录", code=401, status_code=401)

            from app.core.time import ensure_cn_aware
            # DB naive datetime = CN 字面值(见 core/time.py:ensure_cn_aware),不能当 UTC
            exp = ensure_cn_aware(row.expires_at)
            if exp < now:
                raise APIException("refresh_token 已过期，请重新登录", code=401, status_code=401)

            user = db.query(User).filter(
                User.id == row.user_id, User.deleted_at.is_(None)
            ).first()
            if not user:
                raise APIException("账号不存在或已删除", code=401, status_code=401)
            if user.is_active is False and not user.fixed:
                raise APIException("账号已停用", code=403, status_code=403)

            row.revoked_at = now
            resp = _issue_tokens(db, user, ua=ua, client_ip=client_ip)
            db.commit()
            db.refresh(user)

        resp["user"] = _user_to_dict(user, permissions=_load_user_perms(user))
        return resp

    @classmethod
    def revoke_refresh_token(cls, refresh_str: Optional[str]) -> dict:
        """登出 / 手动吊销。空串 / None 静默返回 revoked=False。"""
        if not refresh_str:
            return {"revoked": False}
        h = _hash_refresh(refresh_str.strip())
        with SessionLocal() as db:
            count = (
                db.query(RefreshToken)
                .filter(RefreshToken.token_hash == h, RefreshToken.revoked_at.is_(None))
                .update({"revoked_at": datetime.now(timezone.utc)}, synchronize_session=False)
            )
            db.commit()
            return {"revoked": bool(count)}

"""密码找回 mixin：邮箱验证码两步流（request_password_reset / confirm_password_reset）。

Redis key：
- pwreset_code:{email}    -> 6 位数字，TTL 600s（10 分钟）
- pwreset_send:{email}    -> 防刷标记，TTL 60s（同一邮箱 1 分钟内只发 1 次）
"""
import secrets

from app.boot import APIException, app_config, logger
from app.core.redis_pool import RedisPool
from app.core.security import get_password_hash, validate_password_strength
from app.db import SessionLocal, User

from ._helpers import _fail_key, _lock_key, _normalize_email


class _PasswordResetMixin:

    @classmethod
    def request_password_reset(cls, email: str) -> dict:
        from app.core.mailer import send_mail, _ensure_configured  # 延迟引入避免 boot 顺序问题

        email_norm = _normalize_email(email)
        if not email_norm:
            raise APIException("请输入合法的邮箱", code=10018, status_code=400)

        # SMTP 未配置 → 503 友好提示
        _ensure_configured()

        # 防刷：60s 内同邮箱仅 1 次
        try:
            r = RedisPool.get_redis()
            if r.get(f"pwreset_send:{email_norm}"):
                raise APIException("发送过于频繁，请稍后再试", code=10019, status_code=429)
        except APIException:
            raise
        except Exception as e:
            logger.debug(f"pwreset throttle check skipped: {e}")

        with SessionLocal() as db:
            user = db.query(User).filter(
                User.email == email_norm, User.deleted_at.is_(None)
            ).first()

        # 邮箱不存在也走假流程，避免被用来探测注册邮箱
        if user:
            code = f"{secrets.randbelow(1000000):06d}"
            try:
                r = RedisPool.get_redis()
                r.setex(f"pwreset_code:{email_norm}", 600, code)
                r.setex(f"pwreset_send:{email_norm}", 60, "1")
            except Exception as e:
                logger.error(f"pwreset redis store failed: {e}")
                raise APIException("服务暂不可用，请稍后重试", code=10031, status_code=503)

            send_mail(
                to=email_norm,
                subject=f"【{app_config.name}】密码重置验证码",
                body=(
                    f"您好，\n\n"
                    f"您的密码重置验证码是：{code}\n"
                    f"该验证码 10 分钟内有效，仅可使用一次。\n\n"
                    f"如果您没有发起此请求，请忽略本邮件。\n\n"
                    f"—— {app_config.name}\n"
                ),
            )

        return {"sent": True}

    @classmethod
    def confirm_password_reset(cls, email: str, code: str, new_password: str) -> dict:
        email_norm = _normalize_email(email)
        if not email_norm:
            raise APIException("请输入合法的邮箱", code=10018, status_code=400)
        if not code or len(code) != 6:
            raise APIException("验证码格式不正确", code=10018, status_code=400)
        validate_password_strength(new_password)

        try:
            r = RedisPool.get_redis()
            stored = r.get(f"pwreset_code:{email_norm}")
        except Exception as e:
            logger.error(f"pwreset redis get failed: {e}")
            raise APIException("服务暂不可用，请稍后重试", code=10031, status_code=503)

        stored_str = stored.decode() if isinstance(stored, bytes) else stored
        if not stored_str or stored_str != code:
            raise APIException("验证码无效或已过期", code=10018, status_code=400)

        with SessionLocal() as db:
            user = db.query(User).filter(
                User.email == email_norm, User.deleted_at.is_(None)
            ).first()
            if not user:
                raise APIException("账号不存在", code=10005, status_code=404)
            user.hashed_password = get_password_hash(new_password)
            db.commit()

        # 一次性使用：成功后立即清除验证码 + 解除锁定
        try:
            r = RedisPool.get_redis()
            r.delete(f"pwreset_code:{email_norm}", _lock_key(email_norm), _fail_key(email_norm))
        except Exception:
            pass

        return {"reset": True}

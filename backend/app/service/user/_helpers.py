"""user 子包共享 helpers：refresh token、登录锁定、序列化。

所有 mixin 共用，**对外不暴露**（_ 前缀模块）。
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.boot import APIException, jwt_config, logger
from app.core.jwt import create_access_token
from app.core.redis_pool import RedisPool
from app.db import RefreshToken, SessionLocal, User

# ───────────── Refresh Token ─────────────
# - access  : 短期 JWT（jwt_config.expire_minutes，默认 8h），无状态
# - refresh : opaque 随机串（jwt_config.refresh_expire_days，默认 30d）
#             sha256 后落 refresh_tokens 表，可吊销 / 可 rotate
REFRESH_TOKEN_PREFIX = "rt_"


def _hash_refresh(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _issue_tokens(
    db,
    user: User,
    *,
    ua: Optional[str] = None,
    client_ip: Optional[str] = None,
) -> dict:
    """生成 access + refresh token 对，refresh 已 add 到 db（未 commit）。

    返回标准 token 响应体（不含 user / permissions，调用方自填）。
    """
    access = create_access_token(
        subject=f"{user.id}_{int(bool(user.fixed))}",
        expires_delta=timedelta(minutes=jwt_config.expire_minutes),
    )
    refresh_str = REFRESH_TOKEN_PREFIX + secrets.token_urlsafe(48)
    refresh_expires_at = datetime.now(timezone.utc) + timedelta(days=jwt_config.refresh_expire_days)

    db.add(RefreshToken(
        user_id=user.id,
        token_hash=_hash_refresh(refresh_str),
        expires_at=refresh_expires_at,
        user_agent=(ua or "")[:255] or None,
        client_ip=(client_ip or "")[:64] or None,
    ))

    return {
        "token":              access,
        "access_token":       access,
        "token_type":         "bearer",
        "expires_in":         jwt_config.expire_minutes * 60,
        "refresh_token":      refresh_str,
        "refresh_expires_in": jwt_config.refresh_expire_days * 86400,
    }


def _load_user_perms(user: User) -> list:
    """单独 session 拉用户菜单权限，admin / fixed 返回 ['*']。"""
    from app.db import SysRoleMenu
    if user.role == "admin" or user.fixed:
        return ["*"]
    with SessionLocal() as db:
        grants = db.query(SysRoleMenu.menu_key).filter(SysRoleMenu.role == user.role).all()
        return [row.menu_key for row in grants]


# ───────────── 登录失败锁定 ─────────────
# 按账号 + IP 双维度，防止单账号被刷死也防暴破。Redis 不可用时降级到不锁定。
LOGIN_FAIL_MAX = 5
LOGIN_FAIL_WINDOW = 600   # 10 分钟窗口
LOGIN_LOCK_SECONDS = 900  # 锁 15 分钟


def _fail_key(identifier: str) -> str:
    return f"login_fail:{identifier.strip().lower()}"


def _lock_key(identifier: str) -> str:
    return f"login_lock:{identifier.strip().lower()}"


def _check_login_lock(identifier: str) -> None:
    """命中锁定时直接抛 APIException；Redis 故障静默放行。"""
    try:
        r = RedisPool.get_redis()
        ttl = r.ttl(_lock_key(identifier))
        if ttl and ttl > 0:
            mins = max(1, ttl // 60)
            raise APIException(
                f"账号已被临时锁定，请 {mins} 分钟后重试",
                code=10013,
                status_code=429,
            )
    except APIException:
        raise
    except Exception as e:
        logger.debug(f"login lock check skipped: {e}")


def _record_login_fail(identifier: str) -> None:
    try:
        r = RedisPool.get_redis()
        key = _fail_key(identifier)
        pipe = r.pipeline()
        pipe.incr(key)
        pipe.expire(key, LOGIN_FAIL_WINDOW)
        count, _ = pipe.execute()
        if int(count) >= LOGIN_FAIL_MAX:
            r.setex(_lock_key(identifier), LOGIN_LOCK_SECONDS, "1")
            r.delete(key)
    except Exception as e:
        logger.debug(f"login fail record skipped: {e}")


def _clear_login_fail(identifier: str) -> None:
    try:
        r = RedisPool.get_redis()
        r.delete(_fail_key(identifier), _lock_key(identifier))
    except Exception as e:
        logger.debug(f"login fail clear skipped: {e}")


# ───────────── 序列化辅助 ─────────────
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

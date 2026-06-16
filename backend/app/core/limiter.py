import json
from typing import Optional

from fastapi import Request

from app.core.redis_pool import RedisPool
from app.db import SessionLocal, AccessKey, User
from app.boot.exceptions import APIException
from app.boot import logger


class DynamicIPRateLimiter:
    """基于 AccessKey 配置的 IP 限流器（懒加载 Redis 连接）"""

    _RATE_LIMIT_LUA = """
    local current = redis.call('INCR', KEYS[1])
    if current == 1 then
        redis.call('EXPIRE', KEYS[1], 1)
    end
    return current <= tonumber(ARGV[1])
    """

    def __init__(self):
        self._redis = None

    @property
    def redis(self):
        if self._redis is None:
            self._redis = RedisPool.get_redis()
        return self._redis

    def enforce(self, request: Request):
        # 已通过常规登录认证的请求放行
        if getattr(request.state, "user", None):
            return

        ip = self._get_client_ip(request)
        if not ip:
            raise APIException("获取IP失败", code=1, status_code=400)

        token = request.headers.get("X-Access-Key", "").strip()
        if not token:
            raise APIException("缺少访问密钥", code=401, status_code=401)

        info = self._get_access_key_info(token)
        request.state.access_key = info["access_key"]
        request.state.access_key_user = info["user"]

        if not self._check_ip_limit(ip, info["max_qps"]):
            raise APIException(f"IP请求超过限制（{info['max_qps']}次/秒）", code=429, status_code=429)

    def _get_access_key_info(self, token: str) -> dict:
        """带 Redis 缓存的 AccessKey 查询（含穿透保护）"""
        cache_key = f"access_key_full_info:{token}"

        try:
            cached_data = self.redis.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                if data.get("error") == "not_found":
                    raise APIException("访问密钥无效", code=401, status_code=401)
                return {
                    "max_qps": data["max_qps"],
                    "access_key": type("AccessKey", (), data["access_key"])(),
                    "user": type("User", (), data["user"])() if data["user"] else None,
                }

            with SessionLocal() as db:
                row = (
                    db.query(AccessKey, User)
                    .outerjoin(User, AccessKey.created_by == User.id)
                    .filter(AccessKey.secret_key == token, AccessKey.deleted_at.is_(None))
                    .first()
                )
                if not row or not row[0]:
                    # 穿透保护：缓存 not_found 10 秒
                    self.redis.setex(cache_key, 10, json.dumps({"error": "not_found"}))
                    raise APIException("访问密钥无效", code=401, status_code=401)

                access_key, user_row = row
                user = user_row if user_row and user_row.deleted_at is None else None

                cache_data = {
                    "max_qps": access_key.max_qps,
                    "access_key": {
                        "id": access_key.id,
                        "secret_key": access_key.secret_key,
                        "max_qps": access_key.max_qps,
                        "created_by": access_key.created_by,
                    },
                    "user": {"id": user.id, "username": user.username, "fixed": user.fixed} if user else None,
                }
                self.redis.setex(cache_key, 60, json.dumps(cache_data))

                return {"max_qps": access_key.max_qps, "access_key": access_key, "user": user}

        except APIException:
            raise
        except Exception as e:
            logger.error(f"获取AccessKey信息失败: {e}")
            raise APIException("访问密钥无效", code=401, status_code=401)

    @classmethod
    def clear_access_key_cache(cls, secret_key: str) -> bool:
        try:
            redis_client = RedisPool.get_redis()
            return bool(redis_client.delete(f"access_key_full_info:{secret_key}"))
        except Exception as e:
            logger.error(f"清除 AccessKey 缓存失败 {secret_key}: {e}")
            return False

    def _check_ip_limit(self, ip: str, limit: int) -> bool:
        return bool(self.redis.eval(self._RATE_LIMIT_LUA, 1, f"ip_limit:{ip}", str(limit)))

    def _get_client_ip(self, request: Request) -> str:
        xff = request.headers.get("x-forwarded-for")
        if xff:
            return xff.split(",")[0].strip()
        return (request.client.host if request.client else None) or "0.0.0.0"


_rate_limiter: Optional[DynamicIPRateLimiter] = None


def get_rate_limiter() -> DynamicIPRateLimiter:
    """懒加载全局限流器实例"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = DynamicIPRateLimiter()
    return _rate_limiter

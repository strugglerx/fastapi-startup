import ipaddress
import json
import os
from functools import lru_cache
from typing import Optional, Tuple

from fastapi import Request

from app.core.redis_pool import RedisPool
from app.db import SessionLocal, AccessKey, User
from app.boot.exceptions import APIException
from app.boot import logger


# ════════════════════════ 受信任反代解析 ════════════════════════
# 安全背景：早期所有取真实 IP 的地方（限流 / 审计 / 登录爆破检测）都无条件
# 信任 `X-Forwarded-For` 首段。攻击者只要 `curl -H 'X-Forwarded-For: 1.2.3.4'`
# 就能让 identifier 随机化，登录爆破 / Open API 限流形同虚设。
#
# 修复：只有当 `request.client.host` 落在 `TRUSTED_PROXY_IPS`（env，逗号分隔，
# 支持单 IP 或 CIDR）声明的受信代理范围内时，才采纳 XFF / X-Real-IP 首段；
# 否则强制回退到 socket 对端 `request.client.host`（最严格，无法被 header 伪造）。
#
# **生产部署须知**：nginx / k8s ingress / 云 LB 反代后必须显式配置
# `TRUSTED_PROXY_IPS`（例如 `10.0.0.0/8,172.16.0.0/12`）；否则 IP 会被解析成
# 内网网关地址（如 `127.0.0.1`），所有 IP 维度限流会塌缩到单一桶。

def _parse_trusted_proxies(raw: str) -> Tuple[ipaddress._BaseNetwork, ...]:
    """把 `TRUSTED_PROXY_IPS` 解析成 CIDR 列表；脏数据条目静默丢弃。"""
    if not raw or not raw.strip():
        return ()
    nets = []
    for item in raw.split(","):
        s = item.strip()
        if not s:
            continue
        try:
            # 单 IP 也走 ip_network（strict=False 容忍 host bits）
            nets.append(ipaddress.ip_network(s, strict=False))
        except ValueError:
            logger.warning(f"TRUSTED_PROXY_IPS 条目无效，已忽略: {s!r}")
    return tuple(nets)


@lru_cache(maxsize=1)
def _trusted_proxy_networks() -> Tuple[ipaddress._BaseNetwork, ...]:
    """env 解析结果缓存。进程内 env 不会变；改 env 必须重启。"""
    return _parse_trusted_proxies(os.getenv("TRUSTED_PROXY_IPS", ""))


def _is_trusted_proxy(peer_ip: str) -> bool:
    nets = _trusted_proxy_networks()
    if not nets:
        return False
    try:
        addr = ipaddress.ip_address(peer_ip)
    except ValueError:
        return False
    return any(addr in n for n in nets)


def get_client_ip(request: Request) -> str:
    """获取真实客户端 IP（受信代理感知）。

    返回值：
      - 受信代理 + 有 XFF / X-Real-IP → 取首段（去空白）
      - 其它一切情况 → `request.client.host`（兜底 `"unknown"`）

    所有需要按 IP 限流 / 审计 / 风控的代码都应统一调用本函数，避免
    重复实现「裸取 XFF」的反模式被攻击者绕过。
    """
    peer = (request.client.host if request.client else "") or ""
    if peer and _is_trusted_proxy(peer):
        for header in ("x-forwarded-for", "x-real-ip"):
            val = request.headers.get(header)
            if not val:
                continue
            first = val.split(",")[0].strip()
            if first:
                return first
    return peer or "unknown"


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
                # secret_key 在 DB 里是 Fernet 密文，不能直接 WHERE 比对。
                # 枚举所有活跃 key 后用 decrypt_secret 解密对比（兼容历史明文 → 透传）。
                from app.core.crypto import decrypt_secret
                row = None
                candidates = (
                    db.query(AccessKey, User)
                    .outerjoin(User, AccessKey.created_by == User.id)
                    .filter(AccessKey.deleted_at.is_(None))
                    .all()
                )
                for ak, u in candidates:
                    if decrypt_secret(ak.secret_key) == token:
                        row = (ak, u)
                        break
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
        # 走统一 helper：受信反代名单内才信任 XFF，否则强制 socket 对端。
        ip = get_client_ip(request)
        return ip if ip and ip != "unknown" else "0.0.0.0"


_rate_limiter: Optional[DynamicIPRateLimiter] = None


def get_rate_limiter() -> DynamicIPRateLimiter:
    """懒加载全局限流器实例"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = DynamicIPRateLimiter()
    return _rate_limiter

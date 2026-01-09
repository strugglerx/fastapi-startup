from app.core.redis_pool import RedisPool
from fastapi import Request, HTTPException

from app.db import SessionLocal, AccessKey, User
from app.boot.exceptions import APIException
from app.boot import logger


class DynamicIPRateLimiter:
    def __init__(self):
        self.redis = RedisPool().get_redis()

    def enforce(self, request: Request):
        """执行限流：用Token查QPS配置，对IP限流"""
        # 后台管理预案放行
        if hasattr(request.state, "user"):
            return
        # 获取客户端真实IP
        ip = self._get_client_ip(request)
        if not ip:
            raise APIException("获取IP失败", status_code=400)

        # 从请求头获取Token（仅用于查QPS配置）
        token = request.headers.get("X-Access-Key", "").strip()
        if not token:
            raise APIException("缺少访问密钥", status_code=401, code=1)

        # 获取该Token对应的IP限流配置和用户信息
        access_key_info = self._get_access_key_info(token)
        ip_limit = access_key_info['max_qps']

        # 将 AccessKey 和 User 信息附加到 request.state
        request.state.access_key = access_key_info['access_key']
        request.state.access_key_user = access_key_info['user']

        logger.info(f"IP: {ip}, Token: {token}, IP限流配置: {ip_limit}次/秒, User: {access_key_info['user'].username if access_key_info['user'] else 'Unknown'}")
        
        # 对IP执行限流检查
        if not self._check_ip_limit(ip, ip_limit):
            raise APIException(f"IP请求超过限制（{ip_limit}次/秒）", status_code=429, code=429)
            # raise HTTPException(
            #     status_code=429,
            #     detail=f"IP请求超过限制（{ip_limit}次/秒）",
            #     headers={"Retry-After": "1"}
            # )

    def _get_access_key_info(self, token: str) -> dict:
        """根据Token获取AccessKey完整信息（包括用户信息），带Redis缓存优化"""
        cache_key = f"access_key_full_info:{token}"
        
        try:
            # 1. 先查 Redis 缓存（缓存完整信息）
            cached_data = self.redis.get(cache_key)
            if cached_data:
                import json
                data = json.loads(cached_data)
                
                # 检查是否是缓存的"不存在"结果（缓存穿透保护）
                if data.get("error") == "not_found":
                    logger.debug(f"Cache hit for invalid AccessKey: {token}")
                    raise APIException("访问密钥无效", status_code=401, code=1)
                
                logger.debug(f"Cache hit for AccessKey: {token}")
                
                # 重建对象（简化版，只包含必要字段）
                return {
                    'max_qps': data['max_qps'],
                    'access_key': type('AccessKey', (), data['access_key'])(),  # 简化对象
                    'user': type('User', (), data['user'])() if data['user'] else None
                }
            
            # 2. 缓存未命中，从数据库查询（使用 JOIN 一次性获取）
            logger.debug(f"Cache miss for AccessKey: {token}, querying database")
            with SessionLocal() as db:
                # 使用 JOIN 查询一次性获取 AccessKey 和 User
                from sqlalchemy import join
                
                result = db.query(AccessKey, User).outerjoin(
                    User, AccessKey.created_by == User.id
                ).filter(
                    AccessKey.secret_key == token,
                    AccessKey.deleted_at.is_(None)
                ).first()
                
                if not result or not result[0]:
                    # 缓存穿透保护：缓存"不存在"的结果，TTL 较短（10秒）
                    import json
                    self.redis.setex(cache_key, 10, json.dumps({"error": "not_found"}))
                    logger.warning(f"Invalid AccessKey attempted: {token}")
                    raise APIException("访问密钥无效", status_code=401, code=1)
                
                access_key = result[0]
                user = result[1] if result[1] and result[1].deleted_at is None else None
                
                # 3. 准备缓存数据（只缓存必要字段）
                cache_data = {
                    'max_qps': access_key.max_qps,
                    'access_key': {
                        'id': access_key.id,
                        'secret_key': access_key.secret_key,
                        'max_qps': access_key.max_qps,
                        'created_by': access_key.created_by
                    },
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'fixed': user.fixed
                    } if user else None
                }
                
                # 4. 写入 Redis 缓存（60秒过期）
                import json
                self.redis.setex(cache_key, 60, json.dumps(cache_data))
                logger.debug(f"Cached AccessKey info for: {token}")
                
                return {
                    'max_qps': access_key.max_qps,
                    'access_key': access_key,
                    'user': user
                }

                
        except APIException:
            raise
        except Exception as e:
            logger.error(f"获取AccessKey信息失败：{e}")
            raise APIException("访问密钥无效", status_code=401, code=1)

    @classmethod
    def clear_access_key_cache(cls, secret_key: str):
        """清除指定 AccessKey 的缓存（用于保持缓存一致性）"""
        try:
            redis_client = cls().redis
            cache_key = f"access_key_full_info:{secret_key}"
            result = redis_client.delete(cache_key)
            if result:
                logger.info(f"Cleared cache for AccessKey: {secret_key}")
            return result
        except Exception as e:
            logger.error(f"Failed to clear cache for AccessKey {secret_key}: {e}")
            return False


    def _check_ip_limit(self, ip: str, limit: int) -> bool:
        """检查IP是否超限（原子操作）"""
        key = f"ip_limit:{ip}"
        lua_script = """
        local current = redis.call('INCR', KEYS[1])
        if current == 1 then
            redis.call('EXPIRE', KEYS[1], 1)
        end
        return current <= tonumber(ARGV[1])
        """
        return bool(self.redis.eval(lua_script, 1, key, str(limit)))

    def _get_client_ip(self, request: Request) -> str:
        """获取真实IP（处理代理）"""
        if "x-forwarded-for" in request.headers:
            return request.headers["x-forwarded-for"].split(",")[0].strip()
        return request.client.host or "0.0.0.0"

rate_limiter = DynamicIPRateLimiter()
from fastapi import Depends, Header, Request, Query, HTTPException
from typing import Optional
import json
from app.core.jwt import verify_token
from app.db import SessionLocal, User
from app.boot import APIException
from ipaddress import ip_address
from app.core.redis_pool import RedisPool
from app.boot import logger

USER_CACHE_PREFIX = "user_cache:"
USER_CACHE_TTL = 300  # 5 分钟


def get_cached_user(user_id: int) -> Optional[User]:
    """从 Redis 获取缓存的用户"""
    try:
        redis_client = RedisPool.get_redis()
        cached_data = redis_client.get(f"{USER_CACHE_PREFIX}{user_id}")
        if cached_data:
            d = json.loads(cached_data)
            user = User()
            user.id = d['id']
            user.username = d['username']
            user.email = d.get('email')
            user.full_name = d.get('full_name')
            user.role = d.get('role', 'member')
            user.fixed = d['fixed']
            user.deleted_at = d.get('deleted_at')
            return user
    except Exception as e:
        logger.debug(f"Redis cache get error: {e}")
    return None


def cache_user(user: User):
    """将用户序列化缓存到 Redis"""
    try:
        redis_client = RedisPool.get_redis()
        user_dict = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name,
            'role': user.role,
            'fixed': user.fixed,
            'deleted_at': str(user.deleted_at) if user.deleted_at else None,
        }
        redis_client.setex(f"{USER_CACHE_PREFIX}{user.id}", USER_CACHE_TTL, json.dumps(user_dict))
    except Exception as e:
        logger.debug(f"Redis cache set error: {e}")


def clear_user_cache(user_id: int = None):
    """清除用户缓存（不传 user_id 则清除全部）"""
    try:
        redis_client = RedisPool.get_redis()
        if user_id:
            redis_client.delete(f"{USER_CACHE_PREFIX}{user_id}")
        else:
            for key in redis_client.scan_iter(match=f"{USER_CACHE_PREFIX}*"):
                redis_client.delete(key)
    except Exception as e:
        logger.debug(f"Redis cache clear error: {e}")


async def get_current_user(
    request: Request,
    token_header: Optional[str] = Header(None, alias="Token"),
    token_query: Optional[str] = Query(None, alias="token"),
) -> User:
    """从 Header 或 Query 获取 Token，验证后返回用户（强制认证）"""
    token = token_header or token_query
    if not token:
        raise APIException(msg="缺少Token", code=401)

    try:
        payload = verify_token(token)
        user_id = int(payload.sub.split('_')[0])

        user = get_cached_user(user_id)
        if not user:
            with SessionLocal() as db:
                user = db.query(User).filter(
                    User.id == user_id,
                    User.deleted_at.is_(None)
                ).first()
                if not user:
                    raise APIException(msg="用户不存在", code=401)
                cache_user(user)

        request.state.user = user
        return user
    except APIException:
        raise
    except Exception as e:
        raise APIException(msg=f"Token验证失败: {str(e)}", code=401)


async def get_state_user(request: Request) -> User:
    """从 request.state 获取已注入的用户（需先走过 get_current_user）"""
    user = getattr(request.state, 'user', None)
    if not user:
        raise APIException(msg="未登录", code=401)
    return user


async def get_current_user_no_err(
    request: Request,
    token: Optional[str] = Header(None, alias="Token"),
) -> Optional[User]:
    """可选认证：token 缺失或无效时返回 None，不抛异常"""
    try:
        if token:
            payload = verify_token(token)
            user_id = int(payload.sub.split('_')[0])

            user = get_cached_user(user_id)
            if not user:
                with SessionLocal() as db:
                    user = db.query(User).filter(
                        User.id == user_id,
                        User.deleted_at.is_(None)
                    ).first()
                    if user:
                        cache_user(user)

            if user and not hasattr(request.state, 'user'):
                request.state.user = user
            return user
    except Exception as e:
        logger.debug(f"get_current_user_no_err failed: {e}")
    return None


def is_admin(user: User) -> bool:
    """统一管理员判定：role=='admin' 或 fixed=True"""
    return (user.role == "admin") or bool(user.fixed)


def apply_tenant_filter(query, model, user: User):
    """管理员看全部数据，普通用户只看自己创建的"""
    if is_admin(user):
        return query
    return query.filter(model.created_by == user.id)


async def get_current_user_id(
    request: Request,
    token: Optional[str] = Header(None, alias="Token"),
) -> int:
    """只取用户 ID"""
    user = await get_current_user(request, token)
    return user.id


async def allow_local_only(request: Request):
    """只允许本机回环地址访问"""
    client_ip = ip_address(request.client.host)
    if client_ip not in (ip_address('127.0.0.1'), ip_address('::1')):
        raise HTTPException(status_code=403, detail="Forbidden")
    return True


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """要求管理员权限（role=='admin' 或 fixed=True）"""
    if not is_admin(current_user):
        raise APIException(msg="需要管理员权限", code=403)
    return current_user


async def require_login(current_user: User = Depends(get_current_user)) -> User:
    """要求登录（admin 或 member 都可）"""
    return current_user


def require_permission(permission: str):
    """验证当前用户是否拥有指定权限"""
    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if is_admin(current_user):
            return current_user
        
        # 精确匹配权限，不再隐式继承父级菜单权限
        # 延迟导入，防止循环依赖
        from app.db import SysRoleMenu
        with SessionLocal() as db:
            has_grant = db.query(SysRoleMenu).filter(
                SysRoleMenu.role == current_user.role,
                SysRoleMenu.menu_key == permission
            ).first()
            if not has_grant:
                raise APIException(msg=f"权限不足，需要权限: {permission}", code=403)
        return current_user
    return dependency


class RateLimiter:
    """Redis 令牌桶/滑动窗口限流依赖项"""
    def __init__(self, limit: int, window: int, name: str = "default"):
        self.limit = limit
        self.window = window
        self.name = name

    async def __call__(self, request: Request) -> bool:
        # 获取真实客户端 IP
        ip = ""
        for header in ("x-forwarded-for", "x-real-ip"):
            if val := request.headers.get(header):
                ips = [i.strip() for i in val.split(",")]
                if ips and ips[0]:
                    ip = ips[0]
                    break
        if not ip:
            ip = request.client.host if request.client else ""

        # 检查是否已有已登录用户，结合 IP/用户 ID 限流
        user_id = None
        user = getattr(request.state, "user", None)
        if user:
            user_id = user.id

        identifier = f"user:{user_id}" if user_id else f"ip:{ip}"
        key = f"rate_limit:{self.name}:{identifier}"

        try:
            r = await RedisPool.get_async_redis()
            current = await r.get(key)
            if current is not None:
                current_val = int(current)
                if current_val >= self.limit:
                    ttl = await r.ttl(key)
                    raise APIException(msg=f"请求过于频繁，请在 {ttl} 秒后重试", code=429, status_code=429)
                else:
                    await r.incr(key)
            else:
                # 管道操作，原子性设置限流 key 和 TTL
                pipe = r.pipeline()
                pipe.set(key, 1, ex=self.window)
                await pipe.execute()
        except APIException:
            raise
        except Exception as e:
            # Redis 故障时降级到放行（保可用性），但用结构化日志便于监控告警
            logger.warning(
                "rate_limiter.degraded "
                f"limiter={self.name} path={request.url.path} method={request.method} "
                f"identifier={identifier} reason={type(e).__name__}: {e}"
            )

        return True


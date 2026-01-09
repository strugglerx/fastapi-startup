"""
Base Scaffold 依赖注入模块
注释了强制用户认证，保留代码供参考
"""
from fastapi import Depends, Header, Request, Query, HTTPException
from typing import Optional
import json
from app.core.jwt import verify_token
from app.db import SessionLocal, User
from app.boot import APIException
from ipaddress import ip_address
from app.core.redis_pool import RedisPool
from app.boot import logger

# 用户缓存配置
USER_CACHE_PREFIX = "user_cache:"
USER_CACHE_TTL = 300  # 缓存5分钟

def get_cached_user(user_id: int) -> Optional[User]:
    """从Redis获取缓存的用户对象"""
    try:
        redis_client = RedisPool.get_redis()
        cache_key = f"{USER_CACHE_PREFIX}{user_id}"
        cached_data = redis_client.get(cache_key)

        if cached_data:
            user_dict = json.loads(cached_data)
            user = User()
            user.id = user_dict['id']
            user.username = user_dict['username']
            user.fixed = user_dict['fixed']
            user.deleted_at = user_dict.get('deleted_at')
            return user
    except Exception as e:
        logger.debug(f"Redis cache get error: {e}")
    return None

def cache_user(user: User):
    """缓存用户对象到Redis"""
    try:
        redis_client = RedisPool.get_redis()
        cache_key = f"{USER_CACHE_PREFIX}{user.id}"

        user_dict = {
            'id': user.id,
            'username': user.username,
            'fixed': user.fixed,
            'deleted_at': str(user.deleted_at) if user.deleted_at else None
        }

        redis_client.setex(
            cache_key,
            USER_CACHE_TTL,
            json.dumps(user_dict)
        )
    except Exception as e:
        logger.debug(f"Redis cache set error: {e}")

def clear_user_cache(user_id: int = None):
    """清除用户缓存"""
    try:
        redis_client = RedisPool.get_redis()
        if user_id:
            cache_key = f"{USER_CACHE_PREFIX}{user_id}"
            redis_client.delete(cache_key)
        else:
            pattern = f"{USER_CACHE_PREFIX}*"
            for key in redis_client.scan_iter(match=pattern):
                redis_client.delete(key)
    except Exception as e:
        logger.debug(f"Redis cache clear error: {e}")

"""
以下函数已注释掉强制认证，如需启用可取消注释
保留代码供未来参考使用
"""

async def get_current_user(
    request: Request,
    token_header: Optional[str] = Header(None, alias="Token"),
    token_query: Optional[str] = Query(None, alias="token")
) -> Optional[User]:
    """
    获取当前用户（带强制认证）
    已注释，如需启用请取消注释
    """
    pass

async def get_state_user(request: Request) -> Optional[User]:
    """
    获取request.state中的用户
    已注释，如需启用请取消注释
    """
    pass

async def get_current_user_no_err(
    request: Request,
    token: Optional[str] = Header(None, alias="Token")
) -> Optional[User]:
    """
    获取当前用户（可选认证，失败不抛异常）
    Base Scaffold 默认使用此函数，不强制要求认证
    """
    try:
        if token:
            payload = verify_token(token)
            user_id, fixed = payload.sub.split('_')
            user_id = int(user_id)

            user = get_cached_user(user_id)

            if not user:
                db = SessionLocal()
                try:
                    user = db.query(User).filter(
                        User.id == user_id,
                        User.deleted_at.is_(None)
                    ).first()

                    if user:
                        cache_user(user)
                finally:
                    db.close()

            if user and not hasattr(request.state, 'user'):
                request.state.user = user

            return user
    except Exception as e:
        logger.debug(f"get_current_user_no_err failed: {e}")

    return None

def apply_tenant_filter(query, model, user: User):
    """
    应用租户过滤
    - 如果用户是管理员 (fixed=True)，返回原查询
    - 如果用户是普通用户 (fixed=False)，只返回该用户创建的数据

    保留供参考
    """
    if user.fixed:
        return query
    else:
        return query.filter(model.created_by == user.id)

async def allow_local_only(request: Request):
    """只允许本地回环地址访问"""
    client_ip = ip_address(request.client.host)
    if client_ip not in [ip_address('127.0.0.1'), ip_address('::1')]:
        raise HTTPException(status_code=403, detail="Forbidden")
    return True

# async def require_admin(current_user: User = Depends(get_current_user)) -> User:
#     """要求管理员权限"""
#     if not current_user.fixed:
#         raise APIException(msg="需要管理员权限", code=403)
#     return current_user

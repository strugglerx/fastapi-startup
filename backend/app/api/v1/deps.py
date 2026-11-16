import os
from fastapi import Depends, Header, Request, Response, Query, HTTPException
from typing import Optional
import json
from app.core.jwt import verify_token
from app.db import SessionLocal, User
from app.boot import APIException
from app.boot.plugins import SKIP_WRAP_HEADER
from ipaddress import ip_address
from app.core.redis_pool import RedisPool
from app.boot import logger

USER_CACHE_PREFIX = "user_cache:"
USER_CACHE_TTL = 300  # 5 分钟


def _open_api_require_access_key() -> bool:
    """生产默认要求带 AccessKey；开发期可通过 `OPEN_API_REQUIRE_ACCESS_KEY=false` 关闭。

    关闭后 /api/openai/v1 退化为「裸 X-User-Key 即可」—— 等于把 token 账单
    暴露给任何能猜对一个 user_key 的人，仅供本地调试使用。
    """
    raw = os.getenv("OPEN_API_REQUIRE_ACCESS_KEY", "true").strip().lower()
    return raw not in ("0", "false", "no", "off")


def raw_response(response: Response) -> None:
    """路由声明式跳过响应包装中间件。

    用法：
        @router.post("", dependencies=[Depends(raw_response)])
        async def jsonrpc_endpoint(...): ...

    设置 X-Skip-Wrap header 标记响应；setup_stand_response 中间件检测后
    跳过 {code, data} 包装并剥离该 header（不暴露给客户端）。

    适用：JSON-RPC（MCP/LSP）、SSE 文本流（虽然有前缀跳过列表兜底）、
    需要严格按上游协议格式返回的代理 / 透传场景。
    """
    response.headers[SKIP_WRAP_HEADER] = "1"


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


def authenticate_token(token: str) -> Optional[User]:
    """供非 FastAPI Depend 场景（如 ASGI 中间件）或内部统一使用的 Token 验证函数

    安全约束：admin 与 visitor token 共用同一个 `JWT_SECRET_KEY`，仅靠
    `sub` 解析失败兜底 visitor token 越权风险脆弱（一旦 visitor_id 改成纯数字
    格式即被 `int()` 接受当成 admin user_id）。这里先显式拒绝 visitor token：
      - `payload.kind == "visitor"`（新签发的 visitor token 都带这个 claim）
      - 或 `sub` 以 "visitor:" 前缀开头（兜底，防止 kind claim 缺失）

    DB 查询已下沉到 AuthService；本函数只负责 token 解析 + 缓存调度。
    """
    try:
        payload = verify_token(token)
        # ─── 拒绝 visitor token：admin 校验入口不接受 widget 访客身份 ───
        kind = getattr(payload, "kind", None)
        if kind is None and hasattr(payload, "model_extra"):
            extra = payload.model_extra or {}
            kind = extra.get("kind")
        sub_str = str(payload.sub or "")
        if kind == "visitor" or sub_str.startswith("visitor:"):
            return None
        user_id = int(sub_str.split('_')[0])

        from app.service import AuthService
        return AuthService.load_user_with_cache(
            user_id,
            cache_get=get_cached_user,
            cache_set=cache_user,
        )
    except Exception:
        return None


async def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    token_header: Optional[str] = Header(None, alias="Token"),
    token_query: Optional[str] = Query(None, alias="token"),
) -> User:
    """从 Header 或 Query 获取 Token，验证后返回用户（强制认证）"""
    # 优先使用 request.state 缓存的已认证用户（如由中间件预解析的）
    user = getattr(request.state, "user", None)
    if user:
        return user

    token = None
    # 1. 尝试从 Authorization (Bearer) 提取
    if authorization:
        if authorization.lower().startswith("bearer "):
            token = authorization[7:].strip()
        else:
            token = authorization.strip()
            
    # 2. 尝试从 Token 头部提取
    if not token and token_header:
        token = token_header.strip()
        
    # 3. 尝试从 Query String 提取
    if not token and token_query:
        token = token_query.strip()

    if not token:
        raise APIException(msg="缺少Token", code=401)

    user = authenticate_token(token)
    if not user:
        raise APIException(msg="Token验证失败", code=401)

    request.state.user = user
    return user


async def get_state_user(request: Request) -> User:
    """从 request.state 获取已注入的用户（需先走过 get_current_user）"""
    user = getattr(request.state, 'user', None)
    if not user:
        raise APIException(msg="未登录", code=401)
    return user


async def get_current_user_no_err(
    request: Request,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    token_header: Optional[str] = Header(None, alias="Token"),
) -> Optional[User]:
    """可选认证：token 缺失或无效时返回 None，不抛异常"""
    try:
        # 优先使用已解析过的用户
        user = getattr(request.state, "user", None)
        if user:
            return user
            
        token = None
        if authorization:
            if authorization.lower().startswith("bearer "):
                token = authorization[7:].strip()
            else:
                token = authorization.strip()
        if not token and token_header:
            token = token_header.strip()

        if token:
            user = authenticate_token(token)
            if user:
                if not hasattr(request.state, 'user'):
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
    authorization: Optional[str] = Header(None, alias="Authorization"),
    token_header: Optional[str] = Header(None, alias="Token"),
) -> int:
    """只取用户 ID"""
    user = await get_current_user(request, authorization, token_header)
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
    """验证当前用户是否拥有指定权限。

    SysRoleMenu 查询已下沉到 AuthService.check_permission（service 层封装
    精确匹配，不做父级继承）；本依赖只负责 admin 短路 + 抛 APIException。
    """
    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if is_admin(current_user):
            return current_user

        # 延迟导入，防止循环依赖
        from app.service import AuthService
        if not AuthService.check_permission(current_user.role, permission):
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
        # 获取真实客户端 IP：走 core.limiter.get_client_ip，受信代理白名单内
        # 才采纳 XFF 首段，否则强制 socket 对端 —— 防止伪造 header 绕过爆破限流。
        from app.core.limiter import get_client_ip
        ip = get_client_ip(request)

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


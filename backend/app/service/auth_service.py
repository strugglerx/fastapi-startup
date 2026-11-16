"""AuthService —— deps.py 鉴权层下沉的 service 入口。

职责：把 `api/v1/deps.py` 内残留的 `with SessionLocal()` 业务查询全部搬过来，
让 deps 退化为「Header 解析 + Redis 缓存调度 + 调 service」的薄壳。

强约束（遵守 CLAUDE.md「三层职责」）：
- 不接触 Request/Response、不接触 FastAPI 类型
- 抛 APIException（不抛 HTTPException）
- 返回 detached ORM 对象（已 expunge），调用方可在 Session 关闭后访问字段；
  不返回带 lazy-load 关系的对象
- Redis 缓存层留在 deps.py：缓存语义跟 request lifecycle 强相关，
  AuthService 只暴露 `load_user_with_cache` 封装 cache check + DB miss 回源
"""
from __future__ import annotations

import json
from typing import Callable, Optional

from app.boot import logger
from app.core.redis_pool import RedisPool
from app.db import SessionLocal, SysRoleMenu, User


class AuthService:
    """鉴权数据访问 service。所有方法 classmethod，无状态。"""

    # Redis 缓存常量（跟 deps.py 保持一致，避免 key prefix 漂移）
    USER_CACHE_PREFIX = "user_cache:"
    USER_CACHE_TTL = 300  # 5 分钟

    # ─────────────────────────── DB 原始查询 ───────────────────────────
    @classmethod
    def get_user_for_login(cls, user_id: int) -> Optional[User]:
        """按 user_id 拉一个未软删的 User（detached，可在 session 关闭后用）。

        给 token 校验入口（authenticate_token）用：cache miss 时回源 DB。
        """
        with SessionLocal() as db:
            user = (
                db.query(User)
                .filter(User.id == user_id, User.deleted_at.is_(None))
                .first()
            )
            if user is not None:
                db.expunge(user)
            return user

    @classmethod
    def get_admin_user(cls, user_id: int) -> Optional[User]:
        """按 user_id 拉一个未软删的 User，admin 路径专用（语义别名）。

        当前实现跟 get_user_for_login 一致，分离命名是为了未来在 admin 路径
        加额外约束（如强制 fixed=True）时不会反过来误伤普通登录。
        """
        return cls.get_user_for_login(user_id)

    @classmethod
    def check_permission(cls, role: Optional[str], perm_key: str) -> bool:
        """校验角色是否拥有指定 menu_key 权限。

        - admin 短路：直接 True（保持跟 deps.is_admin 一致语义；但本方法不
          看 fixed，因为 fixed 是 user 字段而非 role 字段，调用方需在外层
          先用 is_admin(user) 判断后再决定是否需要走本方法）
        - 精确匹配 sys_role_menu.menu_key，不做父级继承
        """
        if role == "admin":
            return True
        with SessionLocal() as db:
            row = (
                db.query(SysRoleMenu)
                .filter(SysRoleMenu.role == role, SysRoleMenu.menu_key == perm_key)
                .first()
            )
            return row is not None

    # ─────────────────────────── 缓存封装 ───────────────────────────
    @classmethod
    def load_user_with_cache(
        cls,
        user_id: int,
        *,
        cache_get: Optional[Callable[[int], Optional[User]]] = None,
        cache_set: Optional[Callable[[User], None]] = None,
    ) -> Optional[User]:
        """带缓存的用户加载：先查 Redis，miss 则回 DB 并回填缓存。

        参数：
            cache_get / cache_set —— 由 deps.py 注入，避免 service 反向依赖
            HTTP 层的 cache 实现细节。两者都 None 时退化为「无缓存直查 DB」。

        Redis 抖动时 cache_get 返回 None（按 deps 内既有降级语义），
        本方法直接走 DB；cache_set 失败也静默不抛。
        """
        if cache_get is not None:
            try:
                cached = cache_get(user_id)
            except Exception as e:
                logger.debug(f"AuthService.cache_get error: {e}")
                cached = None
            if cached is not None:
                return cached

        user = cls.get_user_for_login(user_id)
        if user is not None and cache_set is not None:
            try:
                cache_set(user)
            except Exception as e:
                logger.debug(f"AuthService.cache_set error: {e}")
        return user

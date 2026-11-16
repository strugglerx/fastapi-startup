"""RBAC `require_permission` 依赖测试。

覆盖 7 case：
1. admin role 短路 → 通过（不查 SysRoleMenu）
2. fixed=True 用户（即使 role 非 admin）短路 → 通过
3. 普通成员有授权 → 通过
4. 普通成员无授权 → 抛 APIException 403
5. 撤销授权后立即失效（SysRoleMenu DELETE）
6. 权限 key 不存在 / 任意拼写 → 403
7. require_admin 普通成员 → 403；admin → 通过

依赖：`require_permission` 是 closure 返回 async function，需要直接 await 调用。
执行：
    cd backend && python -m pytest tests/test_rbac.py -xvs
"""
from __future__ import annotations

import asyncio
import os
import tempfile
import uuid

import pytest

# 必须先把环境切到 SQLite + 临时库
_TMP_DB = os.path.join(tempfile.gettempdir(), f"rbac_test_{uuid.uuid4().hex}.db")
os.environ["APP_USE_SQLITE"] = "true"
os.environ["APP_SQLITE_PATH"] = _TMP_DB


@pytest.fixture
def isolated_db(monkeypatch):
    """每个测试一个独立 SQLite + 重绑 SessionLocal。"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    fd, path = tempfile.mkstemp(suffix=".db", prefix="rbac_")
    os.close(fd)

    engine = create_engine(
        f"sqlite:///{path}",
        connect_args={"check_same_thread": False},
    )

    from app.db import models as _models  # noqa: F401
    from app.db.models import Base

    Base.metadata.create_all(bind=engine)

    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    import app.db as app_db
    import app.api.v1.deps as deps_mod
    import app.service.auth_service as auth_service_mod

    monkeypatch.setattr(app_db, "SessionLocal", TestSessionLocal, raising=True)
    monkeypatch.setattr(deps_mod, "SessionLocal", TestSessionLocal, raising=True)
    monkeypatch.setattr(auth_service_mod, "SessionLocal", TestSessionLocal, raising=True)

    yield TestSessionLocal

    engine.dispose()
    try:
        os.unlink(path)
    except OSError:
        pass


def _make_user(role: str = "member", fixed: bool = False, uid: int = 1):
    """生成一个最小 User 对象（不入库），只暴露 is_admin / require_permission 用到的字段。"""
    from app.db.models import User
    u = User()
    u.id = uid
    u.role = role
    u.fixed = fixed
    u.username = f"u_{uid}"
    return u


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro) if not asyncio.iscoroutine(coro) else asyncio.new_event_loop().run_until_complete(coro)


# ════════════════════════ Case 1 & 2：admin / fixed 短路 ════════════════════════
def test_admin_role_short_circuits_without_db_check(isolated_db):
    """role=='admin' 不查 SysRoleMenu，直接通过 —— 即使表里没任何授权。"""
    from app.api.v1.deps import require_permission

    dep = require_permission("system:anything")
    admin = _make_user(role="admin", fixed=False, uid=10)

    result = asyncio.run(dep(admin))
    assert result is admin, "admin 短路应原样返回 current_user"


def test_fixed_user_short_circuits_even_if_role_member(isolated_db):
    """fixed=True 也视为 admin（与 is_admin 一致）。"""
    from app.api.v1.deps import require_permission

    dep = require_permission("system:anything")
    fixed_member = _make_user(role="member", fixed=True, uid=11)
    result = asyncio.run(dep(fixed_member))
    assert result is fixed_member


# ════════════════════════ Case 3：普通成员有授权 → 通过 ════════════════════════
def test_member_with_grant_passes(isolated_db):
    from app.api.v1.deps import require_permission
    from app.db.models import SysRoleMenu

    # 给 member 角色授权 'system:user'
    with isolated_db() as db:
        db.add(SysRoleMenu(role="member", menu_key="system:user"))
        db.commit()

    dep = require_permission("system:user")
    user = _make_user(role="member", fixed=False, uid=20)
    result = asyncio.run(dep(user))
    assert result is user


# ════════════════════════ Case 4：普通成员无授权 → 403 ════════════════════════
def test_member_without_grant_raises_403(isolated_db):
    from app.api.v1.deps import require_permission
    from app.boot import APIException

    dep = require_permission("system:user")
    user = _make_user(role="member", fixed=False, uid=21)

    with pytest.raises(APIException) as ei:
        asyncio.run(dep(user))
    assert ei.value.code == 403
    assert "system:user" in ei.value.msg
    assert "权限不足" in ei.value.msg


# ════════════════════════ Case 5：撤销授权立即失效 ════════════════════════
def test_revoking_grant_takes_effect_immediately(isolated_db):
    from app.api.v1.deps import require_permission
    from app.boot import APIException
    from app.db.models import SysRoleMenu

    # 先授权
    with isolated_db() as db:
        db.add(SysRoleMenu(role="member", menu_key="system:role"))
        db.commit()

    dep = require_permission("system:role")
    user = _make_user(role="member", fixed=False, uid=22)
    assert asyncio.run(dep(user)) is user, "授权后应通过"

    # 撤销
    with isolated_db() as db:
        db.query(SysRoleMenu).filter(
            SysRoleMenu.role == "member",
            SysRoleMenu.menu_key == "system:role",
        ).delete()
        db.commit()

    with pytest.raises(APIException) as ei:
        asyncio.run(dep(user))
    assert ei.value.code == 403


# ════════════════════════ Case 6：不存在的权限 key ════════════════════════
def test_nonexistent_permission_key_rejected(isolated_db):
    """member 调一个完全没人授权的 key → 403（与「无授权」走同一分支）。"""
    from app.api.v1.deps import require_permission
    from app.boot import APIException

    dep = require_permission("totally:made-up:key")
    user = _make_user(role="member", fixed=False, uid=23)

    with pytest.raises(APIException) as ei:
        asyncio.run(dep(user))
    assert ei.value.code == 403


def test_grant_to_different_role_does_not_help_this_user(isolated_db):
    """授权给 admin role 不能让 member 通过 —— 必须精确匹配 user.role。"""
    from app.api.v1.deps import require_permission
    from app.boot import APIException
    from app.db.models import SysRoleMenu

    with isolated_db() as db:
        # 只给 admin 授权（虽然 admin 走短路压根不查表，这里只是确保
        # member 的查询不会被 admin grant 错命中）
        db.add(SysRoleMenu(role="admin", menu_key="system:audit"))
        db.commit()

    dep = require_permission("system:audit")
    member = _make_user(role="member", fixed=False, uid=24)
    with pytest.raises(APIException) as ei:
        asyncio.run(dep(member))
    assert ei.value.code == 403


# ════════════════════════ Case 7：require_admin ════════════════════════
def test_require_admin_member_rejected_admin_passes(isolated_db):
    from app.api.v1.deps import require_admin
    from app.boot import APIException

    admin = _make_user(role="admin", fixed=False, uid=30)
    member = _make_user(role="member", fixed=False, uid=31)

    # admin 通过
    assert asyncio.run(require_admin(admin)) is admin

    # member 拒
    with pytest.raises(APIException) as ei:
        asyncio.run(require_admin(member))
    assert ei.value.code == 403
    assert "管理员" in ei.value.msg

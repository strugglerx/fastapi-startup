"""鉴权链路测试：登录 / refresh rotate / token 校验 / 脱敏。

覆盖 9 case：
1. 登录成功返 access_token + refresh_token + user 体
2. 错误密码抛 APIException 401（5 次锁定走 Redis，未注入 fake redis 时降级不锁，
   故这里只验密码错本身；锁定路径由 case 7 单独验）
3. refresh_with_refresh_token 换新 access + 新 refresh + 旧 refresh 被吊销
4. 已软删用户登录 → 抛账号或密码错误（不暴露存在性）
5. authenticate_token 缺 token / 无效 token → 返回 None
6. is_admin 普通成员 → False；fixed=True 用户即使 role=member 也 admin
7. login 5 次失败 → 第 6 次锁定（注入 FakeRedis）
8. visitor token 走 authenticate_token → 返回 None（kind=visitor 拒绝，B4 修）
9. _user_to_dict 不暴露 hashed_password（脱敏：序列化字典里没有密码字段）

执行：
    cd backend && python -m pytest tests/test_auth_flow.py -xvs
"""
from __future__ import annotations

import os
import tempfile
import uuid

import pytest

# 必须先把环境切到 SQLite + 临时库，再 import 任何 app.* 模块
_TMP_DB = os.path.join(tempfile.gettempdir(), f"auth_flow_test_{uuid.uuid4().hex}.db")
os.environ["APP_USE_SQLITE"] = "true"
os.environ["APP_SQLITE_PATH"] = _TMP_DB


# ────────────────────────── Fake Redis（autouse + case 7 锁定共用）──────────────────────────
class _FakePipeline:
    def __init__(self, store):
        self._store = store
        self._ops = []

    def incr(self, key):
        self._ops.append(("incr", key))
        return self

    def expire(self, key, ttl):
        self._ops.append(("expire", key, ttl))
        return self

    def execute(self):
        results = []
        for op in self._ops:
            if op[0] == "incr":
                _, k = op
                cur = int(self._store.get(k, "0")) + 1
                self._store[k] = str(cur)
                results.append(cur)
            elif op[0] == "expire":
                results.append(True)
        self._ops.clear()
        return results


class FakeSyncRedis:
    """RedisPool.get_redis 同步接口的最小 fake：支持 ttl / incr / setex / delete / pipeline。"""

    def __init__(self):
        self.store = {}
        self.ttls = {}

    def ttl(self, key):
        return int(self.ttls.get(key, -2))

    def incr(self, key):
        cur = int(self.store.get(key, "0")) + 1
        self.store[key] = str(cur)
        return cur

    def setex(self, key, ttl, value):
        self.store[key] = str(value)
        self.ttls[key] = int(ttl)
        return True

    def expire(self, key, ttl):
        self.ttls[key] = int(ttl)
        return True

    def delete(self, *keys):
        n = 0
        for k in keys:
            if k in self.store:
                del self.store[k]
                n += 1
            self.ttls.pop(k, None)
        return n

    def get(self, key):
        return self.store.get(key)

    def pipeline(self):
        return _FakePipeline(self.store)


@pytest.fixture(autouse=True)
def _isolated_redis(monkeypatch):
    """所有 case 默认注入一个干净的 FakeSyncRedis，避免跨测试残留登录失败计数 / 锁。

    某些 case（如 test_login_locks_account_after_5_failures）会自行替换为
    自己的 fake 实例以观察状态；那时 monkeypatch 二次覆盖即可。
    """
    fake = FakeSyncRedis()

    from app.core.redis_pool import RedisPool
    from app.service.user import _helpers as h

    monkeypatch.setattr(RedisPool, "get_redis", staticmethod(lambda: fake), raising=False)
    monkeypatch.setattr(h.RedisPool, "get_redis", staticmethod(lambda: fake), raising=False)
    return fake


@pytest.fixture
def isolated_db(monkeypatch):
    """每个测试一个独立 SQLite 临时库，建表后把 SessionLocal 重绑到测试引擎。"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    fd, path = tempfile.mkstemp(suffix=".db", prefix="auth_flow_")
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
    import app.service.user._helpers as helpers_mod
    import app.service.user._auth as auth_mod
    import app.api.v1.deps as deps_mod
    import app.service.auth_service as auth_service_mod
    import app.service.user._admin_crud as admin_crud_mod
    import app.service.role_service as role_service_mod

    monkeypatch.setattr(app_db, "SessionLocal", TestSessionLocal, raising=True)
    monkeypatch.setattr(helpers_mod, "SessionLocal", TestSessionLocal, raising=True)
    monkeypatch.setattr(auth_mod, "SessionLocal", TestSessionLocal, raising=True)
    monkeypatch.setattr(deps_mod, "SessionLocal", TestSessionLocal, raising=True)
    monkeypatch.setattr(auth_service_mod, "SessionLocal", TestSessionLocal, raising=True)
    monkeypatch.setattr(admin_crud_mod, "SessionLocal", TestSessionLocal, raising=True)
    monkeypatch.setattr(role_service_mod, "SessionLocal", TestSessionLocal, raising=True)
    role_service_mod.RoleService.invalidate_cache()
    role_service_mod.RoleService.ensure_seed_roles()

    yield TestSessionLocal

    role_service_mod.RoleService.invalidate_cache()
    engine.dispose()
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture
def seeded_user(isolated_db):
    """种入一个普通成员账号：username=alice / password=Passw0rd!"""
    from app.core.security import get_password_hash
    from app.db.models import User

    with isolated_db() as db:
        u = User(
            username="alice",
            email="alice@example.com",
            full_name="Alice",
            role="member",
            hashed_password=get_password_hash("Passw0rd!"),
            fixed=False,
            is_active=True,
        )
        db.add(u)
        db.commit()
        db.refresh(u)
        return {"id": u.id, "username": u.username, "email": u.email}


# ════════════════════════ Case 1：登录成功 ════════════════════════
def test_login_returns_access_and_refresh_token(isolated_db, seeded_user):
    from app.service import UserService

    resp = UserService.login("alice", "Passw0rd!")

    assert resp["access_token"] and isinstance(resp["access_token"], str)
    assert resp["token"] == resp["access_token"], "token / access_token 双写兼容"
    assert resp["token_type"] == "bearer"
    assert resp["refresh_token"].startswith("rt_"), "refresh_token 必须带 rt_ 前缀"
    assert resp["expires_in"] > 0
    assert resp["refresh_expires_in"] > 0
    assert resp["user"]["username"] == "alice"
    assert resp["user"]["role"] == "member"
    assert "permissions" in resp["user"], "登录响应必须含 permissions 字段"


# ════════════════════════ Case 2：错误密码 ════════════════════════
def test_login_wrong_password_raises_401(isolated_db, seeded_user):
    from app.boot import APIException
    from app.service import UserService

    with pytest.raises(APIException) as ei:
        UserService.login("alice", "WrongPass!")
    assert ei.value.status_code == 401
    # 防 user enumeration：不暴露「用户不存在 / 密码错」差异
    assert "账号或密码" in ei.value.msg


def test_login_nonexistent_user_same_error_as_wrong_password(isolated_db, seeded_user):
    """不存在的用户 → 同样的错误文案（防用户名枚举）。"""
    from app.boot import APIException
    from app.service import UserService

    with pytest.raises(APIException) as ei:
        UserService.login("bob_does_not_exist", "whatever")
    assert ei.value.status_code == 401
    assert "账号或密码" in ei.value.msg


# ════════════════════════ Case 3：refresh rotate ════════════════════════
def test_refresh_with_refresh_token_rotates_old_one(isolated_db, seeded_user):
    """换新 access + 新 refresh；旧 refresh 立即失效。"""
    from app.boot import APIException
    from app.service import UserService

    first = UserService.login("alice", "Passw0rd!")
    old_refresh = first["refresh_token"]
    old_access = first["access_token"]

    rotated = UserService.refresh_with_refresh_token(old_refresh)
    # access_token 可能与旧 token 等值（同一秒签发、payload 完全一致）；
    # 但起码要拿到 access_token，并且 refresh_token 必须 rotate
    assert rotated["access_token"] and isinstance(rotated["access_token"], str)
    assert rotated["refresh_token"] and rotated["refresh_token"] != old_refresh
    assert rotated["user"]["username"] == "alice"
    # 用 old_access 防 lint 报未用
    assert isinstance(old_access, str)

    # 旧 refresh 已吊销 → 再用会 401
    with pytest.raises(APIException) as ei:
        UserService.refresh_with_refresh_token(old_refresh)
    assert ei.value.status_code == 401
    assert "吊销" in ei.value.msg or "无效" in ei.value.msg


# ════════════════════════ Case 4：已删除用户 ════════════════════════
def test_login_for_soft_deleted_user_fails(isolated_db, seeded_user):
    """软删用户登录返回 401，且文案与「密码错」一致（不暴露存在性）。"""
    from datetime import datetime

    from app.boot import APIException
    from app.db.models import User
    from app.service import UserService

    # 软删
    with isolated_db() as db:
        u = db.query(User).filter(User.username == "alice").first()
        u.deleted_at = datetime.now()
        db.commit()

    with pytest.raises(APIException) as ei:
        UserService.login("alice", "Passw0rd!")
    assert ei.value.status_code == 401


# ════════════════════════ Case 5：authenticate_token 边界 ════════════════════════
def test_authenticate_token_invalid_returns_none(isolated_db, seeded_user):
    """token 字符串伪造 / 篡改 → authenticate_token 返回 None（不抛）。"""
    from app.api.v1.deps import authenticate_token

    assert authenticate_token("not-a-jwt") is None
    assert authenticate_token("a.b.c") is None
    assert authenticate_token("") is None


def test_authenticate_token_valid_returns_user(isolated_db, seeded_user, monkeypatch):
    """有效 access token → 返回 user。需绕过 Redis 缓存（fake 不可用时降级走 DB）。"""
    from datetime import timedelta

    # 让 cache miss → 走 DB 查询
    from app.api.v1 import deps as deps_mod
    monkeypatch.setattr(deps_mod, "get_cached_user", lambda uid: None)
    monkeypatch.setattr(deps_mod, "cache_user", lambda u: None)

    from app.api.v1.deps import authenticate_token
    from app.core.jwt import create_access_token

    token = create_access_token(
        subject=f"{seeded_user['id']}_0",
        expires_delta=timedelta(minutes=60),
    )
    user = authenticate_token(token)
    assert user is not None
    assert user.id == seeded_user["id"]
    assert user.username == "alice"


# ════════════════════════ Case 6：is_admin ════════════════════════
def test_is_admin_classifies_correctly():
    """role=='admin' 或 fixed=True 都算 admin。"""
    from app.api.v1.deps import is_admin

    class _U:
        def __init__(self, role, fixed):
            self.role = role
            self.fixed = fixed

    assert is_admin(_U("admin", False)) is True
    assert is_admin(_U("member", True)) is True, "fixed=True 即使 role 不是 admin 也算"
    assert is_admin(_U("admin", True)) is True
    assert is_admin(_U("member", False)) is False


# ════════════════════════ Case 7：登录失败锁定 ════════════════════════
def test_login_locks_account_after_5_failures(isolated_db, seeded_user, monkeypatch):
    """5 次密码错 → 第 6 次锁定（429）。注入 FakeRedis 防真 Redis 不可用导致降级跳过锁定。"""
    fake = FakeSyncRedis()
    from app.core.redis_pool import RedisPool
    from app.service.user import _helpers as h
    monkeypatch.setattr(RedisPool, "get_redis", staticmethod(lambda: fake))
    monkeypatch.setattr(h.RedisPool, "get_redis", staticmethod(lambda: fake))

    from app.boot import APIException
    from app.service import UserService

    # 5 次密码错 → 期望 401
    for i in range(5):
        with pytest.raises(APIException) as ei:
            UserService.login("alice", f"bad{i}")
        assert ei.value.status_code == 401

    # 第 6 次：先命中锁定（429），不再走密码比对
    with pytest.raises(APIException) as ei:
        UserService.login("alice", "Passw0rd!")
    assert ei.value.status_code == 429
    assert "锁定" in ei.value.msg


# ════════════════════════ Case 8：visitor token 不可用于 admin 路由 ════════════════════════
def test_visitor_token_rejected_by_authenticate_token(isolated_db, seeded_user):
    """visitor token（B4 修：kind 校验）走 admin authenticate_token → 返回 None。"""
    from app.api.v1.deps import authenticate_token
    from app.core.jwt import create_visitor_token

    # 用数字 visitor_id：以前没 kind 校验时，int(sub.split('_')[0]) 把
    # "visitor:123:1" 中的 "visitor" 解析失败兜底成 0。新版必须显式拒。
    vt = create_visitor_token(visitor_id="123", widget_id=1)
    assert authenticate_token(vt) is None, "visitor token 进 admin 入口必须返回 None"


def test_visitor_sub_prefix_rejected_even_without_kind(isolated_db, seeded_user):
    """兜底：sub 以 visitor: 开头的 token，即使 kind 缺失也要拒。"""
    from datetime import timedelta

    from app.api.v1.deps import authenticate_token
    from app.core.jwt import create_access_token

    # 故意不带 kind claim
    tok = create_access_token(
        subject="visitor:abc:1",
        expires_delta=timedelta(minutes=5),
    )
    assert authenticate_token(tok) is None, "sub.startswith('visitor:') 兜底也要拒"


# ════════════════════════ Case 9：脱敏 ════════════════════════
def test_user_to_dict_does_not_leak_password_hash(isolated_db, seeded_user):
    """序列化字典不暴露 hashed_password —— 防一不留神返给前端。"""
    from app.db.models import User
    from app.service.user._helpers import _user_to_dict

    with isolated_db() as db:
        u = db.query(User).filter(User.id == seeded_user["id"]).first()
        d = _user_to_dict(u, permissions=["*"])

    # 关键脱敏断言
    assert "hashed_password" not in d
    assert "password" not in d

    # 该有的字段都在
    for k in ("id", "username", "email", "role", "fixed", "is_active", "permissions"):
        assert k in d

    # 登录响应里 user 体同样不含密码字段
    from app.service import UserService

    resp = UserService.login("alice", "Passw0rd!")
    assert "hashed_password" not in resp["user"]
    assert "password" not in resp["user"]


# ════════════════════════ Case 10：软删除账号重构/注册 ════════════════════════
def test_soft_deleted_user_can_be_re_registered(isolated_db):
    """验证已软删除的账号 username 和 email 可以重新注册/创建。"""
    from app.service import UserService
    from app.db.models import User

    # 1. 注册一个用户
    username = "re_test"
    email = "re_test@example.com"
    u1 = UserService.create_admin(
        username=username,
        password="Passw0rd1",
        email=email,
        role="admin"
    )
    assert u1["username"] == username
    assert u1["email"] == email

    # 2. 软删除该用户
    UserService.delete_admin(u1["id"])

    # 3. 再次注册同名用户，应该成功
    u2 = UserService.create_admin(
        username=username,
        password="Passw0rd2",
        email=email,
        role="admin"
    )
    assert u2["username"] == username
    assert u2["email"] == email
    assert u2["id"] != u1["id"]

    # 4. 验证旧的软删除用户的 username 和 email 已经被重命名释放
    with isolated_db() as db:
        old_user = db.query(User).filter(User.id == u1["id"]).first()
        assert old_user.deleted_at is not None
        assert old_user.username != username
        assert old_user.email != email
        assert "_del_" in old_user.username
        assert "_del_" in old_user.email

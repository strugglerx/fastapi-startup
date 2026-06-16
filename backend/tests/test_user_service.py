"""UserService 业务层测试（无需 HTTP）

约定：所有业务异常用 APIException + 业务 code 表达，HTTP 状态不参与判断。
"""
import uuid

import pytest

from app.boot import APIException
from app.service import UserService


def _u() -> str:
    return f"u_{uuid.uuid4().hex[:8]}"


def _code(exc: APIException) -> int:
    """从 APIException 取业务 code"""
    return exc.detail.get("code") if isinstance(exc.detail, dict) else None


def test_register_and_login():
    name = _u()
    res = UserService.register(name, "secret123")
    assert res["id"] > 0
    assert res["username"] == name

    token = UserService.login(name, "secret123")
    assert token["access_token"]
    assert token["token_type"] == "bearer"
    assert token["user"]["username"] == name


def test_register_duplicate_rejected():
    name = _u()
    UserService.register(name, "secret123")
    with pytest.raises(APIException) as exc:
        UserService.register(name, "secret123")
    assert _code(exc.value) == 10003


def test_register_short_username():
    with pytest.raises(APIException) as exc:
        UserService.register("a", "secret123")
    assert _code(exc.value) == 10001


def test_register_short_password():
    with pytest.raises(APIException) as exc:
        UserService.register(_u(), "123")
    assert _code(exc.value) == 10002


def test_login_wrong_password():
    name = _u()
    UserService.register(name, "secret123")
    with pytest.raises(APIException) as exc:
        UserService.login(name, "wrong")
    assert _code(exc.value) == 10004


def test_login_unknown_user():
    with pytest.raises(APIException) as exc:
        UserService.login("does-not-exist", "whatever")
    assert _code(exc.value) == 10004


def test_list_users_paginated():
    UserService.register(_u(), "secret123")
    result = UserService.list_users(page=1, size=5)
    assert "total" in result
    assert "items" in result
    assert len(result["items"]) <= 5


def test_delete_user_then_not_found():
    name = _u()
    created = UserService.register(name, "secret123")
    UserService.delete_user(created["id"])

    with pytest.raises(APIException) as exc:
        UserService.delete_user(created["id"])
    assert _code(exc.value) == 10005


def test_cannot_delete_admin():
    """admin 账户 fixed=True，禁止删除"""
    from app.db import SessionLocal, User
    with SessionLocal() as db:
        admin = db.query(User).filter(User.fixed.is_(True)).first()
        assert admin, "种子数据应包含一个 fixed=True 的管理员"
        admin_id = admin.id

    with pytest.raises(APIException) as exc:
        UserService.delete_user(admin_id)
    assert _code(exc.value) == 10006

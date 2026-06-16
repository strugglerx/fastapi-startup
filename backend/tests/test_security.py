"""bcrypt 密码哈希测试"""
from app.core.security import get_password_hash, verify_password


def test_hash_starts_with_bcrypt_marker():
    h = get_password_hash("hello")
    assert h.startswith("$2")


def test_verify_correct_password():
    h = get_password_hash("super-secret")
    assert verify_password("super-secret", h)


def test_verify_wrong_password():
    h = get_password_hash("super-secret")
    assert not verify_password("wrong", h)


def test_two_hashes_of_same_password_differ():
    """每次 salt 不同，hash 也应不同"""
    a = get_password_hash("same")
    b = get_password_hash("same")
    assert a != b
    assert verify_password("same", a)
    assert verify_password("same", b)

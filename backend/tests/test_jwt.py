"""JWT 编解码、过期、签名校验测试"""
from datetime import timedelta
import pytest

from app.core.jwt import create_access_token, verify_token, decode_token, JWTError


def test_create_and_verify_roundtrip():
    token = create_access_token("user_42", expires_delta=timedelta(minutes=5))
    payload = verify_token(token)
    assert payload.sub == "user_42"
    assert payload.exp > 0


def test_expired_token_raises():
    token = create_access_token("user_1", expires_delta=timedelta(seconds=-1))
    with pytest.raises(JWTError):
        verify_token(token)


def test_decode_token_ignores_expiration():
    """decode_token 不校验过期，应能解出已过期的令牌"""
    token = create_access_token("user_1", expires_delta=timedelta(seconds=-1))
    payload = decode_token(token)
    assert payload.sub == "user_1"


def test_tampered_signature_rejected():
    token = create_access_token("user_1", expires_delta=timedelta(minutes=5))
    parts = token.split(".")
    # 把签名段整体替换为一个不同的有效 base64url 字符串
    tampered_sig = "A" * len(parts[2])
    tampered = f"{parts[0]}.{parts[1]}.{tampered_sig}"
    with pytest.raises(JWTError):
        verify_token(tampered)


def test_tampered_payload_rejected():
    token = create_access_token("user_1", expires_delta=timedelta(minutes=5))
    parts = token.split(".")
    # 改 payload 后签名校验必然失败
    tampered = f"{parts[0]}.{parts[1][:-4] + 'AAAA'}.{parts[2]}"
    with pytest.raises(JWTError):
        verify_token(tampered)


def test_malformed_token_rejected():
    with pytest.raises(JWTError):
        verify_token("not-a-valid-jwt")

import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from app.boot.config import settings
from app.schema.token import TokenPayload


class JWTError(Exception):
    pass


def _utcnow_ts() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def base64url_decode(data: str) -> bytes:
    pad = -len(data) % 4
    return base64.urlsafe_b64decode(data + "=" * pad)


def _sign(message: bytes) -> bytes:
    return hmac.new(settings.jwt.secret_key.encode("utf-8"), message, hashlib.sha256).digest()


def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[Dict[str, Any]] = None,
) -> str:
    now = datetime.now(timezone.utc)
    ttl = expires_delta or timedelta(minutes=settings.jwt.expire_minutes if settings.jwt.expire_minutes > 0 else 120)
    exp = now + ttl

    header = {"alg": "HS256", "typ": "JWT"}
    payload: Dict[str, Any] = {
        "sub": subject,
        "exp": int(exp.timestamp()),
        "iat": int(now.timestamp()),
    }
    if additional_claims:
        payload.update(additional_claims)

    encoded_header = base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    encoded_payload = base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    message = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    encoded_signature = base64url_encode(_sign(message))

    return f"{encoded_header}.{encoded_payload}.{encoded_signature}"


def _decode(token: str, verify_exp: bool) -> TokenPayload:
    try:
        encoded_header, encoded_payload, encoded_signature = token.split(".")
    except ValueError as e:
        raise JWTError("无效的令牌格式") from e

    message = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    expected = _sign(message)
    try:
        signature = base64url_decode(encoded_signature)
    except Exception as e:
        raise JWTError("无效的签名编码") from e

    if not hmac.compare_digest(signature, expected):
        raise JWTError("无效的签名")

    try:
        payload_data = json.loads(base64url_decode(encoded_payload).decode("utf-8"))
    except Exception as e:
        raise JWTError("无效的负载格式") from e

    if verify_exp:
        exp = payload_data.get("exp")
        if exp is not None and int(exp) < _utcnow_ts():
            raise JWTError("令牌已过期")

    try:
        return TokenPayload(**payload_data)
    except Exception as e:
        raise JWTError(f"令牌字段不合法: {e}") from e


def verify_token(token: str) -> TokenPayload:
    return _decode(token, verify_exp=True)


def decode_token(token: str) -> TokenPayload:
    return _decode(token, verify_exp=False)

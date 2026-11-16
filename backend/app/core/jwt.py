import base64
import hashlib
import hmac
import json
import uuid
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
        # jti：随机化 claim，保证同一秒签发的两条 token signature 必然不同
        # （fix flaky test_refresh_with_refresh_token_rotates_old_one），
        # 同时为后续 token 黑名单 / 撤销留出 claim 入口。
        "jti": uuid.uuid4().hex,
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


# ─────────────────────────────────────────────────────────────────────────
# Visitor Token —— Widget 嵌入接入用的短期 JWT，跟 admin user JWT 完全隔离。
# sub 格式：visitor:<visitor_id>:<widget_id>
# 验证后只能访问绑定的 widget；不能继承 admin 权限。
# ─────────────────────────────────────────────────────────────────────────
_VISITOR_SUB_PREFIX = "visitor:"


def create_visitor_token(
    visitor_id: str,
    widget_id: int,
    expires_minutes: int = 120,
) -> str:
    """签发 widget 访客 token。subject = visitor:<vid>:<wid>。

    expires_minutes：默认 2 小时，访客刷一次就重发，不长期持有。
    """
    subject = f"{_VISITOR_SUB_PREFIX}{visitor_id}:{int(widget_id)}"
    return create_access_token(
        subject=subject,
        expires_delta=timedelta(minutes=max(5, expires_minutes)),
        additional_claims={"kind": "visitor"},
    )


def parse_visitor_token(token: str) -> Dict[str, Any]:
    """解析访客 token，返回 {visitor_id, widget_id}。失败抛 JWTError。

    强校验 `kind == "visitor"` —— 防止有人拿 admin token 当 visitor token 用
    （两者共用同一个 JWT_SECRET_KEY，仅靠 sub 前缀检查不足以隔离签名通过的
    admin token，必须显式 reject 非 visitor kind 的 payload）。
    """
    payload = _decode(token, verify_exp=True)
    kind = getattr(payload, "kind", None)
    if kind is None:
        extra = getattr(payload, "model_extra", None) or {}
        kind = extra.get("kind")
    if kind != "visitor":
        raise JWTError("非 visitor token")
    sub = payload.sub or ""
    if not sub.startswith(_VISITOR_SUB_PREFIX):
        raise JWTError("非 visitor token")
    rest = sub[len(_VISITOR_SUB_PREFIX):]
    try:
        visitor_id, widget_id_str = rest.rsplit(":", 1)
        widget_id = int(widget_id_str)
    except Exception as e:
        raise JWTError(f"visitor sub 格式错误: {sub}") from e
    if not visitor_id:
        raise JWTError("visitor_id 为空")
    return {"visitor_id": visitor_id, "widget_id": widget_id}

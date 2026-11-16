"""通用敏感字段加解密 —— 用于 AccessKey / 配置密码 / 敏感存储等。

基于 JWT_SECRET_KEY 衍生稳定 Fernet key（对称加密）。解密失败时透传原值，
因此兼容历史明文数据 —— 升级后旧数据照常工作，下次写入时自动加密。
"""
import base64
import hashlib
from cryptography.fernet import Fernet

from app.boot import logger
from app.boot.config import settings


def _get_fernet() -> Fernet:
    secret = getattr(settings.jwt, "secret_key", None) or "default_fallback_secret_key"
    key_hash = hashlib.sha256(secret.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key_hash))


def encrypt_secret(plain: str) -> str:
    """加密。空串原样返回。"""
    if not plain:
        return ""
    try:
        return _get_fernet().encrypt(plain.encode()).decode()
    except Exception as e:
        logger.error(f"crypto encrypt 失败: {e}")
        return plain


def decrypt_secret(stored: str) -> str:
    """解密。失败时返回原值（兼容历史明文）。"""
    if not stored:
        return ""
    try:
        return _get_fernet().decrypt(stored.encode()).decode()
    except Exception:
        return stored


def mask_secret(plain: str, *, head: int = 4, tail: int = 4) -> str:
    """脱敏：前 head + ***** + 后 tail。"""
    if not plain:
        return ""
    if len(plain) <= head + tail:
        return "*" * len(plain)
    return f"{plain[:head]}{'*' * (len(plain) - head - tail)}{plain[-tail:]}"


import re

import bcrypt

from app.boot import APIException


PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def validate_password_strength(password: str) -> None:
    """密码强度策略（实用而非严苛）：
        - 长度 ≥ 8 且 ≤ 128
        - 至少包含 1 个字母 + 1 个数字
        - 不允许全部为同一字符
    不通过时抛 APIException(code=10020, status_code=400)。
    """
    if not isinstance(password, str):
        raise APIException("密码格式无效", code=10020, status_code=400)
    if len(password) < PASSWORD_MIN_LENGTH:
        raise APIException(f"密码长度不少于 {PASSWORD_MIN_LENGTH} 位", code=10020, status_code=400)
    if len(password) > PASSWORD_MAX_LENGTH:
        raise APIException(f"密码长度不能超过 {PASSWORD_MAX_LENGTH} 位", code=10020, status_code=400)
    if not re.search(r"[A-Za-z]", password):
        raise APIException("密码必须包含至少 1 个字母", code=10020, status_code=400)
    if not re.search(r"\d", password):
        raise APIException("密码必须包含至少 1 个数字", code=10020, status_code=400)
    if len(set(password)) <= 1:
        raise APIException("密码过于简单", code=10020, status_code=400)

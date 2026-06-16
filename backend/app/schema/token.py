from typing import Optional
from pydantic import BaseModel, ConfigDict


class TokenPayload(BaseModel):
    """JWT 负载模型（exp/iat 为 Unix 时间戳）"""
    sub: str
    exp: int
    iat: Optional[int] = None
    jti: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, extra="allow")


class TokenResponse(BaseModel):
    """登录令牌响应"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int  # 过期时间（秒）

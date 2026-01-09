from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class TokenPayload(BaseModel):
    """JWT 负载模型"""
    sub: str  # 主题(用户ID/用户名)
    exp: datetime  # 过期时间
    iat: Optional[datetime] = None  # 签发时间
    jti: Optional[str] = None  # JWT ID
    
    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    """令牌响应模型"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # 过期时间(秒)
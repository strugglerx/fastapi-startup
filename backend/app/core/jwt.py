import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from app.boot.config import settings
from app.schema.token import TokenPayload

class JWTError(Exception):
    """自定义JWT错误"""
    pass

def base64url_encode(data: bytes) -> str:
    """Base64URL编码"""
    return base64.urlsafe_b64encode(data).decode('utf-8').replace('=', '')

def base64url_decode(data: str) -> bytes:
    """Base64URL解码"""
    padding = len(data) % 4
    if padding:
        data += '=' * (4 - padding)
    return base64.urlsafe_b64decode(data)

def create_access_token(
    subject: str,
    expires_delta: timedelta = None,
    additional_claims: Optional[Dict[str, Any]] = None
) -> str:
    """
    生成JWT令牌 (HMAC SHA256实现)
    
    Args:
        subject: 令牌主题(用户ID/用户名)
        expires_delta: 过期时间间隔
        additional_claims: 额外声明
        
    Returns:
        str: JWT令牌
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes= settings.jwt.expire_minutes if  settings.jwt.expire_minutes>0 else 120
        )
    
    header = {
        "alg": "HS256",
        "typ": "JWT"
    }
    
    payload = {
        "sub": subject,
        "exp": int(expire.timestamp()),
        "iat": int(datetime.utcnow().timestamp())
    }
    
    if additional_claims:
        payload.update(additional_claims)
    
    # 编码header和payload
    encoded_header = base64url_encode(json.dumps(header).encode('utf-8'))
    encoded_payload = base64url_encode(json.dumps(payload).encode('utf-8'))
    
    # 创建签名
    message = f"{encoded_header}.{encoded_payload}".encode('utf-8')
    signature = hmac.new(
        settings.jwt.secret_key.encode('utf-8'),
        message,
        hashlib.sha256
    ).digest()
    encoded_signature = base64url_encode(signature)
    
    return f"{encoded_header}.{encoded_payload}.{encoded_signature}"

def verify_token(token: str) -> TokenPayload:
    """
    验证JWT令牌
    
    Args:
        token: JWT令牌
        
    Returns:
        TokenPayload: 解码后的令牌内容
        
    Raises:
        JWTError: 令牌无效或过期
    """
    try:
        # 分割token
        encoded_header, encoded_payload, encoded_signature = token.split('.')
        
        # 验证签名
        message = f"{encoded_header}.{encoded_payload}".encode('utf-8')
        expected_signature = hmac.new(
            settings.jwt.secret_key.encode('utf-8'),
            message,
            hashlib.sha256
        ).digest()
        
        signature = base64url_decode(encoded_signature)
        if not hmac.compare_digest(signature, expected_signature):
            raise JWTError("无效的签名")
        
        # 解码payload
        payload_data = json.loads(base64url_decode(encoded_payload).decode('utf-8'))
        
        # 检查过期时间
        if 'exp' in payload_data and payload_data['exp'] < datetime.utcnow().timestamp():
            raise JWTError("令牌已过期")
        
        return TokenPayload(**payload_data)
    except (ValueError, json.JSONDecodeError, KeyError) as e:
        raise JWTError("无效的令牌格式") from e

def decode_token(token: str) -> TokenPayload:
    """
    验证JWT令牌
    
    Args:
        token: JWT令牌
        
    Returns:
        TokenPayload: 解码后的令牌内容
        
    """
    try:
        # 分割token
        encoded_header, encoded_payload, encoded_signature = token.split('.')
        
        # 验证签名
        message = f"{encoded_header}.{encoded_payload}".encode('utf-8')
        expected_signature = hmac.new(
            settings.jwt.secret_key.encode('utf-8'),
            message,
            hashlib.sha256
        ).digest()
        
        signature = base64url_decode(encoded_signature)
        if not hmac.compare_digest(signature, expected_signature):
            raise JWTError("无效的签名")
        
        # 解码payload
        payload_data = json.loads(base64url_decode(encoded_payload).decode('utf-8'))
        
        return TokenPayload(**payload_data)
    except (ValueError, json.JSONDecodeError, KeyError) as e:
        raise JWTError("无效的令牌格式") from e
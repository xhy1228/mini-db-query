# -*- coding: utf-8 -*-
"""
多源数据查询小程序版 - 安全模块
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from cryptography.fernet import Fernet
import base64
import hashlib

from core.config import settings


# HTTP Bearer认证
security = HTTPBearer()


def _get_fernet_key() -> bytes:
    """从JWT密钥生成Fernet密钥"""
    key = hashlib.sha256(settings.JWT_SECRET_KEY.encode()).digest()
    return base64.urlsafe_b64encode(key)


def encrypt_password(plain_password: str) -> str:
    """
    加密密码（可逆，用于存储数据库连接密码）
    
    Args:
        plain_password: 明文密码
        
    Returns:
        加密后的密码字符串
    """
    if not plain_password:
        return ""
    f = Fernet(_get_fernet_key())
    encrypted = f.encrypt(plain_password.encode())
    return encrypted.decode()


def decrypt_password(encrypted_password: str) -> str:
    """
    解密密码
    
    Args:
        encrypted_password: 加密的密码
        
    Returns:
        明文密码
    """
    if not encrypted_password:
        return ""
    try:
        f = Fernet(_get_fernet_key())
        decrypted = f.decrypt(encrypted_password.encode())
        return decrypted.decode()
    except Exception:
        # 如果解密失败，可能是明文密码（兼容旧数据）
        return encrypted_password


class TokenData(BaseModel):
    """Token数据"""
    user_id: Optional[str] = None
    openid: Optional[str] = None
    role: Optional[str] = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    if isinstance(plain_password, str):
        plain_password = plain_password.encode('utf-8')
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
    try:
        return bcrypt.checkpw(plain_password, hashed_password)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    if isinstance(password, str):
        password = password.encode('utf-8')
    hashed = bcrypt.hashpw(password, bcrypt.gensalt())
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建访问令牌
    
    Args:
        data: 要编码的数据
        expires_delta: 过期时间增量
        
    Returns:
        JWT令牌
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenData]:
    """
    解码访问令牌
    
    Args:
        token: JWT令牌
        
    Returns:
        TokenData或None
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        openid: str = payload.get("openid")
        role: str = payload.get("role", "user")
        
        if user_id is None:
            return None
        
        return TokenData(user_id=user_id, openid=openid, role=role)
    except JWTError:
        return None


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """
    获取当前用户
    
    Args:
        credentials: HTTP认证凭据
        
    Returns:
        TokenData
        
    Raises:
        HTTPException: 认证失败
    """
    token = credentials.credentials
    token_data = decode_access_token(token)
    
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_data


async def get_current_admin(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """
    获取当前管理员用户
    
    Args:
        current_user: 当前用户
        
    Returns:
        TokenData
        
    Raises:
        HTTPException: 权限不足
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    return current_user

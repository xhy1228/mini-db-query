# -*- coding: utf-8 -*-
"""
多源数据查询小程序版 - 核心配置
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用信息
    APP_NAME: str = "多源数据查询小程序"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # 微信小程序配置
    WECHAT_APPID: str = ""
    WECHAT_SECRET: str = ""
    
    # JWT配置
    JWT_SECRET_KEY: str = "mini-db-query-secret-key-2026"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天
    
    # 数据库配置（存储用户、配置等）
    DATABASE_URL: str = "sqlite:///./data/mini_query.db"
    
    # Redis配置（可选）
    REDIS_URL: Optional[str] = None
    
    # 文件存储
    UPLOAD_DIR: str = "./uploads"
    EXPORT_DIR: str = "./exports"
    
    # 安全配置
    ALLOWED_ORIGINS: list = ["*"]
    MAX_QUERY_ROWS: int = 10000
    QUERY_TIMEOUT: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 全局配置实例
settings = Settings()

# 确保必要目录存在
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.EXPORT_DIR, exist_ok=True)
os.makedirs("./data", exist_ok=True)
os.makedirs("./logs", exist_ok=True)

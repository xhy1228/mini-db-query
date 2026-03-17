# -*- coding: utf-8 -*-
"""
多源数据查询小程序版 - 核心配置

Deploy first, configure database later
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os
import re
import json
import logging

logger = logging.getLogger(__name__)


def get_encrypted_db_config() -> Optional[dict]:
    """获取加密存储的数据库配置"""
    env_file = os.path.join(os.path.dirname(__file__), '..', '.env')
    if not os.path.exists(env_file):
        return None
    
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('ENCRYPTED_DB_CONFIG='):
                    encrypted_str = line.split('=', 1)[1].strip()
                    if not encrypted_str:
                        return None
                    
                    try:
                        from core.security import decrypt_password
                        decrypted = decrypt_password(encrypted_str)
                        return json.loads(decrypted)
                    except Exception as e:
                        logger.error(f"解密配置失败: {e}")
                        return None
    except Exception as e:
        logger.error(f"读取配置文件失败: {e}")
    
    return None


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用信息
    APP_NAME: str = "多源数据查询小程序"
    APP_VERSION: str = "1.0.0.28"
    DEBUG: bool = True
    
    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 26316
    
    # 微信小程序配置
    WECHAT_APPID: str = ""
    WECHAT_SECRET: str = ""
    
    # JWT配置
    JWT_SECRET_KEY: str = "mini-db-query-secret-key-2026"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天
    
    # 数据库配置 - 可选，支持部署后再配置
    DATABASE_URL: str = ""
    
    # Redis配置（可选）
    REDIS_URL: Optional[str] = None
    
    # 文件存储
    UPLOAD_DIR: str = "./uploads"
    EXPORT_DIR: str = "./exports"
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "./logs"
    
    # 安全配置
    ALLOWED_ORIGINS: str = "*"
    MAX_QUERY_ROWS: int = 10000
    QUERY_TIMEOUT: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"
    
    @property
    def allowed_origins_list(self) -> list:
        """将ALLOWED_ORIGINS字符串转换为列表"""
        if self.ALLOWED_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    @property
    def is_mysql(self) -> bool:
        """检查是否使用MySQL"""
        # 优先检查加密配置
        encrypted_config = get_encrypted_db_config()
        if encrypted_config:
            return True
        if not self.DATABASE_URL:
            return False
        return self.DATABASE_URL.startswith('mysql')
    
    @property
    def mysql_info(self) -> dict:
        """解析MySQL连接信息"""
        # 优先从加密配置读取
        encrypted_config = get_encrypted_db_config()
        if encrypted_config:
            return {
                'user': encrypted_config.get('user', ''),
                'password': '***',  # 隐藏密码
                'host': encrypted_config.get('host', ''),
                'port': encrypted_config.get('port', 3306),
                'db_name': encrypted_config.get('db_name', '')
            }
        
        if not self.is_mysql:
            return {}
        
        # 解析 mysql+pymysql://user:password@host:port/database
        pattern = r'mysql\+pymysql://([^:]+):([^@]+)@([^:]+):(\d+)/([^?]+)'
        match = re.match(pattern, self.DATABASE_URL)
        if match:
            return {
                'user': match.group(1),
                'password': '***',  # 隐藏密码
                'host': match.group(3),
                'port': int(match.group(4)),
                'db_name': match.group(5)
            }
        return {}


# 全局配置实例
settings = Settings()

# 确保必要目录存在
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.EXPORT_DIR, exist_ok=True)
os.makedirs(settings.LOG_DIR, exist_ok=True)
os.makedirs("./data", exist_ok=True)

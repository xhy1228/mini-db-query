# -*- coding: utf-8 -*-
"""
Security Enhanced Module - 安全增强模块

实现以下安全机制：
1. JWT密钥自动生成和安全存储
2. 登录失败锁定机制
3. IP白名单/黑名单
4. 密码强度验证
5. Token刷新机制
6. 数据删除功能
"""

import os
import json
import secrets
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
from pathlib import Path
import re

logger = logging.getLogger(__name__)


# ============================================
# 1. JWT密钥安全管理
# ============================================

def generate_jwt_secret_key() -> str:
    """生成安全的JWT密钥"""
    return secrets.token_urlsafe(32)


def get_or_create_jwt_secret_key() -> str:
    """
    获取或创建JWT密钥
    
    优先级：
    1. 环境变量 JWT_SECRET_KEY
    2. 本地密钥文件 .keys/jwt.key
    3. 自动生成并保存
    """
    # 1. 检查环境变量
    env_key = os.environ.get('JWT_SECRET_KEY')
    if env_key and len(env_key) >= 32:
        return env_key
    
    # 2. 检查本地密钥文件
    keys_dir = Path("./.keys")
    keys_dir.mkdir(exist_ok=True)
    key_file = keys_dir / "jwt.key"
    
    if key_file.exists():
        try:
            with open(key_file, 'r') as f:
                key = f.read().strip()
                if len(key) >= 32:
                    return key
        except Exception as e:
            logger.warning(f"读取JWT密钥文件失败: {e}")
    
    # 3. 生成新密钥并保存
    new_key = generate_jwt_secret_key()
    try:
        with open(key_file, 'w') as f:
            f.write(new_key)
        # 设置文件权限为仅所有者可读写
        os.chmod(key_file, 0o600)
        logger.info("已生成新的JWT密钥并保存")
    except Exception as e:
        logger.error(f"保存JWT密钥失败: {e}")
    
    return new_key


# ============================================
# 2. 登录失败锁定机制
# ============================================

class LoginLockoutManager:
    """
    登录失败锁定管理器
    
    功能：
    - 记录登录失败次数
    - 超过阈值锁定账户
    - 支持IP锁定
    - 自动解锁
    """
    
    LOCKOUT_FILE = "./data/login_lockout.json"
    MAX_FAILED_ATTEMPTS = 5  # 最大失败次数
    LOCKOUT_DURATION_MINUTES = 15  # 锁定时长(分钟)
    IP_MAX_FAILED_ATTEMPTS = 10  # IP最大失败次数
    
    def __init__(self):
        self.data = self._load_data()
    
    def _load_data(self) -> dict:
        """加载锁定数据"""
        if os.path.exists(self.LOCKOUT_FILE):
            try:
                with open(self.LOCKOUT_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {
            "accounts": {},  # 账户锁定: {phone: {fail_count, locked_until, last_attempt}}
            "ips": {}        # IP锁定: {ip: {fail_count, locked_until}}
        }
    
    def _save_data(self):
        """保存锁定数据"""
        os.makedirs(os.path.dirname(self.LOCKOUT_FILE), exist_ok=True)
        with open(self.LOCKOUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def record_failed_attempt(self, phone: str, ip: str) -> Tuple[bool, str]:
        """
        记录登录失败
        
        Returns:
            (is_locked, message) - 是否锁定, 消息
        """
        now = datetime.now()
        
        # 检查IP是否已锁定
        ip_data = self.data["ips"].get(ip, {"fail_count": 0, "locked_until": None})
        if ip_data.get("locked_until"):
            locked_until = datetime.fromisoformat(ip_data["locked_until"])
            if now < locked_until:
                remaining = (locked_until - now).seconds // 60
                return True, f"IP已被锁定，请{remaining}分钟后再试"
            else:
                # 已解锁，重置
                ip_data = {"fail_count": 0, "locked_until": None}
        
        # 检查账户是否已锁定
        account_data = self.data["accounts"].get(phone, {
            "fail_count": 0, 
            "locked_until": None,
            "last_attempt": None
        })
        
        if account_data.get("locked_until"):
            locked_until = datetime.fromisoformat(account_data["locked_until"])
            if now < locked_until:
                remaining = (locked_until - now).seconds // 60
                return True, f"账户已被锁定，请{remaining}分钟后再试"
            else:
                # 已解锁，重置
                account_data = {"fail_count": 0, "locked_until": None, "last_attempt": None}
        
        # 记录失败
        account_data["fail_count"] = account_data.get("fail_count", 0) + 1
        account_data["last_attempt"] = now.isoformat()
        
        ip_data["fail_count"] = ip_data.get("fail_count", 0) + 1
        
        # 检查是否需要锁定
        message = f"登录失败 ({account_data['fail_count']}/{self.MAX_FAILED_ATTEMPTS})"
        
        if account_data["fail_count"] >= self.MAX_FAILED_ATTEMPTS:
            locked_until = now + timedelta(minutes=self.LOCKOUT_DURATION_MINUTES)
            account_data["locked_until"] = locked_until.isoformat()
            message = f"登录失败次数过多，账户已锁定{self.LOCKOUT_DURATION_MINUTES}分钟"
        
        if ip_data["fail_count"] >= self.IP_MAX_FAILED_ATTEMPTS:
            locked_until = now + timedelta(minutes=self.LOCKOUT_DURATION_MINUTES)
            ip_data["locked_until"] = locked_until.isoformat()
            message = f"IP登录失败次数过多，已锁定{self.LOCKOUT_DURATION_MINUTES}分钟"
        
        # 保存
        self.data["accounts"][phone] = account_data
        self.data["ips"][ip] = ip_data
        self._save_data()
        
        is_locked = bool(account_data.get("locked_until")) or bool(ip_data.get("locked_until"))
        return is_locked, message
    
    def record_successful_login(self, phone: str, ip: str):
        """记录登录成功，清除失败记录"""
        if phone in self.data["accounts"]:
            del self.data["accounts"][phone]
        # IP失败计数减1（不完全清除，防止绕过）
        if ip in self.data["ips"]:
            self.data["ips"][ip]["fail_count"] = max(0, self.data["ips"][ip].get("fail_count", 0) - 1)
        self._save_data()
    
    def is_locked(self, phone: str, ip: str) -> Tuple[bool, str]:
        """检查是否被锁定"""
        now = datetime.now()
        
        # 检查IP锁定
        ip_data = self.data["ips"].get(ip, {})
        if ip_data.get("locked_until"):
            locked_until = datetime.fromisoformat(ip_data["locked_until"])
            if now < locked_until:
                remaining = (locked_until - now).seconds // 60
                return True, f"IP已被锁定，请{remaining}分钟后再试"
        
        # 检查账户锁定
        account_data = self.data["accounts"].get(phone, {})
        if account_data.get("locked_until"):
            locked_until = datetime.fromisoformat(account_data["locked_until"])
            if now < locked_until:
                remaining = (locked_until - now).seconds // 60
                return True, f"账户已被锁定，请{remaining}分钟后再试"
        
        return False, ""
    
    def clear_lockout(self, phone: str):
        """清除账户锁定（管理员操作）"""
        if phone in self.data["accounts"]:
            del self.data["accounts"][phone]
            self._save_data()
            logger.info(f"已清除账户 {phone} 的锁定")


# 全局锁定管理器
login_lockout_manager = LoginLockoutManager()


# ============================================
# 3. IP白名单管理
# ============================================

class IPWhitelistManager:
    """
    IP白名单管理器
    
    功能：
    - 管理后台IP白名单
    - 支持CIDR格式
    - 动态配置
    """
    
    WHITELIST_FILE = "./data/ip_whitelist.json"
    
    def __init__(self):
        self.whitelist = self._load_whitelist()
    
    def _load_whitelist(self) -> dict:
        """加载白名单配置"""
        if os.path.exists(self.WHITELIST_FILE):
            try:
                with open(self.WHITELIST_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {
            "enabled": False,  # 是否启用白名单
            "admin_ips": [],   # 管理后台IP白名单
            "api_ips": []      # API访问IP白名单
        }
    
    def _save_whitelist(self):
        """保存白名单配置"""
        os.makedirs(os.path.dirname(self.WHITELIST_FILE), exist_ok=True)
        with open(self.WHITELIST_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.whitelist, f, ensure_ascii=False, indent=2)
    
    def is_ip_allowed(self, ip: str, access_type: str = "admin") -> bool:
        """
        检查IP是否允许访问
        
        Args:
            ip: 客户端IP
            access_type: 访问类型 (admin/api)
        
        Returns:
            是否允许
        """
        # 白名单未启用，允许所有
        if not self.whitelist.get("enabled"):
            return True
        
        # 获取对应白名单
        whitelist_key = f"{access_type}_ips"
        allowed_ips = self.whitelist.get(whitelist_key, [])
        
        if not allowed_ips:
            return True  # 白名单为空，允许所有
        
        # 检查IP
        for allowed in allowed_ips:
            if self._ip_match(ip, allowed):
                return True
        
        return False
    
    def _ip_match(self, ip: str, pattern: str) -> bool:
        """
        检查IP是否匹配模式
        
        支持格式：
        - 单个IP: 192.168.1.1
        - IP范围: 192.168.1.1-192.168.1.100
        - CIDR: 192.168.1.0/24
        """
        if pattern == ip:
            return True
        
        # CIDR格式
        if '/' in pattern:
            try:
                import ipaddress
                network = ipaddress.ip_network(pattern, strict=False)
                return ipaddress.ip_address(ip) in network
            except:
                return False
        
        # IP范围
        if '-' in pattern:
            try:
                start, end = pattern.split('-')
                start_parts = [int(x) for x in start.split('.')]
                end_parts = [int(x) for x in end.split('.')]
                ip_parts = [int(x) for x in ip.split('.')]
                
                start_int = (start_parts[0] << 24) + (start_parts[1] << 16) + (start_parts[2] << 8) + start_parts[3]
                end_int = (end_parts[0] << 24) + (end_parts[1] << 16) + (end_parts[2] << 8) + end_parts[3]
                ip_int = (ip_parts[0] << 24) + (ip_parts[1] << 16) + (ip_parts[2] << 8) + ip_parts[3]
                
                return start_int <= ip_int <= end_int
            except:
                return False
        
        return False
    
    def add_ip(self, ip: str, access_type: str = "admin"):
        """添加IP到白名单"""
        whitelist_key = f"{access_type}_ips"
        if whitelist_key not in self.whitelist:
            self.whitelist[whitelist_key] = []
        if ip not in self.whitelist[whitelist_key]:
            self.whitelist[whitelist_key].append(ip)
            self._save_whitelist()
    
    def remove_ip(self, ip: str, access_type: str = "admin"):
        """从白名单移除IP"""
        whitelist_key = f"{access_type}_ips"
        if whitelist_key in self.whitelist and ip in self.whitelist[whitelist_key]:
            self.whitelist[whitelist_key].remove(ip)
            self._save_whitelist()
    
    def set_enabled(self, enabled: bool):
        """启用/禁用白名单"""
        self.whitelist["enabled"] = enabled
        self._save_whitelist()
    
    def get_whitelist(self) -> dict:
        """获取白名单配置"""
        return self.whitelist.copy()


# 全局IP白名单管理器
ip_whitelist_manager = IPWhitelistManager()


# ============================================
# 4. 密码强度验证
# ============================================

class PasswordValidator:
    """密码强度验证器"""
    
    MIN_LENGTH = 8
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGIT = True
    REQUIRE_SPECIAL = False
    
    @staticmethod
    def validate(password: str) -> Tuple[bool, str]:
        """
        验证密码强度
        
        Returns:
            (is_valid, message)
        """
        if not password:
            return False, "密码不能为空"
        
        if len(password) < PasswordValidator.MIN_LENGTH:
            return False, f"密码长度至少{PasswordValidator.MIN_LENGTH}位"
        
        if PasswordValidator.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            return False, "密码必须包含大写字母"
        
        if PasswordValidator.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            return False, "密码必须包含小写字母"
        
        if PasswordValidator.REQUIRE_DIGIT and not re.search(r'\d', password):
            return False, "密码必须包含数字"
        
        # 检查常见弱密码
        weak_passwords = ['123456', 'password', 'admin', 'qwerty', '111111', '12345678']
        if password.lower() in weak_passwords:
            return False, "密码过于简单，请使用更复杂的密码"
        
        return True, "密码强度验证通过"
    
    @staticmethod
    def get_strength(password: str) -> dict:
        """
        获取密码强度评级
        
        Returns:
            {score: 0-100, level: weak/medium/strong, suggestions: []}
        """
        score = 0
        suggestions = []
        
        # 长度评分
        length = len(password)
        if length >= 8:
            score += 20
        if length >= 12:
            score += 20
        if length >= 16:
            score += 10
        
        # 字符类型评分
        if re.search(r'[a-z]', password):
            score += 15
        else:
            suggestions.append("添加小写字母")
        
        if re.search(r'[A-Z]', password):
            score += 15
        else:
            suggestions.append("添加大写字母")
        
        if re.search(r'\d', password):
            score += 15
        else:
            suggestions.append("添加数字")
        
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 15
        else:
            suggestions.append("添加特殊字符")
        
        # 评级
        if score < 40:
            level = "weak"
        elif score < 70:
            level = "medium"
        else:
            level = "strong"
        
        return {
            "score": min(score, 100),
            "level": level,
            "suggestions": suggestions
        }


# ============================================
# 5. 数据删除功能
# ============================================

class DataDeletionService:
    """
    数据删除服务
    
    实现：
    - 用户可删除自己的数据
    - 管理员可删除用户数据
    - 软删除+硬删除
    - 删除日志记录
    """
    
    @staticmethod
    def soft_delete_user(db, user_id: int, operator_id: int = None) -> bool:
        """
        软删除用户（标记删除状态）
        
        保留数据用于审计，但用户无法登录
        """
        try:
            from models.database import User
            
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            # 标记为已删除
            user.status = 'deleted'
            user.phone = f"deleted_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            user.openid = None  # 清除微信绑定
            user.unionid = None
            
            db.commit()
            
            # 记录删除日志
            logger.info(f"用户软删除: user_id={user_id}, operator={operator_id}")
            
            return True
        except Exception as e:
            logger.error(f"软删除用户失败: {e}")
            return False
    
    @staticmethod
    def hard_delete_user(db, user_id: int, operator_id: int = None) -> bool:
        """
        硬删除用户（完全删除数据）
        
        删除用户及关联数据
        """
        try:
            from models.database import User, UserSchool, UserSchoolPermission, UserTemplatePermission, QueryLog
            
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            # 删除关联数据
            db.query(UserSchool).filter(UserSchool.user_id == user_id).delete()
            db.query(UserSchoolPermission).filter(UserSchoolPermission.user_id == user_id).delete()
            db.query(UserTemplatePermission).filter(UserTemplatePermission.user_id == user_id).delete()
            db.query(QueryLog).filter(QueryLog.user_id == user_id).delete()
            
            # 删除用户
            db.delete(user)
            db.commit()
            
            # 记录删除日志
            logger.info(f"用户硬删除: user_id={user_id}, operator={operator_id}")
            
            return True
        except Exception as e:
            logger.error(f"硬删除用户失败: {e}")
            return False
    
    @staticmethod
    def delete_user_data(db, user_id: int, data_types: List[str] = None) -> dict:
        """
        删除用户特定类型数据
        
        Args:
            user_id: 用户ID
            data_types: 要删除的数据类型 (query_logs, export_files, etc.)
        
        Returns:
            删除结果
        """
        results = {}
        
        if not data_types:
            data_types = ['query_logs', 'export_files']
        
        if 'query_logs' in data_types:
            try:
                from models.database import QueryLog
                count = db.query(QueryLog).filter(QueryLog.user_id == user_id).delete()
                results['query_logs'] = count
            except Exception as e:
                results['query_logs'] = f"error: {str(e)}"
        
        if 'export_files' in data_types:
            try:
                # 删除导出文件
                import glob
                export_dir = Path("./exports")
                for f in export_dir.glob("*.xlsx"):
                    f.unlink()
                results['export_files'] = 'cleaned'
            except Exception as e:
                results['export_files'] = f"error: {str(e)}"
        
        db.commit()
        logger.info(f"删除用户数据: user_id={user_id}, types={data_types}, results={results}")
        
        return results


# ============================================
# 6. 环境检测
# ============================================

class EnvironmentChecker:
    """环境检测器"""
    
    @staticmethod
    def is_production() -> bool:
        """检测是否为生产环境"""
        # 检查环境变量
        env = os.environ.get('ENVIRONMENT', '').lower()
        if env in ['production', 'prod']:
            return True
        
        # 检查常见生产环境标识
        if os.path.exists('/etc/production'):
            return True
        
        # 检查域名
        host = os.environ.get('HOSTNAME', '')
        if 'prod' in host.lower() or 'live' in host.lower():
            return True
        
        return False
    
    @staticmethod
    def check_security_settings() -> List[dict]:
        """
        检查安全设置
        
        Returns:
            问题列表
        """
        issues = []
        
        # 检查DEBUG模式
        if os.environ.get('DEBUG', '').lower() == 'true':
            issues.append({
                "level": "high",
                "message": "DEBUG模式在生产环境开启",
                "suggestion": "设置 DEBUG=false"
            })
        
        # 检查JWT密钥
        from core.config import settings
        if settings.JWT_SECRET_KEY == "mini-db-query-secret-key-2026":
            issues.append({
                "level": "critical",
                "message": "使用默认JWT密钥",
                "suggestion": "设置环境变量 JWT_SECRET_KEY 或自动生成"
            })
        
        # 检查HTTPS
        # (需要在实际请求中检查)
        
        return issues

# -*- coding: utf-8 -*-
"""
Security API - 安全管理API

提供：
1. 登录锁定管理
2. IP白名单管理
3. 数据删除功能
4. 安全状态检查
5. 账号注销功能
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from models import get_db_session
from core.security import get_current_user, get_current_admin, TokenData
from core.security_enhanced import (
    login_lockout_manager, 
    ip_whitelist_manager, 
    PasswordValidator,
    DataDeletionService,
    EnvironmentChecker
)
from core.logging_middleware import OperationLogger

router = APIRouter(tags=["安全管理"])


# ========== 请求模型 ==========

class UnlockAccountRequest(BaseModel):
    """解锁账户请求"""
    phone: str = Field(..., description="手机号")


class IPWhitelistRequest(BaseModel):
    """IP白名单请求"""
    ip: str = Field(..., description="IP地址或CIDR")
    access_type: str = Field(default="admin", description="访问类型: admin/api")


class DeleteUserDataRequest(BaseModel):
    """删除用户数据请求"""
    user_id: int = Field(..., description="用户ID")
    data_types: Optional[List[str]] = Field(default=None, description="数据类型")


class PasswordStrengthRequest(BaseModel):
    """密码强度检查请求"""
    password: str = Field(..., description="密码")


# ========== 登录锁定管理 ==========

@router.get("/lockout/status")
async def get_lockout_status(
    current_user: TokenData = Depends(get_current_admin),
    db: Session = Depends(get_db_session)
):
    """获取登录锁定状态（管理员）"""
    return {
        "code": 200,
        "message": "获取成功",
        "data": {
            "locked_accounts": login_lockout_manager.data.get("accounts", {}),
            "locked_ips": login_lockout_manager.data.get("ips", {}),
            "config": {
                "max_attempts": login_lockout_manager.MAX_FAILED_ATTEMPTS,
                "lockout_minutes": login_lockout_manager.LOCKOUT_DURATION_MINUTES
            }
        }
    }


@router.post("/lockout/unlock")
async def unlock_account(
    request: UnlockAccountRequest,
    req: Request,
    current_user: TokenData = Depends(get_current_admin),
    db: Session = Depends(get_db_session)
):
    """解锁账户（管理员）"""
    client_ip = req.client.host if req.client else "unknown"
    
    login_lockout_manager.clear_lockout(request.phone)
    
    # 记录操作日志
    OperationLogger.log_operation(
        db=db,
        action="unlock_account",
        resource_type="user",
        resource_id=request.phone,
        details=f"Unlocked account: {request.phone}",
        user_id=int(current_user.user_id),
        ip_address=client_ip
    )
    
    return {
        "code": 200,
        "message": "账户已解锁",
        "data": {"phone": request.phone}
    }


# ========== IP白名单管理 ==========

@router.get("/ip-whitelist")
async def get_ip_whitelist(
    current_user: TokenData = Depends(get_current_admin),
    db: Session = Depends(get_db_session)
):
    """获取IP白名单配置（管理员）"""
    return {
        "code": 200,
        "message": "获取成功",
        "data": ip_whitelist_manager.get_whitelist()
    }


@router.post("/ip-whitelist")
async def add_ip_whitelist(
    request: IPWhitelistRequest,
    req: Request,
    current_user: TokenData = Depends(get_current_admin),
    db: Session = Depends(get_db_session)
):
    """添加IP到白名单（管理员）"""
    client_ip = req.client.host if req.client else "unknown"
    
    ip_whitelist_manager.add_ip(request.ip, request.access_type)
    
    # 记录操作日志
    OperationLogger.log_operation(
        db=db,
        action="add_ip_whitelist",
        resource_type="security",
        details=f"Added IP {request.ip} to {request.access_type} whitelist",
        user_id=int(current_user.user_id),
        ip_address=client_ip
    )
    
    return {
        "code": 200,
        "message": "添加成功",
        "data": ip_whitelist_manager.get_whitelist()
    }


@router.delete("/ip-whitelist")
async def remove_ip_whitelist(
    request: IPWhitelistRequest,
    req: Request,
    current_user: TokenData = Depends(get_current_admin),
    db: Session = Depends(get_db_session)
):
    """从白名单移除IP（管理员）"""
    client_ip = req.client.host if req.client else "unknown"
    
    ip_whitelist_manager.remove_ip(request.ip, request.access_type)
    
    # 记录操作日志
    OperationLogger.log_operation(
        db=db,
        action="remove_ip_whitelist",
        resource_type="security",
        details=f"Removed IP {request.ip} from {request.access_type} whitelist",
        user_id=int(current_user.user_id),
        ip_address=client_ip
    )
    
    return {
        "code": 200,
        "message": "移除成功",
        "data": ip_whitelist_manager.get_whitelist()
    }


@router.put("/ip-whitelist/enabled")
async def toggle_ip_whitelist(
    enabled: bool,
    req: Request,
    current_user: TokenData = Depends(get_current_admin),
    db: Session = Depends(get_db_session)
):
    """启用/禁用IP白名单（管理员）"""
    client_ip = req.client.host if req.client else "unknown"
    
    ip_whitelist_manager.set_enabled(enabled)
    
    # 记录操作日志
    OperationLogger.log_operation(
        db=db,
        action="toggle_ip_whitelist",
        resource_type="security",
        details=f"IP whitelist {'enabled' if enabled else 'disabled'}",
        user_id=int(current_user.user_id),
        ip_address=client_ip
    )
    
    return {
        "code": 200,
        "message": f"IP白名单已{'启用' if enabled else '禁用'}",
        "data": {"enabled": enabled}
    }


# ========== 数据删除 ==========

@router.delete("/users/{user_id}/data")
async def delete_user_data(
    user_id: int,
    data_types: Optional[str] = None,
    hard_delete: bool = False,
    req: Request = None,
    current_user: TokenData = Depends(get_current_admin),
    db: Session = Depends(get_db_session)
):
    """
    删除用户数据（管理员）
    
    - **user_id**: 用户ID
    - **data_types**: 数据类型，逗号分隔 (query_logs,export_files)
    - **hard_delete**: 是否硬删除（完全删除用户）
    """
    client_ip = req.client.host if req else "unknown"
    
    # 不能删除自己
    if int(current_user.user_id) == user_id:
        return {
            "code": 400,
            "message": "不能删除自己的账户",
            "data": None
        }
    
    if hard_delete:
        # 硬删除用户
        success = DataDeletionService.hard_delete_user(db, user_id, int(current_user.user_id))
        
        OperationLogger.log_operation(
            db=db,
            action="hard_delete_user",
            resource_type="user",
            resource_id=str(user_id),
            details="Hard deleted user and all related data",
            user_id=int(current_user.user_id),
            ip_address=client_ip
        )
        
        return {
            "code": 200 if success else 400,
            "message": "用户已完全删除" if success else "删除失败",
            "data": None
        }
    else:
        # 软删除用户
        success = DataDeletionService.soft_delete_user(db, user_id, int(current_user.user_id))
        
        OperationLogger.log_operation(
            db=db,
            action="soft_delete_user",
            resource_type="user",
            resource_id=str(user_id),
            details="Soft deleted user (marked as deleted)",
            user_id=int(current_user.user_id),
            ip_address=client_ip
        )
        
        return {
            "code": 200 if success else 400,
            "message": "用户已标记删除" if success else "删除失败",
            "data": None
        }


@router.delete("/my-data")
async def delete_my_data(
    data_types: Optional[str] = None,
    req: Request = None,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    删除自己的数据
    
    用户可删除自己的查询日志和导出文件
    """
    client_ip = req.client.host if req else "unknown"
    user_id = int(current_user.user_id)
    
    types_list = data_types.split(',') if data_types else ['query_logs', 'export_files']
    
    results = DataDeletionService.delete_user_data(db, user_id, types_list)
    
    OperationLogger.log_operation(
        db=db,
        action="delete_own_data",
        resource_type="user",
        resource_id=str(user_id),
        details=f"Deleted data types: {types_list}",
        user_id=user_id,
        ip_address=client_ip
    )
    
    return {
        "code": 200,
        "message": "数据删除成功",
        "data": results
    }


# ========== 密码强度检查 ==========

@router.post("/password/strength")
async def check_password_strength(
    request: PasswordStrengthRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """检查密码强度"""
    strength = PasswordValidator.get_strength(request.password)
    
    return {
        "code": 200,
        "message": "检查完成",
        "data": strength
    }


# ========== 账号注销 ==========

class AccountDeletionRequest(BaseModel):
    """账号注销请求"""
    password: str = Field(..., description="当前密码（用于验证身份）")
    confirm_text: str = Field(..., description='确认文本（输入"我已知晓"）')


@router.post("/account/delete")
async def delete_my_account(
    request: AccountDeletionRequest,
    req: Request,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    注销自己的账号
    
    用户可注销自己的账号，删除所有个人数据
    需要输入密码确认，并输入"我已知晓"确认
    """
    client_ip = req.client.host if req.client else "unknown"
    user_id = int(current_user.user_id)
    
    # 1. 验证确认文本
    if request.confirm_text != "我已知晓":
        return {
            "code": 400,
            "message": "请输入正确的确认文本：我已知晓",
            "data": None
        }
    
    # 2. 获取用户信息并验证密码
    from services.user_service import UserService
    from core.security import verify_password
    
    user = UserService.get_by_id(db, user_id)
    if not user:
        return {
            "code": 404,
            "message": "用户不存在",
            "data": None
        }
    
    # 验证密码
    if not verify_password(request.password, user.password):
        return {
            "code": 401,
            "message": "密码错误",
            "data": None
        }
    
    # 3. 先删除用户数据（查询日志、导出文件等）
    DataDeletionService.delete_user_data(db, user_id, ['query_logs', 'export_files'])
    
    # 4. 软删除用户（保留审计需要的数据）
    # 清除敏感信息但保留记录
    user.status = 'deleted'
    user.phone = f"deleted_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    user.openid = None
    user.unionid = None
    user.avatar = None
    user.name = f"已注销用户_{user_id}"
    user.id_card = None
    db.commit()
    
    # 5. 记录操作日志
    OperationLogger.log_operation(
        db=db,
        action="delete_own_account",
        resource_type="user",
        resource_id=str(user_id),
        details="User deleted their own account",
        user_id=user_id,
        ip_address=client_ip
    )
    
    return {
        "code": 200,
        "message": "账号注销成功，您的数据已删除",
        "data": {
            "deleted_at": datetime.now().isoformat(),
            "user_id": user_id
        }
    }


# ========== 安全状态检查 ==========

@router.get("/status")
async def get_security_status(
    current_user: TokenData = Depends(get_current_admin),
    db: Session = Depends(get_db_session)
):
    """获取系统安全状态（管理员）"""
    issues = EnvironmentChecker.check_security_settings()
    
    return {
        "code": 200,
        "message": "获取成功",
        "data": {
            "issues": issues,
            "ip_whitelist": ip_whitelist_manager.get_whitelist(),
            "lockout_config": {
                "max_attempts": login_lockout_manager.MAX_FAILED_ATTEMPTS,
                "lockout_minutes": login_lockout_manager.LOCKOUT_DURATION_MINUTES
            }
        }
    }

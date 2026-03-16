# -*- coding: utf-8 -*-
"""
多源数据查询小程序版 - 认证API

Author: 飞书百万（AI助手）
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional

from models import get_db_session
from services.user_service import UserService
from core.security import get_current_user, TokenData


router = APIRouter(tags=["认证"])


# ========== 请求/响应模型 ==========

class LoginRequest(BaseModel):
    """登录请求"""
    phone: str = Field(..., description="手机号")
    password: str = Field(..., description="密码(身份证后6位)")


class LoginResponse(BaseModel):
    """登录响应"""
    code: int
    message: str
    data: Optional[dict] = None


class UserInfoResponse(BaseModel):
    """用户信息响应"""
    code: int
    message: str
    data: Optional[dict] = None


# ========== API路由 ==========

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db_session)):
    """
    用户登录
    
    - **phone**: 手机号（如：13800138000 或 admin）
    - **password**: 密码（身份证后6位，管理员默认123456）
    
    返回：用户信息 + JWT Token
    """
    result = UserService.authenticate(db, request.phone, request.password)
    
    if not result:
        return {
            "code": 401,
            "message": "手机号或密码错误",
            "data": None
        }
    
    return {
        "code": 200,
        "message": "登录成功",
        "data": {
            "token": result["token"],
            "token_type": "bearer",
            "user": result["user"],
            "role": result["role"]
        }
    }


@router.get("/me", response_model=UserInfoResponse)
async def get_me(current_user: TokenData = Depends(get_current_user), 
                db: Session = Depends(get_db_session)):
    """
    获取当前用户信息
    
    需要认证token
    """
    user = UserService.get_by_id(db, int(current_user.user_id))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 获取用户授权的学校
    schools = UserService.get_user_schools(db, user.id)
    
    return {
        "code": 200,
        "message": "获取成功",
        "data": {
            "user": user.to_dict(),
            "schools": schools,
            "role": current_user.role
        }
    }


@router.post("/logout")
async def logout(current_user: TokenData = Depends(get_current_user)):
    """
    退出登录
    
    前端清除token即可，服务端token会过期
    """
    return {
        "code": 200,
        "message": "退出成功",
        "data": None
    }


# ========== 管理员用户管理API ==========

class CreateUserRequest(BaseModel):
    """创建用户请求"""
    phone: str
    password: str = Field(default_factory=lambda: None, description="不传则使用身份证后6位")
    name: str
    id_card: Optional[str] = None
    role: str = "user"
    school_ids: list = []


class UpdateUserRequest(BaseModel):
    """更新用户请求"""
    phone: Optional[str] = None
    name: Optional[str] = None
    id_card: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    school_ids: Optional[list] = None


@router.post("/admin/users", response_model=dict)
async def create_user(request: CreateUserRequest,
                     current_user: TokenData = Depends(get_current_user),
                     db: Session = Depends(get_db_session)):
    """
    创建用户（管理员权限）
    """
    # 检查权限
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    # 检查手机号是否已存在
    existing = UserService.get_by_phone(db, request.phone)
    if existing:
        return {
            "code": 400,
            "message": "手机号已存在",
            "data": None
        }
    
    # 如果没有提供密码，使用身份证后6位
    password = request.password
    if not password and request.id_card:
        password = request.id_card[-6:]
    elif not password:
        password = "123456"  # 默认密码
    
    # 创建用户
    user = UserService.create_user(
        db,
        phone=request.phone,
        password=password,
        name=request.name,
        id_card=request.id_card,
        role=request.role
    )
    
    # 分配学校权限
    for school_id in request.school_ids:
        UserService.grant_school(db, user.id, school_id)
    
    return {
        "code": 200,
        "message": "创建成功",
        "data": user.to_dict()
    }


@router.get("/admin/users")
async def list_users(skip: int = 0, limit: int = 100,
                    current_user: TokenData = Depends(get_current_user),
                    db: Session = Depends(get_db_session)):
    """
    获取用户列表（管理员权限）
    """
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    users = UserService.list_users(db, skip, limit)
    
    return {
        "code": 200,
        "message": "获取成功",
        "data": [u.to_dict() for u in users]
    }


@router.put("/admin/users/{user_id}")
async def update_user(user_id: int, request: UpdateUserRequest,
                     current_user: TokenData = Depends(get_current_user),
                     db: Session = Depends(get_db_session)):
    """
    更新用户（管理员权限）
    """
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    update_data = request.dict(exclude_unset=True)
    
    # 处理学校权限更新
    school_ids = update_data.pop('school_ids', None)
    
    user = UserService.update_user(db, user_id, **update_data)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 更新学校权限
    if school_ids is not None:
        # 先撤销所有权限
        existing_perms = UserService.get_user_schools(db, user_id)
        for perm in existing_perms:
            UserService.revoke_school(db, user_id, perm['id'])
        
        # 重新授予权限
        for school_id in school_ids:
            UserService.grant_school(db, user_id, school_id)
    
    return {
        "code": 200,
        "message": "更新成功",
        "data": user.to_dict()
    }


@router.delete("/admin/users/{user_id}")
async def delete_user(user_id: int,
                     current_user: TokenData = Depends(get_current_user),
                     db: Session = Depends(get_db_session)):
    """
    删除用户（管理员权限）
    """
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    success = UserService.delete_user(db, user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return {
        "code": 200,
        "message": "删除成功",
        "data": None
    }


@router.post("/admin/users/{user_id}/schools/{school_id}")
async def grant_school_permission(user_id: int, school_id: int,
                                 current_user: TokenData = Depends(get_current_user),
                                 db: Session = Depends(get_db_session)):
    """
    授予用户学校权限（管理员权限）
    """
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    perm = UserService.grant_school(db, user_id, school_id)
    
    return {
        "code": 200,
        "message": "授权成功",
        "data": perm.to_dict()
    }


@router.delete("/admin/users/{user_id}/schools/{school_id}")
async def revoke_school_permission(user_id: int, school_id: int,
                                  current_user: TokenData = Depends(get_current_user),
                                  db: Session = Depends(get_db_session)):
    """
    撤销用户学校权限（管理员权限）
    """
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    success = UserService.revoke_school(db, user_id, school_id)
    
    return {
        "code": 200,
        "message": "撤销成功" if success else "权限不存在",
        "data": None
    }

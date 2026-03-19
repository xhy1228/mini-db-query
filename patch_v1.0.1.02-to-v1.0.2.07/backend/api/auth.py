# -*- coding: utf-8 -*-
"""
多源数据查询小程序版 - 认证API

Author: 飞书百万（AI助手）
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional

from models import get_db_session
from services.user_service import UserService
from core.security import get_current_user, TokenData
from core.logging_middleware import OperationLogger
from core.security_enhanced import login_lockout_manager, PasswordValidator


router = APIRouter(tags=["认证"])


# ========== 请求/响应模型 ==========

class LoginRequest(BaseModel):
    """登录请求"""
    phone: str = Field(..., description="手机号")
    password: str = Field(..., description="密码(身份证后6位)")


class WechatLoginRequest(BaseModel):
    """微信登录请求"""
    code: str = Field(..., description="微信登录code")
    encrypted_data: Optional[str] = Field(None, description="加密数据")
    iv: Optional[str] = Field(None, description="初始向量")


class BindPhoneRequest(BaseModel):
    """绑定手机号请求"""
    openid: str = Field(..., description="微信openid")
    phone: str = Field(..., description="手机号")
    password: str = Field(..., description="密码")


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
async def login(request: LoginRequest, req: Request, db: Session = Depends(get_db_session)):
    """
    用户登录
    
    - **phone**: 手机号（如：13800138000 或 admin）
    - **password**: 密码（身份证后6位，管理员默认123456）
    
    返回：用户信息 + JWT Token
    """
    client_ip = req.client.host if req.client else "unknown"
    
    # ========== 登录锁定检查 ==========
    is_locked, lock_message = login_lockout_manager.is_locked(request.phone, client_ip)
    if is_locked:
        return {
            "code": 423,  # Locked
            "message": lock_message,
            "data": None
        }
    # ========== 锁定检查结束 ==========
    
    result = UserService.authenticate(db, request.phone, request.password)
    
    if not result:
        # ========== 记录登录失败并检查锁定 ==========
        is_now_locked, fail_message = login_lockout_manager.record_failed_attempt(request.phone, client_ip)
        
        # 记录登录失败日志
        OperationLogger.log_login(
            db=db,
            user_id=0,
            username=request.phone,
            ip=client_ip,
            status="failed",
            error=fail_message
        )
        
        return {
            "code": 401,
            "message": fail_message,
            "data": None
        }
    
    # ========== 登录成功，清除失败记录 ==========
    login_lockout_manager.record_successful_login(request.phone, client_ip)
    
    # 记录登录成功
    OperationLogger.log_login(
        db=db,
        user_id=result["user"]["id"],
        username=result["user"]["name"],
        ip=client_ip
    )
    
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


@router.post("/wechat/login", response_model=LoginResponse)
async def wechat_login(request: WechatLoginRequest, db: Session = Depends(get_db_session)):
    """
    微信小程序登录
    
    - **code**: 微信登录code（wx.login获取）
    
    返回：用户信息 + JWT Token（如果是已绑定用户）
    """
    import httpx
    import logging
    from models.database import SystemConfig
    
    logger = logging.getLogger(__name__)
    logger.info(f"微信登录请求: code={request.code[:10]}...")
    
    # 获取微信配置
    appid_config = db.query(SystemConfig).filter(SystemConfig.config_key == 'wechat_appid').first()
    secret_config = db.query(SystemConfig).filter(SystemConfig.config_key == 'wechat_secret').first()
    
    if not appid_config or not secret_config:
        logger.warning("微信小程序未配置: appid或secret为空")
        return {
            "code": 500,
            "message": "微信小程序未配置，请联系管理员在系统配置中设置wechat_appid和wechat_secret",
            "data": None
        }
    
    # 解密配置
    try:
        from core.security import decrypt_password
        appid = decrypt_password(appid_config.config_value)
        secret = decrypt_password(secret_config.config_value)
        logger.info(f"微信配置解密成功: appid={appid[:6]}...")
    except Exception as e:
        logger.error(f"微信配置解密失败: {e}")
        return {
            "code": 500,
            "message": f"微信配置解密失败: {str(e)}",
            "data": None
        }
    
    # 调用微信接口获取 openid
    url = f"https://api.weixin.qq.com/sns/jscode2session?appid={appid}&secret={secret}&js_code={request.code}&grant_type=authorization_code"
    logger.info(f"调用微信API: {url[:50]}...")
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            data = response.json()
            logger.info(f"微信API响应: {data}")
    except httpx.TimeoutException:
        logger.error("微信接口调用超时")
        return {
            "code": 504,
            "message": "微信接口调用超时，请检查网络连接",
            "data": None
        }
    except Exception as e:
        logger.error(f"微信接口调用失败: {e}")
        return {
            "code": 500,
            "message": f"微信接口调用失败: {str(e)}",
            "data": None
        }
    
    if 'errcode' in data and data['errcode'] != 0:
        logger.error(f"微信登录失败: {data}")
        return {
            "code": 400,
            "message": data.get('errmsg', '微信登录失败'),
            "data": None
        }
    
    openid = data.get('openid')
    session_key = data.get('session_key')
    
    if not openid:
        logger.error("获取openid失败: 响应中没有openid")
        return {
            "code": 400,
            "message": "获取openid失败",
            "data": None
        }
    
    # 查找是否已绑定用户
    user = UserService.get_by_openid(db, openid)
    
    if user:
        # 已绑定，直接登录
        from core.security import create_access_token
        from datetime import datetime
        
        # 更新最后登录时间
        user.last_login = datetime.now()
        db.commit()
        
        # 生成token
        access_token = create_access_token({
            "sub": str(user.id),
            "phone": user.phone,
            "role": user.role,
            "name": user.name
        })
        
        return {
            "code": 200,
            "message": "登录成功",
            "data": {
                "token": access_token,
                "token_type": "bearer",
                "user": user.to_dict(),
                "role": user.role,
                "is_new": False
            }
        }
    else:
        # 未绑定，返回 openid 让用户绑定手机号
        return {
            "code": 200,
            "message": "请绑定手机号",
            "data": {
                "openid": openid,
                "session_key": session_key,
                "is_new": True
            }
        }


@router.post("/wechat/bind", response_model=LoginResponse)
async def bind_phone(request: BindPhoneRequest, db: Session = Depends(get_db_session)):
    """
    绑定手机号
    
    - **openid**: 微信openid
    - **phone**: 手机号
    - **password**: 密码
    
    返回：用户信息 + JWT Token
    """
    # 检查手机号是否已存在
    existing_user = UserService.get_by_phone(db, request.phone)
    
    if existing_user:
        # 手机号已存在，绑定 openid
        if existing_user.openid:
            return {
                "code": 400,
                "message": "该手机号已绑定其他微信",
                "data": None
            }
        
        existing_user.openid = request.openid
        db.commit()
        
        # 生成token
        from core.security import create_access_token
        from datetime import datetime
        
        existing_user.last_login = datetime.now()
        db.commit()
        
        access_token = create_access_token({
            "sub": str(existing_user.id),
            "phone": existing_user.phone,
            "role": existing_user.role,
            "name": existing_user.name
        })
        
        return {
            "code": 200,
            "message": "绑定成功",
            "data": {
                "token": access_token,
                "token_type": "bearer",
                "user": existing_user.to_dict(),
                "role": existing_user.role
            }
        }
    else:
        # 手机号不存在，创建新用户
        from core.security import get_password_hash, create_access_token
        from datetime import datetime
        
        user = UserService.create_user(
            db,
            phone=request.phone,
            password=request.password,
            name=f"用户{request.phone[-4:]}",
            role='user'
        )
        user.openid = request.openid
        user.last_login = datetime.now()
        db.commit()
        
        access_token = create_access_token({
            "sub": str(user.id),
            "phone": user.phone,
            "role": user.role,
            "name": user.name
        })
        
        return {
            "code": 200,
            "message": "注册成功",
            "data": {
                "token": access_token,
                "token_type": "bearer",
                "user": user.to_dict(),
                "role": user.role
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
async def logout(request: Request, current_user: TokenData = Depends(get_current_user),
                db: Session = Depends(get_db_session)):
    """
    退出登录
    
    前端清除token即可，服务端token会过期
    """
    client_ip = request.client.host if request.client else "unknown"
    
    # 记录登出操作
    user = UserService.get_by_id(db, int(current_user.user_id))
    OperationLogger.log_logout(
        db=db,
        user_id=int(current_user.user_id),
        username=user.name if user else current_user.user_id,
        ip=client_ip
    )
    
    return {
        "code": 200,
        "message": "退出成功",
        "data": None
    }


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., description="原密码")
    new_password: str = Field(..., description="新密码")


@router.post("/change-password")
async def change_password(request: ChangePasswordRequest,
                         current_user: TokenData = Depends(get_current_user),
                         db: Session = Depends(get_db_session)):
    """
    修改密码
    
    需要验证原密码
    """
    user = UserService.get_by_id(db, int(current_user.user_id))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 验证原密码
    from core.security import verify_password, get_password_hash
    
    if not verify_password(request.old_password, user.password):
        return {
            "code": 400,
            "message": "原密码错误",
            "data": None
        }
    
    # 更新密码
    user.password = get_password_hash(request.new_password)
    db.commit()
    
    return {
        "code": 200,
        "message": "密码修改成功",
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
async def create_user(request: CreateUserRequest, req: Request,
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
    
    client_ip = req.client.host if req.client else "unknown"
    admin = UserService.get_by_id(db, int(current_user.user_id))
    
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
    
    # 记录操作日志
    OperationLogger.log_create(
        db=db,
        resource_type="user",
        resource_id=user.id,
        resource_name=user.name,
        user_id=int(current_user.user_id),
        username=admin.name if admin else current_user.user_id,
        ip=client_ip,
        details=f"Created user: {user.name} ({user.phone}), role={user.role}"
    )
    
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
async def update_user(user_id: int, request: UpdateUserRequest, req: Request,
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
    
    client_ip = req.client.host if req.client else "unknown"
    admin = UserService.get_by_id(db, int(current_user.user_id))
    target_user = UserService.get_by_id(db, user_id)
    
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
    
    # 记录操作日志
    changes = {k: v for k, v in update_data.items() if k != 'password'}
    OperationLogger.log_update(
        db=db,
        resource_type="user",
        resource_id=user.id,
        resource_name=user.name,
        user_id=int(current_user.user_id),
        username=admin.name if admin else current_user.user_id,
        ip=client_ip,
        changes=changes
    )
    
    return {
        "code": 200,
        "message": "更新成功",
        "data": user.to_dict()
    }


@router.delete("/admin/users/{user_id}")
async def delete_user(user_id: int, req: Request,
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
    
    client_ip = req.client.host if req.client else "unknown"
    admin = UserService.get_by_id(db, int(current_user.user_id))
    target_user = UserService.get_by_id(db, user_id)
    user_name = target_user.name if target_user else f"ID:{user_id}"
    
    success = UserService.delete_user(db, user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 记录操作日志
    OperationLogger.log_delete(
        db=db,
        resource_type="user",
        resource_id=user_id,
        resource_name=user_name,
        user_id=int(current_user.user_id),
        username=admin.name if admin else current_user.user_id,
        ip=client_ip
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

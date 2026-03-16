# -*- coding: utf-8 -*-
"""
多源数据查询小程序版 - 认证API
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import httpx

from core.config import settings
from core.security import create_access_token, get_current_user
from utils.response import success_response, error_response


router = APIRouter(prefix="/auth", tags=["认证"])


class WechatLoginRequest(BaseModel):
    """微信登录请求"""
    code: str


class UserInfo(BaseModel):
    """用户信息"""
    user_id: str
    openid: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    role: str = "user"


@router.post("/wechat-login")
async def wechat_login(request: WechatLoginRequest):
    """
    微信小程序登录
    
    Args:
        request: 微信登录请求（包含code）
        
    Returns:
        登录结果，包含token和用户信息
    """
    try:
        # 调用微信API获取openid和session_key
        url = f"https://api.weixin.qq.com/sns/jscode2session"
        params = {
            "appid": settings.WECHAT_APPID,
            "secret": settings.WECHAT_SECRET,
            "js_code": request.code,
            "grant_type": "authorization_code"
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params)
            data = resp.json()
        
        if "errcode" in data and data["errcode"] != 0:
            return error_response(f"微信登录失败: {data.get('errmsg', '未知错误')}")
        
        openid = data.get("openid")
        session_key = data.get("session_key")
        
        if not openid:
            return error_response("获取用户信息失败")
        
        # TODO: 查询或创建用户记录
        user_id = openid  # 简化处理，实际应查询数据库
        
        # 生成JWT令牌
        token = create_access_token({
            "sub": user_id,
            "openid": openid,
            "role": "user"
        })
        
        return success_response({
            "token": token,
            "user": {
                "user_id": user_id,
                "openid": openid,
                "role": "user"
            }
        })
        
    except Exception as e:
        return error_response(f"登录异常: {str(e)}")


@router.get("/me")
async def get_user_info(current_user = Depends(get_current_user)):
    """
    获取当前用户信息
    
    Args:
        current_user: 当前用户
        
    Returns:
        用户信息
    """
    return success_response({
        "user_id": current_user.user_id,
        "openid": current_user.openid,
        "role": current_user.role
    })


@router.post("/logout")
async def logout(current_user = Depends(get_current_user)):
    """
    退出登录
    
    Args:
        current_user: 当前用户
        
    Returns:
        退出结果
    """
    # TODO: 清除token（如果使用Redis存储）
    return success_response(message="退出成功")

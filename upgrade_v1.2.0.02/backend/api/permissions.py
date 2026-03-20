# -*- coding: utf-8 -*-
"""
模板权限管理 API
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from models import get_db_session
from models.database import TemplatePermission, QueryTemplate, User, UserSchool
from api.auth import get_current_user

router = APIRouter(tags=["模板权限管理"])


# ============ Pydantic Models ============

class PermissionGrant(BaseModel):
    """授权请求"""
    user_id: int
    template_id: int
    can_query: Optional[bool] = True
    can_export: Optional[bool] = False


class BatchPermissionGrant(BaseModel):
    """批量授权请求"""
    user_id: int
    template_ids: List[int]
    can_query: Optional[bool] = True
    can_export: Optional[bool] = False


class PermissionResponse(BaseModel):
    """权限响应"""
    id: int
    user_id: int
    template_id: int
    can_query: int
    can_export: int

    class Config:
        from_attributes = True


# ============ API Routes ============

@router.get("/templates/{template_id}/permissions", summary="获取模板的权限列表")
async def get_template_permissions(
    template_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """获取指定模板的用户权限列表"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    # 检查模板是否存在
    template = db.query(QueryTemplate).filter(QueryTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    permissions = db.query(TemplatePermission).filter(
        TemplatePermission.template_id == template_id
    ).all()
    
    result = []
    for p in permissions:
        user = db.query(User).filter(User.id == p.user_id).first()
        result.append({
            **p.to_dict(),
            "user_name": user.name if user else None,
            "user_phone": user.phone if user else None
        })
    
    return {
        "code": 200,
        "data": result
    }


@router.get("/users/{user_id}/template-permissions", summary="获取用户的模板权限")
async def get_user_template_permissions(
    user_id: int,
    school_id: int = None,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """获取用户的所有模板权限"""
    if current_user.role != 'admin' and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="无权查看")
    
    query = db.query(TemplatePermission).filter(TemplatePermission.user_id == user_id)
    
    permissions = query.all()
    
    result = []
    for p in permissions:
        template = db.query(QueryTemplate).filter(QueryTemplate.id == p.template_id).first()
        if template:
            # 如果指定了 school_id，过滤
            if school_id and template.school_id != school_id:
                continue
            result.append({
                **p.to_dict(),
                "template_name": template.name,
                "template_category": template.category_name,
                "school_id": template.school_id
            })
    
    return {
        "code": 200,
        "data": result
    }


@router.post("/permissions", summary="授权用户模板权限")
async def grant_permission(
    request: PermissionGrant,
    req: Request,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """为用户授权模板权限"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    # 检查用户和模板是否存在
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    template = db.query(QueryTemplate).filter(QueryTemplate.id == request.template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 检查是否已有权限
    existing = db.query(TemplatePermission).filter(
        TemplatePermission.user_id == request.user_id,
        TemplatePermission.template_id == request.template_id
    ).first()
    
    if existing:
        # 更新
        existing.can_query = 1 if request.can_query else 0
        existing.can_export = 1 if request.can_export else 0
        db.commit()
        db.refresh(existing)
        return {
            "code": 200,
            "message": "权限已更新",
            "data": existing.to_dict()
        }
    
    # 创建新权限
    permission = TemplatePermission(
        user_id=request.user_id,
        template_id=request.template_id,
        can_query=1 if request.can_query else 0,
        can_export=1 if request.can_export else 0
    )
    db.add(permission)
    db.commit()
    db.refresh(permission)
    
    return {
        "code": 200,
        "message": "授权成功",
        "data": permission.to_dict()
    }


@router.post("/permissions/batch", summary="批量授权模板权限")
async def batch_grant_permission(
    request: BatchPermissionGrant,
    req: Request,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """批量为用户授权多个模板权限"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    granted = 0
    for template_id in request.template_ids:
        # 检查模板是否存在
        template = db.query(QueryTemplate).filter(QueryTemplate.id == template_id).first()
        if not template:
            continue
        
        # 检查是否已有权限
        existing = db.query(TemplatePermission).filter(
            TemplatePermission.user_id == request.user_id,
            TemplatePermission.template_id == template_id
        ).first()
        
        if not existing:
            permission = TemplatePermission(
                user_id=request.user_id,
                template_id=template_id,
                can_query=1 if request.can_query else 0,
                can_export=1 if request.can_export else 0
            )
            db.add(permission)
            granted += 1
    
    db.commit()
    
    return {
        "code": 200,
        "message": f"成功授权 {granted} 个模板"
    }


@router.delete("/permissions/{permission_id}", summary="撤销模板权限")
async def revoke_permission(
    permission_id: int,
    req: Request,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """撤销用户的模板权限"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    permission = db.query(TemplatePermission).filter(TemplatePermission.id == permission_id).first()
    if not permission:
        raise HTTPException(status_code=404, detail="权限记录不存在")
    
    db.delete(permission)
    db.commit()
    
    return {
        "code": 200,
        "message": "权限已撤销"
    }


@router.delete("/users/{user_id}/templates/{template_id}", summary="撤销用户指定模板权限")
async def revoke_user_template_permission(
    user_id: int,
    template_id: int,
    req: Request,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """撤销用户指定模板的权限"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    permission = db.query(TemplatePermission).filter(
        TemplatePermission.user_id == user_id,
        TemplatePermission.template_id == template_id
    ).first()
    
    if not permission:
        raise HTTPException(status_code=404, detail="权限记录不存在")
    
    db.delete(permission)
    db.commit()
    
    return {
        "code": 200,
        "message": "权限已撤销"
    }

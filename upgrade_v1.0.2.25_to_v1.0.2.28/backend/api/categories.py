# -*- coding: utf-8 -*-
"""
业务大类管理 API
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from core.database import get_db
from models.database import TemplateCategory, School, User
from api.auth import get_current_user

router = APIRouter(tags=["业务大类管理"])


# ============ Pydantic Models ============

class CategoryCreate(BaseModel):
    """创建业务大类"""
    school_id: int
    code: str
    name: str
    icon: Optional[str] = None
    sort_order: Optional[int] = 0
    description: Optional[str] = None


class CategoryUpdate(BaseModel):
    """更新业务大类"""
    name: Optional[str] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = None
    description: Optional[str] = None
    status: Optional[str] = None


class CategoryResponse(BaseModel):
    """业务大类响应"""
    id: int
    school_id: int
    code: str
    name: str
    icon: Optional[str]
    sort_order: int
    description: Optional[str]
    status: str

    class Config:
        from_attributes = True


# ============ API Routes ============

@router.get("/categories", summary="获取业务大类列表")
async def get_categories(
    school_id: int = None,
    req: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取业务大类列表"""
    query = db.query(TemplateCategory)
    
    if school_id:
        query = query.filter(TemplateCategory.school_id == school_id)
    
    categories = query.order_by(TemplateCategory.sort_order).all()
    
    return {
        "code": 200,
        "data": [c.to_dict() for c in categories]
    }


@router.post("/categories", summary="创建业务大类")
async def create_category(
    request: CategoryCreate,
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建业务大类"""
    # 检查权限
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    # 检查学校是否存在
    school = db.query(School).filter(School.id == request.school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="学校不存在")
    
    # 检查编码是否重复
    existing = db.query(TemplateCategory).filter(
        TemplateCategory.school_id == request.school_id,
        TemplateCategory.code == request.code
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="业务大类编码已存在")
    
    # 创建
    category = TemplateCategory(
        school_id=request.school_id,
        code=request.code,
        name=request.name,
        icon=request.icon,
        sort_order=request.sort_order or 0,
        description=request.description
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    
    return {
        "code": 200,
        "message": "创建成功",
        "data": category.to_dict()
    }


@router.put("/categories/{category_id}", summary="更新业务大类")
async def update_category(
    category_id: int,
    request: CategoryUpdate,
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新业务大类"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    category = db.query(TemplateCategory).filter(TemplateCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="业务大类不存在")
    
    # 更新字段
    if request.name is not None:
        category.name = request.name
    if request.icon is not None:
        category.icon = request.icon
    if request.sort_order is not None:
        category.sort_order = request.sort_order
    if request.description is not None:
        category.description = request.description
    if request.status is not None:
        category.status = request.status
    
    db.commit()
    db.refresh(category)
    
    return {
        "code": 200,
        "message": "更新成功",
        "data": category.to_dict()
    }


@router.delete("/categories/{category_id}", summary="删除业务大类")
async def delete_category(
    category_id: int,
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除业务大类"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    category = db.query(TemplateCategory).filter(TemplateCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="业务大类不存在")
    
    # 检查是否有关联的模板
    from models.database import QueryTemplate
    templates = db.query(QueryTemplate).filter(QueryTemplate.category_id == category_id).count()
    if templates > 0:
        raise HTTPException(status_code=400, detail=f"该业务大类下有 {templates} 个模板，无法删除")
    
    db.delete(category)
    db.commit()
    
    return {
        "code": 200,
        "message": "删除成功"
    }

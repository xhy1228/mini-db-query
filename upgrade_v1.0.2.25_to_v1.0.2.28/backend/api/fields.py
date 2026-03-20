# -*- coding: utf-8 -*-
"""
查询条件管理 API
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from core.database import get_db
from models.database import QueryField, QueryTemplate, User
from api.auth import get_current_user

router = APIRouter(tags=["查询条件管理"])


# ============ Pydantic Models ============

class FieldCreate(BaseModel):
    """创建查询条件"""
    template_id: int
    field_key: str
    field_label: str
    field_type: Optional[str] = "text"
    db_column: Optional[str] = None
    operator: Optional[str] = "="
    default_value: Optional[str] = None
    options: Optional[dict] = None
    required: Optional[bool] = False
    sort_order: Optional[int] = 0
    placeholder: Optional[str] = None


class FieldUpdate(BaseModel):
    """更新查询条件"""
    field_label: Optional[str] = None
    field_type: Optional[str] = None
    db_column: Optional[str] = None
    operator: Optional[str] = None
    default_value: Optional[str] = None
    options: Optional[dict] = None
    required: Optional[bool] = None
    sort_order: Optional[int] = None
    placeholder: Optional[str] = None


class FieldResponse(BaseModel):
    """查询条件响应"""
    id: int
    template_id: int
    field_key: str
    field_label: str
    field_type: str
    db_column: Optional[str]
    operator: str
    default_value: Optional[str]
    options: Optional[dict]
    required: int
    sort_order: int
    placeholder: Optional[str]

    class Config:
        from_attributes = True


# ============ API Routes ============

@router.get("/templates/{template_id}/fields", summary="获取模板的查询条件")
async def get_template_fields(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定模板的查询条件列表"""
    # 检查模板是否存在
    template = db.query(QueryTemplate).filter(QueryTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    fields = db.query(QueryField).filter(
        QueryField.template_id == template_id
    ).order_by(QueryField.sort_order).all()
    
    return {
        "code": 200,
        "data": [f.to_dict() for f in fields]
    }


@router.post("/templates/{template_id}/fields", summary="添加查询条件")
async def create_field(
    template_id: int,
    request: FieldCreate,
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """为模板添加查询条件"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    # 检查模板是否存在
    template = db.query(QueryTemplate).filter(QueryTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 检查字段标识是否重复
    existing = db.query(QueryField).filter(
        QueryField.template_id == template_id,
        QueryField.field_key == request.field_key
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="字段标识已存在")
    
    # 创建
    field = QueryField(
        template_id=template_id,
        field_key=request.field_key,
        field_label=request.field_label,
        field_type=request.field_type or "text",
        db_column=request.db_column,
        operator=request.operator or "=",
        default_value=request.default_value,
        options=request.options,
        required=1 if request.required else 0,
        sort_order=request.sort_order or 0,
        placeholder=request.placeholder
    )
    db.add(field)
    db.commit()
    db.refresh(field)
    
    return {
        "code": 200,
        "message": "创建成功",
        "data": field.to_dict()
    }


@router.put("/fields/{field_id}", summary="更新查询条件")
async def update_field(
    field_id: int,
    request: FieldUpdate,
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新查询条件"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    field = db.query(QueryField).filter(QueryField.id == field_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="查询条件不存在")
    
    # 更新字段
    if request.field_label is not None:
        field.field_label = request.field_label
    if request.field_type is not None:
        field.field_type = request.field_type
    if request.db_column is not None:
        field.db_column = request.db_column
    if request.operator is not None:
        field.operator = request.operator
    if request.default_value is not None:
        field.default_value = request.default_value
    if request.options is not None:
        field.options = request.options
    if request.required is not None:
        field.required = 1 if request.required else 0
    if request.sort_order is not None:
        field.sort_order = request.sort_order
    if request.placeholder is not None:
        field.placeholder = request.placeholder
    
    db.commit()
    db.refresh(field)
    
    return {
        "code": 200,
        "message": "更新成功",
        "data": field.to_dict()
    }


@router.delete("/fields/{field_id}", summary="删除查询条件")
async def delete_field(
    field_id: int,
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除查询条件"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    field = db.query(QueryField).filter(QueryField.id == field_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="查询条件不存在")
    
    db.delete(field)
    db.commit()
    
    return {
        "code": 200,
        "message": "删除成功"
    }


@router.post("/templates/{template_id}/fields/batch", summary="批量添加查询条件")
async def batch_create_fields(
    template_id: int,
    fields: List[FieldCreate],
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量添加查询条件"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    # 检查模板是否存在
    template = db.query(QueryTemplate).filter(QueryTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    created = 0
    for field_data in fields:
        # 检查是否已存在
        existing = db.query(QueryField).filter(
            QueryField.template_id == template_id,
            QueryField.field_key == field_data.field_key
        ).first()
        
        if not existing:
            field = QueryField(
                template_id=template_id,
                field_key=field_data.field_key,
                field_label=field_data.field_label,
                field_type=field_data.field_type or "text",
                db_column=field_data.db_column,
                operator=field_data.operator or "=",
                default_value=field_data.default_value,
                options=field_data.options,
                required=1 if field_data.required else 0,
                sort_order=field_data.sort_order or 0,
                placeholder=field_data.placeholder
            )
            db.add(field)
            created += 1
    
    db.commit()
    
    return {
        "code": 200,
        "message": f"成功创建 {created} 个查询条件"
    }

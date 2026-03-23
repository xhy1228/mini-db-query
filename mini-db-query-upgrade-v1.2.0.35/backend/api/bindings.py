# -*- coding: utf-8 -*-
"""
学校-模板绑定管理 API - v1.2.0

核心功能：
- 学校绑定模板，指定使用的数据库
- 查询学校可用的功能列表
- 启用/禁用绑定
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from models import get_db_session
from models.database import (
    SchoolTemplateBinding, QueryTemplate, DatabaseConfig, 
    School, User, QueryField, TemplateCategory
)
from api.auth import get_current_user

router = APIRouter(tags=["学校-模板绑定管理"])


# ============ Pydantic Models ============

class BindingCreate(BaseModel):
    """创建绑定"""
    school_id: int
    template_id: int
    database_id: int
    enabled: Optional[bool] = True
    custom_name: Optional[str] = None
    sort_order: Optional[int] = 0


class BindingUpdate(BaseModel):
    """更新绑定"""
    database_id: Optional[int] = None
    enabled: Optional[bool] = None
    custom_name: Optional[str] = None
    sort_order: Optional[int] = None


class BindingResponse(BaseModel):
    """绑定响应"""
    id: int
    school_id: int
    template_id: int
    database_id: int
    enabled: int
    custom_name: Optional[str]
    sort_order: int
    
    class Config:
        from_attributes = True


# ============ API Routes ============

@router.get("/bindings", summary="获取所有绑定列表")
async def get_all_bindings(
    school_id: int = None,
    template_id: int = None,
    enabled: int = None,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """获取所有绑定列表（管理员）"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    query = db.query(SchoolTemplateBinding)
    
    if school_id:
        query = query.filter(SchoolTemplateBinding.school_id == school_id)
    if template_id:
        query = query.filter(SchoolTemplateBinding.template_id == template_id)
    if enabled is not None:
        query = query.filter(SchoolTemplateBinding.enabled == enabled)
    
    bindings = query.order_by(SchoolTemplateBinding.sort_order).all()
    
    return {
        "code": 200,
        "data": [b.to_dict() for b in bindings]
    }


@router.get("/schools/{school_id}/bindings", summary="获取学校的绑定列表")
async def get_school_bindings(
    school_id: int,
    enabled_only: bool = False,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """获取指定学校的所有绑定"""
    # 检查学校是否存在
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="学校不存在")
    
    query = db.query(SchoolTemplateBinding).filter(
        SchoolTemplateBinding.school_id == school_id
    )
    
    if enabled_only:
        query = query.filter(SchoolTemplateBinding.enabled == 1)
    
    bindings = query.order_by(SchoolTemplateBinding.sort_order).all()
    
    # 补充模板详细信息
    result = []
    for b in bindings:
        binding_dict = b.to_dict()
        template = b.template
        if template:
            binding_dict['template_category'] = template.category
            binding_dict['template_category_name'] = template.category_name or template.category
            binding_dict['template_category_icon'] = template.category_icon
            binding_dict['template_description'] = template.description
            
            # 获取查询字段
            fields = db.query(QueryField).filter(
                QueryField.template_id == template.id
            ).order_by(QueryField.sort_order).all()
            
            binding_dict['fields'] = [
                {
                    'id': f.field_key,
                    'label': f.field_label,
                    'column': f.db_column or f.field_key,
                    'type': f.field_type or 'text',
                    'operator': f.operator or '=',
                    'default_value': f.default_value,
                    'options': f.options,
                    'required': bool(f.required),
                    'placeholder': f.placeholder
                }
                for f in fields
            ]
        
        result.append(binding_dict)
    
    return {
        "code": 200,
        "data": result
    }


@router.get("/schools/{school_id}/databases", summary="获取学校可用的数据库列表")
async def get_school_databases(
    school_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """获取学校下配置的所有数据库连接"""
    # 检查学校是否存在
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="学校不存在")
    
    # 获取学校下的所有数据库配置
    databases = db.query(DatabaseConfig).filter(
        DatabaseConfig.school_id == school_id,
        DatabaseConfig.status == 'active'
    ).order_by(DatabaseConfig.id).all()
    
    return {
        "code": 200,
        "data": [
            {
                "id": db.id,
                "name": db.name,
                "db_type": db.db_type,
                "host": db.host,
                "port": db.port,
                "db_name": db.db_name,
                "service_name": db.service_name,
                "description": db.description
            }
            for db in databases
        ]
    }


@router.get("/schools/{school_id}/functions", summary="获取学校可用的功能列表（小程序用）")
async def get_school_functions(
    school_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """获取学校可用的功能列表（按分类分组）"""
    # 检查学校是否存在
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="学校不存在")
    
    # 获取启用的绑定
    bindings = db.query(SchoolTemplateBinding).filter(
        SchoolTemplateBinding.school_id == school_id,
        SchoolTemplateBinding.enabled == 1
    ).order_by(SchoolTemplateBinding.sort_order).all()
    
    # 按分类分组
    categories = {}
    for b in bindings:
        template = b.template
        if not template:
            continue
        
        if not template:
            continue
        
        category_key = template.category
        if category_key not in categories:
            # 优先从 template_categories 表获取名称
            category_name = None
            category_icon = None
            
            # 1. 先通过 category_id 查询
            if template.category_id:
                cat_obj = db.query(TemplateCategory).filter(TemplateCategory.id == template.category_id).first()
                if cat_obj:
                    category_name = cat_obj.name
                    category_icon = cat_obj.icon
            
            # 2. 再尝试通过 category（code）查询，不限制 school_id
            if not category_name and template.category:
                cat_obj = db.query(TemplateCategory).filter(
                    TemplateCategory.code == template.category
                ).first()
                if cat_obj:
                    category_name = cat_obj.name
                    category_icon = cat_obj.icon
            
            # 3. 使用默认映射表作为后备
            DEFAULT_CATEGORIES = {
                'consume': {'name': '消费业务', 'icon': '💰'},
                'access': {'name': '门禁业务', 'icon': '🚪'},
                'wechat': {'name': '微信业务', 'icon': '💬'},
                'student': {'name': '学生业务', 'icon': '🎓'},
                'recharge': {'name': '充值业务', 'icon': '💳'},
            }
            if not category_name and category_key in DEFAULT_CATEGORIES:
                category_name = DEFAULT_CATEGORIES[category_key]['name']
                category_icon = DEFAULT_CATEGORIES[category_key]['icon']
            
            # 4. 最后使用 template 自身的字段或编码
            if not category_name:
                category_name = template.category_name or template.category or '未分类'
            if not category_icon:
                category_icon = template.category_icon or '📄'
            
            categories[category_key] = {
                'category': category_key,
                'category_name': category_name,
                'category_icon': category_icon,
                'functions': []
            }
        
        # 获取查询字段（支持两种方式：JSON字段和关联表）
        fields = db.query(QueryField).filter(
            QueryField.template_id == template.id
        ).order_by(QueryField.sort_order).all()
        
        # 如果关联表没有字段，尝试从JSON字段获取
        if not fields and template.fields:
            # template.fields 是JSON数组
            field_list = template.fields if isinstance(template.fields, list) else []
            fields = field_list
        
        # description 为空时返回空字符串而不是 null
        func_description = template.description if template.description else ''
        
        # description 为空时返回空字符串
        func_description = template.description if template.description else ''
        
        # 构建字段列表（支持两种数据格式）
        def build_field(f):
            # 判断是QueryField对象还是字典
            if hasattr(f, 'field_key'):  # QueryField对象
                return {
                    'id': f.field_key,
                    'label': f.field_label,
                    'column': f.db_column or f.field_key,
                    'type': f.field_type or 'text',
                    'operator': f.operator or '=',
                    'default_value': f.default_value,
                    'options': f.options,
                    'required': bool(f.required),
                    'placeholder': f.placeholder
                }
            else:  # JSON字典 - 支持多种字段名格式
                return {
                    'id': f.get('id') or f.get('field_key', ''),
                    'label': f.get('label') or f.get('field_label', '') or f.get('name', ''),
                    'column': f.get('column') or f.get('db_column', f.get('field_key', '')),
                    'type': f.get('type', 'text'),
                    'operator': f.get('operator', '='),
                    'default_value': f.get('default_value'),
                    'options': f.get('options'),
                    'required': bool(f.get('required', False)),
                    'placeholder': f.get('placeholder', '')
                }
        
        categories[category_key]['functions'].append({
            'binding_id': b.id,
            'template_id': template.id,
            'name': b.custom_name or template.name,
            'description': func_description,
            'icon': template.category_icon,
            'time_field': template.time_field,
            'default_limit': template.default_limit,
            'fields': [build_field(f) for f in fields]
        })
    
    return {
        "code": 200,
        "data": {
            "school": school.to_dict(),
            "categories": list(categories.values())
        }
    }


@router.post("/schools/{school_id}/bindings", summary="为学校添加功能绑定")
async def create_binding(
    school_id: int,
    request: BindingCreate,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """为学校添加功能绑定"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    # 验证学校
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="学校不存在")
    
    # 验证模板
    template = db.query(QueryTemplate).filter(QueryTemplate.id == request.template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 验证数据库配置
    database = db.query(DatabaseConfig).filter(DatabaseConfig.id == request.database_id).first()
    if not database:
        raise HTTPException(status_code=404, detail="数据库配置不存在")
    
    # 验证数据库属于该学校
    if database.school_id != school_id:
        raise HTTPException(status_code=400, detail="该数据库配置不属于此学校")
    
    # 检查是否已绑定
    existing = db.query(SchoolTemplateBinding).filter(
        SchoolTemplateBinding.school_id == school_id,
        SchoolTemplateBinding.template_id == request.template_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="该模板已绑定到此学校")
    
    # 检查数据库类型是否支持
    supported_types = template.supported_db_types or ['MySQL', 'Oracle']
    if database.db_type not in supported_types:
        raise HTTPException(
            status_code=400, 
            detail=f"该模板不支持 {database.db_type} 数据库，支持类型: {', '.join(supported_types)}"
        )
    
    # 创建绑定
    binding = SchoolTemplateBinding(
        school_id=school_id,
        template_id=request.template_id,
        database_id=request.database_id,
        enabled=1 if request.enabled else 0,
        custom_name=request.custom_name,
        sort_order=request.sort_order or 0
    )
    db.add(binding)
    db.commit()
    db.refresh(binding)
    
    return {
        "code": 200,
        "message": "绑定成功",
        "data": binding.to_dict()
    }


@router.get("/bindings/{binding_id}", summary="获取绑定详情")
async def get_binding(
    binding_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """获取绑定详情"""
    binding = db.query(SchoolTemplateBinding).filter(
        SchoolTemplateBinding.id == binding_id
    ).first()
    
    if not binding:
        raise HTTPException(status_code=404, detail="绑定不存在")
    
    result = binding.to_dict()
    
    # 补充详细信息
    if binding.template:
        template = binding.template
        result['sql_template'] = template.sql_template
        result['template_description'] = template.description
        result['time_field'] = template.time_field
        result['default_limit'] = template.default_limit
        
        # 获取查询字段
        fields = db.query(QueryField).filter(
            QueryField.template_id == template.id
        ).order_by(QueryField.sort_order).all()
        
        result['fields'] = [
            {
                'id': f.field_key,
                'label': f.field_label,
                'column': f.db_column or f.field_key,
                'type': f.field_type or 'text',
                'operator': f.operator or '=',
                'default_value': f.default_value,
                'options': f.options,
                'required': bool(f.required),
                'placeholder': f.placeholder
            }
            for f in fields
        ]
    
    if binding.database:
        db_config = binding.database
        result['database_config'] = {
            'id': db_config.id,
            'name': db_config.name,
            'db_type': db_config.db_type,
            'host': db_config.host,
            'port': db_config.port,
            'db_name': db_config.db_name
        }
    
    return {
        "code": 200,
        "data": result
    }


@router.put("/bindings/{binding_id}", summary="更新绑定")
async def update_binding(
    binding_id: int,
    request: BindingUpdate,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """更新绑定配置"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    binding = db.query(SchoolTemplateBinding).filter(
        SchoolTemplateBinding.id == binding_id
    ).first()
    
    if not binding:
        raise HTTPException(status_code=404, detail="绑定不存在")
    
    # 更新字段
    if request.database_id is not None:
        # 验证数据库配置
        database = db.query(DatabaseConfig).filter(
            DatabaseConfig.id == request.database_id
        ).first()
        if not database:
            raise HTTPException(status_code=404, detail="数据库配置不存在")
        
        if database.school_id != binding.school_id:
            raise HTTPException(status_code=400, detail="该数据库配置不属于此学校")
        
        # 检查数据库类型是否支持
        template = binding.template
        if template:
            supported_types = template.supported_db_types or ['MySQL', 'Oracle']
            if database.db_type not in supported_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"该模板不支持 {database.db_type} 数据库"
                )
        
        binding.database_id = request.database_id
    
    if request.enabled is not None:
        binding.enabled = 1 if request.enabled else 0
    
    if request.custom_name is not None:
        binding.custom_name = request.custom_name
    
    if request.sort_order is not None:
        binding.sort_order = request.sort_order
    
    db.commit()
    db.refresh(binding)
    
    return {
        "code": 200,
        "message": "更新成功",
        "data": binding.to_dict()
    }


@router.delete("/bindings/{binding_id}", summary="删除绑定")
async def delete_binding(
    binding_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """删除绑定"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    binding = db.query(SchoolTemplateBinding).filter(
        SchoolTemplateBinding.id == binding_id
    ).first()
    
    if not binding:
        raise HTTPException(status_code=404, detail="绑定不存在")
    
    db.delete(binding)
    db.commit()
    
    return {
        "code": 200,
        "message": "删除成功"
    }


@router.post("/bindings/batch", summary="批量创建绑定")
async def batch_create_bindings(
    school_id: int,
    bindings: List[BindingCreate],
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """批量创建绑定"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    # 验证学校
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="学校不存在")
    
    created = 0
    errors = []
    
    for i, binding_data in enumerate(bindings):
        try:
            # 验证模板
            template = db.query(QueryTemplate).filter(
                QueryTemplate.id == binding_data.template_id
            ).first()
            if not template:
                errors.append(f"第{i+1}条: 模板不存在")
                continue
            
            # 验证数据库
            database = db.query(DatabaseConfig).filter(
                DatabaseConfig.id == binding_data.database_id
            ).first()
            if not database:
                errors.append(f"第{i+1}条: 数据库配置不存在")
                continue
            
            if database.school_id != school_id:
                errors.append(f"第{i+1}条: 数据库不属于此学校")
                continue
            
            # 检查是否已绑定
            existing = db.query(SchoolTemplateBinding).filter(
                SchoolTemplateBinding.school_id == school_id,
                SchoolTemplateBinding.template_id == binding_data.template_id
            ).first()
            
            if existing:
                errors.append(f"第{i+1}条: 模板'{template.name}'已绑定")
                continue
            
            # 创建绑定
            binding = SchoolTemplateBinding(
                school_id=school_id,
                template_id=binding_data.template_id,
                database_id=binding_data.database_id,
                enabled=1 if binding_data.enabled else 0,
                custom_name=binding_data.custom_name,
                sort_order=binding_data.sort_order or 0
            )
            db.add(binding)
            created += 1
            
        except Exception as e:
            errors.append(f"第{i+1}条: {str(e)}")
    
    db.commit()
    
    return {
        "code": 200,
        "message": f"成功创建 {created} 个绑定",
        "data": {
            "created": created,
            "errors": errors
        }
    }

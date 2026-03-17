# -*- coding: utf-8 -*-
"""
Mini DB Query - Management API

学校、数据库配置、查询模板的CRUD管理
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from urllib.parse import quote_plus

from models import get_db_session
from models.database import School, DatabaseConfig, QueryTemplate, UserSchool
from core.security import get_current_user, TokenData
from core.config import settings

router = APIRouter(tags=["管理"])


# ========== 请求模型 ==========

class SchoolCreate(BaseModel):
    """创建学校"""
    name: str = Field(..., description="学校名称")
    code: str = Field(..., description="学校编码")
    description: Optional[str] = None


class SchoolUpdate(BaseModel):
    """更新学校"""
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class DatabaseCreate(BaseModel):
    """创建数据库配置"""
    school_id: int
    name: str = Field(..., description="配置名称")
    db_type: str = Field(..., description="数据库类型: MySQL/Oracle/SQLServer/SQLite")
    host: Optional[str] = "localhost"
    port: Optional[int] = 3306
    username: Optional[str] = ""
    password: Optional[str] = ""
    db_name: Optional[str] = ""
    service_name: Optional[str] = None
    driver: Optional[str] = None
    description: Optional[str] = None


class DatabaseUpdate(BaseModel):
    """更新数据库配置"""
    school_id: Optional[int] = None
    name: Optional[str] = None
    db_type: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    db_name: Optional[str] = None
    service_name: Optional[str] = None
    driver: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class TemplateCreate(BaseModel):
    """创建查询模板"""
    school_id: int
    category: str = Field(..., description="业务大类编码")
    category_name: Optional[str] = None
    category_icon: Optional[str] = None
    name: str = Field(..., description="模板名称")
    description: Optional[str] = None
    sql_template: str = Field(..., description="SQL模板")
    fields: Optional[List[dict]] = None
    time_field: Optional[str] = None
    default_limit: Optional[int] = 500


class TemplateUpdate(BaseModel):
    """更新查询模板"""
    school_id: Optional[int] = None
    category: Optional[str] = None
    category_name: Optional[str] = None
    category_icon: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    sql_template: Optional[str] = None
    fields: Optional[List[dict]] = None
    time_field: Optional[str] = None
    default_limit: Optional[int] = None
    status: Optional[str] = None


# ========== 学校管理 API ==========

@router.get("/schools")
async def list_schools(
    skip: int = 0,
    limit: int = 100,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """获取学校列表"""
    schools = db.query(School).offset(skip).limit(limit).all()
    return {
        "code": 200,
        "message": "获取成功",
        "data": [s.to_dict() for s in schools]
    }


@router.post("/schools")
async def create_school(
    request: SchoolCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """创建学校（管理员权限）"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 检查编码是否已存在
    existing = db.query(School).filter(School.code == request.code).first()
    if existing:
        return {"code": 400, "message": "学校编码已存在", "data": None}
    
    school = School(
        name=request.name,
        code=request.code,
        description=request.description
    )
    db.add(school)
    db.commit()
    db.refresh(school)
    
    return {"code": 200, "message": "创建成功", "data": school.to_dict()}


@router.get("/schools/{school_id}")
async def get_school(
    school_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """获取单个学校"""
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="学校不存在")
    return {"code": 200, "message": "获取成功", "data": school.to_dict()}


@router.put("/schools/{school_id}")
async def update_school(
    school_id: int,
    request: SchoolUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """更新学校（管理员权限）"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="学校不存在")
    
    update_data = request.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(school, key, value)
    
    db.commit()
    db.refresh(school)
    return {"code": 200, "message": "更新成功", "data": school.to_dict()}


@router.delete("/schools/{school_id}")
async def delete_school(
    school_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """删除学校（管理员权限）"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="学校不存在")
    
    db.delete(school)
    db.commit()
    return {"code": 200, "message": "删除成功", "data": None}


# ========== 数据库配置管理 API ==========

@router.get("/databases")
async def list_databases(
    school_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """获取数据库配置列表"""
    query = db.query(DatabaseConfig)
    if school_id:
        query = query.filter(DatabaseConfig.school_id == school_id)
    
    databases = query.offset(skip).limit(limit).all()
    return {
        "code": 200,
        "message": "获取成功",
        "data": [d.to_dict() for d in databases]
    }


@router.post("/databases")
async def create_database(
    request: DatabaseCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """创建数据库配置（管理员权限）"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 验证学校存在
    school = db.query(School).filter(School.id == request.school_id).first()
    if not school:
        return {"code": 400, "message": "学校不存在", "data": None}
    
    db_config = DatabaseConfig(
        school_id=request.school_id,
        name=request.name,
        db_type=request.db_type,
        host=request.host or "localhost",
        port=request.port or 3306,
        username=request.username or "",
        password=request.password or "",
        db_name=request.db_name or "",
        service_name=request.service_name,
        driver=request.driver,
        description=request.description
    )
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    
    return {"code": 200, "message": "创建成功", "data": db_config.to_dict()}


@router.get("/databases/{db_id}")
async def get_database(
    db_id: int,
    current_user: TokenData = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """获取单个数据库配置"""
    db_config = session.query(DatabaseConfig).filter(DatabaseConfig.id == db_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="配置不存在")
    return {"code": 200, "message": "获取成功", "data": db_config.to_dict()}


@router.put("/databases/{db_id}")
async def update_database(
    db_id: int,
    request: DatabaseUpdate,
    current_user: TokenData = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """更新数据库配置（管理员权限）"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    db_config = session.query(DatabaseConfig).filter(DatabaseConfig.id == db_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    update_data = request.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_config, key, value)
    
    session.commit()
    session.refresh(db_config)
    return {"code": 200, "message": "更新成功", "data": db_config.to_dict()}


@router.delete("/databases/{db_id}")
async def delete_database(
    db_id: int,
    current_user: TokenData = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """删除数据库配置（管理员权限）"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    db_config = session.query(DatabaseConfig).filter(DatabaseConfig.id == db_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    session.delete(db_config)
    session.commit()
    return {"code": 200, "message": "删除成功", "data": None}


@router.post("/databases/{db_id}/test")
async def test_database_connection(
    db_id: int,
    current_user: TokenData = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """测试数据库连接"""
    db_config = session.query(DatabaseConfig).filter(DatabaseConfig.id == db_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    try:
        from sqlalchemy import create_engine, text
        
        # 构建连接URL，对密码进行URL编码
        if db_config.db_type == 'MySQL':
            encoded_password = quote_plus(db_config.password)
            url = f"mysql+pymysql://{db_config.username}:{encoded_password}@{db_config.host}:{db_config.port}/{db_config.db_name}?charset=utf8mb4"
        elif db_config.db_type == 'Oracle':
            encoded_password = quote_plus(db_config.password)
            url = f"oracle+oracledb://{db_config.username}:{encoded_password}@{db_config.host}:{db_config.port}/?service_name={db_config.service_name}"
        else:
            return {"code": 400, "message": f"暂不支持 {db_config.db_type} 连接测试", "data": None}
        
        engine = create_engine(url, connect_args={"connect_timeout": 5})
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        
        return {"code": 200, "message": "连接成功", "data": {"connected": True}}
    except Exception as e:
        return {"code": 400, "message": f"连接失败: {str(e)}", "data": {"connected": False}}


# ========== 查询模板管理 API ==========

@router.get("/templates")
async def list_templates(
    school_id: Optional[int] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """获取查询模板列表"""
    query = db.query(QueryTemplate)
    if school_id:
        query = query.filter(QueryTemplate.school_id == school_id)
    if category:
        query = query.filter(QueryTemplate.category == category)
    
    templates = query.offset(skip).limit(limit).all()
    return {
        "code": 200,
        "message": "获取成功",
        "data": [t.to_dict() for t in templates]
    }


@router.post("/templates")
async def create_template(
    request: TemplateCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """创建查询模板（管理员权限）"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 验证学校存在
    school = db.query(School).filter(School.id == request.school_id).first()
    if not school:
        return {"code": 400, "message": "学校不存在", "data": None}
    
    template = QueryTemplate(
        school_id=request.school_id,
        category=request.category,
        category_name=request.category_name,
        category_icon=request.category_icon,
        name=request.name,
        description=request.description,
        sql_template=request.sql_template,
        fields=request.fields,
        time_field=request.time_field,
        default_limit=request.default_limit or 500
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return {"code": 200, "message": "创建成功", "data": template.to_dict()}


@router.get("/templates/{template_id}")
async def get_template(
    template_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """获取单个查询模板"""
    template = db.query(QueryTemplate).filter(QueryTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    return {"code": 200, "message": "获取成功", "data": template.to_dict()}


@router.put("/templates/{template_id}")
async def update_template(
    template_id: int,
    request: TemplateUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """更新查询模板（管理员权限）"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    template = db.query(QueryTemplate).filter(QueryTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    update_data = request.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(template, key, value)
    
    db.commit()
    db.refresh(template)
    return {"code": 200, "message": "更新成功", "data": template.to_dict()}


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """删除查询模板（管理员权限）"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    template = db.query(QueryTemplate).filter(QueryTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    db.delete(template)
    db.commit()
    return {"code": 200, "message": "删除成功", "data": None}


# ========== 业务大类统计 ==========

@router.get("/categories")
async def list_categories(
    school_id: Optional[int] = None,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """获取业务大类列表"""
    query = db.query(QueryTemplate)
    if school_id:
        query = query.filter(QueryTemplate.school_id == school_id)
    
    templates = query.all()
    
    # 按category分组
    categories = {}
    for t in templates:
        if t.category not in categories:
            categories[t.category] = {
                "category": t.category,
                "category_name": t.category_name,
                "category_icon": t.category_icon,
                "count": 0
            }
        categories[t.category]["count"] += 1
    
    return {
        "code": 200,
        "message": "获取成功",
        "data": list(categories.values())
    }

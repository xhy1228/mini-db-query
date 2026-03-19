# -*- coding: utf-8 -*-
"""
Mini DB Query - Management API

学校、数据库配置、查询模板的CRUD管理
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from urllib.parse import quote_plus

from models import get_db_session
from models.database import School, DatabaseConfig, QueryTemplate, UserSchool
from core.security import get_current_user, TokenData, encrypt_password, decrypt_password
from core.config import settings
from core.logging_middleware import OperationLogger

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
    school_id: Optional[int] = None
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
    school_id: Optional[int] = None
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
    req: Request,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """创建学校（管理员权限）"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    client_ip = req.client.host if req.client else "unknown"
    
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
    
    # 记录操作日志
    OperationLogger.log_create(
        db=db,
        resource_type="school",
        resource_id=school.id,
        resource_name=school.name,
        user_id=int(current_user.user_id),
        username=current_user.name if hasattr(current_user, 'name') else current_user.user_id,
        ip=client_ip,
        details=f"Created school: {school.name} ({school.code})"
    )
    
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
    req: Request,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """更新学校（管理员权限）"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    client_ip = req.client.host if req.client else "unknown"
    
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="学校不存在")
    
    update_data = request.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(school, key, value)
    
    db.commit()
    db.refresh(school)
    
    # 记录操作日志
    OperationLogger.log_update(
        db=db,
        resource_type="school",
        resource_id=school.id,
        resource_name=school.name,
        user_id=int(current_user.user_id),
        username=current_user.name if hasattr(current_user, 'name') else current_user.user_id,
        ip=client_ip,
        changes=update_data
    )
    
    return {"code": 200, "message": "更新成功", "data": school.to_dict()}


@router.delete("/schools/{school_id}")
async def delete_school(
    school_id: int,
    req: Request,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """删除学校（管理员权限）"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    client_ip = req.client.host if req.client else "unknown"
    
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="学校不存在")
    
    school_name = school.name
    
    db.delete(school)
    db.commit()
    
    # 记录操作日志
    OperationLogger.log_delete(
        db=db,
        resource_type="school",
        resource_id=school_id,
        resource_name=school_name,
        user_id=int(current_user.user_id),
        username=current_user.name if hasattr(current_user, 'name') else current_user.user_id,
        ip=client_ip
    )
    
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
    req: Request,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """创建数据库配置（管理员权限）"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    client_ip = req.client.host if req.client else "unknown"
    
    # 验证学校ID
    if not request.school_id:
        return {"code": 400, "message": "请选择学校", "data": None}
    
    # 验证学校存在
    school = db.query(School).filter(School.id == request.school_id).first()
    if not school:
        return {"code": 400, "message": "学校不存在", "data": None}
    
    # 加密密码
    encrypted_password = encrypt_password(request.password or "")
    
    db_config = DatabaseConfig(
        school_id=request.school_id,
        name=request.name,
        db_type=request.db_type,
        host=request.host or "localhost",
        port=request.port or 3306,
        username=request.username or "",
        password=encrypted_password,  # 加密存储
        db_name=request.db_name or "",
        service_name=request.service_name,
        driver=request.driver,
        description=request.description
    )
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    
    # 记录操作日志
    OperationLogger.log_create(
        db=db,
        resource_type="database",
        resource_id=db_config.id,
        resource_name=db_config.name,
        user_id=int(current_user.user_id),
        username=current_user.name if hasattr(current_user, 'name') else current_user.user_id,
        ip=client_ip,
        details=f"Created database config: {db_config.name} ({db_config.db_type}@{db_config.host}:{db_config.port})"
    )
    
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
    req: Request,
    current_user: TokenData = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """更新数据库配置（管理员权限）"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    client_ip = req.client.host if req.client else "unknown"
    
    db_config = session.query(DatabaseConfig).filter(DatabaseConfig.id == db_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    update_data = request.dict(exclude_unset=True)
    
    # 如果更新密码，需要加密
    if 'password' in update_data and update_data['password']:
        update_data['password'] = encrypt_password(update_data['password'])
    
    for key, value in update_data.items():
        setattr(db_config, key, value)
    
    session.commit()
    session.refresh(db_config)
    
    # 记录操作日志
    OperationLogger.log_update(
        db=session,
        resource_type="database",
        resource_id=db_config.id,
        resource_name=db_config.name,
        user_id=int(current_user.user_id),
        username=current_user.name if hasattr(current_user, 'name') else current_user.user_id,
        ip=client_ip,
        changes=update_data
    )
    
    return {"code": 200, "message": "更新成功", "data": db_config.to_dict()}


@router.delete("/databases/{db_id}")
async def delete_database(
    db_id: int,
    req: Request,
    current_user: TokenData = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """删除数据库配置（管理员权限）"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    client_ip = req.client.host if req.client else "unknown"
    
    db_config = session.query(DatabaseConfig).filter(DatabaseConfig.id == db_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    db_config_name = db_config.name
    
    session.delete(db_config)
    session.commit()
    
    # 记录操作日志
    OperationLogger.log_delete(
        db=session,
        resource_type="database",
        resource_id=db_id,
        resource_name=db_config_name,
        user_id=int(current_user.user_id),
        username=current_user.name if hasattr(current_user, 'name') else current_user.user_id,
        ip=client_ip
    )
    
    return {"code": 200, "message": "删除成功", "data": None}


class TestConnectionRequest(BaseModel):
    """测试连接请求"""
    db_type: str
    host: Optional[str] = "localhost"
    port: Optional[int] = 3306
    username: Optional[str] = ""
    password: Optional[str] = ""
    db_name: Optional[str] = ""
    service_name: Optional[str] = None


@router.post("/databases/test")
async def test_new_database_connection(
    request: TestConnectionRequest,
    current_user: TokenData = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """测试新数据库连接（保存前测试）"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    try:
        from sqlalchemy import create_engine, text
        
        # 构建连接URL，对密码进行URL编码
        if request.db_type == 'MySQL':
            encoded_password = quote_plus(request.password)
            url = f"mysql+pymysql://{request.username}:{encoded_password}@{request.host}:{request.port}/{request.db_name}?charset=utf8mb4"
            engine = create_engine(url, connect_args={"connect_timeout": 5})
            with engine.connect() as conn:
                result = conn.execute(text("SELECT VERSION()"))
                version = result.scalar()
            
            return {
                "code": 200,
                "message": "连接成功",
                "data": {
                    "connected": True,
                    "version": version
                }
            }
        elif request.db_type == 'Oracle':
            encoded_password = quote_plus(request.password)
            url = f"oracle+oracledb://{request.username}:{encoded_password}@{request.host}:{request.port}/?service_name={request.service_name}"
            engine = create_engine(url, connect_args={"connect_timeout": 5})
            with engine.connect() as conn:
                result = conn.execute(text("SELECT * FROM v$version WHERE banner LIKE 'Oracle%'"))
                row = result.fetchone()
                version = row[0] if row else "Oracle"
            
            return {
                "code": 200,
                "message": "连接成功",
                "data": {
                    "connected": True,
                    "version": version
                }
            }
        elif request.db_type == 'SQLite':
            url = f"sqlite:///{request.db_name}"
            engine = create_engine(url)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT sqlite_version()"))
                version = result.scalar()
            
            return {
                "code": 200,
                "message": "连接成功",
                "data": {
                    "connected": True,
                    "version": version
                }
            }
        else:
            return {"code": 400, "message": f"暂不支持 {request.db_type} 连接测试", "data": None}
        
    except Exception as e:
        import logging
        logging.error(f"数据库连接测试失败: {e}")
        return {
            "code": 400,
            "message": f"连接失败: {str(e)}",
            "data": {
                "connected": False,
                "error": str(e)
            }
        }


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
        
        # 解密密码
        try:
            plain_password = decrypt_password(db_config.password)
        except:
            # 如果解密失败，尝试使用原始密码（兼容旧数据）
            plain_password = db_config.password
        
        # 构建连接URL，对密码进行URL编码
        if db_config.db_type == 'MySQL':
            encoded_password = quote_plus(plain_password)
            url = f"mysql+pymysql://{db_config.username}:{encoded_password}@{db_config.host}:{db_config.port}/{db_config.db_name}?charset=utf8mb4"
        elif db_config.db_type == 'Oracle':
            encoded_password = quote_plus(plain_password)
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
    req: Request,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """创建查询模板（管理员权限）"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    client_ip = req.client.host if req.client else "unknown"
    
    # 验证学校ID
    if not request.school_id:
        return {"code": 400, "message": "请选择学校", "data": None}
    
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
    
    # 记录操作日志
    OperationLogger.log_create(
        db=db,
        resource_type="template",
        resource_id=template.id,
        resource_name=template.name,
        user_id=int(current_user.user_id),
        username=current_user.name if hasattr(current_user, 'name') else current_user.user_id,
        ip=client_ip,
        details=f"Created template: {template.name} (category={template.category})"
    )
    
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
    req: Request,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """更新查询模板（管理员权限）"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    client_ip = req.client.host if req.client else "unknown"
    
    template = db.query(QueryTemplate).filter(QueryTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    update_data = request.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(template, key, value)
    
    db.commit()
    db.refresh(template)
    
    # 记录操作日志
    OperationLogger.log_update(
        db=db,
        resource_type="template",
        resource_id=template.id,
        resource_name=template.name,
        user_id=int(current_user.user_id),
        username=current_user.name if hasattr(current_user, 'name') else current_user.user_id,
        ip=client_ip,
        changes=update_data
    )
    
    return {"code": 200, "message": "更新成功", "data": template.to_dict()}


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: int,
    req: Request,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """删除查询模板（管理员权限）"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    client_ip = req.client.host if req.client else "unknown"
    
    template = db.query(QueryTemplate).filter(QueryTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    template_name = template.name
    
    db.delete(template)
    db.commit()
    
    # 记录操作日志
    OperationLogger.log_delete(
        db=db,
        resource_type="template",
        resource_id=template_id,
        resource_name=template_name,
        user_id=int(current_user.user_id),
        username=current_user.name if hasattr(current_user, 'name') else current_user.user_id,
        ip=client_ip
    )
    
    return {"code": 200, "message": "删除成功", "data": None}


# ========== 用户授权管理 API ==========

@router.get("/users/{user_id}/schools")
async def get_user_schools(
    user_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """获取用户授权的学校"""
    if current_user.role != 'admin' and int(current_user.user_id) != user_id:
        raise HTTPException(status_code=403, detail="权限不足")
    
    from services.user_service import UserService
    schools = UserService.get_user_schools(db, user_id)
    return {"code": 200, "message": "获取成功", "data": schools}


@router.post("/users/{user_id}/schools")
async def assign_user_school(
    user_id: int,
    request: dict,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """为用户授权学校（管理员权限）"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    school_id = request.get('school_id')
    if not school_id:
        return {"code": 400, "message": "学校ID不能为空", "data": None}
    
    # 检查是否已授权
    existing = db.query(UserSchool).filter(
        UserSchool.user_id == user_id,
        UserSchool.school_id == school_id
    ).first()
    
    if existing:
        return {"code": 400, "message": "已授权该学校", "data": None}
    
    user_school = UserSchool(user_id=user_id, school_id=school_id)
    db.add(user_school)
    db.commit()
    
    return {"code": 200, "message": "授权成功", "data": None}


@router.delete("/users/{user_id}/schools/{school_id}")
async def remove_user_school(
    user_id: int,
    school_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """取消用户学校授权（管理员权限）"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    user_school = db.query(UserSchool).filter(
        UserSchool.user_id == user_id,
        UserSchool.school_id == school_id
    ).first()
    
    if not user_school:
        raise HTTPException(status_code=404, detail="授权记录不存在")
    
    db.delete(user_school)
    db.commit()
    return {"code": 200, "message": "取消授权成功", "data": None}


# ========== 系统配置管理 API ==========

class SystemConfigUpdate(BaseModel):
    """更新系统配置"""
    config_value: str


@router.get("/system/configs")
async def list_system_configs(
    category: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """获取系统配置列表"""
    from models.database import SystemConfig
    
    query = db.query(SystemConfig)
    if category:
        query = query.filter(SystemConfig.category == category)
    
    configs = query.all()
    
    # 管理员可以看到完整配置，普通用户只能看到隐藏后的
    hide_secret = current_user.role != 'admin'
    
    return {
        "code": 200,
        "message": "获取成功",
        "data": [c.to_dict(hide_secret=hide_secret) for c in configs]
    }


@router.get("/system/configs/{config_key}")
async def get_system_config(
    config_key: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """获取单个系统配置"""
    from models.database import SystemConfig
    
    config = db.query(SystemConfig).filter(SystemConfig.config_key == config_key).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    # 管理员可以看到完整配置
    hide_secret = current_user.role != 'admin'
    
    return {"code": 200, "message": "获取成功", "data": config.to_dict(hide_secret=hide_secret)}


@router.put("/system/configs/{config_key}")
async def update_system_config(
    config_key: str,
    request: SystemConfigUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """更新系统配置（管理员权限）"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    from models.database import SystemConfig
    
    config = db.query(SystemConfig).filter(SystemConfig.config_key == config_key).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    # 如果是敏感配置，加密存储
    if config.config_type == 'secret' and request.config_value:
        config.config_value = encrypt_password(request.config_value)
    else:
        config.config_value = request.config_value
    
    db.commit()
    db.refresh(config)
    
    return {"code": 200, "message": "更新成功", "data": config.to_dict(hide_secret=True)}


@router.post("/system/configs")
async def create_system_config(
    config_key: str,
    display_name: str,
    config_value: str = "",
    config_type: str = "text",
    description: str = "",
    category: str = "system",
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """创建系统配置（管理员权限）"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    from models.database import SystemConfig
    
    # 检查是否已存在
    existing = db.query(SystemConfig).filter(SystemConfig.config_key == config_key).first()
    if existing:
        return {"code": 400, "message": "配置键已存在", "data": None}
    
    # 如果是敏感配置，加密存储
    if config_type == 'secret' and config_value:
        config_value = encrypt_password(config_value)
    
    config = SystemConfig(
        config_key=config_key,
        config_value=config_value,
        config_type=config_type,
        display_name=display_name,
        description=description,
        category=category
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    
    return {"code": 200, "message": "创建成功", "data": config.to_dict(hide_secret=True)}


@router.delete("/system/configs/{config_key}")
async def delete_system_config(
    config_key: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """删除系统配置（管理员权限）"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    from models.database import SystemConfig
    
    config = db.query(SystemConfig).filter(SystemConfig.config_key == config_key).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    db.delete(config)
    db.commit()
    return {"code": 200, "message": "删除成功", "data": None}


# ========== 权限管理 API ==========

class PermissionModuleResponse(BaseModel):
    """权限模块响应"""
    code: str
    name: str
    description: Optional[str]
    parent_code: Optional[str]
    icon: Optional[str]
    children: List["PermissionModuleResponse"] = []


class UserPermissionUpdate(BaseModel):
    """用户权限更新"""
    school_ids: Optional[List[int]] = None
    module_permissions: Optional[List[dict]] = None  # [{school_id, module_code, permission_code, granted}]
    template_permissions: Optional[List[dict]] = None  # [{school_id, template_id, can_query, can_export}]


class UserSchoolPermissionCreate(BaseModel):
    """创建用户学校权限"""
    school_id: int
    module_code: str
    permission_code: str
    granted: bool = True


class UserTemplatePermissionCreate(BaseModel):
    """创建用户模板权限"""
    school_id: int
    template_id: int
    can_query: bool = True
    can_export: bool = False


@router.get("/permissions/modules")
async def get_permission_modules(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """获取所有权限模块（树形结构）"""
    from models.database import PermissionModule
    
    modules = db.query(PermissionModule).filter(
        PermissionModule.status == 'active'
    ).order_by(PermissionModule.sort_order).all()
    
    # Build tree structure
    module_dict = {}
    root_modules = []
    
    for m in modules:
        module_dict[m.code] = {
            'code': m.code,
            'name': m.name,
            'description': m.description,
            'parent_code': m.parent_code,
            'icon': m.icon,
            'children': []
        }
    
    for m in modules:
        if m.parent_code and m.parent_code in module_dict:
            module_dict[m.parent_code]['children'].append(module_dict[m.code])
        else:
            root_modules.append(module_dict[m.code])
    
    return {
        "code": 200,
        "message": "获取成功",
        "data": root_modules
    }


@router.get("/permissions/users/{user_id}")
async def get_user_permissions(
    user_id: int,
    school_id: Optional[int] = None,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """获取用户的所有权限"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    from models.database import User, UserSchool, UserSchoolPermission, UserTemplatePermission
    
    # Get user's schools
    schools_query = db.query(UserSchool).filter(UserSchool.user_id == user_id)
    schools = schools_query.all()
    
    # Get user's module permissions
    module_query = db.query(UserSchoolPermission).filter(UserSchoolPermission.user_id == user_id)
    if school_id:
        module_query = module_query.filter(UserSchoolPermission.school_id == school_id)
    module_permissions = module_query.all()
    
    # Get user's template permissions
    template_query = db.query(UserTemplatePermission).filter(UserTemplatePermission.user_id == user_id)
    if school_id:
        template_query = template_query.filter(UserTemplatePermission.school_id == school_id)
    template_permissions = template_query.all()
    
    return {
        "code": 200,
        "message": "获取成功",
        "data": {
            "schools": [s.to_dict() for s in schools],
            "module_permissions": [p.to_dict() for p in module_permissions],
            "template_permissions": [p.to_dict() for p in template_permissions]
        }
    }


@router.post("/permissions/users/{user_id}/schools")
async def set_user_schools(
    user_id: int,
    school_ids: List[int],
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """设置用户授权的学校列表"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    from models.database import UserSchool
    
    # Delete existing
    db.query(UserSchool).filter(UserSchool.user_id == user_id).delete()
    
    # Add new
    for school_id in school_ids:
        perm = UserSchool(
            user_id=user_id,
            school_id=school_id,
            permissions=['query']  # Default permission
        )
        db.add(perm)
    
    db.commit()
    
    return {"code": 200, "message": "设置成功", "data": {"school_count": len(school_ids)}}


@router.post("/permissions/users/{user_id}/modules")
async def set_user_module_permissions(
    user_id: int,
    permissions: List[UserSchoolPermissionCreate],
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """设置用户的模块权限"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    from models.database import UserSchoolPermission
    
    added_count = 0
    for perm in permissions:
        # Check if exists
        existing = db.query(UserSchoolPermission).filter(
            UserSchoolPermission.user_id == user_id,
            UserSchoolPermission.school_id == perm.school_id,
            UserSchoolPermission.module_code == perm.module_code,
            UserSchoolPermission.permission_code == perm.permission_code
        ).first()
        
        if existing:
            existing.granted = perm.granted
        else:
            new_perm = UserSchoolPermission(
                user_id=user_id,
                school_id=perm.school_id,
                module_code=perm.module_code,
                permission_code=perm.permission_code,
                granted=perm.granted
            )
            db.add(new_perm)
            added_count += 1
    
    db.commit()
    
    return {"code": 200, "message": "设置成功", "data": {"added_count": added_count}}


@router.post("/permissions/users/{user_id}/templates")
async def set_user_template_permissions(
    user_id: int,
    permissions: List[UserTemplatePermissionCreate],
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """设置用户的查询模板权限"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    from models.database import UserTemplatePermission
    
    added_count = 0
    for perm in permissions:
        # Check if exists
        existing = db.query(UserTemplatePermission).filter(
            UserTemplatePermission.user_id == user_id,
            UserTemplatePermission.school_id == perm.school_id,
            UserTemplatePermission.template_id == perm.template_id
        ).first()
        
        if existing:
            existing.can_query = perm.can_query
            existing.can_export = perm.can_export
        else:
            new_perm = UserTemplatePermission(
                user_id=user_id,
                school_id=perm.school_id,
                template_id=perm.template_id,
                can_query=perm.can_query,
                can_export=perm.can_export
            )
            db.add(new_perm)
            added_count += 1
    
    db.commit()
    
    return {"code": 200, "message": "设置成功", "data": {"added_count": added_count}}


@router.delete("/permissions/users/{user_id}/modules")
async def clear_user_module_permissions(
    user_id: int,
    school_id: Optional[int] = None,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """清除用户的模块权限"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    from models.database import UserSchoolPermission
    
    query = db.query(UserSchoolPermission).filter(UserSchoolPermission.user_id == user_id)
    if school_id:
        query = query.filter(UserSchoolPermission.school_id == school_id)
    
    count = query.delete()
    db.commit()
    
    return {"code": 200, "message": "清除成功", "data": {"deleted_count": count}}


@router.delete("/permissions/users/{user_id}/templates")
async def clear_user_template_permissions(
    user_id: int,
    school_id: Optional[int] = None,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """清除用户的模板权限"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    from models.database import UserTemplatePermission
    
    query = db.query(UserTemplatePermission).filter(UserTemplatePermission.user_id == user_id)
    if school_id:
        query = query.filter(UserTemplatePermission.school_id == school_id)
    
    count = query.delete()
    db.commit()
    
    return {"code": 200, "message": "清除成功", "data": {"deleted_count": count}}


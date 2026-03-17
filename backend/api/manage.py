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
from core.security import get_current_user, TokenData, encrypt_password, decrypt_password
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
    
    # 如果更新密码，需要加密
    if 'password' in update_data and update_data['password']:
        update_data['password'] = encrypt_password(update_data['password'])
    
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
    school_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """为用户授权学校（管理员权限）"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
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


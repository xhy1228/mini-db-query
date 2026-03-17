# -*- coding: utf-8 -*-
"""
多源数据查询小程序版 - 查询API

Author: 飞书百万（AI助手）
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional, List, Any
from datetime import datetime
from pathlib import Path
import time
import json
import io
import os
import uuid

from models import get_db_session, DatabaseConfig, QueryTemplate
from models.database import School, QueryLog
from services.user_service import UserService, QueryTemplateService, QueryLogService
from core.security import get_current_user, TokenData
from core.config import settings
from db.connector import get_connector
from db.connection_manager import connection_manager


router = APIRouter(tags=["查询"])


# ========== 请求/响应模型 ==========

class SmartQueryRequest(BaseModel):
    """智能查询请求"""
    school_id: int = Field(..., description="学校ID")
    template_id: int = Field(..., description="查询模板ID")
    conditions: List[dict] = Field(default_factory=list, description="查询条件")
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    limit: Optional[int] = 100


class SqlQueryRequest(BaseModel):
    """SQL查询请求"""
    school_id: int
    sql: str


class ExportRequest(BaseModel):
    """导出请求"""
    school_id: int
    template_id: Optional[int] = None
    sql: Optional[str] = None
    conditions: List[dict] = Field(default_factory=list)
    start_time: Optional[str] = None
    end_time: Optional[str] = None


# ========== 辅助函数 ==========

def check_user_school_permission(db: Session, user_id: int, school_id: int) -> bool:
    """检查用户是否有学校权限"""
    # 超级管理员有所有权限
    user = UserService.get_by_id(db, user_id)
    if user and user.role == 'admin':
        return True
    
    # 检查用户学校权限
    schools = UserService.get_user_schools(db, user_id)
    for school in schools:
        if school['id'] == school_id:
            return True
    return False


def generate_sql_from_template(template: QueryTemplate, conditions: List[dict],
                               start_time: str = None, end_time: str = None) -> str:
    """从模板生成SQL"""
    sql = template.sql_template
    
    # 处理条件
    where_clauses = []
    for cond in conditions:
        field = cond.get('field')
        operator = cond.get('operator', '=')
        value = cond.get('value', '')
        
        if not value:
            continue
        
        if operator.upper() == 'LIKE':
            where_clauses.append(f"{field} LIKE '%{value}%'")
        else:
            where_clauses.append(f"{field} {operator} '{value}'")
    
    # 添加时间条件
    if template.time_field:
        if start_time:
            where_clauses.append(f"{template.time_field} >= '{start_time}'")
        if end_time:
            where_clauses.append(f"{template.time_field} <= '{end_time}'")
    
    # 组合WHERE
    if where_clauses:
        where_str = " AND ".join(where_clauses)
        if "WHERE" in sql.upper():
            sql = sql + " AND " + where_str
        else:
            sql = sql + " WHERE " + where_str
    
    # 添加LIMIT
    if template.default_limit:
        sql = sql + f" LIMIT {template.default_limit}"
    
    return sql


# ========== 小程序端API ==========

@router.get("/user/schools")
async def get_user_schools(current_user: TokenData = Depends(get_current_user),
                          db: Session = Depends(get_db_session)):
    """
    获取用户授权的学校列表
    
    用户登录后获取自己有权访问的学校
    """
    # 超级管理员可以看到所有学校
    user = UserService.get_by_id(db, int(current_user.user_id))
    if user and user.role == 'admin':
        from models.database import School
        schools = db.query(School).filter(School.status == 'active').all()
        return {
            "code": 200,
            "message": "获取成功",
            "data": [s.to_dict() for s in schools]
        }
    
    # 普通用户获取授权学校
    schools = UserService.get_user_schools(db, int(current_user.user_id))
    
    return {
        "code": 200,
        "message": "获取成功",
        "data": schools
    }


@router.get("/user/categories")
async def get_categories(school_id: int,
                        current_user: TokenData = Depends(get_current_user),
                        db: Session = Depends(get_db_session)):
    """
    获取学校的业务大类列表
    
    - **school_id**: 学校ID
    """
    # 检查权限
    if not check_user_school_permission(db, int(current_user.user_id), school_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问该学校"
        )
    
    categories = QueryTemplateService.get_categories(db, school_id)
    
    return {
        "code": 200,
        "message": "获取成功",
        "data": categories
    }


@router.get("/user/templates")
async def get_templates(school_id: int, category: str = None,
                       current_user: TokenData = Depends(get_current_user),
                       db: Session = Depends(get_db_session)):
    """
    获取查询模板列表
    
    - **school_id**: 学校ID
    - **category**: 业务大类（可选）
    """
    # 检查权限
    if not check_user_school_permission(db, int(current_user.user_id), school_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问该学校"
        )
    
    if category:
        templates = QueryTemplateService.get_by_category(db, school_id, category)
    else:
        templates = QueryTemplateService.get_by_school(db, school_id)
    
    return {
        "code": 200,
        "message": "获取成功",
        "data": [t.to_dict() for t in templates]
    }


@router.post("/user/query")
async def smart_query(request: SmartQueryRequest,
                     current_user: TokenData = Depends(get_current_user),
                     db: Session = Depends(get_db_session)):
    """
    智能查询
    
    - **school_id**: 学校ID
    - **template_id**: 查询模板ID
    - **conditions**: 查询条件
    - **start_time**: 开始时间
    - **end_time**: 结束时间
    - **limit**: 结果条数限制
    """
    user_id = int(current_user.user_id)
    
    # 检查权限
    if not check_user_school_permission(db, user_id, request.school_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问该学校"
        )
    
    # 获取模板
    template = db.query(QueryTemplate).filter(
        QueryTemplate.id == request.template_id,
        QueryTemplate.school_id == request.school_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="查询模板不存在"
        )
    
    # 获取数据库配置
    # 从模板获取数据库配置ID或根据学校查找
    # 这里简化处理，假设模板关联了数据库配置
    from models.database import DatabaseConfig
    db_config = db.query(DatabaseConfig).filter(
        DatabaseConfig.school_id == request.school_id,
        DatabaseConfig.status == 'active'
    ).first()
    
    if not db_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="该学校未配置数据库"
        )
    
    # 生成SQL
    sql = generate_sql_from_template(
        template,
        request.conditions,
        request.start_time,
        request.end_time
    )
    
    # 执行查询
    start_time_ms = int(time.time() * 1000)
    try:
        # 构建数据库连接配置
        config = {
            'db_type': db_config.db_type,
            'db_name': db_config.db_name,
        }
        
        # 非SQLite数据库需要更多配置
        if db_config.db_type != 'SQLite':
            from core.security import decrypt_password
            plain_password = decrypt_password(db_config.password)
            config.update({
                'host': db_config.host,
                'port': db_config.port,
                'username': db_config.username,
                'password': plain_password,
                'service_name': db_config.service_name
            })
        
        connector = get_connector(config['db_type'], config)
        if not connector or not connector.connect():
            raise Exception("数据库连接失败")
        
        from db.query_executor import QueryExecutor
        executor = QueryExecutor(connector)
        result = executor.execute_query(sql)
        connector.close()
        
        query_time = int(time.time() * 1000) - start_time_ms
        
        # 记录日志
        QueryLogService.create_log(
            db, user_id, request.school_id, template.id,
            template.name, {"conditions": request.conditions},
            sql, len(result), query_time, "success"
        )
        
        # 转换为字典
        rows = [dict(row) for row in result] if result else []
        
        return {
            "code": 200,
            "message": "查询成功",
            "data": {
                "rows": rows,
                "count": len(rows),
                "query_time": query_time,
                "sql": sql
            }
        }
        
    except Exception as e:
        query_time = int(time.time() * 1000) - start_time_ms
        
        # 记录错误日志
        QueryLogService.create_log(
            db, user_id, request.school_id, template.id,
            template.name, {"conditions": request.conditions},
            sql, 0, query_time, "failed", str(e)
        )
        
        return {
            "code": 500,
            "message": f"查询失败: {str(e)}",
            "data": None
        }


@router.get("/user/history")
async def get_query_history(
    skip: int = 0, 
    limit: int = 30,
    school_id: int = None,
    status: str = None,
    start_date: str = None,
    end_date: str = None,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    获取查询历史（支持分页和筛选）
    
    - **skip**: 跳过条数
    - **limit**: 返回条数
    - **school_id**: 学校ID筛选（可选）
    - **status**: 状态筛选（success/failed）
    - **start_date**: 开始日期筛选（YYYY-MM-DD）
    - **end_date**: 结束日期筛选（YYYY-MM-DD）
    """
    user_id = int(current_user.user_id)
    
    # 管理员可以查看所有历史，普通用户只能看自己的
    query = db.query(QueryLog)
    if current_user.role != 'admin':
        query = query.filter(QueryLog.user_id == user_id)
    else:
        if user_id:
            query = query.filter(QueryLog.user_id == user_id)
    
    # 筛选条件
    if school_id:
        query = query.filter(QueryLog.school_id == school_id)
    if status:
        query = query.filter(QueryLog.status == status)
    if start_date:
        query = query.filter(QueryLog.created_at >= start_date)
    if end_date:
        query = query.filter(QueryLog.created_at <= end_date + " 23:59:59")
    
    # 分页
    total = query.count()
    history = query.order_by(QueryLog.created_at.desc()).offset(skip).limit(limit).all()
    
    # 获取学校名称
    result = []
    for h in history:
        item = h.to_dict()
        school = db.query(School).filter(School.id == h.school_id).first()
        item['school_name'] = school.name if school else None
        result.append(item)
    
    return {
        "code": 200,
        "message": "获取成功",
        "data": result,
        "total": total
    }


@router.get("/user/history/{log_id}")
async def get_history_detail(
    log_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    获取历史记录详情
    
    - **log_id**: 历史记录ID
    """
    user_id = int(current_user.user_id)
    
    log = db.query(QueryLog).filter(QueryLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    # 权限检查
    if current_user.role != 'admin' and log.user_id != user_id:
        raise HTTPException(status_code=403, detail="无权限查看")
    
    # 获取学校名称
    result = log.to_dict()
    school = db.query(School).filter(School.id == log.school_id).first()
    result['school_name'] = school.name if school else None
    
    # 获取模板名称
    if log.template_id:
        template = db.query(QueryTemplate).filter(QueryTemplate.id == log.template_id).first()
        result['template_name'] = template.name if template else None
    
    return {
        "code": 200,
        "message": "获取成功",
        "data": result
    }


@router.delete("/user/history/{log_id}")
async def delete_history(
    log_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    删除历史记录
    
    - **log_id**: 历史记录ID
    """
    user_id = int(current_user.user_id)
    
    log = db.query(QueryLog).filter(QueryLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    # 权限检查
    if current_user.role != 'admin' and log.user_id != user_id:
        raise HTTPException(status_code=403, detail="无权限删除")
    
    db.delete(log)
    db.commit()
    
    return {
        "code": 200,
        "message": "删除成功",
        "data": None
    }


@router.post("/user/sql")
async def direct_sql_query(
    request: SqlQueryRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    直接执行SQL查询
    
    - **school_id**: 学校ID
    - **sql**: SQL语句（仅支持SELECT）
    """
    user_id = int(current_user.user_id)
    
    # 权限检查 - 普通用户需要学校权限
    if not check_user_school_permission(db, user_id, request.school_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问该学校"
        )
    
    # 检查是否是管理员（管理员可以执行SQL）
    user = UserService.get_by_id(db, user_id)
    if user.role != 'admin':
        # 非管理员只能执行查询，且需要配置允许
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="普通用户无直接SQL执行权限，请使用模板查询"
        )
    
    # SQL安全检查
    sql = request.sql.strip().upper()
    if not sql.startswith('SELECT'):
        return {
            "code": 400,
            "message": "仅支持SELECT查询",
            "data": None
        }
    
    # 禁止危险操作
    dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'TRUNCATE', 'ALTER', 'CREATE']
    for keyword in dangerous_keywords:
        if keyword in sql:
            return {
                "code": 400,
                "message": f"不允许执行包含 {keyword} 的SQL",
                "data": None
            }
    
    # 获取数据库配置
    db_config = db.query(DatabaseConfig).filter(
        DatabaseConfig.school_id == request.school_id,
        DatabaseConfig.status == 'active'
    ).first()
    
    if not db_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="该学校未配置数据库"
        )
    
    # 执行查询
    start_time_ms = int(time.time() * 1000)
    try:
        config = {
            'db_type': db_config.db_type,
            'db_name': db_config.db_name,
        }
        
        if db_config.db_type != 'SQLite':
            from core.security import decrypt_password
            plain_password = decrypt_password(db_config.password)
            config.update({
                'host': db_config.host,
                'port': db_config.port,
                'username': db_config.username,
                'password': plain_password,
                'service_name': db_config.service_name
            })
        
        connector = get_connector(config['db_type'], config)
        if not connector or not connector.connect():
            raise Exception("数据库连接失败")
        
        from db.query_executor import QueryExecutor
        executor = QueryExecutor(connector)
        result = executor.execute_query(request.sql)
        connector.close()
        
        query_time = int(time.time() * 1000) - start_time_ms
        
        # 记录日志
        QueryLogService.create_log(
            db, user_id, request.school_id, None,
            "SQL查询", {"type": "direct_sql"},
            request.sql, len(result), query_time, "success"
        )
        
        # 转换为字典
        rows = [dict(row) for row in result] if result else []
        
        return {
            "code": 200,
            "message": "查询成功",
            "data": {
                "rows": rows,
                "count": len(rows),
                "query_time": query_time,
                "sql": request.sql
            }
        }
        
    except Exception as e:
        query_time = int(time.time() * 1000) - start_time_ms
        
        # 记录错误日志
        QueryLogService.create_log(
            db, user_id, request.school_id, None,
            "SQL查询", {"type": "direct_sql"},
            request.sql, 0, query_time, "failed", str(e)
        )
        
        return {
            "code": 500,
            "message": f"查询失败: {str(e)}",
            "data": None
        }


@router.post("/user/export")
async def export_query_result(
    request: ExportRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    导出查询结果为Excel
    
    - **school_id**: 学校ID
    - **template_id**: 查询模板ID（可选）
    - **sql**: SQL语句（可选，直接SQL查询时使用）
    - **conditions**: 查询条件
    - **start_time**: 开始时间
    - **end_time**: 结束时间
    """
    user_id = int(current_user.user_id)
    
    # 权限检查
    if not check_user_school_permission(db, user_id, request.school_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问该学校"
        )
    
    # 获取SQL语句
    sql = request.sql
    query_name = "数据导出"
    
    if request.template_id:
        # 从模板生成SQL
        template = db.query(QueryTemplate).filter(
            QueryTemplate.id == request.template_id,
            QueryTemplate.school_id == request.school_id
        ).first()
        
        if not template:
            raise HTTPException(status_code=404, detail="查询模板不存在")
        
        sql = generate_sql_from_template(
            template,
            request.conditions,
            request.start_time,
            request.end_time
        )
        query_name = template.name
    
    if not sql:
        return {
            "code": 400,
            "message": "请提供SQL语句或模板ID",
            "data": None
        }
    
    # 获取数据库配置
    db_config = db.query(DatabaseConfig).filter(
        DatabaseConfig.school_id == request.school_id,
        DatabaseConfig.status == 'active'
    ).first()
    
    if not db_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="该学校未配置数据库"
        )
    
    # 执行查询
    start_time_ms = int(time.time() * 1000)
    try:
        config = {
            'db_type': db_config.db_type,
            'db_name': db_config.db_name,
        }
        
        if db_config.db_type != 'SQLite':
            from core.security import decrypt_password
            plain_password = decrypt_password(db_config.password)
            config.update({
                'host': db_config.host,
                'port': db_config.port,
                'username': db_config.username,
                'password': plain_password,
                'service_name': db_config.service_name
            })
        
        connector = get_connector(config['db_type'], config)
        if not connector or not connector.connect():
            raise Exception("数据库连接失败")
        
        from db.query_executor import QueryExecutor
        executor = QueryExecutor(connector)
        
        # 限制导出数量
        limit_sql = sql
        if "LIMIT" not in sql.upper():
            limit_sql = sql + " LIMIT 10000"
        
        result = executor.execute_query(limit_sql)
        connector.close()
        
        query_time = int(time.time() * 1000) - start_time_ms
        
        if not result:
            return {
                "code": 400,
                "message": "查询结果为空",
                "data": None
            }
        
        # 转换为字典列表
        rows = [dict(row) for row in result]
        
        # 生成Excel
        try:
            from openpyxl import Workbook
            from openpyxl.utils import get_column_letter
            
            wb = Workbook()
            ws = wb.active
            ws.title = "查询结果"
            
            # 写入表头
            if rows:
                headers = list(rows[0].keys())
                for col_idx, header in enumerate(headers, 1):
                    ws.cell(row=1, column=col_idx, value=header)
                
                # 写入数据
                for row_idx, row_data in enumerate(rows, 2):
                    for col_idx, header in enumerate(headers, 1):
                        value = row_data.get(header, '')
                        # 处理日期等特殊类型
                        if hasattr(value, 'isoformat'):
                            value = value.isoformat()
                        ws.cell(row=row_idx, column=col_idx, value=value)
                
                # 自动调整列宽
                for col_idx, header in enumerate(headers, 1):
                    max_length = len(str(header))
                    for row in ws.iter_rows(min_row=2, max_row=len(rows)+1, min_col=col_idx, max_col=col_idx):
                        for cell in row:
                            if cell.value:
                                max_length = max(max_length, len(str(cell.value)))
                    ws.column_dimensions[get_column_letter(col_idx)].width = min(max_length + 2, 50)
            
            # 保存文件
            export_dir = Path("./exports")
            export_dir.mkdir(exist_ok=True)
            
            filename = f"export_{uuid.uuid4().hex[:8]}_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
            filepath = export_dir / filename
            
            wb.save(filepath)
            
            # 记录日志
            QueryLogService.create_log(
                db, user_id, request.school_id, request.template_id,
                query_name, {"type": "export", "filename": filename},
                sql, len(rows), query_time, "success"
            )
            
            return {
                "code": 200,
                "message": "导出成功",
                "data": {
                    "filename": filename,
                    "url": f"/exports/{filename}",
                    "count": len(rows),
                    "query_time": query_time
                }
            }
            
        except ImportError:
            return {
                "code": 500,
                "message": "Excel导出库未安装",
                "data": None
            }
        
    except Exception as e:
        query_time = int(time.time() * 1000) - start_time_ms
        
        # 记录错误日志
        QueryLogService.create_log(
            db, user_id, request.school_id, request.template_id,
            query_name, {"type": "export"},
            sql, 0, query_time, "failed", str(e)
        )
        
        return {
            "code": 500,
            "message": f"导出失败: {str(e)}",
            "data": None
        }


# ========== 管理平台API ==========

@router.get("/manage/schools")
async def list_schools(skip: int = 0, limit: int = 100,
                      current_user: TokenData = Depends(get_current_user),
                      db: Session = Depends(get_db_session)):
    """获取学校列表"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    from models.database import School
    schools = db.query(School).offset(skip).limit(limit).all()
    
    return {
        "code": 200,
        "message": "获取成功",
        "data": [s.to_dict() for s in schools]
    }


@router.post("/manage/schools")
async def create_school(name: str, code: str, description: str = None,
                       current_user: TokenData = Depends(get_current_user),
                       db: Session = Depends(get_db_session)):
    """创建学校"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    from models.database import School
    school = School(name=name, code=code, description=description)
    db.add(school)
    db.commit()
    db.refresh(school)
    
    return {
        "code": 200,
        "message": "创建成功",
        "data": school.to_dict()
    }


@router.get("/manage/databases")
async def list_databases(school_id: int = None,
                       current_user: TokenData = Depends(get_current_user),
                       db: Session = Depends(get_db_session)):
    """获取数据库配置列表"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    query = db.query(DatabaseConfig)
    if school_id:
        query = query.filter(DatabaseConfig.school_id == school_id)
    
    databases = query.all()
    
    return {
        "code": 200,
        "message": "获取成功",
        "data": [d.to_dict() for d in databases]
    }


@router.post("/manage/databases")
async def create_database(school_id: int, name: str, db_type: str,
                         host: str, port: int, username: str, password: str,
                         database: str = None, service_name: str = None,
                         description: str = None,
                         current_user: TokenData = Depends(get_current_user),
                         db: Session = Depends(get_db_session)):
    """创建数据库配置"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    from core.security import encrypt_password
    
    config = DatabaseConfig(
        school_id=school_id,
        name=name,
        db_type=db_type,
        host=host,
        port=port,
        username=username,
        password=encrypt_password(password),  # 使用可逆加密
        database=database,
        service_name=service_name,
        description=description
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    
    return {
        "code": 200,
        "message": "创建成功",
        "data": config.to_dict()
    }


@router.get("/manage/templates")
async def list_templates(school_id: int = None, category: str = None,
                        current_user: TokenData = Depends(get_current_user),
                        db: Session = Depends(get_db_session)):
    """获取查询模板列表"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    query = db.query(QueryTemplate)
    if school_id:
        query = query.filter(QueryTemplate.school_id == school_id)
    if category:
        query = query.filter(QueryTemplate.category == category)
    
    templates = query.all()
    
    return {
        "code": 200,
        "message": "获取成功",
        "data": [t.to_dict() for t in templates]
    }


@router.post("/manage/templates")
async def create_template(school_id: int, category: str, name: str,
                        sql_template: str, fields: list = None,
                        category_name: str = None, category_icon: str = None,
                        time_field: str = None, default_limit: int = 500,
                        current_user: TokenData = Depends(get_current_user),
                        db: Session = Depends(get_db_session)):
    """创建查询模板"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    template = QueryTemplate(
        school_id=school_id,
        category=category,
        category_name=category_name,
        category_icon=category_icon,
        name=name,
        sql_template=sql_template,
        fields=fields,
        time_field=time_field,
        default_limit=default_limit
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return {
        "code": 200,
        "message": "创建成功",
        "data": template.to_dict()
    }


@router.post("/manage/databases/{db_id}/test")
async def test_database(db_id: int,
                       current_user: TokenData = Depends(get_current_user),
                       db: Session = Depends(get_db_session)):
    """测试数据库连接"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    from core.security import decrypt_password
    
    config = db.query(DatabaseConfig).filter(DatabaseConfig.id == db_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    try:
        # 解密密码
        plain_password = decrypt_password(config.password)
        
        connector = get_connector(config.db_type, {
            'host': config.host,
            'port': config.port,
            'username': config.username,
            'password': plain_password,
            'db_name': config.db_name,
            'service_name': config.service_name
        })
        
        if connector and connector.connect():
            connector.close()
            return {
                "code": 200,
                "message": "连接成功",
                "data": None
            }
        else:
            return {
                "code": 400,
                "message": "连接失败",
                "data": None
            }
    except Exception as e:
        return {
            "code": 500,
            "message": f"连接失败: {str(e)}",
            "data": None
        }


# ========== 学校管理API扩展 ==========

class SchoolUpdateRequest(BaseModel):
    """学校更新请求"""
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


@router.put("/manage/schools/{school_id}")
async def update_school(
    school_id: int,
    request: SchoolUpdateRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """更新学校信息"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="学校不存在")
    
    update_data = request.dict(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(school, key, value)
    
    db.commit()
    db.refresh(school)
    
    return {
        "code": 200,
        "message": "更新成功",
        "data": school.to_dict()
    }


@router.delete("/manage/schools/{school_id}")
async def delete_school(
    school_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """删除学校"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="学校不存在")
    
    db.delete(school)
    db.commit()
    
    return {
        "code": 200,
        "message": "删除成功",
        "data": None
    }


# ========== 数据库配置管理API扩展 ==========

class DatabaseUpdateRequest(BaseModel):
    """数据库配置更新请求"""
    school_id: Optional[int] = None
    name: Optional[str] = None
    db_type: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None
    service_name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


@router.put("/manage/databases/{db_id}")
async def update_database(
    db_id: int,
    request: DatabaseUpdateRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """更新数据库配置"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    config = db.query(DatabaseConfig).filter(DatabaseConfig.id == db_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    update_data = request.dict(exclude_unset=True)
    
    # 处理密码加密
    if 'password' in update_data and update_data['password']:
        from core.security import encrypt_password
        update_data['password'] = encrypt_password(update_data['password'])
    
    for key, value in update_data.items():
        if value is not None:
            setattr(config, key, value)
    
    db.commit()
    db.refresh(config)
    
    return {
        "code": 200,
        "message": "更新成功",
        "data": config.to_dict()
    }


@router.delete("/manage/databases/{db_id}")
async def delete_database(
    db_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """删除数据库配置"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    config = db.query(DatabaseConfig).filter(DatabaseConfig.id == db_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    db.delete(config)
    db.commit()
    
    return {
        "code": 200,
        "message": "删除成功",
        "data": None
    }


# ========== 查询模板管理API扩展 ==========

class TemplateUpdateRequest(BaseModel):
    """查询模板更新请求"""
    school_id: Optional[int] = None
    category: Optional[str] = None
    category_name: Optional[str] = None
    category_icon: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    sql_template: Optional[str] = None
    fields: Optional[list] = None
    time_field: Optional[str] = None
    default_limit: Optional[int] = None
    status: Optional[str] = None


@router.put("/manage/templates/{template_id}")
async def update_template(
    template_id: int,
    request: TemplateUpdateRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """更新查询模板"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    template = db.query(QueryTemplate).filter(QueryTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    update_data = request.dict(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(template, key, value)
    
    db.commit()
    db.refresh(template)
    
    return {
        "code": 200,
        "message": "更新成功",
        "data": template.to_dict()
    }


@router.delete("/manage/templates/{template_id}")
async def delete_template(
    template_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """删除查询模板"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="权限不足")
    
    template = db.query(QueryTemplate).filter(QueryTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    db.delete(template)
    db.commit()
    
    return {
        "code": 200,
        "message": "删除成功",
        "data": None
    }

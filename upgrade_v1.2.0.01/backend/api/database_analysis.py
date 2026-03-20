# -*- coding: utf-8 -*-
"""
数据库分析和模板生成 API - v1.2.0

功能：
1. 获取数据库表列表
2. 分析表结构
3. 自动生成查询模板
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from models import get_db_session
from models.database import DatabaseConfig, QueryTemplate, QueryField, User
from api.auth import get_current_user
from db.connector import get_connector
from db.query_executor import QueryExecutor

router = APIRouter(tags=["数据库分析"], prefix="/manage")


# ============ Pydantic Models ============

class TableAnalysisRequest(BaseModel):
    """分析表请求"""
    table_name: str
    category: str
    category_name: Optional[str] = None
    category_icon: Optional[str] = None


class TemplateGenerateRequest(BaseModel):
    """生成模板请求"""
    table_name: str
    template_name: str
    category: str
    category_name: Optional[str] = None
    category_icon: Optional[str] = None
    time_field: Optional[str] = None
    selected_fields: Optional[List[str]] = None
    generate_all_fields: Optional[bool] = True


# ============ Helper Functions ============

def get_db_connector(db_config: DatabaseConfig):
    """获取数据库连接器"""
    config = db_config.to_dict(include_password=True)
    connector = get_connector(db_config.db_type, config)
    connector.connect()
    return connector


def execute_sql(connector, sql: str):
    """执行SQL查询"""
    executor = QueryExecutor(connector)
    return executor.execute_query(sql)


# ============ API Routes ============

@router.post("/databases/{db_id}/tables", summary="获取数据库表列表")
async def get_database_tables(
    db_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """获取指定数据库连接的所有表"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    db_config = db.query(DatabaseConfig).filter(DatabaseConfig.id == db_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="数据库配置不存在")
    
    connector = None
    try:
        connector = get_db_connector(db_config)
        
        if db_config.db_type == 'MySQL':
            sql = f"""
                SELECT 
                    TABLE_NAME as name,
                    TABLE_COMMENT as comment,
                    TABLE_ROWS as rows
                FROM information_schema.TABLES 
                WHERE TABLE_SCHEMA = '{db_config.db_name}'
                ORDER BY TABLE_NAME
            """
        elif db_config.db_type == 'Oracle':
            sql = """
                SELECT 
                    TABLE_NAME as name,
                    COMMENTS as comment,
                    NUM_ROWS as rows
                FROM USER_TABLES t
                LEFT JOIN USER_TAB_COMMENTS c ON t.TABLE_NAME = c.TABLE_NAME
                ORDER BY TABLE_NAME
            """
        elif db_config.db_type == 'SQLServer':
            sql = """
                SELECT 
                    t.name as name,
                    ep.value as comment,
                    p.rows as rows
                FROM sys.tables t
                LEFT JOIN sys.extended_properties ep ON ep.major_id = t.object_id AND ep.minor_id = 0
                LEFT JOIN sys.partitions p ON p.object_id = t.object_id AND p.index_id IN (0, 1)
                ORDER BY t.name
            """
        else:
            sql = """
                SELECT name, '' as comment, 0 as rows
                FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """
        
        result = execute_sql(connector, sql)
        
        tables = []
        for row in result or []:
            tables.append({
                'name': row.get('name', ''),
                'comment': row.get('comment', ''),
                'rows': row.get('rows', 0)
            })
        
        return {"code": 200, "data": tables}
        
    except Exception as e:
        return {"code": 500, "message": f"获取表列表失败: {str(e)}"}
    finally:
        if connector:
            connector.close()


@router.post("/databases/{db_id}/tables/{table_name}/columns", summary="获取表结构")
async def get_table_columns(
    db_id: int,
    table_name: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """获取指定表的列信息"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    db_config = db.query(DatabaseConfig).filter(DatabaseConfig.id == db_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="数据库配置不存在")
    
    connector = None
    try:
        connector = get_db_connector(db_config)
        
        if db_config.db_type == 'MySQL':
            sql = f"""
                SELECT 
                    COLUMN_NAME as name,
                    COLUMN_TYPE as type,
                    IS_NULLABLE as nullable,
                    COLUMN_DEFAULT as default_value,
                    COLUMN_COMMENT as comment,
                    COLUMN_KEY as key_type,
                    DATA_TYPE as data_type
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = '{db_config.db_name}' 
                  AND TABLE_NAME = '{table_name}'
                ORDER BY ORDINAL_POSITION
            """
            result = execute_sql(connector, sql)
            
            columns = []
            for row in result or []:
                data_type = row.get('data_type', '').lower()
                is_time = any(t in data_type for t in ['date', 'time', 'timestamp', 'datetime'])
                
                columns.append({
                    'name': row.get('name', ''),
                    'type': row.get('type', ''),
                    'nullable': row.get('nullable', 'YES') == 'YES',
                    'default': row.get('default_value'),
                    'comment': row.get('comment', ''),
                    'is_primary': row.get('key_type') == 'PRI',
                    'is_time_field': is_time
                })
        
        elif db_config.db_type == 'Oracle':
            sql = f"""
                SELECT 
                    c.COLUMN_NAME as name,
                    c.DATA_TYPE || 
                        CASE WHEN c.DATA_LENGTH IS NOT NULL THEN '(' || c.DATA_LENGTH || ')' ELSE '' END as type,
                    c.NULLABLE as nullable,
                    c.DATA_DEFAULT as default_value,
                    cc.COMMENTS as comment,
                    CASE WHEN pk.COLUMN_NAME IS NOT NULL THEN 1 ELSE 0 END as is_primary
                FROM USER_TAB_COLUMNS c
                LEFT JOIN USER_COL_COMMENTS cc ON c.TABLE_NAME = cc.TABLE_NAME AND c.COLUMN_NAME = cc.COLUMN_NAME
                LEFT JOIN (
                    SELECT cols.TABLE_NAME, cols.COLUMN_NAME
                    FROM USER_CONSTRAINTS cons
                    JOIN USER_CONS_COLUMNS cols ON cons.CONSTRAINT_NAME = cols.CONSTRAINT_NAME
                    WHERE cons.CONSTRAINT_TYPE = 'P'
                ) pk ON c.TABLE_NAME = pk.TABLE_NAME AND c.COLUMN_NAME = pk.COLUMN_NAME
                WHERE c.TABLE_NAME = UPPER('{table_name}')
                ORDER BY c.COLUMN_ID
            """
            result = execute_sql(connector, sql)
            
            columns = []
            for row in result or []:
                data_type = str(row.get('type', '')).lower()
                is_time = any(t in data_type for t in ['date', 'time', 'timestamp'])
                
                columns.append({
                    'name': row.get('name', ''),
                    'type': row.get('type', ''),
                    'nullable': row.get('nullable', 'Y') == 'Y',
                    'default': row.get('default_value'),
                    'comment': row.get('comment', ''),
                    'is_primary': bool(row.get('is_primary')),
                    'is_time_field': is_time
                })
        
        else:
            # SQLServer / SQLite
            sql = f"SELECT * FROM {table_name} WHERE 1=0"
            result = execute_sql(connector, sql)
            
            # 获取列名（从查询结果中推断）
            columns = []
            if result is not None:
                # 对于空结果，尝试获取列信息
                pass
            
            # 简化处理：使用 PRAGMA 获取 SQLite 表结构
            if db_config.db_type == 'SQLite':
                pragma_sql = f"PRAGMA table_info({table_name})"
                pragma_result = execute_sql(connector, pragma_sql)
                for col in pragma_result or []:
                    col_name = col.get('name', '')
                    col_type = col.get('type', 'text')
                    columns.append({
                        'name': col_name,
                        'type': col_type,
                        'nullable': not col.get('notnull', 0),
                        'default': col.get('dflt_value'),
                        'comment': '',
                        'is_primary': bool(col.get('pk', 0)),
                        'is_time_field': any(t in col_type.lower() for t in ['date', 'time'])
                    })
        
        return {"code": 200, "data": columns}
        
    except Exception as e:
        return {"code": 500, "message": f"获取表结构失败: {str(e)}"}
    finally:
        if connector:
            connector.close()


@router.post("/databases/{db_id}/generate-template", summary="生成查询模板")
async def generate_query_template(
    db_id: int,
    request: TemplateGenerateRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """根据表结构自动生成查询模板"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    db_config = db.query(DatabaseConfig).filter(DatabaseConfig.id == db_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="数据库配置不存在")
    
    try:
        # 获取表结构
        columns_result = await get_table_columns(db_id, request.table_name, db, current_user)
        
        if columns_result['code'] != 200:
            return columns_result
        
        columns = columns_result['data']
        
        # 生成 SQL 模板
        sql_template = f"SELECT * FROM {request.table_name} WHERE 1=1"
        
        # 确定要生成查询条件的字段
        if request.generate_all_fields or not request.selected_fields:
            query_columns = columns[:10]
        else:
            query_columns = [c for c in columns if c['name'] in request.selected_fields]
        
        # 生成查询字段配置
        query_fields = []
        for col in query_columns:
            field_type = 'text'
            operator = '='
            
            col_type = col['type'].lower()
            if 'int' in col_type or 'number' in col_type or 'decimal' in col_type:
                field_type = 'number'
            elif 'date' in col_type or 'time' in col_type:
                field_type = 'date'
                operator = '>='
            elif 'name' in col['name'].lower() or '姓名' in col.get('comment', ''):
                operator = 'LIKE'
            
            query_fields.append({
                'field_key': col['name'],
                'field_label': col.get('comment') or col['name'],
                'field_type': field_type,
                'db_column': col['name'],
                'operator': operator,
                'required': False,
                'sort_order': len(query_fields) + 1,
                'placeholder': f"请输入{col.get('comment') or col['name']}"
            })
        
        # 创建模板
        template = QueryTemplate(
            category=request.category,
            category_name=request.category_name or request.category,
            category_icon=request.category_icon,
            name=request.template_name,
            description=f"自动生成：{request.table_name} 表查询",
            sql_template=sql_template,
            time_field=request.time_field,
            default_limit=500,
            supported_db_types=[db_config.db_type],
            status='active'
        )
        db.add(template)
        db.flush()
        
        # 创建查询字段
        for field_data in query_fields:
            field = QueryField(
                template_id=template.id,
                field_key=field_data['field_key'],
                field_label=field_data['field_label'],
                field_type=field_data['field_type'],
                db_column=field_data['db_column'],
                operator=field_data['operator'],
                required=1 if field_data['required'] else 0,
                sort_order=field_data['sort_order'],
                placeholder=field_data['placeholder']
            )
            db.add(field)
        
        db.commit()
        db.refresh(template)
        
        return {
            "code": 200,
            "message": "模板生成成功",
            "data": {
                "template_id": template.id,
                "template_name": template.name,
                "sql_template": sql_template,
                "fields": query_fields
            }
        }
        
    except Exception as e:
        db.rollback()
        return {"code": 500, "message": f"生成模板失败: {str(e)}"}


@router.post("/databases/{db_id}/preview-data", summary="预览表数据")
async def preview_table_data(
    db_id: int,
    table_name: str,
    limit: int = 10,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """预览表数据（前N条）"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    db_config = db.query(DatabaseConfig).filter(DatabaseConfig.id == db_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="数据库配置不存在")
    
    connector = None
    try:
        connector = get_db_connector(db_config)
        
        if db_config.db_type == 'MySQL':
            sql = f"SELECT * FROM {table_name} LIMIT {limit}"
        elif db_config.db_type == 'Oracle':
            sql = f"SELECT * FROM {table_name} WHERE ROWNUM <= {limit}"
        elif db_config.db_type == 'SQLServer':
            sql = f"SELECT TOP {limit} * FROM {table_name}"
        else:
            sql = f"SELECT * FROM {table_name} LIMIT {limit}"
        
        result = execute_sql(connector, sql)
        
        return {
            "code": 200,
            "data": {
                "columns": list(result[0].keys()) if result else [],
                "rows": result or []
            }
        }
        
    except Exception as e:
        return {"code": 500, "message": f"预览数据失败: {str(e)}"}
    finally:
        if connector:
            connector.close()

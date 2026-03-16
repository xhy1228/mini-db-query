# -*- coding: utf-8 -*-
"""
多源数据查询小程序版 - 查询API
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

from core.security import get_current_user
from utils.response import success_response, error_response, paginate_response
from db.connector import get_connector, check_dependencies
from db.connection_manager import connection_manager
from db.query_template import get_template_manager
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["查询"])


class ExecuteQueryRequest(BaseModel):
    """执行查询请求"""
    config_name: str
    sql: str


class SmartQueryRequest(BaseModel):
    """智能查询请求"""
    config_name: str
    category: str
    query_id: str
    conditions: List[Dict[str, Any]]  # [{field, operator, value, logic}, ...]
    start_time: Optional[str] = None
    end_time: Optional[str] = None


class TestConnectionRequest(BaseModel):
    """测试连接请求"""
    config_name: str


# ==================== 配置管理 ====================

@router.get("/configs")
async def get_configs(current_user = Depends(get_current_user)):
    """
    获取数据库配置列表
    
    Returns:
        配置列表
    """
    try:
        import yaml
        from pathlib import Path
        
        config_file = Path("./config/databases.yaml")
        if not config_file.exists():
            return success_response([])
        
        with open(config_file, 'r', encoding='utf-8') as f:
            configs = yaml.safe_load(f) or {}
        
        # 隐藏敏感信息
        result = []
        for name, config in configs.items():
            result.append({
                "name": name,
                "db_type": config.get("db_type"),
                "host": config.get("host"),
                "port": config.get("port"),
                "database": config.get("database")
            })
        
        return success_response(result)
        
    except Exception as e:
        logger.error(f"获取配置列表失败: {e}")
        return error_response(f"获取配置列表失败: {str(e)}")


# ==================== 连接管理 ====================

@router.post("/test-connection")
async def test_connection(request: TestConnectionRequest, current_user = Depends(get_current_user)):
    """
    测试数据库连接
    
    Args:
        request: 测试连接请求
        
    Returns:
        连接测试结果
    """
    try:
        import yaml
        from pathlib import Path
        
        # 加载配置
        config_file = Path("./config/databases.yaml")
        with open(config_file, 'r', encoding='utf-8') as f:
            configs = yaml.safe_load(f) or {}
        
        config = configs.get(request.config_name)
        if not config:
            return error_response("配置不存在")
        
        # 解密密码
        if config.get("password"):
            # TODO: 实现密码解密
            pass
        
        # 获取连接
        connector = connection_manager.get_connection(request.config_name, config)
        
        if connector:
            return success_response({
                "status": "connected",
                "message": "连接成功"
            })
        else:
            return error_response("连接失败")
            
    except Exception as e:
        logger.error(f"测试连接失败: {e}")
        return error_response(f"连接测试失败: {str(e)}")


# ==================== 智能查询 ====================

@router.get("/categories")
async def get_categories(current_user = Depends(get_current_user)):
    """
    获取业务大类列表
    
    Returns:
        业务大类列表
    """
    try:
        template_manager = get_template_manager()
        categories = template_manager.get_categories()
        return success_response(categories)
    except Exception as e:
        return error_response(f"获取业务大类失败: {str(e)}")


@router.get("/queries/{category_id}")
async def get_queries(category_id: str, current_user = Depends(get_current_user)):
    """
    获取指定大类的查询列表
    
    Args:
        category_id: 大类ID
        
    Returns:
        查询列表
    """
    try:
        template_manager = get_template_manager()
        queries = template_manager.get_queries(category_id)
        return success_response(queries)
    except Exception as e:
        return error_response(f"获取查询列表失败: {str(e)}")


@router.post("/smart")
async def smart_query(request: SmartQueryRequest, current_user = Depends(get_current_user)):
    """
    执行智能查询
    
    Args:
        request: 智能查询请求
        
    Returns:
        查询结果
    """
    try:
        import yaml
        from pathlib import Path
        
        # 加载数据库配置
        config_file = Path("./config/databases.yaml")
        with open(config_file, 'r', encoding='utf-8') as f:
            configs = yaml.safe_load(f) or {}
        
        config = configs.get(request.config_name)
        if not config:
            return error_response("数据库配置不存在")
        
        # 生成SQL
        template_manager = get_template_manager()
        
        # 解析时间
        start_time = None
        end_time = None
        if request.start_time:
            start_time = datetime.strptime(request.start_time, "%Y-%m-%d %H:%M:%S")
        if request.end_time:
            end_time = datetime.strptime(request.end_time, "%Y-%m-%d %H:%M:%S")
        
        # 生成SQL（简化版，实际需要根据conditions生成）
        if request.conditions:
            first_cond = request.conditions[0]
            sql = template_manager.generate_sql(
                request.category,
                request.query_id,
                first_cond.get("field"),
                first_cond.get("value"),
                start_time,
                end_time
            )
        else:
            return error_response("请至少提供一个查询条件")
        
        if not sql:
            return error_response("无法生成查询语句")
        
        # 执行查询
        connector = connection_manager.get_connection(request.config_name, config)
        if not connector:
            return error_response("无法建立数据库连接")
        
        from db.query_executor import QueryExecutor
        executor = QueryExecutor(connector)
        result = executor.execute_query(sql)
        
        # 记录日志
        logger.info(f"用户 {current_user.user_id} 执行查询: {sql[:100]}")
        
        return success_response({
            "sql": sql,
            "rows": result or [],
            "count": len(result) if result else 0
        })
        
    except Exception as e:
        logger.error(f"智能查询失败: {e}")
        return error_response(f"查询失败: {str(e)}")


# ==================== SQL查询 ====================

@router.post("/execute")
async def execute_query(request: ExecuteQueryRequest, current_user = Depends(get_current_user)):
    """
    执行SQL查询
    
    Args:
        request: 执行查询请求
        
    Returns:
        查询结果
    """
    try:
        # 安全校验：检查SQL是否包含危险操作
        sql_upper = request.sql.upper().strip()
        dangerous_keywords = ["DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE", "INSERT", "UPDATE"]
        
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                return error_response(f"安全限制：不允许执行 {keyword} 操作")
        
        import yaml
        from pathlib import Path
        
        # 加载配置
        config_file = Path("./config/databases.yaml")
        with open(config_file, 'r', encoding='utf-8') as f:
            configs = yaml.safe_load(f) or {}
        
        config = configs.get(request.config_name)
        if not config:
            return error_response("数据库配置不存在")
        
        # 获取连接
        connector = connection_manager.get_connection(request.config_name, config)
        if not connector:
            return error_response("无法建立数据库连接")
        
        # 执行查询
        from db.query_executor import QueryExecutor
        executor = QueryExecutor(connector)
        result = executor.execute_query(request.sql)
        
        # 记录日志
        logger.info(f"用户 {current_user.user_id} 执行SQL: {request.sql[:100]}")
        
        return success_response({
            "rows": result or [],
            "count": len(result) if result else 0
        })
        
    except Exception as e:
        logger.error(f"SQL查询失败: {e}")
        return error_response(f"查询失败: {str(e)}")


# ==================== 导出功能 ====================

@router.post("/export")
async def export_query_result(request: ExecuteQueryRequest, current_user = Depends(get_current_user)):
    """
    导出查询结果
    
    Args:
        request: 执行查询请求
        
    Returns:
        导出文件URL
    """
    try:
        # 先执行查询
        query_result = await execute_query(request, current_user)
        
        if query_result.get("code") != 200:
            return query_result
        
        data = query_result.get("data", {})
        rows = data.get("rows", [])
        
        if not rows:
            return error_response("查询结果为空，无法导出")
        
        # 导出为Excel
        import pandas as pd
        from pathlib import Path
        import uuid
        
        export_dir = Path("./exports")
        export_dir.mkdir(exist_ok=True)
        
        filename = f"query_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.xlsx"
        filepath = export_dir / filename
        
        df = pd.DataFrame(rows)
        df.to_excel(filepath, index=False, engine='openpyxl')
        
        # 返回下载URL
        return success_response({
            "filename": filename,
            "url": f"/exports/{filename}",
            "rows": len(rows)
        })
        
    except Exception as e:
        logger.error(f"导出失败: {e}")
        return error_response(f"导出失败: {str(e)}")

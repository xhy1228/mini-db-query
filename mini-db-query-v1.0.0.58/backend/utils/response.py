# -*- coding: utf-8 -*-
"""
多源数据查询小程序版 - API响应工具
"""

from typing import Any, Optional, Dict
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ResponseModel(BaseModel):
    """响应模型"""
    code: int = 200
    message: str = "success"
    data: Any = None


def success_response(data: Any = None, message: str = "success") -> Dict:
    """
    成功响应
    
    Args:
        data: 数据
        message: 消息
        
    Returns:
        响应字典
    """
    return {
        "code": 200,
        "message": message,
        "data": data
    }


def error_response(message: str, code: int = 400, data: Any = None) -> Dict:
    """
    错误响应
    
    Args:
        message: 错误消息
        code: 错误码
        data: 附加数据
        
    Returns:
        响应字典
    """
    return {
        "code": code,
        "message": message,
        "data": data
    }


def paginate_response(data: list, page: int, page_size: int, total: int) -> Dict:
    """
    分页响应
    
    Args:
        data: 数据列表
        page: 当前页码
        page_size: 每页大小
        total: 总数
        
    Returns:
        响应字典
    """
    return {
        "code": 200,
        "message": "success",
        "data": {
            "items": data,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size
        }
    }

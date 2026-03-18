# -*- coding: utf-8 -*-
"""
Statistics API - 数据统计分析

Author: 飞书百万（AI助手）
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel

from models import get_db_session
from models.database import QueryLog, User, School, QueryTemplate
from core.security import get_current_user, TokenData

router = APIRouter(tags=["统计"])


# ========== 响应模型 ==========

class DashboardStats(BaseModel):
    """仪表盘统计"""
    total_queries: int
    today_queries: int
    success_rate: float
    avg_query_time: float
    total_users: int
    active_users: int


class QueryTrend(BaseModel):
    """查询趋势"""
    date: str
    count: int
    success: int
    failed: int


class TopQuery(BaseModel):
    """热门查询"""
    name: str
    count: int
    avg_time: float


class SchoolStats(BaseModel):
    """学校统计"""
    school_id: int
    school_name: str
    query_count: int
    user_count: int


# ========== API路由 ==========

@router.get("/stats/dashboard")
async def get_dashboard_stats(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    获取仪表盘统计数据
    
    返回：总查询数、今日查询数、成功率、平均耗时等
    """
    # 总查询数
    total_queries = db.query(func.count(QueryLog.id)).scalar() or 0
    
    # 今日查询数
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_queries = db.query(func.count(QueryLog.id)).filter(
        QueryLog.created_at >= today_start
    ).scalar() or 0
    
    # 成功率
    success_count = db.query(func.count(QueryLog.id)).filter(
        QueryLog.status == 'success'
    ).scalar() or 0
    success_rate = (success_count / total_queries * 100) if total_queries > 0 else 0
    
    # 平均耗时
    avg_time = db.query(func.avg(QueryLog.query_time)).filter(
        QueryLog.status == 'success'
    ).scalar() or 0
    
    # 总用户数
    total_users = db.query(func.count(User.id)).scalar() or 0
    
    # 活跃用户（近7天有查询）
    week_ago = datetime.now() - timedelta(days=7)
    active_users = db.query(func.count(func.distinct(QueryLog.user_id))).filter(
        QueryLog.created_at >= week_ago
    ).scalar() or 0
    
    return {
        "code": 200,
        "message": "获取成功",
        "data": {
            "total_queries": total_queries,
            "today_queries": today_queries,
            "success_rate": round(success_rate, 2),
            "avg_query_time": round(avg_time, 2),
            "total_users": total_users,
            "active_users": active_users
        }
    }


@router.get("/stats/trend")
async def get_query_trend(
    days: int = Query(7, ge=1, le=30),
    school_id: Optional[int] = None,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    获取查询趋势
    
    - **days**: 统计天数（1-30）
    - **school_id**: 学校ID（可选）
    """
    trends = []
    
    for i in range(days - 1, -1, -1):
        date = datetime.now().date() - timedelta(days=i)
        date_start = datetime.combine(date, datetime.min.time())
        date_end = datetime.combine(date, datetime.max.time())
        
        query = db.query(QueryLog).filter(
            and_(
                QueryLog.created_at >= date_start,
                QueryLog.created_at <= date_end
            )
        )
        
        if school_id:
            query = query.filter(QueryLog.school_id == school_id)
        
        count = query.count()
        success = query.filter(QueryLog.status == 'success').count()
        failed = count - success
        
        trends.append({
            "date": date.strftime("%m-%d"),
            "count": count,
            "success": success,
            "failed": failed
        })
    
    return {
        "code": 200,
        "message": "获取成功",
        "data": trends
    }


@router.get("/stats/top-queries")
async def get_top_queries(
    limit: int = Query(10, ge=1, le=50),
    days: int = Query(7, ge=1, le=30),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    获取热门查询
    
    - **limit**: 返回条数
    - **days**: 统计天数
    """
    start_date = datetime.now() - timedelta(days=days)
    
    # 按查询名称分组统计
    results = db.query(
        QueryLog.query_name,
        func.count(QueryLog.id).label('count'),
        func.avg(QueryLog.query_time).label('avg_time')
    ).filter(
        QueryLog.created_at >= start_date,
        QueryLog.query_name.isnot(None)
    ).group_by(
        QueryLog.query_name
    ).order_by(
        func.count(QueryLog.id).desc()
    ).limit(limit).all()
    
    top_queries = [
        {
            "name": r[0] or "未知查询",
            "count": r[1],
            "avg_time": round(r[2] or 0, 2)
        }
        for r in results
    ]
    
    return {
        "code": 200,
        "message": "获取成功",
        "data": top_queries
    }


@router.get("/stats/schools")
async def get_school_stats(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    获取各学校统计
    
    返回：各学校的查询数、用户数
    """
    # 查询数统计
    query_stats = db.query(
        QueryLog.school_id,
        func.count(QueryLog.id).label('query_count')
    ).group_by(QueryLog.school_id).all()
    
    query_dict = {q[0]: q[1] for q in query_stats}
    
    # 用户数统计（通过 user_schools）
    from models.database import UserSchool
    user_stats = db.query(
        UserSchool.school_id,
        func.count(UserSchool.user_id).label('user_count')
    ).group_by(UserSchool.school_id).all()
    
    user_dict = {u[0]: u[1] for u in user_stats}
    
    # 获取学校信息
    schools = db.query(School).filter(School.status == 'active').all()
    
    result = [
        {
            "school_id": s.id,
            "school_name": s.name,
            "query_count": query_dict.get(s.id, 0),
            "user_count": user_dict.get(s.id, 0)
        }
        for s in schools
    ]
    
    # 按查询数排序
    result.sort(key=lambda x: x['query_count'], reverse=True)
    
    return {
        "code": 200,
        "message": "获取成功",
        "data": result
    }


@router.get("/stats/templates")
async def get_template_stats(
    school_id: Optional[int] = None,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    获取模板使用统计
    
    - **school_id**: 学校ID（可选）
    """
    query = db.query(
        QueryLog.template_id,
        func.count(QueryLog.id).label('use_count'),
        func.avg(QueryLog.query_time).label('avg_time')
    ).filter(
        QueryLog.template_id.isnot(None)
    )
    
    if school_id:
        query = query.filter(QueryLog.school_id == school_id)
    
    results = query.group_by(QueryLog.template_id).all()
    
    # 获取模板信息
    template_ids = [r[0] for r in results]
    templates = db.query(QueryTemplate).filter(
        QueryTemplate.id.in_(template_ids)
    ).all()
    template_dict = {t.id: t for t in templates}
    
    stats = [
        {
            "template_id": r[0],
            "template_name": template_dict.get(r[0], {}).get('name', '未知模板'),
            "use_count": r[1],
            "avg_time": round(r[2] or 0, 2)
        }
        for r in results
    ]
    
    # 按使用次数排序
    stats.sort(key=lambda x: x['use_count'], reverse=True)
    
    return {
        "code": 200,
        "message": "获取成功",
        "data": stats
    }


@router.get("/stats/users")
async def get_user_stats(
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(20, ge=1, le=100),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    获取用户查询统计
    
    - **days**: 统计天数
    - **limit**: 返回条数
    """
    start_date = datetime.now() - timedelta(days=days)
    
    results = db.query(
        QueryLog.user_id,
        QueryLog.username,
        func.count(QueryLog.id).label('query_count'),
        func.sum(QueryLog.result_count).label('total_rows')
    ).filter(
        QueryLog.created_at >= start_date
    ).group_by(
        QueryLog.user_id,
        QueryLog.username
    ).order_by(
        func.count(QueryLog.id).desc()
    ).limit(limit).all()
    
    stats = [
        {
            "user_id": r[0],
            "username": r[1] or f"用户{r[0]}",
            "query_count": r[2],
            "total_rows": r[3] or 0
        }
        for r in results
    ]
    
    return {
        "code": 200,
        "message": "获取成功",
        "data": stats
    }

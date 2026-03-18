# -*- coding: utf-8 -*-
"""
Log API Router - Query and manage operation/query logs
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models import get_db_session, OperationLog, QueryLog
from core.security import get_current_user, get_current_admin, TokenData
from services.log_service import LogService

router = APIRouter(tags=["logs"])


# Response models
class OperationLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    username: Optional[str]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    details: Optional[str]
    ip_address: Optional[str]
    status: str
    error_message: Optional[str]
    created_at: str
    
    class Config:
        from_attributes = True


class QueryLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    username: Optional[str]
    query_type: str
    database_name: Optional[str]
    sql_content: Optional[str]
    parameters: Optional[dict]
    result_count: Optional[int]
    execution_time_ms: Optional[int]
    status: str
    error_message: Optional[str]
    ip_address: Optional[str]
    created_at: str
    
    class Config:
        from_attributes = True


class LogStatsResponse(BaseModel):
    total: int
    success: int
    failed: int
    success_rate: float
    top_actions: List[dict]


# API Endpoints
@router.get("/operations", response_model=List[OperationLogResponse])
async def get_operation_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    days: Optional[int] = Query(7, ge=1, le=90),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get operation logs (requires login)"""
    # Non-admin can only see their own logs
    if current_user.role != "admin" and user_id is None:
        user_id = int(current_user.user_id)
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    logs = LogService.get_operation_logs(
        db=db,
        skip=skip,
        limit=limit,
        user_id=user_id,
        action=action,
        start_date=start_date
    )
    
    return [OperationLogResponse(**log.to_dict()) for log in logs]


@router.get("/queries", response_model=List[QueryLogResponse])
async def get_query_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user_id: Optional[int] = None,
    database_id: Optional[int] = None,
    days: Optional[int] = Query(7, ge=1, le=90),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get query logs (requires login)"""
    # Non-admin can only see their own logs
    if current_user.role != "admin" and user_id is None:
        user_id = int(current_user.user_id)
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    logs = LogService.get_query_logs(
        db=db,
        skip=skip,
        limit=limit,
        user_id=user_id,
        database_id=database_id,
        start_date=start_date
    )
    
    return [QueryLogResponse(**log.to_dict()) for log in logs]


@router.get("/stats", response_model=LogStatsResponse)
async def get_log_stats(
    days: int = Query(7, ge=1, le=90),
    current_user: TokenData = Depends(get_current_admin),
    db: Session = Depends(get_db_session)
):
    """Get log statistics (admin only)"""
    stats = LogService.get_operation_stats(db=db, days=days)
    return LogStatsResponse(**stats)


@router.get("/operations/{log_id}", response_model=OperationLogResponse)
async def get_operation_log_detail(
    log_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get operation log detail"""
    log = db.query(OperationLog).filter(OperationLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    
    # Non-admin can only see their own logs
    if current_user.role != "admin" and log.user_id != int(current_user.user_id):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    return OperationLogResponse(**log.to_dict())


@router.get("/queries/{log_id}", response_model=QueryLogResponse)
async def get_query_log_detail(
    log_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get query log detail"""
    log = db.query(QueryLog).filter(QueryLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    
    # Non-admin can only see their own logs
    if current_user.role != "admin" and log.user_id != int(current_user.user_id):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    return QueryLogResponse(**log.to_dict())


@router.delete("/operations/cleanup")
async def cleanup_old_logs(
    days: int = Query(30, ge=7, le=365),
    current_user: TokenData = Depends(get_current_admin),
    db: Session = Depends(get_db_session)
):
    """Cleanup logs older than specified days (admin only)"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Delete old operation logs
    deleted_ops = db.query(OperationLog).filter(
        OperationLog.created_at < cutoff_date
    ).delete()
    
    # Delete old query logs
    deleted_queries = db.query(QueryLog).filter(
        QueryLog.created_at < cutoff_date
    ).delete()
    
    db.commit()
    
    return {
        "message": f"Cleaned up {deleted_ops} operation logs and {deleted_queries} query logs",
        "deleted_operation_logs": deleted_ops,
        "deleted_query_logs": deleted_queries,
        "cutoff_date": cutoff_date.strftime("%Y-%m-%d %H:%M:%S")
    }

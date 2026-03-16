# -*- coding: utf-8 -*-
"""
多源数据查询小程序版 - 主入口

Author: 飞书百万（AI助手）
"""

import logging
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn

from core.config import settings
from api import auth, query


# 配置日志
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./logs/app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    # 启动时
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} 启动中...")
    logger.info(f"📡 服务地址: http://{settings.HOST}:{settings.PORT}")
    
    # 初始化数据库
    from models.session import init_db
    init_db()
    logger.info("✅ 数据库初始化完成")
    
    # 检查依赖
    try:
        from db.connector import check_dependencies
        missing = check_dependencies()
        if missing:
            logger.warning(f"⚠️ 缺少数据库驱动: {', '.join(missing)}")
        else:
            logger.info("✅ 所有数据库驱动已安装")
    except Exception as e:
        logger.warning(f"⚠️ 数据库驱动检查失败: {e}")
    
    yield
    
    # 关闭时
    try:
        from db.connection_manager import connection_manager
        connection_manager.stop()
    except:
        pass
    logger.info("👋 服务已关闭")


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="多源数据查询小程序后端服务",
    lifespan=lifespan
)


# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    logger.error(f"全局异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": f"服务器内部错误: {str(exc)}",
            "data": None
        }
    )


# 注册路由
app.include_router(auth.router, prefix="/api")
app.include_router(query.router, prefix="/api")


# 静态文件服务（导出文件）
export_dir = Path("./exports")
export_dir.mkdir(exist_ok=True)
app.mount("/exports", StaticFiles(directory="./exports"), name="exports")


# 健康检查
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )

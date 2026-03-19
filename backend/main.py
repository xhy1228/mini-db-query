# -*- coding: utf-8 -*-
"""
Mini DB Query - Main Entry Point

Deploy first, configure database later
"""

import os
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_database_configured() -> bool:
    """检查数据库是否已配置"""
    try:
        from core.config import settings
        return bool(settings.DATABASE_URL and settings.DATABASE_URL.strip())
    except:
        return False


def check_database_connection() -> tuple[bool, str]:
    """检查数据库连接是否可用
    
    Returns:
        (success, message)
    """
    try:
        from sqlalchemy import create_engine, text
        from core.config import settings
        
        if not settings.DATABASE_URL:
            return False, "Database not configured"
        
        if not settings.is_mysql:
            return False, "DATABASE_URL must be MySQL"
        
        # 测试连接
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT VERSION()"))
            version = result.scalar()
            return True, f"MySQL {version}"
            
    except Exception as e:
        return False, str(e)


def check_tables_initialized() -> bool:
    """检查数据库表是否已初始化"""
    try:
        from sqlalchemy import create_engine, text
        from core.config import settings
        
        if not settings.DATABASE_URL:
            return False
        
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            # 检查 users 表是否存在
            result = conn.execute(text("SHOW TABLES LIKE 'users'"))
            return result.fetchone() is not None
    except:
        return False


def main():
    """Main entry point with error handling"""
    try:
        # Setup logging first
        os.makedirs("./logs", exist_ok=True)
        
        from fastapi import FastAPI, Request, Response
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.staticfiles import StaticFiles
        from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
        from contextlib import asynccontextmanager
        import uvicorn
        import logging

        # Setup basic logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('./logs/app.log', encoding='utf-8')
            ]
        )
        logger = logging.getLogger(__name__)

        # Load config
        from core.config import settings
        logger.info("=" * 60)
        logger.info("Starting Mini DB Query Server")
        logger.info("=" * 60)
        logger.info(f"Python: {sys.version}")
        logger.info(f"Working Directory: {os.getcwd()}")
        logger.info(f"App Version: {settings.APP_VERSION}")
        
        # 检查数据库配置状态
        db_configured = check_database_configured()
        db_connected = False
        db_initialized = False
        
        if db_configured:
            mysql_info = settings.mysql_info
            if mysql_info:
                logger.info(f"MySQL: {mysql_info.get('host')}:{mysql_info.get('port')}/{mysql_info.get('db_name')}")
            
            db_connected, db_msg = check_database_connection()
            if db_connected:
                logger.info(f"Database connected: {db_msg}")
                db_initialized = check_tables_initialized()
                if not db_initialized:
                    logger.warning("Database tables not initialized. Please run init_database.sql")
            else:
                logger.warning(f"Database connection failed: {db_msg}")
        else:
            logger.info("Database not configured yet. Use /setup to configure.")

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            """Application lifecycle manager"""
            logger.info("Initializing application...")
            
            # 不强制检查数据库，允许无数据库启动
            if not db_configured:
                logger.info("Database not configured. Please visit /setup to configure.")
            elif not db_connected:
                logger.warning("Database connection failed. Please check configuration.")
            elif not db_initialized:
                logger.warning("Database tables not initialized. Please run init_database.sql")
            else:
                # 初始化数据库会话
                try:
                    from models.session import init_db
                    init_db()
                    logger.info("Database session initialized")
                except Exception as e:
                    logger.error(f"Database session init failed: {e}")
            
            # Check database drivers
            try:
                from db.connector import check_dependencies
                missing = check_dependencies()
                if missing:
                    logger.warning(f"Missing database drivers: {', '.join(missing)}")
                else:
                    logger.info("All database drivers installed")
            except Exception as e:
                logger.warning(f"Database driver check failed: {e}")
            
            logger.info("=" * 60)
            logger.info(f"Server ready at http://{settings.HOST}:{settings.PORT}")
            logger.info(f"Setup Page: http://{settings.HOST}:{settings.PORT}/setup")
            logger.info(f"Admin Panel: http://{settings.HOST}:{settings.PORT}/admin")
            logger.info(f"API Docs: http://{settings.HOST}:{settings.PORT}/docs")
            logger.info("=" * 60)
            
            yield
            
            # Shutdown
            try:
                from db.connection_manager import connection_manager
                connection_manager.stop()
            except:
                pass
            logger.info("Server stopped")

        # 创建FastAPI应用
        app = FastAPI(
            title=settings.APP_NAME,
            version=settings.APP_VERSION,
            description="多源数据查询小程序后端服务 - Deploy first, configure later",
            lifespan=lifespan
        )

        # 配置CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.allowed_origins_list,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 添加统一日志中间件
        from core.logging_middleware import LoggingMiddleware
        app.add_middleware(LoggingMiddleware)

        # 全局异常处理
        @app.exception_handler(Exception)
        async def global_exception_handler(request: Request, exc: Exception):
            """全局异常处理"""
            logger.error(f"Global exception: {exc}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "code": 500,
                    "message": f"服务器内部错误: {str(exc)}",
                    "data": None
                }
            )

        # 注册路由
        from api import auth, query, logs, manage, stats, security
        app.include_router(auth.router, prefix="/api")
        app.include_router(query.router, prefix="/api")
        app.include_router(logs.router, prefix="/api")
        app.include_router(manage.router, prefix="/api/manage")
        app.include_router(stats.router, prefix="/api")
        app.include_router(security.router, prefix="/api/security")
        
        # Setup API - 必须在静态文件之前
        from api.setup import router as setup_router
        app.include_router(setup_router, prefix="/api")

        # 静态文件服务（导出文件）
        export_dir = Path("./exports")
        export_dir.mkdir(exist_ok=True)
        app.mount("/exports", StaticFiles(directory="./exports"), name="exports")

        # 管理后台静态文件
        admin_dir = None
        possible_paths = [
            Path("./admin"),
            Path("../admin"),
            Path("../../admin"),
        ]

        for p in possible_paths:
            if p.exists():
                admin_dir = p
                logger.info(f"Admin panel found at: {p.absolute()}")
                break

        if admin_dir:
            app.mount("/admin", StaticFiles(directory=str(admin_dir.absolute()), html=True), name="admin")
        else:
            logger.warning("Admin panel directory not found!")

        # Setup 页面路由
        @app.get("/setup", response_class=HTMLResponse)
        async def setup_page():
            """配置页面"""
            html_path = Path(__file__).parent / "admin" / "setup.html"
            if html_path.exists():
                return HTMLResponse(content=html_path.read_text(encoding='utf-8'))
            return HTMLResponse(content="<h1>Setup page not found</h1><p>Please check admin/setup.html</p>")

        # 健康检查
        @app.get("/health")
        async def health_check():
            """健康检查"""
            db_status = "not_configured"
            if db_configured:
                if db_connected:
                    db_status = "connected"
                else:
                    db_status = "connection_failed"
            
            return {
                "status": "healthy",
                "app": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "database": db_status
            }
        
        # 获取版本信息
        @app.get("/api/version")
        async def get_version():
            """获取程序版本信息"""
            return {
                "code": 200,
                "message": "success",
                "data": {
                    "version": settings.APP_VERSION,
                    "app_name": settings.APP_NAME
                }
            }

        # 根路径 - 直接返回管理界面（登录页面）
        @app.get("/")
        async def root():
            """根路径 - 返回管理界面（登录页面）"""
            # 直接返回管理界面，让用户登录
            html_path = Path(__file__).parent / "admin" / "index.html"
            if html_path.exists():
                return HTMLResponse(content=html_path.read_text(encoding='utf-8'))
            # 如果找不到管理页面，尝试 ../admin/index.html
            html_path2 = Path(__file__).parent / ".." / "admin" / "index.html"
            if html_path2.exists():
                return HTMLResponse(content=html_path2.read_text(encoding='utf-8'))
            # 都找不到，返回API信息
            return JSONResponse(content={
                "name": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "docs": "/docs",
                "health": "/health",
                "setup": "/setup",
                "admin": "/admin"
            })

        # 启动服务器
        logger.info("Starting uvicorn server...")
        uvicorn.run(
            app,
            host=settings.HOST,
            port=settings.PORT,
            log_level="info"
        )

    except Exception as e:
        # 写入错误日志
        with open('./logs/startup_error.log', 'w', encoding='utf-8') as f:
            import traceback
            f.write(f"Startup Error: {e}\n\n")
            f.write(traceback.format_exc())
        
        print(f"\n[ERROR] Failed to start server: {e}")
        print("Check logs/startup_error.log for details\n")
        input("Press Enter to exit...")
        sys.exit(1)


if __name__ == "__main__":
    main()

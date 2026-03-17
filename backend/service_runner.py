# -*- coding: utf-8 -*-
"""
Mini DB Query - Windows Service Runner

使用 pythonw.exe 运行此脚本可实现无窗口后台运行

两种运行模式:
1. 命令行模式: python service_runner.py
2. 无窗口模式: pythonw service_runner.py
3. Windows服务: 通过 NSSM 或 pywin32 安装
"""

import os
import sys
import logging
import time
import threading
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置日志
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'service.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ServiceRunner:
    """服务运行器"""
    
    def __init__(self):
        self.running = False
        self.server = None
        self.thread = None
    
    def start(self):
        """启动服务"""
        if self.running:
            logger.warning("Service already running")
            return
        
        self.running = True
        logger.info("=" * 50)
        logger.info("Mini DB Query Service Starting...")
        logger.info("=" * 50)
        
        try:
            import uvicorn
            from core.config import settings
            
            # 记录配置信息
            logger.info(f"Host: {settings.HOST}")
            logger.info(f"Port: {settings.PORT}")
            logger.info(f"Debug: {settings.DEBUG}")
            
            # 检查数据库配置
            db_configured = self._check_database()
            if db_configured:
                logger.info("Database: Configured and connected")
            else:
                logger.info("Database: Not configured - visit /setup to configure")
            
            # 启动服务器
            logger.info(f"Starting server on http://{settings.HOST}:{settings.PORT}")
            
            # 使用 uvicorn 运行
            config = uvicorn.Config(
                "main:app",
                host=settings.HOST,
                port=settings.PORT,
                reload=False,  # 服务模式不热重载
                access_log=True,
                log_level="info"
            )
            self.server = uvicorn.Server(config)
            
            # 在新线程中运行
            self.thread = threading.Thread(target=self._run_server, daemon=True)
            self.thread.start()
            
            logger.info("Service started successfully!")
            logger.info(f"Admin Panel: http://localhost:{settings.PORT}/admin")
            logger.info(f"Setup Page: http://localhost:{settings.PORT}/setup")
            
            # 保持主线程运行
            self._keep_alive()
            
        except Exception as e:
            logger.error(f"Failed to start service: {e}", exc_info=True)
            self.running = False
            raise
    
    def _run_server(self):
        """运行服务器"""
        try:
            self.server.run()
        except Exception as e:
            logger.error(f"Server error: {e}", exc_info=True)
            self.running = False
    
    def _check_database(self) -> bool:
        """检查数据库配置"""
        try:
            from core.config import settings
            if not settings.DATABASE_URL:
                return False
            
            from sqlalchemy import create_engine, text
            engine = create_engine(settings.DATABASE_URL)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.warning(f"Database check failed: {e}")
            return False
    
    def _keep_alive(self):
        """保持服务运行"""
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
            self.stop()
    
    def stop(self):
        """停止服务"""
        logger.info("Stopping service...")
        self.running = False
        if self.server:
            self.server.should_exit = True
        logger.info("Service stopped")


def run_as_service():
    """作为 Windows 服务运行 (使用 pywin32)"""
    try:
        import win32serviceutil
        import win32service
        import win32event
        import servicemanager
        
        class MiniDBQueryService(win32serviceutil.ServiceFramework):
            """Mini DB Query Windows 服务"""
            
            _svc_name_ = "MiniDBQuery"
            _svc_display_name_ = "Mini DB Query Service"
            _svc_description_ = "多源数据查询服务 - 为微信小程序提供数据库查询API"
            _svc_deps_ = ["Tcpip"]
            
            def __init__(self, args):
                win32serviceutil.ServiceFramework.__init__(self, args)
                self.stop_event = win32event.CreateEvent(None, 0, 0, None)
                self.runner = None
            
            def SvcStop(self):
                """停止服务"""
                self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
                if self.runner:
                    self.runner.stop()
                win32event.SetEvent(self.stop_event)
            
            def SvcDoRun(self):
                """运行服务"""
                servicemanager.LogMsg(
                    servicemanager.EVENTLOG_INFORMATION_TYPE,
                    servicemanager.PYS_SERVICE_STARTED,
                    (self._svc_name_, '')
                )
                
                self.runner = ServiceRunner()
                try:
                    # 启动服务
                    self.runner.start()
                except Exception as e:
                    servicemanager.LogErrorMsg(str(e))
                
                # 等待停止信号
                win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)
        
        # 安装/卸载/运行服务
        if len(sys.argv) == 1:
            # 作为服务运行
            servicemanager.Initialize()
            servicemanager.PrepareToHostSingle(MiniDBQueryService)
            servicemanager.StartServiceCtrlDispatcher()
        else:
            # 命令行操作
            win32serviceutil.HandleCommandLine(MiniDBQueryService)
    
    except ImportError:
        logger.warning("pywin32 not installed. Running in console mode.")
        run_as_console()


def run_as_console():
    """作为控制台程序运行"""
    runner = ServiceRunner()
    try:
        runner.start()
    except KeyboardInterrupt:
        logger.info("Service interrupted by user")
        runner.stop()


def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Mini DB Query Service')
    parser.add_argument('--service', action='store_true', 
                        help='Run as Windows service (requires pywin32)')
    parser.add_argument('--install', action='store_true',
                        help='Install as Windows service')
    parser.add_argument('--uninstall', action='store_true',
                        help='Uninstall Windows service')
    parser.add_argument('--start', action='store_true',
                        help='Start Windows service')
    parser.add_argument('--stop', action='store_true',
                        help='Stop Windows service')
    
    args = parser.parse_args()
    
    if args.service or args.install or args.uninstall or args.start or args.stop:
        # Windows 服务模式
        run_as_service()
    else:
        # 控制台模式
        run_as_console()


if __name__ == '__main__':
    main()

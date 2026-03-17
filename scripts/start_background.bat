@echo off
REM ============================================
REM Mini DB Query - Background Starter
REM 使用 pythonw.exe 后台运行，无窗口
REM ============================================

set "BACKEND_DIR=%~dp0..\backend"

cd /d "%BACKEND_DIR%"

REM 检查 venv
if exist "venv\Scripts\pythonw.exe" (
    set "PYTHONW=venv\Scripts\pythonw.exe"
) else (
    set "PYTHONW=pythonw.exe"
)

echo.
echo ============================================
echo   Mini DB Query - Background Mode
echo ============================================
echo.
echo [INFO] Starting service in background...
echo [INFO] No console window will be shown.
echo [INFO] Check logs at: backend\logs\service.log
echo.

REM 使用 pythonw.exe 后台运行
start "" /B "%PYTHONW%" service_runner.py

REM 等待服务启动
timeout /t 3 /nobreak >nul

echo [OK] Service started in background!
echo [INFO] Opening browser...
start http://localhost:26316/admin

echo.
echo [INFO] You can close this window now.
echo [INFO] To stop the service, use: stop_background.bat
echo.
pause

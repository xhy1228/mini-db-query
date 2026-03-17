@echo off
REM Mini DB Query - Start Server
REM This is the main startup script

title Mini DB Query Server

cd /d "%~dp0"

echo ============================================
echo    Mini DB Query Server
echo ============================================
echo.

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo [INFO] Please run scripts\install.bat first
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Create necessary directories
if not exist "logs" mkdir logs
if not exist "data" mkdir data
if not exist "exports" mkdir exports

echo [INFO] Starting server...
echo [INFO] Press Ctrl+C to stop
echo.
echo ============================================
echo.

REM Start the server
python main.py

REM If server stops, show message
echo.
echo [INFO] Server stopped
pause

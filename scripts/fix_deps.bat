@echo off
REM ============================================
REM Mini DB Query - Fix Dependencies
REM ============================================

echo.
echo ============================================
echo   Mini DB Query - Fix Dependencies
echo ============================================
echo.

cd /d "%~dp0..\backend"

REM Disable proxy
set HTTP_PROXY=
set HTTPS_PROXY=
set http_proxy=
set https_proxy=

if exist "venv" (
    echo [INFO] Removing old virtual environment...
    rmdir /s /q venv
)

echo [INFO] Creating new virtual environment...
python -m venv venv

echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

echo [INFO] Installing all dependencies...
echo This may take a few minutes, please wait...
echo.

pip install fastapi uvicorn sqlalchemy pymysql pydantic-settings python-jose bcrypt passlib pandas pyyaml openpyxl aiofiles httpx cryptography oracledb pyodbc psutil

if %errorLevel% equ 0 (
    echo.
    echo ============================================
    echo [OK] All dependencies installed!
    echo ============================================
    echo.
    echo Starting server...
    python main.py
) else (
    echo.
    echo [ERROR] Installation failed!
    echo Please check your network connection.
    pause
)

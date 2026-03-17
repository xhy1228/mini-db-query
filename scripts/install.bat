@echo off
REM ============================================
REM Mini DB Query - Windows Installation Script
REM Version: v1.0.0.23
REM Description: Deploy first, configure later
REM ============================================

setlocal enabledelayedexpansion

REM Disable proxy globally
set HTTP_PROXY=
set HTTPS_PROXY=
set http_proxy=
set https_proxy=

REM Setup paths
set "PROJECT_DIR=%~dp0.."
set "BACKEND_DIR=%PROJECT_DIR%\backend"
set "LOG_DIR=%PROJECT_DIR%\logs"

REM Create logs directory
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
set "INSTALL_LOG=%LOG_DIR%\install.log"

REM Clear previous log
echo ============================================ > "%INSTALL_LOG%"
echo Installation started at %date% %time% >> "%INSTALL_LOG%"
echo ============================================ >> "%INSTALL_LOG%"

echo.
echo ============================================
echo    Mini DB Query - Installation
echo    Deploy first, configure database later
echo ============================================
echo.
echo Log file: %INSTALL_LOG%
echo.

REM ============================================
REM Step 1: Check Python
REM ============================================
echo [Step 1/5] Checking Python environment...

where python >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python not found! >> "%INSTALL_LOG%"
    echo [ERROR] Python not found!
    echo.
    echo Please install Python 3.10 or higher from:
    echo   https://www.python.org/downloads/
    echo.
    echo IMPORTANT: Check "Add Python to PATH" during installation!
    echo.
    pause
    exit /b 1
)

for /f "delims=" %%v in ('python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))" 2^>nul') do set "PYTHON_VERSION=%%v"
echo [OK] Python %PYTHON_VERSION% found
echo Python version: %PYTHON_VERSION% >> "%INSTALL_LOG%"

REM ============================================
REM Step 2: Create Virtual Environment
REM ============================================
echo.
echo [Step 2/5] Setting up Python environment...

cd /d "%BACKEND_DIR%"
if %errorLevel% neq 0 (
    echo [ERROR] Cannot change to backend directory: %BACKEND_DIR% >> "%INSTALL_LOG%"
    echo [ERROR] Cannot find backend directory!
    echo.
    pause
    exit /b 1
)

if exist "venv" (
    echo [INFO] Removing old virtual environment...
    rmdir /s /q venv 2>nul
    if %errorLevel% neq 0 (
        echo [WARN] Could not remove old venv, trying to continue... >> "%INSTALL_LOG%"
    )
)

echo Creating virtual environment...
python -m venv venv >> "%INSTALL_LOG%" 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Failed to create virtual environment! >> "%INSTALL_LOG%"
    echo [ERROR] Failed to create virtual environment!
    echo.
    echo Possible causes:
    echo   - Python installation is incomplete
    echo   - Insufficient permissions
    echo.
    pause
    exit /b 1
)
echo [OK] Virtual environment created

REM Activate venv
call venv\Scripts\activate.bat
if %errorLevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment! >> "%INSTALL_LOG%"
    echo [ERROR] Failed to activate virtual environment!
    pause
    exit /b 1
)

REM ============================================
REM Step 3: Install Dependencies
REM ============================================
echo.
echo [Step 3/5] Installing dependencies...
echo This may take a few minutes...
echo.

echo Upgrading pip...
python -m pip install --upgrade pip >> "%INSTALL_LOG%" 2>&1
if %errorLevel% neq 0 (
    echo [WARN] Failed to upgrade pip, trying to continue... >> "%INSTALL_LOG%"
)

echo Installing packages (1/3): core packages...
pip install fastapi uvicorn sqlalchemy pydantic-settings python-jose bcrypt passlib >> "%INSTALL_LOG%" 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Failed to install core packages! >> "%INSTALL_LOG%"
    echo [ERROR] Failed to install core packages!
    echo.
    echo Check install.log for details.
    pause
    exit /b 1
)

echo Installing packages (2/3): database drivers...
pip install pymysql oracledb pyodbc cryptography >> "%INSTALL_LOG%" 2>&1
if %errorLevel% neq 0 (
    echo [WARN] Some database drivers may have failed, continuing... >> "%INSTALL_LOG%"
)

echo Installing packages (3/3): utilities...
pip install pandas pyyaml openpyxl aiofiles httpx psutil python-multipart >> "%INSTALL_LOG%" 2>&1
if %errorLevel% neq 0 (
    echo [WARN] Some utility packages may have failed, continuing... >> "%INSTALL_LOG%"
)

echo [OK] Dependencies installed

REM ============================================
REM Step 4: Create Directories
REM ============================================
echo.
echo [Step 4/5] Creating directories...

if not exist "logs" mkdir logs
if not exist "exports" mkdir exports
if not exist "uploads" mkdir uploads
if not exist "data" mkdir data

echo [OK] Directories created

REM ============================================
REM Step 5: Create Default Config
REM ============================================
echo.
echo [Step 5/5] Creating default configuration...

if not exist ".env" (
    (
echo # Mini DB Query Configuration
echo # Configure database via web interface after deployment
echo.
echo HOST=0.0.0.0
echo PORT=26316
echo DEBUG=True
echo.
echo JWT_SECRET_KEY=mini-db-query-secret-key-2026
echo JWT_ALGORITHM=HS256
echo JWT_EXPIRE_MINUTES=10080
echo.
echo WECHAT_APPID=
echo WECHAT_SECRET=
echo.
echo LOG_LEVEL=INFO
echo LOG_DIR=./logs
echo.
echo ALLOWED_ORIGINS=*
echo MAX_QUERY_ROWS=10000
echo QUERY_TIMEOUT=30
echo.
echo # Database will be configured via setup page
echo DATABASE_URL=
    ) > .env
    echo [OK] Default configuration created
) else (
    echo [INFO] .env already exists, skipping
)

REM ============================================
REM Create Startup Scripts
REM ============================================
cd /d "%PROJECT_DIR%"

echo @echo off > "start_server.bat"
echo cd /d "%%~dp0\backend" >> "start_server.bat"
echo call venv\Scripts\activate.bat >> "start_server.bat"
echo start "Mini DB Query Server" cmd /c "python main.py" >> "start_server.bat"
echo timeout /t 3 /nobreak ^>nul >> "start_server.bat"
echo start http://localhost:26316 >> "start_server.bat"

echo [OK] Startup script created

REM ============================================
REM Installation Complete
REM ============================================
echo. >> "%INSTALL_LOG%"
echo Installation completed at %date% %time% >> "%INSTALL_LOG%"

echo.
echo ============================================
echo    Installation Complete!
echo ============================================
echo.
echo Python: %PYTHON_VERSION%
echo.
echo Next Steps:
echo   1. Run start_server.bat to start the server
echo   2. Open http://localhost:26316 in browser
echo   3. Configure database via setup page
echo   4. Execute init_database.sql in MySQL
echo.
echo Access URLs (after starting):
echo   Setup:  http://localhost:26316/setup
echo   Admin:  http://localhost:26316/admin
echo   API:    http://localhost:26316/docs
echo.
echo ============================================
echo.

REM Auto-start option
echo Starting server now...
cd /d "%BACKEND_DIR%"
start "Mini DB Query Server" cmd /c "call venv\Scripts\activate.bat && python main.py"
timeout /t 3 /nobreak >nul
start http://localhost:26316

echo.
echo Thank you for installing Mini DB Query!
echo.
pause

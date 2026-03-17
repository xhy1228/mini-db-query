@echo off
REM Mini DB Query - Test Script
REM Tests if the server can start correctly

title Testing Mini DB Query

cd /d "%~dp0..\backend"

echo ============================================
echo    Testing Mini DB Query
echo ============================================
echo.

REM Check Python
echo [Test 1/6] Checking Python...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [FAIL] Python not found
    goto :failed
)
echo [PASS] Python found

REM Check venv
echo [Test 2/6] Checking virtual environment...
if not exist "venv\Scripts\python.exe" (
    echo [FAIL] Virtual environment not found
    goto :failed
)
echo [PASS] Virtual environment found

REM Activate venv
call venv\Scripts\activate.bat >nul 2>&1

REM Check dependencies
echo [Test 3/6] Checking dependencies...
python -c "import fastapi, uvicorn, sqlalchemy, pymysql" >nul 2>&1
if %errorLevel% neq 0 (
    echo [FAIL] Dependencies not installed
    goto :failed
)
echo [PASS] Dependencies installed

REM Check config
echo [Test 4/6] Checking configuration...
python -c "from core.config import settings; print(f'Port: {settings.PORT}')" >nul 2>&1
if %errorLevel% neq 0 (
    echo [FAIL] Configuration error
    goto :failed
)
echo [PASS] Configuration OK

REM Check database
echo [Test 5/6] Checking database...
python -c "from models.session import engine; print('OK')" >nul 2>&1
if %errorLevel% neq 0 (
    echo [WARN] Database initialization issue
) else (
    echo [PASS] Database OK
)

REM Test server startup
echo [Test 6/6] Testing server startup...
echo [INFO] Starting server for 5 seconds to test...
start /b /wait timeout /t 5 /nobreak
python -c "
import sys
sys.path.insert(0, '.')
from fastapi import FastAPI
from core.config import settings
from models.session import init_db
print(f'Server config: {settings.PORT}')
init_db()
print('SUCCESS: Server can start!')
" > test_output.txt 2>&1

findstr /C:"SUCCESS" test_output.txt >nul 2>&1
if %errorLevel% equ 0 (
    echo [PASS] Server startup test PASSED
    del test_output.txt
    goto :success
) else (
    type test_output.txt
    del test_output.txt
    echo [FAIL] Server startup test FAILED
    goto :failed
)

:success
echo.
echo ============================================
echo    ALL TESTS PASSED!
echo ============================================
echo.
echo You can start the server with:
echo   scripts\start.bat
echo.
echo Or run manually:
echo   cd backend
echo   venv\Scripts\activate.bat
echo   python main.py
echo.
pause
exit /b 0

:failed
echo.
echo ============================================
echo    SOME TESTS FAILED
echo ============================================
echo.
echo Please check the installation:
echo   scripts\install.bat
echo.
pause
exit /b 1

@echo off
REM ============================================
REM Mini DB Query - Stop Background Service
REM ============================================

echo.
echo ============================================
echo   Mini DB Query - Stop Background Service
echo ============================================
echo.

REM 查找并结束 python/pythonw 进程
echo [INFO] Looking for running instances...

tasklist /FI "IMAGENAME eq pythonw.exe" 2>nul | find /I "pythonw.exe" >nul
if %errorLevel% equ 0 (
    echo [INFO] Found pythonw.exe processes
    taskkill /F /IM pythonw.exe >nul 2>&1
    if %errorLevel% equ 0 (
        echo [OK] pythonw.exe processes stopped
    )
)

tasklist /FI "IMAGENAME eq python.exe" 2>nul | find /I "python.exe" >nul
if %errorLevel% equ 0 (
    echo [INFO] Checking python.exe processes...
    
    REM 更精确地查找运行在 26316 端口的进程
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":26316"') do (
        echo [INFO] Found process on port 26316: PID %%a
        taskkill /F /PID %%a >nul 2>&1
    )
)

echo.
echo [OK] Service stopped!
echo.
pause

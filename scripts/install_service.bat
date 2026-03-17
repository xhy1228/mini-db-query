@echo off
REM ============================================
REM Mini DB Query - Install as Windows Service
REM Run this script as Administrator!
REM ============================================

echo.
echo ============================================
echo   Mini DB Query - Service Installation
echo ============================================
echo.

REM Check admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] This script requires Administrator privileges!
    echo [INFO] Right-click and select "Run as administrator"
    pause
    exit /b 1
)

REM Get paths
set "BACKEND_DIR=%~dp0..\backend"
set "SERVICE_NAME=MiniDBQuery"

REM Check if service already exists
sc query %SERVICE_NAME% >nul 2>&1
if %errorLevel% equ 0 (
    echo [WARN] Service already exists. Removing...
    sc stop %SERVICE_NAME% >nul 2>&1
    timeout /t 2 /nobreak >nul
    sc delete %SERVICE_NAME%
    timeout /t 2 /nobreak >nul
)

REM Create service using sc command
echo [INFO] Creating Windows Service...

REM Use cmd.exe to run our service script
set "BIN_PATH=cmd.exe /c \"%BACKEND_DIR%\run_service.bat\""

sc create %SERVICE_NAME% binPath= "%BIN_PATH%" start= auto DisplayName= "Mini DB Query Service"

if %errorLevel% equ 0 (
    echo [OK] Service created successfully!
    echo.
    
    REM Set service description
    sc description %SERVICE_NAME% "Mini DB Query - Multi-database query service for WeChat mini-program"
    
    echo Service Name: %SERVICE_NAME%
    echo Display Name: Mini DB Query Service
    echo.
    echo Control Commands:
    echo   Start:   net start %SERVICE_NAME%
    echo   Stop:    net stop %SERVICE_NAME%
    echo   Status:  sc query %SERVICE_NAME%
    echo.
    
    set /p START_NOW="Start service now? (Y/N): "
    if /i "%START_NOW%"=="Y" (
        echo [INFO] Starting service...
        net start %SERVICE_NAME%
        timeout /t 3 /nobreak >nul
        echo [OK] Service started!
        echo [INFO] Opening browser...
        start http://localhost:26316/admin
    )
) else (
    echo [ERROR] Failed to create service!
    echo [INFO] Make sure you are running as Administrator.
)

echo.
pause

@echo off
REM ============================================
REM Mini DB Query - Uninstall Windows Service
REM Run this script as Administrator!
REM ============================================

echo.
echo ============================================
echo   Mini DB Query - Service Uninstallation
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

set "SERVICE_NAME=MiniDBQuery"

REM Check if service exists
sc query %SERVICE_NAME% >nul 2>&1
if %errorLevel% neq 0 (
    echo [INFO] Service does not exist.
    pause
    exit /b 0
)

REM Stop service if running
echo [INFO] Stopping service...
sc stop %SERVICE_NAME% >nul 2>&1
timeout /t 3 /nobreak >nul

REM Delete service
echo [INFO] Deleting service...
sc delete %SERVICE_NAME%

if %errorLevel% equ 0 (
    echo [OK] Service uninstalled successfully!
) else (
    echo [ERROR] Failed to uninstall service!
)

echo.
pause

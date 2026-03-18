@echo off
REM ============================================
REM Mini DB Query - Uninstall Windows Service
REM ============================================

echo.
echo ============================================
echo   Mini DB Query - Service Uninstaller
echo ============================================
echo.

REM 检查管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] 需要管理员权限!
    echo [INFO] 请右键选择"以管理员身份运行"
    pause
    exit /b 1
)

set "SCRIPT_DIR=%~dp0"
set "NSSM_EXE=%SCRIPT_DIR%nssm\nssm.exe"
set "SERVICE_NAME=MiniDBQuery"

REM 检查服务是否存在
sc query %SERVICE_NAME% >nul 2>&1
if %errorLevel% neq 0 (
    echo [INFO] Service not found or already removed
    pause
    exit /b 0
)

echo [INFO] Stopping service...
net stop %SERVICE_NAME% >nul 2>&1
timeout /t 2 /nobreak >nul

echo [INFO] Removing service...
if exist "%NSSM_EXE%" (
    %NSSM_EXE% remove %SERVICE_NAME% confirm
) else (
    sc delete %SERVICE_NAME%
)

timeout /t 2 /nobreak >nul

echo [OK] Service removed successfully!
echo.
pause

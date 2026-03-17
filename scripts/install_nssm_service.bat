@echo off
REM ============================================
REM Mini DB Query - Install as Windows Service
REM 使用 NSSM (Non-Sucking Service Manager)
REM ============================================
REM
REM 使用说明:
REM 1. 以管理员身份运行此脚本
REM 2. NSSM 会自动下载或使用本地 nssm.exe
REM 3. 服务安装后可通过 Windows 服务管理器管理
REM
REM ============================================

setlocal enabledelayedexpansion

echo.
echo ============================================
echo   Mini DB Query - Windows Service Installer
echo   Method: NSSM (Recommended)
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

REM 设置路径
set "SCRIPT_DIR=%~dp0"
set "BACKEND_DIR=%SCRIPT_DIR%..\backend"
set "NSSM_DIR=%SCRIPT_DIR%..\tools\nssm"
set "SERVICE_NAME=MiniDBQuery"

REM 检查 NSSM
if not exist "%NSSM_DIR%\nssm.exe" (
    echo [INFO] NSSM not found. Downloading...
    
    REM 创建目录
    if not exist "%NSSM_DIR%" mkdir "%NSSM_DIR%"
    
    REM 使用 PowerShell 下载 NSSM
    echo [INFO] Downloading NSSM from official site...
    powershell -Command "& { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://nssm.cc/release/nssm-2.24.zip' -OutFile '%TEMP%\nssm.zip' }"
    
    if exist "%TEMP%\nssm.zip" (
        echo [INFO] Extracting NSSM...
        powershell -Command "& { Expand-Archive -Path '%TEMP%\nssm.zip' -DestinationPath '%TEMP%\nssm' -Force }"
        
        REM 复制正确的版本 (64位)
        if exist "%TEMP%\nssm\nssm-2.24\win64\nssm.exe" (
            copy "%TEMP%\nssm\nssm-2.24\win64\nssm.exe" "%NSSM_DIR%\nssm.exe" >nul
            echo [OK] NSSM downloaded successfully
        ) else if exist "%TEMP%\nssm\nssm-2.25\win64\nssm.exe" (
            copy "%TEMP%\nssm\nssm-2.25\win64\nssm.exe" "%NSSM_DIR%\nssm.exe" >nul
            echo [OK] NSSM downloaded successfully
        ) else (
            echo [WARN] Could not find nssm.exe in downloaded archive
            echo [INFO] Trying alternative download...
            
            REM 直接下载 exe
            powershell -Command "& { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://nssm.cc/ci/nssm-2.25-53-g92303cc.zip' -OutFile '%TEMP%\nssm2.zip' }"
            if exist "%TEMP%\nssm2.zip" (
                powershell -Command "& { Expand-Archive -Path '%TEMP%\nssm2.zip' -DestinationPath '%TEMP%\nssm2' -Force }"
                for /r "%TEMP%\nssm2" %%f in (nssm.exe) do (
                    if exist "%%f" copy "%%f" "%NSSM_DIR%\nssm.exe" >nul
                )
            )
        )
    )
)

REM 再次检查 NSSM
if not exist "%NSSM_DIR%\nssm.exe" (
    echo.
    echo [ERROR] Failed to download NSSM
    echo.
    echo Please download manually:
    echo   1. Visit https://nssm.cc/download
    echo   2. Download nssm-2.24.zip or later
    echo   3. Extract nssm.exe to: %NSSM_DIR%
    echo   4. Run this script again
    echo.
    pause
    exit /b 1
)

set "NSSM_EXE=%NSSM_DIR%\nssm.exe"
echo [OK] NSSM found: %NSSM_EXE%

REM 检查 Python
where python >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python not found!
    pause
    exit /b 1
)

REM 获取 venv 中 pythonw.exe 路径
set "PYTHONW_PATH=%BACKEND_DIR%\venv\Scripts\pythonw.exe"
if not exist "%PYTHONW_PATH%" (
    for /f "delims=" %%i in ('where python') do set "PYTHON_PATH=%%i"
    set "PYTHONW_PATH=!PYTHON_PATH:\python.exe=\pythonw.exe!"
)

if not exist "%PYTHONW_PATH%" (
    echo [ERROR] pythonw.exe not found!
    echo [INFO] Please ensure Python is installed correctly
    pause
    exit /b 1
)

echo.
echo [INFO] PythonW: %PYTHONW_PATH%
echo [INFO] Backend: %BACKEND_DIR%
echo.

REM 检查服务是否已存在
%NSSM_EXE% status %SERVICE_NAME% >nul 2>&1
if %errorLevel% equ 0 (
    echo [WARN] Service already exists!
    set /p REINSTALL="重新安装? (Y/N): "
    if /i "!REINSTALL!"=="Y" (
        echo [INFO] Stopping and removing old service...
        %NSSM_EXE% stop %SERVICE_NAME% >nul 2>&1
        timeout /t 2 /nobreak >nul
        %NSSM_EXE% remove %SERVICE_NAME% confirm >nul 2>&1
        timeout /t 2 /nobreak >nul
    ) else (
        echo [INFO] Installation cancelled
        pause
        exit /b 0
    )
)

echo.
echo [INFO] Installing service...
echo.

REM 安装服务
%NSSM_EXE% install %SERVICE_NAME% "%PYTHONW_PATH%" "service_runner.py"

if %errorLevel% neq 0 (
    echo [ERROR] Failed to install service!
    pause
    exit /b 1
)

REM 设置服务参数
%NSSM_EXE% set %SERVICE_NAME% AppDirectory "%BACKEND_DIR%"
%NSSM_EXE% set %SERVICE_NAME% AppStdout "%BACKEND_DIR%\logs\service_stdout.log"
%NSSM_EXE% set %SERVICE_NAME% AppStderr "%BACKEND_DIR%\logs\service_stderr.log"
%NSSM_EXE% set %SERVICE_NAME% DisplayName "Mini DB Query Service"
%NSSM_EXE% set %SERVICE_NAME% Description "多源数据查询服务 - 为微信小程序提供数据库查询API"
%NSSM_EXE% set %SERVICE_NAME% Start SERVICE_AUTO_START
%NSSM_EXE% set %SERVICE_NAME% AppRotateFiles 1
%NSSM_EXE% set %SERVICE_NAME% AppRotateBytes 10485760

echo [OK] Service installed successfully!
echo.
echo ============================================
echo   Service Information
echo ============================================
echo   Name: %SERVICE_NAME%
echo   Display: Mini DB Query Service
echo   Status: Installed
echo   Log: %BACKEND_DIR%\logs\
echo.
echo   Control Commands:
echo   - Start:   net start %SERVICE_NAME%
echo   - Stop:    net stop %SERVICE_NAME%
echo   - Status:  sc query %SERVICE_NAME%
echo   - Remove:  uninstall_nssm_service.bat
echo.
echo   Or use Windows Services (Win+R: services.msc)
echo ============================================
echo.

REM 询问是否立即启动
set /p START_NOW="是否立即启动服务? (Y/N): "
if /i "%START_NOW%"=="Y" (
    echo [INFO] Starting service...
    net start %SERVICE_NAME%
    timeout /t 3 /nobreak >nul
    
    echo [OK] Service started!
    echo [INFO] Opening browser...
    start http://localhost:26316/admin
)

echo.
pause

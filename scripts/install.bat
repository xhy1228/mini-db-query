@echo off
chcp 65001 >nul
REM ============================================
REM 多源数据查询小程序版 - Windows一键安装脚本
REM 版本: v1.0.0
REM ============================================

setlocal enabledelayedexpansion

REM 颜色定义
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "BLUE=[94m"
set "NC=[0m"

REM 项目目录
set "PROJECT_DIR=%~dp0.."
set "BACKEND_DIR=%PROJECT_DIR%\backend"
set "DATABASE_DIR=%PROJECT_DIR%\database"

echo.
echo %BLUE%============================================%NC%
echo %BLUE%   多源数据查询小程序版 - 安装向导%NC%
echo %BLUE%============================================%NC%
echo.

REM 检查管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo %YELLOW%提示: 建议以管理员身份运行此脚本%NC%
    echo.
)

REM ============================================
REM 步骤1: 检查Python环境
REM ============================================
echo %GREEN%[步骤1/7] 检查Python环境...%NC%

where python >nul 2>&1
if %errorLevel% equ 0 (
    for /f "tokens=2 delims= " %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo %GREEN%✓ 已安装 Python %PYTHON_VERSION%%NC%
    set PYTHON_CMD=python
    goto :python_found
)

where python3 >nul 2>&1
if %errorLevel% equ 0 (
    for /f "tokens=2 delims= " %%i in ('python3 --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo %GREEN%✓ 已安装 Python %PYTHON_VERSION%%NC%
    set PYTHON_CMD=python3
    goto :python_found
)

echo %YELLOW%! 未检测到Python，准备安装...%NC%
echo.

REM 下载并安装Python
set "PYTHON_URL=https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe"
set "PYTHON_INSTALLER=%TEMP%\python-installer.exe"

echo 正在下载 Python 3.12...
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_INSTALLER%'}"

if exist "%PYTHON_INSTALLER%" (
    echo 正在安装 Python...
    "%PYTHON_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
    echo %GREEN%✓ Python 安装完成%NC%
    set PYTHON_CMD=python
    REM 刷新环境变量
    call :refresh_path
) else (
    echo %RED%✗ Python 下载失败，请手动安装 Python 3.10+%NC%
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

:python_found
REM 验证Python版本
%PYTHON_CMD% -c "import sys; v=tuple(map(int,sys.version.split()[0].split('.'))); sys.exit(0 if v>=(3,10) else 1)"
if %errorLevel% neq 0 (
    echo %RED%✗ Python版本过低，需要 3.10 或更高版本%NC%
    pause
    exit /b 1
)

REM ============================================
REM 步骤2: 创建虚拟环境
REM ============================================
echo.
echo %GREEN%[步骤2/7] 创建Python虚拟环境...%NC%

cd /d "%BACKEND_DIR%"

if exist "venv" (
    echo %YELLOW%! 虚拟环境已存在，跳过创建%NC%
) else (
    %PYTHON_CMD% -m venv venv
    echo %GREEN%✓ 虚拟环境创建完成%NC%
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 升级pip
%PYTHON_CMD% -m pip install --upgrade pip -q

REM ============================================
REM 步骤3: 安装Python依赖
REM ============================================
echo.
echo %GREEN%[步骤3/7] 安装Python依赖包...%NC%

if exist "requirements.txt" (
    pip install -r requirements.txt -q
    echo %GREEN%✓ 依赖包安装完成%NC%
) else (
    echo %RED%✗ 未找到 requirements.txt%NC%
    pause
    exit /b 1
)

REM 安装额外依赖
pip install pymysql cryptography -q

REM ============================================
REM 步骤4: 检查MySQL服务
REM ============================================
echo.
echo %GREEN%[步骤4/7] 检查MySQL服务...%NC%

sc query MySQL80 >nul 2>&1
if %errorLevel% equ 0 (
    echo %GREEN%✓ 检测到 MySQL 8.0 服务%NC%
    goto :mysql_found
)

sc query MySQL >nul 2>&1
if %errorLevel% equ 0 (
    echo %GREEN%✓ 检测到 MySQL 服务%NC%
    goto :mysql_found
)

echo %YELLOW%! 未检测到MySQL服务%NC%
echo.
echo 请确保已安装 MySQL 8.0.2 或更高版本
echo 下载地址: https://dev.mysql.com/downloads/installer/
echo.
echo 安装MySQL后，请:
echo   1. 启动MySQL服务
echo   2. 记住root密码
echo   3. 重新运行此安装脚本
echo.

set /p MYSQL_CONTINUE="是否已完成MySQL安装并继续? (Y/N): "
if /i not "%MYSQL_CONTINUE%"=="Y" (
    echo %YELLOW%安装已暂停，请完成MySQL安装后重新运行%NC%
    pause
    exit /b 0
)

:mysql_found
REM ============================================
REM 步骤5: 配置数据库
REM ============================================
echo.
echo %GREEN%[步骤5/7] 配置数据库...%NC%

echo.
echo 请输入MySQL连接信息:
echo.

set /p MYSQL_HOST="MySQL主机地址 (默认: localhost): "
if "%MYSQL_HOST%"=="" set MYSQL_HOST=localhost

set /p MYSQL_PORT="MySQL端口 (默认: 3306): "
if "%MYSQL_PORT%"=="" set MYSQL_PORT=3306

set /p MYSQL_USER="MySQL用户名 (默认: root): "
if "%MYSQL_USER%"=="" set MYSQL_USER=root

set /p MYSQL_PASS="MySQL密码: "
if "%MYSQL_PASS%"=="" (
    echo %RED%密码不能为空%NC%
    pause
    exit /b 1
)

set /p MYSQL_DB="数据库名称 (默认: mini_db_query): "
if "%MYSQL_DB%"=="" set MYSQL_DB=mini_db_query

echo.
echo %BLUE%正在创建数据库和用户...%NC%

REM 创建数据库初始化SQL
set "INIT_SQL=%TEMP%\init_db.sql"

echo CREATE DATABASE IF NOT EXISTS `%MYSQL_DB%` DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci; > "%INIT_SQL%"
echo CREATE USER IF NOT EXISTS 'mini_query'@'localhost' IDENTIFIED BY 'MiniQuery@2026'; >> "%INIT_SQL%"
echo CREATE USER IF NOT EXISTS 'mini_query'@'%%' IDENTIFIED BY 'MiniQuery@2026'; >> "%INIT_SQL%"
echo GRANT ALL PRIVILEGES ON `%MYSQL_DB%`.* TO 'mini_query'@'localhost'; >> "%INIT_SQL%"
echo GRANT ALL PRIVILEGES ON `%MYSQL_DB%`.* TO 'mini_query'@'%%'; >> "%INIT_SQL%"
echo FLUSH PRIVILEGES; >> "%INIT_SQL%"

REM 执行SQL（需要mysql命令）
where mysql >nul 2>&1
if %errorLevel% equ 0 (
    mysql -h%MYSQL_HOST% -P%MYSQL_PORT% -u%MYSQL_USER% -p%MYSQL_PASS% < "%INIT_SQL%"
    echo %GREEN%✓ 数据库创建完成%NC%
) else (
    echo %YELLOW%! 未找到mysql命令，请手动执行以下SQL:%NC%
    type "%INIT_SQL%"
    echo.
)

REM 创建表结构
echo.
echo %BLUE%正在创建数据表...%NC%

if exist "%DATABASE_DIR%\mysql_schema.sql" (
    mysql -h%MYSQL_HOST% -P%MYSQL_PORT% -u%MYSQL_USER% -p%MYSQL_PASS% %MYSQL_DB% < "%DATABASE_DIR%\mysql_schema.sql" 2>nul
    echo %GREEN%✓ 数据表创建完成%NC%
)

REM ============================================
REM 步骤6: 创建配置文件
REM ============================================
echo.
echo %GREEN%[步骤6/7] 创建配置文件...%NC%

REM 生成JWT密钥
set JWT_SECRET=
for /f "delims=" %%i in ('python -c "import secrets; print(secrets.token_hex(32))"') do set JWT_SECRET=%%i

REM 创建.env文件
(
echo # 多源数据查询小程序版 - 配置文件
echo # 自动生成于 %date% %time%
echo.
echo # 数据库配置
echo DATABASE_URL=mysql+pymysql://mini_query:MiniQuery@2026@%MYSQL_HOST%:%MYSQL_PORT%/%MYSQL_DB%?charset=utf8mb4
echo.
echo # 微信小程序配置 (请修改为实际值)
echo WECHAT_APPID=your_wechat_appid
echo WECHAT_SECRET=your_wechat_secret
echo.
echo # JWT配置
echo JWT_SECRET_KEY=%JWT_SECRET%
echo JWT_EXPIRE_MINUTES=10080
echo.
echo # 服务配置
echo HOST=0.0.0.0
echo PORT=8000
echo DEBUG=False
) > ".env"

echo %GREEN%✓ 配置文件创建完成: backend\.env%NC%

REM ============================================
REM 步骤7: 创建快捷方式和服务
REM ============================================
echo.
echo %GREEN%[步骤7/7] 创建快捷方式...%NC%

REM 创建桌面快捷方式
set "SHORTCUT_PATH=%USERPROFILE%\Desktop\查询小程序服务.lnk"
powershell -Command "& {$ws=New-Object -ComObject WScript.Shell; $s=$ws.CreateShortcut('%SHORTCUT_PATH%'); $s.TargetPath='%BACKEND_DIR%\venv\Scripts\python.exe'; $s.Arguments='main.py'; $s.WorkingDirectory='%BACKEND_DIR%'; $s.Description='多源数据查询小程序服务'; $s.Save()}"

REM 创建启动脚本
(
echo @echo off
echo chcp 65001 ^>nul
echo cd /d "%BACKEND_DIR%"
echo call venv\Scripts\activate.bat
echo echo 启动服务中...
echo python main.py
echo pause
) > "%PROJECT_DIR%\scripts\start-service.bat"

REM 创建停止脚本
(
echo @echo off
echo echo 正在停止服务...
echo taskkill /f /im python.exe 2^>nul
echo echo 服务已停止
echo timeout /t 3
) > "%PROJECT_DIR%\scripts\stop-service.bat"

echo %GREEN%✓ 桌面快捷方式创建完成%NC%

REM ============================================
REM 安装完成
REM ============================================
echo.
echo %GREEN%============================================%NC%
echo %GREEN%   安装完成!%NC%
echo %GREEN%============================================%NC%
echo.
echo 数据库信息:
echo   数据库: %MYSQL_DB%
echo   用户名: mini_query
echo   密码:   MiniQuery@2026
echo.
echo 管理员账号:
echo   用户名: admin
echo   密码:   admin123
echo.
echo 启动方式:
echo   1. 双击桌面快捷方式 "查询小程序服务"
echo   2. 或运行 scripts\start-service.bat
echo.
echo 访问地址:
echo   API: http://localhost:8000
echo   文档: http://localhost:8000/docs
echo.
echo %YELLOW%重要提示:%NC%
echo   1. 请修改 backend\.env 中的微信小程序配置
echo   2. 请修改管理员密码
echo   3. 首次运行请确保MySQL服务已启动
echo.

REM 打开配置文件供编辑
set /p OPEN_CONFIG="是否打开配置文件进行编辑? (Y/N): "
if /i "%OPEN_CONFIG%"=="Y" (
    notepad ".env"
)

echo.
echo 按任意键启动服务...
pause >nul

REM 启动服务
cd /d "%BACKEND_DIR%"
call venv\Scripts\activate.bat
python main.py

exit /b 0

REM ============================================
REM 函数: 刷新环境变量
REM ============================================
:refresh_path
REM 从注册表重新读取PATH
for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul') do set "SYS_PATH=%%b"
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "USR_PATH=%%b"
set "PATH=%USR_PATH%;%SYS_PATH%"
goto :eof

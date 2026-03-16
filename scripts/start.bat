@echo off
chcp 65001 >nul
REM ============================================
REM 多源数据查询小程序版 - 启动脚本
REM ============================================

REM 获取项目目录
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."
set "BACKEND_DIR=%PROJECT_DIR%\backend"

cd /d "%BACKEND_DIR%"

REM 检查虚拟环境
if not exist "venv" (
    echo [WARN] 未找到虚拟环境，请先运行 install.bat 进行安装
    pause
    exit /b 1
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 检查.env文件
if not exist ".env" (
    echo [WARN] 未找到.env配置文件，使用默认配置
    if exist ".env.example" (
        copy .env.example .env
    )
)

echo.
echo ============================================
echo   多源数据查询小程序版 服务启动
echo ============================================
echo.
echo 项目目录: %BACKEND_DIR%
echo API地址: http://localhost:8000
echo 文档地址: http://localhost:8000/docs
echo.
echo 按 Ctrl+C 停止服务
echo.

REM 启动服务
python main.py

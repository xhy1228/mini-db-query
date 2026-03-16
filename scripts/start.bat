@echo off
chcp 65001 >nul
echo ============================================
echo   多源数据查询小程序 - 启动服务
echo ============================================
echo.

cd /d %~dp0\backend

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.10+
    pause
    exit /b 1
)

REM 检查依赖
echo [1/3] 检查依赖...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo [安装] 正在安装依赖...
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
)

REM 创建必要目录
echo [2/3] 创建必要目录...
if not exist "logs" mkdir logs
if not exist "exports" mkdir exports
if not exist "data" mkdir data

REM 启动服务
echo [3/3] 启动服务...
echo.
echo 服务地址: http://localhost:8000
echo API文档: http://localhost:8000/docs
echo.
python main.py

pause

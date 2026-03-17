@echo off
chcp 65001 >nul
REM ============================================
REM 多源数据查询小程序版 - 停止脚本
REM ============================================

echo [INFO] 正在停止多源数据查询服务...

REM 查找并停止Python进程
setlocal enabledelayedexpansion

REM 查找包含main.py的Python进程
for /f "tokens=2" %%i in ('tasklist ^| findstr "python.exe"') do (
    REM 检查该进程是否运行main.py
    wmic process where "ProcessId=%%i" get CommandLine 2>nul | findstr "main.py" >nul
    if !errorLevel! equ 0 (
        echo [INFO] 停止进程 PID: %%i
        taskkill /F /PID %%i >nul 2>&1
    )
)

REM 查找并停止uvicorn进程
for /f "tokens=2" %%i in ('tasklist ^| findstr "python.exe"') do (
    wmic process where "ProcessId=%%i" get CommandLine 2>nul | findstr "uvicorn" >nul
    if !errorLevel! equ 0 (
        echo [INFO] 停止uvicorn进程 PID: %%i
        taskkill /F /PID %%i >nul 2>&1
    )
)

echo [INFO] 服务已停止
timeout /t 3

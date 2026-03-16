@echo off
chcp 65001 >nul
echo ============================================
echo   多源数据查询小程序 - 安装为Windows服务
echo ============================================
echo.

cd /d %~dp0

REM 检查NSSM
nssm version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到NSSM，请先下载安装NSSM
    echo 下载地址: https://nssm.cc/download
    echo.
    echo 安装后请将nssm.exe放到系统PATH中或当前目录
    pause
    exit /b 1
)

REM 安装服务
echo [安装] 正在安装Windows服务...
nssm install MiniDbQuery "python" "main.py"
nssm set MiniDbQuery AppDirectory "%~dp0backend"
nssm set MiniDbQuery DisplayName "多源数据查询小程序服务"
nssm set MiniDbQuery Description "提供多源数据库查询API服务"
nssm set MiniDbQuery Start SERVICE_AUTO_START

echo.
echo [完成] 服务安装成功！
echo.
echo 管理命令:
echo   启动服务: nssm start MiniDbQuery
echo   停止服务: nssm stop MiniDbQuery
echo   重启服务: nssm restart MiniDbQuery
echo   卸载服务: nssm remove MiniDbQuery confirm
echo.

pause

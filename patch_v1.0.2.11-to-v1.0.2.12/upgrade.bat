@echo off
chcp 65001 >nul
title Mini DB Query 升级程序 v1.0.2.12

echo ========================================
echo   Mini DB Query 升级程序
echo   v1.0.2.11 -> v1.0.2.12
echo ========================================
echo.

echo [1/4] 备份当前文件...
if not exist "backend\api_backup" (
    xcopy /E /I /Y backend\api backend\api_backup >nul 2>&1
    echo      备份完成
) else (
    echo      已存在备份，跳过
)

echo.
echo [2/4] 升级后端文件...
xcopy /E /I /Y patch_v1.0.2.11-to-v1.0.2.12\backend\api backend\ >nul 2>&1
copy /Y patch_v1.0.2.11-to-v1.0.2.12\backend\version.py backend\ >nul 2>&1
echo      后端升级完成

echo.
echo [3/4] 升级管理后台...
xcopy /E /I /Y patch_v1.0.2.11-to-v1.0.2.12\backend\admin backend\admin\ >nul 2>&1
echo      管理后台升级完成

echo.
echo [4/4] 升级小程序...
xcopy /E /I /Y patch_v1.0.2.11-to-v1.0.2.12\miniapp\query miniapp\pages\query\ >nul 2>&1
echo      小程序升级完成

echo.
echo ========================================
echo   升级完成！
echo   请重启后端服务
echo ========================================
echo.
pause

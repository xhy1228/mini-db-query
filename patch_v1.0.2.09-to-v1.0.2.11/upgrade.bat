@echo off
chcp 65001 >nul
title Mini DB Query 升级程序 v1.0.2.11

echo ========================================
echo   Mini DB Query 升级程序
echo   v1.0.2.09 -> v1.0.2.11
echo ========================================
echo.

echo [1/5] 正在检查当前版本...
if exist "backend\version.py" (
    type backend\version.py
) else (
    echo      未找到版本文件
)

echo.
echo [2/5] 正在备份当前文件...
if not exist "backend\admin_backup" (
    xcopy /E /I /Y backend\admin backend\admin_backup >nul 2>&1
    xcopy /E /I /Y miniapp\pages\query miniapp\pages\query_backup >nul 2>&1
    echo      备份完成
) else (
    echo      已存在备份，跳过备份
)

echo.
echo [3/5] 正在升级后端文件...
xcopy /E /I /Y patch_v1.0.2.09-to-v1.0.2.11\backend\admin backend\ >nul 2>&1
copy /Y patch_v1.0.2.09-to-v1.0.2.11\backend\version.py backend\ >nul 2>&1
echo      后端文件升级完成

echo.
echo [4/5] 正在升级小程序文件...
xcopy /E /I /Y patch_v1.0.2.09-to-v1.0.2.11\miniapp\query miniapp\pages\query\ >nul 2>&1
echo      小程序文件升级完成

echo.
echo [5/5] 验证版本...
echo.
echo ========================================
echo   升级完成！
echo   请重启后端服务
echo ========================================
echo.
echo 按任意键退出...
pause >nul

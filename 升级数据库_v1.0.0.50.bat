@echo off
chcp 65001 >nul
echo ============================================
echo Mini DB Query - 数据库迁移工具
echo 版本: v1.0.0.50
echo ============================================
echo.

set /p DB_HOST="请输入数据库主机 (默认: localhost): "
if "%DB_HOST%"=="" set DB_HOST=localhost

set /p DB_PORT="请输入端口 (默认: 3306): "
if "%DB_PORT%"=="" set DB_PORT=3306

set /p DB_USER="请输入用户名 (默认: root): "
if "%DB_USER%"=="" set DB_USER=root

set /p DB_PASS="请输入密码: "
set /p DB_NAME="请输入数据库名 (默认: mini_db_query): "
if "%DB_NAME%"=="" set DB_NAME=mini_db_query

echo.
echo 正在执行数据库迁移...
echo.

mysql -h%DB_HOST% -P%DB_PORT% -u%DB_USER% -p%DB_PASS% %DB_NAME% < backend\migrations\v1.0.0.50_safe_migrate.sql

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================
    echo 迁移完成！
    echo ============================================
) else (
    echo.
    echo ============================================
    echo 迁移失败，请检查数据库连接信息
    echo ============================================
)

pause

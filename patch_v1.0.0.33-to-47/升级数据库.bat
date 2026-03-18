@echo off
chcp 65001 >nul
echo =============================================
echo 数据库升级脚本 v1.0.0.33 -^> v1.0.0.47
echo =============================================
echo.
echo 请确保MySQL服务已启动
echo.

set /p MYSQL_ROOT=请输入MySQL root密码: 

echo.
echo 正在执行数据库升级...
echo.

mysql -u root -p%MYSQL_ROOT% mini_db_query -e "ALTER TABLE query_logs ADD COLUMN error_detail JSON COMMENT '错误详情';" 2>nul

if %errorlevel% equ 0 (
    echo.
    echo =============================================
    echo 数据库升级成功！
    echo =============================================
) else (
    echo.
    echo =============================================
    echo 升级失败，请检查：
    echo 1. MySQL服务是否启动
    echo 2. 密码是否正确
    echo 3. 数据库 mini_db_query 是否存在
    echo =============================================
)

echo.
pause

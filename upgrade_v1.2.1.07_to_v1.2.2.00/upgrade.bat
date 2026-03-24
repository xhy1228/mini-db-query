@echo off
chcp 65001 >nul
echo ================================================
echo   升级包 v1.2.1.07 -> v1.2.2.00
echo ================================================
echo.

echo [1/3] 正在执行数据库升级...
echo.
mysql -u root -p123456 mini_db_query < scripts\upgrade_smart_template_v1.2.2.00.sql
if %errorlevel% neq 0 (
    echo 数据库升级失败，请检查错误
    pause
    exit /b 1
)
echo 数据库升级完成
echo.

echo [2/3] 正在备份旧文件...
if not exist backup mkdir backup
copy /Y backend\version.py backup\ >nul
copy /Y backend\admin\index.html backup\ >nul
copy /Y backend\api\auth.py backup\ >nul
copy /Y backend\api\manage.py backup\ >nul
copy /Y backend\api\query.py backup\ >nul
copy /Y backend\models\database.py backup\ >nul
copy /Y backend\services\log_service.py backup\ >nul
echo 备份完成
echo.

echo [3/3] 正在复制新文件...
copy /Y upgrade_v1.2.1.07_to_v1.2.2.00\version.py backend\ >nul
copy /Y upgrade_v1.2.1.07_to_v1.2.2.00\backend\index.html backend\admin\ >nul
copy /Y upgrade_v1.2.1.07_to_v1.2.2.00\backend\api\auth.py backend\api\ >nul
copy /Y upgrade_v1.2.1.07_to_v1.2.2.00\backend\api\manage.py backend\api\ >nul
copy /Y upgrade_v1.2.1.07_to_v1.2.2.00\backend\api\query.py backend\api\ >nul
copy /Y upgrade_v1.2.1.07_to_v1.2.2.00\backend\models\database.py backend\models\ >nul
copy /Y upgrade_v1.2.1.07_to_v1.2.2.00\backend\services\log_service.py backend\services\ >nul
echo 文件复制完成
echo.

echo ================================================
echo   升级完成！
echo   请重启后端服务使更改生效
echo ================================================
echo.
pause

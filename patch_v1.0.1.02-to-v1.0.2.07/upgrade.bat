@echo off
chcp 65001 >nul
echo ========================================
echo Mini DB Query 升级脚本
echo v1.0.1.02 -^> v1.0.2.07
echo ========================================
echo.

:: 检查备份
if not exist "backup_v1.0.1.02" (
    echo [警告] 未发现备份目录 backup_v1.0.1.02
    echo [建议] 请先备份当前程序和数据
    pause
)

:: 1. 备份当前版本
echo [步骤1] 备份当前文件...
if not exist "backup_v1.0.1.02" (
    mkdir backup_v1.0.1.02
    xcopy /E /I /Y backend backup_v1.0.1.02\backend >nul
    xcopy /E /I /Y miniapp backup_v1.0.1.02\miniapp >nul
    echo 备份完成
) else (
    echo 备份目录已存在，跳过备份
)

:: 2. 复制新文件
echo.
echo [步骤2] 更新文件...
xcopy /E /I /Y patch_v1.0.1.02-to-v1.0.2.07\backend backend >nul
xcopy /E /I /Y patch_v1.0.1.02-to-v1.0.2.07\miniapp miniapp >nul
echo 文件更新完成

:: 3. 创建必要目录
echo.
echo [步骤3] 创建必要目录...
if not exist "backend\.keys" mkdir backend\.keys
if not exist "backend\data" mkdir backend\data
if not exist "backend\logs" mkdir backend\logs
if not exist "exports" mkdir exports
echo 目录创建完成

:: 4. 数据库升级提示
echo.
echo [步骤4] 数据库升级
echo ========================================
echo 请手动执行数据库升级脚本:
echo.
echo mysql -u root -p mini_db_query ^< scripts\upgrade_v1.0.2.01.sql
echo.
echo 或使用 MySQL Workbench 执行:
echo scripts\upgrade_v1.0.2.01.sql
echo ========================================
echo.

:: 5. 完成
echo.
echo ========================================
echo 升级完成！
echo.
echo 版本: v1.0.2.07
echo.
echo 重要提示:
echo 1. 首次启动会自动生成JWT密钥
echo 2. DEBUG模式已默认关闭
echo 3. JWT有效期改为2小时
echo 4. 请执行数据库升级脚本
echo.
echo 启动命令: start.bat
echo ========================================
pause

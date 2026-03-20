@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

echo ========================================
echo Mini DB Query Upgrade Script
echo Version: v1.0.2.25 -> v1.0.2.28
echo ========================================
echo.

:: Check if running from project root
if not exist "backend" (
    echo [ERROR] Please run this script from project root directory!
    echo Expected structure:
    echo   project_root/
    echo   ├── backend/
    echo   ├── upgrade.bat
    echo   └── scripts/
    echo.
    pause
    exit /b 1
)

:: Check current version
echo [Step 1/5] Checking current version...
if exist "backend\version.py" (
    set /p CURRENT_VER=<backend\version.py
    echo Current version: !CURRENT_VER!
    if "!CURRENT_VER!"=="1.0.2.28" (
        echo Already at v1.0.2.28, no upgrade needed.
        pause
        exit /b 0
    )
) else (
    echo Version file not found, will create new one.
)

:: Confirm upgrade
echo.
echo [Step 2/5] Ready to upgrade to v1.0.2.28
echo.
echo Changes in this upgrade:
echo   - Fixed: User permission API path (404 error)
echo   - Fixed: User management API path
echo   - Fixed: Data serialization issues
echo   - Added: New database tables for v1.1.0
echo.
set /p CONFIRM="Continue? (Y/N): "
if /i not "!CONFIRM!"=="Y" (
    echo Upgrade cancelled.
    pause
    exit /b 0
)

:: Backup current files
echo.
echo [Step 3/5] Backing up files...
set BACKUP_DIR=backup_v1.0.2.28_%date:~0,4%%date:~5,2%%date:~8,2%
if not exist "!BACKUP_DIR!" mkdir "!BACKUP_DIR!"
if exist "backend\admin\index.html" (
    copy /Y "backend\admin\index.html" "!BACKUP_DIR!\index.html" >nul
    echo   - backend\admin\index.html backed up
)
if exist "backend\version.py" (
    copy /Y "backend\version.py" "!BACKUP_DIR!\version.py" >nul
    echo   - backend\version.py backed up
)
echo   Backup saved to: !BACKUP_DIR!\

:: Apply file updates
echo.
echo [Step 4/5] Applying file updates...
if exist "backend\version.py" (
    copy /Y "backend\version.py" "backend\version.py" >nul
    echo   - version.py updated
)
if exist "backend\admin\index.html" (
    copy /Y "backend\admin\index.html" "backend\admin\index.html" >nul
    echo   - admin\index.html updated
)
if exist "backend\api\categories.py" (
    copy /Y "backend\api\categories.py" "backend\api\categories.py" >nul 2>nul
    echo   - categories.py updated
)
if exist "backend\api\fields.py" (
    copy /Y "backend\api\fields.py" "backend\api\fields.py" >nul 2>nul
    echo   - fields.py updated
)
if exist "backend\api\permissions.py" (
    copy /Y "backend\api\permissions.py" "backend\api\permissions.py" >nul 2>nul
    echo   - permissions.py updated
)
if exist "backend\db\query_executor.py" (
    copy /Y "backend\db\query_executor.py" "backend\db\query_executor.py" >nul 2>nul
    echo   - query_executor.py updated
)
if exist "backend\models\database.py" (
    copy /Y "backend\models\database.py" "backend\models\database.py" >nul 2>nul
    echo   - database.py updated
)
if exist "backend\services\user_service.py" (
    copy /Y "backend\services\user_service.py" "backend\services\user_service.py" >nul 2>nul
    echo   - user_service.py updated
)

echo.
echo ========================================
echo File upgrade completed!
echo ========================================
echo.

:: Database upgrade
echo [Step 5/5] Database Upgrade Required!
echo.
echo Please run the database upgrade script:
echo   Option 1: scripts\upgrade_database.sql
echo.
echo Command example:
echo   mysql -h 118.195.172.93 -P 3306 -u root -p mini_db_query ^< scripts\upgrade_database.sql
echo.
echo Note: You need MySQL client installed.
echo.

set /p RUN_DB_NOW="Run database upgrade now? (Y/N): "
if /i "!RUN_DB_NOW!"=="Y" (
    echo.
    echo Running database upgrade...
    mysql -h 118.195.172.93 -P 3306 -u root -p mini_db_query < scripts\upgrade_database.sql
    if !errorlevel! equ 0 (
        echo.
        echo Database upgrade completed successfully!
    ) else (
        echo.
        echo Database upgrade failed. Please run manually.
    )
)

echo.
echo ========================================
echo Upgrade process completed!
echo ========================================
echo.
echo Please RESTART the backend service now.
echo.
pause

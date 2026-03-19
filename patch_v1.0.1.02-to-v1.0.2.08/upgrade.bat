@echo off
chcp 65001 >nul
echo ========================================
echo Mini DB Query Upgrade Script
echo v1.0.1.02 -^> v1.0.2.08
echo ========================================
echo.

:: Step 1: Backup
echo [Step 1] Backing up...
if not exist "backup_v1.0.1.02" (
    mkdir backup_v1.0.1.02
    xcopy /E /I /Y backend backup_v1.0.1.02\backend >nul
    xcopy /E /I /Y miniapp backup_v1.0.1.02\miniapp >nul
    echo Backup completed
) else (
    echo Backup directory exists, skipping
)

:: Step 2: Copy new files
echo.
echo [Step 2] Updating files...
if exist "patch_v1.0.1.02-to-v1.0.2.08\backend" (
    xcopy /E /I /Y patch_v1.0.1.02-to-v1.0.2.08\backend backend >nul
)
if exist "patch_v1.0.1.02-to-v1.0.2.08\miniapp" (
    xcopy /E /I /Y patch_v1.0.1.02-to-v1.0.2.08\miniapp miniapp >nul
)
echo Files updated

:: Step 3: Create directories
echo.
echo [Step 3] Creating directories...
if not exist "backend\.keys" mkdir backend\.keys
if not exist "backend\data" mkdir backend\data
if not exist "backend\logs" mkdir backend\logs
if not exist "exports" mkdir exports
echo Directories created

:: Step 4: Database upgrade
echo.
echo [Step 4] Database upgrade required!
echo ========================================
echo Please run this command manually:
echo.
echo   mysql -u root -p mini_db_query ^< scripts\upgrade_v1.0.2.01.sql
echo.
echo Or use MySQL Workbench to execute:
echo   scripts\upgrade_v1.0.2.01.sql
echo ========================================
echo.

:: Step 5: Done
echo.
echo ========================================
echo Upgrade completed!
echo.
echo Version: v1.0.2.08
echo.
echo Important notes:
echo   1. JWT key will be generated on first start
echo   2. DEBUG mode is disabled by default
echo   3. JWT token expires in 2 hours
echo   4. Run database upgrade script
echo.
echo Start command: start.bat
echo ========================================
pause

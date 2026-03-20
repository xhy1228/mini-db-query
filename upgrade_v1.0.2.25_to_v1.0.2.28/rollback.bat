@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

echo ========================================
echo Mini DB Query Rollback Script
echo ========================================
echo.

:: Check if backup exists
set BACKUP_DIR=
for /f "delims=" %%i in ('dir /b /ad backup_v1.0.2.28_* 2^>nul') do set BACKUP_DIR=%%i

if "!BACKUP_DIR!"=="" (
    echo [ERROR] No backup found!
    echo Please backup files manually before upgrading.
    pause
    exit /b 1
)

echo Found backup: !BACKUP_DIR!
echo.

:: Confirm rollback
set /p CONFIRM="Continue with rollback? (Y/N): "
if /i not "!CONFIRM!"=="Y" (
    echo Rollback cancelled.
    pause
    exit /b 0
)

:: Restore files
echo Restoring files...
if exist "!BACKUP_DIR!\index.html" (
    copy /Y "!BACKUP_DIR!\index.html" "backend\admin\index.html" >nul
    echo   - backend\admin\index.html restored
)
if exist "!BACKUP_DIR!\version.py" (
    copy /Y "!BACKUP_DIR!\version.py" "backend\version.py" >nul
    echo   - backend\version.py restored
)

echo.
echo ========================================
echo Rollback completed!
echo ========================================
echo.
echo Please RESTART the backend service.
echo.
pause

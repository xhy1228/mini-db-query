@echo off
REM Mini DB Query - Root Install Script
REM This script calls the actual installer in scripts folder

title Mini DB Query - Installer

echo.
echo ============================================
echo    Mini DB Query - Installation
echo ============================================
echo.

REM Check Python first
echo Checking Python...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo [ERROR] Python not found!
    echo.
    echo Please install Python 3.10+ from:
    echo   https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo Python found. Starting installation...
echo.

REM Run the actual installer
cd /d "%~dp0scripts"
call install.bat

pause

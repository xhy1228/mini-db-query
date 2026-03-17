@echo off
REM Mini DB Query - Start Server

cd /d "%~dp0backend"

if not exist "venv" (
    echo [ERROR] Virtual environment not found!
    echo Please run install.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
python main.py

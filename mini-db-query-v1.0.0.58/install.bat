@echo off
REM ============================================
REM Mini DB Query - Install Dependencies
REM ============================================

echo Installing dependencies...
echo.

cd backend

pip install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Installation failed!
    pause
    exit /b 1
)

echo.
echo Installation completed!
echo Run start.bat to start the server.
echo.
pause

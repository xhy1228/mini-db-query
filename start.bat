@echo off
REM ============================================
REM Mini DB Query - Start Server
REM ============================================

cd backend

echo Starting server...
echo Port: 26316
echo URL: http://localhost:26316
echo.

python main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Failed to start server!
    pause
)

@echo off
echo ============================================
echo Database Check Tool
echo ============================================
echo.

set /p DB_HOST="Host (default: localhost): "
if "%DB_HOST%"=="" set DB_HOST=localhost

set /p DB_PORT="Port (default: 3306): "
if "%DB_PORT%"=="" set DB_PORT=3306

set /p DB_USER="User (default: root): "
if "%DB_USER%"=="" set DB_USER=root

set /p DB_PASS="Password: "
set /p DB_NAME="Database (default: mini_db_query): "
if "%DB_NAME%"=="" set DB_NAME=mini_db_query

echo.
echo Checking users table...
echo.

mysql -h%DB_HOST% -P%DB_PORT% -u%DB_USER% -p%DB_PASS% %DB_NAME% -e "SHOW COLUMNS FROM users;"

echo.
echo ============================================
echo Done!
echo ============================================
pause

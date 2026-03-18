@echo off
echo ============================================
echo Database Fix Tool v1.0.0.50
echo ============================================
echo.

set DB_HOST=localhost
set DB_PORT=3306
set DB_USER=root
set DB_PASS=
set DB_NAME=mini_db_query

if not "%1"=="" set DB_HOST=%1
if not "%2"=="" set DB_PORT=%2
if not "%3"=="" set DB_USER=%3
if not "%4"=="" set DB_PASS=%4
if not "%5"=="" set DB_NAME=%5

echo Host: %DB_HOST%
echo Port: %DB_PORT%
echo User: %DB_USER%
echo Database: %DB_NAME%
echo.
echo Running database fix...
echo.

mysql -h%DB_HOST% -P%DB_PORT% -u%DB_USER% -p%DB_PASS% %DB_NAME% < fix_database.sql

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================
    echo Fix completed successfully!
    echo ============================================
) else (
    echo.
    echo ============================================
    echo Fix failed! Please check:
    echo 1. MySQL is running
    echo 2. Database credentials are correct
    echo 3. Database '%DB_NAME%' exists
    echo ============================================
)

pause

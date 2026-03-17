-- Mini DB Query - MySQL Database Initialization
-- MySQL 8.0.2+ Required
-- 
-- Usage:
--   mysql -u root -p < init_database.sql
--
-- Or in MySQL console:
--   source /path/to/init_database.sql

-- Create database
CREATE DATABASE IF NOT EXISTS mini_db_query 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- Use database
USE mini_db_query;

-- Grant permissions (modify username and password as needed)
-- CREATE USER IF NOT EXISTS 'miniquery'@'localhost' IDENTIFIED BY 'your_password';
-- GRANT ALL PRIVILEGES ON mini_db_query.* TO 'miniquery'@'localhost';
-- FLUSH PRIVILEGES;

-- Show success message
SELECT 'Database mini_db_query created successfully!' AS Message;
SELECT 'Now configure your .env file with the connection details.' AS NextStep;

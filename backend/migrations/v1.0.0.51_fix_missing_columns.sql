-- ============================================
-- One-Click Fix Script for users table
-- Safe to run multiple times
-- ============================================

-- Check and add missing columns
SET @dbname = DATABASE();
SET @tablename = 'users';

-- Add openid column if not exists
SET @columnname = 'openid';
SET @preparedStatement = (SELECT IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = @columnname) > 0,
  'SELECT "Column openid already exists" AS message',
  'ALTER TABLE users ADD COLUMN openid VARCHAR(100) UNIQUE COMMENT "微信openid"'
));
PREPARE stmt FROM @preparedStatement;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add unionid column if not exists
SET @columnname = 'unionid';
SET @preparedStatement = (SELECT IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = @columnname) > 0,
  'SELECT "Column unionid already exists" AS message',
  'ALTER TABLE users ADD COLUMN unionid VARCHAR(100) UNIQUE COMMENT "微信unionid"'
));
PREPARE stmt FROM @preparedStatement;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add id_card column if not exists
SET @columnname = 'id_card';
SET @preparedStatement = (SELECT IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = @columnname) > 0,
  'SELECT "Column id_card already exists" AS message',
  'ALTER TABLE users ADD COLUMN id_card VARCHAR(255) COMMENT "身份证号(加密)"'
));
PREPARE stmt FROM @preparedStatement;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add avatar column if not exists
SET @columnname = 'avatar';
SET @preparedStatement = (SELECT IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = @columnname) > 0,
  'SELECT "Column avatar already exists" AS message',
  'ALTER TABLE users ADD COLUMN avatar VARCHAR(500) COMMENT "头像URL"'
));
PREPARE stmt FROM @preparedStatement;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add error_detail to query_logs if not exists
SET @tablename = 'query_logs';
SET @columnname = 'error_detail';
SET @preparedStatement = (SELECT IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = @columnname) > 0,
  'SELECT "Column error_detail already exists" AS message',
  'ALTER TABLE query_logs ADD COLUMN error_detail JSON COMMENT "错误详情"'
));
PREPARE stmt FROM @preparedStatement;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Show result
SELECT '=== users table columns ===' AS info;
SHOW COLUMNS FROM users;

SELECT '=== query_logs table columns ===' AS info;
SHOW COLUMNS FROM query_logs;

SELECT '=== Fix completed! ===' AS info;

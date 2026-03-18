-- ============================================
-- 数据库迁移脚本
-- 版本: v1.0.0.50
-- 日期: 2026-03-18
-- 说明: 修复 users 表字段缺失问题（安全版本）
-- 使用方法: 逐条执行，忽略已存在的错误
-- ============================================

-- 使用存储过程安全添加字段
DELIMITER //

DROP PROCEDURE IF EXISTS add_column_if_not_exists //

CREATE PROCEDURE add_column_if_not_exists(
    IN table_name_param VARCHAR(100),
    IN column_name_param VARCHAR(100),
    IN column_definition VARCHAR(500)
)
BEGIN
    DECLARE column_exists INT DEFAULT 0;
    
    SELECT COUNT(*) INTO column_exists
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = table_name_param
      AND COLUMN_NAME = column_name_param;
    
    IF column_exists = 0 THEN
        SET @sql = CONCAT('ALTER TABLE ', table_name_param, ' ADD COLUMN ', column_name_param, ' ', column_definition);
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
        SELECT CONCAT('已添加字段: ', column_name_param) AS result;
    ELSE
        SELECT CONCAT('字段已存在: ', column_name_param) AS result;
    END IF;
END //

DELIMITER ;

-- 执行迁移
CALL add_column_if_not_exists('users', 'openid', "VARCHAR(100) UNIQUE COMMENT '微信openid'");
CALL add_column_if_not_exists('users', 'unionid', "VARCHAR(100) UNIQUE COMMENT '微信unionid'");
CALL add_column_if_not_exists('users', 'id_card', "VARCHAR(255) COMMENT '身份证号(加密)'");
CALL add_column_if_not_exists('users', 'avatar', "VARCHAR(500) COMMENT '头像URL'");
CALL add_column_if_not_exists('query_logs', 'error_detail', "JSON COMMENT '错误详情'");

-- 清理存储过程
DROP PROCEDURE IF EXISTS add_column_if_not_exists;

-- 验证
SELECT 'users 表字段:' AS info;
SHOW COLUMNS FROM users;

SELECT 'query_logs 表字段:' AS info;
SHOW COLUMNS FROM query_logs;

-- =====================================================
-- v1.2.0.04 修复: system_configs 表缺失字段
-- 执行时间: 2026-03-21
-- =====================================================

-- 添加 display_name 字段 (忽略如果已存在)
-- 使用 MariaDB 语法或 MySQL 8.0+ 语法
-- 方法1: 使用存储过程
DROP PROCEDURE IF EXISTS add_column_if_not_exists;
DELIMITER //
CREATE PROCEDURE add_column_if_not_exists()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = DATABASE() 
        AND TABLE_NAME = 'system_configs' 
        AND COLUMN_NAME = 'display_name'
    ) THEN
        ALTER TABLE system_configs ADD COLUMN display_name VARCHAR(100) NULL COMMENT '显示名称';
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = DATABASE() 
        AND TABLE_NAME = 'system_configs' 
        AND COLUMN_NAME = 'description'
    ) THEN
        ALTER TABLE system_configs ADD COLUMN description TEXT NULL COMMENT '描述';
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = DATABASE() 
        AND TABLE_NAME = 'system_configs' 
        AND COLUMN_NAME = 'category'
    ) THEN
        ALTER TABLE system_configs ADD COLUMN category VARCHAR(50) DEFAULT 'system' COMMENT '分类: wechat/system/security';
    END IF;
END //
DELIMITER ;

-- 执行存储过程
CALL add_column_if_not_exists();

-- 删除存储过程
DROP PROCEDURE IF EXISTS add_column_if_not_exists;

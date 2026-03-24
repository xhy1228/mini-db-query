-- ============================================
-- 智能模板配置升级 - v1.2.2.00
-- 功能：获取表/字段、字段别名、脱敏配置
-- ============================================

-- 1. query_fields 表扩展
-- ============================================

-- 检查并添加 display_name 字段
-- 注意：MySQL 不支持 ADD COLUMN IF NOT EXISTS，使用存储过程处理
DROP PROCEDURE IF EXISTS add_column_if_not_exists;
DELIMITER //
CREATE PROCEDURE add_column_if_not_exists()
BEGIN
    -- display_name: 显示名称(别名)
    IF NOT EXISTS (SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'query_fields' AND COLUMN_NAME = 'display_name') THEN
        ALTER TABLE query_fields ADD COLUMN display_name VARCHAR(100) COMMENT '显示名称(别名)';
    END IF;
    
    -- show_in_list: 列表是否显示
    IF NOT EXISTS (SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'query_fields' AND COLUMN_NAME = 'show_in_list') THEN
        ALTER TABLE query_fields ADD COLUMN show_in_list TINYINT DEFAULT 1 COMMENT '列表是否显示: 0否/1是';
    END IF;
    
    -- need_mask: 脱敏模式
    IF NOT EXISTS (SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'query_fields' AND COLUMN_NAME = 'need_mask') THEN
        ALTER TABLE query_fields ADD COLUMN need_mask TINYINT DEFAULT 0 COMMENT '脱敏模式: 0自动/1强制/2不脱敏';
    END IF;
    
    -- mask_type: 脱敏类型
    IF NOT EXISTS (SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'query_fields' AND COLUMN_NAME = 'mask_type') THEN
        ALTER TABLE query_fields ADD COLUMN mask_type VARCHAR(20) COMMENT '脱敏类型: phone/id_card/bank_card/email/name';
    END IF;
END //
DELIMITER ;

CALL add_column_if_not_exists();
DROP PROCEDURE IF EXISTS add_column_if_not_exists;

-- 2. 更新版本号
-- ============================================
INSERT INTO system_configs (config_key, config_value, description) 
VALUES ('version', 'v1.2.2.01', '智能模板配置版本')
ON DUPLICATE KEY UPDATE config_value = 'v1.2.2.00';

SELECT '智能模板配置升级完成!' as result;

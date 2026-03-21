-- Mini DB Query v1.2.0.03 修复脚本
-- 修复测试发现的问题
-- 执行时间: 2026-03-21

-- 1. template_categories 表 - is_system 字段
SET @column_exists = (SELECT COUNT(*) FROM information_schema.columns 
WHERE table_schema = DATABASE() AND table_name = 'template_categories' AND column_name = 'is_system');

SET @sql = IF(@column_exists = 0, 
    'ALTER TABLE template_categories ADD COLUMN is_system TINYINT DEFAULT 0 COMMENT ''是否系统预置:1是 0否''', 
    'SELECT ''is_system 字段已存在''');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 2. query_logs 表 - binding_id 字段 (v1.2.0新增)
SET @log_col_exists = (SELECT COUNT(*) FROM information_schema.columns 
WHERE table_schema = DATABASE() AND table_name = 'query_logs' AND column_name = 'binding_id');

SET @log_sql = IF(@log_col_exists = 0, 
    'ALTER TABLE query_logs ADD COLUMN binding_id INT COMMENT ''绑定ID''', 
    'SELECT ''binding_id 字段已存在''');

PREPARE log_stmt FROM @log_sql;
EXECUTE log_stmt;
DEALLOCATE PREPARE log_stmt;

-- 3. 插入默认系统配置（如果不存在）
INSERT INTO system_configs (config_key, config_value, config_type, display_name, description, category)
SELECT 'site_name', 'Mini DB Query', 'text', '站点名称', '系统站点名称', 'system'
WHERE NOT EXISTS (SELECT 1 FROM system_configs WHERE config_key = 'site_name');

INSERT INTO system_configs (config_key, config_value, config_type, display_name, description, category)
SELECT 'site_logo', '', 'text', '站点Logo', '系统站点Logo URL', 'system'
WHERE NOT EXISTS (SELECT 1 FROM system_configs WHERE config_key = 'site_logo');

INSERT INTO system_configs (config_key, config_value, config_type, display_name, description, category)
SELECT 'wechat_appid', '', 'secret', '小程序AppID', '微信小程序AppID', 'wechat'
WHERE NOT EXISTS (SELECT 1 FROM system_configs WHERE config_key = 'wechat_appid');

INSERT INTO system_configs (config_key, config_value, config_type, display_name, description, category)
SELECT 'wechat_secret', '', 'secret', '小程序密钥', '微信小程序密钥', 'wechat'
WHERE NOT EXISTS (SELECT 1 FROM system_configs WHERE config_key = 'wechat_secret');

SELECT '修复完成' as message;

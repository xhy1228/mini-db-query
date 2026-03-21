-- Mini DB Query v1.2.0.03 修复脚本
-- 修复测试发现的问题
-- 执行时间: 2026-03-21

-- 1. 检查 template_categories 表结构
-- 如果 is_system 字段不存在则添加
SET @column_exists = (SELECT COUNT(*) FROM information_schema.columns 
WHERE table_schema = DATABASE() AND table_name = 'template_categories' AND column_name = 'is_system');

SET @sql = IF(@column_exists = 0, 
    'ALTER TABLE template_categories ADD COLUMN is_system TINYINT DEFAULT 0 COMMENT ''是否系统预置:1是 0否''', 
    'SELECT ''is_system 字段已存在''');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SELECT '修复完成' as message;

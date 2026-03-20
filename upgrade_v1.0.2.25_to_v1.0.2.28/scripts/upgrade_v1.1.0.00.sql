-- ============================================
-- Mini DB Query - Database Upgrade Script
-- Version: v1.1.0.00
-- Description: 数据结构优化 - 业务大类/查询条件/模板关联/版本控制
-- Date: 2026-03-19
-- ============================================

USE mini_db_query;

-- ============================================
-- 1. 创建业务大类表 (template_categories)
-- ============================================
CREATE TABLE IF NOT EXISTS `template_categories` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '主键',
    `school_id` INT NOT NULL COMMENT '学校ID',
    `code` VARCHAR(50) NOT NULL COMMENT '业务大类编码',
    `name` VARCHAR(100) NOT NULL COMMENT '业务大类名称',
    `icon` VARCHAR(50) COMMENT '图标',
    `sort_order` INT DEFAULT 0 COMMENT '排序',
    `description` TEXT COMMENT '描述',
    `status` VARCHAR(20) DEFAULT 'active' COMMENT '状态',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_school_category` (`school_id`, `code`),
    KEY `idx_school_id` (`school_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='业务大类表';

-- ============================================
-- 2. 创建查询条件表 (query_fields)
-- ============================================
CREATE TABLE IF NOT EXISTS `query_fields` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '主键',
    `template_id` INT NOT NULL COMMENT '模板ID',
    `field_key` VARCHAR(50) NOT NULL COMMENT '字段标识',
    `field_label` VARCHAR(100) NOT NULL COMMENT '字段名称',
    `field_type` VARCHAR(20) DEFAULT 'text' COMMENT '字段类型: text/number/date/select',
    `db_column` VARCHAR(100) COMMENT '数据库列名',
    `operator` VARCHAR(20) DEFAULT '=' COMMENT '操作符: =/LIKE/>/</>=/<=/IN',
    `default_value` VARCHAR(255) COMMENT '默认值',
    `options` JSON COMMENT '选项(select类型)',
    `required` TINYINT(1) DEFAULT 0 COMMENT '是否必填',
    `sort_order` INT DEFAULT 0 COMMENT '排序',
    `placeholder` VARCHAR(200) COMMENT '提示文字',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_template_field` (`template_id`, `field_key`),
    KEY `idx_template_id` (`template_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='查询条件表';

-- ============================================
-- 3. 修改查询模板表 (query_templates)
-- 添加: database_id, category_id, version, description
-- ============================================
ALTER TABLE `query_templates` 
    ADD COLUMN IF NOT EXISTS `database_id` INT COMMENT '数据库配置ID' AFTER `school_id`,
    ADD COLUMN IF NOT EXISTS `category_id` INT COMMENT '业务大类ID' AFTER `category`,
    ADD COLUMN IF NOT EXISTS `version` VARCHAR(20) DEFAULT 'v1.0.0' COMMENT '版本号' AFTER `default_limit`,
    ADD COLUMN IF NOT EXISTS `change_log` TEXT COMMENT '变更日志' AFTER `version`;

ALTER TABLE `query_templates` 
    ADD INDEX IF NOT EXISTS `idx_database_id` (`database_id`),
    ADD INDEX IF NOT EXISTS `idx_category_id` (`category_id`);

-- ============================================
-- 4. 创建模板历史表 (query_template_history)
-- ============================================
CREATE TABLE IF NOT EXISTS `query_template_history` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '主键',
    `template_id` INT NOT NULL COMMENT '模板ID',
    `version` VARCHAR(20) NOT NULL COMMENT '版本号',
    `name` VARCHAR(100) COMMENT '查询名称',
    `description` TEXT COMMENT '描述',
    `sql_template` TEXT COMMENT 'SQL模板',
    `fields` JSON COMMENT '查询字段配置',
    `change_log` TEXT COMMENT '变更日志',
    `changed_by` INT COMMENT '修改人ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_template_id` (`template_id`),
    KEY `idx_version` (`version`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='模板历史表';

-- ============================================
-- 5. 创建模板权限表 (template_permissions)
-- ============================================
CREATE TABLE IF NOT EXISTS `template_permissions` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '主键',
    `user_id` INT NOT NULL COMMENT '用户ID',
    `template_id` INT NOT NULL COMMENT '模板ID',
    `can_query` TINYINT(1) DEFAULT 1 COMMENT '可查询',
    `can_export` TINYINT(1) DEFAULT 0 COMMENT '可导出',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '授权时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_template` (`user_id`, `template_id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_template_id` (`template_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='模板权限表';

-- ============================================
-- 6. 迁移现有数据: 业务大类
-- ============================================
INSERT INTO `template_categories` (`school_id`, `code`, `name`, `icon`, `sort_order`, `status`)
SELECT DISTINCT 
    school_id, 
    category AS code, 
    MAX(category_name) AS name, 
    MAX(category_icon) AS icon,
    CASE category 
        WHEN 'student' THEN 1 
        WHEN 'consume' THEN 2 
        WHEN 'access' THEN 3 
        WHEN 'wechat' THEN 4 
        ELSE 5 
    END AS sort_order,
    'active' AS status
FROM `query_templates`
GROUP BY school_id, category
ON DUPLICATE KEY UPDATE name = VALUES(name), icon = VALUES(icon);

-- ============================================
-- 7. 更新模板表: 关联业务大类ID
-- ============================================
UPDATE `query_templates` t
JOIN `template_categories` c ON t.school_id = c.school_id AND t.category = c.code
SET t.category_id = c.id;

-- ============================================
-- 8. 迁移现有数据: 查询条件 (从 fields JSON 迁移到独立表)
-- ============================================
-- 注意: 需要通过程序处理, 这里仅创建示例结构
-- 实际迁移在 Python 代码中执行

-- ============================================
-- 9. 更新用户权限表: 添加模板级权限字段
-- ============================================
ALTER TABLE `user_schools`
    ADD COLUMN IF NOT EXISTS `template_permissions` JSON COMMENT '模板权限详情';

-- ============================================
-- Verification
-- ============================================
SELECT 'Upgrade completed!' AS status;
SHOW TABLES;

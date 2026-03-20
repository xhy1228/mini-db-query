-- ============================================================
-- 智能查询功能重构 v1.2.0 - 数据库升级脚本
-- 创建时间: 2026-03-20
-- 说明: 创建学校-模板绑定表，调整模板表结构
-- ============================================================

-- 0. 设置事务和错误处理
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================
-- 1. 创建 school_template_bindings 表
-- ============================================================
DROP TABLE IF EXISTS school_template_bindings;

CREATE TABLE school_template_bindings (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    school_id INT NOT NULL COMMENT '学校ID',
    template_id INT NOT NULL COMMENT '模板ID',
    database_id INT NOT NULL COMMENT '使用的数据库ID',
    enabled TINYINT DEFAULT 1 COMMENT '是否启用：1启用 0禁用',
    custom_name VARCHAR(100) NULL COMMENT '自定义名称(可选)',
    sort_order INT DEFAULT 0 COMMENT '排序',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE CASCADE,
    FOREIGN KEY (template_id) REFERENCES query_templates(id) ON DELETE CASCADE,
    FOREIGN KEY (database_id) REFERENCES database_configs(id) ON DELETE CASCADE,
    UNIQUE KEY uk_school_template (school_id, template_id),
    INDEX idx_school_id (school_id),
    INDEX idx_template_id (template_id),
    INDEX idx_database_id (database_id),
    INDEX idx_enabled (enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='学校-模板绑定表';

-- ============================================================
-- 2. 为 query_templates 添加 supported_db_types 字段
-- ============================================================
-- 检查字段是否存在，不存在则添加
-- ALTER TABLE query_templates ADD COLUMN supported_db_types JSON NULL COMMENT '支持的数据库类型：["MySQL", "Oracle"]' AFTER default_limit;

-- 3. 从 query_templates 移除旧的关联字段（如果存在）
-- 注意：这些字段在 v1.1.0 中可能已添加，如果存在则移除
-- ALTER TABLE query_templates DROP COLUMN IF EXISTS school_id;
-- ALTER TABLE query_templates DROP COLUMN IF EXISTS database_id;
-- ALTER TABLE query_templates DROP COLUMN IF EXISTS category_id;

-- ============================================================
-- 4. 迁移现有数据到绑定表
-- 说明: 将现有的 query_templates 按学校关系迁移到 school_template_bindings
-- 注意: 此迁移假设原有模板按 school_id 区分学校
-- ============================================================

-- 4.1 检查是否有需要迁移的数据
-- SELECT COUNT(*) as template_count, school_id FROM query_templates WHERE school_id IS NOT NULL GROUP BY school_id;

-- 4.2 如果有学校关联的模板，迁移到绑定表
-- 注意: 需要先为每个学校创建一个默认数据库配置，这里只是示例
-- INSERT INTO school_template_bindings (school_id, template_id, database_id, enabled)
-- SELECT t.school_id, t.id, 
--        (SELECT id FROM database_configs WHERE school_id = t.school_id LIMIT 1) as database_id,
--        1
-- FROM query_templates t
-- WHERE t.school_id IS NOT NULL;

-- ============================================================
-- 5. 添加业务大类字段（可选，保留用于兼容）
-- 为 template_categories 表添加额外字段
-- ============================================================
-- ALTER TABLE template_categories ADD COLUMN is_system TINYINT DEFAULT 0 COMMENT '是否系统预置：1是 0否' AFTER status;

-- ============================================================
-- 6. 重建 query_templates 表（如果需要完全重建）
-- 注意: 仅在新安装时执行，或在确认数据已迁移后执行
-- ============================================================

-- 由于需要保持兼容性，这里不直接删除字段
-- 如果是全新安装，使用以下完整表结构

-- ============================================================
-- 7. 验证表结构
-- ============================================================
-- SHOW CREATE TABLE school_template_bindings;
-- SHOW CREATE TABLE query_templates;

-- ============================================================
-- 8. 插入默认业务大类（如果不存在）
-- ============================================================
INSERT IGNORE INTO template_categories (school_id, code, name, icon, sort_order, description, status)
VALUES 
(0, 'consume', '消费业务', '💰', 1, '消费记录查询相关功能', 'active'),
(0, 'access', '门禁业务', '🚪', 2, '门禁进出记录查询相关功能', 'active'),
(0, 'wechat', '微信业务', '💬', 3, '微信绑定等查询相关功能', 'active'),
(0, 'student', '学生业务', '🎓', 4, '学生信息查询相关功能', 'active'),
(0, 'recharge', '充值业务', '💳', 5, '充值记录查询相关功能', 'active');

-- ============================================================
-- 9. 设置外键检查
-- ============================================================
SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================
-- 执行完成提示
-- ============================================================
SELECT '✅ v1.2.0 升级脚本执行完成' as message;
SELECT '📋 school_template_bindings 表已创建' as table_status;
SELECT '📋 请检查 query_templates 表结构' as next_step;

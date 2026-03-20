-- ============================================
-- Mini DB Query 数据库升级脚本
-- 版本: v1.0.2.25 -> v1.0.2.28
-- 日期: 2026-03-20
-- ============================================

-- 检查当前版本
SELECT '当前数据库版本检查...' as step;

-- ============================================
-- 1. 为 query_templates 表添加新字段
-- ============================================
SELECT '添加 query_templates 表新字段...' as step;

-- 添加 database_id 字段（数据库配置ID）
ALTER TABLE query_templates 
ADD COLUMN IF NOT EXISTS database_id INT DEFAULT NULL 
COMMENT '数据库配置ID' 
AFTER school_id;

-- 添加 category_id 字段（业务大类ID）
ALTER TABLE query_templates 
ADD COLUMN IF NOT EXISTS category_id INT DEFAULT NULL 
COMMENT '业务大类ID' 
AFTER database_id;

-- 添加 version 字段（版本号）
ALTER TABLE query_templates 
ADD COLUMN IF NOT EXISTS version VARCHAR(20) DEFAULT '1.0.0' 
COMMENT '版本号' 
AFTER default_limit;

-- 添加 change_log 字段（变更日志）
ALTER TABLE query_templates 
ADD COLUMN IF NOT EXISTS change_log TEXT 
COMMENT '变更日志' 
AFTER version;

-- ============================================
-- 2. 创建业务大类表（如果不存在）
-- ============================================
SELECT '创建业务大类表...' as step;

CREATE TABLE IF NOT EXISTS template_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    school_id INT NOT NULL COMMENT '学校ID',
    code VARCHAR(50) NOT NULL COMMENT '分类编码',
    name VARCHAR(100) NOT NULL COMMENT '分类名称',
    icon VARCHAR(20) DEFAULT '📋' COMMENT '图标',
    sort_order INT DEFAULT 0 COMMENT '排序',
    description TEXT COMMENT '描述',
    status VARCHAR(20) DEFAULT 'active' COMMENT '状态',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_school_code (school_id, code),
    KEY idx_school_id (school_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='业务大类表';

-- ============================================
-- 3. 创建查询条件表（如果不存在）
-- ============================================
SELECT '创建查询条件表...' as step;

CREATE TABLE IF NOT EXISTS query_fields (
    id INT AUTO_INCREMENT PRIMARY KEY,
    template_id INT NOT NULL COMMENT '模板ID',
    field_key VARCHAR(50) NOT NULL COMMENT '字段标识',
    field_label VARCHAR(100) NOT NULL COMMENT '字段名称',
    field_type VARCHAR(20) DEFAULT 'text' COMMENT '字段类型(text/select/date/datetime/number)',
    db_column VARCHAR(100) COMMENT '数据库列名',
    operator VARCHAR(20) DEFAULT '=' COMMENT '操作符(=/like/</>/between)',
    default_value VARCHAR(255) COMMENT '默认值',
    options JSON COMMENT '选项(select类型用)',
    required TINYINT DEFAULT 0 COMMENT '是否必填',
    sort_order INT DEFAULT 0 COMMENT '排序',
    placeholder VARCHAR(200) COMMENT '提示文字',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    KEY idx_template_id (template_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='查询条件表';

-- ============================================
-- 4. 创建模板历史表（如果不存在）
-- ============================================
SELECT '创建模板历史表...' as step;

CREATE TABLE IF NOT EXISTS query_template_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    template_id INT NOT NULL COMMENT '模板ID',
    version VARCHAR(20) NOT NULL COMMENT '版本号',
    sql_template TEXT NOT NULL COMMENT 'SQL模板',
    change_log TEXT COMMENT '变更日志',
    created_by INT COMMENT '创建者ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    KEY idx_template_id (template_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='模板历史表';

-- ============================================
-- 5. 创建模板权限表（如果不存在）
-- ============================================
SELECT '创建模板权限表...' as step;

CREATE TABLE IF NOT EXISTS template_permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    template_id INT NOT NULL COMMENT '模板ID',
    user_id INT NOT NULL COMMENT '用户ID',
    can_query TINYINT DEFAULT 1 COMMENT '是否可查询',
    can_export TINYINT DEFAULT 0 COMMENT '是否可导出',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_template_user (template_id, user_id),
    KEY idx_user_id (user_id),
    KEY idx_template_id (template_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='模板权限表';

-- ============================================
-- 6. 更新 users 表添加权限字段
-- ============================================
SELECT '更新 users 表...' as step;

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS template_permissions JSON 
COMMENT '模板权限JSON' 
AFTER role;

-- ============================================
-- 7. 初始化默认业务大类数据
-- ============================================
SELECT '初始化业务大类数据...' as step;

-- 消费业务
INSERT IGNORE INTO template_categories (school_id, code, name, icon, sort_order) 
SELECT s.id, 'consume', '消费业务', '💰', 1 FROM schools s;

-- 门禁业务
INSERT IGNORE INTO template_categories (school_id, code, name, icon, sort_order) 
SELECT s.id, 'access', '门禁业务', '🚪', 2 FROM schools s;

-- 微信业务
INSERT IGNORE INTO template_categories (school_id, code, name, icon, sort_order) 
SELECT s.id, 'wechat', '微信业务', '💬', 3 FROM schools s;

-- 学生业务
INSERT IGNORE INTO template_categories (school_id, code, name, icon, sort_order) 
SELECT s.id, 'student', '学生业务', '🎓', 4 FROM schools s;

-- ============================================
-- 8. 为已有模板设置 category_id
-- ============================================
SELECT '更新模板分类...' as step;

UPDATE query_templates qt 
SET qt.category_id = (
    SELECT tc.id FROM template_categories tc 
    WHERE tc.school_id = qt.school_id AND tc.code = qt.category
    LIMIT 1
)
WHERE qt.category_id IS NULL 
AND qt.category IS NOT NULL
AND EXISTS (
    SELECT 1 FROM template_categories tc 
    WHERE tc.school_id = qt.school_id AND tc.code = qt.category
);

-- ============================================
-- 升级完成
-- ============================================
SELECT '========================================' as '';
SELECT '数据库升级完成！' as result;
SELECT '版本: v1.0.2.25 -> v1.0.2.28' as version;
SELECT '========================================' as '';

-- 显示新增表结构
SELECT '新增表:' as info;
SELECT TABLE_NAME, TABLE_COMMENT 
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = DATABASE() 
AND TABLE_NAME IN ('template_categories', 'query_fields', 'query_template_history', 'template_permissions');

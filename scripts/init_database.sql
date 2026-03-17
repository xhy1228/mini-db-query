-- ============================================
-- Mini DB Query - Database Initialization Script
-- Version: v1.0.0.18
-- MySQL 8.0.2+ Required
-- ============================================

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS mini_db_query 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

USE mini_db_query;

-- ============================================
-- Table: schools (学校/项目表)
-- ============================================
CREATE TABLE IF NOT EXISTS `schools` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '主键',
    `name` VARCHAR(100) NOT NULL COMMENT '学校名称',
    `code` VARCHAR(50) NOT NULL COMMENT '学校编码',
    `description` TEXT COMMENT '描述',
    `status` VARCHAR(20) DEFAULT 'active' COMMENT '状态: active/inactive',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_schools_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='学校/项目表';

-- ============================================
-- Table: database_configs (数据库配置表)
-- ============================================
CREATE TABLE IF NOT EXISTS `database_configs` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '主键',
    `school_id` INT NOT NULL COMMENT '学校ID',
    `name` VARCHAR(100) NOT NULL COMMENT '配置名称',
    `db_type` VARCHAR(50) NOT NULL COMMENT '数据库类型',
    `host` VARCHAR(255) NOT NULL COMMENT '主机地址',
    `port` INT NOT NULL COMMENT '端口',
    `username` VARCHAR(100) NOT NULL COMMENT '用户名',
    `password` TEXT NOT NULL COMMENT '密码(加密)',
    `database` VARCHAR(100) COMMENT '数据库名',
    `service_name` VARCHAR(100) COMMENT 'Oracle服务名',
    `driver` VARCHAR(100) COMMENT 'ODBC驱动',
    `description` TEXT COMMENT '描述',
    `status` VARCHAR(20) DEFAULT 'active' COMMENT '状态',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_school_id` (`school_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据库配置表';

-- ============================================
-- Table: query_templates (查询模板表)
-- ============================================
CREATE TABLE IF NOT EXISTS `query_templates` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '主键',
    `school_id` INT NOT NULL COMMENT '学校ID',
    `category` VARCHAR(50) NOT NULL COMMENT '业务大类',
    `category_name` VARCHAR(100) COMMENT '业务大类名称',
    `category_icon` VARCHAR(20) COMMENT '业务大类图标',
    `name` VARCHAR(100) NOT NULL COMMENT '查询名称',
    `description` TEXT COMMENT '描述',
    `sql_template` TEXT NOT NULL COMMENT 'SQL模板',
    `fields` JSON COMMENT '查询字段配置',
    `time_field` VARCHAR(100) COMMENT '时间字段',
    `default_limit` INT DEFAULT 500 COMMENT '默认条数限制',
    `status` VARCHAR(20) DEFAULT 'active' COMMENT '状态',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_school_id` (`school_id`),
    KEY `idx_category` (`category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='查询模板表';

-- ============================================
-- Table: users (用户表)
-- ============================================
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '主键',
    `phone` VARCHAR(20) NOT NULL COMMENT '手机号(登录账号)',
    `password` VARCHAR(255) NOT NULL COMMENT '密码(加密)',
    `name` VARCHAR(100) NOT NULL COMMENT '姓名',
    `id_card` VARCHAR(255) COMMENT '身份证号(加密)',
    `role` VARCHAR(20) DEFAULT 'user' COMMENT '角色: admin/user',
    `status` VARCHAR(20) DEFAULT 'active' COMMENT '状态',
    `last_login` DATETIME COMMENT '最后登录时间',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_users_phone` (`phone`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- ============================================
-- Table: user_schools (用户学校权限表)
-- ============================================
CREATE TABLE IF NOT EXISTS `user_schools` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '主键',
    `user_id` INT NOT NULL COMMENT '用户ID',
    `school_id` INT NOT NULL COMMENT '学校ID',
    `permissions` JSON COMMENT '权限列表',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '授权时间',
    PRIMARY KEY (`id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_school_id` (`school_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户学校权限表';

-- ============================================
-- Table: query_logs (查询日志表)
-- ============================================
CREATE TABLE IF NOT EXISTS `query_logs` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '主键',
    `user_id` INT COMMENT '用户ID',
    `username` VARCHAR(50) COMMENT '用户名',
    `school_id` INT COMMENT '学校ID',
    `template_id` INT COMMENT '模板ID',
    `query_name` VARCHAR(200) COMMENT '查询名称',
    `query_type` VARCHAR(50) COMMENT '查询类型: smart_sql/direct_sql/template',
    `query_params` JSON COMMENT '查询参数',
    `database_id` INT COMMENT '数据库配置ID',
    `database_name` VARCHAR(100) COMMENT '数据库名称',
    `sql_executed` TEXT COMMENT '执行的SQL',
    `sql_content` TEXT COMMENT 'SQL内容',
    `parameters` JSON COMMENT '查询参数(新)',
    `result_count` INT DEFAULT 0 COMMENT '结果条数',
    `query_time` INT COMMENT '查询耗时(ms)',
    `execution_time_ms` INT COMMENT '执行时间(毫秒)',
    `status` VARCHAR(20) DEFAULT 'success' COMMENT '状态: success/failed',
    `error_message` TEXT COMMENT '错误信息',
    `ip_address` VARCHAR(50) COMMENT 'IP地址',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_school_id` (`school_id`),
    KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='查询日志表';

-- ============================================
-- Default Data: Schools
-- ============================================
INSERT INTO `schools` (`name`, `code`, `description`, `status`) VALUES
('示例学校A', 'SCHOOL_A', '示例学校A的数据库查询系统', 'active'),
('示例学校B', 'SCHOOL_B', '示例学校B的数据库查询系统', 'active');

-- ============================================
-- Default Data: Admin User
-- Password: 123456 (hashed)
-- ============================================
-- 注意: 密码使用 bcrypt 加密，这里是 123456 的加密结果
-- 实际密码需要在程序中通过 get_password_hash('123456') 生成
INSERT INTO `users` (`phone`, `password`, `name`, `id_card`, `role`, `status`) VALUES
('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7y.VRV6vW2', '超级管理员', NULL, 'admin', 'active'),
('13800138000', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7y.VRV6vW2', '张三', NULL, 'user', 'active'),
('13900139000', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7y.VRV6vW2', '李四', NULL, 'user', 'active');

-- ============================================
-- Default Data: User School Permissions
-- ============================================
INSERT INTO `user_schools` (`user_id`, `school_id`, `permissions`) VALUES
(1, 1, '["admin", "query", "config"]'),
(1, 2, '["admin", "query", "config"]'),
(2, 1, '["query"]'),
(3, 1, '["query"]'),
(3, 2, '["query"]');

-- ============================================
-- Default Data: Query Templates (示例)
-- ============================================
INSERT INTO `query_templates` (`school_id`, `category`, `category_name`, `category_icon`, `name`, `description`, `sql_template`, `fields`, `time_field`, `default_limit`, `status`) VALUES
(1, 'student', '学生业务', '🎓', '学生信息查询', '查询学生基本信息', 
 'SELECT CUSTNAME as 姓名, STUDENTID as 学号, IDCARD as 身份证号 FROM CARD_CUSTOMERS WHERE 1=1', 
 '[{"id": "name", "label": "姓名", "column": "CUSTNAME", "type": "text", "operator": "LIKE"}, {"id": "student_id", "label": "学号", "column": "STUDENTID", "type": "text", "operator": "="}]', 
 NULL, 100, 'active'),

(1, 'consume', '消费业务', '💰', '消费明细查询', '查询消费流水明细', 
 'SELECT CARDID as 卡号, TRANAMT as 金额, TRATIME as 时间 FROM DATA_CARD_CONSUME WHERE 1=1', 
 '[{"id": "card_id", "label": "卡号", "column": "CARDID", "type": "text", "operator": "="}]', 
 'TRATIME', 500, 'active'),

(1, 'consume', '消费业务', '💰', '充值明细查询', '查询充值流水明细', 
 'SELECT CARDID as 卡号, CASH as 金额, CASH_TIME as 时间 FROM DATA_ONLINE_CASH WHERE 1=1', 
 '[{"id": "card_id", "label": "卡号", "column": "CARDID", "type": "text", "operator": "="}]', 
 'CASH_TIME', 500, 'active'),

(1, 'access', '门禁业务', '🚪', '门禁记录查询', '查询门禁进出记录', 
 'SELECT CARDID as 卡号, INOUTTIME as 时间, DEVICENAME as 设备 FROM ACCESS_INOUT_RECORD WHERE 1=1', 
 '[{"id": "card_id", "label": "卡号", "column": "CARDID", "type": "text", "operator": "="}]', 
 'INOUTTIME', 500, 'active'),

(1, 'wechat', '微信业务', '💬', '微信绑定查询', '查询微信用户绑定信息', 
 'SELECT user_no, user_name, phone, wechat_openid, bind_time FROM wx_user WHERE 1=1', 
 '[{"id": "user_no", "label": "用户编号", "column": "user_no", "type": "text", "operator": "="}, {"id": "phone", "label": "手机号", "column": "phone", "type": "text", "operator": "="}]', 
 'bind_time', 100, 'active');

-- ============================================
-- Verification
-- ============================================
SELECT 'Tables created successfully!' as status;
SHOW TABLES;

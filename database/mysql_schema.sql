-- ============================================
-- 多源数据查询小程序版 - MySQL 数据库架构
-- 版本: v1.0.0
-- 兼容: MySQL 8.0.2+
-- 字符集: utf8mb4
-- ============================================

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS mini_db_query 
    DEFAULT CHARACTER SET utf8mb4 
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE mini_db_query;

-- ============================================
-- 学校/项目表
-- ============================================
CREATE TABLE IF NOT EXISTS schools (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    name VARCHAR(100) NOT NULL COMMENT '学校名称',
    code VARCHAR(50) NOT NULL COMMENT '学校编码',
    description TEXT COMMENT '描述',
    status VARCHAR(20) DEFAULT 'active' COMMENT '状态: active/inactive',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    UNIQUE KEY uk_code (code),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='学校/项目表';

-- ============================================
-- 数据库配置表
-- ============================================
CREATE TABLE IF NOT EXISTS database_configs (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    school_id INT NOT NULL COMMENT '学校ID',
    name VARCHAR(100) NOT NULL COMMENT '配置名称',
    db_type VARCHAR(50) NOT NULL COMMENT '数据库类型: MySQL/Oracle/SQLServer',
    host VARCHAR(255) NOT NULL COMMENT '主机地址',
    port INT NOT NULL COMMENT '端口',
    username VARCHAR(100) NOT NULL COMMENT '用户名',
    password TEXT NOT NULL COMMENT '密码(加密存储)',
    database VARCHAR(100) COMMENT '数据库名',
    service_name VARCHAR(100) COMMENT 'Oracle服务名',
    driver VARCHAR(100) COMMENT 'ODBC驱动',
    description TEXT COMMENT '描述',
    status VARCHAR(20) DEFAULT 'active' COMMENT '状态: active/inactive',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_school_id (school_id),
    INDEX idx_db_type (db_type),
    INDEX idx_status (status),
    
    CONSTRAINT fk_db_config_school FOREIGN KEY (school_id) 
        REFERENCES schools(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据库配置表';

-- ============================================
-- 查询模板表
-- ============================================
CREATE TABLE IF NOT EXISTS query_templates (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    school_id INT NOT NULL COMMENT '学校ID',
    category VARCHAR(50) NOT NULL COMMENT '业务大类编码',
    category_name VARCHAR(100) COMMENT '业务大类名称',
    category_icon VARCHAR(20) COMMENT '业务大类图标',
    name VARCHAR(100) NOT NULL COMMENT '查询名称',
    description TEXT COMMENT '描述',
    sql_template TEXT NOT NULL COMMENT 'SQL模板',
    fields JSON COMMENT '查询字段配置',
    time_field VARCHAR(100) COMMENT '时间字段',
    default_limit INT DEFAULT 500 COMMENT '默认条数限制',
    status VARCHAR(20) DEFAULT 'active' COMMENT '状态: active/inactive',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_school_id (school_id),
    INDEX idx_category (category),
    INDEX idx_status (status),
    
    CONSTRAINT fk_template_school FOREIGN KEY (school_id) 
        REFERENCES schools(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='查询模板表';

-- ============================================
-- 用户表
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    phone VARCHAR(20) NOT NULL COMMENT '手机号(登录账号)',
    password VARCHAR(255) NOT NULL COMMENT '密码(加密存储)',
    name VARCHAR(100) NOT NULL COMMENT '姓名',
    id_card VARCHAR(255) COMMENT '身份证号(加密存储)',
    role VARCHAR(20) DEFAULT 'user' COMMENT '角色: admin/user',
    status VARCHAR(20) DEFAULT 'active' COMMENT '状态: active/inactive/locked',
    last_login DATETIME COMMENT '最后登录时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    UNIQUE KEY uk_phone (phone),
    INDEX idx_role (role),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- ============================================
-- 用户学校权限表
-- ============================================
CREATE TABLE IF NOT EXISTS user_schools (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    user_id INT NOT NULL COMMENT '用户ID',
    school_id INT NOT NULL COMMENT '学校ID',
    permissions JSON COMMENT '权限列表',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '授权时间',
    
    UNIQUE KEY uk_user_school (user_id, school_id),
    INDEX idx_user_id (user_id),
    INDEX idx_school_id (school_id),
    
    CONSTRAINT fk_user_school_user FOREIGN KEY (user_id) 
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_user_school_school FOREIGN KEY (school_id) 
        REFERENCES schools(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户学校权限表';

-- ============================================
-- 查询日志表
-- ============================================
CREATE TABLE IF NOT EXISTS query_logs (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    user_id INT NOT NULL COMMENT '用户ID',
    school_id INT COMMENT '学校ID',
    template_id INT COMMENT '模板ID',
    query_name VARCHAR(200) COMMENT '查询名称',
    query_params JSON COMMENT '查询参数',
    sql_executed TEXT COMMENT '执行的SQL',
    result_count INT DEFAULT 0 COMMENT '结果条数',
    query_time INT COMMENT '查询耗时(毫秒)',
    status VARCHAR(20) DEFAULT 'success' COMMENT '状态: success/failed',
    error_message TEXT COMMENT '错误信息',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    INDEX idx_user_id (user_id),
    INDEX idx_school_id (school_id),
    INDEX idx_template_id (template_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    
    CONSTRAINT fk_log_user FOREIGN KEY (user_id) 
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_log_school FOREIGN KEY (school_id) 
        REFERENCES schools(id) ON DELETE SET NULL,
    CONSTRAINT fk_log_template FOREIGN KEY (template_id) 
        REFERENCES query_templates(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='查询日志表';

-- ============================================
-- 系统配置表
-- ============================================
CREATE TABLE IF NOT EXISTS system_configs (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    config_key VARCHAR(100) NOT NULL COMMENT '配置键',
    config_value TEXT COMMENT '配置值',
    config_type VARCHAR(50) DEFAULT 'string' COMMENT '配置类型: string/number/json/boolean',
    description VARCHAR(255) COMMENT '描述',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    UNIQUE KEY uk_config_key (config_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统配置表';

-- ============================================
-- 初始数据
-- ============================================

-- 插入默认系统配置
INSERT INTO system_configs (config_key, config_value, config_type, description) VALUES
('jwt_expire_minutes', '10080', 'number', 'JWT Token有效期(分钟), 默认7天'),
('query_timeout', '30', 'number', '查询超时时间(秒)'),
('max_export_rows', '10000', 'number', '最大导出行数'),
('system_name', '多源数据查询小程序', 'string', '系统名称'),
('system_version', '1.0.0', 'string', '系统版本')
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- ============================================
-- 创建视图
-- ============================================

-- 用户权限视图
CREATE OR REPLACE VIEW v_user_permissions AS
SELECT 
    u.id AS user_id,
    u.phone,
    u.name AS user_name,
    u.role,
    s.id AS school_id,
    s.name AS school_name,
    s.code AS school_code,
    us.permissions
FROM users u
LEFT JOIN user_schools us ON u.id = us.user_id
LEFT JOIN schools s ON us.school_id = s.id
WHERE u.status = 'active';

-- 查询统计视图
CREATE OR REPLACE VIEW v_query_statistics AS
SELECT 
    DATE(created_at) AS query_date,
    school_id,
    COUNT(*) AS total_queries,
    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS success_count,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_count,
    AVG(query_time) AS avg_query_time,
    SUM(result_count) AS total_result_count
FROM query_logs
GROUP BY DATE(created_at), school_id;

-- ============================================
-- 存储过程
-- ============================================

DELIMITER //

-- 清理过期日志存储过程
CREATE PROCEDURE sp_clean_old_logs(IN days_to_keep INT)
BEGIN
    DELETE FROM query_logs 
    WHERE created_at < DATE_SUB(NOW(), INTERVAL days_to_keep DAY);
    SELECT ROW_COUNT() AS deleted_rows;
END //

-- 创建管理员用户存储过程
CREATE PROCEDURE sp_create_admin(
    IN p_phone VARCHAR(20),
    IN p_password VARCHAR(255),
    IN p_name VARCHAR(100)
)
BEGIN
    INSERT INTO users (phone, password, name, role, status)
    VALUES (p_phone, p_password, p_name, 'admin', 'active')
    ON DUPLICATE KEY UPDATE 
        password = p_password,
        name = p_name,
        status = 'active';
    SELECT LAST_INSERT_ID() AS user_id;
END //

DELIMITER ;

-- ============================================
-- 索引优化建议
-- ============================================
-- 对于大数据量场景，可考虑以下优化:
-- 1. query_logs 表按时间分区
-- 2. 为常用查询条件添加复合索引
-- 3. 考虑使用全文索引优化搜索

-- 完成
SELECT 'MySQL Schema initialized successfully!' AS message;

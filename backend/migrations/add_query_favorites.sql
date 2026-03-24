-- 常用查询收藏功能 v1.2.2.02
-- 添加查询收藏表
-- 执行时间: 2026-03-25

-- 创建收藏表
CREATE TABLE IF NOT EXISTS query_favorites (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID',
    binding_id INT COMMENT '功能绑定ID',
    template_id INT COMMENT '模板ID',
    school_id INT COMMENT '学校ID',
    query_name VARCHAR(200) COMMENT '收藏名称',
    query_params JSON COMMENT '查询参数(条件)',
    start_time VARCHAR(20) COMMENT '开始时间',
    end_time VARCHAR(20) COMMENT '结束时间',
    sort_fields VARCHAR(500) COMMENT '排序字段',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_user_id (user_id),
    INDEX idx_binding_id (binding_id),
    INDEX idx_template_id (template_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='查询收藏表';

-- 添加字段说明
ALTER TABLE query_favorites 
    MODIFY COLUMN query_params JSON COMMENT '查询参数(条件)';

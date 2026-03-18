-- =============================================
-- 数据库升级脚本 v1.0.0.33 → v1.0.0.47
-- 执行方法: 直接在MySQL中执行以下SQL
-- =============================================

-- 为 query_logs 表添加 error_detail 字段
ALTER TABLE query_logs ADD COLUMN error_detail JSON COMMENT '错误详情: 包含error_type, error_message, sql, suggestion等';

-- 执行完成后检查字段是否添加成功
-- SHOW COLUMNS FROM query_logs LIKE 'error_detail';

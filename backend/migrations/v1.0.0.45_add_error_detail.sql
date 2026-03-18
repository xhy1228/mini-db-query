-- 数据库迁移脚本
-- 版本: v1.0.0.45
-- 日期: 2026-03-18
-- 说明: 为 query_logs 表添加 error_detail 字段，用于记录详细错误信息

-- 添加 error_detail 字段（JSON类型，存储完整错误详情）
ALTER TABLE query_logs ADD COLUMN error_detail JSON COMMENT '错误详情: 包含error_type, error_message, sql, suggestion等';

-- 如果上面的语句执行失败（MySQL版本不支持JSON），可以使用TEXT类型
-- ALTER TABLE query_logs ADD COLUMN error_detail TEXT COMMENT '错误详情';

-- 为 query_templates 表添加 table_name 字段
-- 如果字段已存在会报错，忽略即可

ALTER TABLE query_templates ADD COLUMN table_name VARCHAR(100) COMMENT '查询表名';

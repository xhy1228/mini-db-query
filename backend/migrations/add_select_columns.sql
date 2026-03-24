-- 添加 select_columns 字段到 query_templates 表
-- 执行时间: 2026-03-24

ALTER TABLE query_templates ADD COLUMN select_columns JSON COMMENT '返回字段配置 [{"column": "CUSTNAME", "alias": "姓名"}, ...]' AFTER sql_template;

-- 如果执行报错（字段已存在），忽略即可

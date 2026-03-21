-- Mini DB Query v1.2.0.03 修复脚本
-- 修复测试发现的问题
-- 执行时间: 2026-03-21

SET NAMES utf8mb4;

-- 1. 修复 template_categories 表缺少 is_system 字段
-- 使用判断避免重复添加报错
ALTER TABLE template_categories ADD COLUMN is_system TINYINT DEFAULT 0 COMMENT '是否系统预置:1是 0否';

SELECT '修复完成' as message;

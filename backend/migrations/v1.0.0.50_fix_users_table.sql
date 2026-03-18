-- ============================================
-- 数据库迁移脚本
-- 版本: v1.0.0.50
-- 日期: 2026-03-18
-- 说明: 修复 users 表字段缺失问题
-- ============================================

-- 1. 为 users 表添加 openid 字段（如果不存在）
ALTER TABLE users ADD COLUMN openid VARCHAR(100) UNIQUE COMMENT '微信openid';

-- 2. 为 users 表添加 unionid 字段（如果不存在）
ALTER TABLE users ADD COLUMN unionid VARCHAR(100) UNIQUE COMMENT '微信unionid';

-- 3. 为 users 表添加 id_card 字段（如果不存在）
ALTER TABLE users ADD COLUMN id_card VARCHAR(255) COMMENT '身份证号(加密)';

-- 4. 为 query_logs 表添加 error_detail 字段（如果不存在）
-- 注意：执行前先检查表中是否已有该字段
-- ALTER TABLE query_logs ADD COLUMN error_detail JSON COMMENT '错误详情';

-- ============================================
-- 验证迁移结果
-- ============================================
-- 执行以下SQL验证字段是否添加成功：
-- SHOW COLUMNS FROM users LIKE 'openid';
-- SHOW COLUMNS FROM users LIKE 'unionid';
-- SHOW COLUMNS FROM users LIKE 'id_card';

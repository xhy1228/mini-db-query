-- ============================================
-- Upgrade Script: v1.0.1.10 -> v1.0.2.01
-- Query Templates for WeChat System
-- ============================================

-- Add WeChat query templates to template library (school_id=1)
-- Note: If school_id=1 does not exist, create it first

-- Ensure template library school exists
INSERT INTO `schools` (`id`, `name`, `code`, `description`, `status`) 
VALUES (1, 'Template Library', 'TEMPLATE_LIB', 'System preset query template library', 'active')
ON DUPLICATE KEY UPDATE `name` = VALUES(`name`);

-- ========== WeChat System Templates ==========

-- 1. Student Full Info Query
INSERT INTO `query_templates` (`school_id`, `category`, `category_name`, `category_icon`, `name`, `description`, `sql_template`, `fields`, `time_field`, `default_limit`, `status`)
VALUES (
    1, 
    'wechat', 
    'WeChat Business', 
    'wechat', 
    'Student Full Info Query', 
    'Query student full info by student_id/name/id_card (includes class, teacher, dorm)',
    'SELECT u.name AS name, u.id_card AS id_card, u.user_number AS student_id, d.dept_name AS class_name, tu.name AS teacher_name, CASE WHEN rb.id IS NOT NULL THEN "checked_in" ELSE "not_checked_in" END AS dorm_status, a1.name AS building, a2.name AS floor, r.room_name AS room, rb.bed_name AS bed FROM sys_user u LEFT JOIN sys_dept d ON u.dept_id = d.dept_id LEFT JOIN sys_user_dept sud ON d.dept_id = sud.dept_id AND sud.header_teacher = 1 LEFT JOIN sys_user tu ON sud.user_id = tu.user_id LEFT JOIN wx_room_bed rb ON rb.user_id = u.user_id LEFT JOIN wx_room r ON rb.room_id = r.room_id LEFT JOIN wx_address a1 ON r.address_parent_id = a1.id LEFT JOIN wx_address a2 ON r.address_id = a2.id WHERE u.user_number = {keyword} OR u.name = {keyword} OR u.id_card = {keyword}',
    '[{"id": "keyword", "label": "Student ID/Name/ID Card", "column": "keyword", "type": "text", "operator": "="}]',
    NULL, 
    100, 
    'active'
) ON DUPLICATE KEY UPDATE `sql_template` = VALUES(`sql_template`);

-- 2. Door Access Record Query
INSERT INTO `query_templates` (`school_id`, `category`, `category_name`, `category_icon`, `name`, `description`, `sql_template`, `fields`, `time_field`, `default_limit`, `status`)
VALUES (
    1, 
    'wechat', 
    'WeChat Business', 
    'wechat', 
    'Door Access Record Query', 
    'Query door access records (sign_type: 0=in, 1=out)',
    'SELECT user_no AS student_id, CASE sign_type WHEN 0 THEN "in" WHEN 1 THEN "out" END AS access_type, device_name AS device, record_time AS access_time FROM m_user_door_record_info WHERE user_no = {user_no}',
    '[{"id": "user_no", "label": "Student ID", "column": "user_no", "type": "text", "operator": "="}]',
    'record_time', 
    500, 
    'active'
) ON DUPLICATE KEY UPDATE `sql_template` = VALUES(`sql_template`);

-- 3. Teacher Query
INSERT INTO `query_templates` (`school_id`, `category`, `category_name`, `category_icon`, `name`, `description`, `sql_template`, `fields`, `time_field`, `default_limit`, `status`)
VALUES (
    1, 
    'wechat', 
    'WeChat Business', 
    'wechat', 
    'Teacher Query', 
    'Query all homeroom teachers',
    'SELECT u.name AS name, u.user_number AS employee_id, d.dept_name AS class_name FROM sys_user_dept ud JOIN sys_user u ON ud.user_id = u.user_id JOIN sys_dept d ON ud.dept_id = d.dept_id WHERE ud.header_teacher = 1',
    '[]',
    NULL, 
    500, 
    'active'
) ON DUPLICATE KEY UPDATE `sql_template` = VALUES(`sql_template`);

-- ========== One-Card System Templates ==========

-- 4. Student Info Query
INSERT INTO `query_templates` (`school_id`, `category`, `category_name`, `category_icon`, `name`, `description`, `sql_template`, `fields`, `time_field`, `default_limit`, `status`)
VALUES (
    1, 
    'student', 
    'Student Business', 
    'student', 
    'Student Info Query', 
    'Query student basic info',
    'SELECT CUSTNAME as name, STUDENTID as student_id, IDCARD as id_card, CARDID as card_id, CARDSTATE as card_status FROM CARD_CUSTOMERS WHERE 1=1',
    '[{"id": "name", "label": "Name", "column": "CUSTNAME", "type": "text", "operator": "LIKE"}, {"id": "student_id", "label": "Student ID", "column": "STUDENTID", "type": "text", "operator": "="}, {"id": "id_card", "label": "ID Card", "column": "IDCARD", "type": "text", "operator": "="}]',
    NULL, 
    100, 
    'active'
) ON DUPLICATE KEY UPDATE `sql_template` = VALUES(`sql_template`);

-- 5. Consumption Record Query
INSERT INTO `query_templates` (`school_id`, `category`, `category_name`, `category_icon`, `name`, `description`, `sql_template`, `fields`, `time_field`, `default_limit`, `status`)
VALUES (
    1, 
    'consume', 
    'Consumption Business', 
    'consume', 
    'Consumption Record Query', 
    'Query consumption records',
    'SELECT CARDID as card_id, STUDENTID as student_id, TRANAMT as amount, TRATIME as time, SHOPNAME as shop FROM DATA_CARD_CONSUME WHERE 1=1',
    '[{"id": "card_id", "label": "Card ID", "column": "CARDID", "type": "text", "operator": "="}, {"id": "student_id", "label": "Student ID", "column": "STUDENTID", "type": "text", "operator": "="}]',
    'TRATIME', 
    500, 
    'active'
) ON DUPLICATE KEY UPDATE `sql_template` = VALUES(`sql_template`);

-- 6. Recharge Record Query
INSERT INTO `query_templates` (`school_id`, `category`, `category_name`, `category_icon`, `name`, `description`, `sql_template`, `fields`, `time_field`, `default_limit`, `status`)
VALUES (
    1, 
    'consume', 
    'Consumption Business', 
    'consume', 
    'Recharge Record Query', 
    'Query recharge records',
    'SELECT CARDID as card_id, TRANAMT as amount, TRATIME as time, PAYTYPE as pay_type FROM DATA_ONLINE_CASH WHERE 1=1',
    '[{"id": "card_id", "label": "Card ID", "column": "CARDID", "type": "text", "operator": "="}, {"id": "student_id", "label": "Student ID", "column": "STUDENTID", "type": "text", "operator": "="}]',
    'TRATIME', 
    500, 
    'active'
) ON DUPLICATE KEY UPDATE `sql_template` = VALUES(`sql_template`);

-- 7. Access Record Query
INSERT INTO `query_templates` (`school_id`, `category`, `category_name`, `category_icon`, `name`, `description`, `sql_template`, `fields`, `time_field`, `default_limit`, `status`)
VALUES (
    1, 
    'access', 
    'Access Business', 
    'access', 
    'Access Record Query', 
    'Query access records',
    'SELECT CARDID as card_id, STUDENTID as student_id, INOUTTIME as time, INOUTFLAG as flag, DEVICENAME as device FROM ACCESS_INOUT_RECORD WHERE 1=1',
    '[{"id": "card_id", "label": "Card ID", "column": "CARDID", "type": "text", "operator": "="}, {"id": "student_id", "label": "Student ID", "column": "STUDENTID", "type": "text", "operator": "="}]',
    'INOUTTIME', 
    500, 
    'active'
) ON DUPLICATE KEY UPDATE `sql_template` = VALUES(`sql_template`);

-- Verification
SELECT 'Templates upgrade completed!' AS status;
SELECT COUNT(*) AS template_count FROM query_templates WHERE school_id = 1;

-- ============================================
-- Upgrade Script: v1.0.1.10 -> v1.0.2.01
-- Permission Management System
-- ============================================

-- Table: permission_modules
CREATE TABLE IF NOT EXISTS `permission_modules` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT 'Primary Key',
    `code` VARCHAR(50) NOT NULL COMMENT 'Module Code',
    `name` VARCHAR(100) NOT NULL COMMENT 'Module Name',
    `description` VARCHAR(255) COMMENT 'Module Description',
    `parent_code` VARCHAR(50) COMMENT 'Parent Module Code',
    `icon` VARCHAR(50) COMMENT 'Icon',
    `sort_order` INT DEFAULT 0 COMMENT 'Sort Order',
    `status` VARCHAR(20) DEFAULT 'active' COMMENT 'Status',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Created At',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_code` (`code`),
    KEY `idx_parent` (`parent_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Permission Modules Table';

-- Table: user_school_permissions
CREATE TABLE IF NOT EXISTS `user_school_permissions` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT 'Primary Key',
    `user_id` INT NOT NULL COMMENT 'User ID',
    `school_id` INT NOT NULL COMMENT 'School ID',
    `module_code` VARCHAR(50) NOT NULL COMMENT 'Module Code',
    `permission_code` VARCHAR(50) NOT NULL COMMENT 'Permission Code',
    `granted` TINYINT(1) DEFAULT 1 COMMENT 'Granted',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Created At',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_school_module_perm` (`user_id`, `school_id`, `module_code`, `permission_code`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_school_id` (`school_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='User School Permissions Table';

-- Table: user_template_permissions
CREATE TABLE IF NOT EXISTS `user_template_permissions` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT 'Primary Key',
    `user_id` INT NOT NULL COMMENT 'User ID',
    `school_id` INT NOT NULL COMMENT 'School ID',
    `template_id` INT NOT NULL COMMENT 'Template ID',
    `can_query` TINYINT(1) DEFAULT 1 COMMENT 'Can Query',
    `can_export` TINYINT(1) DEFAULT 0 COMMENT 'Can Export',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Created At',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_school_template` (`user_id`, `school_id`, `template_id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_school_id` (`school_id`),
    KEY `idx_template_id` (`template_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='User Template Permissions Table';

-- Default Permission Modules
INSERT INTO `permission_modules` (`code`, `name`, `description`, `parent_code`, `icon`, `sort_order`, `status`) VALUES
-- Top level modules
('school', 'School Management', 'School management permissions', NULL, 'school', 1, 'active'),
('query', 'Query Management', 'Query related permissions', NULL, 'search', 2, 'active'),
('config', 'Config Management', 'System configuration permissions', NULL, 'setting', 3, 'active'),
('user', 'User Management', 'User management permissions', NULL, 'user', 4, 'active'),
('log', 'Log Management', 'Log viewing permissions', NULL, 'log', 5, 'active'),

-- School sub-permissions
('school.view', 'View Schools', 'View school list', 'school', 'view', 1, 'active'),
('school.create', 'Create School', 'Create new school', 'school', 'create', 2, 'active'),
('school.edit', 'Edit School', 'Edit school info', 'school', 'edit', 3, 'active'),
('school.delete', 'Delete School', 'Delete school', 'school', 'delete', 4, 'active'),

-- Query sub-permissions
('query.execute', 'Execute Query', 'Execute query', 'query', 'run', 1, 'active'),
('query.export', 'Export Data', 'Export query results', 'query', 'export', 2, 'active'),
('query.template', 'Manage Templates', 'Manage query templates', 'query', 'template', 3, 'active'),

-- Config sub-permissions
('config.view', 'View Config', 'View system config', 'config', 'view', 1, 'active'),
('config.edit', 'Edit Config', 'Edit system config', 'config', 'edit', 2, 'active'),

-- User sub-permissions
('user.view', 'View Users', 'View user list', 'user', 'view', 1, 'active'),
('user.create', 'Create User', 'Create new user', 'user', 'create', 2, 'active'),
('user.edit', 'Edit User', 'Edit user info', 'user', 'edit', 3, 'active'),
('user.delete', 'Delete User', 'Delete user', 'user', 'delete', 4, 'active'),
('user.permission', 'Manage Permissions', 'Manage user permissions', 'user', 'permission', 5, 'active'),

-- Log sub-permissions
('log.view', 'View Logs', 'View operation logs', 'log', 'view', 1, 'active')
ON DUPLICATE KEY UPDATE `name` = VALUES(`name`);

-- Verification
SELECT 'Upgrade completed!' AS status;
SELECT COUNT(*) AS module_count FROM permission_modules;

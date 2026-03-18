# v1.0.0.47 → v1.0.0.50 升级说明

## 问题修复

本次升级修复了登录时报错 `Unknown column 'users.openid'` 的问题。

### 问题原因
数据库表结构与代码模型不一致，`users` 表缺少 `openid`、`unionid`、`id_card`、`avatar` 字段。

### 修复内容

| 版本 | 更新内容 |
|------|---------|
| v1.0.0.48 | 管理平台添加版本号显示 |
| v1.0.0.49 | 修复 query.py 缩进错误 |
| v1.0.0.50 | 修复数据库表结构不一致问题 |

## 升级步骤

### 1. 停止服务
```bash
# 如果使用脚本启动
scripts/stop_background.bat

# 或者直接关闭命令行窗口
```

### 2. 备份数据库（重要！）
```bash
mysqldump -u root -p mini_db_query > backup_$(date +%Y%m%d).sql
```

### 3. 执行数据库迁移

**方式一：运行批处理脚本**
```bash
双击运行: 升级数据库_v1.0.0.50.bat
```

**方式二：手动执行SQL**
```bash
mysql -u root -p mini_db_query < backend/migrations/v1.0.0.50_safe_migrate.sql
```

**方式三：逐条执行（推荐）**
如果上述方式失败，可以在 MySQL 客户端中逐条执行：
```sql
-- 添加 openid 字段
ALTER TABLE users ADD COLUMN openid VARCHAR(100) UNIQUE COMMENT '微信openid';

-- 添加 unionid 字段
ALTER TABLE users ADD COLUMN unionid VARCHAR(100) UNIQUE COMMENT '微信unionid';

-- 添加 id_card 字段
ALTER TABLE users ADD COLUMN id_card VARCHAR(255) COMMENT '身份证号(加密)';

-- 添加 avatar 字段
ALTER TABLE users ADD COLUMN avatar VARCHAR(500) COMMENT '头像URL';

-- 添加 error_detail 字段（如果之前没有执行过）
ALTER TABLE query_logs ADD COLUMN error_detail JSON COMMENT '错误详情';
```

### 4. 覆盖代码文件

将升级包中的文件复制到对应目录：

```
patch_v1.0.0.47-to-50/
├── index.html                      → 覆盖 admin/index.html
├── backend/
│   ├── api/query.py                → 覆盖 backend/api/query.py
│   ├── core/config.py              → 覆盖 backend/core/config.py
│   ├── version.py                  → 覆盖 backend/version.py
│   └── migrations/
│       └── v1.0.0.50_safe_migrate.sql  → 复制到 backend/migrations/
└── 升级数据库_v1.0.0.50.bat        → 根目录
```

### 5. 启动服务
```bash
start.bat
# 或
scripts/start_background.bat
```

### 6. 验证

1. 访问管理平台，右下角应显示：**版本: 1.0.0.50**
2. 使用 admin / 123456 登录成功
3. 检查数据库字段：
```sql
SHOW COLUMNS FROM users;
```

## 涉及文件

| 文件 | 变更 |
|------|------|
| `admin/index.html` | 添加版本号显示 |
| `backend/api/query.py` | 修复缩进错误 |
| `backend/core/config.py` | 版本号动态读取 |
| `backend/version.py` | 更新为 1.0.0.50 |
| `backend/migrations/v1.0.0.50_safe_migrate.sql` | 数据库迁移脚本 |

## 回滚

如升级后出现问题：
1. 恢复数据库备份
2. 恢复备份的代码文件

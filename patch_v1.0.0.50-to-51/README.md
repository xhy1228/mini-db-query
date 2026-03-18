# v1.0.0.50 → v1.0.0.51 升级指南

## 本次更新内容

### 1. 移除启动时自动初始化数据库
- 启动时不再自动检测/创建数据库表
- 只读取配置文件中的数据库连接信息
- 解决了远程数据库连接问题

### 2. 添加完整数据库初始化脚本
- `scripts/init_database_v1.0.0.51.sql`
- 包含完整的表结构和默认数据

---

## 升级步骤

### 步骤1：初始化本地数据库

如果你还没有在本地创建数据库，请执行：

```bash
mysql -u root -p < scripts/init_database_v1.0.0.51.sql
```

或者在 MySQL 客户端中运行 `init_database_v1.0.0.51.sql`

### 步骤2：配置数据库连接

修改 `backend/.env` 文件：

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=你的密码
DB_NAME=mini_db_query
```

### 步骤3：更新代码文件

将以下文件复制到对应位置：

```
patch_v1.0.0.50-to-51/
├── backend/
│   ├── models/session.py  → backend/models/session.py
│   └── version.py         → backend/version.py
└── scripts/
    └── init_database_v1.0.0.51.sql  → scripts/init_database_v1.0.0.51.sql
```

### 步骤4：重启服务

```bash
# 停止服务
Ctrl+C

# 启动服务
start.bat
```

### 步骤5：验证

1. 访问管理后台：`http://localhost:8000/admin`
2. 登录：`admin` / `123456`
3. 右下角版本显示：`1.0.0.51`

---

## 默认账号

| 账号 | 密码 | 角色 |
|------|------|------|
| admin | 123456 | 超级管理员 |

---

## 注意事项

1. 如果之前使用的是远程数据库，需要重新在本地创建数据库
2. 数据不会自动迁移，如需保留旧数据请手动导出导入

# Mini DB Query 升级包 v1.0.2.25 -> v1.0.2.28

## 升级说明

本升级包包含从 v1.0.2.25 升级到 v1.0.2.28 的所有文件和数据库脚本。

## 升级内容

### v1.0.2.28
- 修复：用户权限保存 API 路径错误（404）
- 修复：前端权限管理功能

### v1.0.2.27
- 修复：数据序列化问题（datetime/Decimal/bytes）
- 修复：模板字段合并逻辑
- 修复：数据库字段名映射

### v1.0.2.26
- 修复：用户管理 API 路径错误（404）
- 修复：前端 API 调用路径

### v1.1.0 数据结构升级
- 新增：业务大类表 `template_categories`
- 新增：查询条件表 `query_fields`
- 新增：模板历史表 `query_template_history`
- 新增：模板权限表 `template_permissions`
- 新增：模板表字段 `database_id`, `category_id`, `version`, `change_log`

---

## 升级步骤

### 方法一：自动升级（推荐）

1. 解压升级包到项目根目录
2. 双击运行 `upgrade.bat`
3. 按 Y 确认升级
4. 执行数据库升级（见下方）
5. 重启后端服务

### 方法二：手动升级

#### 步骤 1：备份现有文件
```
备份 backend/admin/index.html
备份 backend/version.py
```

#### 步骤 2：复制新文件
```
将 upgrade_v1.0.2.25_to_v1.0.2.28/backend/ 目录内容
复制到项目 backend/ 目录
```

#### 步骤 3：执行数据库升级
```cmd
mysql -h 数据库主机 -P 3306 -u 用户名 -p 数据库名 < scripts/upgrade_database.sql
```

示例：
```cmd
mysql -h 118.195.172.93 -P 3306 -u root -p mini_db_query < scripts/upgrade_database.sql
```

#### 步骤 4：重启后端服务

---

## 文件清单

```
upgrade_v1.0.2.25_to_v1.0.2.28/
├── README.md                    # 本说明文件
├── upgrade.bat                  # Windows 升级脚本
├── rollback.bat                 # Windows 回滚脚本
├── backend/
│   ├── version.py              # 版本号文件
│   ├── admin/
│   │   └── index.html          # 管理后台前端
│   ├── api/
│   │   ├── categories.py       # 业务大类 API
│   │   ├── fields.py           # 查询条件 API
│   │   └── permissions.py      # 模板权限 API
│   ├── db/
│   │   └── query_executor.py   # 查询执行器
│   ├── models/
│   │   └── database.py         # 数据库模型
│   └── services/
│       └── user_service.py     # 用户服务
└── scripts/
    └── upgrade_database.sql    # 数据库升级脚本
```

---

## 数据库变更

### 新增表

| 表名 | 说明 |
|------|------|
| template_categories | 业务大类表 |
| query_fields | 查询条件表 |
| query_template_history | 模板历史表 |
| template_permissions | 模板权限表 |

### 修改表

| 表名 | 新增字段 |
|------|----------|
| query_templates | database_id, category_id, version, change_log |
| users | template_permissions |

---

## 注意事项

1. **升级前请备份数据库**
2. 数据库升级脚本支持重复执行（幂等）
3. 升级后需要重启后端服务
4. 如有问题，可使用 rollback.bat 回滚前端文件

---

## 问题反馈

如遇问题，请提供：
- 错误信息截图
- app.log 日志文件
- 当前版本号

---

*升级包生成时间: 2026-03-20*

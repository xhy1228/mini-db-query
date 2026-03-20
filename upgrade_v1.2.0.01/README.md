# v1.2.0.01 智能查询功能升级包

## 升级说明

从 v1.0.2.28 升级到 v1.2.0.01

## 升级步骤

### 1. 备份数据库
在执行升级前，请先备份现有数据库。

### 2. 执行数据库升级脚本
```sql
-- 在 MySQL 中执行
mysql -u root -p mini_db_query < upgrade_v1.2.0.00.sql
```

### 3. 更新后端代码
将以下文件覆盖到服务器：

```
backend/
├── api/
│   ├── bindings.py (新增)
│   └── database_analysis.py (新增)
├── models/
│   └── database.py (更新)
├── admin/
│   └── index.html (更新)
├── main.py (更新)
└── version.py (更新)
```

### 4. 重启服务
```bash
# Windows
net stop mini-db-query
net start mini-db-query

# 或手动重启
```

## v1.2.0 新功能

### 智能查询功能重构
- **模板复用**：查询模板不再绑定学校，可被多个学校复用
- **一校多库**：一个学校可配置多个数据库连接（MySQL/Oracle/SQLServer）
- **灵活绑定**：学校通过"功能绑定"指定每个功能使用的数据库

### 配置流程
1. **学校管理** → 配置学校
2. **学校详情** → 添加数据库连接
3. **查询模板** → 创建通用模板
4. **学校详情** → 绑定功能（选择模板 + 数据库）

## 文件变更清单

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| upgrade_v1.2.0.00.sql | 新增 | 数据库升级脚本 |
| api/bindings.py | 新增 | 学校-模板绑定管理 API |
| api/database_analysis.py | 新增 | 数据库分析 API |
| models/database.py | 更新 | 新增 SchoolTemplateBinding 模型 |
| main.py | 更新 | 注册新 API 路由 |
| admin/index.html | 更新 | 学校详情页 + 功能绑定 |
| version.py | 更新 | 版本号 1.2.0.01 |

## 兼容性说明

- ✅ 向后兼容：保留原有模板数据
- ✅ 新增功能：不影响现有查询功能
- ⚠️ 需要执行数据库升级脚本

## 问题反馈

如有问题，请在 GitHub Issues 中反馈。

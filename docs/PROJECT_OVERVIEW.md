# Mini DB Query - 功能需求与安装验证流程

## 一、项目概述

| 项目 | 说明 |
|------|------|
| 项目名称 | Mini DB Query（多源数据查询小程序版） |
| 项目类型 | 微信小程序 + FastAPI后端 + Web管理后台 |
| 系统数据库 | MySQL 8.0.2+（必需） |
| 查询数据源 | MySQL, Oracle, SQL Server |
| 后端端口 | 26316 |
| 当前版本 | v1.0.0.18 |

---

## 二、已实现功能

### 2.1 认证模块 (auth.py)

| API端点 | 功能 | 状态 |
|---------|------|------|
| `POST /api/login` | 用户登录 | ✅ 已实现 |
| `GET /api/me` | 获取当前用户信息 | ✅ 已实现 |
| `POST /api/logout` | 用户登出 | ✅ 已实现 |

### 2.2 用户管理

| API端点 | 功能 | 状态 |
|---------|------|------|
| `POST /api/admin/users` | 创建用户 | ✅ 已实现 |
| `GET /api/admin/users` | 获取用户列表 | ✅ 已实现 |
| `PUT /api/admin/users/{user_id}` | 更新用户 | ✅ 已实现 |
| `DELETE /api/admin/users/{user_id}` | 删除用户 | ✅ 已实现 |

### 2.3 学校管理

| API端点 | 功能 | 状态 |
|---------|------|------|
| `GET /api/manage/schools` | 获取学校列表 | ✅ 已实现 |
| `POST /api/manage/schools` | 创建学校 | ✅ 已实现 |
| `PUT /api/manage/schools/{school_id}` | 更新学校 | ✅ 已实现 |
| `DELETE /api/manage/schools/{school_id}` | 删除学校 | ✅ 已实现 |

### 2.4 数据库管理

| API端点 | 功能 | 状态 |
|---------|------|------|
| `GET /api/manage/databases` | 获取数据库列表 | ✅ 已实现 |
| `POST /api/manage/databases` | 添加数据库配置 | ✅ 已实现 |
| `PUT /api/manage/databases/{db_id}` | 更新数据库配置 | ✅ 已实现 |
| `DELETE /api/manage/databases/{db_id}` | 删除数据库配置 | ✅ 已实现 |
| `POST /api/manage/databases/{db_id}/test` | 测试数据库连接 | ✅ 已实现 |

### 2.5 查询模板管理

| API端点 | 功能 | 状态 |
|---------|------|------|
| `GET /api/manage/templates` | 获取模板列表 | ✅ 已实现 |
| `POST /api/manage/templates` | 创建模板 | ✅ 已实现 |
| `PUT /api/manage/templates/{template_id}` | 更新模板 | ✅ 已实现 |
| `DELETE /api/manage/templates/{template_id}` | 删除模板 | ✅ 已实现 |

### 2.6 查询功能

| API端点 | 功能 | 状态 |
|---------|------|------|
| `GET /api/user/schools` | 获取用户可访问学校 | ✅ 已实现 |
| `GET /api/user/categories` | 获取查询分类 | ✅ 已实现 |
| `GET /api/user/templates` | 获取查询模板 | ✅ 已实现 |
| `POST /api/user/query` | 执行模板查询 | ✅ 已实现 |
| `POST /api/user/sql` | 执行自定义SQL | ✅ 已实现 |
| `GET /api/user/history` | 获取查询历史 | ✅ 已实现 |
| `DELETE /api/user/history/{log_id}` | 删除查询历史 | ✅ 已实现 |
| `POST /api/user/export` | 导出查询结果 | ✅ 已实现 |

### 2.7 日志管理

| API端点 | 功能 | 状态 |
|---------|------|------|
| `GET /api/logs/operations` | 获取操作日志 | ✅ 已实现 |
| `GET /api/logs/queries` | 获取查询日志 | ✅ 已实现 |
| `GET /api/logs/stats` | 获取日志统计 | ✅ 已实现 |
| `DELETE /api/logs/operations/cleanup` | 清理旧日志 | ✅ 已实现 |

### 2.8 Web管理后台

| 页面 | 功能 | 状态 |
|------|------|------|
| 登录页 | 用户登录 | ✅ 已实现 |
| Dashboard | 系统概览 | ✅ 已实现 |
| 用户管理 | 用户CRUD | ✅ 已实现 |
| 学校管理 | 学校CRUD | ✅ 已实现 |
| 数据库管理 | 数据库配置 | ✅ 已实现 |
| 模板管理 | 查询模板配置 | ✅ 已实现 |
| 日志查看 | 操作/查询日志 | ✅ 已实现 |

---

## 三、数据模型

| 模型 | 说明 |
|------|------|
| `User` | 用户表 |
| `School` | 学校/机构表 |
| `DatabaseConfig` | 数据库配置表 |
| `QueryTemplate` | 查询模板表 |
| `UserSchool` | 用户-学校关联表 |
| `QueryLog` | 查询日志表 |

---

## 四、安装流程

### 4.1 系统要求

```
操作系统:  Windows 10/11 或 Windows Server 2016+
Python:    3.10 或更高版本
MySQL:     8.0.2 或更高版本（必需）
内存:      建议 4GB+
磁盘:      建议 1GB+
```

### 4.2 安装前准备

**步骤1：安装MySQL 8.0.2+**

**步骤2：创建系统数据库**
```sql
CREATE DATABASE mini_db_query 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;
```

### 4.3 安装步骤

```
1. 下载发布包 zip 文件
2. 解压到目标目录
3. 运行 scripts\install.bat（以管理员身份）
4. 按提示输入MySQL连接信息
5. 等待安装完成
6. 服务自动启动
```

### 4.4 安装脚本执行流程

```
Step 1: 检查Python环境
Step 2: 检查MySQL服务
Step 3: 配置数据库连接（交互式输入）
Step 4: 创建Python虚拟环境
Step 5: 安装依赖包
Step 6: 创建必要目录
Step 7: 测试数据库连接
Step 8: 初始化数据库表
Step 9: 创建启动脚本
Step 10: 启动服务
```

---

## 五、验证流程

### 5.1 安装验证清单

| 检查项 | 验证方法 | 预期结果 |
|--------|----------|----------|
| Python环境 | `python --version` | Python 3.10+ |
| 虚拟环境 | `dir backend\venv\Scripts` | python.exe存在 |
| 依赖包 | `pip list` | 显示fastapi等包 |
| 配置文件 | `type backend\.env` | DATABASE_URL已配置 |
| 数据库连接 | 服务启动日志 | MySQL Connected |
| 系统表 | MySQL中查看表 | users, schools等表存在 |

### 5.2 功能验证清单

| 检查项 | 验证方法 | 预期结果 |
|--------|----------|----------|
| 管理后台 | 访问 http://localhost:26316/admin | 显示登录页 |
| 用户登录 | admin / 123456 | 登录成功进入后台 |
| API文档 | 访问 http://localhost:26316/docs | 显示Swagger文档 |
| 健康检查 | 访问 http://localhost:26316/health | {"status":"healthy"} |
| 数据库添加 | 管理后台添加数据库连接 | 连接测试成功 |
| SQL查询 | 执行SELECT查询 | 返回结果 |

---

## 六、配置文件说明

```env
# 必需配置
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/mini_db_query?charset=utf8mb4

# 服务器配置
HOST=0.0.0.0
PORT=26316
DEBUG=True

# JWT配置
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080

# 日志配置
LOG_LEVEL=INFO
LOG_DIR=./logs

# 安全配置
ALLOWED_ORIGINS=*
MAX_QUERY_ROWS=10000
QUERY_TIMEOUT=30
```

---

## 七、目录结构

```
mini-db-query/
├── backend/                 # 后端代码
│   ├── main.py             # 主入口
│   ├── run_service.bat     # 启动脚本
│   ├── .env                # 配置文件
│   ├── api/                # API路由
│   ├── models/             # 数据模型
│   ├── db/                 # 数据库模块
│   ├── services/           # 业务服务
│   ├── core/               # 核心模块
│   └── admin/              # 管理后台
├── miniapp/                # 微信小程序（待开发）
├── database/               # 数据库脚本
├── scripts/                # 安装脚本
└── docs/                   # 文档
```

---

## 八、当前版本状态

| 版本 | 状态 | 说明 |
|------|------|------|
| v1.0.0.18 | ✅ 最新 | 修复ALLOWED_ORIGINS配置错误 |

---

**文档更新时间**: 2026-03-17  
**文档作者**: 飞书百万（AI助手）

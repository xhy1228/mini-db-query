# 日志机制完善说明文档

## 更新日期
2026-03-19

## 版本信息
v1.0.0.53 - 日志机制完善版

---

## 一、日志体系结构

### 1.1 三层日志架构

```
┌─────────────────────────────────────────────────────────────┐
│  应用层 (Application Logs)                                   │
│  ├── 请求日志 (Request Logging)                             │
│  └── 操作日志 (Operation Logs)                              │
├─────────────────────────────────────────────────────────────┤
│  业务层 (Business Logs)                                      │
│  ├── 查询日志 (Query Logs)                                  │
│  └── 导出日志 (Export Logs)                                 │
├─────────────────────────────────────────────────────────────┤
│  系统层 (System Logs)                                        │
│  ├── 启动/关闭日志                                          │
│  ├── 错误/警告日志                                          │
│  └── 性能日志                                               │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 日志存储位置

| 日志类型 | 存储位置 | 表名 |
|---------|---------|------|
| 操作日志 | 数据库 | `operation_logs` |
| 查询日志 | 数据库 | `query_logs` |
| 系统日志 | 数据库 | `system_logs` |
| 应用日志 | 文件 | `./logs/app.log` |

---

## 二、日志功能详解

### 2.1 请求日志中间件 (LoggingMiddleware)

**位置**: `backend/core/logging_middleware.py`

**功能**:
- 为每个请求生成唯一请求ID (Request-ID)
- 记录请求参数（敏感信息自动脱敏）
- 记录响应状态和耗时
- 错误时记录详细错误信息

**脱敏字段**:
- `password`, `pwd`, `secret`, `token`, `key`, `credential`

**日志格式**:
```
[2026-03-19 07:16:00] [INFO] root: [a1b2c3d4] >>> POST /api/login
[2026-03-19 07:16:00] [INFO] root: [a1b2c3d4] <<< ✅ POST /api/login | 200 | 15ms
[2026-03-19 07:16:01] [ERROR] root: [e5f6g7h8] 💥 GET /api/query | Exception: ... | Duration: 120ms | IP: 192.168.1.1
```

### 2.2 操作日志记录器 (OperationLogger)

**记录的操作类型**:

#### 认证相关
| Action | 描述 | API |
|--------|------|-----|
| `login` | 用户登录 | POST /api/login |
| `login` | 微信登录 | POST /api/wechat/login |
| `logout` | 用户登出 | POST /api/logout |

#### 用户管理
| Action | 描述 | API |
|--------|------|-----|
| `create_user` | 创建用户 | POST /api/admin/users |
| `update_user` | 更新用户 | PUT /api/admin/users/{id} |
| `delete_user` | 删除用户 | DELETE /api/admin/users/{id} |

#### 学校管理
| Action | 描述 | API |
|--------|------|-----|
| `create_school` | 创建学校 | POST /api/manage/schools |
| `update_school` | 更新学校 | PUT /api/manage/schools/{id} |
| `delete_school` | 删除学校 | DELETE /api/manage/schools/{id} |

#### 数据库配置管理
| Action | 描述 | API |
|--------|------|-----|
| `create_database` | 创建数据库配置 | POST /api/manage/databases |
| `update_database` | 更新数据库配置 | PUT /api/manage/databases/{id} |
| `delete_database` | 删除数据库配置 | DELETE /api/manage/databases/{id} |

#### 查询模板管理
| Action | 描述 | API |
|--------|------|-----|
| `create_template` | 创建查询模板 | POST /api/manage/templates |
| `update_template` | 更新查询模板 | PUT /api/manage/templates/{id} |
| `delete_template` | 删除查询模板 | DELETE /api/manage/templates/{id} |

**操作日志字段**:
- `id`: 日志ID
- `user_id`: 操作用户ID
- `username`: 操作用户名
- `action`: 操作类型
- `resource_type`: 资源类型 (user, school, database, template, query)
- `resource_id`: 资源ID
- `details`: 操作详情
- `ip_address`: 操作者IP
- `status`: 状态 (success/failed)
- `error_message`: 错误信息
- `created_at`: 操作时间

### 2.3 查询日志记录器 (QueryLogService)

**记录的查询类型**:
- 智能查询
- SQL直接查询
- 数据导出

**查询日志字段**:
- `user_id`: 用户ID
- `school_id`: 学校ID
- `template_id`: 模板ID
- `query_name`: 查询名称
- `query_params`: 查询参数 (JSON)
- `sql_executed`: 执行的SQL
- `result_count`: 结果条数
- `query_time`: 查询耗时 (ms)
- `status`: 状态
- `error_message`: 错误信息
- `error_detail`: 错误详情 (JSON)
- `ip_address`: IP地址

**错误详情包含**:
- `error_type`: 错误类型
- `error_message`: 错误消息
- `sql`: SQL语句
- `suggestion`: 建议解决方案

### 2.4 系统日志记录器 (SystemLogger)

**记录的系统事件**:

| Log Type | 描述 |
|----------|------|
| `startup` | 系统启动 |
| `shutdown` | 系统关闭 |
| `error` | 系统错误 |
| `warning` | 系统警告 |
| `info` | 系统信息 |
| `performance` | 性能指标 |

**系统日志字段**:
- `log_type`: 日志类型
- `component`: 组件名称 (server, database, cache, api)
- `message`: 日志消息
- `details`: 详细信息
- `cpu_percent`: CPU使用率
- `memory_percent`: 内存使用率
- `disk_percent`: 磁盘使用率

---

## 三、错误日志完善

### 3.1 错误类型识别

系统自动识别以下错误类型并提供建议：

| 错误关键词 | 建议 |
|-----------|------|
| `connection`, `connect` | 数据库连接失败，请检查数据库配置和网络连接 |
| `syntax`, `sql` | SQL语法错误，请检查SQL语句 |
| `permission`, `denied` | 数据库权限不足，请联系管理员 |
| `timeout` | 查询超时，请优化SQL或缩小查询范围 |
| `table` + `not exist` | 表不存在，请检查表名或模板配置 |
| `column` + `unknown` | 字段不存在，请检查字段名或模板配置 |

### 3.2 错误日志内容

每个错误日志包含：
- 请求ID（用于追踪）
- 错误类型
- 错误消息
- 相关SQL（如果是查询错误）
- 请求参数
- 用户ID
- IP地址
- 时间戳
- 建议解决方案

---

## 四、日志查询API

### 4.1 操作日志查询

```
GET /api/logs/operations
```

**参数**:
- `skip`: 跳过条数
- `limit`: 返回条数 (1-200)
- `user_id`: 用户ID筛选
- `action`: 操作类型筛选
- `days`: 最近多少天 (1-90, 默认7)

**响应**:
```json
{
  "id": 1,
  "user_id": 1,
  "username": "admin",
  "action": "login",
  "resource_type": "user",
  "details": "User admin logged in",
  "ip_address": "192.168.1.1",
  "status": "success",
  "created_at": "2026-03-19 07:16:00"
}
```

### 4.2 查询日志查询

```
GET /api/logs/queries
```

**参数**:
- `skip`: 跳过条数
- `limit`: 返回条数
- `user_id`: 用户ID筛选
- `database_id`: 数据库ID筛选
- `days`: 最近多少天

### 4.3 日志统计

```
GET /api/logs/stats
```

**响应**:
```json
{
  "total": 100,
  "success": 95,
  "failed": 5,
  "success_rate": 95.0,
  "top_actions": [
    {"action": "query", "count": 80},
    {"action": "login", "count": 15}
  ]
}
```

---

## 五、日志清理

### 5.1 自动清理

```
DELETE /api/logs/operations/cleanup?days=30
```

清理30天前的日志。

### 5.2 清理策略建议

| 日志类型 | 建议保留时间 |
|---------|-------------|
| 操作日志 | 90天 |
| 查询日志 | 30天 |
| 系统日志 | 7天 |
| 应用日志 | 7天 |

---

## 六、问题排查指南

### 6.1 用户登录问题

**排查步骤**:
1. 查询操作日志: `action=login`, 查看状态
2. 查看请求日志: 路径 `/api/login`, 查看响应状态码
3. 检查错误详情: 如果有失败记录，查看 error_message

### 6.2 查询失败问题

**排查步骤**:
1. 查询查询日志: `status=failed`
2. 查看错误详情: `error_detail` 字段
3. 根据 `suggestion` 进行排查
4. 查看请求日志: 请求ID关联

### 6.3 系统性能问题

**排查步骤**:
1. 查询系统日志: `log_type=performance`
2. 查看 CPU、内存、磁盘使用率
3. 查询查询日志: 耗时较长的查询
4. 查看应用日志: `./logs/app.log`

---

## 七、安全注意事项

1. **敏感信息脱敏**: 密码、token等自动脱敏处理
2. **日志访问控制**: 非管理员只能查看自己的日志
3. **日志定期清理**: 防止日志无限增长
4. **SQL语句记录**: 便于问题追溯，但需注意SQL注入风险

---

## 八、新增文件清单

| 文件 | 描述 |
|------|------|
| `backend/core/logging_middleware.py` | 日志中间件和操作/系统日志记录器 |

## 九、修改文件清单

| 文件 | 修改内容 |
|------|---------|
| `backend/main.py` | 添加日志中间件 |
| `backend/api/auth.py` | 登录/登出/用户管理操作日志 |
| `backend/api/manage.py` | 学校/数据库/模板管理操作日志 |

---

**文档版本**: v1.0  
**更新日期**: 2026-03-19

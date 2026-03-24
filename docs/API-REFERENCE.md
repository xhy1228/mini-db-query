# 📖 API 接口速查表

> 所有接口前缀: `/api`

---

## 🔐 认证接口 (auth.py)

### POST /auth/login
登录获取Token

**请求体**:
```json
{
  "phone": "13800138000",
  "password": "123456"
}
```

**响应**:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "phone": "13800138000",
    "name": "张三",
    "role": "admin"
  }
}
```

---

### GET /auth/me
获取当前用户信息

**Header**: `Authorization: Bearer {token}`

**响应**:
```json
{
  "id": 1,
  "phone": "13800138000",
  "name": "张三",
  "role": "admin",
  "schools": [
    {"id": 1, "name": "测试学校"}
  ]
}
```

---

## 🔍 查询接口 (query.py)

### GET /user/query/templates
获取用户可用的查询模板

**Header**: `Authorization: Bearer {token}`

**参数**: `school_id` (可选)

**响应**:
```json
{
  "templates": [
    {
      "id": 1,
      "name": "门禁记录查询",
      "category": "access",
      "category_name": "门禁业务",
      "category_icon": "🚪",
      "binding_id": 1
    }
  ]
}
```

---

### POST /user/query/execute
执行查询

**请求体**:
```json
{
  "binding_id": 1,
  "params": {
    "start_time": "2024-01-01",
    "end_time": "2024-01-31",
    "card_no": ""
  }
}
```

**响应**:
```json
{
  "success": true,
  "data": [
    {"name": "张*", "time": "2024-01-15 08:30:00", ...}
  ],
  "total": 100,
  "masked_fields": ["name", "phone"]
}
```

---

### GET /user/query/history
获取查询历史

**响应**:
```json
{
  "history": [
    {
      "id": 1,
      "template_name": "门禁查询",
      "query_time": "2024-01-15 10:30:00",
      "result_count": 50
    }
  ]
}
```

---

## 🏫 学校接口 (manage.py)

### GET /manage/schools
获取学校列表

**响应**:
```json
{
  "schools": [
    {
      "id": 1,
      "name": "测试学校",
      "code": "TEST001",
      "status": "active"
    }
  ]
}
```

---

### POST /manage/schools
创建学校

**请求体**:
```json
{
  "name": "新学校",
  "code": "NEW001",
  "description": "描述"
}
```

---

## 🗄️ 数据库配置接口 (manage.py)

### GET /manage/databases
获取数据库配置列表

### POST /manage/databases
创建数据库配置

**请求体**:
```json
{
  "school_id": 1,
  "name": "MySQL消费库",
  "db_type": "MySQL",
  "host": "192.168.1.100",
  "port": 3306,
  "username": "root",
  "password": "加密后的密码",
  "db_name": "consume_db"
}
```

---

### GET /manage/databases/{id}/tables
获取数据库表列表

### GET /manage/databases/{id}/tables/{table}/columns
获取表字段列表

### POST /manage/databases/{id}/test-query
测试SQL查询

---

## 📋 模板接口 (manage.py)

### GET /manage/templates
获取模板列表

### POST /manage/templates
创建模板

**请求体**:
```json
{
  "category": "access",
  "name": "门禁查询",
  "sql_template": "SELECT * FROM access_records WHERE time BETWEEN '{start_time}' AND '{end_time}'",
  "fields": [
    {
      "name": "start_time",
      "label": "开始时间",
      "type": "date",
      "required": true
    }
  ]
}
```

---

## 🔗 绑定接口 (bindings.py)

### GET /schools/{school_id}/bindings
获取学校的模板绑定

### POST /bindings
创建绑定

**请求体**:
```json
{
  "school_id": 1,
  "template_id": 1,
  "database_id": 1,
  "enabled": true
}
```

---

### GET /schools/{school_id}/databases
获取学校下的数据库配置列表

**响应**:
```json
{
  "databases": [
    {
      "id": 1,
      "name": "MySQL消费库",
      "db_type": "MySQL",
      "host": "192.168.1.100"
    }
  ]
}
```

---

## ⚙️ 系统配置接口 (manage.py)

### GET /manage/configs
获取系统配置

### POST /manage/configs
保存系统配置

**请求体**:
```json
{
  "wechat_appid": "wx...",
  "wechat_secret": "...",
  "site_title": "数据库查询系统"
}
```

---

*最后更新: 2026-03-24*

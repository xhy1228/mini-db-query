# 多源数据查询小程序 - API文档

**更新时间**: 2026-03-17 09:34:55 (北京时间)


## 基础信息

- **基础URL**: `http://localhost:8000/api`
- **认证方式**: Bearer Token (JWT)
- **响应格式**: JSON

## 统一响应格式

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

## API列表

### 1. 认证相关

#### 1.1 微信登录
```
POST /auth/wechat-login
```

**请求体**:
```json
{
  "code": "微信登录code"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "token": "jwt_token",
    "user": {
      "user_id": "xxx",
      "openid": "xxx",
      "role": "user"
    }
  }
}
```

#### 1.2 获取用户信息
```
GET /auth/me
Authorization: Bearer {token}
```

---

### 2. 查询相关

#### 2.1 获取数据库配置列表
```
GET /query/configs
Authorization: Bearer {token}
```

#### 2.2 测试连接
```
POST /query/test-connection
Authorization: Bearer {token}
```

**请求体**:
```json
{
  "config_name": "mysql_demo"
}
```

#### 2.3 获取业务大类
```
GET /query/categories
Authorization: Bearer {token}
```

#### 2.4 获取查询列表
```
GET /query/queries/{category_id}
Authorization: Bearer {token}
```

#### 2.5 智能查询
```
POST /query/smart
Authorization: Bearer {token}
```

**请求体**:
```json
{
  "config_name": "mysql_demo",
  "category": "student",
  "query_id": "student_info",
  "conditions": [
    {
      "field": "name",
      "operator": "=",
      "value": "张三",
      "logic": ""
    }
  ],
  "start_time": "2026-01-01 00:00:00",
  "end_time": "2026-03-16 23:59:59"
}
```

#### 2.6 执行SQL查询
```
POST /query/execute
Authorization: Bearer {token}
```

**请求体**:
```json
{
  "config_name": "mysql_demo",
  "sql": "SELECT * FROM users LIMIT 10"
}
```

#### 2.7 导出查询结果
```
POST /query/export
Authorization: Bearer {token}
```

---

### 3. 错误码说明

| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权/Token过期 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

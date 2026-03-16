# 多源数据查询小程序版 - 开发记录

**项目名称**: 多源数据查询小程序版  
**项目代号**: mini-db-query  
**创建日期**: 2026-03-16  
**开发者**: 飞书百万（AI助手）

---

## 开发日志

### 2026-03-16 项目初始化

#### 23:25 - 需求分析

**用户需求**:
1. 开发微信小程序版本的多源数据查询工具
2. 后端服务部署在Windows Server
3. 预留管理平台功能接口
4. 功能与桌面版完全一致

**技术选型**:
- 后端: Python + FastAPI（高性能异步框架）
- 前端: 微信小程序原生开发
- 认证: 微信登录 + JWT Token
- 数据库: 复用桌面版连接器

#### 23:26 - 架构设计

**分层架构**:
```
用户层 → API网关层 → 业务服务层 → 数据访问层
```

**核心模块**:
1. 认证模块: 微信OAuth + JWT
2. 查询模块: 智能查询 + SQL查询
3. 连接模块: 复用桌面版连接器
4. 导出模块: Excel导出

#### 23:27 - 目录结构设计

```
mini-db-query/
├── backend/          # Python后端
├── miniapp/          # 微信小程序
├── admin/            # 管理平台(后期)
├── docs/             # 文档
└── scripts/          # 脚本
```

#### 23:28 - 后端核心模块开发

**配置管理** (`core/config.py`):
- 使用pydantic-settings管理配置
- 支持环境变量和.env文件
- 默认配置合理

**安全模块** (`core/security.py`):
- JWT Token生成和验证
- 微信登录认证
- 密码加密

**API模块** (`api/auth.py`):
- POST /auth/wechat-login - 微信登录
- GET /auth/me - 获取用户信息
- POST /auth/logout - 退出登录

**查询模块** (`api/query.py`):
- GET /query/configs - 获取配置列表
- POST /query/test-connection - 测试连接
- GET /query/categories - 获取业务大类
- POST /query/smart - 智能查询
- POST /query/execute - SQL查询
- POST /query/export - 导出结果

#### 23:29 - 数据库连接器复用

从桌面版复制以下模块:
- `db/connector.py` - 数据库连接器
- `db/connection_manager.py` - 连接管理器
- `db/query_template.py` - 查询模板

#### 23:30 - 微信小程序开发

**入口配置** (`app.js`):
- 全局数据管理
- 自动登录检测
- Token验证

**网络封装** (`utils/request.js`):
- 统一请求格式
- 自动添加Token
- 错误处理

**首页开发** (`pages/index/`):
- 业务大类展示
- 数据库配置列表
- 快速入口

#### 23:31 - 部署脚本开发

**启动脚本** (`scripts/start.bat`):
- 自动检查依赖
- 创建必要目录
- 启动服务

**服务安装** (`scripts/install-service.bat`):
- 使用NSSM安装Windows服务
- 自动启动配置

#### 23:32 - 文档编写

**API文档** (`docs/API.md`):
- 完整API列表
- 请求/响应示例
- 错误码说明

**部署文档** (`docs/DEPLOY.md`):
- 环境要求
- 部署步骤
- 常见问题

#### 23:33 - Git初始化

```bash
git init
git add -A
git commit -m "init: 多源数据查询小程序版项目初始化"
```

---

## 技术要点

### 1. 微信登录流程

```
小程序端                 后端服务                 微信服务器
   │                       │                       │
   │  wx.login()           │                       │
   │ ─────────────────────>│                       │
   │                       │  code2session         │
   │                       │ ─────────────────────>│
   │                       │  {openid, session_key}│
   │                       │ <─────────────────────│
   │  {token, user_info}   │                       │
   │ <─────────────────────│                       │
   │                       │                       │
```

### 2. JWT认证机制

```python
# 生成Token
token = create_access_token({
    "sub": user_id,
    "openid": openid,
    "role": "user"
})

# 验证Token
@router.get("/me")
async def get_user(current_user = Depends(get_current_user)):
    return current_user
```

### 3. 连接池管理

复用桌面版的连接管理器:
- 连接池复用
- 自动超时断开
- 连接状态跟踪

### 4. SQL安全过滤

```python
dangerous_keywords = ["DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE", "INSERT", "UPDATE"]
for keyword in dangerous_keywords:
    if keyword in sql_upper:
        return error_response(f"安全限制：不允许执行 {keyword} 操作")
```

---

## 代码统计

| 类型 | 文件数 | 代码行数 |
|------|--------|----------|
| Python后端 | 10 | ~1500行 |
| 小程序 | 6 | ~300行 |
| 文档 | 3 | ~500行 |
| 脚本 | 2 | ~50行 |
| **总计** | **21** | **~2350行** |

---

## 依赖列表

```
fastapi>=0.104.0
uvicorn>=0.24.0
sqlalchemy>=2.0.0
pymysql>=1.0.0
oracledb>=1.0.0
pyodbc>=4.0.0
pyyaml>=6.0
pandas>=2.0.0
openpyxl>=3.0.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6
aiofiles>=23.2.1
redis>=5.0.0
httpx>=0.25.0
```

---

## 测试清单

### 后端API测试

- [ ] POST /auth/wechat-login
- [ ] GET /auth/me
- [ ] GET /query/configs
- [ ] POST /query/test-connection
- [ ] GET /query/categories
- [ ] POST /query/smart
- [ ] POST /query/execute
- [ ] POST /query/export

### 小程序测试

- [ ] 首页加载
- [ ] 业务大类选择
- [ ] 智能查询
- [ ] SQL查询
- [ ] 结果展示
- [ ] 数据导出

---

## 已知问题

1. 用户数据库尚未实现（当前使用内存存储）
2. 小程序查询页面尚未完成
3. 导出文件下载链接需要配置静态文件服务

---

## 待优化

1. 添加Redis缓存
2. 实现异步导出（大数据量）
3. 添加请求限流
4. 完善错误处理
5. 添加单元测试

---

## 版本规划

| 版本 | 功能 | 状态 |
|------|------|------|
| v1.0.0 | 基础框架+核心API | ✅ 已完成 |
| v1.1.0 | 小程序完整功能 | 🔄 开发中 |
| v1.2.0 | 用户管理 | 📋 计划中 |
| v2.0.0 | Web管理平台 | 📋 计划中 |

---

*文档生成时间: 2026-03-16 23:34*

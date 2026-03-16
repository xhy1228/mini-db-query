# Mini DB Query 部署说明

多源数据查询小程序版 - 部署文档

## 项目概述

本项目是一个多源数据库查询工具的微信小程序版本，支持：
- MySQL / Oracle / SQL Server / SQLite 等多种数据库
- 基于模板的智能查询
- 用户权限管理
- 查询历史记录

## 系统架构

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   微信小程序    │────▶│   FastAPI后端   │────▶│   业务数据库    │
│   (miniapp/)    │     │   (backend/)    │     │ (MySQL/Oracle等)│
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │  SQLite配置库   │
                        │ (用户/学校/模板) │
                        └─────────────────┘
```

## 后端部署

### 1. 环境要求

- Python 3.10+
- pip 或 pnpm

### 2. 安装依赖

```bash
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 3. 初始化数据库

```bash
# 初始化表结构和管理员账号
python init_db.py

# 创建示例数据（可选）
python init_sample_data.py

# 创建SQLite测试数据库（可选，用于测试）
python init_test_data.py

# 更新数据库配置为SQLite（测试用）
python update_db_config.py
```

### 4. 配置环境变量

创建 `.env` 文件：

```env
# 应用配置
APP_NAME=多源数据查询小程序
DEBUG=false

# 服务器配置
HOST=0.0.0.0
PORT=8000

# JWT密钥（生产环境请修改）
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_EXPIRE_MINUTES=10080

# 允许的跨域来源
ALLOWED_ORIGINS=["https://your-domain.com"]
```

### 5. 启动服务

**开发环境：**
```bash
python main.py
```

**生产环境（推荐使用 gunicorn）：**
```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

**使用 systemd 服务（Linux）：**

创建 `/etc/systemd/system/mini-db-query.service`：

```ini
[Unit]
Description=Mini DB Query API Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/mini-db-query/backend
Environment="PATH=/path/to/mini-db-query/backend/venv/bin"
ExecStart=/path/to/mini-db-query/backend/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable mini-db-query
sudo systemctl start mini-db-query
```

### 6. 验证部署

```bash
# 健康检查
curl http://localhost:8000/health

# 测试登录
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"phone":"admin","password":"123456"}'
```

## 小程序部署

### 1. 配置服务器地址

修改 `miniapp/utils/request.js`：

```javascript
// 生产环境
const BASE_URL = 'https://your-domain.com/api'

// 开发环境
// const BASE_URL = 'http://localhost:8000/api'
```

### 2. 配置小程序信息

修改 `miniapp/project.config.json`：

```json
{
  "appid": "your-wechat-appid",
  "projectname": "mini-db-query"
}
```

### 3. 上传代码

1. 使用微信开发者工具打开 `miniapp` 目录
2. 点击"上传"按钮
3. 填写版本号和备注

### 4. 提交审核

1. 登录微信公众平台
2. 进入"版本管理"
3. 将开发版本提交审核

## Nginx 配置（推荐）

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # HTTPS 重定向
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # API 代理
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 导出文件
    location /exports {
        proxy_pass http://127.0.0.1:8000/exports;
    }
    
    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }
}
```

## 默认账号

| 账号 | 密码 | 角色 |
|------|------|------|
| admin | 123456 | 管理员 |
| 13800000001 | 123456 | 普通用户 |

**⚠️ 生产环境请立即修改默认密码！**

## API 接口文档

启动后端后访问：`http://localhost:8000/docs`

### 主要接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/login | 用户登录 |
| GET | /api/user/schools | 获取用户学校列表 |
| GET | /api/user/categories | 获取业务大类 |
| GET | /api/user/templates | 获取查询模板 |
| POST | /api/user/query | 执行查询 |
| GET | /api/user/history | 获取查询历史 |

## 常见问题

### 1. 数据库连接失败

检查：
- 数据库服务是否启动
- 防火墙是否开放端口
- 用户名密码是否正确
- 是否有访问权限

### 2. 小程序请求失败

检查：
- 服务器地址是否正确
- 域名是否已在微信公众平台配置
- HTTPS 证书是否有效

### 3. JWT Token 过期

- 默认有效期 7 天
- 可在 `.env` 中修改 `JWT_EXPIRE_MINUTES`

## 技术支持

- 后端框架：FastAPI
- 数据库：SQLAlchemy + SQLite
- 认证：JWT
- 小程序：微信原生开发

---

© 2026 飞书百万

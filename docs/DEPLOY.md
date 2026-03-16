# 多源数据查询小程序 - 部署指南

## 环境要求

- Windows Server 2016+
- Python 3.10+
- 4GB+ RAM
- 10GB+ 可用磁盘

## 部署步骤

### 1. 环境准备

#### 1.1 安装Python
下载并安装 Python 3.10 或更高版本：
https://www.python.org/downloads/

**注意**: 安装时勾选 "Add Python to PATH"

#### 1.2 安装依赖
```bash
cd backend
pip install -r requirements.txt
```

#### 1.3 配置数据库连接

复制配置文件：
```bash
cp config/databases.yaml.example config/databases.yaml
```

编辑 `config/databases.yaml`，填入实际的数据库配置：
```yaml
my_mysql:
  db_type: MySQL
  host: 192.168.1.100
  port: 3306
  username: your_username
  password: your_password
  database: your_database

my_oracle:
  db_type: Oracle
  host: 192.168.1.101
  port: 1521
  username: your_username
  password: your_password
  database: ORCL
```

#### 1.4 配置微信小程序

编辑 `.env` 文件或设置环境变量：
```
WECHAT_APPID=your_appid
WECHAT_SECRET=your_secret
```

### 2. 运行服务

#### 方式一：直接运行
```bash
cd backend
python main.py
```

#### 方式二：使用脚本
双击运行 `scripts/start.bat`

#### 方式三：安装为Windows服务（推荐）

使用 NSSM 将服务安装为Windows服务：

1. 下载 NSSM: https://nssm.cc/download
2. 运行 `scripts/install-service.bat`

### 3. 配置Nginx反向代理（可选）

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # 静态文件
    location /exports/ {
        alias /path/to/exports/;
    }
}
```

### 4. 微信小程序配置

1. 登录微信公众平台
2. 开发管理 → 开发设置
3. 配置服务器域名：
   - request合法域名: `https://your-domain.com`
   - uploadFile合法域名: `https://your-domain.com`

## 配置说明

### 配置文件结构

```
backend/
├── config/
│   ├── databases.yaml      # 数据库配置
│   └── query_templates.json # 查询模板
├── data/                   # 数据目录
├── exports/                # 导出文件目录
└── logs/                   # 日志目录
```

### 日志说明

- 访问日志: `logs/app.log`
- 错误日志: `logs/error.log`

## 常见问题

### 1. 端口被占用
修改 `backend/core/config.py` 中的 `PORT` 配置

### 2. 数据库连接失败
- 检查数据库配置是否正确
- 检查网络连通性
- 确认数据库用户名密码

### 3. 微信登录失败
- 检查 WECHAT_APPID 和 WECHAT_SECRET 是否正确
- 确认微信小程序AppID与后台配置一致

## 安全建议

1. **修改JWT密钥**: 在 `.env` 中设置 `JWT_SECRET_KEY`
2. **启用HTTPS**: 使用Nginx配置SSL证书
3. **限制访问**: 配置 `ALLOWED_ORIGINS`
4. **定期备份**: 定期备份 `data/` 和 `config/` 目录

## 后续功能

### 管理平台（后期）

- 用户管理
- 配置管理
- 日志审计
- 系统监控

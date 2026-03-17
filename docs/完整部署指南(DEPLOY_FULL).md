# 部署指南补充

**更新时间**: 2026-03-17 09:34:55 (北京时间)


本文件提供完整的部署配置说明。

## 快速部署

### 1. 后端部署

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 初始化数据库（首次部署）
python init_sample_data.py

# 启动服务
python main.py
# 或使用
bash run.sh
```

### 2. 配置文件说明

创建 `.env` 文件（可选，会使用默认值）：

```env
# 应用配置
APP_NAME=多源数据查询小程序
APP_VERSION=1.0.0
DEBUG=false

# 服务器
HOST=0.0.0.0
PORT=8000

# JWT密钥（生产环境请修改）
JWT_SECRET_KEY=your-secret-key-change-in-production

# 微信小程序（可选）
WECHAT_APPID=your_appid
WECHAT_SECRET=your_secret
```

### 3. 微信小程序配置

#### 3.1 配置服务器域名

登录微信公众平台 → 开发管理 → 开发设置 → 服务器域名：

- request合法域名: `https://your-domain.com`
- uploadFile合法域名: `https://your-domain.com`

#### 3.2 修改小程序请求地址

编辑 `miniapp/utils/request.js`：

```javascript
// 开发环境
const BASE_URL = 'http://localhost:8000/api'

// 生产环境（替换为实际域名）
const BASE_URL = 'https://your-domain.com/api'
```

#### 3.3 编译发布

1. 打开微信开发者工具
2. 导入 `miniapp` 目录
3. 点击"编译"测试
4. 点击"上传"发布

### 4. Nginx 反向代理配置

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # 静态文件（导出文件）
    location /exports/ {
        alias /path/to/backend/exports/;
        autoindex on;
    }

    # WebSocket 支持（如需要）
    location /ws/ {
        proxy_pass http://127.0.0.1:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 5. HTTPS 配置（推荐）

使用 Let's Encrypt 免费证书：

```bash
# 安装 certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期配置
sudo certbot renew --dry-run
```

## 初始化数据说明

首次部署后，系统包含：

| 类型 | 默认账号 | 密码 |
|------|---------|------|
| 超级管理员 | admin | 123456 |

| 数据 | 说明 |
|------|------|
| 学校 | 示例学校（demo_school） |
| 查询模板 | 学生信息查询、消费明细查询、门禁记录查询 |

⚠️ **重要**：请及时修改默认密码和数据库连接配置！

## 目录结构

```
mini-db-query/
├── backend/                 # 后端服务
│   ├── main.py            # 主入口
│   ├── init_sample_data.py # 初始化数据
│   ├── run.sh             # 启动脚本
│   ├── requirements.txt   # Python依赖
│   ├── core/              # 核心模块
│   ├── api/               # API接口
│   ├── models/            # 数据模型
│   ├── services/          # 业务服务
│   ├── db/                # 数据库连接器
│   ├── data/              # 数据目录（SQLite）
│   ├── exports/           # 导出文件
│   └── logs/              # 日志目录
│
├── miniapp/                # 微信小程序
│   ├── pages/             # 页面
│   ├── utils/              # 工具
│   ├── images/             # 图片资源
│   └── app.js             # 小程序入口
│
└── docs/                   # 文档
```

## 常见问题

### 1. 端口被占用

```bash
# 查看端口占用
netstat -tlnp | grep 8000

# 杀掉进程
kill -9 <PID>

# 或修改端口
# 编辑 backend/core/config.py
# PORT = 8001
```

### 2. 数据库连接失败

- 检查数据库配置是否正确
- 确认数据库服务是否运行
- 检查网络连通性

### 3. 小程序无法访问后端

- 确认服务器域名已配置
- 检查防火墙是否开放端口
- 确认API地址正确

## 生产环境检查清单

- [ ] 修改 JWT_SECRET_KEY
- [ ] 启用 HTTPS
- [ ] 配置防火墙规则
- [ ] 设置定期备份
- [ ] 修改默认管理员密码
- [ ] 配置数据库连接
- [ ] 设置日志轮转

## 联系支持

如有问题，请联系管理员。

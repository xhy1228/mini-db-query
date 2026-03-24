# 📚 代码知识库 - 持久化代码理解

> 本文档帮助快速理解代码，避免每次重新分析。持续更新。

---

## 🗂️ 项目结构

```
mini-db-query/
├── backend/                 # FastAPI 后端
│   ├── api/                 # API 路由
│   │   ├── auth.py          # 登录认证
│   │   ├── query.py         # 查询接口
│   │   ├── manage.py        # 管理接口
│   │   └── bindings.py     # 绑定管理
│   ├── core/                # 核心功能
│   │   ├── config.py        # 配置
│   │   ├── security.py      # 安全工具
│   │   └── decrypt.py       # 密码解密
│   ├── db/                  # 数据库操作
│   │   └── connection.py    # 数据库连接
│   ├── models/
│   │   └── database.py      # SQLAlchemy 模型
│   ├── services/
│   │   └── log_service.py   # 日志服务
│   ├── admin/               # 管理后台静态文件
│   │   ├── index.html       # 管理主页
│   │   └── setup.html       # 初始化页面
│   └── version.py           # 版本信息
│
├── miniapp/                 # 微信小程序
│   ├── pages/
│   │   ├── index/           # 首页
│   │   ├── query/           # 查询页
│   │   ├── history/         # 查询历史
│   │   └── profile/         # 个人中心
│   ├── app.js
│   ├── app.json
│   └── utils/
│       └── request.js       # 请求封装
│
├── scripts/                 # 脚本
│   ├── init_database.sql    # 初始化
│   ├── quick-check.sh       # 快速检查
│   └── deploy.sh            # 部署脚本
│
└── .github/workflows/       # CI/CD
```

---

## 🔑 核心模块

### 1. 认证模块 (auth.py)

**功能**：用户登录、Token生成

**关键函数**：
```python
# 创建访问令牌
create_access_token(data: dict, expires_delta: timedelta) -> str

# 验证密码
verify_password(plain_password: str, hashed_password: str) -> bool

# 获取当前用户（依赖注入）
get_current_user(token: str) -> User
```

**API 接口**：
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/auth/login | 登录 |
| POST | /api/auth/register | 注册 |
| GET | /api/auth/me | 当前用户信息 |

---

### 2. 查询模块 (query.py)

**功能**：执行数据库查询

**关键函数**：
```python
# 执行查询
execute_query(sql: str, db_config: dict, params: dict) -> list

# 脱敏处理
mask_value(value: str, field_name: str) -> str
```

**API 接口**：
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/user/query/templates | 获取可用模板 |
| POST | /api/user/query/execute | 执行查询 |
| GET | /api/user/query/history | 查询历史 |

**查询流程**：
```
1. 获取用户学校 → 2. 获取学校绑定的模板 → 3. 获取模板SQL → 4. 获取数据库配置 → 5. 连接目标数据库 → 6. 执行查询 → 7. 脱敏处理 → 8. 返回结果
```

---

### 3. 管理模块 (manage.py)

**功能**：系统配置、数据库管理

**API 接口**：
| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | /api/manage/schools | 学校管理 |
| GET/POST | /api/manage/databases | 数据库配置 |
| GET/POST | /api/manage/templates | 模板管理 |
| GET/POST | /api/manage/configs | 系统配置 |

---

### 4. 绑定模块 (bindings.py)

**功能**：学校-模板-数据库绑定管理

**API 接口**：
| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | /api/bindings | 绑定列表 |
| GET/POST | /api/schools/{id}/bindings | 学校绑定 |
| GET | /api/schools/{id}/databases | 学校数据库 |

---

## 🛠️ 关键代码模式

### 1. 数据库连接（支持多类型）

```python
# 核心连接逻辑 (db/connection.py)
def get_connection(db_config: dict):
    db_type = db_config['db_type']
    
    if db_type == 'MySQL':
        return pymysql.connect(...)
    elif db_type == 'Oracle':
        return cx_Oracle.connect(...)
    elif db_type == 'SQLServer':
        return pyodbc.connect(...)
```

### 2. 密码解密

```python
# 核心解密逻辑 (core/decrypt.py)
from core.security import decrypt_password

# 管理后台保存密码时加密，查询时解密
decrypted = decrypt_password(encrypted_password)
```

**注意**：MySQL 和 SQLServer 密码也需要解密！

### 3. 脱敏处理

```python
# 字段脱敏 (api/query.py)
def mask_value(value: str, field_name: str, need_mask: int = 0) -> str:
    """
    need_mask: 0=自动脱敏, 1=强制脱敏, 2=不脱敏
    """
    if not value or need_mask == 2:
        return value
    
    # 手机号脱敏
    if 'phone' in field_name.lower() or 'mobile' in field_name.lower():
        return value[:3] + '****' + value[-4:]
    
    # 姓名脱敏
    if 'name' in field_name.lower() and len(value) >= 2:
        return value[0] + '*' * (len(value) - 2) + value[-1]
    
    return value
```

### 4. 模板SQL渲染

```python
# 模板变量替换
def render_template(sql_template: str, params: dict) -> str:
    for key, value in params.items():
        sql_template = sql_template.replace(f'{{{key}}}', str(value))
    return sql_template
```

---

## 📋 重要配置

### 版本号格式
```
v主版本.次版本.修订号-YYMMDD-HHmmss
示例: v1.2.2.01-240324-180000
```

### 数据库类型枚举
- `MySQL` - MySQL 数据库
- `Oracle` - Oracle 数据库
- `SQLServer` - SQL Server 数据库
- `SQLite` - SQLite 本地数据库

### 业务分类
| code | 名称 | 图标 |
|------|------|------|
| consume | 消费业务 | 💰 |
| access | 门禁业务 | 🚪 |
| wechat | 微信业务 | 💬 |
| student | 学生业务 | 🎓 |
| recharge | 充值业务 | 💳 |

---

## ⚠️ 常见问题 (FAQ)

### Q1: 密码哈希问题
**问题**：登录失败，密码不正确
**解决**：
- 必须用 `get_password_hash()` 生成密码哈希
- 不要用在线 bcrypt 工具！

### Q2: 数据库连接失败
**检查**：
1. 密码是否解密？（MySQL/Oracle/SQLServer 都要解密）
2. 端口是否正确？（MySQL 3306, Oracle 1521, SQLServer 1433）
3. 防火墙是否放行？

### Q3: 查询结果为空
**检查**：
1. SQL 模板变量是否正确替换
2. 目标数据库是否有数据
3. 时间范围是否正确

### Q4: 前端请求失败
**检查**：
1. 请求路径是否加了重复的 `/api` 前缀
2. Token 是否过期
3. CORS 配置

---

## 🔧 开发规范

### Python
- 使用 `async/await` 异步处理
- 路由函数使用 `Depends` 依赖注入
- 错误处理用 `HTTPException`

### 前端 (小程序)
- WXML 禁止 ES6 箭头函数
- 禁止模板内复杂计算 → 用 JS 预处理
- request 路径注意不要重复前缀

### 数据库
- 升级脚本必须幂等（可重复执行）
- VARCHAR 不要设置字符串默认值
- Emoji 字符不能作为默认值

---

## 📌 待补充

- [ ] 详细 API 参数说明
- [ ] 错误码对照表
- [ ] 小程序页面流程图

---

*最后更新: 2026-03-24*

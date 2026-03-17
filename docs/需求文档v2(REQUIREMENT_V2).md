# 需求分析与架构重构方案

**更新时间**: 2026-03-17 09:34:55 (北京时间)


## 一、需求理解

### 1.1 用户群体
- **超级管理员**: 管理整个系统，配置学校、数据库、用户权限
- **现场管理人员**: 使用小程序查询数据，无SQL技术背景

### 1.2 核心需求

#### 小程序端（简化）
1. 用户登录（手机号 + 身份证后六位）
2. 选择业务类型
3. 输入查询条件
4. 查看查询结果
5. 超级管理员可在小程序管理用户

#### 管理平台（Web）
1. 学校/项目管理
2. 数据库连接配置
3. 查询模板配置
4. 用户管理（录入手机号、身份证、姓名）
5. 用户权限分配（授权学校）

### 1.3 数据层级

```
学校/项目 (School)
  └── 数据库配置 (Database)
        └── 查询模板 (QueryTemplate)
              └── 用户权限 (UserSchool)
                    └── 查询日志 (QueryLog)
```

### 1.4 权限模型

```
超级管理员
  └── 所有学校权限
  └── 用户管理权限
  └── 系统配置权限

普通用户
  └── 授权学校权限（查询数据）
```

## 二、架构调整

### 2.1 新的数据模型

#### 学校/项目表 (schools)
```sql
- id: 学校ID
- name: 学校名称
- code: 学校编码
- description: 描述
- status: 状态 (active/inactive)
- created_at: 创建时间
```

#### 数据库配置表 (database_configs)
```sql
- id: 配置ID
- school_id: 学校ID（关联）
- name: 配置名称
- db_type: 数据库类型 (MySQL/Oracle/SQLServer)
- host: 主机地址
- port: 端口
- username: 用户名
- password: 密码（加密）
- database: 数据库名
- status: 状态
- created_at: 创建时间
```

#### 查询模板表 (query_templates)
```sql
- id: 模板ID
- school_id: 学校ID（关联）
- category: 业务大类
- name: 查询名称
- description: 描述
- sql_template: SQL模板
- fields: 查询字段配置 (JSON)
- time_field: 时间字段
- default_limit: 默认条数
- status: 状态
- created_at: 创建时间
```

#### 用户表 (users)
```sql
- id: 用户ID
- phone: 手机号（登录账号）
- password: 密码（身份证后6位，加密）
- name: 姓名
- id_card: 身份证号（加密）
- role: 角色 (admin/user)
- status: 状态
- created_at: 创建时间
```

#### 用户学校权限表 (user_schools)
```sql
- id: 权限ID
- user_id: 用户ID
- school_id: 学校ID
- permissions: 权限列表 (JSON)
- created_at: 授权时间
```

#### 查询日志表 (query_logs)
```sql
- id: 日志ID
- user_id: 用户ID
- school_id: 学校ID
- template_id: 模板ID
- query_params: 查询参数 (JSON)
- result_count: 结果条数
- query_time: 查询时间
- created_at: 创建时间
```

### 2.2 API接口重新设计

#### 小程序端API
```
POST /api/auth/login              # 手机号+密码登录
GET  /api/auth/me                 # 获取用户信息
POST /api/auth/logout             # 退出登录

GET  /api/user/schools            # 获取用户授权学校列表
GET  /api/user/categories         # 获取业务大类（按学校筛选）
GET  /api/user/templates          # 获取查询模板（按学校和业务大类筛选）
POST /api/user/query              # 智能查询
GET  /api/user/history            # 查询历史
POST /api/user/export             # 导出结果

# 超级管理员专用
GET  /api/admin/users             # 用户列表
POST /api/admin/users             # 创建用户
PUT  /api/admin/users/:id         # 更新用户
DELETE /api/admin/users/:id       # 删除用户
POST /api/admin/users/:id/permissions  # 分配权限
```

#### 管理平台API
```
# 学校管理
GET  /api/manage/schools          # 学校列表
POST /api/manage/schools          # 创建学校
PUT  /api/manage/schools/:id      # 更新学校
DELETE /api/manage/schools/:id    # 删除学校

# 数据库配置
GET  /api/manage/databases        # 数据库列表
POST /api/manage/databases        # 创建配置
PUT  /api/manage/databases/:id    # 更新配置
DELETE /api/manage/databases/:id  # 删除配置
POST /api/manage/databases/:id/test  # 测试连接

# 查询模板
GET  /api/manage/templates        # 模板列表
POST /api/manage/templates        # 创建模板
PUT  /api/manage/templates/:id    # 更新模板
DELETE /api/manage/templates/:id  # 删除模板

# 用户管理
GET  /api/manage/users            # 用户列表
POST /api/manage/users            # 创建用户
PUT  /api/manage/users/:id        # 更新用户
DELETE /api/manage/users/:id      # 删除用户
POST /api/manage/users/:id/schools    # 分配学校权限
```

### 2.3 小程序页面调整

#### 原页面（删除数据库配置相关）
- ~~数据库配置选择~~ → **删除**

#### 新页面结构
```
pages/
├── login/          # 登录页（新增）
├── index/          # 首页（学校选择 + 业务大类）
├── query/          # 查询页（模板选择 + 条件输入 + 结果展示）
├── history/        # 查询历史
├── profile/        # 个人中心
└── admin/          # 管理页面（超级管理员）
    ├── users/      # 用户管理
    └── permissions/ # 权限管理
```

## 三、开发计划

### 第一阶段：数据库和用户体系（当前）
- [ ] 创建数据库表结构
- [ ] 实现用户登录认证
- [ ] 实现学校权限模型
- [ ] 超级管理员初始化

### 第二阶段：管理平台API
- [ ] 学校管理接口
- [ ] 数据库配置接口
- [ ] 查询模板接口
- [ ] 用户管理接口

### 第三阶段：小程序端调整
- [ ] 登录页面
- [ ] 首页调整（学校选择）
- [ ] 查询页面调整
- [ ] 管理员功能

### 第四阶段：Web管理平台
- [ ] Vue3 + Element Plus
- [ ] 学校管理
- [ ] 数据库配置
- [ ] 查询模板配置
- [ ] 用户管理

## 四、关键变更点

| 原设计 | 新设计 | 原因 |
|--------|--------|------|
| 小程序配置数据库 | 管理平台配置 | 用户无技术背景 |
| 单层级配置 | 学校→数据库→模板 | 多学校管理需求 |
| 自由登录 | 手机号+身份证后6位 | 企业级权限控制 |
| 无用户管理 | 完整用户体系 | 现场人员管理需求 |

## 五、超级管理员默认账号

- 手机号: `admin`
- 密码: `123456`（首次登录后修改）
- 角色: 超级管理员
- 权限: 所有学校、所有功能

---

*文档创建时间: 2026-03-17 00:28*

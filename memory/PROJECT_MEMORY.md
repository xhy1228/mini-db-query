# Mini DB Query - 项目记忆

## 版本历史

### v1.0.0.19 (2026-03-17)
**管理后台完整功能**

#### 新增 API
- `/api/manage/schools` - 学校管理 CRUD
- `/api/manage/databases` - 数据库配置 CRUD
- `/api/manage/templates` - 查询模板 CRUD
- `/api/manage/databases/{id}/test` - 数据库连接测试
- `/api/manage/categories` - 业务大类统计

#### 管理后台功能
| 模块 | 状态 | 说明 |
|------|------|------|
| 用户管理 | ✅ | 增删改查、权限分配 |
| 学校管理 | ✅ | 增删改查 |
| 数据库配置 | ✅ | 增删改查、连接测试 |
| 查询模板 | ✅ | 增删改查 |
| 操作日志 | ✅ | 分页查询、详情查看 |

---

### v1.0.0.18 (2026-03-17)
**重大更新: "先部署，后配置"架构**

#### 设计理念
- 部署和数据库配置分离
- 部署时无需数据库
- 通过 Web 界面配置数据库
- 初始化脚本独立执行

#### 安装流程 (新)
```
1. 运行 install.bat
   - 只检查 Python
   - 创建虚拟环境
   - 安装依赖
   - 创建目录

2. 启动服务 start_server.bat
   - 服务无数据库启动
   - 访问 http://localhost:26316

3. 浏览器配置数据库
   - 访问 /setup 页面
   - 输入 MySQL 连接信息
   - 测试连接
   - 保存配置
   - 自动跳转到 /admin

4. 初始化数据库
   - 在 MySQL 中执行 scripts/init_database.sql
   - 或使用 MySQL 客户端工具执行
```

#### 新增文件
- `backend/api/setup.py` - 配置 API
- `backend/admin/setup.html` - 配置页面
- `scripts/init_database.sql` - 独立初始化脚本

#### 访问地址
| 地址 | 说明 |
|------|------|
| http://localhost:26316/setup | 配置页面 |
| http://localhost:26316/admin | 管理后台 |
| http://localhost:26316/docs | API 文档 |

---

## 技术栈
- 后端: Python 3.10+ FastAPI
- 前端: 微信小程序 + Element Plus
- 认证: JWT
- 数据库: MySQL 8.0.2+ (系统自身)
- 支持数据源: MySQL, Oracle, SQL Server

---

## 相关项目
- 桌面版: `/root/projects/multi-db-query-tool`
- GitHub: https://github.com/xhy1228/mini-db-query

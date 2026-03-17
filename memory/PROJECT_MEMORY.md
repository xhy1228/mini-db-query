# Mini DB Query - 项目记忆

## 版本历史

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

#### 修改文件
- `scripts/install.bat` - 移除数据库步骤
- `backend/main.py` - 支持无数据库启动
- `backend/core/config.py` - DATABASE_URL 可为空

#### 访问地址
| 地址 | 说明 |
|------|------|
| http://localhost:26316/setup | 配置页面 |
| http://localhost:26316/admin | 管理后台 |
| http://localhost:26316/docs | API 文档 |

#### 默认账号
| 角色 | 账号 | 密码 |
|------|------|------|
| 超级管理员 | admin | 123456 |
| 示例用户 | 13800138000 | 123456 |

---

## 技术栈
- 后端: Python 3.10+ FastAPI
- 前端: 微信小程序
- 认证: JWT
- 数据库: MySQL 8.0.2+ (系统自身)
- 支持数据源: MySQL, Oracle, SQL Server

---

## 相关项目
- 桌面版: `/root/projects/multi-db-query-tool`
- GitHub: https://github.com/xhy1228/mini-db-query

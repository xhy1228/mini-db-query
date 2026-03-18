# v1.0.0.50 → v1.0.0.52 升级指南

## 本次更新内容

### 1. 新增系统配置菜单
- 添加"系统配置"菜单项
- 支持配置微信小程序参数（AppID、Secret）
- 支持配置系统参数（Token有效期、最大查询条数等）
- 支持配置安全参数

### 2. 版本号显示优化
- 确保版本号在页面右下角正确显示

---

## 升级步骤

### 步骤1：更新代码文件

将以下文件复制到对应位置：

```
patch_v1.0.0.50-to-52/
├── index.html                          → admin/index.html (覆盖)
├── backend/
│   ├── models/session.py               → backend/models/session.py (覆盖)
│   └── version.py                      → backend/version.py (覆盖)
└── scripts/
    └── init_database_v1.0.0.51.sql     → scripts/init_database_v1.0.0.51.sql (可选)
```

### 步骤2：重启服务

```bash
# 停止服务
Ctrl+C

# 启动服务
start.bat
```

### 步骤3：验证

1. 访问管理后台：`http://localhost:8000/admin`
2. 登录：`admin` / `123456`
3. 检查侧边栏是否有"系统配置"菜单
4. 点击"系统配置"查看是否可以配置微信小程序参数
5. 检查右下角版本号显示：`1.0.0.52`

---

## 系统配置说明

### 微信配置
| 配置项 | 说明 |
|--------|------|
| wechat_appid | 微信小程序AppID |
| wechat_secret | 微信小程序Secret |

### 系统配置
| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| jwt_expire_minutes | Token有效期(分钟) | 10080 (7天) |
| max_query_rows | 最大查询条数 | 10000 |
| query_timeout | 查询超时(秒) | 30 |

---

## 注意事项

1. **清空浏览器缓存**：升级后请按 `Ctrl+F5` 刷新页面，确保加载最新代码
2. **系统配置菜单需要管理员权限**，普通用户看不到此菜单
3. 微信小程序配置用于小程序端的微信登录功能

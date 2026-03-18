# v1.0.0.53 → v1.0.0.55 完整升级包

## 本次更新

### 1. 版本号显示
- 显示在侧边栏"管理平台"下方

### 2. 系统配置菜单
- 新增「系统配置」菜单
- 可配置微信小程序参数

### 3. 端口保持
- 默认端口：26316

---

## ⚠️ 重要：必须覆盖所有文件！

### 升级步骤

#### 1. 停止服务
按 `Ctrl+C`

#### 2. 复制所有文件（覆盖）

```
patch_v1.0.0.53-to-55/
├── index.html                    → admin/index.html (覆盖)
└── backend/
    ├── main.py                   → backend/main.py (覆盖)
    ├── version.py                → backend/version.py (覆盖)
    ├── core/config.py            → backend/core/config.py (覆盖)
    └── api/stats.py              → backend/api/stats.py (复制)
```

#### 3. 清除浏览器缓存

**必须按 `Ctrl+Shift+Delete` 清除浏览器缓存！**

或者按 `Ctrl+F5` 强制刷新页面！

#### 4. 重启服务

```bash
start.bat
```

#### 5. 访问

```
http://localhost:26316
```

#### 6. 验证

1. 登录后，侧边栏"管理平台"下方显示 `v1.0.0.55`
2. 左侧菜单有「系统配置」选项
3. 点击「系统配置」可以配置微信小程序参数

---

## 如果还是看不到

1. 确认 `admin/index.html` 文件已正确覆盖
2. 确认浏览器缓存已清除
3. 尝试使用无痕模式打开页面
4. 按 `F12` 打开开发者工具，查看控制台是否有错误

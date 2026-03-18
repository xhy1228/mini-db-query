# 打包检查清单

发布新版本前必须执行以下检查：

## ✅ 文件完整性检查

```cmd
dir backend\admin
```

必须包含：
- `index.html` (管理后台主页)
- `setup.html` (数据库配置页)

```cmd
type backend\version.py
```

必须显示正确版本号

---

## ✅ 编码检查

### 1. .bat 文件
- 必须纯英文，不能有任何中文字符
- 检查：`start.bat`, `install.bat`

### 2. requirements.txt
- 注释必须英文或无注释
- 不能有中文字符

---

## ✅ 功能验证

1. 运行 `start.bat` 启动服务
2. 访问 http://localhost:26316/setup - 数据库配置页
3. 访问 http://localhost:26316/docs - API 文档
4. 访问 http://localhost:26316 - 管理后台登录页
5. 检查版本号显示

---

## ⚠️ 打包注意事项

**禁止删除：**
- `backend/admin/` 目录
- `backend/admin/index.html`
- `backend/admin/setup.html`

**可以清理：**
- `backend/__pycache__/`
- `backend/.env` (用户配置)
- `backend/data/*.db` (运行数据)
- `backend/logs/*.log` (日志文件)

---

*创建时间: 2026-03-18*

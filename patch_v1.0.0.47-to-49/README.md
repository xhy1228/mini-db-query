# v1.0.0.47 → v1.0.0.49 升级说明

## 升级内容

### v1.0.0.48
- 管理平台页面添加版本号显示（右下角显示当前版本）
- 版本号从 `version.py` 文件动态读取

### v1.0.0.49
- 修复 `query.py` 缩进错误导致的启动失败

## 升级步骤

### 1. 停止后端服务

```bash
# 如果使用脚本启动
scripts/stop_background.bat

# 如果使用 nssm 服务
scripts/uninstall_nssm_service.bat
```

### 2. 备份当前文件

建议先备份以下文件：
- `backend/api/query.py`
- `backend/core/config.py`
- `backend/version.py`
- `admin/index.html`

### 3. 覆盖升级文件

将升级包中的文件复制到对应目录：

```
patch_v1.0.0.47-to-49/
├── admin/index.html         → 覆盖 admin/index.html
├── backend/
│   ├── api/query.py         → 覆盖 backend/api/query.py
│   ├── core/config.py       → 覆盖 backend/core/config.py
│   └── version.py           → 覆盖 backend/version.py
└── README.md
```

### 4. 启动服务

```bash
# 方式1: 直接启动
start.bat

# 方式2: 后台启动
scripts/start_background.bat

# 方式3: 安装为 Windows 服务
scripts/install_nssm_service.bat
```

### 5. 验证

- 访问管理平台，右下角应显示：**版本: 1.0.0.49**
- 查询功能应正常工作，无缩进错误

## 涉及文件

| 文件 | 变更 |
|------|------|
| `admin/index.html` | 添加版本号显示，调用 /api/version 接口 |
| `backend/api/query.py` | 修复缩进错误（重复的 try-except 块） |
| `backend/core/config.py` | 版本号从 version.py 动态读取 |
| `backend/version.py` | 更新为 1.0.0.49 |

## 回滚

如升级后出现问题，可恢复备份的文件。

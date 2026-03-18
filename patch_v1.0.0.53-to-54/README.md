# v1.0.0.53 → v1.0.0.54 升级指南

## 本次更新

### 修改默认端口
- 默认端口从 26316 改为 **80**

---

## 升级步骤

### 1. 停止服务
按 `Ctrl+C`

### 2. 更新文件

```
patch_v1.0.0.53-to-54/
└── backend/
    ├── core/config.py   → backend/core/config.py (覆盖)
    └── version.py       → backend/version.py (覆盖)
```

### 3. 重启服务

```bash
start.bat
```

### 4. 访问

服务启动后，访问：**http://localhost** (默认80端口可省略)

---

## 端口修改位置

文件：`backend/core/config.py`

```python
# 第68行
PORT: int = 80  # 原来是 26316
```

# Mini DB Query - Windows 服务安装指南

## 问题说明

当前启动服务后会一直显示 CMD 窗口，关闭窗口服务就停止。

## 解决方案

提供三种方案供选择：

---

## 方案一：无窗口后台运行（推荐新手）

### 启动服务
```batch
双击运行：start_background.bat
```
- 使用 `pythonw.exe` 运行，无控制台窗口
- 服务在后台运行，关闭当前窗口不影响

### 停止服务
```batch
双击运行：stop_background.bat
```

### 优点
- 简单易用，无需安装
- 无需管理员权限

### 缺点
- 系统重启后需要手动启动

---

## 方案二：安装为 Windows 服务（推荐生产）

### 安装服务
```batch
以管理员身份运行：install_nssm_service.bat
```

### 特点
- 自动下载 NSSM 工具
- 安装为系统服务，开机自启
- 可通过 Windows 服务管理器管理
- 崩溃后自动重启

### 管理命令
```batch
# 启动服务
net start MiniDBQuery

# 停止服务
net stop MiniDBQuery

# 查看状态
sc query MiniDBQuery

# 卸载服务
双击运行：uninstall_nssm_service.bat
```

### 优点
- 开机自启动
- 稳定可靠
- 崩溃自动恢复
- 专业的服务管理

---

## 方案三：使用 pywin32 服务（开发者）

### 安装 pywin32
```batch
pip install pywin32
```

### 安装服务
```batch
python service_runner.py --install
```

### 管理命令
```batch
python service_runner.py --start    # 启动
python service_runner.py --stop     # 停止
python service_runner.py --uninstall # 卸载
```

---

## 文件说明

```
scripts/
├── start_background.bat        # 方案一：后台启动
├── stop_background.bat         # 方案一：停止服务
├── install_nssm_service.bat    # 方案二：安装服务（推荐）
├── uninstall_nssm_service.bat  # 方案二：卸载服务
└── nssm/                       # NSSM 工具目录（自动下载）
    └── nssm.exe

backend/
├── service_runner.py           # 服务运行器
└── logs/
    ├── service.log             # 服务日志
    ├── service_stdout.log      # 标准输出
    └── service_stderr.log      # 错误输出
```

---

## 推荐方案

| 场景 | 推荐方案 |
|------|---------|
| 开发测试 | 方案一：start_background.bat |
| 生产环境 | 方案二：NSSM 服务 |
| 开发者调试 | 方案三：pywin32 |

---

## 常见问题

### Q: 端口被占用怎么办？
```batch
# 查找占用端口的进程
netstat -ano | findstr ":26316"

# 结束进程
taskkill /F /PID <PID>
```

### Q: 服务无法启动？
1. 检查日志文件：`backend/logs/service_stderr.log`
2. 确认 Python 路径正确
3. 确认已安装依赖：`pip install -r requirements.txt`

### Q: 如何查看服务状态？
```batch
# 方式一：命令行
sc query MiniDBQuery

# 方式二：服务管理器
services.msc

# 方式三：浏览器
http://localhost:26316/health
```

---

© 2026 Mini DB Query

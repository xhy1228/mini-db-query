# 升级包: v1.0.1.02 → v1.0.2.07

## 快速升级

### Windows用户
1. 将此目录解压到项目根目录
2. 双击运行 `upgrade.bat`
3. 执行数据库升级脚本

### 手动升级
1. 备份现有数据
2. 将 `backend/` 和 `miniapp/` 目录复制到项目目录
3. 执行 `scripts/upgrade_v1.0.2.01.sql`
4. 重启服务

## 主要更新

### 🔐 安全机制全面加固
- JWT密钥自动生成
- 登录失败锁定（5次锁定15分钟）
- SQL安全验证（只允许SELECT）
- IP白名单功能
- 数据删除功能

### 📝 日志机制完善
- 所有操作有日志记录
- 请求ID追踪
- 敏感信息脱敏

## 新增文件

```
backend/core/sql_validator.py       # SQL安全验证
backend/core/security_enhanced.py   # 安全增强模块
backend/core/logging_middleware.py  # 日志中间件
backend/api/security.py             # 安全管理API
```

## 数据库升级

```sql
-- 执行此脚本完成数据库升级
source scripts/upgrade_v1.0.2.01.sql;
```

## 验证升级

访问 http://localhost:26316/api/version
应显示: `1.0.2.07`

---

**发布日期**: 2026-03-19

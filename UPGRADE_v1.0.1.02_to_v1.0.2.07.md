# 升级说明: v1.0.1.02 → v1.0.2.07

## 升级概要

| 项目 | 内容 |
|------|------|
| 当前版本 | v1.0.1.02 |
| 目标版本 | v1.0.2.07 |
| 升级类型 | 重大安全更新 |
| 预计时间 | 10-15分钟 |

---

## 主要更新内容

### 1. 🔐 安全机制全面加固 (v1.0.2.04 - v1.0.2.06)

#### JWT密钥安全
- ✅ 自动生成安全的JWT密钥（32字节随机）
- ✅ 密钥存储在 `.keys/jwt.key` 文件
- ✅ 文件权限设置为600（仅所有者可读写）

#### 登录失败锁定
- ✅ 5次登录失败锁定15分钟
- ✅ IP级别锁定（10次失败）
- ✅ 自动解锁机制
- ✅ 管理员可手动解锁

#### SQL安全验证
- ✅ 小程序端只允许SELECT查询
- ✅ 禁止DELETE/UPDATE/INSERT/DROP等危险操作
- ✅ 检测SQL注入攻击
- ✅ 检测多语句执行

#### IP白名单
- ✅ 管理后台IP白名单
- ✅ 支持CIDR格式
- ✅ 动态配置

#### 数据删除功能
- ✅ 用户可删除自己的数据
- ✅ 管理员可软删除/硬删除用户
- ✅ 符合个人信息保护法要求

### 2. 📝 日志机制完善 (v1.0.2.03)

- ✅ 所有API请求记录日志
- ✅ 每个请求生成唯一Request-ID
- ✅ 敏感信息自动脱敏
- ✅ 操作日志完整记录

### 3. 🔧 其他修复 (v1.0.1.03)

- ✅ 密钥配置显示优化
- ✅ 微信SQL模板添加

---

## 升级步骤

### 步骤1: 备份现有数据

```bash
# 备份数据库
mysqldump -u root -p mini_db_query > backup_v1.0.1.02_$(date +%Y%m%d).sql

# 备份配置文件
cp .env .env.backup
cp backend/.env backend/.env.backup
```

### 步骤2: 停止服务

```bash
# Windows
按 Ctrl+C 停止服务

# 或查找进程并终止
taskkill /f /im python.exe
```

### 步骤3: 解压升级包

```bash
# 将 patch_v1.0.1.02-to-v1.0.2.07.zip 解压到项目目录
# 覆盖现有文件
```

### 步骤4: 执行数据库升级脚本

```bash
cd backend
venv\Scripts\activate

# 执行升级脚本
mysql -u root -p mini_db_query < ../scripts/upgrade_v1.0.2.01.sql
```

### 步骤5: 安装新依赖

```bash
pip install -r requirements.txt
```

### 步骤6: 启动服务

```bash
start.bat
```

---

## 升级后验证

### 1. 检查版本号
```
访问: http://localhost:26316/api/version
应显示: 1.0.2.07
```

### 2. 检查JWT密钥
```bash
# 检查密钥文件是否生成
cat .keys/jwt.key
# 应显示随机字符串，不是默认密钥
```

### 3. 测试登录锁定
- 故意输错密码5次
- 第6次应显示"账户已被锁定，请15分钟后再试"

### 4. 测试数据删除
- 登录小程序 → 我的 → 清除我的数据
- 应能成功清除查询历史

---

## 新增API接口

| 接口 | 功能 | 权限 |
|------|------|------|
| `POST /api/security/lockout/unlock` | 解锁账户 | 管理员 |
| `GET /api/security/ip-whitelist` | 获取IP白名单 | 管理员 |
| `POST /api/security/ip-whitelist` | 添加IP白名单 | 管理员 |
| `DELETE /api/security/my-data` | 清除自己的数据 | 用户 |
| `DELETE /api/security/users/{id}/data` | 删除用户数据 | 管理员 |
| `POST /api/security/password/strength` | 密码强度检查 | 用户 |
| `GET /api/security/status` | 安全状态检查 | 管理员 |

---

## 注意事项

1. **首次启动会生成JWT密钥** - 这是正常的安全机制
2. **DEBUG模式默认关闭** - 如需调试，手动开启
3. **JWT有效期改为2小时** - 需要重新登录更频繁
4. **建议立即修改管理员密码** - 使用复杂密码

---

## 回滚方案

如果升级后出现问题：

```bash
# 1. 停止服务

# 2. 恢复数据库
mysql -u root -p mini_db_query < backup_v1.0.1.02_YYYYMMDD.sql

# 3. 恢复配置文件
cp .env.backup .env
cp backend/.env.backup backend/.env

# 4. 使用 v1.0.1.02 版本重新部署
```

---

**升级包**: `patch_v1.0.1.02-to-v1.0.2.07.zip`

**发布日期**: 2026-03-19

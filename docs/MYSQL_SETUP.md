# Mini DB Query - MySQL 配置指南

## 系统要求

- **MySQL**: 8.0.2 或更高版本
- **Python**: 3.10 或更高版本
- **操作系统**: Windows 10/11 或 Windows Server 2016+

---

## 安装步骤

### 1. 安装 MySQL 8.0+

如果还没有安装MySQL，请从官网下载：
- 官网：https://dev.mysql.com/downloads/mysql/
- 选择 MySQL Community Server 8.0.x

### 2. 创建数据库

**方式A：使用SQL脚本**

```batch
cd database
mysql -u root -p < init_database.sql
```

**方式B：手动创建**

```sql
-- 登录MySQL
mysql -u root -p

-- 创建数据库
CREATE DATABASE mini_db_query 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- （可选）创建专用用户
CREATE USER 'miniquery'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON mini_db_query.* TO 'miniquery'@'localhost';
FLUSH PRIVILEGES;
```

### 3. 配置数据库连接

编辑 `backend\.env` 文件：

```env
DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/mini_db_query?charset=utf8mb4
```

**参数说明：**

| 参数 | 说明 | 示例 |
|------|------|------|
| user | MySQL用户名 | root |
| password | MySQL密码 | your_password |
| host | MySQL主机地址 | localhost |
| port | MySQL端口 | 3306 |
| database | 数据库名称 | mini_db_query |

### 4. 测试连接

```batch
cd backend
venv\Scripts\activate.bat
python -c "from models.session import engine; print('MySQL Connected!')"
```

### 5. 启动服务

```batch
cd backend
run_service.bat
```

或使用项目根目录的：
```batch
start_server.bat
```

---

## 验证MySQL版本

```sql
SELECT VERSION();
```

输出应该类似：`8.0.36` 或更高版本。

---

## 常见问题

### Q1: 连接失败 "Access denied"

**原因**：用户名或密码错误

**解决**：
1. 确认MySQL用户名和密码
2. 确认用户有访问mini_db_query数据库的权限

```sql
-- 检查用户权限
SHOW GRANTS FOR 'root'@'localhost';

-- 授权
GRANT ALL PRIVILEGES ON mini_db_query.* TO 'root'@'localhost';
FLUSH PRIVILEGES;
```

### Q2: 连接失败 "Unknown database"

**原因**：数据库不存在

**解决**：
```sql
CREATE DATABASE mini_db_query CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Q3: 连接失败 "Can't connect to MySQL server"

**原因**：MySQL服务未运行

**解决**：
```batch
# 检查服务状态
sc query MySQL80

# 启动服务
net start MySQL80
```

### Q4: 版本不兼容

**原因**：MySQL版本低于8.0.2

**解决**：升级到MySQL 8.0.2或更高版本

---

## 安全建议

### 生产环境配置

1. **修改JWT密钥**：
   ```env
   JWT_SECRET_KEY=your-random-secret-key-at-least-32-characters
   ```

2. **创建专用数据库用户**：
   ```sql
   CREATE USER 'miniquery'@'localhost' IDENTIFIED BY 'strong_password';
   GRANT SELECT, INSERT, UPDATE, DELETE ON mini_db_query.* TO 'miniquery'@'localhost';
   FLUSH PRIVILEGES;
   ```

3. **关闭调试模式**：
   ```env
   DEBUG=False
   ```

4. **限制CORS来源**：
   ```env
   ALLOWED_ORIGINS=https://your-domain.com
   ```

---

## 配置文件示例

### 最小配置

```env
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/mini_db_query?charset=utf8mb4
```

### 完整配置

```env
# Database (MySQL 8.0.2+)
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/mini_db_query?charset=utf8mb4

# Server
HOST=0.0.0.0
PORT=26316
DEBUG=False

# JWT
JWT_SECRET_KEY=your-random-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080

# WeChat (Optional)
WECHAT_APPID=
WECHAT_SECRET=

# Logging
LOG_LEVEL=INFO
LOG_DIR=./logs

# Security
ALLOWED_ORIGINS=https://your-domain.com
MAX_QUERY_ROWS=10000
QUERY_TIMEOUT=30
```

---

## 下一步

配置完成后：

1. 运行 `scripts\install.bat` 安装依赖
2. 运行 `start_server.bat` 启动服务
3. 访问 http://localhost:26316/admin
4. 使用 `admin / 123456` 登录

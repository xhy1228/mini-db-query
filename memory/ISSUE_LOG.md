# Mini DB Query - 问题记录与解决方案

## v1.0.0.18 及之前版本的问题

### 问题1: install.bat 仍包含数据库配置步骤
**现象**: 
```
[Step 3/8] Configuring database connection...
Reconfigure database? (Y/N):
```

**原因**: 旧版本install.bat没有彻底移除数据库配置逻辑

**解决方案**: 
- v1.0.0.18已修复，只保留5步：Python检查、虚拟环境、依赖安装、目录创建、默认配置
- 不再检查MySQL、不再配置数据库、不再初始化数据库

---

### 问题2: .env文件已存在时仍显示旧的DATABASE_URL
**现象**:
```
Current DATABASE_URL:
DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/mini_db_query
```

**原因**: .env文件是旧版本的，包含DATABASE_URL

**解决方案**:
- 新版本默认.env不包含DATABASE_URL
- DATABASE_URL为空时表示未配置
- 通过/setup页面配置后才会写入

---

### 问题3: 解压路径嵌套导致路径错误
**现象**: 
```
g:\mini-db-query\mini-db-query-v1.0.0.18-xxx-windows\dist\backend\venv\...
```

**原因**: 用户在错误目录下运行，或zip包结构有问题

**解决方案**:
- 确保zip包结构正确，无多余嵌套
- 在README中明确说明解压后直接运行scripts/install.bat

---

## 安装流程设计原则

### "先部署后配置"架构
1. **部署阶段**: 只涉及Python环境和依赖，不碰数据库
2. **配置阶段**: 通过Web界面配置数据库，保存后生效
3. **初始化阶段**: 独立的SQL脚本，由部署人员手动执行

### install.bat 应该做什么
```
[Step 1/5] 检查Python
[Step 2/5] 创建虚拟环境
[Step 3/5] 安装依赖
[Step 4/5] 创建目录
[Step 5/5] 创建默认配置(.env无DATABASE_URL)
```

### install.bat 不应该做什么
- ❌ 检查MySQL服务
- ❌ 配置数据库连接
- ❌ 测试数据库连接
- ❌ 初始化数据库表
- ❌ 提示用户输入数据库信息

---

## 发布检查清单

每次发布前必须检查：

1. ✅ install.bat 只有5步，无数据库相关步骤
2. ✅ .env默认不包含DATABASE_URL
3. ✅ start_server.bat 可以无数据库启动
4. ✅ /setup 页面可以正常配置数据库
5. ✅ zip包结构正确，无多余嵌套
6. ✅ 小程序端口正确 (26316)
7. ✅ 所有API路径正确

---

## 相关版本

| 版本 | 状态 | 说明 |
|------|------|------|
| v1.0.0.17及之前 | ❌废弃 | 包含数据库配置步骤 |
| v1.0.0.18 | ✅修复 | 移除数据库配置步骤 |
| v1.0.0.19 | ✅完善 | 添加管理API |
| v1.0.0.20 | ✅当前 | Bug修复 |

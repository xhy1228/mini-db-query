# v1.2.0.03 升级包

## 升级内容

### 新增功能
1. **功能绑定** - 学校-模板绑定管理（v1.2.0核心功能）
2. **数据库分析** - 分析数据库表结构，一键生成查询模板

### 升级步骤

#### 1. 备份现有文件
```bash
# 备份现有管理后台
copy G:\mini-db-query\backend\admin\index.html G:\mini-db-query\backend\admin\index.html.backup
```

#### 2. 更新文件
将 `index.html` 复制到 `backend/admin/` 目录：
```
index.html → G:\mini-db-query\backend\admin\index.html
```

#### 3. 清理缓存
```bash
cd G:\mini-db-query\backend
rmdir /s /q __pycache__
rmdir /s /q api\__pycache__
rmdir /s /q models\__pycache__
```

#### 4. 刷新浏览器
按 `Ctrl + F5` 强制刷新页面

### 注意事项
- 此版本使用国内CDN（cdn.bootcdn.net），无需担心网络问题
- 新增两个菜单：功能绑定、数据库分析
- 如果页面显示异常，请检查浏览器控制台是否有错误

## 文件清单
- `index.html` - 管理后台前端页面（已添加功能绑定和数据库分析界面）
- `version.txt` - 版本号

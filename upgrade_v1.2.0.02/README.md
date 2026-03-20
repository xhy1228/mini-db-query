# v1.2.0.02 升级包

## 从 v1.0.2.28 升级到 v1.2.0.02

### 升级步骤

#### 1. 备份
```bash
# 备份现有文件
copy G:\mini-db-query\backend G:\mini-db-query\backend_backup
```

#### 2. 停止服务
```bash
# 停止正在运行的服务
```

#### 3. 更新文件
将升级包中的文件复制到对应目录：

```
backend/
├── version.py          → G:\mini-db-query\backend\
├── main.py             → G:\mini-db-query\backend\
├── api/
│   ├── auth.py         → G:\mini-db-query\backend\api\
│   ├── categories.py   → G:\mini-db-query\backend\api\
│   ├── fields.py       → G:\mini-db-query\backend\api\
│   ├── permissions.py  → G:\mini-db-query\backend\api\
│   ├── bindings.py     → G:\mini-db-query\backend\api\
│   └── database_analysis.py → G:\mini-db-query\backend\api\
├── models/
│   └── database.py     → G:\mini-db-query\backend\models\
└── admin/
    └── index.html      → G:\mini-db-query\backend\admin\

miniapp/pages/profile/
├── profile.js          → 小程序前端（可选）
├── profile.wxml        → 小程序前端（可选）
└── profile.wxss        → 小程序前端（可选）
```

#### 4. 清理缓存
```bash
cd G:\mini-db-query\backend
rmdir /s /q __pycache__
rmdir /s /q api\__pycache__
rmdir /s /q models\__pycache__
rmdir /s /q core\__pycache__
```

#### 5. 数据库升级
执行 `upgrade_v1.2.0.00.sql` 脚本：
```sql
-- 在 MySQL 中执行
source G:/mini-db-query/upgrade_v1.2.0.00.sql
```

或手动执行以下关键 SQL：
```sql
-- 创建学校-模板绑定表
CREATE TABLE IF NOT EXISTS school_template_bindings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    school_id INT NOT NULL,
    template_id INT NOT NULL,
    database_config_id INT,
    is_enabled TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_school_template (school_id, template_id),
    FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE CASCADE,
    FOREIGN KEY (template_id) REFERENCES query_templates(id) ON DELETE CASCADE
);
```

#### 6. 启动服务
```bash
cd G:\mini-db-query\backend
python main.py
```

### 更新内容

#### v1.2.0.02
- 修复：完善升级包，包含所有必要的 API 文件
- 新增：学校-模板绑定功能 (bindings.py)
- 新增：数据库分析功能 (database_analysis.py)
- 更新：权限管理、业务大类、查询条件 API

#### v1.2.0.01
- 智能查询功能重构
- 新增 school_template_bindings 表
- 支持一校多库配置

# v1.2.0.04 升级包

## 更新内容

1. **修复业务大类加载问题** - 页面初始化时自动加载业务大类数据
2. **数据库修复** - system_configs 表添加缺失字段

## 文件清单

```
upgrade_v1.2.0.04/
├── README.md
├── backend/
│   ├── admin/index.html
│   └── version.py
└── scripts/
    └── upgrade_v1.2.0.04.sql
```

## 升级步骤

### 1. 执行数据库升级脚本

```sql
-- 登录MySQL后执行
source upgrade_v1.2.0.04.sql

-- 或直接执行SQL
ALTER TABLE system_configs ADD COLUMN display_name VARCHAR(100) NULL COMMENT '显示名称';
ALTER TABLE system_configs ADD COLUMN description TEXT NULL COMMENT '描述';
ALTER TABLE system_configs ADD COLUMN category VARCHAR(50) DEFAULT 'system' COMMENT '分类: wechat/system/security';
```

### 2. 替换后端文件

- 覆盖 `backend/admin/index.html`
- 覆盖 `backend/version.py`

### 3. 重启服务

```cmd
# Windows
taskkill /F /IM python.exe
cd backend
python main.py
```

## 版本号

v1.2.0.04

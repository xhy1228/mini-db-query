# 升级包 v1.0.0.33 → v1.0.0.47

## 一、后端升级（直接覆盖）

1. 将 `backend` 文件夹直接复制到项目根目录，覆盖原有文件
   - `backend/api/query.py`
   - `backend/models/database.py`
   - `backend/services/user_service.py`
   - `backend/version.py`

2. 重启后端服务

## 二、数据库升级

直接执行以下SQL语句：

```sql
ALTER TABLE query_logs ADD COLUMN error_detail JSON COMMENT '错误详情';
```

或执行脚本文件：`backend/migrations/升级数据库.sql`

## 三、小程序升级（直接覆盖）

将 `miniapp/pages` 下的文件夹直接复制到小程序项目对应目录：
- `query` 文件夹覆盖
- `sql` 文件夹覆盖
- `login` 文件夹覆盖

## 四、更新内容

- v1.0.0.44: 查询错误信息详细化
- v1.0.0.45: 错误详情记录到日志
- v1.0.0.46: 查询结果横向滚动+导出功能
- v1.0.0.47: 登录页面科技感背景

# v1.2.0.34 → v1.2.0.35 升级说明

## 升级内容
- 分页查询功能（每页50条）
- 上一页/下一页翻页
- 刷新查询按钮
- 总条数显示
- 导出Excel优化

## 文件变更
### 后端
- backend/api/query.py
- backend/api/bindings.py
- backend/api/manage.py
- backend/models/database.py
- backend/admin/index.html

### 前端
- miniapp/pages/query/query.js, .wxml, .wxss
- miniapp/pages/index/index.js, .wxml, .wxss
- miniapp/pages/profile/profile.js, .wxml, .wxss

## 升级步骤
1. 解压覆盖对应文件
2. 重启后端服务
3. 小程序刷新即可

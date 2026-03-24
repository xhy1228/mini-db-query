# 小程序图片资源

## 图标列表

### TabBar 图标 (81x81px)

| 文件名 | 用途 | 风格 |
|--------|------|------|
| home.png | 首页图标（未选中） | 灰色线条 |
| home-active.png | 首页图标（选中） | 蓝色发光 |
| query.png | 查询图标（未选中） | 灰色线条 |
| query-active.png | 查询图标（选中） | 蓝色发光 |
| history.png | 历史图标（未选中） | 灰色线条 |
| history-active.png | 历史图标（选中） | 蓝色发光 |
| profile.png | 我的图标（未选中） | 灰色线条 |
| profile-active.png | 我的图标（选中） | 蓝色发光 |

### 其他图标

| 文件名 | 尺寸 | 用途 |
|--------|------|------|
| default-avatar.png | 200x200px | 默认用户头像 |
| logo.png | 512x512px | 应用Logo |
| empty.png | 160x160px | 空状态图标 |

## 设计风格

- **主题**: 科技感
- **颜色**: 
  - 激活状态: `#1890ff` (蓝色)
  - 未激活状态: `#999999` (灰色)
- **风格**: 简洁、线性、发光效果
- **格式**: PNG 透明背景

## 图标生成

所有图标均由 Python PIL 自动生成，确保风格统一。

```python
# 图标已在 2026-03-17 自动生成
# 如需重新生成，请运行:
python scripts/generate_icons.py
```

## 使用方式

小程序 `app.json` 配置:

```json
{
  "tabBar": {
    "list": [
      {
        "pagePath": "pages/index/index",
        "text": "首页",
        "iconPath": "images/home.png",
        "selectedIconPath": "images/home-active.png"
      }
    ]
  }
}
```

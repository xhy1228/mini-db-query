# 小程序图片资源说明

由于图片文件为二进制文件，请自行准备以下图标：

## TabBar 图标（必需）

| 文件名 | 尺寸 | 用途 | 建议 |
|--------|------|------|------|
| home.png | 81x81px | 首页图标 | 房子轮廓，灰色 |
| home-active.png | 81x81px | 首页选中 | 房子填充，蓝色 #1890ff |
| query.png | 81x81px | 查询图标 | 放大镜轮廓，灰色 |
| query-active.png | 81x81px | 查询选中 | 放大镜填充，蓝色 |
| history.png | 81x81px | 历史图标 | 时钟轮廓，灰色 |
| history-active.png | 81x81px | 历史选中 | 时钟填充，蓝色 |
| profile.png | 81x81px | 我的图标 | 用户轮廓，灰色 |
| profile-active.png | 81x81px | 我的选中 | 用户填充，蓝色 |

## 其他图标（可选）

| 文件名 | 尺寸 | 用途 |
|--------|------|------|
| default-avatar.png | 200x200px | 默认用户头像 |
| logo.png | 512x512px | 应用Logo |

## 图标设计规范

1. **格式**: PNG 格式，支持透明背景
2. **尺寸**: 81x81 像素（推荐 2 倍图 162x162px）
3. **颜色**: 
   - 未选中: #999999
   - 选中: #1890ff
4. **风格**: 简洁、线性、统一

## 临时解决方案

可以使用微信小程序自带的图标：
```json
{
  "tabBar": {
    "list": [
      {
        "pagePath": "pages/index/index",
        "text": "首页"
        // 不设置 iconPath 使用默认样式
      }
    ]
  }
}
```

## 图标下载推荐

- [阿里巴巴矢量图标库](https://www.iconfont.cn/)
- [Flaticon](https://www.flaticon.com/)
- [Icons8](https://icons8.com/)

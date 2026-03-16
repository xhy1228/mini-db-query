// pages/profile/profile.js
// 个人中心页面

const app = getApp()

Page({
  data: {
    userInfo: {
      nickname: '用户',
      avatar: '',
      role: 'user'
    },
    version: '1.0.0'
  },

  onLoad() {
    this.loadUserInfo()
  },

  onShow() {
    this.loadUserInfo()
  },

  // 加载用户信息
  loadUserInfo() {
    const userInfo = wx.getStorageSync('userInfo') || {}
    this.setData({ 
      userInfo: {
        ...userInfo,
        nickname: userInfo.nickname || '用户',
        role: userInfo.role || 'user'
      }
    })
  },

  // 快捷操作
  onQuickAction(e) {
    const action = e.currentTarget.dataset.action
    
    switch (action) {
      case 'history':
        wx.navigateTo({ url: '/pages/history/history' })
        break
      case 'favorites':
        wx.showToast({ title: '功能开发中', icon: 'none' })
        break
      case 'export':
        wx.showToast({ title: '功能开发中', icon: 'none' })
        break
    }
  },

  // 菜单点击
  onMenuTap(e) {
    const menu = e.currentTarget.dataset.menu
    
    switch (menu) {
      case 'configs':
        wx.showModal({
          title: '数据库配置',
          content: '请在管理后台配置数据库连接',
          showCancel: false
        })
        break
      case 'templates':
        wx.showModal({
          title: '查询模板',
          content: '请在管理后台配置查询模板',
          showCancel: false
        })
        break
      case 'about':
        wx.showModal({
          title: '关于',
          content: '多源数据查询小程序\n版本: v1.0.0\n\n支持MySQL、Oracle、SQL Server等数据库的智能查询',
          showCancel: false
        })
        break
    }
  }
})

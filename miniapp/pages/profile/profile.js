// pages/profile/profile.js
// 个人中心页面

const app = getApp()
const { post } = require('../../utils/request')

Page({
  data: {
    userInfo: null,
    isAdmin: false,
    version: '1.1.0'
  },

  onLoad() {
    this.loadUserInfo()
  },

  onShow() {
    this.loadUserInfo()
  },

  // 加载用户信息
  loadUserInfo() {
    const userInfo = wx.getStorageSync('userInfo')
    const userRole = wx.getStorageSync('userRole')
    
    this.setData({
      userInfo: userInfo,
      isAdmin: userRole === 'admin'
    })
  },

  // 退出登录
  logout() {
    wx.showModal({
      title: '确认退出',
      content: '确定要退出登录吗？',
      success: (res) => {
        if (res.confirm) {
          // 清除本地存储
          app.clearUserInfo()
          
          wx.showToast({
            title: '已退出',
            icon: 'success'
          })
          
          // 跳转到登录页
          setTimeout(() => {
            wx.redirectTo({ url: '/pages/login/login' })
          }, 1500)
        }
      }
    })
  },

  // 快捷操作
  onQuickAction(e) {
    const action = e.currentTarget.dataset.action
    
    switch (action) {
      case 'history':
        wx.switchTab({ url: '/pages/history/history' })
        break
      case 'query':
        wx.switchTab({ url: '/pages/query/query' })
        break
      case 'about':
        this.showAbout()
        break
    }
  },

  // 显示关于
  showAbout() {
    wx.showModal({
      title: '关于',
      content: `多源数据查询小程序
版本: v${this.data.version}

支持MySQL、Oracle、SQL Server等
多种数据库的智能查询

© 2026 飞书百万`,
      showCancel: false
    })
  },

  // 菜单点击
  onMenuTap(e) {
    const menu = e.currentTarget.dataset.menu
    
    switch (menu) {
      case 'about':
        this.showAbout()
        break
      case 'logout':
        this.logout()
        break
    }
  }
})

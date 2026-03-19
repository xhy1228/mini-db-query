// pages/profile/profile.js
// 个人中心页面

const app = getApp()
const { post, get } = require('../../utils/request')

Page({
  data: {
    userInfo: null,
    isAdmin: false,
    version: '1.0.0',
    serverUrl: '',
    // 统计数据
    stats: {
      queryCount: 0,
      schoolCount: 0
    }
  },

  onLoad() {
    this.loadUserInfo()
    this.loadStats()
    this.getServerUrl()
    this.loadVersion()
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

  // 加载统计数据
  async loadStats() {
    try {
      // 获取查询历史数量
      const historyRes = await get('/user/history?limit=1')
      if (historyRes.code === 200) {
        this.setData({
          'stats.queryCount': historyRes.total || 0
        })
      }
      
      // 获取学校数量
      const schoolsRes = await get('/user/schools')
      if (schoolsRes.code === 200) {
        this.setData({
          'stats.schoolCount': (schoolsRes.data || []).length
        })
      }
    } catch (error) {
      console.error('加载统计失败:', error)
    }
  },

  // 获取服务器地址
  getServerUrl() {
    const request = require('../../utils/request')
    this.setData({
      serverUrl: request.BASE_URL || ''
    })
  },

  // 加载版本号
  async loadVersion() {
    try {
      const res = await get('/version')
      if (res.code === 200 && res.data.version) {
        this.setData({ version: res.data.version })
      }
    } catch (error) {
      console.error('获取版本失败:', error)
    }
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
      case 'sql':
        // SQL查询 - 仅管理员
        if (this.data.isAdmin) {
          wx.navigateTo({ url: '/pages/sql/sql' })
        } else {
          wx.showToast({ title: '权限不足', icon: 'none' })
        }
        break
      case 'admin':
        // 管理后台 - 仅管理员
        if (this.data.isAdmin) {
          wx.setClipboardData({
            data: this.data.serverUrl.replace('/api', '/admin/'),
            success: () => {
              wx.showToast({ title: '链接已复制', icon: 'success' })
            }
          })
        }
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

新功能：
• SQL直接查询（管理员）
• 数据导出Excel
• 查询历史详情

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
  },

  // 复制服务器地址
  copyServerUrl() {
    if (this.data.serverUrl) {
      wx.setClipboardData({
        data: this.data.serverUrl,
        success: () => {
          wx.showToast({ title: '已复制', icon: 'success' })
        }
      })
    }
  },
  
  // 清除我的数据
  clearMyData() {
    wx.showModal({
      title: '清除数据',
      content: '确定要清除您的查询历史和导出文件吗？此操作不可恢复。',
      confirmText: '确定清除',
      confirmColor: '#ff4d4f',
      success: async (res) => {
        if (res.confirm) {
          wx.showLoading({ title: '清除中...' })
          
          try {
            const result = await del('/security/my-data')
            wx.hideLoading()
            
            if (result.code === 200) {
              wx.showModal({
                title: '清除成功',
                content: '您的数据已成功清除',
                showCancel: false,
                success: () => {
                  // 刷新统计数据
                  this.loadStats()
                }
              })
            } else {
              wx.showToast({
                title: result.message || '清除失败',
                icon: 'none'
              })
            }
          } catch (error) {
            wx.hideLoading()
            wx.showToast({
              title: '清除失败',
              icon: 'none'
            })
          }
        }
      }
    })
  },
  
  // 注销账号
  deleteMyAccount() {
    wx.showModal({
      title: '注销账号',
      content: '注销后将删除所有个人数据，且无法恢复。\n\n请确认：\n• 您已了解此操作不可逆\n• 您的所有数据将被永久删除',
      confirmText: '继续注销',
      confirmColor: '#ff4d4f',
      cancelText: '取消',
      success: (res) => {
        if (res.confirm) {
          // 第二步：要求输入密码
          this.showPasswordInput()
        }
      }
    })
  },
  
  // 显示密码输入框
  showPasswordInput() {
    wx.showModal({
      title: '验证身份',
      content: '请输入您的登录密码以确认注销',
      editable: true,
      placeholderText: '请输入登录密码',
      success: (res) => {
        if (res.confirm && res.content) {
          const password = res.content
          if (!password) {
            wx.showToast({ title: '请输入密码', icon: 'none' })
            return
          }
          // 第三步：要求输入确认文本
          this.showConfirmTextInput(password)
        }
      }
    })
  },
  
  // 显示确认文本输入框
  showConfirmTextInput(password) {
    wx.showModal({
      title: '最终确认',
      content: '为确认您知晓风险，请输入「我已知晓」',
      editable: true,
      placeholderText: '我已知晓',
      confirmText: '确认注销',
      confirmColor: '#ff4d4f',
      success: (res) => {
        if (res.confirm && res.content) {
          const confirmText = res.content
          if (confirmText !== '我已知晓') {
            wx.showToast({ title: '输入错误，请重新操作', icon: 'none' })
            return
          }
          // 执行注销
          this.doDeleteAccount(password)
        }
      }
    })
  },
  
  // 执行账号注销
  async doDeleteAccount(password) {
    wx.showLoading({ title: '注销中...' })
    
    try {
      const result = await post('/security/account/delete', {
        password: password,
        confirm_text: '我已知晓'
      })
      
      wx.hideLoading()
      
      if (result.code === 200) {
        // 注销成功，清除本地存储
        wx.showModal({
          title: '注销成功',
          content: '您的账号已成功注销，感谢您的使用！',
          showCancel: false,
          success: () => {
            // 清除所有本地存储
            app.clearUserInfo()
            wx.clearStorageSync()
            // 跳转到登录页
            wx.reLaunch({ url: '/pages/login/login' })
          }
        })
      } else {
        wx.showToast({
          title: result.message || '注销失败',
          icon: 'none'
        })
      }
    } catch (error) {
      wx.hideLoading()
      wx.showToast({
        title: '注销失败，请重试',
        icon: 'none'
      })
    }
  }
})

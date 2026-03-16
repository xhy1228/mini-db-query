// pages/login/login.js
// 登录页面

const { post, setToken } = require('../../utils/request')

Page({
  data: {
    phone: '',
    password: '',
    showPassword: false,
    loading: false
  },

  onLoad(options) {
    // 检查是否已登录
    this.checkLogin()
  },

  // 检查登录状态
  checkLogin() {
    const token = wx.getStorageSync('token')
    if (token) {
      // 已登录，跳转到首页
      wx.switchTab({ url: '/pages/index/index' })
    }
  },

  // 输入手机号
  onPhoneInput(e) {
    this.setData({ phone: e.detail.value })
  },

  // 输入密码
  onPasswordInput(e) {
    this.setData({ password: e.detail.value })
  },

  // 切换密码可见
  togglePassword() {
    this.setData({ showPassword: !this.data.showPassword })
  },

  // 登录
  async doLogin() {
    const { phone, password } = this.data

    // 验证输入
    if (!phone) {
      wx.showToast({ title: '请输入手机号', icon: 'none' })
      return
    }
    if (!password) {
      wx.showToast({ title: '请输入密码', icon: 'none' })
      return
    }

    this.setData({ loading: true })

    try {
      const res = await post('/login', {
        phone: phone,
        password: password
      })

      if (res.code === 200) {
        // 保存token
        wx.setStorageSync('token', res.data.token)
        wx.setStorageSync('userInfo', res.data.user)
        wx.setStorageSync('userRole', res.data.role)

        wx.showToast({
          title: '登录成功',
          icon: 'success',
          duration: 1500
        })

        // 跳转到首页
        setTimeout(() => {
          wx.switchTab({ url: '/pages/index/index' })
        }, 1500)
      } else {
        wx.showToast({
          title: res.message || '登录失败',
          icon: 'none'
        })
      }
    } catch (error) {
      console.error('登录失败:', error)
      wx.showToast({
        title: '网络错误，请重试',
        icon: 'none'
      })
    } finally {
      this.setData({ loading: false })
    }
  },

  // 忘记密码
  onForgotPassword() {
    wx.showModal({
      title: '忘记密码',
      content: '请联系管理员重置密码\n\n管理员联系方式：\n电话：13800138000',
      showCancel: false
    })
  },

  // 联系管理员
  onContactAdmin() {
    wx.showModal({
      title: '联系管理员',
      content: '如有问题请联系管理员\n\n电话：13800138000',
      showCancel: false
    })
  }
})

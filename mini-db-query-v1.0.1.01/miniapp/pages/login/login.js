// pages/login/login.js
// 登录页面

const { post, get, setToken } = require('../../utils/request')

Page({
  data: {
    phone: '',
    password: '',
    showPassword: false,
    loading: false,
    // 微信登录相关
    showBindPhone: false,
    openid: '',
    bindPhone: '',
    bindPassword: ''
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

  // 微信登录
  async doWechatLogin() {
    this.setData({ loading: true })
    
    try {
      // 获取微信登录code
      const loginRes = await wx.login()
      if (!loginRes.code) {
        wx.showToast({ title: '微信登录失败', icon: 'none' })
        return
      }
      
      // 调用后端微信登录接口
      const res = await post('/wechat/login', {
        code: loginRes.code
      })
      
      if (res.code === 200) {
        if (res.data.is_new) {
          // 新用户，需要绑定手机号
          this.setData({
            showBindPhone: true,
            openid: res.data.openid
          })
          wx.showToast({
            title: '请绑定手机号',
            icon: 'none'
          })
        } else {
          // 已绑定用户，直接登录成功
          wx.setStorageSync('token', res.data.token)
          wx.setStorageSync('userInfo', res.data.user)
          wx.setStorageSync('userRole', res.data.role)
          
          wx.showToast({
            title: '登录成功',
            icon: 'success',
            duration: 1500
          })
          
          setTimeout(() => {
            wx.switchTab({ url: '/pages/index/index' })
          }, 1500)
        }
      } else {
        wx.showToast({
          title: res.message || '微信登录失败',
          icon: 'none'
        })
      }
    } catch (error) {
      console.error('微信登录失败:', error)
      wx.showToast({
        title: '网络错误，请重试',
        icon: 'none'
      })
    } finally {
      this.setData({ loading: false })
    }
  },

  // 绑定手机号输入
  onBindPhoneInput(e) {
    this.setData({ bindPhone: e.detail.value })
  },
  
  onBindPasswordInput(e) {
    this.setData({ bindPassword: e.detail.value })
  },

  // 提交绑定手机号
  async doBindPhone() {
    const { openid, bindPhone, bindPassword } = this.data
    
    if (!bindPhone) {
      wx.showToast({ title: '请输入手机号', icon: 'none' })
      return
    }
    if (!bindPassword) {
      wx.showToast({ title: '请输入密码', icon: 'none' })
      return
    }
    
    this.setData({ loading: true })
    
    try {
      const res = await post('/wechat/bind', {
        openid: openid,
        phone: bindPhone,
        password: bindPassword
      })
      
      if (res.code === 200) {
        wx.setStorageSync('token', res.data.token)
        wx.setStorageSync('userInfo', res.data.user)
        wx.setStorageSync('userRole', res.data.role)
        
        wx.showToast({
          title: '绑定成功',
          icon: 'success',
          duration: 1500
        })
        
        setTimeout(() => {
          wx.switchTab({ url: '/pages/index/index' })
        }, 1500)
      } else {
        wx.showToast({
          title: res.message || '绑定失败',
          icon: 'none'
        })
      }
    } catch (error) {
      console.error('绑定失败:', error)
      wx.showToast({
        title: '网络错误，请重试',
        icon: 'none'
      })
    } finally {
      this.setData({ loading: false })
    }
  },
  
  // 取消绑定
  cancelBind() {
    this.setData({
      showBindPhone: false,
      openid: '',
      bindPhone: '',
      bindPassword: ''
    })
  },

  // 账号密码登录
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

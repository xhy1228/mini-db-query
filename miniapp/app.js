// app.js
// 多源数据查询小程序版 - 入口文件

App({
  globalData: {
    userInfo: null,
    token: null,
    baseUrl: 'http://localhost:8000/api' // 开发环境，生产环境需修改
  },

  onLaunch() {
    // 检查登录状态
    this.checkLogin()
  },

  // 检查登录状态
  checkLogin() {
    const token = wx.getStorageSync('token')
    const userInfo = wx.getStorageSync('userInfo')
    
    if (token && userInfo) {
      this.globalData.token = token
      this.globalData.userInfo = userInfo
      
      // 验证token是否有效
      this.verifyToken()
    } else {
      // 自动登录
      this.login()
    }
  },

  // 微信登录
  login() {
    wx.login({
      success: (res) => {
        if (res.code) {
          // 发送code到后端换取token
          wx.request({
            url: `${this.globalData.baseUrl}/auth/wechat-login`,
            method: 'POST',
            data: { code: res.code },
            success: (res) => {
              if (res.data.code === 200) {
                const { token, user } = res.data.data
                this.globalData.token = token
                this.globalData.userInfo = user
                
                // 保存到本地
                wx.setStorageSync('token', token)
                wx.setStorageSync('userInfo', user)
              } else {
                console.error('登录失败:', res.data.message)
              }
            },
            fail: (err) => {
              console.error('登录请求失败:', err)
            }
          })
        }
      }
    })
  },

  // 验证token
  verifyToken() {
    wx.request({
      url: `${this.globalData.baseUrl}/auth/me`,
      method: 'GET',
      header: {
        'Authorization': `Bearer ${this.globalData.token}`
      },
      success: (res) => {
        if (res.data.code !== 200) {
          // token无效，重新登录
          this.login()
        }
      },
      fail: () => {
        this.login()
      }
    })
  }
})

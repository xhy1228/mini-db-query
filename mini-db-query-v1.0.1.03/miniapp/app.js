// app.js
// 小程序入口

App({
  globalData: {
    userInfo: null,
    userRole: null,
    schools: [],
    selectedSchool: null
  },

  onLaunch() {
    // 检查登录状态
    this.checkLoginStatus()
  },

  // 检查登录状态
  checkLoginStatus() {
    const token = wx.getStorageSync('token')
    const userInfo = wx.getStorageSync('userInfo')
    const userRole = wx.getStorageSync('userRole')

    if (token && userInfo) {
      this.globalData.userInfo = userInfo
      this.globalData.userRole = userRole
      return true
    }
    return false
  },

  // 设置用户信息
  setUserInfo(userInfo, token, role) {
    this.globalData.userInfo = userInfo
    this.globalData.userRole = role
    wx.setStorageSync('token', token)
    wx.setStorageSync('userInfo', userInfo)
    wx.setStorageSync('userRole', role)
  },

  // 清除用户信息
  clearUserInfo() {
    this.globalData.userInfo = null
    this.globalData.userRole = null
    this.globalData.schools = []
    this.globalData.selectedSchool = null
    wx.removeStorageSync('token')
    wx.removeStorageSync('userInfo')
    wx.removeStorageSync('userRole')
  },

  // 检查是否已登录
  isLoggedIn() {
    return !!this.globalData.userInfo || !!wx.getStorageSync('token')
  },

  // 检查是否是管理员
  isAdmin() {
    return this.globalData.userRole === 'admin'
  }
})

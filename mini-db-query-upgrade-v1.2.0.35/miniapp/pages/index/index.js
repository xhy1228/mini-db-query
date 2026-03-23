// pages/index/index.js
// 首页 - v1.2.0 使用 binding API

const app = getApp()
const { get } = require('../../utils/request')

Page({
  data: {
    // 用户信息
    userInfo: null,
    isAdmin: false,
    
    // 学校列表
    schools: [],
    selectedSchool: null,
    showSchoolPicker: false,
    
    // 业务大类
    categories: [],
    selectedCategory: null,
    showCategoryPicker: false,
    
    // 统计数据
    stats: {
      total_queries: 0,
      today_queries: 0,
      success_rate: 0
    },
    
    // 最近查询
    recentQueries: [],
    
    // 加载状态
    loading: true
  },

  onLoad() {
    // 检查登录状态
    this.checkLogin()
  },

  onShow() {
    // 刷新数据
    if (app.isLoggedIn()) {
      this.loadData()
    }
  },

  // 检查登录
  checkLogin() {
    if (!app.isLoggedIn()) {
      wx.redirectTo({ url: '/pages/login/login' })
      return
    }
    
    this.setData({
      userInfo: app.globalData.userInfo,
      isAdmin: app.isAdmin()
    })
    
    this.loadData()
  },

  // 加载数据
  async loadData() {
    this.setData({ loading: true })
    
    try {
      // 获取用户授权的学校
      const schoolsRes = await get('/user/schools')
      
      if (schoolsRes.code === 200) {
        const schools = schoolsRes.data || []
        
        this.setData({
          schools,
          loading: false
        })
        
        // 如果只有一个学校，自动选择
        if (schools.length === 1) {
          this.selectSchool(schools[0])
        }
      }
      
      // 加载统计数据
      this.loadStats()
      
      // 加载最近查询
      this.loadRecentQueries()
    } catch (error) {
      console.error('加载数据失败:', error)
      this.setData({ loading: false })
      
      // 使用模拟数据
      this.setData({
        schools: this.getMockSchools()
      })
    }
  },

  // 加载统计数据
  async loadStats() {
    try {
      const res = await get('/stats/dashboard')
      if (res.code === 200) {
        this.setData({ stats: res.data })
      }
    } catch (error) {
      console.error('加载统计失败:', error)
    }
  },

  // 加载最近查询
  async loadRecentQueries() {
    try {
      const res = await get('/user/history?limit=5')
      if (res.code === 200) {
        const recentQueries = (res.data || []).map(item => ({
          ...item,
          timeText: this.formatRecentTime(item.created_at)
        }))
        this.setData({ recentQueries })
      }
    } catch (error) {
      console.error('加载最近查询失败:', error)
    }
  },

  // 格式化最近查询时间
  formatRecentTime(timeStr) {
    if (!timeStr) return ''
    const date = new Date(timeStr)
    const now = new Date()
    const diff = now - date
    
    if (diff < 60000) return '刚刚'
    if (diff < 3600000) return `${Math.floor(diff/60000)}分钟前`
    if (diff < 86400000) return `${Math.floor(diff/3600000)}小时前`
    return `${Math.floor(diff/86400000)}天前`
  },

  // 获取模拟学校数据
  getMockSchools() {
    return [
      { id: 1, name: '示例学校A', code: 'SCHOOL_A' },
      { id: 2, name: '示例学校B', code: 'SCHOOL_B' }
    ]
  },

  // 选择学校
  async selectSchool(school) {
    this.setData({ 
      selectedSchool: school,
      selectedCategory: null,
      categories: []
    })
    
    // 保存到全局
    app.globalData.selectedSchool = school
    
    // 加载该学校的业务大类（使用新API）
    try {
      const res = await get(`/schools/${school.id}/functions`)
      
      if (res.code === 200 && res.data) {
        this.setData({ 
          categories: res.data.categories || [],
          // 默认选中第一个
          selectedCategory: res.data.categories && res.data.categories.length > 0 
            ? res.data.categories[0] 
            : null
        })
      }
    } catch (error) {
      console.error('加载业务大类失败:', error)
    }
  },

  // 显示学校选择器
  showSchoolPicker() {
    this.setData({ showSchoolPicker: true })
  },

  // 隐藏学校选择器
  hideSchoolPicker() {
    this.setData({ showSchoolPicker: false })
  },

  // 选择学校（从弹窗）
  onSchoolSelect(e) {
    const school = e.currentTarget.dataset.school
    this.selectSchool(school)
    this.setData({ showSchoolPicker: false })
  },

  // 显示业务大类选择器
  showCategoryPicker() {
    this.setData({ showCategoryPicker: true })
  },

  // 隐藏业务大类选择器
  hideCategoryPicker() {
    this.setData({ showCategoryPicker: false })
  },

  // 选择业务大类（从弹窗）
  onCategorySelect(e) {
    const category = e.currentTarget.dataset.category
    this.setData({ 
      selectedCategory: category,
      showCategoryPicker: false
    })
  },

  // 开始查询
  startQuery() {
    const { selectedSchool, selectedCategory } = this.data
    if (!selectedSchool) {
      wx.showToast({ title: '请先选择学校', icon: 'none' })
      return
    }
    if (!selectedCategory) {
      wx.showToast({ title: '请先选择业务大类', icon: 'none' })
      return
    }
    
    // 跳转到查询页面
    wx.switchTab({
      url: `/pages/query/query?school_id=${selectedSchool.id}&category=${selectedCategory.category}&category_name=${encodeURIComponent(selectedCategory.category_name)}`
    })
  },

  // 点击学校卡片
  onSchoolTap(e) {
    const school = e.currentTarget.dataset.school
    this.selectSchool(school)
  },

  // 点击业务大类
  onCategoryTap(e) {
    const category = e.currentTarget.dataset.category
    const school = this.data.selectedSchool
    
    if (!school) {
      wx.showToast({ title: '请先选择学校', icon: 'none' })
      return
    }
    
    // 跳转到查询页面
    wx.switchTab({
      url: `/pages/query/query?school_id=${school.id}&category=${category.id}&category_name=${encodeURIComponent(category.name)}`
    })
  },

  // 跳转到查询页
  goToQuery() {
    wx.switchTab({ url: '/pages/query/query' })
  },

  // 跳转到历史页
  goToHistory() {
    wx.switchTab({ url: '/pages/history/history' })
  },

  // 跳转到我的
  goToProfile() {
    wx.switchTab({ url: '/pages/profile/profile' })
  },

  // 下拉刷新
  onPullDownRefresh() {
    this.loadData().finally(() => {
      wx.stopPullDownRefresh()
    })
  }
})

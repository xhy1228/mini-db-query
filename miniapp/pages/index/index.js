// pages/index/index.js
// 首页

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
    
    // 业务大类
    categories: [],
    
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
    } catch (error) {
      console.error('加载数据失败:', error)
      this.setData({ loading: false })
      
      // 使用模拟数据
      this.setData({
        schools: this.getMockSchools()
      })
    }
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
    this.setData({ selectedSchool: school })
    
    // 保存到全局
    app.globalData.selectedSchool = school
    
    // 加载该学校的业务大类
    try {
      const res = await get(`/user/categories?school_id=${school.id}`)
      
      if (res.code === 200) {
        this.setData({ categories: res.data || [] })
      }
    } catch (error) {
      console.error('加载业务大类失败:', error)
      
      // 使用模拟数据
      this.setData({
        categories: this.getMockCategories()
      })
    }
  },

  // 获取模拟业务大类
  getMockCategories() {
    return [
      { id: 'student', name: '学生业务', icon: '🎓', count: 5 },
      { id: 'consume', name: '消费业务', icon: '💰', count: 8 },
      { id: 'access', name: '门禁业务', icon: '🚪', count: 4 }
    ]
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

  // 下拉刷新
  onPullDownRefresh() {
    this.loadData().finally(() => {
      wx.stopPullDownRefresh()
    })
  }
})

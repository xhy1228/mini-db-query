// pages/index/index.js
// 首页

const { get } = require('../../utils/request')

Page({
  data: {
    // 业务大类列表
    categories: [],
    // 数据库配置列表
    configs: [],
    // 加载状态
    loading: true,
    // 用户信息
    userInfo: null,
    // 系统信息
    systemInfo: null,
    // 快捷入口
    quickEntries: [
      { id: 'smart', name: '智能查询', icon: '🧠', color: '#1890ff' },
      { id: 'sql', name: 'SQL查询', icon: '📝', color: '#52c41a' },
      { id: 'history', name: '查询历史', icon: '📋', color: '#faad14' },
      { id: 'export', name: '导出记录', icon: '📥', color: '#722ed1' }
    ]
  },

  onLoad() {
    this.loadSystemInfo()
    this.loadData()
  },

  onShow() {
    // 每次显示都刷新数据
    this.loadData()
  },

  onPullDownRefresh() {
    this.loadData().finally(() => {
      wx.stopPullDownRefresh()
    })
  },

  // 加载系统信息
  loadSystemInfo() {
    const systemInfo = wx.getSystemInfoSync()
    this.setData({ systemInfo })
  },

  // 加载数据
  async loadData() {
    this.setData({ loading: true })
    
    try {
      // 尝试加载后端数据
      const [categoriesRes, configsRes] = await Promise.all([
        get('/query/categories'),
        get('/query/configs')
      ])
      
      // 如果后端有数据则使用后端数据，否则使用模拟数据
      const categories = categoriesRes.code === 200 ? categoriesRes.data : this.getMockCategories()
      const configs = configsRes.code === 200 ? configsRes.data : this.getMockConfigs()
      
      this.setData({
        categories,
        configs,
        loading: false
      })
    } catch (error) {
      console.error('加载数据失败，使用模拟数据:', error)
      // 后端不可用时使用模拟数据
      this.setData({
        categories: this.getMockCategories(),
        configs: this.getMockConfigs(),
        loading: false
      })
    }
  },

  // 获取模拟业务大类数据
  getMockCategories() {
    return [
      { id: 'student', name: '学生业务', icon: '🎓', description: '学生信息查询', count: 5 },
      { id: 'consume', name: '消费业务', icon: '💰', description: '消费充值记录', count: 8 },
      { id: 'access', name: '门禁业务', icon: '🚪', description: '进出记录查询', count: 4 },
      { id: 'wechat', name: '微信业务', icon: '💬', description: '微信用户查询', count: 3 }
    ]
  },

  // 获取模拟数据库配置
  getMockConfigs() {
    return [
      { name: '一卡通Oracle', db_type: 'Oracle', status: 'online', description: '一卡通系统数据库' },
      { name: '微信MySQL', db_type: 'MySQL', status: 'online', description: '微信系统数据库' },
      { name: 'SQLServer测试', db_type: 'SQLServer', status: 'offline', description: '测试数据库' }
    ]
  },

  // 选择业务大类
  onCategoryTap(e) {
    const { id, name } = e.currentTarget.dataset
    wx.navigateTo({
      url: `/pages/query/query?categoryId=${id}&categoryName=${encodeURIComponent(name)}`
    })
  },

  // 选择数据库配置
  onConfigTap(e) {
    const { name } = e.currentTarget.dataset
    wx.navigateTo({
      url: `/pages/query/query?configName=${encodeURIComponent(name)}`
    })
  },

  // 快捷入口点击
  onQuickEntryTap(e) {
    const { id } = e.currentTarget.dataset
    
    switch (id) {
      case 'smart':
      case 'sql':
        wx.switchTab({ url: '/pages/query/query' })
        break
      case 'history':
        wx.navigateTo({ url: '/pages/history/history' })
        break
      case 'export':
        wx.showToast({ title: '功能开发中', icon: 'none' })
        break
    }
  },

  // 跳转到查询页面
  goToQuery() {
    wx.switchTab({ url: '/pages/query/query' })
  },

  // 跳转到个人中心
  goToProfile() {
    wx.switchTab({ url: '/pages/profile/profile' })
  }
})

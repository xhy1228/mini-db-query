// pages/index/index.js
// 首页

const { get } = require('../../utils/request')

Page({
  data: {
    categories: [],
    configs: [],
    loading: true
  },

  onLoad() {
    this.loadData()
  },

  onPullDownRefresh() {
    this.loadData().then(() => {
      wx.stopPullDownRefresh()
    })
  },

  async loadData() {
    try {
      // 并行加载业务大类和数据库配置
      const [categoriesRes, configsRes] = await Promise.all([
        get('/query/categories'),
        get('/query/configs')
      ])
      
      this.setData({
        categories: categoriesRes.data || [],
        configs: configsRes.data || [],
        loading: false
      })
    } catch (error) {
      console.error('加载数据失败:', error)
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      })
      this.setData({ loading: false })
    }
  },

  // 选择业务大类
  onCategoryTap(e) {
    const { id, name } = e.currentTarget.dataset
    wx.navigateTo({
      url: `/pages/query/query?categoryId=${id}&categoryName=${name}`
    })
  },

  // 选择数据库配置
  onConfigTap(e) {
    const { name } = e.currentTarget.dataset
    wx.navigateTo({
      url: `/pages/query/query?configName=${name}`
    })
  }
})

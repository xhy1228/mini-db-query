// pages/history/history.js
// 历史记录页面

const app = getApp()
const { get } = require('../../utils/request')

Page({
  data: {
    historyList: [],
    loading: true,
    page: 1,
    hasMore: true
  },

  onLoad() {
    // 检查登录
    if (!app.isLoggedIn()) {
      wx.redirectTo({ url: '/pages/login/login' })
      return
    }
    
    this.loadHistory()
  },

  onShow() {
    // 刷新数据
    if (app.isLoggedIn()) {
      this.setData({ page: 1, hasMore: true })
      this.loadHistory()
    }
  },

  // 加载历史记录
  async loadHistory() {
    if (!this.data.hasMore && this.data.page > 1) return
    
    this.setData({ loading: true })
    
    try {
      const res = await get('/user/history', {
        skip: (this.data.page - 1) * 30,
        limit: 30
      })
      
      if (res.code === 200) {
        const list = res.data || []
        
        // 格式化数据
        const formattedList = list.map(item => ({
          ...item,
          timeText: this.formatTime(item.created_at),
          statusText: item.status === 'success' ? '成功' : '失败',
          statusClass: item.status === 'success' ? 'success' : 'failed'
        }))
        
        if (this.data.page === 1) {
          this.setData({ historyList: formattedList })
        } else {
          this.setData({ 
            historyList: [...this.data.historyList, ...formattedList]
          })
        }
        
        this.setData({
          hasMore: list.length === 30,
          loading: false
        })
      }
    } catch (error) {
      console.error('加载历史记录失败:', error)
      
      // 使用本地存储作为备用
      const localHistory = wx.getStorageSync('queryHistory') || []
      this.setData({ 
        historyList: localHistory,
        loading: false,
        hasMore: false
      })
    }
  },

  // 格式化时间
  formatTime(timeStr) {
    if (!timeStr) return ''
    
    const date = new Date(timeStr)
    const now = new Date()
    const diff = now - date
    
    // 今天
    if (diff < 86400000) {
      return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
    }
    
    // 昨天
    if (diff < 172800000) {
      return `昨天 ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
    }
    
    // 其他
    return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
  },

  // 点击历史记录
  onHistoryTap(e) {
    const item = e.currentTarget.dataset.item
    
    // 设置全局学校
    if (item.school_id) {
      app.globalData.selectedSchool = { id: item.school_id }
    }
    
    // 跳转到查询页面
    wx.switchTab({
      url: '/pages/query/query',
      success: () => {
        // 可以通过事件传递查询信息
      }
    })
  },

  // 下拉刷新
  onPullDownRefresh() {
    this.setData({ page: 1, hasMore: true })
    this.loadHistory().finally(() => {
      wx.stopPullDownRefresh()
    })
  },

  // 上拉加载更多
  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) {
      this.setData({ page: this.data.page + 1 })
      this.loadHistory()
    }
  },

  // 清空历史
  clearHistory() {
    wx.showModal({
      title: '确认清空',
      content: '确定要清空所有查询历史吗？',
      success: (res) => {
        if (res.confirm) {
          wx.setStorageSync('queryHistory', [])
          this.setData({ historyList: [] })
          wx.showToast({
            title: '已清空',
            icon: 'success'
          })
        }
      }
    })
  }
})

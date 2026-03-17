// pages/history/history.js
// 历史记录页面

const app = getApp()
const { get } = require('../../utils/request')

Page({
  data: {
    historyList: [],
    loading: true,
    page: 1,
    hasMore: true,
    total: 0,
    // 筛选条件
    showFilter: false,
    filterStatus: '',
    filterSchoolId: null,
    schools: [],
    startDate: '',
    endDate: ''
  },

  onLoad() {
    // 检查登录
    if (!app.isLoggedIn()) {
      wx.redirectTo({ url: '/pages/login/login' })
      return
    }
    
    this.loadSchools()
    this.loadHistory()
  },

  onShow() {
    // 刷新数据
    if (app.isLoggedIn()) {
      this.setData({ page: 1, hasMore: true })
      this.loadHistory()
    }
  },

  // 加载学校列表（用于筛选）
  async loadSchools() {
    try {
      const res = await get('/user/schools')
      if (res.code === 200) {
        this.setData({ schools: res.data || [] })
      }
    } catch (error) {
      console.error('加载学校失败:', error)
    }
  },

  // 加载历史记录
  async loadHistory() {
    if (!this.data.hasMore && this.data.page > 1) return
    
    this.setData({ loading: true })
    
    try {
      let url = `/user/history?skip=${(this.data.page - 1) * 30}&limit=30`
      
      // 添加筛选条件
      if (this.data.filterStatus) {
        url += `&status=${this.data.filterStatus}`
      }
      if (this.data.filterSchoolId) {
        url += `&school_id=${this.data.filterSchoolId}`
      }
      if (this.data.startDate) {
        url += `&start_date=${this.data.startDate}`
      }
      if (this.data.endDate) {
        url += `&end_date=${this.data.endDate}`
      }
      
      const res = await get(url)
      
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
          this.setData({ 
            historyList: formattedList,
            total: res.total || list.length
          })
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
      return `今天 ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
    }
    
    // 昨天
    if (diff < 172800000) {
      return `昨天 ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
    }
    
    // 其他
    return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
  },

  // 点击历史记录 - 查看详情
  onHistoryTap(e) {
    const item = e.currentTarget.dataset.item
    
    wx.navigateTo({
      url: `/pages/history-detail/history-detail?id=${item.id}`
    })
  },

  // 切换筛选面板
  toggleFilter() {
    this.setData({ showFilter: !this.data.showFilter })
  },

  // 状态筛选
  onStatusChange(e) {
    this.setData({ filterStatus: e.detail.value })
  },

  // 学校筛选
  onSchoolChange(e) {
    const index = e.detail.value
    if (index === '0') {
      this.setData({ filterSchoolId: null })
    } else {
      const school = this.data.schools[index - 1]
      this.setData({ filterSchoolId: school.id })
    }
  },

  // 日期筛选
  onStartDateChange(e) {
    this.setData({ startDate: e.detail.value })
  },

  onEndDateChange(e) {
    this.setData({ endDate: e.detail.value })
  },

  // 应用筛选
  applyFilter() {
    this.setData({ 
      page: 1, 
      hasMore: true,
      showFilter: false
    })
    this.loadHistory()
  },

  // 重置筛选
  resetFilter() {
    this.setData({
      filterStatus: '',
      filterSchoolId: null,
      startDate: '',
      endDate: ''
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
          this.setData({ historyList: [], total: 0 })
          wx.showToast({
            title: '已清空',
            icon: 'success'
          })
        }
      }
    })
  }
})

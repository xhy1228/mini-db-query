// pages/history/history.js
// 查询历史页面

const app = getApp()
const { get, del } = require('../../utils/request')

Page({
  data: {
    // 历史记录列表
    historyList: [],
    
    // 加载状态
    loading: true,
    loadingMore: false,
    
    // 分页
    page: 1,
    pageSize: 20,
    hasMore: true,
    
    // 当前选中的记录
    selectedRecord: null,
    showDetailModal: false,
    detailData: []
  },

  onLoad() {
    // 检查登录
    if (!app.isLoggedIn()) {
      wx.redirectTo({ url: '/pages/login/login' })
      return
    }
    
    this.loadHistory()
  },

  // 加载历史记录
  async loadHistory() {
    this.setData({ loading: true })
    
    try {
      const res = await get('/user/history', {
        page: 1,
        page_size: this.data.pageSize
      })
      
      if (res.code === 200) {
        const historyList = (res.data || []).map(item => ({
          ...item,
          timeText: this.formatTime(item.created_at)
        }))
        
        this.setData({
          historyList,
          page: 1,
          hasMore: res.data.length >= this.data.pageSize,
          loading: false
        })
      } else {
        this.setData({ loading: false })
        wx.showToast({ title: res.message || '加载失败', icon: 'none' })
      }
    } catch (error) {
      console.error('加载历史失败:', error)
      this.setData({ loading: false })
      wx.showToast({ title: '加载失败', icon: 'none' })
    }
  },

  // 格式化时间
  formatTime(timeStr) {
    if (!timeStr) return ''
    const date = new Date(timeStr)
    const now = new Date()
    const diff = now - date
    
    if (diff < 60000) return '刚刚'
    if (diff < 3600000) return `${Math.floor(diff/60000)}分钟前`
    if (diff < 86400000) return `${Math.floor(diff/3600000)}小时前`
    
    // 超过1天显示具体日期
    const month = date.getMonth() + 1
    const day = date.getDate()
    const hour = date.getHours().toString().padStart(2, '0')
    const minute = date.getMinutes().toString().padStart(2, '0')
    
    return `${month}月${day}日 ${hour}:${minute}`
  },

  // 加载更多
  async loadMore() {
    if (this.data.loadingMore || !this.data.hasMore) return
    
    this.setData({ loadingMore: true })
    
    try {
      const nextPage = this.data.page + 1
      const res = await get('/user/history', {
        page: nextPage,
        page_size: this.data.pageSize
      })
      
      if (res.code === 200) {
        const newList = (res.data || []).map(item => ({
          ...item,
          timeText: this.formatTime(item.created_at)
        }))
        
        this.setData({
          historyList: [...this.data.historyList, ...newList],
          page: nextPage,
          hasMore: res.data.length >= this.data.pageSize,
          loadingMore: false
        })
      } else {
        this.setData({ loadingMore: false })
      }
    } catch (error) {
      console.error('加载更多失败:', error)
      this.setData({ loadingMore: false })
    }
  },

  // 查看详情
  async showDetail(e) {
    const logId = e.currentTarget.dataset.id
    
    try {
      const res = await get(`/user/history/${logId}`)
      
      if (res.code === 200 && res.data) {
        const data = res.data
        
        // 转换为详情格式
        const detailData = [
          { label: '查询名称', value: data.query_name || '-' },
          { label: '学校', value: data.school_name || '-' },
          { label: '查询时间', value: data.created_at || '-' },
          { label: '查询条件', value: this.formatConditions(data.conditions) },
          { label: '结果数量', value: data.result_count !== null ? `${data.result_count}条` : '-' },
          { label: '执行时间', value: data.query_time ? `${data.query_time}ms` : '-' },
          { label: '状态', value: data.status === 'success' ? '成功' : '失败' }
        ]
        
        // 如果有错误信息
        if (data.error_message) {
          detailData.push({ label: '错误信息', value: data.error_message })
        }
        
        // 如果有SQL
        if (data.sql) {
          detailData.push({ label: 'SQL', value: data.sql })
        }
        
        this.setData({
          selectedRecord: data,
          showDetailModal: true,
          detailData: detailData
        })
      }
    } catch (error) {
      console.error('获取详情失败:', error)
      wx.showToast({ title: '获取详情失败', icon: 'none' })
    }
  },

  // 格式化查询条件
  formatConditions(conditions) {
    if (!conditions) return '-'
    if (typeof conditions === 'string') {
      try {
        conditions = JSON.parse(conditions)
      } catch {
        return conditions
      }
    }
    if (Array.isArray(conditions)) {
      return conditions.map(c => `${c.label || c.field} ${c.operator || '='} ${c.value}`).join(', ')
    }
    return '-'
  },

  // 隐藏详情弹窗
  hideDetailModal() {
    this.setData({
      showDetailModal: false,
      selectedRecord: null,
      detailData: []
    })
  },

  // 重新查询
  reQuery(e) {
    const record = e.currentTarget.dataset.record
    if (!record) return
    
    // 跳转到查询页面
    wx.switchTab({
      url: `/pages/query/query?school_id=${record.school_id}`
    })
  },

  // 删除记录
  async deleteRecord(e) {
    const logId = e.currentTarget.dataset.id
    
    wx.showModal({
      title: '确认删除',
      content: '确定要删除这条查询记录吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            const result = await del(`/user/history/${logId}`)
            
            if (result.code === 200) {
              wx.showToast({ title: '删除成功', icon: 'success' })
              // 刷新列表
              this.loadHistory()
            } else {
              wx.showToast({ title: result.message || '删除失败', icon: 'none' })
            }
          } catch (error) {
            console.error('删除失败:', error)
            wx.showToast({ title: '删除失败', icon: 'none' })
          }
        }
      }
    })
  },

  // 清空全部历史
  clearAll() {
    wx.showModal({
      title: '清空历史',
      content: '确定要清空所有查询历史吗？此操作不可恢复。',
      success: async (res) => {
        if (res.confirm) {
          try {
            // 逐条删除
            const list = this.data.historyList
            for (const item of list) {
              await del(`/user/history/${item.id}`)
            }
            
            wx.showToast({ title: '已清空', icon: 'success' })
            this.setData({
              historyList: [],
              hasMore: false
            })
          } catch (error) {
            console.error('清空失败:', error)
            wx.showToast({ title: '清空失败', icon: 'none' })
          }
        }
      }
    })
  },

  // 下拉刷新
  onPullDownRefresh() {
    this.loadHistory().finally(() => {
      wx.stopPullDownRefresh()
    })
  },

  // 上拉加载更多
  onReachBottom() {
    this.loadMore()
  }
})

// pages/history-detail/history-detail.js
// 历史详情页面

const app = getApp()
const { get, post } = require('../../utils/request')

Page({
  data: {
    logId: null,
    logDetail: null,
    loading: true,
    reexecuteLoading: false
  },

  onLoad(options) {
    if (options.id) {
      this.setData({ logId: options.id })
      this.loadDetail()
    }
  },

  // 加载详情
  async loadDetail() {
    this.setData({ loading: true })
    
    try {
      const res = await get(`/user/history/${this.data.logId}`)
      
      if (res.code === 200) {
        this.setData({ 
          logDetail: res.data,
          loading: false
        })
      } else {
        wx.showToast({ title: res.message || '加载失败', icon: 'none' })
        this.setData({ loading: false })
      }
    } catch (error) {
      console.error('加载详情失败:', error)
      wx.showToast({ title: '加载失败', icon: 'none' })
      this.setData({ loading: false })
    }
  },

  // 重新执行查询
  async reexecuteQuery() {
    if (!this.data.logDetail) return
    
    const log = this.data.logDetail
    
    // 检查是否有模板ID
    if (log.template_id) {
      // 使用模板查询
      wx.navigateTo({
        url: `/pages/query/query?template_id=${log.template_id}&school_id=${log.school_id}`
      })
    } else if (log.sql_executed) {
      // 直接SQL查询 - 需要是管理员
      const userInfo = app.globalData.userInfo
      if (!userInfo || userInfo.role !== 'admin') {
        wx.showToast({ title: '仅管理员可重新执行SQL', icon: 'none' })
        return
      }
      
      wx.showModal({
        title: '确认执行',
        content: '确定要重新执行此查询吗？',
        success: async (res) => {
          if (res.confirm) {
            this.setData({ reexecuteLoading: true })
            
            try {
              const result = await post('/user/sql', {
                school_id: log.school_id,
                sql: log.sql_executed
              })
              
              if (result.code === 200) {
                wx.showToast({ title: '执行成功', icon: 'success' })
                // 刷新详情
                this.loadDetail()
              } else {
                wx.showToast({ title: result.message || '执行失败', icon: 'none' })
              }
            } catch (error) {
              wx.showToast({ title: '执行失败', icon: 'none' })
            } finally {
              this.setData({ reexecuteLoading: false })
            }
          }
        }
      })
    }
  },

  // 复制SQL
  copySql() {
    if (!this.data.logDetail || !this.data.logDetail.sql_executed) return
    
    wx.setClipboardData({
      data: this.data.logDetail.sql_executed,
      success: () => {
        wx.showToast({ title: '已复制', icon: 'success' })
      }
    })
  },

  // 复制查询参数
  copyParams() {
    if (!this.data.logDetail || !this.data.logDetail.query_params) return
    
    wx.setClipboardData({
      data: JSON.stringify(this.data.logDetail.query_params, null, 2),
      success: () => {
        wx.showToast({ title: '已复制', icon: 'success' })
      }
    })
  },

  // 删除记录
  async deleteLog() {
    wx.showModal({
      title: '确认删除',
      content: '确定要删除此记录吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            const result = await wx.request({
              url: `${app.globalData.apiBaseUrl}/user/history/${this.data.logId}`,
              method: 'DELETE',
              header: {
                'Authorization': `Bearer ${wx.getStorageSync('token')}`
              }
            })
            
            if (result.data.code === 200) {
              wx.showToast({ title: '已删除', icon: 'success' })
              setTimeout(() => {
                wx.navigateBack()
              }, 1500)
            } else {
              wx.showToast({ title: result.data.message || '删除失败', icon: 'none' })
            }
          } catch (error) {
            console.error('删除失败:', error)
            wx.showToast({ title: '删除失败', icon: 'none' })
          }
        }
      }
    })
  },

  // 格式化时间
  formatTime(timeStr) {
    if (!timeStr) return ''
    const date = new Date(timeStr)
    return date.toLocaleString('zh-CN')
  }
})

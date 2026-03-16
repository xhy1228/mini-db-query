// pages/history/history.js
// 历史记录页面

Page({
  data: {
    historyList: []
  },

  onLoad() {
    this.loadHistory()
  },

  onShow() {
    this.loadHistory()
  },

  // 加载历史记录
  loadHistory() {
    const history = wx.getStorageSync('queryHistory') || []
    this.setData({ historyList: history })
  },

  // 点击历史记录
  onHistoryTap(e) {
    const item = e.currentTarget.dataset.item
    
    // 跳转到查询页面并传递参数
    wx.navigateTo({
      url: `/pages/query/query?configName=${item.config}&categoryId=${item.categoryId}`
    })
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

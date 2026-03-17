// pages/sql/sql.js
// SQL查询页面 - 管理员专用

const app = getApp()
const { post, get } = require('../../utils/request')

Page({
  data: {
    schools: [],
    selectedSchool: null,
    sqlContent: '',
    loading: false,
    results: null,
    error: null,
    history: [],
    showHistory: false
  },

  onLoad() {
    // 检查登录
    if (!app.isLoggedIn()) {
      wx.redirectTo({ url: '/pages/login/login' })
      return
    }
    
    // 检查权限 - 只有管理员才能使用SQL查询
    const userInfo = app.globalData.userInfo
    if (!userInfo || userInfo.role !== 'admin') {
      wx.showModal({
        title: '权限不足',
        content: 'SQL查询功能仅限管理员使用',
        showCancel: false,
        success: () => {
          wx.switchTab({ url: '/pages/index/index' })
        }
      })
      return
    }
    
    this.loadSchools()
    this.loadHistory()
  },

  // 加载学校列表
  async loadSchools() {
    try {
      const res = await get('/user/schools')
      if (res.code === 200) {
        this.setData({ schools: res.data || [] })
        
        // 设置默认选中
        if (this.data.schools.length > 0) {
          this.setData({ selectedSchool: this.data.schools[0] })
        }
      }
    } catch (error) {
      console.error('加载学校失败:', error)
    }
  },

  // 加载SQL历史
  async loadHistory() {
    const history = wx.getStorageSync('sqlHistory') || []
    this.setData({ history: history.slice(0, 10) })
  },

  // 选择学校
  onSchoolChange(e) {
    const index = e.detail.value
    this.setData({ selectedSchool: this.data.schools[index] })
  },

  // SQL输入
  onSqlInput(e) {
    this.setData({ sqlContent: e.detail.value })
  },

  // 执行SQL查询
  async executeSql() {
    if (!this.data.selectedSchool) {
      wx.showToast({ title: '请选择学校', icon: 'none' })
      return
    }
    
    if (!this.data.sqlContent.trim()) {
      wx.showToast({ title: '请输入SQL语句', icon: 'none' })
      return
    }
    
    // 安全检查
    const sql = this.data.sqlContent.trim().toUpperCase()
    if (!sql.startsWith('SELECT')) {
      wx.showToast({ title: '仅支持SELECT查询', icon: 'none' })
      return
    }
    
    const dangerousKeywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'TRUNCATE', 'ALTER', 'CREATE']
    for (const keyword of dangerousKeywords) {
      if (sql.includes(keyword)) {
        wx.showToast({ title: `不允许${keyword}操作`, icon: 'none' })
        return
      }
    }
    
    this.setData({ loading: true, error: null, results: null })
    
    try {
      const res = await post('/user/sql', {
        school_id: this.data.selectedSchool.id,
        sql: this.data.sqlContent.trim()
      })
      
      if (res.code === 200) {
        const data = res.data
        this.setData({ 
          results: {
            rows: data.rows || [],
            count: data.count,
            queryTime: data.query_time,
            sql: data.sql
          }
        })
        
        // 保存到历史
        this.saveToHistory()
        
        wx.showToast({ title: `查询成功，${data.count}条`, icon: 'success' })
      } else {
        this.setData({ error: res.message })
        wx.showToast({ title: res.message, icon: 'none' })
      }
    } catch (error) {
      console.error('SQL查询失败:', error)
      this.setData({ error: error.message || '查询失败' })
      wx.showToast({ title: '查询失败', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },

  // 保存到历史
  saveToHistory() {
    let history = wx.getStorageSync('sqlHistory') || []
    const newItem = {
      sql: this.data.sqlContent.trim(),
      school: this.data.selectedSchool.name,
      time: new Date().toLocaleString()
    }
    
    // 去重
    history = history.filter(h => h.sql !== newItem.sql)
    history.unshift(newItem)
    
    // 最多保存20条
    history = history.slice(0, 20)
    
    wx.setStorageSync('sqlHistory', history)
    this.setData({ history: history.slice(0, 10) })
  },

  // 使用历史SQL
  useHistory(e) {
    const sql = e.currentTarget.dataset.sql
    this.setData({ 
      sqlContent: sql,
      showHistory: false
    })
  },

  // 切换历史显示
  toggleHistory() {
    this.setData({ showHistory: !this.data.showHistory })
  },

  // 清空历史
  clearHistory() {
    wx.showModal({
      title: '确认清空',
      content: '确定要清空SQL历史吗？',
      success: (res) => {
        if (res.confirm) {
          wx.setStorageSync('sqlHistory', [])
          this.setData({ history: [], showHistory: false })
          wx.showToast({ title: '已清空', icon: 'success' })
        }
      }
    })
  },

  // 导出结果
  async exportResults() {
    if (!this.data.results || !this.data.results.rows.length) {
      wx.showToast({ title: '无数据可导出', icon: 'none' })
      return
    }
    
    this.setData({ loading: true })
    
    try {
      const res = await post('/user/export', {
        school_id: this.data.selectedSchool.id,
        sql: this.data.results.sql
      })
      
      if (res.code === 200) {
        wx.showModal({
          title: '导出成功',
          content: `已导出${res.data.count}条数据\n文件名：${res.data.filename}`,
          confirmText: '复制链接',
          success: (modalRes) => {
            if (modalRes.confirm) {
              wx.setClipboardData({
                data: res.data.url,
                success: () => {
                  wx.showToast({ title: '已复制', icon: 'success' })
                }
              })
            }
          }
        })
      } else {
        wx.showToast({ title: res.message || '导出失败', icon: 'none' })
      }
    } catch (error) {
      console.error('导出失败:', error)
      wx.showToast({ title: '导出失败', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },

  // 复制SQL
  copySql() {
    if (!this.data.results || !this.data.results.sql) return
    
    wx.setClipboardData({
      data: this.data.results.sql,
      success: () => {
        wx.showToast({ title: '已复制', icon: 'success' })
      }
    })
  },

  // 清空结果
  clearResults() {
    this.setData({ results: null, error: null })
  },

  // 格式化时间
  formatQueryTime(ms) {
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(2)}s`
  }
})

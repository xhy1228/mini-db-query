// pages/query/query.js
// 查询页面

const app = getApp()
const { get, post } = require('../../utils/request')

Page({
  data: {
    // 当前学校
    selectedSchool: null,
    
    // 业务大类
    categories: [],
    selectedCategory: null,
    
    // 查询模板
    templates: [],
    selectedTemplate: null,
    
    // 查询条件
    conditions: [],
    startTime: '',
    endTime: '',
    
    // 快捷时间
    quickTimeOptions: ['今天', '近7天', '近30天', '本月'],
    selectedQuickTime: '',
    
    // 查询结果
    loading: false,
    result: [],
    resultColumns: [],
    queried: false,
    
    // 导出中
    exporting: false
  },

  onLoad(options) {
    // 检查登录
    if (!app.isLoggedIn()) {
      wx.redirectTo({ url: '/pages/login/login' })
      return
    }
    
    // 获取参数
    if (options.school_id) {
      this.setData({
        selectedSchool: { id: options.school_id, name: decodeURIComponent(options.school_name || '') }
      })
    }
    
    // 如果没有学校，从全局获取
    if (!this.data.selectedSchool && app.globalData.selectedSchool) {
      this.setData({ selectedSchool: app.globalData.selectedSchool })
    }
    
    // 加载业务大类
    this.loadCategories()
  },

  onShow() {
    // 从全局获取选中的学校
    if (app.globalData.selectedSchool && !this.data.selectedSchool) {
      this.setData({ selectedSchool: app.globalData.selectedSchool })
      this.loadCategories()
    }
  },

  // 加载业务大类
  async loadCategories() {
    const school = this.data.selectedSchool
    if (!school) {
      // 跳转到首页选择学校
      wx.switchTab({ url: '/pages/index/index' })
      return
    }
    
    try {
      const res = await get('/user/categories', { school_id: school.id })
      
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

  // 选择业务大类
  async onCategoryTap(e) {
    const category = e.currentTarget.dataset.category
    this.setData({ 
      selectedCategory: category,
      templates: [],
      selectedTemplate: null
    })
    
    // 加载查询模板
    await this.loadTemplates(category.id)
  },

  // 加载查询模板
  async loadTemplates(category) {
    const school = this.data.selectedSchool
    if (!school) return
    
    try {
      const res = await get('/user/templates', { 
        school_id: school.id,
        category: category
      })
      
      if (res.code === 200) {
        this.setData({ templates: res.data || [] })
      }
    } catch (error) {
      console.error('加载查询模板失败:', error)
      // 使用模拟数据
      this.setData({
        templates: this.getMockTemplates()
      })
    }
  },

  // 获取模拟模板
  getMockTemplates() {
    return [
      {
        id: 1,
        name: '学生信息查询',
        description: '根据姓名或学号查询学生基本信息',
        fields: [
          { id: 'name', label: '姓名', column: 'CUSTNAME', type: 'text', operator: 'LIKE' },
          { id: 'student_id', label: '学号', column: 'STUDENTID', type: 'text', operator: '=' }
        ],
        time_field: null
      },
      {
        id: 2,
        name: '消费明细查询',
        description: '查询消费流水明细记录',
        fields: [
          { id: 'card_id', label: '卡号', column: 'CARDID', type: 'text', operator: '=' }
        ],
        time_field: 'TRATIME'
      }
    ]
  },

  // 选择查询模板
  onTemplateTap(e) {
    const template = e.currentTarget.dataset.template
    
    // 初始化查询条件
    const conditions = template.fields.map(field => ({
      field: field.column,
      operator: field.operator || '=',
      value: ''
    }))
    
    this.setData({
      selectedTemplate: template,
      conditions: conditions,
      startTime: '',
      endTime: ''
    })
  },

  // 输入查询条件
  onConditionInput(e) {
    const index = e.currentTarget.dataset.index
    const value = e.detail.value
    
    const conditions = this.data.conditions
    conditions[index].value = value
    
    this.setData({ conditions })
  },

  // 选择时间
  onStartTimeChange(e) {
    this.setData({ startTime: e.detail.value, selectedQuickTime: '' })
  },

  onEndTimeChange(e) {
    this.setData({ endTime: e.detail.value, selectedQuickTime: '' })
  },

  // 选择快捷时间
  selectQuickTime(e) {
    const index = e.currentTarget.dataset.index
    const option = this.data.quickTimeOptions[index]
    const now = new Date()
    let startTime = ''
    let endTime = now.toISOString().split('T')[0]
    
    switch(option) {
      case '今天':
        startTime = endTime
        break
      case '近7天':
        const d7 = new Date(now - 7 * 24 * 60 * 60 * 1000)
        startTime = d7.toISOString().split('T')[0]
        break
      case '近30天':
        const d30 = new Date(now - 30 * 24 * 60 * 60 * 1000)
        startTime = d30.toISOString().split('T')[0]
        break
      case '本月':
        const firstDay = new Date(now.getFullYear(), now.getMonth(), 1)
        startTime = firstDay.toISOString().split('T')[0]
        break
    }
    
    this.setData({
      selectedQuickTime: option,
      startTime: startTime,
      endTime: endTime
    })
  },

  // 导出结果
  async exportResult() {
    if (!this.data.result || this.data.result.length === 0) {
      wx.showToast({ title: '无数据可导出', icon: 'none' })
      return
    }
    
    this.setData({ exporting: true })
    
    try {
      const res = await post('/user/export', {
        school_id: this.data.selectedSchool.id,
        template_id: this.data.selectedTemplate.id,
        conditions: this.data.conditions.filter(c => c.value.trim()),
        start_time: this.data.startTime ? `${this.data.startTime} 00:00:00` : null,
        end_time: this.data.endTime ? `${this.data.endTime} 23:59:59` : null
      })
      
      if (res.code === 200) {
        wx.showModal({
          title: '导出成功',
          content: `已导出${res.data.count}条数据\n下载链接已复制到剪贴板`,
          showCancel: false,
          success: () => {
            wx.setClipboardData({
              data: res.data.url
            })
          }
        })
      } else {
        wx.showToast({ title: res.message || '导出失败', icon: 'none' })
      }
    } catch (error) {
      console.error('导出失败:', error)
      wx.showToast({ title: '导出失败', icon: 'none' })
    } finally {
      this.setData({ exporting: false })
    }
  },

  // 执行查询
  async doQuery() {
    const { selectedSchool, selectedTemplate, conditions, startTime, endTime } = this.data
    
    if (!selectedSchool) {
      wx.showToast({ title: '请先选择学校', icon: 'none' })
      return
    }
    
    if (!selectedTemplate) {
      wx.showToast({ title: '请先选择查询模板', icon: 'none' })
      return
    }
    
    // 验证查询条件
    const hasCondition = conditions.some(c => c.value.trim())
    if (!hasCondition) {
      wx.showToast({ title: '请至少输入一个查询条件', icon: 'none' })
      return
    }
    
    this.setData({ loading: true, queried: false })
    
    try {
      const res = await post('/user/query', {
        school_id: selectedSchool.id,
        template_id: selectedTemplate.id,
        conditions: conditions.filter(c => c.value.trim()),
        start_time: startTime ? `${startTime} 00:00:00` : null,
        end_time: endTime ? `${endTime} 23:59:59` : null,
        limit: 500
      })
      
      if (res.code === 200) {
        const result = res.data.rows || []
        const columns = result.length > 0 ? Object.keys(result[0]) : []
        
        this.setData({
          result: result,
          resultColumns: columns,
          queried: true
        })
        
        wx.showToast({
          title: `查询成功，共${result.length}条`,
          icon: 'success'
        })
      } else {
        wx.showToast({
          title: res.message || '查询失败',
          icon: 'none'
        })
      }
    } catch (error) {
      console.error('查询失败:', error)
      wx.showToast({
        title: '查询失败，请重试',
        icon: 'none'
      })
    } finally {
      this.setData({ loading: false })
    }
  },

  // 返回重新选择
  goBack() {
    this.setData({
      selectedTemplate: null,
      selectedCategory: null,
      result: [],
      queried: false
    })
  }
})

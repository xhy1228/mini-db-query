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
    queryTime: 0,
    errorInfo: null,
    
    // 导出相关
    exporting: false,
    showExportModal: false,
    
    // 详情弹窗
    showDetailModal: false,
    detailData: [],
    
    // 排序功能
    sortColumn: '',
    sortOrder: '', // 'asc' or 'desc'
    
    // 表格显示优化
    columnWidths: {}
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

  // 显示导出选项
  showExportOptions() {
    this.setData({ showExportModal: true })
  },

  // 隐藏导出选项
  hideExportModal() {
    this.setData({ showExportModal: false })
  },

  // 阻止事件冒泡
  stopPropagation() {},

  // 导出为Excel
  async exportToExcel() {
    this.hideExportModal()
    
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
        // 获取完整URL
        const baseUrl = app.globalData.apiBase || ''
        const downloadUrl = baseUrl + res.data.url
        
        wx.showModal({
          title: '导出成功',
          content: `已导出 ${res.data.count} 条数据\n点击"确定"下载文件`,
          confirmText: '确定',
          success: (confirmRes) => {
            if (confirmRes.confirm) {
              // 下载文件
              wx.downloadFile({
                url: downloadUrl,
                success: (downloadRes) => {
                  if (downloadRes.statusCode === 200) {
                    // 保存到本地
                    wx.saveFile({
                      tempFilePath: downloadRes.tempFilePath,
                      success: (saveRes) => {
                        wx.showToast({ title: '已保存到文件', icon: 'success' })
                      },
                      fail: (err) => {
                        console.error('保存文件失败:', err)
                        wx.showToast({ title: '保存失败', icon: 'none' })
                      }
                    })
                  }
                },
                fail: (err) => {
                  console.error('下载失败:', err)
                  // 尝试打开链接
                  wx.setClipboardData({
                    data: downloadUrl,
                    success: () => {
                      wx.showToast({ title: '链接已复制', icon: 'success' })
                    }
                  })
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
      this.setData({ exporting: false })
    }
  },

  // 复制到剪贴板
  copyToClipboard() {
    this.hideExportModal()
    
    if (!this.data.result || this.data.result.length === 0) {
      wx.showToast({ title: '无数据可复制', icon: 'none' })
      return
    }
    
    try {
      const columns = this.data.resultColumns
      const rows = this.data.result
      
      // 生成Tab分隔的文本
      let text = columns.join('\t') + '\n'
      rows.forEach(row => {
        const values = columns.map(col => {
          const val = row[col]
          return val !== null && val !== undefined ? String(val) : '-'
        })
        text += values.join('\t') + '\n'
      })
      
      wx.setClipboardData({
        data: text,
        success: () => {
          wx.showToast({ title: '已复制到剪贴板', icon: 'success' })
        }
      })
    } catch (error) {
      console.error('复制失败:', error)
      wx.showToast({ title: '复制失败', icon: 'none' })
    }
  },

  // 显示行详情
  showRowDetail(e) {
    const row = e.currentTarget.dataset.row
    if (!row) return
    
    // 转换为详情格式
    const detailData = this.data.resultColumns.map(col => ({
      label: col,
      value: row[col]
    }))
    
    this.setData({
      showDetailModal: true,
      detailData: detailData
    })
  },

  // 隐藏详情弹窗
  hideDetailModal() {
    this.setData({ showDetailModal: false, detailData: [] })
  },
  
  // 复制详情整行
  copyDetailRow() {
    const { detailData } = this.data
    if (!detailData || detailData.length === 0) return
    
    const text = detailData.map(item => `${item.label}: ${item.value != null ? item.value : '-'}`).join('\n')
    
    wx.setClipboardData({
      data: text,
      success: () => {
        wx.showToast({ title: '已复制', icon: 'success' })
      }
    })
  },
  
  // 长按复制单个字段
  copyDetailItem(e) {
    const index = e.currentTarget.dataset.index
    const item = this.data.detailData[index]
    if (!item) return
    
    wx.setClipboardData({
      data: String(item.value != null ? item.value : '-'),
      success: () => {
        wx.showToast({ title: '已复制', icon: 'success', duration: 1000 })
      }
    })
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
    
    this.setData({ 
      loading: true, 
      queried: false,
      errorInfo: null 
    })
    
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
        
        // 计算每列的宽度，确保表头和内容对齐
        const columnWidths = this.calculateColumnWidths(columns, result)
        
        this.setData({
          result: result,
          resultColumns: columns,
          columnWidths: columnWidths,
          queried: true,
          queryTime: res.data.query_time || 0,
          errorInfo: null
        })
        
        wx.showToast({
          title: `查询成功，共${result.length}条`,
          icon: 'success'
        })
      } else {
        // 处理错误
        const errorInfo = res.data?.error || {
          error_message: res.message || '查询失败',
          suggestion: '请重试或联系管理员'
        }
        
        this.setData({
          result: [],
          resultColumns: [],
          queried: true,
          errorInfo: errorInfo
        })
        
        wx.showToast({
          title: res.message || '查询失败',
          icon: 'none'
        })
      }
    } catch (error) {
      console.error('查询失败:', error)
      
      const errorInfo = {
        error_message: error.message || '网络错误，请检查网络连接',
        suggestion: '请检查网络后重试'
      }
      
      this.setData({
        result: [],
        resultColumns: [],
        queried: true,
        errorInfo: errorInfo
      })
      
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
      resultColumns: [],
      queried: false,
      queryTime: 0,
      errorInfo: null,
      sortColumn: '',
      sortOrder: ''
    })
  },
  
  // ========== 新增优化功能 ==========
  
  // 点击表头排序
  onHeaderTap(e) {
    const column = e.currentTarget.dataset.column
    const { sortColumn, sortOrder, result } = this.data
    
    if (!result || result.length === 0) return
    
    let newOrder = 'asc'
    if (sortColumn === column) {
      newOrder = sortOrder === 'asc' ? 'desc' : ''
    }
    
    if (!newOrder) {
      // 取消排序，恢复原始顺序
      this.setData({ sortColumn: '', sortOrder: '' })
      return
    }
    
    // 排序数据
    const sortedResult = [...result].sort((a, b) => {
      let valA = a[column]
      let valB = b[column]
      
      // 处理null/undefined
      if (valA == null) valA = ''
      if (valB == null) valB = ''
      
      // 数字比较
      const numA = parseFloat(valA)
      const numB = parseFloat(valB)
      if (!isNaN(numA) && !isNaN(numB)) {
        return newOrder === 'asc' ? numA - numB : numB - numA
      }
      
      // 字符串比较
      const strA = String(valA).toLowerCase()
      const strB = String(valB).toLowerCase()
      if (newOrder === 'asc') {
        return strA.localeCompare(strB, 'zh-CN')
      } else {
        return strB.localeCompare(strA, 'zh-CN')
      }
    })
    
    this.setData({
      result: sortedResult,
      sortColumn: column,
      sortOrder: newOrder
    })
  },
  
  // 长按复制单元格
  onCellLongPress(e) {
    const value = e.currentTarget.dataset.value
    if (value == null) return
    
    wx.setClipboardData({
      data: String(value),
      success: () => {
        wx.showToast({ title: '已复制', icon: 'success', duration: 1000 })
      }
    })
  },
  
  // 复制整行数据
  copyRow(e) {
    const row = e.currentTarget.dataset.row
    if (!row) return
    
    const text = this.data.resultColumns.map(col => {
      const val = row[col]
      return `${col}: ${val != null ? val : '-'}`
    }).join('\n')
    
    wx.setClipboardData({
      data: text,
      success: () => {
        wx.showToast({ title: '已复制整行', icon: 'success' })
      }
    })
  },
  
  // 格式化显示值
  formatValue(value, column) {
    if (value == null) return '-'
    
    // 日期字段格式化
    if (column.toLowerCase().includes('time') || column.toLowerCase().includes('date')) {
      if (typeof value === 'string' && value.length >= 10) {
        // 截取日期部分
        return value.substring(0, 19).replace('T', ' ')
      }
    }
    
    // 金额字段格式化
    if (column.toLowerCase().includes('amount') || column.toLowerCase().includes('money') || column.toLowerCase().includes('fee')) {
      const num = parseFloat(value)
      if (!isNaN(num)) {
        return num.toFixed(2)
      }
    }
    
    return value
  },
  
  // 计算列统计信息
  getColumnStats(column) {
    const { result } = this.data
    if (!result || result.length === 0) return null
    
    const values = result.map(r => r[column]).filter(v => v != null)
    if (values.length === 0) return null
    
    const nums = values.map(v => parseFloat(v)).filter(n => !isNaN(n))
    
    if (nums.length > 0 && nums.length === values.length) {
      // 数值列，计算统计
      const sum = nums.reduce((a, b) => a + b, 0)
      const avg = sum / nums.length
      const max = Math.max(...nums)
      const min = Math.min(...nums)
      
      return {
        isNumeric: true,
        count: nums.length,
        sum: sum.toFixed(2),
        avg: avg.toFixed(2),
        max: max.toFixed(2),
        min: min.toFixed(2)
      }
    }
    
    return {
      isNumeric: false,
      count: values.length
    }
  },
  
  // 计算每列的宽度，确保表头和内容对齐
  calculateColumnWidths(columns, result) {
    const widths = {}
    const minWidth = 120  // 最小宽度 rpx
    const maxWidth = 300  // 最大宽度 rpx
    const charWidth = 30  // 每个字符的宽度 rpx
    
    columns.forEach(col => {
      // 考虑表头宽度
      let maxLen = String(col).length
      
      // 考虑每行数据的宽度
      result.slice(0, 100).forEach(row => {
        const val = row[col]
        if (val != null) {
          const len = String(val).length
          if (len > maxLen) maxLen = len
        }
      })
      
      // 计算需要的宽度
      let width = maxLen * charWidth
      if (width < minWidth) width = minWidth
      if (width > maxWidth) width = maxWidth
      
      widths[col] = width + 'rpx'
    })
    
    return widths
  }
})

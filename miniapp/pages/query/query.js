// pages/query/query.js
// 查询页面

const { get, post } = require('../../utils/request')

Page({
  data: {
    // 数据库配置
    configs: [],
    selectedConfig: '',
    
    // 查询模式
    queryMode: 'smart',
    
    // 智能查询
    categories: [],
    queries: [],
    fields: [],
    operators: ['=', 'LIKE', '>', '<', '>=', '<=', '!='],
    
    selectedCategoryId: '',
    selectedCategoryName: '',
    selectedQueryId: '',
    selectedQueryName: '',
    selectedField: '',
    selectedFieldLabel: '',
    selectedOperator: '=',
    queryValue: '',
    
    // 时间范围
    enableTimeRange: false,
    startTime: '',
    endTime: '',
    
    // SQL查询
    sqlText: '',
    
    // 结果
    loading: false,
    result: [],
    resultHeaders: [],
    queried: false
  },

  onLoad(options) {
    // 加载数据库配置
    this.loadConfigs()
    // 加载业务大类
    this.loadCategories()
    
    // 从首页跳转时可能带有参数
    if (options.configName) {
      this.setData({ selectedConfig: options.configName })
    }
    if (options.categoryId) {
      this.setData({ selectedCategoryId: options.categoryId })
      this.loadQueries(options.categoryId)
    }
  },

  // 加载数据库配置
  async loadConfigs() {
    try {
      const res = await get('/query/configs')
      if (res.code === 200) {
        this.setData({ configs: res.data || [] })
      }
    } catch (error) {
      console.error('加载配置失败:', error)
    }
  },

  // 加载业务大类
  async loadCategories() {
    try {
      const res = await get('/query/categories')
      if (res.code === 200) {
        this.setData({ categories: res.data || [] })
      }
    } catch (error) {
      console.error('加载业务大类失败:', error)
    }
  },

  // 切换查询模式
  switchMode(e) {
    const mode = e.currentTarget.dataset.mode
    this.setData({ queryMode: mode })
  },

  // 选择数据库
  onConfigChange(e) {
    const index = e.detail.value
    const config = this.data.configs[index]
    this.setData({ 
      selectedConfig: config.name 
    })
  },

  // 选择业务大类
  onCategoryChange(e) {
    const index = e.detail.value
    const category = this.data.categories[index]
    this.setData({ 
      selectedCategoryId: category.id,
      selectedCategoryName: category.name 
    })
    this.loadQueries(category.id)
  },

  // 加载查询列表
  async loadQueries(categoryId) {
    try {
      const res = await get(`/query/queries/${categoryId}`)
      if (res.code === 200) {
        this.setData({ queries: res.data || [] })
      }
    } catch (error) {
      console.error('加载查询列表失败:', error)
    }
  },

  // 选择查询类型
  onQueryChange(e) {
    const index = e.detail.value
    const query = this.data.queries[index]
    this.setData({ 
      selectedQueryId: query.id,
      selectedQueryName: query.name,
      fields: query.fields || []
    })
  },

  // 选择字段
  onFieldChange(e) {
    const index = e.detail.value
    const field = this.data.fields[index]
    this.setData({ 
      selectedField: field.id,
      selectedFieldLabel: field.label
    })
  },

  // 选择操作符
  onOperatorChange(e) {
    const index = e.detail.value
    this.setData({ 
      selectedOperator: this.data.operators[index]
    })
  },

  // 输入查询值
  onValueInput(e) {
    this.setData({ queryValue: e.detail.value })
  },

  // 切换时间范围
  toggleTimeRange() {
    this.setData({ enableTimeRange: !this.data.enableTimeRange })
  },

  // 选择开始时间
  onStartTimeChange(e) {
    this.setData({ startTime: e.detail.value })
  },

  // 选择结束时间
  onEndTimeChange(e) {
    this.setData({ endTime: e.detail.value })
  },

  // 输入SQL
  onSqlInput(e) {
    this.setData({ sqlText: e.detail.value })
  },

  // 执行查询
  async executeQuery() {
    if (!this.data.selectedConfig) {
      wx.showToast({ title: '请选择数据库', icon: 'none' })
      return
    }

    this.setData({ loading: true })

    try {
      let result
      
      if (this.data.queryMode === 'smart') {
        // 智能查询
        result = await post('/query/smart', {
          config_name: this.data.selectedConfig,
          category: this.data.selectedCategoryId,
          query_id: this.data.selectedQueryId,
          conditions: [{
            field: this.data.selectedField,
            operator: this.data.selectedOperator,
            value: this.data.queryValue
          }],
          start_time: this.data.startTime ? `${this.data.startTime} 00:00:00` : null,
          end_time: this.data.endTime ? `${this.data.endTime} 23:59:59` : null
        })
      } else {
        // SQL查询
        if (!this.data.sqlText.trim()) {
          wx.showToast({ title: '请输入SQL语句', icon: 'none' })
          this.setData({ loading: false })
          return
        }
        result = await post('/query/execute', {
          config_name: this.data.selectedConfig,
          sql: this.data.sqlText
        })
      }

      if (result.code === 200) {
        const rows = result.data.rows || []
        const headers = rows.length > 0 ? Object.keys(rows[0]) : []
        
        this.setData({
          result: rows,
          resultHeaders: headers,
          queried: true
        })

        if (rows.length === 0) {
          wx.showToast({ title: '查询结果为空', icon: 'none' })
        }
      } else {
        wx.showToast({ title: result.message || '查询失败', icon: 'none' })
      }
    } catch (error) {
      wx.showToast({ title: '查询失败', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },

  // 导出结果
  async exportResult() {
    try {
      wx.showLoading({ title: '导出中...' })
      
      const result = await post('/query/export', {
        config_name: this.data.selectedConfig,
        sql: this.data.queryMode === 'sql' ? this.data.sqlText : ''
      })

      wx.hideLoading()

      if (result.code === 200) {
        wx.showModal({
          title: '导出成功',
          content: `共${result.data.rows}条数据\n点击确定下载`,
          success: (res) => {
            if (res.confirm) {
              // 下载文件
              wx.downloadFile({
                url: result.data.url,
                success: (res) => {
                  wx.openDocument({
                    filePath: res.tempFilePath,
                    fileType: 'xlsx'
                  })
                }
              })
            }
          }
        })
      }
    } catch (error) {
      wx.hideLoading()
      wx.showToast({ title: '导出失败', icon: 'none' })
    }
  }
})

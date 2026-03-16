// utils/request.js
// 网络请求封装

const app = getApp()

/**
 * 发起请求
 * @param {Object} options 请求配置
 * @returns {Promise}
 */
function request(options) {
  return new Promise((resolve, reject) => {
    const token = app.globalData.token
    
    wx.request({
      url: `${app.globalData.baseUrl}${options.url}`,
      method: options.method || 'GET',
      data: options.data || {},
      header: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
        ...options.header
      },
      success(res) {
        if (res.data.code === 200) {
          resolve(res.data)
        } else if (res.data.code === 401) {
          // 未授权，跳转登录
          app.login()
          reject(new Error('请先登录'))
        } else {
          reject(new Error(res.data.message || '请求失败'))
        }
      },
      fail(err) {
        reject(new Error('网络请求失败'))
      }
    })
  })
}

// GET请求
function get(url, data = {}) {
  return request({ url, method: 'GET', data })
}

// POST请求
function post(url, data = {}) {
  return request({ url, method: 'POST', data })
}

module.exports = {
  request,
  get,
  post
}

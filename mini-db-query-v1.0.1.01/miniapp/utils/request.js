// utils/request.js
// 网络请求封装

// 开发环境（本地测试）
// const BASE_URL = 'http://localhost:26316/api'

// 生产环境（云服务器）
const BASE_URL = 'https://miniapp.xzhykt.cn/api'

/**
 * 获取请求头
 */
function getHeaders() {
  const token = wx.getStorageSync('token')
  const headers = {
    'Content-Type': 'application/json'
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  return headers
}

/**
 * 处理响应
 */
function handleResponse(res) {
  // 检查HTTP状态码
  if (res.statusCode === 401) {
    // 未授权，跳转登录
    wx.removeStorageSync('token')
    wx.removeStorageSync('userInfo')
    wx.reLaunch({ url: '/pages/login/login' })
    return Promise.reject(new Error('未授权，请重新登录'))
  }

  if (res.statusCode >= 400) {
    return Promise.reject(new Error(res.data?.message || '请求失败'))
  }

  return res.data
}

/**
 * GET请求
 */
function get(url, data = {}) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: BASE_URL + url,
      method: 'GET',
      data: data,
      header: getHeaders(),
      success: (res) => {
        handleResponse(res).then(resolve).catch(reject)
      },
      fail: (err) => {
        reject(new Error('网络错误，请检查网络连接'))
      }
    })
  })
}

/**
 * POST请求
 */
function post(url, data = {}) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: BASE_URL + url,
      method: 'POST',
      data: data,
      header: getHeaders(),
      success: (res) => {
        handleResponse(res).then(resolve).catch(reject)
      },
      fail: (err) => {
        reject(new Error('网络错误，请检查网络连接'))
      }
    })
  })
}

/**
 * PUT请求
 */
function put(url, data = {}) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: BASE_URL + url,
      method: 'PUT',
      data: data,
      header: getHeaders(),
      success: (res) => {
        handleResponse(res).then(resolve).catch(reject)
      },
      fail: (err) => {
        reject(new Error('网络错误，请检查网络连接'))
      }
    })
  })
}

/**
 * DELETE请求
 */
function del(url, data = {}) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: BASE_URL + url,
      method: 'DELETE',
      data: data,
      header: getHeaders(),
      success: (res) => {
        handleResponse(res).then(resolve).catch(reject)
      },
      fail: (err) => {
        reject(new Error('网络错误，请检查网络连接'))
      }
    })
  })
}

/**
 * 设置Token
 */
function setToken(token) {
  wx.setStorageSync('token', token)
}

/**
 * 获取Token
 */
function getToken() {
  return wx.getStorageSync('token')
}

/**
 * 清除Token
 */
function clearToken() {
  wx.removeStorageSync('token')
}

module.exports = {
  get,
  post,
  put,
  del,
  setToken,
  getToken,
  clearToken,
  BASE_URL
}

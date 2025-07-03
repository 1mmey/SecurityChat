// ==================== 认证API配置 ====================

// API 基础配置 - 直接连接远程服务器
const API_BASE_URL = 'http://127.0.0.1:8080'

// 获取完整的API URL
const getApiUrl = (path) => {
  return `${API_BASE_URL}${path}`
}

// 获取认证头
const getAuthHeaders = () => {
  const token = localStorage.getItem('access_token')
  const tokenType = localStorage.getItem('token_type') || 'Bearer'
  
  if (token) {
    return {
      'Authorization': `${tokenType} ${token}`
    }
  }
  return {}
}

// 统一的API请求处理（仅用于认证相关）
const authApiRequest = async (url, options = {}) => {
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
      ...options.headers
    },
    ...options
  }
  
  try {
    const response = await fetch(getApiUrl(url), config)
    
    // 处理401错误（token过期或无效）
    if (response.status === 401) {
      removeToken()
      throw new Error('认证失败，请重新登录')
    }
    
    return response
  } catch (error) {
    console.error('认证API请求错误:', error)
    if (error.message.includes('认证失败')) {
      throw error
    }
    throw new Error('网络错误，请检查网络连接')
  }
}

// ==================== 认证相关API ====================

/**
 * 用户登录API
 * @param {string} username - 用户名
 * @param {string} password - 密码
 * @returns {Promise<Object>} 登录结果
 */
export const loginApi = async (username, password) => {
  try {
    // 后端使用 OAuth2PasswordRequestForm，需要 form-data 格式
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)
    
    console.log('发送登录请求到:', getApiUrl('/token'))
    
    const response = await fetch(getApiUrl('/token'), {
      method: 'POST',
      body: formData
      // 不设置 Content-Type，让浏览器自动设置为 multipart/form-data
    })
    
    console.log('登录响应状态:', response.status)
    
    if (!response.ok) {
      const responseText = await response.text()
      console.error('登录失败响应:', responseText)
      
      let errorData
      try {
        errorData = JSON.parse(responseText)
      } catch (e) {
        throw new Error(`登录失败 (${response.status})`)
      }
      
      throw new Error(errorData.detail || '登录失败')
    }
    
    const tokenData = await response.json()
    console.log('登录成功')
    
    // 保存token
    saveToken(tokenData)
    
    return {
      success: true,
      data: tokenData,
      message: '登录成功'
    }
  } catch (error) {
    console.error('登录API错误:', error)
    
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      return {
        success: false,
        message: '无法连接到服务器'
      }
    }
    
    return {
      success: false,
      message: error.message || '登录失败'
    }
  }
}

/**
 * 用户注册API
 * @param {Object} userData - 用户注册数据
 * @param {string} userData.username - 用户名
 * @param {string} userData.email - 邮箱
 * @param {string} userData.password - 密码
 * @returns {Promise<Object>} 注册结果
 */
export const registerApi = async (userData) => {
  try {
    console.log('发送注册请求到:', getApiUrl('/users/'))
    
    const response = await authApiRequest('/users/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData)
    })
    
    console.log('注册响应状态:', response.status)
    
    if (!response.ok) {
      const responseText = await response.text()
      console.error('注册失败响应:', responseText)
      
      let errorData
      try {
        errorData = JSON.parse(responseText)
      } catch (e) {
        throw new Error(`注册失败 (${response.status})`)
      }
      
      throw new Error(errorData.detail || '注册失败')
    }
    
    const result = await response.json()
    console.log('注册成功')
    
    return {
      success: true,
      data: result,
      message: '注册成功'
    }
  } catch (error) {
    console.error('注册API错误:', error)
    return {
      success: false,
      message: error.message || '注册失败'
    }
  }
}

/**
 * 用户登出API
 * @returns {Promise<Object>} 登出结果
 */
export const logoutApi = async () => {
  try {
    // 如果有token，尝试调用服务器登出接口
    if (isAuthenticated()) {
      const response = await authApiRequest('/logout', {
        method: 'POST'
      })
      
      if (!response.ok) {
        console.warn('服务器登出失败，但会清除本地token')
      }
    }
    
    // 无论服务器响应如何，都清除本地token
    removeToken()
    clearUserData()
    
    return {
      success: true,
      message: '登出成功'
    }
  } catch (error) {
    // 即使出错也要清除本地数据
    removeToken()
    clearUserData()
    
    return {
      success: false,
      message: '登出时发生错误，但已清除本地数据'
    }
  }
}

/**
 * 验证token有效性
 * @returns {Promise<Object>} 验证结果
 */
export const validateTokenApi = async () => {
  try {
    if (!isAuthenticated()) {
      return {
        success: false,
        message: '未找到token'
      }
    }
    
    // 通过调用需要认证的接口来验证token
    const response = await authApiRequest('/me/connection-info', {
      method: 'PUT',
      body: JSON.stringify({ port: 0 }) // 临时端口，仅用于验证
    })
    
    if (response.ok) {
      return {
        success: true,
        message: 'Token有效'
      }
    } else {
      removeToken()
      return {
        success: false,
        message: 'Token无效'
      }
    }
  } catch (error) {
    removeToken()
    return {
      success: false,
      message: 'Token验证失败'
    }
  }
}

// ==================== Token 管理 ====================

/**
 * 保存认证token
 * @param {Object} tokenData - token数据
 * @param {string} tokenData.access_token - 访问token
 * @param {string} tokenData.token_type - token类型
 */
export const saveToken = (tokenData) => {
  localStorage.setItem('access_token', tokenData.access_token)
  localStorage.setItem('token_type', tokenData.token_type || 'Bearer')
  
  // 保存token获取时间，用于过期检查
  localStorage.setItem('token_timestamp', Date.now().toString())
}

/**
 * 移除认证token
 */
export const removeToken = () => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('token_type')
  localStorage.removeItem('token_timestamp')
}

/**
 * 获取当前token
 * @returns {string|null} 当前token
 */
export const getToken = () => {
  return localStorage.getItem('access_token')
}

/**
 * 获取token类型
 * @returns {string} token类型
 */
export const getTokenType = () => {
  return localStorage.getItem('token_type') || 'Bearer'
}

/**
 * 检查用户是否已认证
 * @returns {boolean} 是否已认证
 */
export const isAuthenticated = () => {
  const token = getToken()
  const timestamp = localStorage.getItem('token_timestamp')
  
  if (!token || !timestamp) {
    return false
  }
  
  // 检查token是否过期（假设token有效期为24小时）
  const tokenAge = Date.now() - parseInt(timestamp)
  const maxAge = 24 * 60 * 60 * 1000 // 24小时
  
  if (tokenAge > maxAge) {
    removeToken()
    return false
  }
  
  return true
}

// ==================== 用户数据管理 ====================

/**
 * 保存用户信息
 * @param {Object} userInfo - 用户信息
 */
export const saveUserInfo = (userInfo) => {
  localStorage.setItem('user_info', JSON.stringify(userInfo))
}

/**
 * 获取用户信息
 * @returns {Object|null} 用户信息
 */
export const getUserInfo = () => {
  const userInfo = localStorage.getItem('user_info')
  return userInfo ? JSON.parse(userInfo) : null
}

/**
 * 清除用户数据
 */
export const clearUserData = () => {
  localStorage.removeItem('user_info')
  // 清除其他用户相关的本地数据
  localStorage.removeItem('chat_settings')
  localStorage.removeItem('friend_list')
}

// ==================== 认证状态监听 ====================

/**
 * 认证状态监听器列表
 */
const authStateListeners = new Set()

/**
 * 添加认证状态监听器
 * @param {Function} callback - 回调函数
 */
export const addAuthStateListener = (callback) => {
  authStateListeners.add(callback)
}

/**
 * 移除认证状态监听器
 * @param {Function} callback - 回调函数
 */
export const removeAuthStateListener = (callback) => {
  authStateListeners.delete(callback)
}

/**
 * 通知认证状态变化
 * @param {boolean} isAuth - 是否已认证
 */
const notifyAuthStateChange = (isAuth) => {
  authStateListeners.forEach(callback => {
    try {
      callback(isAuth)
    } catch (error) {
      console.error('认证状态监听器错误:', error)
    }
  })
}

// 重写saveToken和removeToken以触发状态变化通知
const originalSaveToken = saveToken
const originalRemoveToken = removeToken

export const saveTokenWithNotify = (tokenData) => {
  originalSaveToken(tokenData)
  notifyAuthStateChange(true)
}

export const removeTokenWithNotify = () => {
  originalRemoveToken()
  clearUserData()
  notifyAuthStateChange(false)
}

// ==================== 工具函数 ====================

/**
 * 获取认证头（供其他模块使用）
 * @returns {Object} 认证头对象
 */
export const getAuthHeadersForExport = () => {
  return getAuthHeaders()
}

/**
 * 获取API基础URL（供其他模块使用）
 * @returns {string} API基础URL
 */
export const getApiBaseUrl = () => {
  return API_BASE_URL
}

/**
 * 获取完整API URL（供其他模块使用）
 * @param {string} path - API路径
 * @returns {string} 完整URL
 */
export const getFullApiUrl = (path) => {
  return getApiUrl(path)
}

/**
 * 处理认证错误的通用方法
 * @param {Error} error - 错误对象
 * @returns {string} 格式化的错误消息
 */
export const handleAuthError = (error) => {
  if (error.message.includes('认证失败')) {
    removeTokenWithNotify()
    return '登录已过期，请重新登录'
  } else if (error.message.includes('网络错误')) {
    return '网络连接失败，请检查网络设置'
  } else {
    return error.message || '操作失败'
  }
}

// ==================== 自动认证检查 ====================

/**
 * 定期检查token有效性
 */
let tokenCheckInterval = null

/**
 * 启动token有效性检查
 * @param {number} interval - 检查间隔（毫秒），默认5分钟
 */
export const startTokenValidityCheck = (interval = 5 * 60 * 1000) => {
  if (tokenCheckInterval) {
    clearInterval(tokenCheckInterval)
  }
  
  tokenCheckInterval = setInterval(async () => {
    if (isAuthenticated()) {
      const result = await validateTokenApi()
      if (!result.success) {
        console.log('Token已失效，需要重新登录')
        notifyAuthStateChange(false)
      }
    }
  }, interval)
}

/**
 * 停止token有效性检查
 */
export const stopTokenValidityCheck = () => {
  if (tokenCheckInterval) {
    clearInterval(tokenCheckInterval)
    tokenCheckInterval = null
  }
}

// ==================== 默认导出 ====================

export default {
  // 认证API
  loginApi,
  registerApi,
  logoutApi,
  validateTokenApi,
  
  // Token管理
  saveToken: saveTokenWithNotify,
  removeToken: removeTokenWithNotify,
  getToken,
  getTokenType,
  isAuthenticated,
  
  // 用户数据管理
  saveUserInfo,
  getUserInfo,
  clearUserData,
  
  // 状态监听
  addAuthStateListener,
  removeAuthStateListener,
  
  // 工具函数
  getAuthHeaders: getAuthHeadersForExport,
  getApiBaseUrl,
  getFullApiUrl,
  handleAuthError,
  
  // 自动检查
  startTokenValidityCheck,
  stopTokenValidityCheck
}
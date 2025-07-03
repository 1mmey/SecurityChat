import { getFullApiUrl, getAuthHeadersForExport } from '@/api/auth.js'
import { getUserInfo } from '@/api/auth.js' 
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

const chatApiRequest = async (url, options = {}) => {
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeadersForExport(),  // 使用统一的认证头获取方法
      ...options.headers
    },
    ...options
  }
  
  try {
    const response = await fetch(getFullApiUrl(url), config)  // 使用统一的URL生成方法
    
    if (response.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('token_type')
      window.location.href = '/login'
      throw new Error('认证失败，请重新登录')
    }
    
    return response
  } catch (error) {
    console.error('聊天API请求错误:', error)
    if (error.message.includes('认证失败')) {
      throw error
    }
    throw new Error('网络错误，请检查网络连接')
  }
}

/**
 * 发送离线消息
 * @param {Object} messageData - 消息数据
 * @param {string} messageData.recipient_username - 接收者用户名
 * @param {string} messageData.encrypted_content - 加密内容
 * @returns {Promise<Object>} 发送结果
 */
const sendOfflineMessage = async (messageData) => {
  try {
    const response = await chatApiRequest('/messages/', {
      method: 'POST',
      body: JSON.stringify(messageData)
    })
    
    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`发送消息失败: ${errorText}`)
    }
    
    const data = await response.json()
    return {
      success: true,
      data: data,
      message: '消息发送成功'
    }
  } catch (error) {
    return {
      success: false,
      message: error.message || '发送消息失败'
    }
  }
}

/**
 * 获取离线消息
 * @returns {Promise<Object>} 离线消息列表
 */
const getOfflineMessages = async () => {
  try {
    const response = await chatApiRequest('/messages/')
    
    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`获取离线消息失败: ${errorText}`)
    }
    
    const data = await response.json()
    return {
      success: true,
      data: data.map(message => ({
        id: message.id,
        sender_id: message.sender_id,
        receiver_id: message.receiver_id,
        encrypted_content: message.encrypted_content,
        sent_at: message.sent_at,
        is_read: message.is_read,
        sender: message.sender ? {
          id: message.sender.id,
          username: message.sender.username
        } : null,
        receiver: message.receiver ? {
          id: message.receiver.id,
          username: message.receiver.username
        } : null
      }))
    }
  } catch (error) {
    return {
      success: false,
      message: error.message || '获取离线消息失败'
    }
  }
}

/**
 * 更新用户连接信息
 * @param {Object} connectionInfo - 连接信息
 * @param {number} connectionInfo.port - 端口号
 * @returns {Promise<Object>} 更新结果
 */
const updateConnectionInfo = async (connectionInfo) => {
  try {
    const response = await chatApiRequest('/me/connection-info', {
      method: 'PUT',
      body: JSON.stringify(connectionInfo)
    })
    
    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`更新连接信息失败: ${errorText}`)
    }
    
    const data = await response.json()
    return {
      success: true,
      data: data,
      message: '连接信息更新成功'
    }
  } catch (error) {
    return {
      success: false,
      message: error.message || '更新连接信息失败'
    }
  }
}

/**
 * 🆕 获取好友在线状态
 * @returns {Promise<Object>} 好友在线状态列表
 */
const getFriendsOnlineStatus = async () => {
  try {
    const response = await chatApiRequest('/me/contacts/online')
    
    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`获取好友在线状态失败: ${errorText}`)
    }
    
    const data = await response.json()
    return {
      success: true,
      data: data.map(friend => ({
        id: friend.id,
        username: friend.username,
        is_online: friend.is_online,
        ip_address: friend.ip_address,
        port: friend.port,
        public_key: friend.public_key,
        last_seen: friend.last_seen
      })),
      message: '获取好友在线状态成功'
    }
  } catch (error) {
    return {
      success: false,
      message: error.message || '获取好友在线状态失败'
    }
  }
}

/**
 * 🆕 获取用户连接信息（用于P2P连接）
 * @param {string} username - 用户名
 * @returns {Promise<Object>} 用户连接信息
 */
const getUserConnectionInfo = async (username) => {
  try {
    const response = await chatApiRequest(`/users/${username}/connection-info`)
    
    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`获取用户连接信息失败: ${errorText}`)
    }
    
    const data = await response.json()
    return {
      success: true,
      data: {
        id: data.id,
        username: data.username,
        is_online: data.is_online,
        ip_address: data.ip_address,
        port: data.port,
        public_key: data.public_key
      },
      message: '获取用户连接信息成功'
    }
  } catch (error) {
    return {
      success: false,
      message: error.message || '获取用户连接信息失败'
    }
  }
}

/**
 * 🆕 增强的WebSocket连接管理器 - 适配后端接口
 */
export class EnhancedWebSocketManager {
  constructor() {
    this.ws = null
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectInterval = 3000
    this.messageHandlers = new Set()
    this.connectionHandlers = new Set()
    this.statusChangeHandlers = new Set()
    this.offlineMessageHandlers = new Set()
    this.isManualClose = false
    this.heartbeatInterval = null
    this.heartbeatIntervalTime = 30000 // 30秒心跳
    this.usernameToIdMap = new Map()
    this.idToUsernameMap = new Map()
  }

  connect(token) {
    return new Promise((resolve, reject) => {
      try {
        const wsUrl = `ws://127.0.0.1:8080/ws?token=${token}`
        this.ws = new WebSocket(wsUrl)
        this.isManualClose = false

        this.ws.onopen = () => {
          console.log('✅ WebSocket连接已建立')
          this.reconnectAttempts = 0
          this.startHeartbeat()
          this.notifyConnectionHandlers('connected')
          resolve(true)
        }

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            this.handleIncomingMessage(data)
          } catch (error) {
            // 🆕 处理非JSON消息（如系统广播）
            console.log('收到文本消息:', event.data)
            this.notifyMessageHandlers({ 
              type: 'system_broadcast', 
              content: event.data,
              timestamp: Date.now()
            })
          }
        }

        this.ws.onclose = (event) => {
          console.log('WebSocket连接已关闭', event.code, event.reason)
          this.stopHeartbeat()
          this.notifyConnectionHandlers('disconnected', event)
          
          if (!this.isManualClose && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect(token)
          }
        }

        this.ws.onerror = (error) => {
          console.error('WebSocket连接错误:', error)
          this.notifyConnectionHandlers('error', error)
          reject(error)
        }

      } catch (error) {
        reject(error)
      }
    })
  }

  /**
   * 🆕 处理收到的消息，适配后端消息格式
   * @param {Object} data - 收到的数据
   */
  handleIncomingMessage(data) {
    console.log('📨 收到WebSocket消息:', data)
    
    switch (data.type) {
      case 'offline_message':
        // 🆕 处理离线消息推送
        this.handleOfflineMessage(data)
        break
      
      case 'p2p_message':
        // 🆕 处理实时P2P消息
        this.handleP2PMessage(data)
        break
      
      case 'system_broadcast':
        // 系统广播消息
        this.notifyMessageHandlers({
          type: 'system_broadcast',
          content: data.content || data,
          timestamp: Date.now()
        })
        break
      
      default:
        // 🆕 处理状态消息和错误消息
        if (data.status) {
          console.log('📋 收到状态消息:', data.status)
          this.notifyMessageHandlers({
            type: 'status',
            content: data.status,
            timestamp: Date.now()
          })
        } else if (data.error) {
          console.error('❌ 收到错误消息:', data.error)
          this.notifyMessageHandlers({
            type: 'error',
            content: data.error,
            timestamp: Date.now()
          })
        } else {
          // 其他未知类型消息
          this.notifyMessageHandlers(data)
        }
        break
    }
  }

  /**
   * 🆕 处理离线消息
   * @param {Object} data - 离线消息数据
   */
  handleOfflineMessage(data) {
    const message = {
      id: `offline_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type: 'text',
      content: data.content,
      timestamp: new Date(data.timestamp).getTime(),
      senderId: data.sender_username, // 使用用户名作为发送者标识
      senderName: data.sender_username,
      receiverId: 'current_user', // 当前用户
      isOfflineMessage: true,
      status: 'delivered'
    }
    
    console.log('📬 处理离线消息:', message)
    this.notifyOfflineMessageHandlers(message)
  }

  /**
   * 🆕 处理实时P2P消息
   * @param {Object} data - P2P消息数据
   */
  handleP2PMessage(data) {
    const message = {
      id: `p2p_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type: 'text',
      content: data.content,
      timestamp: new Date(data.timestamp).getTime(),
      senderId: data.sender_username, // 使用用户名作为发送者标识
      senderName: data.sender_username,
      receiverId: 'current_user', // 当前用户
      isRealTimeMessage: true,
      status: 'delivered'
    }
    
    console.log('⚡ 处理实时P2P消息:', message)
    this.notifyMessageHandlers(message)
  }

  /**
   * 🆕 发送消息到指定用户 - 适配后端格式
   * @param {string} recipientUsername - 接收者用户名
   * @param {string} content - 消息内容
   * @returns {boolean} 是否发送成功
   */
  sendMessageToUser(recipientUsername, content) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message = {
        recipient_username: recipientUsername,
        content: content
      }
      
      try {
        this.ws.send(JSON.stringify(message))
        console.log('📤 发送消息:', message)
        return true
      } catch (error) {
        console.error('发送消息失败:', error)
        return false
      }
    }
    
    console.warn('WebSocket未连接，无法发送消息')
    return false
  }

  /**
   * 🆕 发送给指定用户 - 保持兼容性
   * @param {string} userId - 用户ID（这里转换为用户名）
   * @param {Object} message - 消息内容
   * @returns {boolean} 是否发送成功
   */
  sendToUser(userId, message) {
    // 🆕 需要将用户ID转换为用户名
    // 这个方法需要配合好友列表来获取用户名
    console.warn('sendToUser需要用户名，请使用sendMessageToUser')
    return this.send(message)
  }

  /**
   * 🆕 开始心跳 - 暂时移除，后端会自动检测连接状态
   */
  startHeartbeat() {
    // 后端通过连接状态自动管理，前端暂不需要主动心跳
    console.log('WebSocket心跳由后端管理')
  }

  /**
   * 🆕 停止心跳
   */
  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }
  }

  scheduleReconnect(token) {
    this.reconnectAttempts++
    console.log(`准备第 ${this.reconnectAttempts} 次重连...`)
    
    setTimeout(() => {
      if (!this.isManualClose) {
        this.connect(token).catch(console.error)
      }
    }, this.reconnectInterval * this.reconnectAttempts)
  }

  send(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const messageStr = typeof message === 'string' ? message : JSON.stringify(message)
      this.ws.send(messageStr)
      return true
    }
    console.warn('WebSocket未连接，无法发送消息')
    return false
  }

  close() {
    this.isManualClose = true
    this.stopHeartbeat()
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  // 原有方法保持不变
  addMessageHandler(handler) {
    this.messageHandlers.add(handler)
  }

  removeMessageHandler(handler) {
    this.messageHandlers.delete(handler)
  }

  addConnectionHandler(handler) {
    this.connectionHandlers.add(handler)
  }

  removeConnectionHandler(handler) {
    this.connectionHandlers.delete(handler)
  }

  /**
   * 🆕 添加状态变化处理器
   * @param {Function} handler - 处理器函数
   */
  addStatusChangeHandler(handler) {
    this.statusChangeHandlers.add(handler)
  }

  removeStatusChangeHandler(handler) {
    this.statusChangeHandlers.delete(handler)
  }

  /**
   * 🆕 添加离线消息处理器
   * @param {Function} handler - 处理器函数
   */
  addOfflineMessageHandler(handler) {
    this.offlineMessageHandlers.add(handler)
  }

  removeOfflineMessageHandler(handler) {
    this.offlineMessageHandlers.delete(handler)
  }

  notifyMessageHandlers(message) {
    this.messageHandlers.forEach(handler => {
      try {
        handler(message)
      } catch (error) {
        console.error('消息处理器错误:', error)
      }
    })
  }

  notifyConnectionHandlers(status, event = null) {
    this.connectionHandlers.forEach(handler => {
      try {
        handler(status, event)
      } catch (error) {
        console.error('连接状态处理器错误:', error)
      }
    })
  }

  /**
   * 🆕 通知状态变化处理器
   * @param {Object} statusData - 状态变化数据
   */
  notifyStatusChangeHandlers(statusData) {
    this.statusChangeHandlers.forEach(handler => {
      try {
        handler(statusData)
      } catch (error) {
        console.error('状态变化处理器错误:', error)
      }
    })
  }

  /**
   * 🆕 通知离线消息处理器
   * @param {Object} messageData - 离线消息数据
   */
  notifyOfflineMessageHandlers(messageData) {
    this.offlineMessageHandlers.forEach(handler => {
      try {
        handler(messageData)
      } catch (error) {
        console.error('离线消息处理器错误:', error)
      }
    })
  }

  getConnectionStatus() {
    if (!this.ws) return 'disconnected'
    
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING:
        return 'connecting'
      case WebSocket.OPEN:
        return 'connected'
      case WebSocket.CLOSING:
        return 'disconnecting'
      case WebSocket.CLOSED:
        return 'disconnected'
      default:
        return 'unknown'
    }
  }

  /**
   * 设置好友映射表，用于用户名和ID的转换
   * @param {Array} friendsList - 好友列表
   */
  setFriendsMap(friendsList) {
    console.log('📋 更新WebSocket好友映射表:', friendsList.length, '个好友')
    
    // 创建用户名到ID的映射
    this.usernameToIdMap = new Map()
    this.idToUsernameMap = new Map()
    
    friendsList.forEach(friend => {
      if (friend.username && friend.id) {
        this.usernameToIdMap.set(friend.username, friend.id)
        this.idToUsernameMap.set(friend.id, friend.username)
      }
    })
    
    console.log('📋 好友映射更新完成')
  }

  /**
   * 根据用户名获取用户ID
   * @param {string} username - 用户名
   * @returns {number|null} 用户ID
   */
  getUserIdByUsername(username) {
    return this.usernameToIdMap ? this.usernameToIdMap.get(username) : null
  }

  /**
   * 根据用户ID获取用户名
   * @param {number} userId - 用户ID
   * @returns {string|null} 用户名
   */
  getUsernameById(userId) {
    return this.idToUsernameMap ? this.idToUsernameMap.get(userId) : null
  }
}


class WebSocketManager {
  constructor() {
    this.socket = null
    this.isConnected = false
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectInterval = 3000
    this.messageListeners = new Set()
    this.connectionListeners = new Set()
    this.chatMessages = new Map() // 存储聊天记录 username -> messages[]
    this.currentUser = null
    
    // 用户信息映射
    this.friendsMap = new Map() // username -> friend info
    this.userIdToUsernameMap = new Map() // userId -> username
    this.usernameToUserIdMap = new Map() // username -> userId
  }

  // 设置好友列表映射
  setFriendsMap(friendsList) {
    this.friendsMap.clear()
    this.userIdToUsernameMap.clear()
    this.usernameToUserIdMap.clear()
    
    friendsList.forEach(friend => {
      this.friendsMap.set(friend.username, friend)
      this.userIdToUsernameMap.set(friend.id, friend.username)
      this.usernameToUserIdMap.set(friend.username, friend.id)
    })
    
    console.log('🔧 设置好友映射:', {
      friends: this.friendsMap.size,
      userIds: this.userIdToUsernameMap.size
    })
  }

  // 通过用户名获取用户ID
  getUserIdByUsername(username) {
    return this.usernameToUserIdMap.get(username) || username
  }

  // 通过用户ID获取用户名
  getUsernameById(userId) {
    return this.userIdToUsernameMap.get(userId) || userId.toString()
  }

  connect() {
    const userInfo = getUserInfo()
    if (!userInfo) {
      console.error('❌ 无法连接WebSocket：未找到用户信息')
      return false
    }

    const token = userInfo.token || localStorage.getItem('access_token')
    if (!token) {
      console.error('❌ 无法连接WebSocket：未找到认证token')
      return false
    }

    this.currentUser = userInfo
    // 直接使用固定地址
    const wsUrl = `ws://127.0.0.1:8080/ws?token=${token}`
    
    try {
      this.socket = new WebSocket(wsUrl)
      this.setupEventListeners()
      return true
    } catch (error) {
      console.error('❌ WebSocket连接失败:', error)
      return false
    }
  }

  setupEventListeners() {
    if (!this.socket) return

    this.socket.onopen = () => {
      console.log('✅ WebSocket连接成功')
      this.isConnected = true
      this.reconnectAttempts = 0
      this.notifyConnectionListeners('connected')
    }

    this.socket.onclose = () => {
      console.log('❌ WebSocket连接关闭')
      this.isConnected = false
      this.notifyConnectionListeners('disconnected')
      this.attemptReconnect()
    }

    this.socket.onerror = (error) => {
      console.error('❌ WebSocket错误:', error)
      this.notifyConnectionListeners('error', error)
    }

    this.socket.onmessage = (event) => {
      this.handleMessage(event.data)
    }
  }

  handleMessage(data) {
    try {
      let message
      try {
        message = JSON.parse(data)
      } catch {
        console.log('📢 系统消息:', data)
        this.notifyListeners({ 
          type: 'system', 
          content: data, 
          timestamp: new Date().toISOString() 
        })
        return
      }
      
      console.log('📨 收到WebSocket消息:', message)
      
      switch (message.type) {
        case 'offline_message':
          this.handleOfflineMessage(message)
          break
        case 'p2p_message':
          this.handleP2PMessage(message)
          break
        default:
          if (message.status) {
            this.handleStatusMessage(message)
          } else if (message.error) {
            this.handleErrorMessage(message)
          }
      }
    } catch (error) {
      console.error('❌ 解析WebSocket消息失败:', error)
    }
  }

  handleOfflineMessage(message) {
    console.log('📬 离线消息:', message)
    const senderId = this.getUserIdByUsername(message.sender_username)
    const senderInfo = this.friendsMap.get(message.sender_username)
    
    const chatMessage = {
      id: `offline_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type: 'received',
      content: message.content,
      timestamp: message.timestamp,
      senderId: senderId,
      senderName: message.sender_username,
      senderUsername: message.sender_username,
      receiverId: this.currentUser?.id,
      receiverName: this.currentUser?.username,
      avatar: senderInfo?.avatar || '',
      isOffline: true,
      status: 'delivered'
    }
    
    this.addMessageToHistory(message.sender_username, chatMessage)
    this.notifyListeners({ 
      type: 'message', 
      message: chatMessage, 
      sender: message.sender_username 
    })
  }

  handleP2PMessage(message) {
    console.log('💬 实时消息:', message)
    const senderId = this.getUserIdByUsername(message.sender_username)
    const senderInfo = this.friendsMap.get(message.sender_username)
    
    const chatMessage = {
      id: `p2p_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type: 'received',
      content: message.content,
      timestamp: message.timestamp,
      senderId: senderId,
      senderName: message.sender_username,
      senderUsername: message.sender_username,
      receiverId: this.currentUser?.id,
      receiverName: this.currentUser?.username,
      avatar: senderInfo?.avatar || '',
      isOffline: false,
      status: 'delivered'
    }
    
    this.addMessageToHistory(message.sender_username, chatMessage)
    this.notifyListeners({ 
      type: 'message', 
      message: chatMessage, 
      sender: message.sender_username 
    })
  }

  handleStatusMessage(message) {
    console.log('ℹ️ 状态消息:', message.status)
    this.notifyListeners({ type: 'status', content: message.status })
  }

  handleErrorMessage(message) {
    console.error('❌ 服务器错误:', message.error)
    this.notifyListeners({ type: 'error', content: message.error })
  }

  // 发送消息 - 支持多种格式
  sendMessage(recipient, content) {
    if (!this.isConnected || !this.socket) {
      console.error('❌ WebSocket未连接，无法发送消息')
      return false
    }

    // 支持传入用户ID、用户名或用户对象
    let recipientUsername
    if (typeof recipient === 'string') {
      recipientUsername = recipient
    } else if (typeof recipient === 'object' && recipient.username) {
      recipientUsername = recipient.username
    } else if (typeof recipient === 'object' && recipient.id) {
      recipientUsername = this.getUsernameById(recipient.id)
    } else {
      recipientUsername = this.getUsernameById(recipient)
    }

    const message = {
      recipient_username: recipientUsername,
      content: content
    }

    try {
      this.socket.send(JSON.stringify(message))
      console.log('📤 发送消息:', message)
      
      // 创建本地消息记录
      const chatMessage = {
        id: `sent_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        type: 'sent',
        content: content,
        timestamp: new Date().toISOString(),
        senderId: this.currentUser?.id,
        senderName: this.currentUser?.username,
        senderUsername: this.currentUser?.username,
        receiverId: this.getUserIdByUsername(recipientUsername),
        receiverName: recipientUsername,
        receiverUsername: recipientUsername,
        avatar: '',
        isOffline: false,
        status: 'sending'
      }
      
      this.addMessageToHistory(recipientUsername, chatMessage)
      this.notifyListeners({ 
        type: 'message', 
        message: chatMessage, 
        sender: recipientUsername 
      })
      
      return true
    } catch (error) {
      console.error('❌ 发送消息失败:', error)
      return false
    }
  }

  addMessageToHistory(username, message) {
    if (!this.chatMessages.has(username)) {
      this.chatMessages.set(username, [])
    }
    
    const messages = this.chatMessages.get(username)
    messages.push(message)
  }

  getChatHistory(username) {
    if (!this.chatMessages.has(username)) {
      this.chatMessages.set(username, [])
    }
    return this.chatMessages.get(username) || []
  }

  // 检查是否为当前用户的消息
  isCurrentUserMessage(message) {
    return message.senderId === this.currentUser?.id || 
           message.senderUsername === this.currentUser?.username ||
           message.type === 'sent'
  }

  addMessageListener(listener) {
    this.messageListeners.add(listener)
  }

  removeMessageListener(listener) {
    this.messageListeners.delete(listener)
  }

  addConnectionListener(listener) {
    this.connectionListeners.add(listener)
  }

  removeConnectionListener(listener) {
    this.connectionListeners.delete(listener)
  }

  notifyListeners(data) {
    this.messageListeners.forEach(listener => {
      try {
        listener(data)
      } catch (error) {
        console.error('消息监听器错误:', error)
      }
    })
  }

  notifyConnectionListeners(status, data = null) {
    this.connectionListeners.forEach(listener => {
      try {
        listener(status, data)
      } catch (error) {
        console.error('连接监听器错误:', error)
      }
    })
  }

  attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('❌ WebSocket重连次数超限，停止重连')
      return
    }

    console.log(`🔄 WebSocket重连中... (${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`)
    this.reconnectAttempts++

    setTimeout(() => {
      this.connect()
    }, this.reconnectInterval)
  }

  disconnect() {
    if (this.socket) {
      this.socket.close()
      this.socket = null
    }
    this.isConnected = false
    this.currentUser = null
  }

  // 获取连接状态
  getConnectionStatus() {
    if (!this.socket) return 'disconnected'
    
    switch (this.socket.readyState) {
      case WebSocket.CONNECTING:
        return 'connecting'
      case WebSocket.OPEN:
        return 'connected'
      case WebSocket.CLOSING:
        return 'disconnecting'
      case WebSocket.CLOSED:
        return 'disconnected'
      default:
        return 'unknown'
    }
  }
}

// 🆕 创建WebSocket管理器实例
const wsManagerInstance = new WebSocketManager()

// 🆕 导入好友联系人API（如果需要的话）
export { getContacts, addContact, deleteContact } from '@/api/friend.js'

// 🆕 导出API函数（确保这些函数在文件前面已经定义）
export {
  sendOfflineMessage,
  getOfflineMessages,
  updateConnectionInfo,
  getFriendsOnlineStatus,
  getUserConnectionInfo,
}

// 🆕 命名导出WebSocket管理器
export const wsManager = wsManagerInstance

// 🆕 默认导出WebSocket管理器
export default wsManagerInstance
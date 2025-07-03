import { getUserInfo, getFullApiUrl } from '@/api/auth.js'

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
    
    // 🆕 用户信息映射
    this.friendsMap = new Map() // username -> friend info
    this.userIdToUsernameMap = new Map() // userId -> username
    this.usernameToUserIdMap = new Map() // username -> userId
  }

  // 🆕 设置好友列表映射
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

  // 🆕 通过用户名获取用户ID
  getUserIdByUsername(username) {
    return this.usernameToUserIdMap.get(username) || username
  }

  // 🆕 通过用户ID获取用户名
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
    // 🆕 使用动态API地址
    const apiBaseUrl = getFullApiUrl('').replace('http', 'ws')
    const wsUrl = `${apiBaseUrl}/ws?token=${token}`
    
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

  // 🆕 发送消息 - 支持多种格式
  sendMessage(recipient, content) {
    if (!this.isConnected || !this.socket) {
      console.error('❌ WebSocket未连接，无法发送消息')
      return false
    }

    // 🆕 支持传入用户ID、用户名或用户对象
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
      
      // 🆕 创建本地消息记录
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
    
    // 保存到本地存储 - 禁用localStorage存储
    // this.saveChatHistory(username, messages)
  }

  getChatHistory(username) {
    if (!this.chatMessages.has(username)) {
      // 从本地存储加载 - 禁用localStorage读取
      // const saved = this.loadChatHistory(username)
      // if (saved) {
      //   this.chatMessages.set(username, saved)
      // } else {
        this.chatMessages.set(username, [])
      // }
    }
    return this.chatMessages.get(username) || []
  }

  // 🆕 获取与特定用户的聊天记录
  getChatHistoryWithUser(userId) {
    const username = this.getUsernameById(userId)
    return this.getChatHistory(username)
  }

  // 禁用localStorage操作
  saveChatHistory(username, messages) {
    // localStorage在artifacts中不可用，改为内存存储
    console.log(`💾 聊天记录已保存到内存 (${username}): ${messages.length} 条消息`)
  }

  loadChatHistory(username) {
    // localStorage在artifacts中不可用
    return null
  }

  // 🆕 检查是否为当前用户的消息
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

  clearChatHistory(username) {
    this.chatMessages.delete(username)
    console.log(`🗑️ 已清除 ${username} 的聊天记录`)
  }

  // 🆕 清除与特定用户的聊天记录
  clearChatHistoryWithUser(userId) {
    const username = this.getUsernameById(userId)
    this.clearChatHistory(username)
  }

  getAllChatUsers() {
    return Array.from(this.chatMessages.keys())
  }

  // 🆕 获取连接状态
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

  // 🆕 获取统计信息
  getStats() {
    return {
      isConnected: this.isConnected,
      connectionStatus: this.getConnectionStatus(),
      totalChatUsers: this.chatMessages.size,
      totalFriends: this.friendsMap.size,
      reconnectAttempts: this.reconnectAttempts,
      messageListeners: this.messageListeners.size,
      connectionListeners: this.connectionListeners.size
    }
  }
}

// 🆕 WebSocket管理器初始化助手
export const initializeWebSocketManager = async () => {
  try {
    // 动态导入好友API
    const { getContacts, getCurrentUserId, getCurrentUsername } = await import('@/api/friend.js')
    const { getUserInfo } = await import('@/api/auth.js')
    
    // 获取当前用户信息
    const userInfo = getUserInfo()
    if (!userInfo) {
      console.warn('⚠️ 未找到用户信息，跳过WebSocket初始化')
      return false
    }
    
    // 加载好友列表
    const contactsResult = await getContacts()
    if (contactsResult.success) {
      const friendsList = contactsResult.data
        .filter(contact => contact.status === 'accepted')
        .map(contact => ({
          id: contact.friend_id,
          username: contact.friend?.username || `User${contact.friend_id}`,
          avatar: contact.friend?.avatar || '',
          is_online: contact.friend?.is_online || false,
          email: contact.friend?.email || ''
        }))
      
      wsManager.setFriendsMap(friendsList)
      console.log('✅ WebSocket管理器初始化完成，好友数量:', friendsList.length)
    }
    
    return true
  } catch (error) {
    console.error('❌ WebSocket管理器初始化失败:', error)
    return false
  }
}

export const wsManager = new WebSocketManager()
export default wsManager
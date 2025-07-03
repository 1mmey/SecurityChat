import Peer from 'peerjs'
import { getUserConnectionInfo, getFriendsOnlineStatus } from '@/api/chat.js'
import { getUserInfo } from '@/api/auth.js'
import { ElMessage } from 'element-plus'

/**
 * P2P即时通信管理器 - 修复版
 */
export class P2PManager {
  constructor() {
    this.peer = null
    this.connections = new Map() // username -> connection
    this.messageHandlers = new Set()
    this.connectionHandlers = new Set()
    this.isInitialized = false
    this.currentUser = null
    this.reconnectAttempts = new Map()
    this.maxReconnectAttempts = 3
    
    // 消息缓存
    this.messageQueue = new Map()
    
    // 🆕 用户PeerID注册表
    this.userPeerIds = new Map() // username -> peerId
    this.peerIdUsers = new Map() // peerId -> username
  }

  /**
   * 🆕 生成标准的PeerID
   */
  generatePeerId(username) {
    // 使用固定格式，便于其他用户连接
    return `chat_${username.toLowerCase()}`
  }

  /**
   * 初始化P2P连接
   */
  async initialize() {
    try {
      const userInfo = getUserInfo()
      if (!userInfo) {
        throw new Error('用户信息获取失败')
      }

      this.currentUser = userInfo
      
      // 🆕 使用标准PeerID生成规则
      const peerId = this.generatePeerId(userInfo.username)
      
      console.log('🔗 创建PeerJS实例，PeerID:', peerId)
      
      this.peer = new Peer(peerId, {
        // 🆕 使用免费的公共服务器，更稳定
        host: '0.peerjs.com',
        port: 443,
        path: '/',
        secure: true,
        debug: 1,
        config: {
          'iceServers': [
            { urls: 'stun:stun.l.google.com:19302' },
            { urls: 'stun:stun1.l.google.com:19302' }
          ]
        }
      })

      this.setupPeerEvents()
      
      await this.waitForPeerReady()
      
      // 🆕 注册自己的PeerID
      this.userPeerIds.set(userInfo.username, peerId)
      this.peerIdUsers.set(peerId, userInfo.username)
      
      this.isInitialized = true
      console.log('✅ P2P管理器初始化成功，PeerID:', this.peer.id)
      
      this.notifyConnectionHandlers('initialized', { peerId: this.peer.id })
      
      return true
    } catch (error) {
      console.error('❌ P2P管理器初始化失败:', error)
      this.notifyConnectionHandlers('error', error)
      throw error
    }
  }

  /**
   * 等待Peer连接就绪
   */
  waitForPeerReady() {
    return new Promise((resolve, reject) => {
      if (this.peer.open) {
        resolve()
        return
      }

      this.peer.on('open', (id) => {
        console.log('🔗 PeerJS连接已建立，ID:', id)
        resolve()
      })

      this.peer.on('error', (error) => {
        console.error('❌ PeerJS连接错误:', error)
        reject(error)
      })

      // 设置超时
      setTimeout(() => {
        if (!this.peer.open) {
          reject(new Error('PeerJS连接超时'))
        }
      }, 15000) // 增加超时时间
    })
  }

  /**
   * 设置Peer事件监听
   */
  setupPeerEvents() {
    this.peer.on('connection', (conn) => {
      console.log('📞 收到P2P连接请求，来自:', conn.peer)
      this.handleIncomingConnection(conn)
    })

    this.peer.on('error', (error) => {
      console.error('❌ PeerJS错误:', error)
      this.notifyConnectionHandlers('error', error)
      
      // 🆕 改进错误处理
      if (error.type === 'disconnected') {
        console.log('🔄 PeerJS连接断开，尝试重连...')
        setTimeout(() => this.attemptReconnectPeer(), 3000)
      } else if (error.type === 'peer-unavailable') {
        console.warn('⚠️ 目标用户不在线或PeerID不存在')
      }
    })

    this.peer.on('disconnected', () => {
      console.log('🔌 PeerJS服务器连接断开')
      this.notifyConnectionHandlers('disconnected')
    })

    this.peer.on('close', () => {
      console.log('🔌 PeerJS连接已关闭')
      this.isInitialized = false
    })
  }

  /**
   * 处理接收到的P2P连接
   */
  handleIncomingConnection(conn) {
    const senderPeerId = conn.peer
    const senderUsername = this.extractUsernameFromPeerId(senderPeerId)
    
    console.log(`📞 处理来自 ${senderUsername} (${senderPeerId}) 的连接`)
    
    // 🆕 注册发送方的PeerID
    this.userPeerIds.set(senderUsername, senderPeerId)
    this.peerIdUsers.set(senderPeerId, senderUsername)
    
    conn.on('open', () => {
      console.log(`✅ P2P连接已建立: ${senderUsername}`)
      this.connections.set(senderUsername, conn)
      this.notifyConnectionHandlers('peer_connected', { username: senderUsername, peerId: senderPeerId })
      
      // 发送缓存的消息
      this.sendQueuedMessages(senderUsername)
    })

    conn.on('data', (data) => {
      console.log(`📨 收到来自 ${senderUsername} 的P2P消息:`, data)
      this.handleIncomingMessage(data, senderUsername)
    })

    conn.on('close', () => {
      console.log(`🔌 与 ${senderUsername} 的P2P连接已关闭`)
      this.connections.delete(senderUsername)
      this.notifyConnectionHandlers('peer_disconnected', { username: senderUsername })
    })

    conn.on('error', (error) => {
      console.error(`❌ 与 ${senderUsername} 的P2P连接错误:`, error)
      this.connections.delete(senderUsername)
      this.notifyConnectionHandlers('peer_error', { username: senderUsername, error })
    })
  }

  /**
   * 🆕 改进的用户名提取方法
   */
  extractUsernameFromPeerId(peerId) {
    // PeerID格式: chat_username
    if (peerId.startsWith('chat_')) {
      return peerId.substring(5) // 移除 'chat_' 前缀
    }
    return peerId
  }

  /**
   * 🆕 改进的连接到用户方法
   */
  async connectToUser(username) {
    try {
      if (!this.isInitialized) {
        await this.initialize()
      }

      // 检查是否已经连接
      if (this.connections.has(username)) {
        const existingConn = this.connections.get(username)
        if (existingConn.open) {
          console.log(`✅ 已经与 ${username} 建立P2P连接`)
          return existingConn
        } else {
          // 清理无效连接
          this.connections.delete(username)
        }
      }

      console.log(`🔗 正在连接到用户: ${username}`)

      // 🆕 使用标准PeerID
      const targetPeerId = this.generatePeerId(username)
      console.log(`🎯 目标PeerID: ${targetPeerId}`)

      // 尝试连接
      const conn = this.peer.connect(targetPeerId, {
        label: 'chat',
        serialization: 'json',
        metadata: {
          username: this.currentUser.username,
          timestamp: Date.now()
        }
      })

      return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          if (!conn.open) {
            conn.close()
            reject(new Error(`连接到 ${username} 超时`))
          }
        }, 10000)

        conn.on('open', () => {
          clearTimeout(timeout)
          console.log(`✅ 成功连接到 ${username}`)
          
          // 🆕 注册对方的PeerID
          this.userPeerIds.set(username, targetPeerId)
          this.peerIdUsers.set(targetPeerId, username)
          
          this.connections.set(username, conn)
          this.notifyConnectionHandlers('peer_connected', { username, peerId: targetPeerId })
          
          // 发送缓存的消息
          this.sendQueuedMessages(username)
          
          resolve(conn)
        })

        conn.on('error', (error) => {
          clearTimeout(timeout)
          console.error(`❌ 连接到 ${username} 失败:`, error)
          reject(error)
        })

        // 🆕 处理连接关闭
        conn.on('close', () => {
          console.log(`🔌 与 ${username} 的连接被关闭`)
          this.connections.delete(username)
        })
      })

    } catch (error) {
      console.error(`❌ 连接到 ${username} 失败:`, error)
      throw error
    }
  }

  /**
   * 发送消息给指定用户
   */
  async sendMessage(username, content, messageType = 'text') {
    try {
      const message = {
        id: `p2p_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        type: messageType,
        content: content,
        sender: this.currentUser.username,
        recipient: username,
        timestamp: new Date().toISOString()
      }

      console.log(`📤 准备发送P2P消息给 ${username}:`, message)

      // 检查是否有活跃连接
      let connection = this.connections.get(username)
      
      if (!connection || !connection.open) {
        console.log(`🔗 尝试建立与 ${username} 的P2P连接`)
        
        try {
          connection = await this.connectToUser(username)
        } catch (error) {
          console.warn(`❌ P2P连接失败: ${error.message}`)
          
          // 将消息加入队列
          this.queueMessage(username, message)
          throw new Error(`P2P连接失败: ${error.message}`)
        }
      }

      // 发送消息
      if (connection && connection.open) {
        connection.send(message)
        console.log(`📤 P2P消息已发送给 ${username}`)
        
        // 通知消息发送成功
        this.notifyMessageHandlers({
          type: 'sent',
          message: {
            ...message,
            senderId: this.currentUser.id,
            senderName: this.currentUser.username,
            senderUsername: this.currentUser.username,
            receiverUsername: username,
            status: 'delivered',
            isP2PMessage: true
          }
        })
        
        return true
      } else {
        throw new Error('P2P连接不可用')
      }

    } catch (error) {
      console.error('❌ P2P消息发送失败:', error)
      
      // 将失败的消息加入队列
      this.queueMessage(username, {
        id: `p2p_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        type: messageType,
        content: content,
        sender: this.currentUser.username,
        recipient: username,
        timestamp: new Date().toISOString(),
        failed: true
      })
      
      throw error
    }
  }

  /**
   * 处理接收到的消息
   */
  handleIncomingMessage(data, senderUsername) {
    try {
      console.log('📨 处理P2P接收消息，来自:', senderUsername, '内容:', data)
      
      const message = {
        id: data.id || `received_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        type: 'received',
        content: data.content,
        timestamp: new Date(data.timestamp).getTime(),
        senderId: senderUsername, // 使用用户名作为ID
        senderName: senderUsername,
        senderUsername: senderUsername,
        receiverId: this.currentUser.id,
        receiverUsername: this.currentUser.username,
        avatar: '',
        isP2PMessage: true,
        status: 'delivered'
      }

      console.log('📨 格式化后的P2P消息:', message)
      
      // 通知消息处理器
      this.notifyMessageHandlers({
        type: 'received',
        message: message,
        sender: senderUsername
      })

    } catch (error) {
      console.error('❌ 处理P2P消息失败:', error)
    }
  }

  /**
   * 将消息加入队列
   */
  queueMessage(username, message) {
    if (!this.messageQueue.has(username)) {
      this.messageQueue.set(username, [])
    }
    
    this.messageQueue.get(username).push(message)
    console.log(`📝 消息已加入队列 (${username}):`, message)
  }

  /**
   * 发送队列中的消息
   */
  sendQueuedMessages(username) {
    const queue = this.messageQueue.get(username)
    if (!queue || queue.length === 0) {
      return
    }

    const connection = this.connections.get(username)
    if (!connection || !connection.open) {
      return
    }

    console.log(`📤 发送队列中的消息给 ${username}:`, queue.length, '条')

    queue.forEach(message => {
      try {
        connection.send(message)
        console.log('📤 队列消息已发送:', message)
      } catch (error) {
        console.error('❌ 发送队列消息失败:', error)
      }
    })

    // 清空队列
    this.messageQueue.set(username, [])
  }

  /**
   * 🆕 简化的连接在线好友方法
   */
  async connectToOnlineFriends() {
    try {
      console.log('🔗 开始连接在线好友...')
      
      // 不主动连接，而是等待其他用户连接
      // 这样可以避免双向连接冲突
      console.log('⏳ P2P管理器已就绪，等待其他用户连接')
      
    } catch (error) {
      console.error('❌ 连接在线好友失败:', error)
    }
  }

  /**
   * 断开与指定用户的连接
   */
  disconnectFromUser(username) {
    const connection = this.connections.get(username)
    if (connection) {
      connection.close()
      this.connections.delete(username)
      console.log(`🔌 已断开与 ${username} 的P2P连接`)
    }
  }

  /**
   * 断开所有P2P连接
   */
  disconnectAll() {
    this.connections.forEach((conn, username) => {
      conn.close()
      console.log(`🔌 断开与 ${username} 的连接`)
    })
    this.connections.clear()
    this.userPeerIds.clear()
    this.peerIdUsers.clear()

    if (this.peer && !this.peer.destroyed) {
      this.peer.destroy()
      this.peer = null
    }

    this.isInitialized = false
    console.log('🔌 所有P2P连接已断开')
  }

  /**
   * 获取连接状态
   */
  getConnectionStatus(username = null) {
    if (!this.isInitialized) {
      return 'not_initialized'
    }

    if (username) {
      const connection = this.connections.get(username)
      return connection && connection.open ? 'connected' : 'disconnected'
    }

    return {
      initialized: this.isInitialized,
      peerId: this.peer?.id,
      totalConnections: this.connections.size,
      connectedUsers: Array.from(this.connections.keys()),
      queuedMessages: Array.from(this.messageQueue.entries()).map(([user, messages]) => ({
        user,
        count: messages.length
      }))
    }
  }

  // 其他方法保持不变...
  addMessageHandler(handler) { this.messageHandlers.add(handler) }
  removeMessageHandler(handler) { this.messageHandlers.delete(handler) }
  addConnectionHandler(handler) { this.connectionHandlers.add(handler) }
  removeConnectionHandler(handler) { this.connectionHandlers.delete(handler) }

  notifyMessageHandlers(data) {
    this.messageHandlers.forEach(handler => {
      try {
        handler(data)
      } catch (error) {
        console.error('❌ P2P消息处理器错误:', error)
      }
    })
  }

  notifyConnectionHandlers(status, data = null) {
    this.connectionHandlers.forEach(handler => {
      try {
        handler(status, data)
      } catch (error) {
        console.error('❌ P2P连接状态处理器错误:', error)
      }
    })
  }

  attemptReconnectPeer() {
    if (this.peer && !this.peer.destroyed) {
      console.log('🔄 尝试重连PeerJS服务器')
      this.peer.reconnect()
    }
  }
}

// 创建全局P2P管理器实例
export const p2pManager = new P2PManager()

// 导出默认实例
export default p2pManager
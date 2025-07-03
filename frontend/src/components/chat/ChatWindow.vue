<template>
  <div class="chat-window">
    <!-- 左侧对话列表面板 -->
    <div class="friends-panel">
      <!-- 搜索栏 -->
      <div class="search-section">
        <div class="search-input">
          <el-icon class="search-icon">
            <Search />
          </el-icon>
          <input
            v-model="searchText"
            type="text"
            placeholder="搜索聊天..."
            @input="handleSearch"
            class="search-field"
          />
          <el-icon 
            v-if="searchText"
            class="clear-icon"
            @click="clearSearch"
          >
            <Close />
          </el-icon>
        </div>
      </div>

      <!-- 聊天列表头部 -->
      <div class="list-header">
        <div class="header-title">
          <span>最近聊天</span>
          <span class="chat-count">({{ filteredChats.length }})</span>
        </div>
        <!-- WebSocket连接状态指示器 -->
        <div class="connection-status">
          <div 
            class="status-indicator"
            :class="connectionStatus"
            :title="connectionStatusText"
          ></div>
        </div>
      </div>

      <!-- 聊天列表 -->
      <div class="friends-container">
        <div class="friends-list-content">
          <div
            v-for="chat in filteredChats"
            :key="chat?.id || Math.random()"
            class="friend-item"
            :class="{ active: selectedFriend?.id === chat?.id }"
            @click="selectFriend(chat)"
          >
            <!-- 好友头像 -->
            <div class="friend-avatar">
              <img 
                :src="chat?.avatar || defaultAvatar"
                :alt="chat?.username || 'User'"
                class="avatar-img"
              />
              <div 
                class="status-dot"
                :class="chat?.is_online ? 'online' : 'offline'"
              ></div>
            </div>

            <!-- 好友信息 -->
            <div class="friend-info">
              <div class="friend-name">{{ chat?.username || 'Unknown' }}</div>
              <div class="friend-message">
                <span class="message-text">{{ chat?.lastMessage || '开始对话吧' }}</span>
              </div>
            </div>

            <!-- 时间和未读数 -->
            <div class="friend-meta">
              <div class="message-time">{{ formatTime(chat?.lastMessageTime) }}</div>
              <div 
                v-if="chat?.unreadCount > 0"
                class="unread-badge"
              >
                {{ chat.unreadCount > 99 ? '99+' : chat.unreadCount }}
              </div>
            </div>
          </div>

          <!-- 空状态 -->
          <div v-if="filteredChats.length === 0" class="empty-state">
            <el-icon class="empty-icon">
              <ChatDotRound />
            </el-icon>
            <div class="empty-text">
              {{ searchText ? '未找到相关聊天' : '暂无聊天记录' }}
            </div>
            <div class="empty-hint">
              从左侧好友列表双击好友开始聊天
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧聊天内容区域 -->
    <div class="chat-content">
      <!-- 聊天头部 -->
      <div v-if="selectedFriend" class="chat-header">
        <div class="friend-info">
          <img 
            :src="selectedFriend?.avatar || defaultAvatar"
            :alt="selectedFriend?.username || 'User'"
            class="friend-avatar"
          />
          <div class="friend-details">
            <div class="friend-name">{{ selectedFriend?.username || 'Unknown' }}</div>
            <div class="friend-status">{{ selectedFriend?.is_online ? '在线' : '离线' }}</div>
          </div>
        </div>
        
        <div class="chat-actions">
          <el-button 
            circle 
            size="small" 
            :icon="Phone" 
            @click="makeVoiceCall"
            class="action-btn"
          />
          <el-button 
            circle 
            size="small" 
            :icon="VideoCamera" 
            @click="makeVideoCall"
            class="action-btn"
          />
          <el-button 
            circle 
            size="small" 
            :icon="InfoFilled" 
            @click="showChatInfo"
            class="action-btn"
          />
        </div>
      </div>

      <!-- 消息区域 -->
      <div class="messages-container" ref="messagesContainer">
        <div class="messages-content">
          <!-- 选中好友时显示消息 -->
          <div v-if="selectedFriend && currentMessages.length > 0">
            <div
              v-for="message in currentMessages"
              :key="message?.id || `msg-${Math.random()}`"
              class="message-item"
              :class="{ 
                'own-message': isOwnMessage(message),
                'offline-message': message?.isOfflineMessage,
                'sending': message?.status === 'sending'
              }"
            >
              <div class="message-avatar">
                <img 
                  :src="message?.avatar || defaultAvatar"
                  :alt="message?.senderName || 'User'"
                  class="avatar-img"
                />
              </div>
              
              <div class="message-content">
                <div class="message-bubble">
                  <div v-if="message?.type === 'text' || message?.type === 'sent' || message?.type === 'received'" class="text-message">
                    {{ message?.content || '消息内容为空' }}
                  </div>
                  
                  <div v-else-if="message?.type === 'image'" class="image-message">
                    <img 
                      :src="message?.content"
                      @click="previewImage(message?.content)"
                      class="message-image"
                    />
                  </div>
                  
                  <div v-else-if="message?.type === 'file'" class="file-message">
                    <div class="file-info">
                      <el-icon class="file-icon">
                        <Document />
                      </el-icon>
                      <div class="file-details">
                        <span class="file-name">{{ message?.fileName || '未知文件' }}</span>
                        <span class="file-size">({{ formatFileSize(message?.fileSize || 0) }})</span>
                      </div>
                    </div>
                    <!-- 如果是接收到的文件且有文件数据，显示下载按钮 -->
                    <el-button 
                      v-if="message?.fileData && !isOwnMessage(message)"
                      size="small" 
                      type="primary" 
                      @click="downloadReceivedFile(message)"
                      class="download-btn"
                    >
                      下载
                    </el-button>
                  </div>
                </div>
                
                <div class="message-meta">
                  <div class="message-time">
                    {{ formatMessageTime(message?.timestamp) }}
                  </div>
                  <!-- 消息状态指示器 -->
                  <div v-if="isOwnMessage(message)" class="message-status">
                    <el-icon v-if="message?.status === 'sending'" class="status-sending">
                      <Loading />
                    </el-icon>
                    <el-icon v-else-if="message?.status === 'delivered'" class="status-delivered">
                      <Check />
                    </el-icon>
                    <el-icon v-else-if="message?.status === 'failed'" class="status-failed">
                      <Close />
                    </el-icon>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-else-if="selectedFriend && currentMessages.length === 0" class="empty-messages">
            <div class="welcome-info">
              <div class="friend-name-large">{{ selectedFriend?.username || 'Unknown' }}</div>
              <div class="friend-status-info">{{ selectedFriend?.is_online ? '在线' : '离线' }}</div>
            </div>
            <el-icon class="empty-icon">
              <ChatDotRound />
            </el-icon>
            <div class="empty-text">开始与 {{ selectedFriend?.username || 'Unknown' }} 的对话吧</div>
            <div class="empty-hint">发送第一条消息来开始聊天</div>
          </div>

          <!-- 未选中好友状态 -->
          <div v-else class="no-chat-selected">
            <el-icon class="welcome-icon">
              <ChatLineRound />
            </el-icon>
            <div class="welcome-title">安全即时通讯</div>
            <div class="welcome-subtitle">选择一个好友开始聊天</div>
            <div class="welcome-hint">
              <el-icon><InfoFilled /></el-icon>
              <span>从左侧好友列表双击好友可以快速开始对话</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div v-if="selectedFriend" class="input-area">
        <div class="input-toolbar">
          <el-button 
            size="small" 
            :icon="Paperclip" 
            @click="selectFile"
            text
            class="toolbar-btn"
          >
            文件
          </el-button>
          <el-button 
            size="small" 
            :icon="Picture" 
            @click="selectImage"
            text
            class="toolbar-btn"
          >
            图片
          </el-button>
          <el-button 
            size="small" 
            :icon="Lock" 
            @click="toggleSteganography"
            text
            class="toolbar-btn"
          >
            隐写
          </el-button>
        </div>
        
        <div class="input-container">
          <el-input
            v-model="inputMessage"
            ref="messageInput"
            type="textarea"
            placeholder="输入消息..."
            class="message-input"
            :autosize="{ minRows: 1, maxRows: 4 }"
            @keydown="handleKeyDown"
            resize="none"
          />
          
          <el-button
            type="primary"
            :disabled="!inputMessage.trim() || connectionStatus !== 'connected'"
            @click="sendMessage"
            class="send-button"
            size="default"
            :loading="sendingMessage"
          >
            发送
          </el-button>
        </div>
        
        <!-- 连接状态提示 -->
        <div v-if="connectionStatus !== 'connected'" class="connection-warning">
          <el-icon><Warning /></el-icon>
          <span>{{ connectionStatusText }}，消息将在连接恢复后发送</span>
        </div>
      </div>
    </div>
    
    <!-- 隐藏的文件选择器 -->
    <input
      ref="fileInput"
      type="file"
      style="display: none"
      @change="handleFileSelect"
    />
    
    <input
      ref="imageInput"
      type="file"
      accept="image/*"
      style="display: none"
      @change="handleImageSelect"
    />
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch, onMounted, onUnmounted } from 'vue'
import { getUserInfo } from '@/api/auth.js'
import { ElMessage } from 'element-plus'
import { 
  Search, 
  Close, 
  Phone, 
  VideoCamera, 
  InfoFilled,
  ChatDotRound,
  ChatLineRound,
  Document,
  Paperclip,
  Picture,
  Lock,
  Loading,
  Check,
  Warning
} from '@element-plus/icons-vue'
import { getCurrentUserId } from '@/api/friend.js'
import defaultAvatarImg from '/src/assets/image.png'
import wsManagerInstance from '@/api/chat.js'
import { FileTransferAPI } from '@/api/file.js'

// WebSocket相关变量
let messageListener = null
let connectionListener = null
const connectionStatus = ref('disconnected')
const sendingMessage = ref(false)

const emit = defineEmits(['send-message', 'file-upload', 'friend-status-changed'])

const props = defineProps({
  activeFriend: {
    type: Object,
    default: null
  },
  friendsList: {
    type: Array,
    default: () => []
  },
  messages: {
    type: Array,
    default: () => []
  }
})

// 基础变量
const currentUserId = ref(null)
const inputMessage = ref('')
const searchText = ref('')
const selectedFriend = ref(null)
const currentMessages = ref([])
const chatList = ref([])
const defaultAvatar = defaultAvatarImg

// DOM引用
const messagesContainer = ref(null)
const messageInput = ref(null)
const fileInput = ref(null)
const imageInput = ref(null)

// 连接状态文本
const connectionStatusText = computed(() => {
  switch (connectionStatus.value) {
    case 'connected':
      return '已连接'
    case 'connecting':
      return '连接中'
    case 'disconnected':
      return '连接已断开'
    case 'error':
      return '连接错误'
    default:
      return '未知状态'
  }
})

// 过滤后的聊天列表
const filteredChats = computed(() => {
  if (!searchText.value.trim()) {
    return chatList.value
  }
  
  return chatList.value.filter(chat => 
    chat?.username?.toLowerCase().includes(searchText.value.toLowerCase())
  )
})

const isOwnMessage = (message) => {
  if (!message) return false
  
  const currentUsername = getCurrentUsername()
  
  return message.senderId === currentUserId.value || 
         message.type === 'sent' ||
         message.senderUsername === currentUsername ||
         (wsManagerInstance && typeof wsManagerInstance.isCurrentUserMessage === 'function' && wsManagerInstance.isCurrentUserMessage(message))
}

// 设置WebSocket监听器
const setupWebSocketListeners = async () => {
  try {
    const userInfo = getUserInfo()
    const token = userInfo?.token || localStorage.getItem('access_token')
    
    if (!token) {
      console.error('无法初始化WebSocket：缺少认证token')
      ElMessage.error('认证信息缺失，请重新登录')
      return
    }

    console.log('🔗 开始建立WebSocket连接...')

    // 设置好友列表映射
    if (props.friendsList.length > 0) {
        wsManagerInstance.setFriendsMap(props.friendsList)
    }
    
    // 移除旧的监听器（避免重复）
    if (messageListener) {
        wsManagerInstance.removeMessageListener(messageListener)
    }
    if (connectionListener) {
        wsManagerInstance.removeConnectionListener(connectionListener)
    }
    
    // 设置新的消息处理器
    messageListener = (data) => {
      console.log('📨 ChatWindow收到消息:', data)
      handleIncomingWebSocketMessage(data)
    }
      wsManagerInstance.addMessageListener(messageListener)
    
    // 设置连接状态处理器
    connectionListener = (status, event) => {
      console.log('🔌 WebSocket状态变化:', status)
      connectionStatus.value = status
      
      // 🆕 添加状态提示
      if (status === 'connected') {
        ElMessage.success('WebSocket连接成功')
      } else if (status === 'error') {
        ElMessage.error('WebSocket连接失败')
      } else if (status === 'disconnected') {
        ElMessage.warning('WebSocket连接已断开')
      }
    }
      wsManagerInstance.addConnectionListener(connectionListener)
    
    // 🆕 修改连接方式
    connectionStatus.value = 'connecting'
    const success =   wsManagerInstance.connect()
    
    if (!success) {
      console.error('WebSocket连接启动失败')
      connectionStatus.value = 'error'
      ElMessage.error('WebSocket连接启动失败')
    }
    
  } catch (error) {
    console.error('WebSocket初始化失败:', error)
    connectionStatus.value = 'error'
    ElMessage.error('WebSocket初始化失败: ' + error.message)
  }
}


const handleIncomingWebSocketMessage = (data) => {
  console.log('📨 处理WebSocket消息:', data)
  console.log('📨 当前选中好友:', selectedFriend.value?.username)
  console.log('📨 当前用户名:', getCurrentUsername())
  
  // 根据新的chat.js结构处理消息
  if (data.type === 'message') {
    // 处理来自WebSocketManager包装的消息
    const message = data.message
    if (message && message.senderUsername) {
      console.log('📨 处理封装消息:', message)
      addReceivedMessage(message)
    }
  } else if (data.type === 'system') {
    // 处理系统消息
    console.log('📢 系统消息:', data.content)
    handleSystemMessage(data.content)
  } else if (data.type === 'status') {
    console.log('📋 状态消息:', data.content)
  } else if (data.type === 'error') {
    console.error('❌ 错误消息:', data.content)
    ElMessage.error(data.content)
  } else {
    // 处理直接的消息对象（可能是离线消息或P2P消息）
    console.log('📨 处理直接消息:', data)
    
    // 检查是否是文件消息
    if (data.content && FileTransferAPI.isFileMessage(data.content)) {
      console.log('📁 识别为文件消息')
      const fileInfo = FileTransferAPI.parseFileMessage(data.content)
      if (fileInfo) {
        const fileMessage = {
          id: `file_received_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          type: 'file',
          content: `收到文件: ${fileInfo.fileName}`,
          fileName: fileInfo.fileName,
          fileSize: fileInfo.fileSize,
          fileType: fileInfo.fileType,
          fileData: fileInfo.fileData,
          timestamp: data.timestamp ? new Date(data.timestamp).getTime() : Date.now(),
          senderId: data.senderUsername || data.sender_username,
          senderName: data.senderUsername || data.sender_username,
          senderUsername: data.senderUsername || data.sender_username,
          receiverId: currentUserId.value,
          avatar: defaultAvatar,
          status: 'delivered'
        }
        
        console.log('📁 创建文件消息对象:', fileMessage)
        addReceivedMessage(fileMessage)
        ElMessage.success(`收到来自 ${fileMessage.senderName} 的文件: ${fileInfo.fileName}`)
        return
      }
    }
    
    // 普通文本消息
    if (data.content && (data.senderUsername || data.sender_username)) {
      const message = {
        id: `received_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        type: 'received',
        content: data.content,
        timestamp: data.timestamp ? new Date(data.timestamp).getTime() : Date.now(),
        senderId: data.senderUsername || data.sender_username,
        senderName: data.senderUsername || data.sender_username,
        senderUsername: data.senderUsername || data.sender_username,
        receiverId: currentUserId.value,
        avatar: defaultAvatar,
        status: 'delivered'
      }
      
      console.log('💬 创建文本消息:', message)
      addReceivedMessage(message)
    }
  }
}

const downloadReceivedFile = (message) => {
  if (message.fileData && message.fileName) {
    FileTransferAPI.downloadFile(message.fileData, message.fileName)
    ElMessage.success('文件下载完成')
  }
}

const addReceivedMessage = (message) => {
  if (!message || !message.senderUsername) {
    console.warn('收到无效消息，跳过处理:', message)
    return
  }

  // 避免处理自己发送的消息
  const currentUsername = getCurrentUsername()
  if (message.senderUsername === currentUsername) {
    console.log('⏭️ 跳过自己发送的消息')
    return
  }

  try {
    console.log('📨 处理接收到的消息:', message)
    console.log('📨 发送者:', message.senderUsername)
    console.log('📨 当前选中好友:', selectedFriend.value?.username)
    
    // 保存到本地存储
    addMessageToLocalStorage(message.senderUsername, message)
    
    // 检查是否属于当前聊天
    if (selectedFriend.value && selectedFriend.value.username === message.senderUsername) {
      // 避免重复添加
      const existingMessage = currentMessages.value.find(m => m && m.id === message.id)
      if (!existingMessage) {
        console.log('📨 添加消息到当前聊天')
        currentMessages.value.push(message)
        currentMessages.value.sort((a, b) => (a?.timestamp || 0) - (b?.timestamp || 0))
        
        nextTick(() => {
          scrollToBottom()
        })
      } else {
        console.log('📨 消息已存在，跳过添加')
      }
    } else {
      console.log('📨 消息不属于当前聊天，只更新聊天列表')
    }
    
    // 更新聊天列表
    updateChatListWithMessage(message, message.senderUsername)
    
    // 显示通知
    if (!selectedFriend.value || message.senderUsername !== selectedFriend.value.username) {
      if (message.type === 'file') {
        ElMessage.info(`收到来自 ${message.senderName || message.senderUsername} 的文件`)
      } else {
        ElMessage.info(`收到来自 ${message.senderName || message.senderUsername} 的新消息`)
      }
    }
  } catch (error) {
    console.error('处理接收消息时出错:', error)
  }
}

const saveMessagesToLocal = (username, messages) => {
  try {
    const currentUser = getCurrentUsername()
    const storageKey = `chat_messages_${currentUser}_${username}`
    localStorage.setItem(storageKey, JSON.stringify(messages))
    console.log(`💾 保存聊天记录到本地: ${username}, ${messages.length}条消息`)
  } catch (error) {
    console.error('保存聊天记录失败:', error)
  }
}

const loadMessagesFromLocal = (username) => {
  try {
    const currentUser = getCurrentUsername()
    const storageKey = `chat_messages_${currentUser}_${username}`
    const stored = localStorage.getItem(storageKey)
    if (stored) {
      const messages = JSON.parse(stored)
      console.log(`📂 从本地加载聊天记录: ${username}, ${messages.length}条消息`)
      return messages
    }
  } catch (error) {
    console.error('加载聊天记录失败:', error)
  }
  return []
}

const addMessageToLocalStorage = (username, message) => {
  const existingMessages = loadMessagesFromLocal(username)
  
  // 避免重复添加
  const existingMessage = existingMessages.find(m => m.id === message.id)
  if (!existingMessage) {
    existingMessages.push(message)
    existingMessages.sort((a, b) => (a.timestamp || 0) - (b.timestamp || 0))
    saveMessagesToLocal(username, existingMessages)
  }
}


// 处理系统消息
const handleSystemMessage = (content) => {
  if (content && (content.includes('已上线') || content.includes('已下线'))) {
    // 好友上线/下线，更新好友状态
    setTimeout(() => {
      emit('friend-status-changed')
    }, 1000)
  }
}

const updateChatListWithMessage = (message, senderUsername) => {
  if (!message || !senderUsername) {
    console.warn('updateChatListWithMessage: 无效参数', { message, senderUsername })
    return
  }

  try {
    const friendUsername = isOwnMessage(message) ? 
      (message.receiverUsername || selectedFriend.value?.username) : 
      senderUsername
    
    if (!friendUsername) return
    
    const friend = props.friendsList.find(f => f && f.username === friendUsername)
    if (friend) {
      ensureFriendInChatList(friend)
      
      // 更新最后消息
      const chatItem = chatList.value.find(chat => chat && chat.username === friendUsername)
      if (chatItem) {
        // 改进：为文件消息显示更友好的预览
        let displayMessage = ''
        if (message.type === 'file') {
          displayMessage = `[文件] ${message.fileName}`
        } else if (message.content) {
          displayMessage = message.content.length > 20 ? 
            message.content.substring(0, 20) + '...' : 
            message.content
        }
        
        if (displayMessage) {
          chatItem.lastMessage = displayMessage
          chatItem.lastMessageTime = message.timestamp
          
          // 只有接收到的消息（非自己发送的）且不在当前聊天中时才增加未读数
          if (!isOwnMessage(message) && (!selectedFriend.value || selectedFriend.value.username !== friendUsername)) {
            chatItem.unreadCount = (chatItem.unreadCount || 0) + 1
          }
          
          // 移到列表顶部
          const index = chatList.value.indexOf(chatItem)
          if (index > 0) {
            chatList.value.splice(index, 1)
            chatList.value.unshift(chatItem)
          }
        }
      }
    }
  } catch (error) {
    console.error('更新聊天列表时出错:', error)
  }
}

const getCurrentUsername = () => {
  const userInfo = getUserInfo()
  return userInfo?.username || localStorage.getItem('username') || 'Unknown'
}

const sendMessage = async () => {
  if (!inputMessage.value.trim() || !selectedFriend.value) return
  
  console.log('发送消息到:', selectedFriend.value.username)
  sendingMessage.value = true
  
  try {
    const messageContent = inputMessage.value.trim()
    
    // 🆕 改进连接状态检查
    const currentStatus =   wsManagerInstance.getConnectionStatus()
    console.log('当前WebSocket状态:', currentStatus)
    
    if (currentStatus !== 'connected') {
      console.warn('WebSocket未连接，状态:', currentStatus)
      
      // 🆕 如果连接断开，尝试重新连接
      if (currentStatus === 'disconnected') {
        console.log('尝试重新连接WebSocket...')
        connectionStatus.value = 'connecting'
        const success =   wsManagerInstance.connect()
        if (!success) {
          throw new Error('重新连接失败')
        }
        // 等待连接建立
        await new Promise(resolve => setTimeout(resolve, 2000))
      }
      
      if (  wsManagerInstance.getConnectionStatus() !== 'connected') {
        throw new Error('WebSocket连接未建立')
      }
    }
    
    // 立即添加到本地聊天记录（发送前显示）
    const localMessage = {
      id: `sent_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type: 'sent',
      content: messageContent,
      timestamp: Date.now(),
      senderId: currentUserId.value,
      senderName: getCurrentUsername(),
      senderUsername: getCurrentUsername(),
      receiverId: selectedFriend.value.id,
      receiverUsername: selectedFriend.value.username,
      avatar: '',
      status: 'sending',
      isLocalMessage: true
    }
    
    // 立即显示在聊天窗口
    currentMessages.value.push(localMessage)
    updateChatListWithMessage(localMessage, selectedFriend.value.username)
    inputMessage.value = ''
    addMessageToLocalStorage(selectedFriend.value.username, localMessage)
    scrollToBottom()

    // 使用WebSocket发送消息
    const success =   wsManagerInstance.sendMessage(selectedFriend.value.username, messageContent)
    
    if (success) {
      console.log('📤 消息发送成功')
      localMessage.status = 'delivered'
      addMessageToLocalStorage(selectedFriend.value.username, localMessage)
    } else {
      throw new Error('WebSocket发送失败')
    }
    
  } catch (error) {
    console.error('发送消息失败:', error)
    ElMessage.error('消息发送失败: ' + error.message)
    
    // 🆕 更新最后一条消息的状态为失败
    if (currentMessages.value.length > 0) {
      const lastMessage = currentMessages.value[currentMessages.value.length - 1]
      if (lastMessage.status === 'sending') {
        lastMessage.status = 'failed'
      }
    }
    addMessageToLocalStorage(selectedFriend.value.username, localMessage)
  } finally {
    sendingMessage.value = false
  }
}

// 简化版本，暂时不从WebSocket加载历史记录
const loadChatMessagesFromWebSocket = (friendUsername) => {
  console.log(`📝 暂时跳过从WebSocket加载 ${friendUsername} 的聊天记录`)
}

// 修改后的加载聊天消息函数
const loadChatMessages = (friendId) => {
  // 🆕 首先从props.messages中筛选与该好友的聊天记录
  const propsMessages = props.messages.filter(msg => 
    (msg.senderId === currentUserId.value && msg.receiverId === friendId) ||
    (msg.senderId === friendId && msg.receiverId === currentUserId.value)
  )
  
  // 🆕 从本地存储加载聊天记录
  const friend = props.friendsList.find(f => f.id === friendId)
  let localMessages = []
  if (friend && friend.username) {
    localMessages = loadMessagesFromLocal(friend.username)
    console.log(`📂 从本地加载 ${friend.username} 的消息:`, localMessages.length, '条')
  }
  
  // 🆕 合并所有消息并去重
  const allMessages = [...propsMessages, ...localMessages]
  const uniqueMessages = allMessages.reduce((acc, current) => {
    const existingMessage = acc.find(msg => msg.id === current.id)
    if (!existingMessage) {
      acc.push(current)
    }
    return acc
  }, [])
  
  // 🆕 按时间排序
  currentMessages.value = uniqueMessages.sort((a, b) => (a.timestamp || 0) - (b.timestamp || 0))
  
  console.log('📝 加载聊天消息完成，好友ID:', friendId, '总消息数量:', currentMessages.value.length)
  console.log('📝 消息详情:', currentMessages.value)
  
  // 滚动到底部
  scrollToBottom()
}

// 其余函数保持原样
const ensureFriendInChatList = (friend) => {
  if (!friend || !friend.id) return
  
  const existingIndex = chatList.value.findIndex(chat => chat && chat.id === friend.id)
  
  const chatItem = {
    ...friend,
    lastMessage: getLastMessageForFriend(friend.id),
    lastMessageTime: getLastMessageTimeForFriend(friend.id),
    unreadCount: 0
  }
  
  if (existingIndex === -1) {
    chatList.value.unshift(chatItem)
    console.log('添加新好友到聊天列表:', friend.username)
  } else {
    chatList.value.splice(existingIndex, 1)
    chatList.value.unshift(chatItem)
    console.log('更新好友信息并置顶:', friend.username)
  }
}

const getLastMessageForFriend = (friendId) => {
  const friendMessages = props.messages.filter(msg => 
    (msg.senderId === currentUserId.value && msg.receiverId === friendId) ||
    (msg.senderId === friendId && msg.receiverId === currentUserId.value)
  )
  
  if (friendMessages.length === 0) return ''
  
  const lastMessage = friendMessages[friendMessages.length - 1]
  return lastMessage.type === 'text' ? lastMessage.content : '[文件]'
}

const getLastMessageTimeForFriend = (friendId) => {
  const friendMessages = props.messages.filter(msg => 
    (msg.senderId === currentUserId.value && msg.receiverId === friendId) ||
    (msg.senderId === friendId && msg.receiverId === currentUserId.value)
  )
  
  if (friendMessages.length === 0) return null
  
  const lastMessage = friendMessages[friendMessages.length - 1]
  return lastMessage.timestamp
}

const initializeChatList = () => {
  const chatsWithMessages = []
  const currentUser = currentUserId.value
  
  if (props.friendsList) {
    props.friendsList.forEach(friend => {
      if (!friend || !friend.id) return
      
      const friendMessages = props.messages.filter(msg => 
        (msg.senderId === currentUser && msg.receiverId === friend.id) ||
        (msg.senderId === friend.id && msg.receiverId === currentUser)
      )
      
      if (friendMessages.length > 0) {
        const lastMessage = friendMessages[friendMessages.length - 1]
        chatsWithMessages.push({
          ...friend,
          lastMessage: lastMessage.type === 'text' ? lastMessage.content : '[文件]',
          lastMessageTime: lastMessage.timestamp,
          unreadCount: 0
        })
      }
    })
  }
  
  chatsWithMessages.sort((a, b) => (b.lastMessageTime || 0) - (a.lastMessageTime || 0))
  chatList.value = chatsWithMessages
  console.log('聊天列表初始化完成:', chatList.value)
}

const handleSearch = () => {
  console.log('搜索聊天:', searchText.value)
}

const clearSearch = () => {
  searchText.value = ''
}

const selectFriend = (friend) => {
  if (!friend) return
  
  selectedFriend.value = friend
  console.log('选中好友开始聊天:', friend)
  
  loadChatMessages(friend.id)
  
  const chatItem = chatList.value.find(chat => chat && chat.id === friend.id)
  if (chatItem) {
    chatItem.unreadCount = 0
  }
  
  nextTick(() => {
    messageInput.value?.focus()
  })
}

const handleKeyDown = (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

const addMessage = (message) => {
  if (!message || !selectedFriend.value) return
  
  if (message.senderId === selectedFriend.value.id || message.receiverId === selectedFriend.value.id) {
    currentMessages.value.push(message)
    scrollToBottom()
  }
  
  const friendId = message.senderId === currentUserId.value ? message.receiverId : message.senderId
  const friend = props.friendsList.find(f => f && f.id === friendId)
  if (friend) {
    ensureFriendInChatList(friend)
  }
}

const selectFile = () => {
  fileInput.value?.click()
}

const selectImage = () => {
  imageInput.value?.click()
}

const toggleSteganography = () => {
  console.log('切换隐写模式')
  ElMessage.info('图片隐写功能开发中...')
}

const handleFileSelect = async (event) => {
  const file = event.target.files[0]
  if (file && selectedFriend.value) {
    console.log('发送文件:', file.name)
    
    const result = await FileTransferAPI.sendFile(file, selectedFriend.value.username)
    
    if (result.success) {
      // 添加文件消息到聊天记录
      const fileMessage = {
        id: `file_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        type: 'file',
        content: `发送了文件: ${file.name}`,
        fileName: file.name,
        fileSize: file.size,
        fileType: file.type,
        timestamp: Date.now(),
        senderId: currentUserId.value,
        senderName: getCurrentUsername(),
        senderUsername: getCurrentUsername(),
        receiverId: selectedFriend.value.id,
        receiverUsername: selectedFriend.value.username,
        status: 'delivered'
      }
      
      currentMessages.value.push(fileMessage)
      addMessageToLocalStorage(selectedFriend.value.username, fileMessage)
      updateChatListWithMessage(fileMessage, selectedFriend.value.username)
      scrollToBottom()
      ElMessage.success('文件发送成功')
    } else {
      ElMessage.error('文件发送失败')
    }
  }
  event.target.value = ''
}

const handleImageSelect = (event) => {
  const file = event.target.files[0]
  if (file && selectedFriend.value) {
    emit('file-upload', {
      type: 'image',
      file: file,
      receiverId: selectedFriend.value.id
    })
  }
  event.target.value = ''
}

const makeVoiceCall = () => {
  console.log('发起语音通话')
  ElMessage.info('语音通话功能开发中...')
}

const makeVideoCall = () => {
  console.log('发起视频通话')
  ElMessage.info('视频通话功能开发中...')
}

const showChatInfo = () => {
  console.log('显示聊天信息')
  ElMessage.info('聊天信息功能开发中...')
}

const previewImage = (imageSrc) => {
  console.log('预览图片:', imageSrc)
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatMessageTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit',
    hour12: false 
  })
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  
  const now = new Date()
  const messageTime = new Date(timestamp)
  const diffTime = now - messageTime
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))
  
  if (diffDays === 0) {
    return messageTime.toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: false 
    })
  } else if (diffDays === 1) {
    return '昨天'
  } else if (diffDays < 7) {
    const weekdays = ['日', '一', '二', '三', '四', '五', '六']
    return `周${weekdays[messageTime.getDay()]}`
  } else {
    return messageTime.toLocaleDateString('zh-CN', {
      month: 'numeric',
      day: 'numeric'
    })
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    const container = messagesContainer.value
    if (container) {
      container.scrollTop = container.scrollHeight
    }
  })
}

// 监听器
watch(() => props.activeFriend, (newFriend) => {
  if (newFriend) {
    console.log('接收到从MainPage传入的好友，开始聊天:', newFriend)
    ensureFriendInChatList(newFriend)
    selectFriend(newFriend)
    ElMessage.success(`已打开与 ${newFriend.username} 的对话窗口`)
  }
}, { immediate: true })

watch(() => props.friendsList, (newFriendsList) => {
  console.log('好友列表更新:', newFriendsList?.length || 0, '个好友')
  if (  wsManagerInstance && newFriendsList && newFriendsList.length > 0) {
    if (typeof   wsManagerInstance.setFriendsMap === 'function') {
        wsManagerInstance.setFriendsMap(newFriendsList)
    } else {
      console.warn('WebSocket管理器不支持setFriendsMap方法')
    }
  }
  initializeChatList()
}, { immediate: true, deep: true })

watch(() => props.messages, (newMessages) => {
  console.log('消息列表更新:', newMessages?.length || 0, '条消息')
  initializeChatList()
  
  if (selectedFriend.value) {
    loadChatMessages(selectedFriend.value.id)
  }
}, { immediate: true, deep: true })

watch(() => selectedFriend.value, (newFriend) => {
  console.log('选中好友变化:', newFriend?.username || '无')
  inputMessage.value = ''
  scrollToBottom()
})

// 生命周期
onMounted(async () => {
  currentUserId.value = getCurrentUserId()
  console.log('ChatWindow 初始化，当前用户ID:', currentUserId.value)
  
  // 设置WebSocket监听器
  await setupWebSocketListeners()
  
  initializeChatList()
  
  if (props.activeFriend) {
    console.log('初始化时有activeFriend，自动选中:', props.activeFriend.username)
    ensureFriendInChatList(props.activeFriend)
    selectFriend(props.activeFriend)
  }
})

onUnmounted(() => {
  // 清理WebSocket连接
  if (messageListener) {
      wsManagerInstance.removeMessageListener(messageListener)
  }
  if (connectionListener) {
      wsManagerInstance.removeConnectionListener(connectionListener)
  }
  console.log('WebSocket监听器已清理')
})

// 暴露方法给父组件
defineExpose({
  selectFriend,
  addMessage,
  ensureFriendInChatList
})
</script>

<style scoped>
.chat-window {
  display: flex;
  height: 100vh;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  color: #ffffff;
}

/* 左侧对话列表面板 */
.friends-panel {
  width: 320px;
  min-width: 280px;
  max-width: 400px;
  background: rgba(30, 30, 50, 0.95);
  backdrop-filter: blur(20px);
  border-right: 1px solid rgba(139, 69, 191, 0.2);
  display: flex;
  flex-direction: column;
}

.search-section {
  padding: 20px;
  border-bottom: 1px solid rgba(139, 69, 191, 0.1);
}

.search-input {
  position: relative;
  display: flex;
  align-items: center;
  background: rgba(139, 69, 191, 0.1);
  border: 1px solid rgba(139, 69, 191, 0.3);
  border-radius: 12px;
  padding: 12px 16px;
  transition: all 0.3s ease;
}

.search-input:hover {
  border-color: rgba(139, 69, 191, 0.5);
}

.search-input:focus-within {
  border-color: #8b45bf;
  box-shadow: 0 0 0 2px rgba(139, 69, 191, 0.2);
}

.search-icon {
  color: rgba(255, 255, 255, 0.6);
  margin-right: 12px;
  font-size: 16px;
}

.search-field {
  flex: 1;
  border: none;
  background: transparent;
  outline: none;
  font-size: 14px;
  color: #ffffff;
}

.search-field::placeholder {
  color: rgba(255, 255, 255, 0.5);
}

.clear-icon {
  color: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  transition: color 0.2s ease;
}

.clear-icon:hover {
  color: #ffffff;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(139, 69, 191, 0.1);
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #ffffff;
}

.chat-count {
  color: rgba(255, 255, 255, 0.6);
  font-weight: 400;
  margin-left: 6px;
}

.friends-container {
  flex: 1;
  overflow-y: auto;
}

.friends-list-content {
  padding: 8px 0;
}

.friend-item {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  margin: 2px 8px;
  border-radius: 12px;
}

.friend-item:hover {
  background: rgba(139, 69, 191, 0.15);
}

.friend-item.active {
  background: linear-gradient(135deg, rgba(139, 69, 191, 0.3), rgba(139, 69, 191, 0.2));
  border-left: 3px solid #8b45bf;
}

.friend-avatar {
  position: relative;
  margin-right: 16px;
}

.avatar-img {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  object-fit: cover;
  border: 2px solid rgba(139, 69, 191, 0.3);
}

.status-dot {
  position: absolute;
  bottom: -2px;
  right: -2px;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid rgba(30, 30, 50, 0.95);
}

.status-dot.online { 
  background-color: #00d4aa; 
}

.status-dot.offline { 
  background-color: #90a4ae; 
}

.friend-info {
  flex: 1;
  min-width: 0;
}

.friend-name {
  font-size: 15px;
  font-weight: 500;
  color: #ffffff;
  margin-bottom: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.message-text {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: block;
}

.friend-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
}

.message-time {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.unread-badge {
  background: linear-gradient(135deg, #8b45bf, #a855f7);
  color: #ffffff;
  font-size: 11px;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 12px;
  min-width: 20px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(139, 69, 191, 0.3);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  text-align: center;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 20px;
  color: rgba(255, 255, 255, 0.3);
}

.empty-text {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
}

/* 右侧聊天内容区域 */
.chat-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: rgba(0, 0, 0, 0.2);
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: rgba(30, 30, 50, 0.8);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(139, 69, 191, 0.2);
}

.chat-header .friend-info {
  display: flex;
  align-items: center;
}

.chat-header .friend-avatar {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  object-fit: cover;
  margin-right: 16px;
  border: 2px solid rgba(139, 69, 191, 0.3);
}

.friend-name {
  font-size: 16px;
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 4px;
}

.friend-status {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
}

.chat-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  background: rgba(139, 69, 191, 0.2) !important;
  border: 1px solid rgba(139, 69, 191, 0.3) !important;
  color: #ffffff !important;
  transition: all 0.3s ease !important;
}

.action-btn:hover {
  background: rgba(139, 69, 191, 0.4) !important;
  border-color: rgba(139, 69, 191, 0.5) !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(139, 69, 191, 0.3);
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: transparent;
}

.messages-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 100%;
}

.message-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.message-item.own-message {
  flex-direction: row-reverse;
}

.message-item .avatar-img {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  object-fit: cover;
  border: 2px solid rgba(139, 69, 191, 0.3);
}

.message-content {
  max-width: 60%;
}

.own-message .message-content {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.message-bubble {
  padding: 14px 18px;
  border-radius: 16px;
  margin-bottom: 6px;
  word-wrap: break-word;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.message-item:not(.own-message) .message-bubble {
  background: rgba(255, 255, 255, 0.1);
  color: #ffffff;
}

.own-message .message-bubble {
  background: linear-gradient(135deg, rgba(139, 69, 191, 0.8), rgba(139, 69, 191, 0.6));
  color: #ffffff;
  border: 1px solid rgba(139, 69, 191, 0.3);
}

.text-message {
  line-height: 1.5;
  font-size: 14px;
}

.image-message {
  padding: 0;
  border-radius: 12px;
  overflow: hidden;
}

.message-image {
  max-width: 240px;
  max-height: 240px;
  cursor: pointer;
  display: block;
  border-radius: 12px;
}

.file-message {
  display: flex;
  align-items: center;
  gap: 10px;
}

.file-icon {
  font-size: 18px;
}

.file-name {
  font-weight: 500;
}

.file-size {
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
}

.message-time {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
  margin: 0 12px;
}

.empty-messages,
.no-chat-selected {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  color: rgba(255, 255, 255, 0.6);
}

.welcome-icon {
  font-size: 64px;
  margin-bottom: 24px;
  color: rgba(139, 69, 191, 0.5);
}

.welcome-title {
  font-size: 20px;
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 12px;
}

.welcome-subtitle {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
}

.input-area {
  background: rgba(30, 30, 50, 0.8);
  backdrop-filter: blur(20px);
  border-top: 1px solid rgba(139, 69, 191, 0.2);
}

.input-toolbar {
  display: flex;
  gap: 8px;
  padding: 12px 24px;
  border-bottom: 1px solid rgba(139, 69, 191, 0.1);
}

.toolbar-btn {
  background: transparent !important;
  border: 1px solid rgba(139, 69, 191, 0.3) !important;
  color: rgba(255, 255, 255, 0.8) !important;
  transition: all 0.3s ease !important;
  font-size: 12px !important;
}

.toolbar-btn:hover {
  background: rgba(139, 69, 191, 0.2) !important;
  border-color: rgba(139, 69, 191, 0.5) !important;
  color: #ffffff !important;
  transform: translateY(-1px);
}

.input-container {
  display: flex;
  align-items: flex-end;
  padding: 16px 24px;
  gap: 16px;
}

.message-input {
  flex: 1;
  background: rgba(255, 255, 255, 0.1) !important;
  border: 1px solid rgba(139, 69, 191, 0.3) !important;
  border-radius: 12px !important;
  color: #ffffff !important;
  transition: all 0.3s ease !important;
}

.message-input:hover {
  border-color: rgba(139, 69, 191, 0.5) !important;
}

.message-input:focus {
  border-color: #8b45bf !important;
  box-shadow: 0 0 0 2px rgba(139, 69, 191, 0.2) !important;
  background: rgba(255, 255, 255, 0.15) !important;
}

.message-input :deep(.el-textarea__inner) {
  background: transparent !important;
  border: none !important;
  color: #ffffff !important;
  font-size: 14px;
  line-height: 1.5;
  padding: 12px 16px !important;
}

.message-input :deep(.el-textarea__inner)::placeholder {
  color: rgba(255, 255, 255, 0.5) !important;
}

.send-button {
  background: linear-gradient(135deg, #8b45bf, #a855f7) !important;
  border: none !important;
  color: #ffffff !important;
  border-radius: 12px !important;
  padding: 12px 24px !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  transition: all 0.3s ease !important;
  box-shadow: 0 4px 12px rgba(139, 69, 191, 0.3);
}

.send-button:hover:not(.is-disabled) {
  background: linear-gradient(135deg, #7a40a3, #9333ea) !important;
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(139, 69, 191, 0.4);
}

.send-button.is-disabled {
  background: rgba(255, 255, 255, 0.1) !important;
  color: rgba(255, 255, 255, 0.4) !important;
  cursor: not-allowed !important;
  box-shadow: none;
}

/* 滚动条样式 */
.friends-container::-webkit-scrollbar,
.messages-container::-webkit-scrollbar {
  width: 6px;
}

.friends-container::-webkit-scrollbar-track,
.messages-container::-webkit-scrollbar-track {
  background: rgba(139, 69, 191, 0.1);
  border-radius: 3px;
}

.friends-container::-webkit-scrollbar-thumb,
.messages-container::-webkit-scrollbar-thumb {
  background: rgba(139, 69, 191, 0.4);
  border-radius: 3px;
}

.friends-container::-webkit-scrollbar-thumb:hover,
.messages-container::-webkit-scrollbar-thumb:hover {
  background: rgba(139, 69, 191, 0.6);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .friends-panel {
    width: 280px;
    min-width: 250px;
  }
  
  .message-content {
    max-width: 75%;
  }
  
  .input-container {
    padding: 12px 16px;
  }
  
  .chat-header {
    padding: 12px 16px;
  }
  
  .messages-container {
    padding: 16px;
  }
}

/* Element Plus 组件样式覆盖 */
:deep(.el-button) {
  font-family: inherit;
}

:deep(.el-input__wrapper) {
  background-color: transparent !important;
  box-shadow: none !important;
}

:deep(.el-textarea) {
  --el-input-bg-color: transparent;
  --el-input-border-color: rgba(139, 69, 191, 0.3);
  --el-input-hover-border-color: rgba(139, 69, 191, 0.5);
  --el-input-focus-border-color: #8b45bf;
}
.file-message {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
  max-width: 300px;
  border: 1px solid #e4e7ed;
}

.file-info {
  display: flex;
  align-items: center;
  flex: 1;
}

.file-icon {
  font-size: 24px;
  margin-right: 8px;
  color: #409eff;
}

.file-details {
  display: flex;
  flex-direction: column;
}

.file-name {
  font-weight: 500;
  font-size: 14px;
  color: #303133;
  word-break: break-all;
  margin-bottom: 2px;
}

.file-size {
  font-size: 12px;
  color: #909399;
}

.download-btn {
  margin-left: 12px;
  flex-shrink: 0;
}

/* 确保消息气泡样式正确 */
.message-bubble .file-message {
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
}

.own-message .message-bubble .file-message {
  background: #e6f7ff;
  border: 1px solid #91d5ff;
}
</style>
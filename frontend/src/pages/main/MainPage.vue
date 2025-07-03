<template>
  <div 
    class="main-layout"
    :class="{ 'compact-mode': isCompactMode }"
  >
    <!-- 左侧导航栏 - 固定 -->
    <div class="side-navigation">
      <SideNavigation 
        ref="sideNavigationRef"
        :current-user="currentUser"
        @navigation-change="handleNavigationChange"
      />
    </div>

    <!-- 右侧主内容区域 -->
    <div class="main-content">
      <!-- 聊天界面 -->
      <ChatWindow
        v-if="currentView === 'chat'"
        :active-friend="selectedFriend"
        :friends-list="friendsList"
        :messages="currentMessages"
        @send-message="handleSendMessage"
        @file-upload="handleFileUpload"
      />
      
      <!-- 好友管理界面 -->
      <FriendsManager
        v-else-if="currentView === 'friends'"
        ref="friendsManagerRef"
        @start-chat="handleStartChat"
        @friend-updated="handleFriendUpdated"
      />
      
      <!-- 设置界面 -->
      <div v-else-if="currentView === 'settings'" class="settings-view">
        <div class="settings-content">
          <div class="settings-icon">⚙️</div>
          <div class="settings-title">系统设置</div>
          <div class="settings-subtitle">设置功能开发中...</div>
        </div>
      </div>
      
      <!-- 默认欢迎界面 -->
      <div v-else class="welcome-view">
        <div class="welcome-content">
          <div class="welcome-icon">🎉</div>
          <div class="welcome-title">欢迎使用安全即时通讯系统</div>
          <div class="welcome-subtitle">选择左侧菜单开始使用</div>
          <div class="feature-list">
            <div class="feature-item">
              <span class="feature-icon">🔒</span>
              <span class="feature-text">端到端加密通信</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">🖼️</span>
              <span class="feature-text">图片隐写功能</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">📁</span>
              <span class="feature-text">安全文件传输</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">🌐</span>
              <span class="feature-text">P2P直连通信</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import heartbeatManager from '@/utils/heartbeat.js'
import SideNavigation from '../../components/chat/SideNavigation.vue'
import ChatWindow from '../../components/chat/ChatWindow.vue'
import FriendsManager from '../../components/chat/FriendsManager.vue'
import { 
  getUserInfo,
  isAuthenticated,
  startTokenValidityCheck
} from '@/api/auth.js'
import { 
  getContacts, 
  getOfflineMessages,
  sendOfflineMessage,
  updateConnectionInfo
} from '@/api/chat.js'
import wsManager, { initializeWebSocketManager } from '@/utils/websocket.js'

const router = useRouter()
const friendsManagerRef = ref(null)
const sideNavigationRef = ref(null)

// 当前用户信息
const currentUser = ref({
  id: 'current-user-id',
  username: 'TestUser',
  avatar: '',
  status: 'online'
})

// 当前视图
const currentView = ref('friends')

// 选中的好友（用于聊天）
const selectedFriend = ref(null)

// 好友列表
const friendsList = ref([])

// 当前聊天消息
const currentMessages = ref([])

// 窗口大小响应式状态
const windowSize = ref({
  width: window.innerWidth,
  height: window.innerHeight
})

// 布局响应式配置
const isCompactMode = ref(false)

// 处理导航栏切换
const handleNavigationChange = (navType) => {
  console.log('导航切换:', navType)
  currentView.value = navType
  
  // 如果不是切换到聊天界面，清除选中的好友
  if (navType !== 'chat') {
    selectedFriend.value = null
  }
  
  // 根据导航类型加载不同数据
  switch (navType) {
    case 'chat':
      loadChatData()
      break
    case 'friends':
      console.log('切换到好友管理界面')
      if (friendsManagerRef.value) {
        friendsManagerRef.value.refreshFriends()
      }
      break
    case 'settings':
      loadSettingsData()
      break
    default:
      break
  }
}

// 处理发送消息
const handleSendMessage = async (messageData) => {
  console.log('📤 发送消息:', messageData)
  
  try {
    // 🆕 首先尝试通过WebSocket发送
    const recipient = {
      id: messageData.receiverId,
      username: messageData.receiverUsername || selectedFriend.value?.username
    }
    
    const wsSuccess = wsManager.sendMessage(recipient, messageData.content)
    
    if (wsSuccess) {
      console.log('✅ WebSocket消息发送成功')
      ElMessage.success('消息发送成功')
    } else {
      // 🆕 WebSocket不可用，尝试发送离线消息
      console.log('⚠️ WebSocket不可用，发送离线消息')
      const result = await sendOfflineMessage({
        recipient_username: recipient.username,
        encrypted_content: messageData.content
      })
      
      if (result.success) {
        ElMessage.success('离线消息发送成功')
      } else {
        ElMessage.error('消息发送失败')
      }
    }
  } catch (error) {
    console.error('❌ 发送消息失败:', error)
    ElMessage.error('消息发送失败')
  }
}

// 处理文件上传
const handleFileUpload = (fileData) => {
  console.log('文件上传:', fileData)
  ElMessage.info('文件传输功能开发中...')
}

// 处理开始聊天（从好友管理界面）
const handleStartChat = (friend) => {
  console.log('从好友管理开始聊天:', friend)
  
  // 保存选中的好友
  selectedFriend.value = friend
  
  // 切换到聊天界面
  currentView.value = 'chat'
  
  // 切换左侧导航到聊天
  if (sideNavigationRef.value) {
    sideNavigationRef.value.setActiveNav('chat')
  }
  
  ElMessage.success(`开始与 ${friend.username} 聊天`)
}

// 处理好友更新
const handleFriendUpdated = (friendData) => {
  console.log('好友信息更新:', friendData)
  // 重新加载好友列表
  loadFriendsList()
}

// 加载好友列表
const loadFriendsList = async () => {
  try {
    console.log('加载好友列表')
    const result = await getContacts()
    
    if (result.success) {
      friendsList.value = result.data
        .filter(contact => contact.status === 'accepted')
        .map(contact => ({
          id: contact.friend_id,
          contactId: contact.id,
          username: contact.friend?.username || `User${contact.friend_id}`,
          avatar: contact.friend?.avatar || '',
          is_online: contact.friend?.is_online || false,
          email: contact.friend?.email || '',
          last_seen: contact.friend?.last_seen,
          created_at: contact.created_at
        }))
      
      console.log('好友列表加载完成:', friendsList.value)
    }
  } catch (error) {
    console.error('加载好友列表失败:', error)
    ElMessage.error('加载好友列表失败')
  }
}

// 加载聊天数据
const loadChatData = async () => {
  try {
    console.log('加载聊天数据')
    
    // 确保好友列表已加载
    if (friendsList.value.length === 0) {
      await loadFriendsList()
    }
    
    // 获取离线消息
    const result = await getOfflineMessages()
    if (result.success) {
      currentMessages.value = result.data.map(msg => {
        try {
          return JSON.parse(msg.encrypted_content)
        } catch {
          return {
            id: msg.id,
            content: msg.encrypted_content,
            timestamp: new Date(msg.sent_at).getTime(),
            type: 'text'
          }
        }
      })
    }
  } catch (error) {
    console.error('加载聊天数据失败:', error)
    ElMessage.error('加载聊天数据失败')
  }
}

// 加载设置数据
const loadSettingsData = async () => {
  try {
    console.log('加载设置数据')
    // 设置相关逻辑
  } catch (error) {
    console.error('加载设置数据失败:', error)
    ElMessage.error('加载设置数据失败')
  }
}

// 初始化WebSocket连接
const initWebSocket = async () => {
  try {
    console.log('🚀 开始初始化WebSocket连接...')
    
    // 🆕 首先初始化WebSocket管理器
    const initSuccess = await initializeWebSocketManager()
    if (!initSuccess) {
      console.error('❌ WebSocket管理器初始化失败')
      return false
    }
    
    // 🆕 连接WebSocket
    const connected = wsManager.connect()
    if (!connected) {
      console.error('❌ WebSocket连接失败')
      return false
    }
    
    // 🆕 添加消息处理器
    wsManager.addMessageListener((data) => {
      console.log('📨 收到WebSocket消息:', data)
      handleWebSocketMessage(data)
    })
    
    // 🆕 添加连接状态处理器
    wsManager.addConnectionListener((status, event) => {
      console.log('🔌 WebSocket连接状态变化:', status)
      handleWebSocketConnection(status, event)
    })
    
    console.log('✅ WebSocket初始化完成')
    return true
  } catch (error) {
    console.error('❌ WebSocket初始化失败:', error)
    return false
  }
}

const handleWebSocketMessage = (data) => {
  try {
    switch (data.type) {
      case 'message':
        // 处理聊天消息
        handleChatMessage(data.message, data.sender)
        break
      
      case 'system':
        // 处理系统消息
        console.log('📢 系统消息:', data.content)
        if (data.content.includes('已上线')) {
          // 好友上线，刷新好友列表
          loadFriendsList()
        } else if (data.content.includes('已下线')) {
          // 好友下线，刷新好友列表
          loadFriendsList()
        }
        break
      
      case 'status':
        // 处理状态消息
        console.log('ℹ️ 状态消息:', data.content)
        ElMessage.info(data.content)
        break
      
      case 'error':
        // 处理错误消息
        console.error('❌ WebSocket错误:', data.content)
        ElMessage.error(data.content)
        break
      
      default:
        console.log('📨 未知消息类型:', data)
    }
  } catch (error) {
    console.error('❌ 处理WebSocket消息失败:', error)
  }
}

const handleChatMessage = (message, senderUsername) => {
  try {
    console.log('💬 处理聊天消息:', message)
    
    // 添加到当前消息列表
    currentMessages.value.push({
      id: message.id,
      type: 'text',
      content: message.content,
      timestamp: new Date(message.timestamp).getTime(),
      senderId: message.senderId,
      senderName: message.senderName || senderUsername,
      senderUsername: message.senderUsername || senderUsername,
      receiverId: message.receiverId,
      avatar: message.avatar || '',
      status: message.status || 'delivered'
    })
    
    // 🆕 如果消息是发给当前选中好友的，需要更新聊天窗口
    if (selectedFriend.value && 
        (message.senderUsername === selectedFriend.value.username || 
         message.receiverUsername === selectedFriend.value.username)) {
      // 触发ChatWindow更新
      console.log('📱 更新当前聊天窗口')
    }
    
    // 🆕 显示新消息通知
    if (message.type === 'received') {
      ElMessage.success(`收到来自 ${message.senderName} 的新消息`)
    }
    
  } catch (error) {
    console.error('❌ 处理聊天消息失败:', error)
  }
}

const handleWebSocketConnection = (status, event) => {
  try {
    switch (status) {
      case 'connected':
        console.log('✅ WebSocket已连接')
        currentUser.value.status = 'online'
        ElMessage.success('连接成功，您现在在线')
        break
      
      case 'disconnected':
        console.log('❌ WebSocket已断开')
        currentUser.value.status = 'offline'
        ElMessage.warning('连接已断开，正在尝试重连...')
        break
      
      case 'error':
        console.error('❌ WebSocket连接错误:', event)
        currentUser.value.status = 'error'
        ElMessage.error('连接出现错误')
        break
      
      case 'connecting':
        console.log('🔄 WebSocket连接中...')
        currentUser.value.status = 'connecting'
        break
      
      default:
        console.log('🔌 WebSocket状态:', status)
    }
  } catch (error) {
    console.error('❌ 处理WebSocket连接状态失败:', error)
  }
}

// 更新用户连接信息
const updateUserConnection = async () => {
  try {
    const result = await updateConnectionInfo({ port: 8080 })
    if (result.success) {
      console.log('用户连接信息更新成功')
    }
  } catch (error) {
    console.error('更新连接信息失败:', error)
  }
}

// 处理窗口大小变化
const handleWindowResize = () => {
  windowSize.value = {
    width: window.innerWidth,
    height: window.innerHeight
  }
  
  isCompactMode.value = windowSize.value.width < 1000
}

// 检查认证状态
const checkAuth = () => {
  if (!isAuthenticated()) {
    ElMessage.error('登录已过期，请重新登录')
    router.push('/login')
    return false
  }
  return true
}

// 初始化数据
onMounted(async () => {
  try {
    console.log('🚀 主应用初始化开始')
    
    // 检查认证状态
    if (!checkAuth()) return
    
    // 获取当前用户信息
    const userInfo = getUserInfo()
    if (userInfo) {
      currentUser.value.username = userInfo.username
      currentUser.value.id = userInfo.id
    }
    
    // 监听浏览器窗口大小变化
    window.addEventListener('resize', handleWindowResize)
    handleWindowResize()

    // 启动心跳管理器
    heartbeatManager.start()
    
    // 🆕 更新用户连接信息
    await updateUserConnection()
    
    // 🆕 初始化WebSocket连接（包括好友列表加载）
    const wsSuccess = await initWebSocket()
    if (!wsSuccess) {
      console.warn('⚠️ WebSocket初始化失败，将使用离线模式')
    }
    
    // 🆕 加载好友列表（如果WebSocket初始化失败）
    if (!wsSuccess) {
      await loadFriendsList()
    }
    
    // 🆕 加载离线消息
    await loadOfflineMessages()
    
    ElMessage.success('欢迎使用安全即时通讯系统')
    
  } catch (error) {
    console.error('❌ 应用初始化失败:', error)
    ElMessage.error('应用初始化失败')
  }
})

const loadOfflineMessages = async () => {
  try {
    console.log('📬 加载离线消息...')
    const result = await getOfflineMessages()
    
    if (result.success && result.data.length > 0) {
      console.log(`📬 收到 ${result.data.length} 条离线消息`)
      
      result.data.forEach(msg => {
        const message = {
          id: msg.id,
          type: 'text',
          content: msg.encrypted_content,
          timestamp: new Date(msg.sent_at).getTime(),
          senderId: msg.sender_id,
          senderName: msg.sender?.username || 'Unknown',
          senderUsername: msg.sender?.username || 'Unknown',
          receiverId: msg.receiver_id,
          avatar: '',
          isOfflineMessage: true,
          status: 'delivered'
        }
        
        currentMessages.value.push(message)
      })
      
      ElMessage.success(`收到 ${result.data.length} 条离线消息`)
    }
  } catch (error) {
    console.error('❌ 加载离线消息失败:', error)
  }
}

// 清理监听器
onUnmounted(() => {
  window.removeEventListener('resize', handleWindowResize)
  heartbeatManager.stop()
  
  // 🆕 断开WebSocket连接
  if (wsManager) {
    wsManager.disconnect()
  }
})
</script>

<style scoped>
.main-layout {
  display: flex;
  height: 100vh;
  background-color: #ffffff;
  overflow: hidden;
  transition: all 0.3s ease;
}

.side-navigation {
  flex-shrink: 0;
  z-index: 3;
  transition: all 0.3s ease;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: #ffffff;
  overflow: hidden;
  transition: all 0.3s ease;
}

/* 欢迎界面样式 */
.welcome-view {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
}

.welcome-content {
  text-align: center;
  max-width: 500px;
  padding: 40px;
}

.welcome-icon {
  font-size: 80px;
  margin-bottom: 24px;
  opacity: 0.8;
}

.welcome-title {
  font-size: 32px;
  font-weight: 700;
  color: #333333;
  margin-bottom: 12px;
  background: linear-gradient(135deg, #8b45bf 0%, #6a3093 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.welcome-subtitle {
  font-size: 16px;
  color: #666666;
  margin-bottom: 40px;
}

.feature-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-top: 40px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background-color: #ffffff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.feature-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(139, 69, 191, 0.15);
}

.feature-icon {
  font-size: 24px;
}

.feature-text {
  font-size: 14px;
  font-weight: 500;
  color: #333333;
}

/* 设置界面样式 */
.settings-view {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  background-color: #fafafa;
}

.settings-content {
  text-align: center;
  max-width: 400px;
  padding: 40px;
}

.settings-icon {
  font-size: 64px;
  margin-bottom: 20px;
  opacity: 0.6;
}

.settings-title {
  font-size: 24px;
  font-weight: 600;
  color: #333333;
  margin-bottom: 8px;
}

.settings-subtitle {
  font-size: 14px;
  color: #999999;
}

/* 紧凑模式样式 */
.main-layout.compact-mode .main-content {
  min-width: 600px;
}

/* 窗口拖拽区域 */
.main-layout::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 30px;
  -webkit-app-region: drag;
  z-index: 1000;
  pointer-events: none;
}

/* 小屏幕适配 */
@media (max-width: 1000px) {
  .main-layout.compact-mode {
    flex-direction: row;
  }
  
  .main-content {
    min-width: 500px;
  }
  
  .feature-list {
    grid-template-columns: 1fr;
  }
}

/* 超小屏幕适配 */
@media (max-width: 768px) {
  .welcome-content {
    padding: 20px;
  }
  
  .welcome-title {
    font-size: 24px;
  }
  
  .welcome-icon {
    font-size: 60px;
  }
  
  .feature-item {
    padding: 12px;
  }
  
  .feature-icon {
    font-size: 20px;
  }
  
  .feature-text {
    font-size: 13px;
  }
}

/* 高度适配 */
@media (max-height: 600px) {
  .main-layout {
    min-height: 600px;
  }
  
  .welcome-content {
    padding: 20px;
  }
  
  .welcome-icon {
    font-size: 50px;
    margin-bottom: 16px;
  }
  
  .welcome-title {
    font-size: 24px;
    margin-bottom: 8px;
  }
  
  .feature-list {
    margin-top: 20px;
  }
}

/* 全局样式重置 */
* {
  box-sizing: border-box;
}

/* Electron专用样式 */
.electron-app {
  -webkit-user-select: none;
  user-select: none;
}

.electron-app input,
.electron-app textarea {
  -webkit-user-select: auto;
  user-select: auto;
}

/* 防止拖拽 */
img {
  -webkit-user-drag: none;
  user-drag: none;
}

/* 优化性能 */
.main-layout * {
  will-change: auto;
}

.side-navigation,
.main-content {
  transform: translateZ(0);
  backface-visibility: hidden;
}

/* 滚动条样式 */
:deep(.el-scrollbar__bar) {
  opacity: 0.3;
  transition: opacity 0.3s ease;
}

:deep(.el-scrollbar__bar:hover) {
  opacity: 0.6;
}

:deep(.el-scrollbar__thumb) {
  background-color: #c1c1c1;
  border-radius: 4px;
}
</style>
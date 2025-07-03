<template>
  <div class="friends-panel">
    <div class="panel-header">
      <h2 class="panel-title">好友列表</h2>
      <el-button 
        type="primary" 
        :icon="Plus" 
        @click="showAddFriendDialog"
        size="small"
        round
        class="add-friend-btn"
      >
        添加好友
      </el-button>
    </div>

    <div class="search-section">
      <div class="search-input">
        <el-icon class="search-icon">
          <Search />
        </el-icon>
        <input
          v-model="searchText"
          type="text"
          placeholder="搜索好友..."
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

    <div v-if="pendingRequests.length > 0" class="pending-requests">
      <div class="request-header">
        <el-icon class="request-icon">
          <Bell />
        </el-icon>
        <span class="request-title">好友请求 ({{ pendingRequests.length }})</span>
      </div>
      <div class="request-list">
        <div
          v-for="request in pendingRequests"
          :key="request.id"
          class="request-item"
        >
          <div class="request-avatar">
            <img 
              :src="request.user?.avatar || defaultAvatar"
              :alt="request.user?.username"
              class="avatar-img"
            />
          </div>
          <div class="request-info">
            <div class="request-name">{{ request.user?.username }}</div>
            <div class="request-time">{{ formatTime(request.created_at) }}</div>
          </div>
          <div class="request-actions">
            <el-button 
              type="success" 
              size="small"
              @click="handleAcceptFriendRequest(request)"
              :loading="request.processing"
            >
              接受
            </el-button>
            <el-button 
              type="danger" 
              size="small"
              @click="handleRejectFriendRequest(request)"
              :loading="request.processing"
            >
              拒绝
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <div class="friends-stats">
      <span class="stats-text">
        在线: {{ onlineFriendsCount }} / {{ totalFriendsCount }}
      </span>
    </div>

    <div class="friends-container">
      <el-scrollbar class="scrollbar">
        <div class="friends-list-content">
          <div v-if="onlineFriends.length > 0" class="friends-group">
            <div class="group-header">
              <el-icon class="group-icon">
                <UserFilled />
              </el-icon>
              <span class="group-title">在线好友</span>
              <span class="group-count">({{ onlineFriends.length }})</span>
            </div>
            
            <div
              v-for="friend in onlineFriends"
              :key="friend.id"
              class="friend-item online"
              @dblclick="startChatDirectly(friend)"
              @click="selectFriend(friend)"
              :class="{ 'selected': selectedFriendId === friend.id }"
            >
              <div class="friend-avatar">
                <img 
                  :src="friend.avatar || defaultAvatar"
                  :alt="friend.username"
                  class="avatar-img"
                />
                <div class="status-dot online"></div>
              </div>

              <div class="friend-info">
                <div class="friend-name">{{ friend.username }}</div>
                <div class="friend-status">在线</div>
              </div>

              <div class="friend-actions">
                <el-dropdown 
                  @command="handleFriendAction"
                  trigger="click"
                  placement="bottom-end"
                >
                  <el-button 
                    :icon="MoreFilled"
                    circle
                    size="small"
                    class="action-btn more-btn"
                    @click.stop
                  />
                  <template #dropdown>
                    <el-dropdown-menu class="friend-menu">
                      <el-dropdown-item 
                        :command="{action: 'chat', friend}"
                        :icon="ChatDotRound"
                      >
                        发起聊天
                      </el-dropdown-item>
                      <el-dropdown-item 
                        :command="{action: 'profile', friend}"
                        :icon="User"
                      >
                        查看资料
                      </el-dropdown-item>
                      <el-dropdown-item 
                        :command="{action: 'delete', friend}"
                        :icon="Delete"
                        class="danger-item"
                        divided
                      >
                        删除好友
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>
          </div>

          <div v-if="offlineFriends.length > 0" class="friends-group">
            <div class="group-header">
              <el-icon class="group-icon">
                <User />
              </el-icon>
              <span class="group-title">离线好友</span>
              <span class="group-count">({{ offlineFriends.length }})</span>
            </div>
            
            <div
              v-for="friend in offlineFriends"
              :key="friend.id"
              class="friend-item offline"
              @dblclick="startChatDirectly(friend)"
              @click="selectFriend(friend)"
              :class="{ 'selected': selectedFriendId === friend.id }"
            >
              <div class="friend-avatar">
                <img 
                  :src="friend.avatar || defaultAvatar"
                  :alt="friend.username"
                  class="avatar-img"
                />
                <div class="status-dot offline"></div>
              </div>

              <div class="friend-info">
                <div class="friend-name">{{ friend.username }}</div>
                <div class="friend-status">{{ formatLastSeen(friend.last_seen) }}</div>
              </div>

              <div class="friend-actions">
                <el-dropdown 
                  @command="handleFriendAction"
                  trigger="click"
                  placement="bottom-end"
                >
                  <el-button 
                    :icon="MoreFilled"
                    circle
                    size="small"
                    class="action-btn more-btn"
                    @click.stop
                  />
                  <template #dropdown>
                    <el-dropdown-menu class="friend-menu">
                      <el-dropdown-item 
                        :command="{action: 'chat', friend}"
                        :icon="ChatDotRound"
                      >
                        发起聊天
                      </el-dropdown-item>
                      <el-dropdown-item 
                        :command="{action: 'profile', friend}"
                        :icon="User"
                      >
                        查看资料
                      </el-dropdown-item>
                      <el-dropdown-item 
                        :command="{action: 'delete', friend}"
                        :icon="Delete"
                        class="danger-item"
                        divided
                      >
                        删除好友
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>
          </div>

          <div v-if="filteredFriends.length === 0 && pendingRequests.length === 0" class="empty-state">
            <el-icon class="empty-icon">
              <Users />
            </el-icon>
            <div class="empty-text">
              {{ searchText ? '未找到相关好友' : '暂无好友' }}
            </div>
            <el-button 
              v-if="!searchText"
              type="primary"
              :icon="Plus"
              @click="showAddFriendDialog"
              class="empty-action"
              round
            >
              添加第一个好友
            </el-button>
          </div>
        </div>
      </el-scrollbar>
    </div>

    <el-dialog
      v-model="showAddDialog"
      title="添加好友"
      width="450px"
      class="add-friend-dialog"
      align-center
    >
      <el-form 
        :model="addFriendForm" 
        label-width="80px"
        class="add-friend-form"
      >
        <el-form-item label="用户名" required>
          <el-input
            v-model="addFriendForm.username"
            placeholder="请输入用户名进行搜索"
            :prefix-icon="User"
            clearable
            @input="handleSearchInput"
            @keyup.enter="handleSearchSubmit"
          />
        </el-form-item>
        
        <div v-if="isSearching" class="search-loading">
          <el-icon class="is-loading">
            <Loading />
          </el-icon>
          <span>搜索中...</span>
        </div>
        
        <div v-if="searchResults.length > 0" class="search-results">
          <div class="search-results-header">
            <span>搜索结果 ({{ searchResults.length }}):</span>
            <small>点击选择要添加的用户</small>
          </div>
          <div class="search-results-list">
            <div
              v-for="user in searchResults"
              :key="user.id"
              class="search-result-item"
              :class="{ 'selected': selectedUser?.id === user.id }"
              @click="selectUser(user)"
            >
              <div class="user-info">
                <div class="user-name">{{ user.username }}</div>
                <div class="user-status" :class="{ 'online': user.is_online }">
                  {{ user.is_online ? '在线' : '离线' }}
                </div>
              </div>
              <el-icon v-if="selectedUser?.id === user.id" class="check-icon">
                <Check />
              </el-icon>
            </div>
          </div>
        </div>
        
        <div v-else-if="hasSearched && addFriendForm.username.trim() && !isSearching" class="no-results">
          <el-icon><Search /></el-icon>
          <span>未找到用户 "{{ addFriendForm.username }}"</span>
          <small>请检查用户名是否正确</small>
        </div>
        
        <div v-if="!hasSearched && addFriendForm.username.trim().length > 0 && addFriendForm.username.trim().length < 2" class="search-hint">
          <el-icon><InfoFilled /></el-icon>
          <span>请输入至少2个字符进行搜索</span>
        </div>
        
        <div v-if="searchResults.length > 0 && !selectedUser" class="selection-hint">
          <el-icon><InfoFilled /></el-icon>
          <span>请点击上方搜索结果中的用户来选择</span>
        </div>
        
        <div class="search-tip">
          <el-icon><InfoFilled /></el-icon>
          <span>可以向任何已注册用户发送好友请求</span>
        </div>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="closeAddFriendDialog" class="cancel-btn">
            取消
          </el-button>
          <el-button 
            type="primary"
            @click="addFriend"
            :disabled="!selectedUser"
            :loading="addingFriend"
            class="confirm-btn"
          >
            {{ !selectedUser ? '请先选择用户' : '发送请求' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Plus,
  Search, 
  Close, 
  UserFilled,
  User,
  Users,
  ChatDotRound,
  MoreFilled,
  Delete,
  Bell,
  InfoFilled,
  Check,
  Loading
} from '@element-plus/icons-vue'
import { 
  getContacts, 
  getPendingRequests,
  addContact, 
  searchUsers,
  acceptFriendRequest,
  deleteFriendOrRequest,
  updateConnectionInfo,
  getCurrentUserId
} from '@/api/friend.js'
import defaultAvatarImg from '/src/assets/image.png'

const emit = defineEmits(['start-chat', 'friend-updated'])

// 基础数据
const searchText = ref('')
const showAddDialog = ref(false)
const addingFriend = ref(false)
const isSearching = ref(false)
const addFriendForm = ref({
  username: ''
})

const allContacts = ref([])
const pendingRequests = ref([])
const defaultAvatar = defaultAvatarImg
const heartbeatInterval = ref(null)
const selectedFriendId = ref(null) // 当前选中的好友ID

const searchResults = ref([])
const selectedUser = ref(null)
const hasSearched = ref(false)
const searchTimeout = ref(null)

// 计算属性
const acceptedFriends = computed(() => {
  return allContacts.value
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
})

const filteredFriends = computed(() => {
  if (!searchText.value.trim()) {
    return acceptedFriends.value
  }
  
  return acceptedFriends.value.filter(friend => 
    friend.username.toLowerCase().includes(searchText.value.toLowerCase())
  )
})

const onlineFriends = computed(() => {
  return filteredFriends.value.filter(friend => friend.is_online)
})

const offlineFriends = computed(() => {
  return filteredFriends.value.filter(friend => !friend.is_online)
})

const onlineFriendsCount = computed(() => onlineFriends.value.length)
const totalFriendsCount = computed(() => filteredFriends.value.length)

// 选中好友（单击）
const selectFriend = (friend) => {
  selectedFriendId.value = friend.id
  console.log('选中好友:', friend)
}

// 直接开始聊天（双击）- 删除了对话框
const startChatDirectly = (friend) => {
  console.log('💬 双击直接开始聊天:', friend)
  selectedFriendId.value = friend.id
  startChat(friend)
}

// 搜索处理
const handleSearch = () => {
  // 搜索逻辑已在 computed 中处理
}

const clearSearch = () => {
  searchText.value = ''
}

// 开始聊天
const startChat = (friend) => {
  console.log('💬 开始与好友聊天:', friend)
  
  // 确保传递完整的好友信息
  const chatFriend = {
    id: friend.id,
    username: friend.username,
    avatar: friend.avatar,
    is_online: friend.is_online,
    email: friend.email
  }
  
  emit('start-chat', chatFriend)
  ElMessage.success(`正在打开与 ${friend.username} 的对话窗口`)
}

// 好友操作处理
const handleFriendAction = ({ action, friend }) => {
  switch (action) {
    case 'chat':
      selectedFriendId.value = friend.id
      startChat(friend)
      break
    case 'profile':
      showFriendProfile(friend)
      break
    case 'delete':
      deleteFriendAction(friend)
      break
  }
}

const showFriendProfile = (friend) => {
  ElMessage.info('查看好友资料功能开发中...')
}

const deleteFriendAction = async (friend) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除好友 ${friend.username} 吗？删除后需要重新添加才能恢复好友关系。`,
      '删除好友',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const result = await deleteFriendOrRequest(friend.id)
    
    if (result.success) {
      ElMessage.success(`已删除好友 ${friend.username}`)
      // 如果删除的是当前选中的好友，清除选中状态
      if (selectedFriendId.value === friend.id) {
        selectedFriendId.value = null
      }
      loadFriends()
      emit('friend-updated', friend)
    } else {
      ElMessage.error(result.message)
    }
    
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除好友失败:', error)
      ElMessage.error('删除好友失败')
    }
  }
}

// 添加好友相关逻辑
const handleSearchInput = () => {
  selectedUser.value = null
  
  if (searchTimeout.value) {
    clearTimeout(searchTimeout.value)
  }
  
  const query = addFriendForm.value.username.trim()
  if (query.length >= 2) {
    isSearching.value = true
    searchTimeout.value = setTimeout(() => {
      performSearch(query)
    }, 300)
  } else {
    searchResults.value = []
    hasSearched.value = false
    isSearching.value = false
  }
}

const handleSearchSubmit = () => {
  const query = addFriendForm.value.username.trim()
  if (query.length >= 2) {
    isSearching.value = true
    performSearch(query)
  } else {
    ElMessage.warning('请输入至少2个字符进行搜索')
  }
}

const performSearch = async (query) => {
  try {
    console.log('🔍 开始搜索用户:', query)
    
    hasSearched.value = true
    const result = await searchUsers(query)
    
    console.log('🔍 搜索原始结果:', result)
    
    if (result.success) {
      const currentUserId = getCurrentUserId()
      console.log('👤 当前用户ID:', currentUserId)
      
      const friendIds = new Set([
        ...acceptedFriends.value.map(f => f.id),
        ...pendingRequests.value.map(r => r.user?.id).filter(Boolean)
      ])
      
      console.log('👥 已有好友和待处理请求ID:', Array.from(friendIds))
      
      const filteredResults = result.data.filter(user => {
        const isCurrentUser = user.id === currentUserId
        const isAlreadyFriend = friendIds.has(user.id)
        
        console.log(`🔍 用户 ${user.username}(ID:${user.id}):`, {
          isCurrentUser,
          isAlreadyFriend,
          willShow: !isCurrentUser && !isAlreadyFriend
        })
        
        return !isCurrentUser && !isAlreadyFriend
      })
      
      searchResults.value = filteredResults
      console.log('✅ 最终搜索结果:', filteredResults)
      
      if (filteredResults.length === 0) {
        if (result.data.length > 0) {
          ElMessage.info('找到的用户已经是您的好友或已发送请求')
        }
      }
    } else {
      searchResults.value = []
      console.error('🔍 搜索失败:', result.message)
      if (result.message !== '搜索用户失败') {
        ElMessage.error(result.message)
      }
    }
  } catch (error) {
    console.error('🔍 搜索用户失败:', error)
    searchResults.value = []
    ElMessage.error('搜索失败，请重试')
  } finally {
    isSearching.value = false
  }
}

const selectUser = (user) => {
  console.log('👆 选择用户:', user)
  selectedUser.value = user
  addFriendForm.value.username = user.username
  ElMessage.success(`已选择用户: ${user.username}`)
}

const showAddFriendDialog = () => {
  console.log('📱 打开添加好友对话框')
  console.log('👤 当前用户ID:', getCurrentUserId())
  
  showAddDialog.value = true
  addFriendForm.value = { username: '' }
  searchResults.value = []
  selectedUser.value = null
  hasSearched.value = false
  isSearching.value = false
}

const closeAddFriendDialog = () => {
  showAddDialog.value = false
}
const addFriend = async () => {
  if (!selectedUser.value) {
    ElMessage.warning('请先选择要添加的用户')
    return
  }
  
  console.log('➕ 发送好友请求给:', selectedUser.value)
  console.log('👤 当前用户ID:', getCurrentUserId())
  console.log('👥 目标用户ID:', selectedUser.value.id)
  
  // 前端预检查
  if (getCurrentUserId() === selectedUser.value.id) {
    ElMessage.warning('不能添加自己为好友')
    return
  }
  
  const existingFriend = acceptedFriends.value.find(friend => friend.id === selectedUser.value.id)
  const existingRequest = pendingRequests.value.find(request => request.user?.id === selectedUser.value.id)
  
  if (existingFriend) {
    ElMessage.warning(`${selectedUser.value.username} 已经是您的好友`)
    return
  }
  
  if (existingRequest) {
    ElMessage.warning(`已向 ${selectedUser.value.username} 发送过好友请求`)
    return
  }
  
  addingFriend.value = true
  
  try {
    const result = await addContact({
      friend_id: selectedUser.value.id
    })
    
    if (result.success) {
      const statusText = selectedUser.value.is_online ? '(在线)' : '(离线)'
      ElMessage.success(`已向 ${selectedUser.value.username} ${statusText} 发送好友请求`)
      closeAddFriendDialog()
      
      // 利用搜索到的用户信息构建好友对象
      const newFriendInfo = {
        id: selectedUser.value.id,
        username: selectedUser.value.username,
        is_online: selectedUser.value.is_online,
        avatar: selectedUser.value.avatar || '',
        email: selectedUser.value.email || ''
      }
      
      // 即使API返回数据不完整，我们也有完整的用户信息
      emit('friend-updated', newFriendInfo)
      loadFriends()
    } else {
      // 详细分析错误原因
      const errorMsg = result.message
      if (errorMsg.includes('不能添加自己')) {
        ElMessage.warning('不能添加自己为好友')
      } else if (errorMsg.includes('请求已存在')) {
        ElMessage.warning(`已向 ${selectedUser.value.username} 发送过好友请求`)
      } else if (errorMsg.includes('用户不存在')) {
        ElMessage.error(`用户 ${selectedUser.value.username} 不存在`)
      } else {
        ElMessage.error(`添加好友失败: ${errorMsg}`)
      }
    }
    
  } catch (error) {
    console.error('添加好友失败:', error)
    ElMessage.error('网络错误，请重试')
  } finally {
    addingFriend.value = false
  }
}

// 处理好友请求
const handleAcceptFriendRequest = async (request) => {
  request.processing = true
  
  try {
    console.log('✅ 接受好友请求，请求数据:', request)
    console.log('✅ 发起者用户信息:', request.user)
    
    const result = await acceptFriendRequest(request.user_id)
    
    if (result.success) {
      ElMessage.success(`已接受 ${request.user?.username} 的好友请求`)
      
      // 重新加载数据以确保同步
      await Promise.all([loadFriends(), loadPendingRequests()])
      
      // 传递更完整的好友信息
      const friendInfo = {
        id: request.user_id,
        username: request.user?.username,
        email: request.user?.email,
        avatar: request.user?.avatar,
        is_online: request.user?.is_online || false
      }
      
      emit('friend-updated', friendInfo)
    } else {
      ElMessage.error(result.message)
    }
    
  } catch (error) {
    console.error('接受好友请求失败:', error)
    ElMessage.error('接受好友请求失败')
  } finally {
    request.processing = false
  }
}

const handleRejectFriendRequest = async (request) => {
  request.processing = true
  
  try {
    const result = await deleteFriendOrRequest(request.user_id)
    
    if (result.success) {
      ElMessage.success(`已拒绝 ${request.user?.username} 的好友请求`)
      loadPendingRequests()
    } else {
      ElMessage.error(result.message)
    }
    
  } catch (error) {
    console.error('拒绝好友请求失败:', error)
    ElMessage.error('拒绝好友请求失败')
  } finally {
    request.processing = false
  }
}

// 数据加载
const loadFriends = async () => {
  try {
    const result = await getContacts()
    
    if (result.success) {
      allContacts.value = result.data
      console.log('👥 加载好友列表:', result.data)
    } else {
      console.error('加载好友列表失败:', result.message)
      ElMessage.error('加载好友列表失败')
    }
    
  } catch (error) {
    console.error('加载好友列表失败:', error)
    ElMessage.error('加载好友列表失败')
  }
}

const loadPendingRequests = async () => {
  try {
    const result = await getPendingRequests()
    
    if (result.success) {
      pendingRequests.value = result.data.map(request => ({
        ...request,
        processing: false
      }))
      console.log('📋 加载待处理请求:', result.data)
    } else {
      console.error('加载待处理请求失败:', result.message)
    }
    
  } catch (error) {
    console.error('加载待处理请求失败:', error)
  }
}

// 心跳和生命周期
const startHeartbeat = () => {
  heartbeatInterval.value = setInterval(async () => {
    try {
      await updateConnectionInfo(0)
      loadFriends()
    } catch (error) {
      console.error('心跳失败:', error)
    }
  }, 30000)
}

const stopHeartbeat = () => {
  if (heartbeatInterval.value) {
    clearInterval(heartbeatInterval.value)
    heartbeatInterval.value = null
  }
}

// 时间格式化
const formatTime = (timestamp) => {
  if (!timestamp) return ''
  
  const date = new Date(timestamp)
  const now = new Date()
  const diffTime = now - date
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))
  
  if (diffDays === 0) {
    return date.toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: false 
    })
  } else if (diffDays === 1) {
    return '昨天'
  } else if (diffDays < 7) {
    const weekdays = ['日', '一', '二', '三', '四', '五', '六']
    return `周${weekdays[date.getDay()]}`
  } else {
    return date.toLocaleDateString('zh-CN', {
      month: 'numeric',
      day: 'numeric'
    })
  }
}

const formatLastSeen = (lastSeen) => {
  if (!lastSeen) return '离线'
  
  const date = new Date(lastSeen)
  const now = new Date()
  const diffTime = now - date
  const diffMinutes = Math.floor(diffTime / (1000 * 60))
  const diffHours = Math.floor(diffTime / (1000 * 60 * 60))
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))
  
  if (diffMinutes < 5) {
    return '刚刚离线'
  } else if (diffMinutes < 60) {
    return `${diffMinutes}分钟前在线`
  } else if (diffHours < 24) {
    return `${diffHours}小时前在线`
  } else if (diffDays < 7) {
    return `${diffDays}天前在线`
  } else {
    return '很久未上线'
  }
}

// 生命周期钩子
onMounted(() => {
  loadFriends()
  loadPendingRequests()
  startHeartbeat()
  
  const refreshInterval = setInterval(() => {
    loadPendingRequests()
  }, 60000)
  
  onUnmounted(() => {
    clearInterval(refreshInterval)
    stopHeartbeat()
  })
})

onUnmounted(() => {
  if (searchTimeout.value) {
    clearTimeout(searchTimeout.value)
  }
})

// 暴露方法
defineExpose({
  refreshFriends: () => {
    loadFriends()
    loadPendingRequests()
  }
})
</script>

<style lang="scss" scoped>
.friends-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #1a1a1a;
  color: #ffffff;
  padding: 16px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.panel-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
  color: #ffffff;
}

.add-friend-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
  }
}

.search-section {
  margin-bottom: 16px;
}

.search-input {
  position: relative;
  display: flex;
  align-items: center;
  background: #2d2d2d;
  border-radius: 12px;
  padding: 0 12px;
  transition: all 0.3s ease;

  &:focus-within {
    background: #3d3d3d;
    box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.3);
  }
}

.search-icon {
  color: #888;
  margin-right: 8px;
}

.search-field {
  flex: 1;
  border: none;
  background: transparent;
  padding: 12px 0;
  color: #ffffff;
  font-size: 14px;

  &::placeholder {
    color: #888;
  }

  &:focus {
    outline: none;
  }
}

.clear-icon {
  color: #888;
  cursor: pointer;
  margin-left: 8px;
  transition: color 0.3s ease;

  &:hover {
    color: #ffffff;
  }
}

.pending-requests {
  background: #2d2d2d;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
  border-left: 4px solid #764ba2;
}

.request-header {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.request-icon {
  color: #764ba2;
  margin-right: 8px;
}

.request-title {
  font-weight: 600;
  color: #ffffff;
}

.request-item {
  display: flex;
  align-items: center;
  padding: 12px;
  background: #3d3d3d;
  border-radius: 8px;
  margin-bottom: 8px;
  transition: all 0.3s ease;

  &:hover {
    background: #4d4d4d;
  }

  &:last-child {
    margin-bottom: 0;
  }
}

.request-avatar {
  position: relative;
  margin-right: 12px;
}

.avatar-img {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
}

.request-info {
  flex: 1;
}

.request-name {
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 4px;
}

.request-time {
  font-size: 12px;
  color: #888;
}

.request-actions {
  display: flex;
  gap: 8px;
}

.friends-stats {
  padding: 12px 16px;
  background: #2d2d2d;
  border-radius: 8px;
  margin-bottom: 16px;
}

.stats-text {
  font-size: 14px;
  color: #888;
}

.friends-container {
  flex: 1;
  overflow: hidden;
}

.friends-list-content {
  padding-right: 8px;
}

.friends-group {
  margin-bottom: 24px;

  &:last-child {
    margin-bottom: 0;
  }
}

.group-header {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: rgba(102, 126, 234, 0.1);
  border-radius: 8px;
}

.group-icon {
  color: #667eea;
  margin-right: 8px;
}

.group-title {
  font-weight: 600;
  color: #ffffff;
  margin-right: 8px;
}

.group-count {
  color: #888;
  font-size: 14px;
}

.friend-item {
  display: flex;
  align-items: center;
  padding: 12px;
  background: #2d2d2d;
  border-radius: 12px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;

  &:hover {
    background: #3d3d3d;
    transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  }

  &:last-child {
    margin-bottom: 0;
  }

  &.online {
    border-left: 3px solid #4CAF50;
  }

  &.offline {
    border-left: 3px solid #888;
  }
}

.friend-avatar {
  position: relative;
  margin-right: 12px;
}

.status-dot {
  position: absolute;
  bottom: 2px;
  right: 2px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid #1a1a1a;

  &.online {
    background: #4CAF50;
  }

  &.offline {
    background: #888;
  }
}

.friend-info {
  flex: 1;
}

.friend-name {
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 4px;
  font-size: 14px;
}

.friend-status {
  font-size: 12px;
  color: #888;
}

.friend-actions {
  opacity: 0;
  transition: opacity 0.3s ease;
}

.friend-item:hover .friend-actions {
  opacity: 1;
}

.action-btn {
  background: transparent;
  border: 1px solid #555;
  color: #888;
  transition: all 0.3s ease;

  &:hover {
    background: #667eea;
    border-color: #667eea;
    color: white;
  }
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #888;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  color: #555;
}

.empty-text {
  font-size: 16px;
  margin-bottom: 20px;
}

.empty-action {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
}

.add-friend-dialog {
  :deep(.el-dialog) {
    background: #2d2d2d;
    color: #ffffff;
  }

  :deep(.el-dialog__title) {
    color: #ffffff;
  }
}

.add-friend-form {
  :deep(.el-form-item__label) {
    color: #ffffff;
  }
}

.search-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: rgba(102, 126, 234, 0.1);
  border-radius: 8px;
  margin-top: 16px;
  color: #667eea;
}

.search-results {
  margin-top: 16px;
  border: 1px solid #444;
  border-radius: 8px;
  overflow: hidden;
}

.search-results-header {
  padding: 12px 16px;
  background: #3d3d3d;
  font-weight: 600;
  color: #ffffff;
  display: flex;
  justify-content: space-between;
  align-items: center;

  small {
    color: #888;
    font-weight: normal;
  }
}

.search-results-list {
  max-height: 200px;
  overflow-y: auto;
}

.search-result-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #2d2d2d;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    background: #3d3d3d;
  }

  &.selected {
    background: rgba(102, 126, 234, 0.2);
    border-left: 3px solid #667eea;
  }

  &:not(:last-child) {
    border-bottom: 1px solid #444;
  }
}

.user-info {
  flex: 1;
}

.user-name {
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 4px;
}

.user-status {
  font-size: 12px;
  color: #888;

  &.online {
    color: #4CAF50;
  }
}

.check-icon {
  color: #667eea;
  font-size: 18px;
}

.no-results {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
  color: #888;
  gap: 8px;

  small {
    color: #666;
  }
}

.search-hint, .selection-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  padding: 12px;
  background: rgba(255, 193, 7, 0.1);
  border-radius: 8px;
  font-size: 14px;
  color: #ffc107;
}

.search-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  padding: 12px;
  background: rgba(102, 126, 234, 0.1);
  border-radius: 8px;
  font-size: 14px;
  color: #888;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.cancel-btn {
  background: transparent;
  border: 1px solid #555;
  color: #888;

  &:hover {
    background: #555;
    color: white;
  }
}

.confirm-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;

  &:hover {
    opacity: 0.9;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    background: #555;
  }
}

:deep(.friend-menu) {
  background: #2d2d2d;
  border: 1px solid #444;

  .el-dropdown-menu__item {
    color: #ffffff;

    &:hover {
      background: #3d3d3d;
      color: #667eea;
    }

    &.danger-item {
      color: #ff6b6b;

      &:hover {
        background: rgba(255, 107, 107, 0.1);
        color: #ff6b6b;
      }
    }
  }
}

:deep(.el-scrollbar__thumb) {
  background: #555;
  border-radius: 4px;
}
</style>
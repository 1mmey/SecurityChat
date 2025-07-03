<template>
  <div class="side-navigation">
    <!-- 用户头像区域 -->
    <div class="user-avatar-section">
      <div class="user-avatar" @click="showUserMenu">
        <img 
          :src="currentUser.avatar || defaultAvatar" 
          :alt="currentUser.username"
          class="avatar-img"
        />
        <div 
          class="status-indicator"
          :class="currentUser.status"
        ></div>
      </div>
      <div class="user-info">
        <div class="username">{{ currentUser.username || 'User' }}</div>
        <div class="user-status">{{ getStatusText(currentUser.status) }}</div>
      </div>
    </div>

    <!-- 导航菜单 -->
    <div class="nav-menu">
      <div 
        v-for="item in navItems" 
        :key="item.id"
        class="nav-item"
        :class="{ active: activeNav === item.id }"
        @click="handleNavClick(item)"
      >
        <div class="nav-icon">{{ item.icon }}</div>
        <div class="nav-label">{{ item.label }}</div>
      </div>
    </div>

    <!-- 底部功能区 -->
    <div class="bottom-actions">
      <div 
        class="nav-item" 
        @click="showSettings"
      >
        <div class="nav-icon">SETTINGS</div>
        <div class="nav-label">设置</div>
      </div>
      
      <div 
        class="nav-item logout-btn" 
        @click="handleLogout"
      >
        <div class="nav-icon">LOGOUT</div>
        <div class="nav-label">退出</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { logout } from '@/api/auth.js'
import defaultAvatarImg from '/src/assets/image.png'

const router = useRouter()
const emit = defineEmits(['navigation-change'])

const props = defineProps({
  currentUser: {
    type: Object,
    default: () => ({})
  }
})

// 当前激活的导航
const activeNav = ref('friends') // 默认激活好友

// 默认头像
const defaultAvatar = defaultAvatarImg

// 导航菜单项 - 只保留聊天和好友
const navItems = ref([
  {
    id: 'friends',
    label: '好友',
    icon: 'FRIENDS'
  },
  {
    id: 'chat',
    label: '聊天',
    icon: 'CHAT'
  }
])

// 获取状态文本
const getStatusText = (status) => {
  const statusMap = {
    online: '在线',
    busy: '忙碌',
    away: '离开',
    offline: '离线'
  }
  return statusMap[status] || '在线'
}

// 处理导航点击
const handleNavClick = (item) => {
  console.log('侧边导航点击:', item)
  
  activeNav.value = item.id
  emit('navigation-change', item.id)
}

// 显示用户菜单
const showUserMenu = () => {
  console.log('显示用户菜单')
  ElMessage.info('用户状态切换功能开发中...')
}

// 显示设置
const showSettings = () => {
  console.log('打开设置')
  activeNav.value = 'settings'
  emit('navigation-change', 'settings')
}

// 退出登录
const handleLogout = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要退出登录吗？',
      '退出确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    try {
      // 调用登出API
      await logout()
    } catch (error) {
      console.error('登出API调用失败:', error)
    }
    
    // 清除登录状态
    localStorage.removeItem('access_token')
    localStorage.removeItem('userInfo')
    
    ElMessage.success('退出成功')
    router.push('/login')
  } catch (error) {
    // 用户取消退出
    if (error !== 'cancel') {
      console.error('退出登录失败:', error)
    }
  }
}

// 监听外部激活状态变化（如果需要）
watch(() => props.currentUser, (newUser) => {
  console.log('用户信息更新:', newUser)
}, { deep: true })

// 暴露方法给父组件
defineExpose({
  setActiveNav: (navId) => {
    activeNav.value = navId
  },
  getActiveNav: () => {
    return activeNav.value
  }
})
</script>

<style scoped>
.side-navigation {
  width: 200px;
  min-width: 200px;
  background: linear-gradient(135deg, #2d1b3d 0%, #1a0f26 50%, #0f0618 100%);
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 20px 0;
  position: relative;
  box-shadow: 2px 0 10px rgba(0, 0, 0, 0.3);
}

.user-avatar-section {
  padding: 0 20px;
  margin-bottom: 30px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  position: relative;
  width: 50px;
  height: 50px;
  cursor: pointer;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.user-avatar:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 15px rgba(139, 69, 191, 0.4);
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 12px;
}

.status-indicator {
  position: absolute;
  bottom: -2px;
  right: -2px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 3px solid #2d1b3d;
}

.status-indicator.online {
  background-color: #34c759;
}

.status-indicator.busy {
  background-color: #ff3b30;
}

.status-indicator.away {
  background-color: #ff9500;
}

.status-indicator.offline {
  background-color: #8e8e93;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.username {
  font-size: 16px;
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-status {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
}

.nav-menu {
  flex: 1;
  padding: 0 16px;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  cursor: pointer;
  border-radius: 12px;
  margin-bottom: 8px;
  transition: all 0.3s ease;
  color: rgba(255, 255, 255, 0.8);
  position: relative;
  overflow: hidden;
}

.nav-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
  transition: left 0.5s ease;
}

.nav-item:hover::before {
  left: 100%;
}

.nav-item:hover {
  background-color: rgba(255, 255, 255, 0.1);
  color: #ffffff;
  transform: translateX(4px);
}

.nav-item.active {
  background: linear-gradient(135deg, #8b45bf 0%, #6a3093 100%);
  color: #ffffff;
  box-shadow: 0 4px 15px rgba(139, 69, 191, 0.3);
}

.nav-item.active:hover {
  background: linear-gradient(135deg, #9b55cf 0%, #7a40a3 100%);
  transform: translateX(2px);
}

.nav-icon {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 1px;
  margin-right: 12px;
  min-width: 50px;
}

.nav-label {
  font-size: 14px;
  font-weight: 500;
}

.bottom-actions {
  padding: 0 16px;
  margin-top: auto;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding-top: 20px;
}

.logout-btn:hover {
  background-color: rgba(255, 59, 48, 0.2);
  color: #ff6b6b;
}

.logout-btn.active {
  background: linear-gradient(135deg, #ff3b30 0%, #e03028 100%);
}

/* 响应式调整 */
@media (max-width: 768px) {
  .side-navigation {
    width: 180px;
    min-width: 180px;
  }
  
  .user-avatar-section {
    padding: 0 16px;
  }
  
  .nav-item {
    padding: 14px 16px;
  }
  
  .nav-icon {
    font-size: 11px;
    min-width: 45px;
  }
  
  .nav-label {
    font-size: 13px;
  }
}
</style>
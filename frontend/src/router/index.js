import { createRouter, createWebHistory } from 'vue-router'
import { 
  isAuthenticated, 
  validateTokenApi, 
  addAuthStateListener,
  removeTokenWithNotify 
} from '@/api/auth.js'
import { ElMessage } from 'element-plus'

// 路由配置
const routes = [
  {
    path: '/',
    redirect: () => {
      return isAuthenticated() ? '/main' : '/login'
    }
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/pages/auth/LoginPage.vue'),
    meta: { 
      requiresGuest: true,
      title: '登录'
    }
  },
  {
    path: '/register',
    name: 'Register', 
    component: () => import('@/pages/auth/RegisterPage.vue'),
    meta: { 
      requiresGuest: true,
      title: '注册'
    }
  },
  {
    path: '/main',
    name: 'Main',
    component: () => import('@/pages/main/MainPage.vue'),
    meta: { 
      requiresAuth: true,
      title: '主界面'
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    redirect: '/login'
  }
]

// 创建路由实例
const router = createRouter({
  history: createWebHistory('/'),
  routes
})

// 开发模式 - 跳过认证检查
const DEV_MODE = true

// Token验证缓存
let lastTokenValidation = null
const TOKEN_VALIDATION_CACHE_TIME = 5 * 60 * 1000

// 验证Token有效性（带缓存）
const validateTokenWithCache = async () => {
  const now = Date.now()
  
  if (lastTokenValidation && 
      (now - lastTokenValidation.timestamp) < TOKEN_VALIDATION_CACHE_TIME) {
    return lastTokenValidation.result
  }
  
  const result = await validateTokenApi()
  lastTokenValidation = {
    timestamp: now,
    result: result
  }
  
  return result
}

// 路由守卫
router.beforeEach(async (to, from, next) => {
  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - 安全即时通讯系统`
  }
  
  // 开发模式：跳过认证检查
  if (DEV_MODE) {
    next()
    return
  }
  
  const hasToken = isAuthenticated()
  
  // 需要认证的路由
  if (to.meta.requiresAuth) {
    if (!hasToken) {
      ElMessage.warning('请先登录')
      next({
        path: '/login',
        query: { redirect: to.fullPath }
      })
      return
    }
    
    // 验证Token有效性
    const tokenValidation = await validateTokenWithCache()
    if (!tokenValidation.success) {
      ElMessage.error('登录已过期，请重新登录')
      removeTokenWithNotify()
      next({
        path: '/login',
        query: { redirect: to.fullPath }
      })
      return
    }
  }
  
  // 需要未登录状态的路由
  if (to.meta.requiresGuest && hasToken) {
    const redirectPath = to.query.redirect || '/main'
    next(redirectPath)
    return
  }
  
  next()
})

// 监听认证状态变化
addAuthStateListener((isAuth) => {
  if (!isAuth) {
    const currentRoute = router.currentRoute.value
    if (currentRoute.meta.requiresAuth) {
      router.push({
        path: '/login',
        query: { redirect: currentRoute.fullPath }
      })
    }
  } else {
    lastTokenValidation = null
  }
})

export default router
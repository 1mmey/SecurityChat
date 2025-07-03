<template>
  <AuthLayout>
    <!-- 登录表单 -->
    <el-form ref="loginFormRef" :model="loginForm" size="large">
      <el-form-item>
        <el-input
          v-model="loginForm.username"
          placeholder="USERNAME OR ID"
          clearable
          :disabled="loading"
        />
      </el-form-item>
      
      <el-form-item>
        <el-input
          v-model="loginForm.password"
          type="password"
          placeholder="PASSWORD"
          show-password
          :disabled="loading"
          @keyup.enter="handleLogin"
        />
      </el-form-item>
      
      <el-form-item>
        <el-button 
          type="primary" 
          @click="handleLogin"
          :loading="loading"
          :disabled="!loginForm.username || !loginForm.password"
          style="width: 100%"
        >
          {{ loading ? 'LOGINING...' : 'LOGIN' }}
        </el-button>
      </el-form-item>
    </el-form>

    <!-- 底部切换区域 -->
    <template #footer>
      <div class="auth-footer">
        <span>No Account？</span>
        <span class="link-text" @click="switchToRegister">Register</span>
      </div>
      
      <div class="forgot-password">
        <span class="forgot-text" @click="handleForgotPassword">Forget Password？</span>
      </div>
    </template>
  </AuthLayout>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AuthLayout from '@/components/layout/AuthLayout.vue'
import { loginApi, saveUserInfo, startTokenValidityCheck } from '@/api/auth.js'

const router = useRouter()
const loading = ref(false)

// 登录表单数据
const loginForm = reactive({
  username: '',
  password: ''
})

// 登录处理
const handleLogin = async () => {
  if (!loginForm.username || !loginForm.password) {
    ElMessage.warning('请填写用户名和密码')
    return
  }
  
  loading.value = true
  
  try {
    const result = await loginApi(loginForm.username, loginForm.password)
    
    if (result.success) {
      // 保存用户信息
      saveUserInfo({
        username: loginForm.username,
        loginTime: new Date().toISOString()
      })
      
      // 启动token检查
      startTokenValidityCheck()
      
      ElMessage.success('登录成功')
      
      // 跳转到主界面
      router.push('/main')
    } else {
      ElMessage.error(result.message)
    }
  } catch (error) {
    ElMessage.error('登录失败')
  } finally {
    loading.value = false
  }
}

// 切换到注册页面
const switchToRegister = () => {
  router.push('/register')
}

// 忘记密码处理
const handleForgotPassword = () => {
  ElMessage.info('请联系管理员重置密码')
}

// 开发环境自动填充
onMounted(() => {
  if (process.env.NODE_ENV === 'development') {
    loginForm.username = 'testuser'
    loginForm.password = 'testpass123'
  }
})
</script>

<style scoped>
.auth-footer {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.link-text {
  color: #000000;
  cursor: pointer;
  text-decoration: none;
}

.link-text:hover {
  text-decoration: underline;
}

.forgot-password {
  text-align: center;
}

.forgot-text {
  color: #909399;
  cursor: pointer;
  font-size: 12px;
}

.forgot-text:hover {
  text-decoration: underline;
}
.el-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 加载状态下的输入框样式 */
.el-input.is-disabled .el-input__wrapper {
  background-color: var(--el-disabled-bg-color);
  box-shadow: 0 0 0 1px var(--el-disabled-border-color) inset;
}

/* 表单验证错误样式微调 */
.el-form-item.is-error .el-input__wrapper {
  box-shadow: 0 0 0 1px var(--el-color-danger) inset;
}

/* 响应式调整 */
@media (max-width: 480px) {
  .el-form {
    padding: 0 10px;
  }
}
</style>
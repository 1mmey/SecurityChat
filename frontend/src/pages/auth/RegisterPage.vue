<template>
  <AuthLayout>
    <!-- 注册表单 -->
    <el-form ref="registerFormRef" :model="registerForm" size="large">
      <el-form-item>
        <el-input
          v-model="registerForm.username"
          placeholder="USERNAME"
          clearable
          :disabled="loading"
        />
      </el-form-item>
      
      <el-form-item>
        <el-input
          v-model="registerForm.email"
          placeholder="EMAIL"
          clearable
          :disabled="loading"
        />
      </el-form-item>
      
      <el-form-item>
        <el-input
          v-model="registerForm.password"
          type="password"
          placeholder="PASSWORD"
          show-password
          :disabled="loading"
        />
      </el-form-item>
      
      <el-form-item>
        <el-input
          v-model="registerForm.confirmPassword"
          type="password"
          placeholder="CONFIRM PASSWORD"
          show-password
          :disabled="loading"
          @keyup.enter="handleRegister"
        />
      </el-form-item>
      
      <el-form-item>
        <el-button 
          type="primary" 
          @click="handleRegister"
          :loading="loading"
          :disabled="!isFormValid"
          style="width: 100%"
        >
          {{ loading ? 'REGISTERING...' : 'REGISTER' }}
        </el-button>
      </el-form-item>
    </el-form>

    <!-- 底部切换区域 -->
    <template #footer>
      <div class="auth-footer">
        <span>Have Account？</span>
        <span class="link-text" @click="switchToLogin">Login</span>
      </div>
    </template>
  </AuthLayout>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AuthLayout from '@/components/layout/AuthLayout.vue'
import { registerApi } from '@/api/auth.js'

const router = useRouter()
const loading = ref(false)

// 注册表单数据
const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

// 检查表单是否有效
const isFormValid = computed(() => {
  return registerForm.username && 
         registerForm.email && 
         registerForm.password && 
         registerForm.confirmPassword &&
         registerForm.password === registerForm.confirmPassword
})

// 生成简单的公钥（实际项目中应使用真正的密钥生成）
const generateKeyPair = () => {
  const timestamp = Date.now()
  const username = registerForm.username
  const keyData = btoa(`${username}:${timestamp}`).slice(0, 64)
  
  return {
    publicKey: `-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA${keyData}
${keyData}==
-----END PUBLIC KEY-----`,
    privateKey: `-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC${keyData}
${keyData}==
-----END PRIVATE KEY-----`
  }
}

// 注册处理
const handleRegister = async () => {
  if (!isFormValid.value) {
    ElMessage.warning('请填写完整信息')
    return
  }
  
  if (registerForm.password !== registerForm.confirmPassword) {
    ElMessage.error('两次输入的密码不一致')
    return
  }
  
  loading.value = true
  
  try {
    // 生成密钥对
    const keyPair = generateKeyPair()
    
    // 准备注册数据
    const registerData = {
      username: registerForm.username,
      email: registerForm.email,
      password: registerForm.password,
      public_key: keyPair.publicKey
    }
    
    const result = await registerApi(registerData)
    
    if (result.success) {
      // 保存私钥
      localStorage.setItem(`private_key_${registerForm.username}`, keyPair.privateKey)
      
      ElMessage.success('注册成功，请登录')
      
      // 清空表单
      Object.keys(registerForm).forEach(key => {
        registerForm[key] = ''
      })
      
      // 跳转到登录页
      router.push('/login')
    } else {
      ElMessage.error(result.message)
    }
  } catch (error) {
    ElMessage.error('注册失败')
  } finally {
    loading.value = false
  }
}

// 切换到登录页面
const switchToLogin = () => {
  router.push('/login')
}

// 开发环境自动填充
onMounted(() => {
  if (process.env.NODE_ENV === 'development') {
    registerForm.username = 'newuser'
    registerForm.email = 'test@example.com'
    registerForm.password = 'testpass123'
    registerForm.confirmPassword = 'testpass123'
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

/* 密码强度提示样式 */
.password-strength {
  font-size: 12px;
  margin-top: 4px;
  color: var(--el-text-color-regular);
}

.password-strength.weak {
  color: var(--el-color-danger);
}

.password-strength.medium {
  color: var(--el-color-warning);
}

.password-strength.strong {
  color: var(--el-color-success);
}

/* 响应式调整 */
@media (max-width: 480px) {
  .el-form {
    padding: 0 10px;
  }
}
</style>
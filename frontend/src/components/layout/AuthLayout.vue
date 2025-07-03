<template>
  <div class="auth-layout">
    <!-- 自定义窗口标题栏 -->
    <div class="window-header">
      <div class="window-controls">
        <div class="control-button close" @click="closeWindow"></div>
        <div class="control-button minimize" @click="minimizeWindow"></div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 登录表单卡片 -->
      <div class="auth-card">
        <div class="form-section">
          <slot></slot>
        </div>
        <div class="switch-section">
          <slot name="footer"></slot>
        </div>
      </div>

      <!-- 信息展示卡片 -->
      <div class="info-card">
        <div class="info-content">
          <h3>New in</h3>
          <div class="discover-btn">Discover</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'

const closeWindow = () => {
  if (window.electronAPI) {
    window.electronAPI.closeWindow()
  }
}

const minimizeWindow = () => {
  if (window.electronAPI) {
    window.electronAPI.minimizeWindow()
  }
}

onMounted(() => {
  document.addEventListener('contextmenu', e => e.preventDefault())
})
</script>

<style scoped lang="scss">
.auth-layout {
  width: 100vw;
  height: 100vh;
  background: linear-gradient(135deg, #f5f5f7 0%, #e5e5e7 100%);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  user-select: none;
}

.window-header {
  height: 32px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  display: flex;
  justify-content: flex-start;
  align-items: center;
  padding: 0 12px;
  -webkit-app-region: drag;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);

  .window-controls {
    display: flex;
    gap: 8px;
    -webkit-app-region: no-drag;

    .control-button {
      width: 12px;
      height: 12px;
      border-radius: 50%;
      cursor: pointer;
      transition: all 0.2s ease;

      &.close {
        background: #ff5f57;
        &:hover { background: #ff3b30; }
      }

      &.minimize {
        background: #ffbd2e;
        &:hover { background: #ff9500; }
      }
    }
  }
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px;
  align-items: center;
  justify-content: center;
}

.auth-card {
  background: rgba(255, 255, 255, 0.35);
  backdrop-filter: blur(20px);
  border-radius: 26px;
  padding: 35px 32px;
  width: 100%;
  max-width: 320px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);

  .form-section {
    margin-bottom: 24px;
  }

  .switch-section {
    text-align: center;
  }
}

.info-card {
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(20px);
  border-radius: 26px;
  padding: 24px;
  width: 100%;
  max-width: 320px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.1);

  .info-content {
    color: white;
    text-align: left;

    h3 {
      font-size: 20px;
      font-weight: 600;
      margin: 0 0 8px 0;
    }

    p {
      font-size: 14px;
      margin: 0 0 16px 0;
      opacity: 0.7;
    }

    .discover-btn {
      font-size: 16px;
      font-weight: 500;
      opacity: 1;
      cursor: pointer;
      transition: opacity 0.2s ease;
      text-align: right;
    }
  }
}

// ElementPlus样式保持不变
:deep(.el-input) {
  margin-bottom: 16px;
  
  .el-input__wrapper {
    border-radius: 8px;
    background: white;
    border: 2px solid #1d1d1f;
    
    &:hover { background: #ebebeb; }
  }
  
  .el-input__inner {
    color: #1d1d1f;
    font-size: 14px;
    
    &::placeholder { color: #86868b; }
  }
}

:deep(.el-button) {
  width: 100%;
  height: 44px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 12px;
  transition: all 0.2s ease;
  border: 2px solid #ffffff;
  
  &.el-button--primary {
    background: #000000;
    
    &:hover {
      background: #00296a;
    }
  }
}

:deep(.el-text) {
  color: #86868b;
  font-size: 14px;
  
  &.is-link {
    color: #007AFF;
    cursor: pointer;
    
    &:hover { color: #0051D5; }
  }
}
</style>
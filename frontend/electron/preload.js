const { contextBridge, ipcRenderer } = require('electron')

// 向渲染进程暴露安全的API
contextBridge.exposeInMainWorld('electronAPI', {
  // 窗口控制
  switchToMain: () => ipcRenderer.invoke('switch-to-main'),
  switchToAuth: () => ipcRenderer.invoke('switch-to-auth'),
  
  // 获取窗口信息
  getWindowInfo: () => ipcRenderer.invoke('get-window-info'),
  
  // 监听窗口大小变化
  onWindowResize: (callback) => {
    ipcRenderer.on('window-resized', (event, data) => callback(data))
  },
  
  // 移除窗口大小变化监听器
  removeWindowResizeListener: () => {
    ipcRenderer.removeAllListeners('window-resized')
  },
  
  // 应用信息
  platform: process.platform,
  isElectron: true
})

// 开发模式下的调试信息
if (process.env.NODE_ENV === 'development') {
  contextBridge.exposeInMainWorld('electronDev', {
    openDevTools: () => ipcRenderer.invoke('open-dev-tools'),
    getAppVersion: () => ipcRenderer.invoke('get-app-version')
  })
}

console.log('Preload script loaded successfully')
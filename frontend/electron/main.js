const { app, BrowserWindow, ipcMain } = require('electron')
const path = require('path')
const isDev = process.env.NODE_ENV === 'development'

// 窗口实例
let authWindow = null
let mainWindow = null

// 窗口配置
const WINDOW_CONFIG = {
  // 登录/注册窗口配置
  auth: {
    width: 400,
    height: 500,
    minWidth: 380,
    minHeight: 450,
    maxWidth: 500,
    maxHeight: 600,
    resizable: true,
    center: true,
    show: false,
    frame: true,
    titleBarStyle: 'default'
  },
  
  // 主界面窗口配置  
  main: {
    width: 1200,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    resizable: true,
    center: true,
    show: false,
    frame: true,
    titleBarStyle: 'default'
  }
}

// 创建登录窗口
function createAuthWindow() {
  console.log('创建认证窗口')
  
  authWindow = new BrowserWindow({
    ...WINDOW_CONFIG.auth,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, '../build/icon.png') // 应用图标
  })

  // 加载应用
  const startUrl = isDev 
    ? 'http://localhost:8080' 
    : `file://${path.join(__dirname, '../dist/index.html')}`
  
  authWindow.loadURL(startUrl)

  // 窗口就绪后显示
  authWindow.once('ready-to-show', () => {
    authWindow.show()
    console.log('认证窗口显示完成')
  })

  // 开发模式下打开开发者工具
  if (isDev) {
    authWindow.webContents.openDevTools()
  }

  // 窗口关闭事件
  authWindow.on('closed', () => {
    authWindow = null
    console.log('认证窗口已关闭')
  })

  // 监听页面导航，实现窗口切换
  authWindow.webContents.on('did-navigate', (event, navigationUrl) => {
    const url = new URL(navigationUrl)
    console.log('页面导航:', url.pathname)
    
    // 如果导航到主界面，切换到主窗口
    if (url.pathname === '/main') {
      createMainWindow()
      authWindow.hide()
    }
  })

  return authWindow
}

// 创建主窗口
function createMainWindow() {
  console.log('创建主界面窗口')
  
  mainWindow = new BrowserWindow({
    ...WINDOW_CONFIG.main,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, '../build/icon.png')
  })

  // 加载主界面
  const startUrl = isDev 
    ? 'http://localhost:8080/#/main' 
    : `file://${path.join(__dirname, '../dist/index.html')}#/main`
  
  mainWindow.loadURL(startUrl)

  // 窗口就绪后显示
  mainWindow.once('ready-to-show', () => {
    mainWindow.show()
    mainWindow.focus()
    
    // 关闭认证窗口
    if (authWindow && !authWindow.isDestroyed()) {
      authWindow.close()
    }
    
    console.log('主界面窗口显示完成')
  })

  // 开发模式下打开开发者工具
  if (isDev) {
    mainWindow.webContents.openDevTools()
  }

  // 窗口关闭事件
  mainWindow.on('closed', () => {
    mainWindow = null
    console.log('主界面窗口已关闭')
  })

  // 响应式处理：监听窗口大小变化
  mainWindow.on('resize', () => {
    const [width, height] = mainWindow.getSize()
    console.log(`窗口大小变化: ${width}x${height}`)
    
    // 发送窗口大小变化事件到渲染进程
    mainWindow.webContents.send('window-resized', { width, height })
  })

  // 监听页面导航
  mainWindow.webContents.on('did-navigate', (event, navigationUrl) => {
    const url = new URL(navigationUrl)
    console.log('主窗口页面导航:', url.pathname)
    
    // 如果导航回登录页，切换到认证窗口
    if (url.pathname === '/login' || url.pathname === '/register') {
      createAuthWindow()
      mainWindow.close()
    }
  })

  return mainWindow
}

// 应用就绪事件
app.whenReady().then(() => {
  console.log('Electron应用就绪')
  
  // 创建初始窗口（认证窗口）
  createAuthWindow()

  // macOS: 点击dock图标时重新创建窗口
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createAuthWindow()
    }
  })
})

// 所有窗口关闭事件
app.on('window-all-closed', () => {
  console.log('所有窗口已关闭')
  
  // macOS: 通常应用不会完全退出
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

// IPC 通信处理
ipcMain.handle('switch-to-main', async () => {
  console.log('收到切换主窗口请求')
  createMainWindow()
  return true
})

ipcMain.handle('switch-to-auth', async () => {
  console.log('收到切换认证窗口请求')
  createAuthWindow()
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.close()
  }
  return true
})

ipcMain.handle('get-window-info', async () => {
  const currentWindow = BrowserWindow.getFocusedWindow()
  if (currentWindow) {
    const [width, height] = currentWindow.getSize()
    return { width, height, type: currentWindow === mainWindow ? 'main' : 'auth' }
  }
  return null
})

// 应用退出前清理
app.on('before-quit', () => {
  console.log('应用即将退出，清理资源')
})

// 防止意外退出
app.on('will-quit', (event) => {
  console.log('应用尝试退出')
  // 可以在这里添加退出确认逻辑
})

// 错误处理
process.on('uncaughtException', (error) => {
  console.error('未捕获的异常:', error)
})

process.on('unhandledRejection', (reason, promise) => {
  console.error('未处理的Promise拒绝:', reason)
})
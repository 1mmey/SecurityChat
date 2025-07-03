const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  
  // 开发服务器配置
  devServer: {
    host: '0.0.0.0', // 允许外部访问
    port: 8000, 
    open: true, // 自动打开浏览器
  },
  
  // 生产环境配置
  publicPath: process.env.NODE_ENV === 'production' ? './' : '/',
  lintOnSave: false,
  // Electron配置
  pluginOptions: {
    electronBuilder: {
      nodeIntegration: true,
      contextIsolation: false,
      enableRemoteModule: true,
      preload: 'electron/preload.js',
      mainProcessFile: 'electron/main.js',
      rendererProcessFile: 'src/main.js'
    }
  }
})
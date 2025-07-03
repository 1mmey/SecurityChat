import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

// Element Plus
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'

// 创建Vue应用实例
const app = createApp(App)

// 注册插件
app.use(ElementPlus)
app.use(router)

// 挂载应用
app.mount('#app')

// 开发环境调试
if (process.env.NODE_ENV === 'development') {
  console.log('应用已启动，路由已配置')
}
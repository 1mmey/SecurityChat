import { updateConnectionInfo } from '@/api/friend.js'

class HeartbeatManager {
  constructor() {
    this.interval = null
    this.isRunning = false
    this.intervalTime = 30000
    this.callbacks = new Set()
    this.errorCallbacks = new Set()
    this.lastHeartbeatTime = null
    this.consecutiveErrors = 0
    this.maxConsecutiveErrors = 3
  }

  start() {
    if (this.isRunning) {
      console.warn('心跳已经在运行中')
      return
    }

    this.isRunning = true
    this.consecutiveErrors = 0
    console.log('开始心跳管理')

    this.sendHeartbeat()

    this.interval = setInterval(() => {
      this.sendHeartbeat()
    }, this.intervalTime)
  }

  stop() {
    if (!this.isRunning) {
      return
    }

    if (this.interval) {
      clearInterval(this.interval)
      this.interval = null
    }

    this.isRunning = false
    console.log('心跳管理已停止')
  }

  async sendHeartbeat() {
    try {
      const result = await updateConnectionInfo(0)
      
      if (result.success) {
        this.lastHeartbeatTime = Date.now()
        this.consecutiveErrors = 0
        console.log('心跳发送成功')
        
        this.callbacks.forEach(callback => {
          try {
            callback(result)
          } catch (error) {
            console.error('心跳成功回调执行失败:', error)
          }
        })
      } else {
        this.handleHeartbeatError(new Error(result.message || '心跳发送失败'))
      }
    } catch (error) {
      this.handleHeartbeatError(error)
    }
  }

  handleHeartbeatError(error) {
    this.consecutiveErrors++
    console.warn(`心跳发送失败 (${this.consecutiveErrors}/${this.maxConsecutiveErrors}):`, error.message)
    
    this.errorCallbacks.forEach(callback => {
      try {
        callback(error, this.consecutiveErrors)
      } catch (callbackError) {
        console.error('心跳错误回调执行失败:', callbackError)
      }
    })

    if (this.consecutiveErrors >= this.maxConsecutiveErrors) {
      console.error('心跳连续失败次数达到上限，可能需要检查网络连接')
    }
  }

  addCallback(callback) {
    if (typeof callback === 'function') {
      this.callbacks.add(callback)
      console.log('添加心跳成功回调，当前回调数量:', this.callbacks.size)
    }
  }

  removeCallback(callback) {
    this.callbacks.delete(callback)
    console.log('移除心跳成功回调，当前回调数量:', this.callbacks.size)
  }

  addErrorCallback(callback) {
    if (typeof callback === 'function') {
      this.errorCallbacks.add(callback)
      console.log('添加心跳错误回调，当前错误回调数量:', this.errorCallbacks.size)
    }
  }

  removeErrorCallback(callback) {
    this.errorCallbacks.delete(callback)
    console.log('移除心跳错误回调，当前错误回调数量:', this.errorCallbacks.size)
  }

  setInterval(time) {
    if (time > 0) {
      this.intervalTime = time
      
      if (this.isRunning) {
        this.stop()
        this.start()
      }
      
      console.log('设置心跳间隔为:', time + 'ms')
    }
  }

  getStatus() {
    return {
      isRunning: this.isRunning,
      intervalTime: this.intervalTime,
      callbackCount: this.callbacks.size,
      errorCallbackCount: this.errorCallbacks.size,
      lastHeartbeatTime: this.lastHeartbeatTime,
      consecutiveErrors: this.consecutiveErrors,
      timeSinceLastHeartbeat: this.lastHeartbeatTime ? Date.now() - this.lastHeartbeatTime : null,
      isHealthy: this.consecutiveErrors < this.maxConsecutiveErrors
    }
  }

  triggerHeartbeat() {
    console.log('手动触发心跳')
    this.sendHeartbeat()
  }

  reset() {
    console.log('重置心跳管理器')
    this.stop()
    this.consecutiveErrors = 0
    this.lastHeartbeatTime = null
  }

  isHealthy() {
    if (!this.isRunning) {
      return false
    }

    if (this.consecutiveErrors >= this.maxConsecutiveErrors) {
      return false
    }

    if (this.lastHeartbeatTime) {
      const timeSinceLastHeartbeat = Date.now() - this.lastHeartbeatTime
      return timeSinceLastHeartbeat < this.intervalTime * 2
    }

    return true
  }

  getHealthReport() {
    const status = this.getStatus()
    
    return {
      ...status,
      healthStatus: this.isHealthy() ? 'healthy' : 'unhealthy',
      networkStatus: navigator.onLine ? 'online' : 'offline',
      recommendations: this.getRecommendations()
    }
  }

  getRecommendations() {
    const recommendations = []
    
    if (!navigator.onLine) {
      recommendations.push('检查网络连接')
    }
    
    if (this.consecutiveErrors >= this.maxConsecutiveErrors) {
      recommendations.push('检查服务器连接状态')
      recommendations.push('考虑重新登录')
    }
    
    if (this.lastHeartbeatTime && Date.now() - this.lastHeartbeatTime > this.intervalTime * 3) {
      recommendations.push('心跳响应超时，建议重启心跳服务')
    }
    
    return recommendations
  }

  cleanup() {
    console.log('清理心跳管理器')
    this.stop()
    this.callbacks.clear()
    this.errorCallbacks.clear()
    this.lastHeartbeatTime = null
    this.consecutiveErrors = 0
    console.log('心跳管理器清理完成')
  }
}

const heartbeatManager = new HeartbeatManager()

export default heartbeatManager
/**
 * 优化的页面访问日志记录工具
 * 减少调用频率，使用更高效的批量处理机制
 */

import logService from '@/services/api/logService'

class PageLogger {
  constructor() {
    this.logQueue = []
    this.isProcessing = false
    this.batchTimeout = null
    this.lastLogTime = 0
    this.debounceTimers = new Map() // 防抖定时器
    this.rateLimitCounter = 0 // 频率限制计数器
    this.rateLimitResetTime = Date.now() // 频率限制重置时间
    
    // 配置参数
    this.minInterval = 3000 // 最小间隔3秒
    this.maxBatchSize = 15 // 最大批量大小
    this.batchTimeoutMs = 8000 // 批量处理超时时间8秒
    this.debounceDelay = 800 // 防抖延迟800ms
    this.maxPerMinute = 20 // 每分钟最大记录次数
    
    // 检测移动端
    this.isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
    
    // 移动端优化
    if (this.isMobile) {
      this.maxBatchSize = 10
      this.batchTimeoutMs = 5000
    }
  }

  /**
   * 记录页面访问（带防抖和频率限制）
   * @param {string} pageName 页面名称
   * @param {string} pagePath 页面路径
   */
  logPageAccess(pageName, pagePath) {
    // 检查是否已登录
    if (!localStorage.getItem('token')) {
      return
    }

    // 检查是否在排除列表中
    if (this._isExcluded(pageName, pagePath)) {
      return
    }

    // 频率限制检查
    if (!this._checkRateLimit()) {
      return
    }

    // 创建唯一键，用于防抖
    const key = `${pageName}-${pagePath}`
    
    // 清除之前的防抖定时器
    if (this.debounceTimers.has(key)) {
      clearTimeout(this.debounceTimers.get(key))
    }

    // 设置防抖定时器
    const debounceTimer = setTimeout(() => {
      this.debounceTimers.delete(key)
      this._addToQueue(pageName, pagePath)
    }, this.debounceDelay)

    this.debounceTimers.set(key, debounceTimer)
  }

  /**
   * 检查是否在排除列表中
   */
  _isExcluded(pageName, pagePath) {
    const excludedPaths = ['/login', '/logout', '/error', '/404', '/500']
    const excludedNames = ['登录', '登出', '错误页面', '404页面', '500页面']
    
    return excludedPaths.includes(pagePath) || excludedNames.includes(pageName)
  }

  /**
   * 检查频率限制
   */
  _checkRateLimit() {
    const now = Date.now()
    
    // 每分钟重置计数器
    if (now - this.rateLimitResetTime >= 60000) {
      this.rateLimitCounter = 0
      this.rateLimitResetTime = now
    }

    // 检查是否超过限制
    if (this.rateLimitCounter >= this.maxPerMinute) {
      return false
    }

    this.rateLimitCounter++
    return true
  }

  /**
   * 添加到队列（带频率限制）
   * @param {string} pageName 页面名称
   * @param {string} pagePath 页面路径
   */
  _addToQueue(pageName, pagePath) {
    const now = Date.now()
    
    // 频率限制：最小间隔内不重复记录同一页面
    if (now - this.lastLogTime < this.minInterval) {
      // 检查是否已存在相同页面的记录
      const existingIndex = this.logQueue.findIndex(
        item => item.page_name === pageName && item.page_path === pagePath
      )
      
      if (existingIndex !== -1) {
        // 更新现有记录的时间戳
        this.logQueue[existingIndex].timestamp = new Date().toISOString()
        return
      }
    }

    // 添加到队列
    this.logQueue.push({
      page_name: pageName,
      page_path: pagePath,
      from_path: '菜单导航',
      timestamp: new Date().toISOString()
    })

    this.lastLogTime = now

    // 智能批量处理
    this._smartBatchProcess()
  }

  /**
   * 智能批量处理
   */
  _smartBatchProcess() {
    // 如果队列达到最大批量大小，立即处理
    if (this.logQueue.length >= this.maxBatchSize) {
      this._processBatch()
      return
    }

    // 清除之前的定时器
    if (this.batchTimeout) {
      clearTimeout(this.batchTimeout)
    }

    // 设置新的定时器
    this.batchTimeout = setTimeout(() => {
      this._processBatch()
    }, this.batchTimeoutMs)
  }

  /**
   * 批量处理日志队列
   */
  async _processBatch() {
    if (this.isProcessing || this.logQueue.length === 0) {
      return
    }

    this.isProcessing = true
    const batch = [...this.logQueue]
    this.logQueue = []

    try {
      // 去重处理：合并相同页面的访问记录
      const uniqueLogs = this._deduplicateLogs(batch)
      
      // 批量发送到服务器
      await this._sendBatchToServer(uniqueLogs)
      
      console.debug(`📊 批量处理页面访问日志: ${uniqueLogs.length} 条记录`)
    } catch (error) {
      console.debug('批量页面访问日志处理失败:', error)
    } finally {
      this.isProcessing = false
    }
  }

  /**
   * 去重处理日志
   * @param {Array} logs 日志数组
   * @returns {Array} 去重后的日志
   */
  _deduplicateLogs(logs) {
    const uniqueMap = new Map()
    
    logs.forEach(log => {
      const key = `${log.page_name}-${log.page_path}`
      if (!uniqueMap.has(key) || new Date(log.timestamp) > new Date(uniqueMap.get(key).timestamp)) {
        uniqueMap.set(key, log)
      }
    })
    
    return Array.from(uniqueMap.values())
  }

  /**
   * 批量发送到服务器
   * @param {Array} logs 日志数组
   */
  async _sendBatchToServer(logs) {
    // 如果只有一条记录，直接发送
    if (logs.length === 1) {
      await logService.recordPageAccess(logs[0])
      return
    }

    // 多条记录时，使用Promise.all提高效率
    const promises = logs.map(log => 
      logService.recordPageAccess(log).catch(error => {
        console.debug('单个页面访问日志记录失败:', error)
        return null
      })
    )

    await Promise.all(promises)
  }

  /**
   * 立即处理所有待处理日志（页面卸载时使用）
   */
  async flushLogs() {
    // 清除所有防抖定时器
    this.debounceTimers.forEach(timer => clearTimeout(timer))
    this.debounceTimers.clear()

    if (this.batchTimeout) {
      clearTimeout(this.batchTimeout)
      this.batchTimeout = null
    }
    
    await this._processBatch()
  }

  /**
   * 获取当前队列状态（调试用）
   */
  getQueueStatus() {
    return {
      queueLength: this.logQueue.length,
      isProcessing: this.isProcessing,
      debounceTimersCount: this.debounceTimers.size,
      lastLogTime: this.lastLogTime,
      rateLimitCounter: this.rateLimitCounter,
      isMobile: this.isMobile
    }
  }
}

// 创建全局实例
const pageLogger = new PageLogger()

// 页面卸载时清空日志队列
window.addEventListener('beforeunload', () => {
  pageLogger.flushLogs()
})

// 页面隐藏时也处理日志（移动端优化）
document.addEventListener('visibilitychange', () => {
  if (document.hidden) {
    pageLogger.flushLogs()
  }
})

export default pageLogger 
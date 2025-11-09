/**
 * 优化的页面访问日志记录 Mixin
 * 减少调用频率，只在必要时记录访问日志
 */

import pageLogger from '@/utils/page_logger_optimized'

export default {
  data() {
    return {
      pageLogDebounceTimer: null,
      hasLoggedAccess: false
    }
  },

  mounted() {
    // 在页面加载完成后记录访问日志
    this.$nextTick(() => {
      this.logPageAccess()
    })
  },

  methods: {
    /**
     * 记录当前页面访问日志（带防抖和条件判断）
     */
    logPageAccess() {
      try {
        // 从路由元信息获取页面标题
        const pageName = this.$route.meta?.title
        const pagePath = this.$route.path

        // 条件判断：只在满足条件时记录
        if (!this._shouldLogPageAccess(pageName, pagePath)) {
          return
        }

        // 防抖处理：避免短时间内重复调用
        if (this.pageLogDebounceTimer) {
          clearTimeout(this.pageLogDebounceTimer)
        }

        this.pageLogDebounceTimer = setTimeout(() => {
          // 安全记录页面访问日志
          if (pageName && this.$route.meta?.requiresAuth) {
            // 异步记录，不阻塞页面加载
            setTimeout(() => {
              pageLogger.logPageAccess(pageName, pagePath)
              this.hasLoggedAccess = true
            }, 200) // 延迟200ms，确保页面完全加载
            
            console.debug(`📊 记录页面访问: ${pageName} (${pagePath})`)
          }
        }, 300) // 300ms防抖

      } catch (error) {
        // 静默处理错误，不影响页面功能
        console.debug('页面访问日志记录失败:', error)
      }
    },

    /**
     * 判断是否应该记录页面访问
     * @param {string} pageName 页面名称
     * @param {string} pagePath 页面路径
     * @returns {boolean} 是否应该记录
     */
    _shouldLogPageAccess(pageName, pagePath) {
      // 基本条件检查
      if (!pageName || !pagePath) {
        return false
      }

      // 检查是否需要认证
      if (!this.$route.meta?.requiresAuth) {
        return false
      }

      // 检查是否已记录过（避免重复记录）
      if (this.hasLoggedAccess) {
        return false
      }

      // 检查是否在排除列表中
      const excludedPaths = [
        '/login',
        '/logout',
        '/error',
        '/404',
        '/500'
      ]
      
      if (excludedPaths.includes(pagePath)) {
        return false
      }

      // 检查是否在排除的页面名称中
      const excludedPageNames = [
        '登录',
        '登出',
        '错误页面',
        '404页面',
        '500页面'
      ]
      
      if (excludedPageNames.includes(pageName)) {
        return false
      }

      // 检查用户是否已登录
      if (!localStorage.getItem('token')) {
        return false
      }

      return true
    }
  },

  // Vue 3 兼容：使用 beforeUnmount 替代 beforeDestroy
  beforeUnmount() {
    // 清除防抖定时器
    if (this.pageLogDebounceTimer) {
      clearTimeout(this.pageLogDebounceTimer)
      this.pageLogDebounceTimer = null
    }

    // 页面销毁时确保日志已处理
    if (pageLogger && typeof pageLogger.flushLogs === 'function') {
      pageLogger.flushLogs()
    }
  },

  // Vue 2 兼容：保留 beforeDestroy
  beforeDestroy() {
    // 清除防抖定时器
    if (this.pageLogDebounceTimer) {
      clearTimeout(this.pageLogDebounceTimer)
      this.pageLogDebounceTimer = null
    }

    // 页面销毁时确保日志已处理
    if (pageLogger && typeof pageLogger.flushLogs === 'function') {
      pageLogger.flushLogs()
    }
  }
} 
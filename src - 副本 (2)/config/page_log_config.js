/**
 * 页面访问日志配置
 * 提供灵活的配置选项来控制日志记录行为
 */

export default {
  // 是否启用页面访问日志
  enabled: true,

  // 批量处理配置
  batch: {
    // 最大批量大小
    maxSize: 20,
    // 批量处理超时时间（毫秒）
    timeout: 5000,
    // 最小间隔时间（毫秒）
    minInterval: 2000
  },

  // 防抖配置
  debounce: {
    // 防抖延迟时间（毫秒）
    delay: 500,
    // 是否启用防抖
    enabled: true
  },

  // 频率限制配置
  rateLimit: {
    // 是否启用频率限制
    enabled: true,
    // 最小记录间隔（毫秒）
    minInterval: 2000,
    // 最大每分钟记录次数
    maxPerMinute: 30
  },

  // 排除的页面路径
  excludedPaths: [
    '/login',
    '/logout',
    '/error',
    '/404',
    '/500',
    '/unauthorized',
    '/forbidden'
  ],

  // 排除的页面名称
  excludedPageNames: [
    '登录',
    '登出',
    '错误页面',
    '404页面',
    '500页面',
    '未授权',
    '禁止访问'
  ],

  // 只记录特定页面（如果为空则记录所有页面）
  includedPaths: [],

  // 只记录特定页面名称（如果为空则记录所有页面）
  includedPageNames: [],

  // 调试模式
  debug: false,

  // 日志级别
  logLevel: 'info', // 'debug', 'info', 'warn', 'error'

  // 是否在控制台输出调试信息
  consoleOutput: false,

  // 移动端优化
  mobile: {
    // 移动端是否启用
    enabled: true,
    // 移动端批量大小（通常更小）
    batchSize: 10,
    // 移动端超时时间（通常更短）
    timeout: 3000
  },

  // 性能监控
  performance: {
    // 是否监控性能
    enabled: false,
    // 性能阈值（毫秒）
    threshold: 1000
  }
} 
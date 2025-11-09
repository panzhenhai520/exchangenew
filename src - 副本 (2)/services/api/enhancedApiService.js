/**
 * 增强的API服务类
 * 集成缓存、重试、批量请求、性能监控等功能
 */

import api from '../api';
import { globalCache, globalBatchManager, globalPerformanceMonitor, debounce } from '@/utils/performance';

/**
 * 增强的API服务类
 */
export class EnhancedApiService {
  constructor(options = {}) {
    this.options = {
      enableCache: true,
      defaultCacheTTL: 300000, // 5分钟
      enableRetry: true,
      maxRetries: 3,
      retryDelay: 1000,
      enableBatch: false,
      enablePerformanceMonitoring: true,
      ...options
    };
    
    this.cache = globalCache;
    this.batchManager = globalBatchManager;
    this.performanceMonitor = globalPerformanceMonitor;
    this.pendingRequests = new Map(); // 防止重复请求
  }

  /**
   * 生成缓存键
   * @param {string} url - 请求URL
   * @param {Object} params - 请求参数
   * @param {string} method - 请求方法
   * @returns {string} 缓存键
   */
  generateCacheKey(url, params = {}, method = 'GET') {
    const sortedParams = Object.keys(params)
      .sort()
      .reduce((result, key) => {
        result[key] = params[key];
        return result;
      }, {});
    
    return `${method}:${url}:${JSON.stringify(sortedParams)}`;
  }

  /**
   * 执行带缓存的GET请求
   * @param {string} url - 请求URL
   * @param {Object} options - 请求选项
   * @returns {Promise} 请求结果
   */
  async get(url, options = {}) {
    const {
      params = {},
      cache = this.options.enableCache,
      cacheTTL = this.options.defaultCacheTTL,
      retry = this.options.enableRetry,
      ...restOptions
    } = options;

    const cacheKey = this.generateCacheKey(url, params, 'GET');
    
    // 性能监控
    if (this.options.enablePerformanceMonitoring) {
      this.performanceMonitor.mark(`api_start_${cacheKey}`);
    }

    // 检查缓存
    if (cache) {
      const cached = this.cache.get(cacheKey);
      if (cached !== null) {
        console.log(`Cache hit for GET ${url}`);
        if (this.options.enablePerformanceMonitoring) {
          this.performanceMonitor.mark(`api_end_${cacheKey}`);
          this.performanceMonitor.measure(`api_duration_${cacheKey}`, `api_start_${cacheKey}`, `api_end_${cacheKey}`);
        }
        return cached;
      }
    }

    // 防止重复请求
    if (this.pendingRequests.has(cacheKey)) {
      console.log(`Duplicate request detected for GET ${url}, waiting for existing request`);
      return this.pendingRequests.get(cacheKey);
    }

    // 创建请求Promise
    const requestPromise = this.executeRequest(() => 
      api.get(url, { params, ...restOptions }), retry
    );

    this.pendingRequests.set(cacheKey, requestPromise);

    try {
      const result = await requestPromise;
      
      // 缓存结果
      if (cache && result.data.success) {
        this.cache.set(cacheKey, result, cacheTTL);
        console.log(`Cache set for GET ${url}`);
      }

      if (this.options.enablePerformanceMonitoring) {
        this.performanceMonitor.mark(`api_end_${cacheKey}`);
        this.performanceMonitor.measure(`api_duration_${cacheKey}`, `api_start_${cacheKey}`, `api_end_${cacheKey}`);
      }

      return result;
    } finally {
      this.pendingRequests.delete(cacheKey);
    }
  }

  /**
   * 执行POST请求
   * @param {string} url - 请求URL
   * @param {Object} data - 请求数据
   * @param {Object} options - 请求选项
   * @returns {Promise} 请求结果
   */
  async post(url, data = {}, options = {}) {
    const {
      retry = this.options.enableRetry,
      invalidateCache = true,
      ...restOptions
    } = options;

    const cacheKey = `POST:${url}`;
    
    if (this.options.enablePerformanceMonitoring) {
      this.performanceMonitor.mark(`api_start_${cacheKey}`);
    }

    try {
      const result = await this.executeRequest(() => 
        api.post(url, data, restOptions), retry
      );

      // POST请求成功后，清除相关缓存
      if (invalidateCache && result.data.success) {
        this.invalidateRelatedCache(url);
      }

      if (this.options.enablePerformanceMonitoring) {
        this.performanceMonitor.mark(`api_end_${cacheKey}`);
        this.performanceMonitor.measure(`api_duration_${cacheKey}`, `api_start_${cacheKey}`, `api_end_${cacheKey}`);
      }

      return result;
    } catch (error) {
      if (this.options.enablePerformanceMonitoring) {
        this.performanceMonitor.mark(`api_error_${cacheKey}`);
      }
      throw error;
    }
  }

  /**
   * 执行PUT请求
   * @param {string} url - 请求URL
   * @param {Object} data - 请求数据
   * @param {Object} options - 请求选项
   * @returns {Promise} 请求结果
   */
  async put(url, data = {}, options = {}) {
    const {
      retry = this.options.enableRetry,
      invalidateCache = true,
      ...restOptions
    } = options;

    const result = await this.executeRequest(() => 
      api.put(url, data, restOptions), retry
    );

    // PUT请求成功后，清除相关缓存
    if (invalidateCache && result.data.success) {
      this.invalidateRelatedCache(url);
    }

    return result;
  }

  /**
   * 执行DELETE请求
   * @param {string} url - 请求URL
   * @param {Object} options - 请求选项
   * @returns {Promise} 请求结果
   */
  async delete(url, options = {}) {
    const {
      retry = this.options.enableRetry,
      invalidateCache = true,
      ...restOptions
    } = options;

    const result = await this.executeRequest(() => 
      api.delete(url, restOptions), retry
    );

    // DELETE请求成功后，清除相关缓存
    if (invalidateCache && result.data.success) {
      this.invalidateRelatedCache(url);
    }

    return result;
  }

  /**
   * 执行带重试的请求
   * @param {Function} requestFn - 请求函数
   * @param {boolean} enableRetry - 是否启用重试
   * @returns {Promise} 请求结果
   */
  async executeRequest(requestFn, enableRetry = true) {
    let lastError;
    const maxRetries = enableRetry ? this.options.maxRetries : 0;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await requestFn();
      } catch (error) {
        lastError = error;
        
        // 如果是最后一次尝试或者不应该重试的错误，直接抛出
        if (attempt === maxRetries || !this.shouldRetry(error)) {
          break;
        }

        // 等待后重试
        const delay = this.options.retryDelay * Math.pow(2, attempt); // 指数退避
        console.log(`Request failed, retrying in ${delay}ms (attempt ${attempt + 1}/${maxRetries + 1})`);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }

    throw lastError;
  }

  /**
   * 判断是否应该重试
   * @param {Error} error - 错误对象
   * @returns {boolean} 是否应该重试
   */
  shouldRetry(error) {
    // 网络错误或5xx服务器错误才重试
    if (!error.response) {
      return true; // 网络错误
    }

    const status = error.response.status;
    return status >= 500 || status === 408 || status === 429; // 服务器错误、超时、限流
  }

  /**
   * 清除相关缓存
   * @param {string} url - URL模式
   */
  invalidateRelatedCache(url) {
    const stats = this.cache.getStats();
    const keysToDelete = stats.keys.filter(key => key.includes(url.split('?')[0]));
    
    keysToDelete.forEach(key => {
      this.cache.delete(key);
      console.log(`Cache invalidated: ${key}`);
    });
  }

  /**
   * 批量请求
   * @param {Array} requests - 请求数组
   * @returns {Promise} 批量请求结果
   */
  async batchRequest(requests) {
    if (!this.options.enableBatch) {
      // 如果未启用批量请求，则并行执行
      return Promise.allSettled(requests.map(req => this.executeRequest(req.requestFn, req.retry)));
    }

    const promises = requests.map(req => 
      this.batchManager.add(() => this.executeRequest(req.requestFn, req.retry))
    );

    return Promise.allSettled(promises);
  }

  /**
   * 预加载数据
   * @param {Array} urls - 要预加载的URL数组
   * @param {Object} options - 预加载选项
   */
  async preload(urls, options = {}) {
    const {
      priority = 'low',
      delay = 100
    } = options;

    console.log(`Preloading ${urls.length} resources with ${priority} priority`);

    const requests = urls.map(url => ({
      requestFn: () => this.get(url, { cache: true }),
      retry: false
    }));

    // 低优先级预加载使用延迟
    if (priority === 'low') {
      await new Promise(resolve => setTimeout(resolve, delay));
    }

    return this.batchRequest(requests);
  }

  /**
   * 获取性能报告
   * @returns {Object} 性能报告
   */
  getPerformanceReport() {
    if (!this.options.enablePerformanceMonitoring) {
      return null;
    }

    const report = this.performanceMonitor.getReport();
    const cacheStats = this.cache.getStats();

    return {
      ...report,
      cache: cacheStats,
      pendingRequests: this.pendingRequests.size
    };
  }

  /**
   * 清除所有缓存
   */
  clearCache() {
    this.cache.clear();
    console.log('All cache cleared');
  }

  /**
   * 清除性能数据
   */
  clearPerformanceData() {
    if (this.options.enablePerformanceMonitoring) {
      this.performanceMonitor.clear();
    }
  }
}

/**
 * 创建专门的服务实例
 */

// 仪表板服务 - 启用缓存，较长TTL
export const dashboardApiService = new EnhancedApiService({
  enableCache: true,
  defaultCacheTTL: 600000, // 10分钟
  enableRetry: true,
  maxRetries: 2
});

// 交易服务 - 禁用缓存，启用重试
export const transactionApiService = new EnhancedApiService({
  enableCache: false,
  enableRetry: true,
  maxRetries: 3,
  retryDelay: 2000
});

// 汇率服务 - 启用缓存，中等TTL
export const rateApiService = new EnhancedApiService({
  enableCache: true,
  defaultCacheTTL: 300000, // 5分钟
  enableRetry: true,
  maxRetries: 2
});

// 用户服务 - 启用缓存，较短TTL
export const userApiService = new EnhancedApiService({
  enableCache: true,
  defaultCacheTTL: 180000, // 3分钟
  enableRetry: true,
  maxRetries: 2
});

// 系统服务 - 启用缓存，长TTL
export const systemApiService = new EnhancedApiService({
  enableCache: true,
  defaultCacheTTL: 900000, // 15分钟
  enableRetry: true,
  maxRetries: 1
});

/**
 * Vue组合式API钩子
 */
export function useEnhancedApi(serviceType = 'default') {
  const services = {
    default: new EnhancedApiService(),
    dashboard: dashboardApiService,
    transaction: transactionApiService,
    rate: rateApiService,
    user: userApiService,
    system: systemApiService
  };

  const service = services[serviceType] || services.default;

  return {
    get: service.get.bind(service),
    post: service.post.bind(service),
    put: service.put.bind(service),
    delete: service.delete.bind(service),
    batchRequest: service.batchRequest.bind(service),
    preload: service.preload.bind(service),
    clearCache: service.clearCache.bind(service),
    getPerformanceReport: service.getPerformanceReport.bind(service)
  };
}

/**
 * 防抖搜索钩子
 */
export function useDebouncedSearch(searchFn, delay = 500) {
  const debouncedSearch = debounce(searchFn, delay);
  
  return {
    search: debouncedSearch,
    immediateSearch: searchFn
  };
}

export default EnhancedApiService; 
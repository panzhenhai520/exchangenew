/**
 * 性能优化工具类
 * 提供缓存、防抖、节流、懒加载等性能优化功能
 */

/**
 * 内存缓存管理器
 */
export class CacheManager {
  constructor(maxSize = 100, defaultTTL = 300000) { // 默认5分钟过期
    this.cache = new Map();
    this.maxSize = maxSize;
    this.defaultTTL = defaultTTL;
    this.accessTimes = new Map(); // 记录访问时间，用于LRU
  }

  /**
   * 设置缓存
   * @param {string} key - 缓存键
   * @param {any} value - 缓存值
   * @param {number} ttl - 过期时间（毫秒）
   */
  set(key, value, ttl = this.defaultTTL) {
    // 如果缓存已满，删除最久未使用的项
    if (this.cache.size >= this.maxSize && !this.cache.has(key)) {
      this.evictLRU();
    }

    const expireTime = Date.now() + ttl;
    this.cache.set(key, { value, expireTime });
    this.accessTimes.set(key, Date.now());
  }

  /**
   * 获取缓存
   * @param {string} key - 缓存键
   * @returns {any} 缓存值或null
   */
  get(key) {
    const item = this.cache.get(key);
    if (!item) return null;

    // 检查是否过期
    if (Date.now() > item.expireTime) {
      this.delete(key);
      return null;
    }

    // 更新访问时间
    this.accessTimes.set(key, Date.now());
    return item.value;
  }

  /**
   * 删除缓存
   * @param {string} key - 缓存键
   */
  delete(key) {
    this.cache.delete(key);
    this.accessTimes.delete(key);
  }

  /**
   * 清空缓存
   */
  clear() {
    this.cache.clear();
    this.accessTimes.clear();
  }

  /**
   * 删除最久未使用的缓存项
   */
  evictLRU() {
    let oldestKey = null;
    let oldestTime = Date.now();

    for (const [key, time] of this.accessTimes) {
      if (time < oldestTime) {
        oldestTime = time;
        oldestKey = key;
      }
    }

    if (oldestKey) {
      this.delete(oldestKey);
    }
  }

  /**
   * 获取缓存统计信息
   */
  getStats() {
    return {
      size: this.cache.size,
      maxSize: this.maxSize,
      keys: Array.from(this.cache.keys())
    };
  }
}

/**
 * 防抖函数
 * @param {Function} func - 要防抖的函数
 * @param {number} delay - 延迟时间（毫秒）
 * @param {boolean} immediate - 是否立即执行
 * @returns {Function} 防抖后的函数
 */
export function debounce(func, delay = 300, immediate = false) {
  let timeoutId;
  
  return function debounced(...args) {
    const callNow = immediate && !timeoutId;
    
    clearTimeout(timeoutId);
    
    timeoutId = setTimeout(() => {
      timeoutId = null;
      if (!immediate) {
        func.apply(this, args);
      }
    }, delay);
    
    if (callNow) {
      func.apply(this, args);
    }
  };
}

/**
 * 节流函数
 * @param {Function} func - 要节流的函数
 * @param {number} limit - 限制时间间隔（毫秒）
 * @returns {Function} 节流后的函数
 */
export function throttle(func, limit = 300) {
  let inThrottle;
  let lastFunc;
  let lastRan;
  
  return function throttled(...args) {
    if (!inThrottle) {
      func.apply(this, args);
      lastRan = Date.now();
      inThrottle = true;
    } else {
      clearTimeout(lastFunc);
      lastFunc = setTimeout(() => {
        if ((Date.now() - lastRan) >= limit) {
          func.apply(this, args);
          lastRan = Date.now();
        }
      }, limit - (Date.now() - lastRan));
    }
  };
}

/**
 * 懒加载管理器
 */
export class LazyLoader {
  constructor(options = {}) {
    this.options = {
      rootMargin: '50px',
      threshold: 0.1,
      ...options
    };
    this.observer = null;
    this.callbacks = new Map();
    this.init();
  }

  init() {
    if ('IntersectionObserver' in window) {
      this.observer = new IntersectionObserver(
        this.handleIntersection.bind(this),
        this.options
      );
    }
  }

  /**
   * 观察元素
   * @param {Element} element - 要观察的元素
   * @param {Function} callback - 进入视口时的回调
   */
  observe(element, callback) {
    if (!this.observer) {
      // 不支持IntersectionObserver时立即执行
      callback();
      return;
    }

    this.callbacks.set(element, callback);
    this.observer.observe(element);
  }

  /**
   * 停止观察元素
   * @param {Element} element - 要停止观察的元素
   */
  unobserve(element) {
    if (this.observer) {
      this.observer.unobserve(element);
    }
    this.callbacks.delete(element);
  }

  /**
   * 处理交叉观察
   * @param {IntersectionObserverEntry[]} entries - 交叉观察条目
   */
  handleIntersection(entries) {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const callback = this.callbacks.get(entry.target);
        if (callback) {
          callback();
          this.unobserve(entry.target);
        }
      }
    });
  }

  /**
   * 销毁观察器
   */
  destroy() {
    if (this.observer) {
      this.observer.disconnect();
      this.observer = null;
    }
    this.callbacks.clear();
  }
}

/**
 * 请求缓存装饰器
 * @param {number} ttl - 缓存时间（毫秒）
 * @param {string} keyGenerator - 缓存键生成函数
 */
export function withCache(ttl = 300000, keyGenerator = null) {
  const cache = new CacheManager();
  
  return function decorator(target, propertyKey, descriptor) {
    const originalMethod = descriptor.value;
    
    descriptor.value = async function(...args) {
      // 生成缓存键
      const cacheKey = keyGenerator 
        ? keyGenerator(...args)
        : `${propertyKey}_${JSON.stringify(args)}`;
      
      // 尝试从缓存获取
      const cached = cache.get(cacheKey);
      if (cached !== null) {
        console.log(`Cache hit for ${cacheKey}`);
        return cached;
      }
      
      // 执行原方法
      const result = await originalMethod.apply(this, args);
      
      // 缓存结果
      cache.set(cacheKey, result, ttl);
      console.log(`Cache set for ${cacheKey}`);
      
      return result;
    };
    
    return descriptor;
  };
}

/**
 * 批量请求管理器
 */
export class BatchRequestManager {
  constructor(batchSize = 10, delay = 100) {
    this.batchSize = batchSize;
    this.delay = delay;
    this.queue = [];
    this.processing = false;
  }

  /**
   * 添加请求到批次
   * @param {Function} requestFn - 请求函数
   * @returns {Promise} 请求结果
   */
  add(requestFn) {
    return new Promise((resolve, reject) => {
      this.queue.push({ requestFn, resolve, reject });
      this.process();
    });
  }

  /**
   * 处理批次请求
   */
  async process() {
    if (this.processing || this.queue.length === 0) {
      return;
    }

    this.processing = true;

    while (this.queue.length > 0) {
      const batch = this.queue.splice(0, this.batchSize);
      
      try {
        // 并行执行批次中的请求
        const promises = batch.map(({ requestFn }) => requestFn());
        const results = await Promise.allSettled(promises);
        
        // 处理结果
        results.forEach((result, index) => {
          const { resolve, reject } = batch[index];
          if (result.status === 'fulfilled') {
            resolve(result.value);
          } else {
            reject(result.reason);
          }
        });
        
        // 批次间延迟
        if (this.queue.length > 0) {
          await new Promise(resolve => setTimeout(resolve, this.delay));
        }
      } catch (error) {
        // 处理批次错误
        batch.forEach(({ reject }) => reject(error));
      }
    }

    this.processing = false;
  }
}

/**
 * 虚拟滚动管理器
 */
export class VirtualScrollManager {
  constructor(options = {}) {
    this.options = {
      itemHeight: 50,
      containerHeight: 400,
      buffer: 5,
      ...options
    };
    this.scrollTop = 0;
    this.totalItems = 0;
  }

  /**
   * 计算可见范围
   * @param {number} scrollTop - 滚动位置
   * @param {number} totalItems - 总项目数
   * @returns {Object} 可见范围信息
   */
  getVisibleRange(scrollTop, totalItems) {
    this.scrollTop = scrollTop;
    this.totalItems = totalItems;

    const { itemHeight, containerHeight, buffer } = this.options;
    
    const visibleCount = Math.ceil(containerHeight / itemHeight);
    const startIndex = Math.floor(scrollTop / itemHeight);
    const endIndex = Math.min(startIndex + visibleCount, totalItems);
    
    // 添加缓冲区
    const bufferedStart = Math.max(0, startIndex - buffer);
    const bufferedEnd = Math.min(totalItems, endIndex + buffer);
    
    return {
      startIndex: bufferedStart,
      endIndex: bufferedEnd,
      visibleStartIndex: startIndex,
      visibleEndIndex: endIndex,
      offsetY: bufferedStart * itemHeight,
      totalHeight: totalItems * itemHeight
    };
  }
}

/**
 * 性能监控器
 */
export class PerformanceMonitor {
  constructor() {
    this.marks = new Map();
    this.measures = new Map();
  }

  /**
   * 标记性能点
   * @param {string} name - 标记名称
   */
  mark(name) {
    const timestamp = performance.now();
    this.marks.set(name, timestamp);
    
    if (performance.mark) {
      performance.mark(name);
    }
  }

  /**
   * 测量性能
   * @param {string} name - 测量名称
   * @param {string} startMark - 开始标记
   * @param {string} endMark - 结束标记
   * @returns {number} 耗时（毫秒）
   */
  measure(name, startMark, endMark = null) {
    const startTime = this.marks.get(startMark);
    const endTime = endMark ? this.marks.get(endMark) : performance.now();
    
    if (!startTime) {
      console.warn(`Start mark "${startMark}" not found`);
      return 0;
    }
    
    const duration = endTime - startTime;
    this.measures.set(name, duration);
    
    if (performance.measure) {
      try {
        // 只有当endMark存在且有效时才使用浏览器原生API
        if (endMark && this.marks.has(endMark)) {
          performance.measure(name, startMark, endMark);
        } else {
          // 使用当前时间作为结束点
          const endMarkName = `${name}_end_${Date.now()}`;
          performance.mark(endMarkName);
          performance.measure(name, startMark, endMarkName);
        }
      } catch (e) {
        console.warn('Performance measure failed:', e);
      }
    }
    
    return duration;
  }

  /**
   * 获取测量结果
   * @param {string} name - 测量名称
   * @returns {number} 耗时（毫秒）
   */
  getMeasure(name) {
    return this.measures.get(name) || 0;
  }

  /**
   * 清除标记和测量
   */
  clear() {
    this.marks.clear();
    this.measures.clear();
    
    if (performance.clearMarks) {
      performance.clearMarks();
    }
    if (performance.clearMeasures) {
      performance.clearMeasures();
    }
  }

  /**
   * 获取性能报告
   * @returns {Object} 性能报告
   */
  getReport() {
    return {
      marks: Object.fromEntries(this.marks),
      measures: Object.fromEntries(this.measures),
      memory: this.getMemoryInfo(),
      timing: this.getTimingInfo()
    };
  }

  /**
   * 获取内存信息
   * @returns {Object} 内存信息
   */
  getMemoryInfo() {
    if (performance.memory) {
      return {
        usedJSHeapSize: performance.memory.usedJSHeapSize,
        totalJSHeapSize: performance.memory.totalJSHeapSize,
        jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
      };
    }
    return null;
  }

  /**
   * 获取页面时序信息
   * @returns {Object} 时序信息
   */
  getTimingInfo() {
    if (performance.timing) {
      const timing = performance.timing;
      return {
        domContentLoaded: timing.domContentLoadedEventEnd - timing.navigationStart,
        loadComplete: timing.loadEventEnd - timing.navigationStart,
        domReady: timing.domComplete - timing.navigationStart
      };
    }
    return null;
  }
}

// 创建全局实例
export const globalCache = new CacheManager();
export const globalLazyLoader = new LazyLoader();
export const globalBatchManager = new BatchRequestManager();
export const globalPerformanceMonitor = new PerformanceMonitor();

/**
 * Vue组合式API钩子
 */
export function usePerformance() {
  return {
    cache: globalCache,
    lazyLoader: globalLazyLoader,
    batchManager: globalBatchManager,
    performanceMonitor: globalPerformanceMonitor,
    debounce,
    throttle
  };
}

/**
 * 图片懒加载指令
 */
export const lazyImageDirective = {
  mounted(el, binding) {
    const imageUrl = binding.value;
    const placeholder = binding.arg || 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iI2Y4ZjlmYSIvPjx0ZXh0IHg9IjUwIiB5PSI1NSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE0IiBmaWxsPSIjNmM3NTdkIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5sb2FkaW5nLi4uPC90ZXh0Pjwvc3ZnPg==';
    
    el.src = placeholder;
    
    globalLazyLoader.observe(el, () => {
      const img = new Image();
      img.onload = () => {
        el.src = imageUrl;
        el.classList.add('loaded');
      };
      img.onerror = () => {
        el.classList.add('error');
      };
      img.src = imageUrl;
    });
  },
  
  unmounted(el) {
    globalLazyLoader.unobserve(el);
  }
}; 
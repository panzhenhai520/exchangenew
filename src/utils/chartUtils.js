/**
 * Chart.js 工具类 - 用于安全地创建和清理图表
 * 解决Vue组件快速切换时的内存泄漏问题
 */

export class ChartManager {
  constructor() {
    this.charts = new Map();
    this.componentStates = new Map();
    this.pendingOperations = new Map(); // 跟踪待处理的操作
    this.debounceTimeouts = new Map(); // 防抖定时器
  }

  /**
   * 注册组件状态
   * @param {string} componentId - 组件唯一标识
   * @param {object} componentRef - 组件引用
   */
  registerComponent(componentId, componentRef) {
    console.log(`Registering component: ${componentId}`);
    this.componentStates.set(componentId, {
      isMounted: true,
      componentRef: componentRef,
      lastActivity: Date.now()
    });
  }

  /**
   * 检查组件是否还挂载
   * @param {string} componentId - 组件唯一标识
   * @returns {boolean}
   */
  isComponentMounted(componentId) {
    const state = this.componentStates.get(componentId);
    return state ? state.isMounted : false;
  }

  /**
   * 取消待处理的操作
   * @param {string} componentId - 组件唯一标识
   */
  cancelPendingOperations(componentId) {
    const pending = this.pendingOperations.get(componentId);
    if (pending) {
      pending.cancelled = true;
      this.pendingOperations.delete(componentId);
    }

    const timeout = this.debounceTimeouts.get(componentId);
    if (timeout) {
      clearTimeout(timeout);
      this.debounceTimeouts.delete(componentId);
    }
  }

  /**
   * 防抖创建图表
   * @param {string} componentId - 组件唯一标识
   * @param {string} containerId - 容器元素ID或引用
   * @param {object} config - Chart.js配置
   * @param {function} Chart - Chart.js构造函数
   * @param {number} delay - 防抖延迟时间（毫秒）
   * @returns {Promise<object|null>} 图表实例或null
   */
  async createChartDebounced(componentId, containerId, config, Chart, delay = 150) {
    // 取消之前的操作
    this.cancelPendingOperations(componentId);

    return new Promise((resolve) => {
      const timeout = setTimeout(async () => {
        this.debounceTimeouts.delete(componentId);
        const chart = await this.createChart(componentId, containerId, config, Chart);
        resolve(chart);
      }, delay);

      this.debounceTimeouts.set(componentId, timeout);
    });
  }

  /**
   * 安全创建图表
   * @param {string} componentId - 组件唯一标识
   * @param {string|Element} container - 容器元素ID或DOM元素
   * @param {object} config - Chart.js配置
   * @param {function} Chart - Chart.js构造函数
   * @returns {object|null} 图表实例或null
   */
  async createChart(componentId, container, config, Chart) {
    try {
      console.log(`Creating chart for component: ${componentId}`);
      
      // 创建操作跟踪
      const operation = { cancelled: false, startTime: Date.now() };
      this.pendingOperations.set(componentId, operation);

      // 检查组件是否还挂载
      if (!this.isComponentMounted(componentId)) {
        console.log(`Component ${componentId} is not mounted, skipping chart creation`);
        return null;
      }

      // 清理现有图表
      this.destroyChart(componentId);

      // 检查操作是否被取消
      if (operation.cancelled) {
        console.log(`Chart creation cancelled for component: ${componentId}`);
        return null;
      }

      // 获取容器元素
      let containerElement;
      if (typeof container === 'string') {
        containerElement = document.getElementById(container);
      } else if (container && container.value) {
        containerElement = container.value; // Vue ref
      } else {
        containerElement = container; // DOM元素
      }

      if (!containerElement) {
        console.error(`Container not found for component: ${componentId}`);
        return null;
      }

      // 检查容器是否在DOM中
      if (!document.contains(containerElement)) {
        console.error(`Container not in DOM for component: ${componentId}`);
        return null;
      }

      // 再次检查组件状态和操作状态
      if (!this.isComponentMounted(componentId) || operation.cancelled) {
        console.log(`Component unmounted or operation cancelled during container check: ${componentId}`);
        return null;
      }

      // 清理容器内容
      containerElement.innerHTML = '';

      // 创建canvas元素
      const canvas = document.createElement('canvas');
      const canvasId = `chart_${componentId}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      canvas.id = canvasId;
      canvas.style.width = '100%';
      canvas.style.height = '100%';
      
      // 添加canvas到容器
      containerElement.appendChild(canvas);

      // 等待DOM更新
      await new Promise(resolve => requestAnimationFrame(() => {
        requestAnimationFrame(resolve);
      }));

      // 检查操作是否被取消
      if (operation.cancelled || !this.isComponentMounted(componentId)) {
        console.log(`Operation cancelled or component unmounted during DOM update: ${componentId}`);
        return null;
      }

      // 获取上下文
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        console.error(`Failed to get context for component: ${componentId}`);
        return null;
      }

      // 确保动画配置安全
      if (!config.options) {
        config.options = {};
      }
      if (!config.options.animation) {
        config.options.animation = {};
      }
      
      // 根据组件状态设置动画
      config.options.animation.duration = this.isComponentMounted(componentId) ? 
        (config.options.animation.duration || 800) : 0;

      // 最后检查操作状态
      if (operation.cancelled || !this.isComponentMounted(componentId)) {
        console.log(`Final check failed for component: ${componentId}`);
        return null;
      }

      // 创建图表
      const chart = new Chart(ctx, config);
      
      // 存储图表引用
      this.charts.set(componentId, chart);
      this.pendingOperations.delete(componentId);
      
      console.log(`Chart created successfully for component: ${componentId}`);
      return chart;

    } catch (error) {
      console.error(`Error creating chart for component ${componentId}:`, error);
      this.destroyChart(componentId);
      this.pendingOperations.delete(componentId);
      return null;
    }
  }

  /**
   * 安全销毁图表
   * @param {string} componentId - 组件唯一标识
   */
  destroyChart(componentId) {
    console.log(`Destroying chart for component: ${componentId}`);
    
    // 取消待处理的操作
    this.cancelPendingOperations(componentId);

    const chart = this.charts.get(componentId);
    if (chart) {
      try {
        // 停止所有动画
        if (typeof chart.stop === 'function') {
          chart.stop();
        }
        // 销毁图表
        if (typeof chart.destroy === 'function') {
          chart.destroy();
        }
        console.log(`Chart destroyed successfully for component: ${componentId}`);
      } catch (error) {
        console.warn(`Chart destroy error for component ${componentId} (non-critical):`, error);
      } finally {
        this.charts.delete(componentId);
      }
    }
  }

  /**
   * 组件卸载时调用
   * @param {string} componentId - 组件唯一标识
   */
  onComponentUnmount(componentId) {
    console.log(`Component ${componentId} is being unmounted`);
    
    // 更新组件状态
    const state = this.componentStates.get(componentId);
    if (state) {
      state.isMounted = false;
    }

    // 取消所有待处理的操作
    this.cancelPendingOperations(componentId);

    // 销毁图表
    this.destroyChart(componentId);
    
    // 延迟清理组件状态，避免竞态条件
    setTimeout(() => {
      this.componentStates.delete(componentId);
      console.log(`Component state cleaned up for: ${componentId}`);
    }, 2000);
  }

  /**
   * 获取图表实例
   * @param {string} componentId - 组件唯一标识
   * @returns {object|null}
   */
  getChart(componentId) {
    return this.charts.get(componentId) || null;
  }

  /**
   * 清理所有图表
   */
  destroyAll() {
    console.log('Destroying all charts');
    for (const componentId of this.charts.keys()) {
      this.destroyChart(componentId);
    }
    // 清理所有待处理的操作
    for (const componentId of this.pendingOperations.keys()) {
      this.cancelPendingOperations(componentId);
    }
    this.componentStates.clear();
  }

  /**
   * 获取组件状态信息（用于调试）
   */
  getDebugInfo() {
    return {
      charts: Array.from(this.charts.keys()),
      components: Array.from(this.componentStates.keys()),
      pendingOperations: Array.from(this.pendingOperations.keys()),
      debounceTimeouts: Array.from(this.debounceTimeouts.keys())
    };
  }
}

// 创建全局实例
export const chartManager = new ChartManager();

// 在窗口卸载时清理所有图表
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    chartManager.destroyAll();
  });

  // 添加调试功能（仅在开发环境）
  if (process.env.NODE_ENV === 'development') {
    window.chartManagerDebug = () => chartManager.getDebugInfo();
  }
}

/**
 * Vue组合式API hook，用于在组件中使用图表管理器
 * @param {string} componentName - 组件名称
 * @returns {object} 图表管理相关方法
 */
export function useChartManager(componentName) {
  const componentId = `${componentName}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  
  const registerComponent = () => {
    chartManager.registerComponent(componentId, null);
  };

  const createChart = async (container, config, Chart) => {
    return await chartManager.createChart(componentId, container, config, Chart);
  };

  const createChartDebounced = async (container, config, Chart, delay = 150) => {
    return await chartManager.createChartDebounced(componentId, container, config, Chart, delay);
  };

  const destroyChart = () => {
    chartManager.destroyChart(componentId);
  };

  const onUnmount = () => {
    chartManager.onComponentUnmount(componentId);
  };

  const getChart = () => {
    return chartManager.getChart(componentId);
  };

  const isComponentMounted = () => {
    return chartManager.isComponentMounted(componentId);
  };

  return {
    componentId,
    registerComponent,
    createChart,
    createChartDebounced,
    destroyChart,
    onUnmount,
    getChart,
    isComponentMounted
  };
} 
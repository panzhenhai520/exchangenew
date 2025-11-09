<template>
  <div class="performance-monitor" v-if="showMonitor">
    <div class="monitor-header">
      <h6 class="mb-0">
        <i class="fas fa-tachometer-alt me-2"></i>
        性能监控
      </h6>
      <div class="monitor-controls">
        <button 
          class="btn btn-sm btn-outline-secondary me-2"
          @click="refreshData"
          :disabled="refreshing"
        >
          <i class="fas fa-sync" :class="{ 'fa-spin': refreshing }"></i>
        </button>
        <button 
          class="btn btn-sm btn-outline-danger me-2"
          @click="clearData"
        >
          <i class="fas fa-trash"></i>
        </button>
        <button 
          class="btn btn-sm btn-outline-secondary"
          @click="toggleMinimize"
        >
          <i class="fas" :class="minimized ? 'fa-expand' : 'fa-compress'"></i>
        </button>
      </div>
    </div>
    
    <div class="monitor-content" v-if="!minimized">
      <!-- 基本性能指标 -->
      <div class="performance-section">
        <h6 class="section-title">基本指标</h6>
        <div class="metrics-grid">
          <div class="metric-item">
            <div class="metric-label">页面加载时间</div>
            <div class="metric-value" :class="getPerformanceClass(timing.loadComplete)">
              {{ formatDuration(timing.loadComplete) }}
            </div>
          </div>
          <div class="metric-item">
            <div class="metric-label">DOM就绪时间</div>
            <div class="metric-value" :class="getPerformanceClass(timing.domReady)">
              {{ formatDuration(timing.domReady) }}
            </div>
          </div>
          <div class="metric-item">
            <div class="metric-label">内存使用</div>
            <div class="metric-value" :class="getMemoryClass(memory.usedJSHeapSize)">
              {{ formatMemory(memory.usedJSHeapSize) }}
            </div>
          </div>
          <div class="metric-item">
            <div class="metric-label">缓存命中率</div>
            <div class="metric-value" :class="getCacheHitRateClass(cacheStats.hitRate)">
              {{ (cacheStats.hitRate * 100).toFixed(1) }}%
            </div>
          </div>
        </div>
      </div>
      
      <!-- API性能 -->
      <div class="performance-section" v-if="apiMetrics.length > 0">
        <h6 class="section-title">API性能</h6>
        <div class="api-metrics">
          <div 
            v-for="metric in apiMetrics.slice(0, 5)" 
            :key="metric.name"
            class="api-metric-item"
          >
            <div class="api-name">{{ metric.name }}</div>
            <div class="api-duration" :class="getPerformanceClass(metric.duration)">
              {{ formatDuration(metric.duration) }}
            </div>
            <div class="api-status" :class="metric.status === 'success' ? 'text-success' : 'text-danger'">
              <i class="fas" :class="metric.status === 'success' ? 'fa-check' : 'fa-times'"></i>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 缓存统计 -->
      <div class="performance-section">
        <h6 class="section-title">缓存统计</h6>
        <div class="cache-stats">
          <div class="cache-stat">
            <span class="stat-label">缓存大小:</span>
            <span class="stat-value">{{ cacheStats.size }}/{{ cacheStats.maxSize }}</span>
          </div>
          <div class="cache-stat">
            <span class="stat-label">命中次数:</span>
            <span class="stat-value text-success">{{ cacheStats.hits }}</span>
          </div>
          <div class="cache-stat">
            <span class="stat-label">未命中次数:</span>
            <span class="stat-value text-warning">{{ cacheStats.misses }}</span>
          </div>
        </div>
      </div>
      
      <!-- 实时图表 -->
      <div class="performance-section" v-if="showChart">
        <h6 class="section-title">性能趋势</h6>
        <div class="performance-chart">
          <canvas ref="performanceChart" width="300" height="100"></canvas>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue';
import { usePerformance } from '@/utils/performance';

export default {
  name: 'PerformanceMonitor',
  props: {
    autoRefresh: {
      type: Boolean,
      default: true
    },
    refreshInterval: {
      type: Number,
      default: 5000 // 5秒
    },
    showChart: {
      type: Boolean,
      default: false
    },
    position: {
      type: String,
      default: 'bottom-right',
      validator: value => ['top-left', 'top-right', 'bottom-left', 'bottom-right'].includes(value)
    }
  },
  setup(props) {
    const showMonitor = ref(process.env.NODE_ENV === 'development');
    const minimized = ref(false);
    const refreshing = ref(false);
    const performanceChart = ref(null);
    
    const { performanceMonitor, cache } = usePerformance();
    
    // 性能数据
    const timing = ref({
      loadComplete: 0,
      domReady: 0,
      domContentLoaded: 0
    });
    
    const memory = ref({
      usedJSHeapSize: 0,
      totalJSHeapSize: 0,
      jsHeapSizeLimit: 0
    });
    
    const cacheStats = ref({
      size: 0,
      maxSize: 0,
      hits: 0,
      misses: 0,
      hitRate: 0
    });
    
    const apiMetrics = ref([]);
    const refreshTimer = ref(null);
    
    // 计算属性
    const positionClass = computed(() => {
      const positions = {
        'top-left': 'position-top-left',
        'top-right': 'position-top-right',
        'bottom-left': 'position-bottom-left',
        'bottom-right': 'position-bottom-right'
      };
      return positions[props.position] || positions['bottom-right'];
    });
    
    // 获取性能数据
    const refreshData = async () => {
      refreshing.value = true;
      
      try {
        // 获取性能报告
        const report = performanceMonitor.getReport();
        
        // 更新时序信息
        if (report.timing) {
          timing.value = { ...report.timing };
        }
        
        // 更新内存信息
        if (report.memory) {
          memory.value = { ...report.memory };
        }
        
        // 更新缓存统计
        const stats = cache.getStats();
        const totalRequests = cacheStats.value.hits + cacheStats.value.misses;
        cacheStats.value = {
          ...stats,
          hits: cacheStats.value.hits,
          misses: cacheStats.value.misses,
          hitRate: totalRequests > 0 ? cacheStats.value.hits / totalRequests : 0
        };
        
        // 更新API指标
        if (report.measures) {
          const newMetrics = Object.entries(report.measures)
            .filter(([name]) => name.includes('api_duration'))
            .map(([name, duration]) => ({
              name: name.replace('api_duration_', '').replace(/_/g, ' '),
              duration,
              status: 'success',
              timestamp: Date.now()
            }))
            .sort((a, b) => b.timestamp - a.timestamp);
          
          apiMetrics.value = newMetrics;
        }
        
      } catch (error) {
        console.error('Failed to refresh performance data:', error);
      } finally {
        refreshing.value = false;
      }
    };
    
    // 清除数据
    const clearData = () => {
      performanceMonitor.clear();
      cache.clear();
      apiMetrics.value = [];
      cacheStats.value.hits = 0;
      cacheStats.value.misses = 0;
      cacheStats.value.hitRate = 0;
    };
    
    // 切换最小化状态
    const toggleMinimize = () => {
      minimized.value = !minimized.value;
    };
    
    // 格式化持续时间
    const formatDuration = (ms) => {
      if (!ms || ms === 0) return '0ms';
      if (ms < 1000) return `${Math.round(ms)}ms`;
      return `${(ms / 1000).toFixed(2)}s`;
    };
    
    // 格式化内存大小
    const formatMemory = (bytes) => {
      if (!bytes || bytes === 0) return '0B';
      const units = ['B', 'KB', 'MB', 'GB'];
      let size = bytes;
      let unitIndex = 0;
      
      while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
      }
      
      return `${size.toFixed(1)}${units[unitIndex]}`;
    };
    
    // 获取性能等级样式
    const getPerformanceClass = (duration) => {
      if (!duration) return '';
      if (duration < 100) return 'text-success';
      if (duration < 500) return 'text-warning';
      return 'text-danger';
    };
    
    // 获取内存等级样式
    const getMemoryClass = (bytes) => {
      if (!bytes) return '';
      const mb = bytes / (1024 * 1024);
      if (mb < 50) return 'text-success';
      if (mb < 100) return 'text-warning';
      return 'text-danger';
    };
    
    // 获取缓存命中率样式
    const getCacheHitRateClass = (rate) => {
      if (rate >= 0.8) return 'text-success';
      if (rate >= 0.6) return 'text-warning';
      return 'text-danger';
    };
    
    // 监听缓存事件
    const originalCacheGet = cache.get.bind(cache);
    const originalCacheSet = cache.set.bind(cache);
    
    cache.get = function(key) {
      const result = originalCacheGet(key);
      if (result !== null) {
        cacheStats.value.hits++;
      } else {
        cacheStats.value.misses++;
      }
      return result;
    };
    
    cache.set = function(key, value, ttl) {
      return originalCacheSet(key, value, ttl);
    };
    
    onMounted(() => {
      // 初始加载数据
      refreshData();
      
      // 设置自动刷新
      if (props.autoRefresh) {
        refreshTimer.value = setInterval(refreshData, props.refreshInterval);
      }
    });
    
    onBeforeUnmount(() => {
      // 清理定时器
      if (refreshTimer.value) {
        clearInterval(refreshTimer.value);
      }
      
      // 恢复原始缓存方法
      cache.get = originalCacheGet;
      cache.set = originalCacheSet;
    });
    
    return {
      showMonitor,
      minimized,
      refreshing,
      performanceChart,
      timing,
      memory,
      cacheStats,
      apiMetrics,
      positionClass,
      refreshData,
      clearData,
      toggleMinimize,
      formatDuration,
      formatMemory,
      getPerformanceClass,
      getMemoryClass,
      getCacheHitRateClass
    };
  }
};
</script>

<style scoped>
.performance-monitor {
  position: fixed;
  z-index: 9999;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  font-size: 0.75rem;
  max-width: 350px;
  min-width: 280px;
}

.position-top-left {
  top: 20px;
  left: 20px;
}

.position-top-right {
  top: 20px;
  right: 20px;
}

.position-bottom-left {
  bottom: 20px;
  left: 20px;
}

.position-bottom-right {
  bottom: 20px;
  right: 20px;
}

.monitor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #f8f9fa;
  border-bottom: 1px solid #e0e0e0;
  border-radius: 8px 8px 0 0;
}

.monitor-controls {
  display: flex;
  align-items: center;
}

.monitor-content {
  padding: 12px;
  max-height: 400px;
  overflow-y: auto;
}

.performance-section {
  margin-bottom: 16px;
}

.performance-section:last-child {
  margin-bottom: 0;
}

.section-title {
  font-size: 0.7rem;
  font-weight: 600;
  color: #666;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.metric-item {
  background: #f8f9fa;
  padding: 6px 8px;
  border-radius: 4px;
  border: 1px solid #e9ecef;
}

.metric-label {
  font-size: 0.65rem;
  color: #666;
  margin-bottom: 2px;
}

.metric-value {
  font-size: 0.75rem;
  font-weight: 600;
}

.api-metrics {
  space-y: 4px;
}

.api-metric-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 8px;
  background: #f8f9fa;
  border-radius: 4px;
  border: 1px solid #e9ecef;
  margin-bottom: 4px;
}

.api-name {
  flex: 1;
  font-size: 0.65rem;
  color: #666;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.api-duration {
  font-size: 0.7rem;
  font-weight: 600;
  margin: 0 8px;
}

.api-status {
  font-size: 0.7rem;
}

.cache-stats {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.cache-stat {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 8px;
  background: #f8f9fa;
  border-radius: 4px;
  border: 1px solid #e9ecef;
}

.stat-label {
  font-size: 0.65rem;
  color: #666;
}

.stat-value {
  font-size: 0.7rem;
  font-weight: 600;
}

.performance-chart {
  background: #f8f9fa;
  border-radius: 4px;
  padding: 8px;
  border: 1px solid #e9ecef;
}

/* 滚动条样式 */
.monitor-content::-webkit-scrollbar {
  width: 4px;
}

.monitor-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 2px;
}

.monitor-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 2px;
}

.monitor-content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .performance-monitor {
    max-width: 280px;
    min-width: 250px;
  }
  
  .metrics-grid {
    grid-template-columns: 1fr;
  }
}
</style> 
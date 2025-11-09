<template>
  <div class="async-chart-container" :style="{ height: height }">
    <!-- 图表容器 - 始终存在 -->
    <div 
      ref="chartContainer" 
      class="chart-container"
      :class="{ 'chart-ready': isChartReady }"
    >
      <!-- 加载状态 -->
      <div v-if="isLoading" class="chart-loading">
        <div class="loading-spinner">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">{{ $t('rates.chart_loading') }}</span>
          </div>
        </div>
        <div class="loading-text">{{ loadingText }}</div>
        <div class="loading-progress">
          <div class="progress">
            <div 
              class="progress-bar progress-bar-animated" 
              :style="{ width: loadingProgress + '%' }"
            ></div>
          </div>
        </div>
      </div>

      <!-- 错误状态 -->
      <div v-else-if="hasError" class="chart-error">
        <div class="error-icon">
          <i class="fas fa-exclamation-triangle text-warning"></i>
        </div>
        <div class="error-message">{{ errorMessage }}</div>
        <button class="btn btn-outline-primary btn-sm mt-2" @click="retryLoad">
          <i class="fas fa-sync"></i> {{ $t('rates.chart_retry') }}
        </button>
      </div>

      <!-- Canvas将在这里动态创建（当图表准备好时） -->
    </div>

    <!-- 图表工具栏 -->
    <div v-if="showToolbar && isChartReady" class="chart-toolbar">
      <button 
        class="btn btn-outline-secondary btn-sm" 
        @click="refreshChart"
        :disabled="isRefreshing"
      >
        <i class="fas fa-sync" :class="{ 'fa-spin': isRefreshing }"></i>
        {{ $t('rates.chart_refresh') }}
      </button>
      <button 
        class="btn btn-outline-secondary btn-sm ms-2" 
        @click="downloadChart"
      >
        <i class="fas fa-download"></i>
        {{ $t('rates.chart_download') }}
      </button>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import { useI18n } from 'vue-i18n';
import { 
  Chart,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  LineController
} from 'chart.js';

// 注册Chart.js组件
Chart.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  LineController
);

export default {
  name: 'AsyncChart',
  props: {
    chartData: {
      type: Object,
      default: () => ({})
    },
    chartOptions: {
      type: Object,
      default: () => ({})
    },
    height: {
      type: String,
      default: '400px'
    },
    loadingDelay: {
      type: Number,
      default: 300
    },
    showToolbar: {
      type: Boolean,
      default: false
    },
    autoRefresh: {
      type: Boolean,
      default: false
    },
    refreshInterval: {
      type: Number,
      default: 60000 // 1分钟
    }
  },
  emits: ['chart-ready', 'chart-error', 'chart-refresh'],
  setup(props, { emit }) {
    const { t } = useI18n();
    const chartContainer = ref(null);
    const chart = ref(null);
    const isLoading = ref(true);
    const isChartReady = ref(false);
    const hasError = ref(false);
    const errorMessage = ref('');
    const loadingText = ref(t('rates.chart_initializing'));
    const loadingProgress = ref(0);
    const isRefreshing = ref(false);
    const isComponentMounted = ref(false);
    const isCreating = ref(false);
    
    // 定时器和延迟处理
    const loadingTimer = ref(null);
    const progressTimer = ref(null);
    const refreshTimer = ref(null);
    const retryTimer = ref(null);
    
    // 防抖定时器
    const debounceTimer = ref(null);

    // 组件唯一ID
    const componentId = `AsyncChart_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    // 清理所有定时器
    const clearAllTimers = () => {
      [loadingTimer, progressTimer, refreshTimer, retryTimer, debounceTimer].forEach(timer => {
        if (timer.value) {
          clearTimeout(timer.value);
          timer.value = null;
        }
      });
    };

    // 模拟加载进度
    const simulateLoadingProgress = () => {
      const steps = [
        { progress: 20, text: t('rates.chart_loading_data') },
        { progress: 40, text: t('rates.chart_preparing') },
        { progress: 60, text: t('rates.chart_rendering') },
        { progress: 80, text: t('rates.chart_optimizing') },
        { progress: 100, text: t('rates.chart_loading_complete') }
      ];

      let currentStep = 0;
      
      const updateProgress = () => {
        if (!isComponentMounted.value || !isLoading.value) {
          return;
        }
        
        if (currentStep < steps.length) {
          const step = steps[currentStep];
          loadingProgress.value = step.progress;
          loadingText.value = step.text;
          currentStep++;
          
          progressTimer.value = setTimeout(updateProgress, 200 + Math.random() * 300);
        }
      };
      
      progressTimer.value = setTimeout(updateProgress, 100);
    };

    // 异步创建图表
    const createChartAsync = async () => {
      // 防止并发创建
      if (isCreating.value) {
        console.log(`[${componentId}] Chart creation already in progress, skipping`);
        return;
      }

      isCreating.value = true;

      try {
        console.log(`[${componentId}] Starting async chart creation`);
        console.log(`[${componentId}] Chart data:`, props.chartData);
        console.log(`[${componentId}] Chart options:`, props.chartOptions);
        
        if (!isComponentMounted.value) {
          console.log(`[${componentId}] Component not mounted, aborting`);
          return;
        }

        // 检查数据是否有效
        if (!props.chartData) {
          console.log(`[${componentId}] No chart data provided`);
          hasError.value = true;
          errorMessage.value = '未提供图表数据';
          isLoading.value = false;
          return;
        }

        if (!props.chartData.labels) {
          console.log(`[${componentId}] No labels in chart data`);
          hasError.value = true;
          errorMessage.value = '图表数据缺少标签';
          isLoading.value = false;
          return;
        }

        if (!props.chartData.datasets) {
          console.log(`[${componentId}] No datasets in chart data`);
          hasError.value = true;
          errorMessage.value = '图表数据缺少数据集';
          isLoading.value = false;
          return;
        }

        if (props.chartData.labels.length === 0) {
          console.log(`[${componentId}] Empty labels array`);
          hasError.value = true;
          errorMessage.value = t('rates.chart_no_historical_data');
          isLoading.value = false;
          return;
        }

        if (props.chartData.datasets.length === 0) {
          console.log(`[${componentId}] Empty datasets array`);
          hasError.value = true;
          errorMessage.value = '图表数据集为空';
          isLoading.value = false;
          return;
        }

        // 重置状态
        isLoading.value = true;
        hasError.value = false;
        isChartReady.value = false;
        loadingProgress.value = 0;
        
        // 开始进度模拟
        simulateLoadingProgress();

        // 等待最小加载时间
        await new Promise(resolve => {
          loadingTimer.value = setTimeout(resolve, Math.max(props.loadingDelay, 500));
        });

        if (!isComponentMounted.value) {
          console.log(`[${componentId}] Component unmounted during delay`);
          return;
        }

        // 销毁现有图表
        if (chart.value) {
          try {
            // 立即停止所有动画
            chart.value.stop();
            
            // 强制清除动画状态
            if (chart.value.animator) {
              chart.value.animator.stop();
            }
            
            // 销毁图表实例
            chart.value.destroy();
            
            console.log(`[${componentId}] Chart destroyed successfully`);
          } catch (error) {
            console.warn(`[${componentId}] Error during cleanup:`, error);
          } finally {
            chart.value = null;
          }
        }

        // 等待DOM准备
        await nextTick();
        await new Promise(resolve => requestAnimationFrame(resolve));

        if (!isComponentMounted.value) {
          console.log(`[${componentId}] Component unmounted during DOM wait`);
          return;
        }

        // 检查容器 - 增加重试机制
        let container = chartContainer.value;
        let retries = 0;
        const maxRetries = 10;

        while ((!container || !document.contains(container)) && retries < maxRetries && isComponentMounted.value) {
          console.log(`[${componentId}] Container not ready, retry ${retries + 1}/${maxRetries}`);
          await new Promise(resolve => setTimeout(resolve, 100));
          await nextTick();
          container = chartContainer.value;
          retries++;
        }

        if (!container) {
          throw new Error('图表容器未找到');
        }

        if (!document.contains(container)) {
          throw new Error('图表容器不在DOM中');
        }

        console.log(`[${componentId}] Container found successfully after ${retries} retries`);

        // 安全清理容器 - 避免与Vue虚拟DOM冲突
        const existingCanvas = container.querySelector('canvas');
        if (existingCanvas) {
          console.log(`[${componentId}] Removing existing canvas`);
          try {
            existingCanvas.remove();
          } catch (error) {
            console.warn(`[${componentId}] Error removing existing canvas:`, error);
          }
        }

        // 再次检查组件状态
        if (!isComponentMounted.value) {
          console.log(`[${componentId}] Component unmounted during canvas cleanup`);
          return;
        }

        // 再次检查容器有效性
        if (!chartContainer.value || !document.contains(chartContainer.value)) {
          throw new Error('容器在操作过程中变为无效');
        }

        // 创建canvas
        const canvas = document.createElement('canvas');
        canvas.id = `chart_${componentId}`;
        canvas.style.width = '100%';
        canvas.style.height = '100%';
        
        // 安全添加canvas
        try {
          chartContainer.value.appendChild(canvas);
          console.log(`[${componentId}] Canvas added successfully`);
        } catch (error) {
          console.error(`[${componentId}] Error appending canvas:`, error);
          throw new Error('无法添加Canvas元素');
        }

        // 再次等待DOM更新
        await new Promise(resolve => requestAnimationFrame(resolve));

        if (!isComponentMounted.value) {
          console.log(`[${componentId}] Component unmounted during canvas creation`);
          return;
        }

        // 获取上下文
        const ctx = canvas.getContext('2d');
        if (!ctx) {
          throw new Error('无法获取Canvas上下文');
        }

        // 准备图表配置
        const config = {
          type: 'line',
          data: props.chartData || { labels: [], datasets: [] },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false, // 完全禁用动画以避免getContext错误
            plugins: {
              legend: {
                display: true,
                position: 'top'
              },
              tooltip: {
                mode: 'index',
                intersect: false
              }
            },
            scales: {
              y: {
                beginAtZero: false
              }
            },
            ...props.chartOptions
          }
        };

        // 最后检查
        if (!isComponentMounted.value) {
          console.log(`[${componentId}] Component unmounted before chart creation`);
          return;
        }

        // 创建图表
        chart.value = new Chart(ctx, config);
        
        // 立即设置为就绪状态（因为没有动画）
        isChartReady.value = true;
        emit('chart-ready', chart.value);
        
        // 延迟隐藏加载状态
        setTimeout(() => {
          if (isComponentMounted.value) {
            isLoading.value = false;
            console.log(`[${componentId}] Chart creation completed successfully`);
          }
        }, 200);

      } catch (error) {
        console.error(`[${componentId}] Error creating chart:`, error);
        hasError.value = true;
        errorMessage.value = error.message || t('rates.chart_creation_failed');
        isLoading.value = false;
        emit('chart-error', error);
      } finally {
        isCreating.value = false;
      }
    };

    // 重试加载
    const retryLoad = () => {
      console.log(`[${componentId}] Retrying chart load`);
      hasError.value = false;
      retryTimer.value = setTimeout(() => {
        if (isComponentMounted.value) {
          createChartAsync();
        }
      }, 500);
    };

    // 刷新图表
    const refreshChart = async () => {
      if (isRefreshing.value) return;
      
      isRefreshing.value = true;
      emit('chart-refresh');
      
      try {
        await createChartAsync();
      } finally {
        isRefreshing.value = false;
      }
    };

    // 下载图表
    const downloadChart = () => {
      if (!chart.value) return;
      
      try {
        const url = chart.value.toBase64Image();
        const link = document.createElement('a');
        link.download = `chart_${Date.now()}.png`;
        link.href = url;
        link.click();
      } catch (error) {
        console.error(t('rates.chart_download_failed') + ':', error);
      }
    };

    // 防抖创建图表
    const debouncedCreateChart = () => {
      if (debounceTimer.value) {
        clearTimeout(debounceTimer.value);
      }
      
      debounceTimer.value = setTimeout(() => {
        if (isComponentMounted.value && !isLoading.value && !hasError.value && !isCreating.value) {
          createChartAsync();
        }
      }, 300);
    };

    // 监听数据变化
    watch(() => props.chartData, () => {
      if (isComponentMounted.value && !isLoading.value && !hasError.value) {
        console.log(`[${componentId}] Chart data changed, recreating chart`);
        debouncedCreateChart();
      }
    }, { deep: true });

    // 监听配置变化
    watch(() => props.chartOptions, () => {
      if (isComponentMounted.value && !isLoading.value && !hasError.value) {
        console.log(`[${componentId}] Chart options changed, recreating chart`);
        debouncedCreateChart();
      }
    }, { deep: true });

    // 组件挂载
    onMounted(async () => {
      console.log(`[${componentId}] Component mounted`);
      console.log(`[${componentId}] Container ref:`, chartContainer.value);
      console.log(`[${componentId}] Props:`, props);
      
      isComponentMounted.value = true;
      
      // 确保容器在DOM中
      await nextTick();
      await new Promise(resolve => requestAnimationFrame(resolve));
      
      console.log(`[${componentId}] After nextTick - Container ref:`, chartContainer.value);
      
      // 延迟启动图表创建
      setTimeout(() => {
        if (isComponentMounted.value) {
          console.log(`[${componentId}] Starting delayed chart creation`);
          console.log(`[${componentId}] Container at creation time:`, chartContainer.value);
          createChartAsync();
        }
      }, Math.max(100, props.loadingDelay || 100));

      // 设置自动刷新
      if (props.autoRefresh && props.refreshInterval > 0) {
        refreshTimer.value = setInterval(() => {
          if (isComponentMounted.value && !isLoading.value) {
            refreshChart();
          }
        }, props.refreshInterval);
      }
    });

    // 组件卸载
    onBeforeUnmount(() => {
      console.log(`[${componentId}] Component unmounting`);
      isComponentMounted.value = false;
      isCreating.value = false; // 重置创建锁

      // 清理定时器
      clearAllTimers();

      // 销毁图表
      if (chart.value) {
        try {
          // 立即停止所有动画
          chart.value.stop();
          
          // 强制清除动画状态
          if (chart.value.animator) {
            chart.value.animator.stop();
          }
          
          // 销毁图表实例
          chart.value.destroy();
          
          console.log(`[${componentId}] Chart destroyed successfully`);
        } catch (error) {
          console.warn(`[${componentId}] Error during cleanup:`, error);
        } finally {
          chart.value = null;
        }
      }

      // 安全清理DOM - 避免与Vue虚拟DOM冲突
      if (chartContainer.value) {
        const canvas = chartContainer.value.querySelector('canvas');
        if (canvas) {
          try {
            canvas.remove();
          } catch (error) {
            console.warn(`[${componentId}] Error removing canvas:`, error);
          }
        }
      }
    });

    return {
      chartContainer,
      isLoading,
      isChartReady,
      hasError,
      errorMessage,
      loadingText,
      loadingProgress,
      isRefreshing,
      retryLoad,
      refreshChart,
      downloadChart
    };
  }
};
</script>

<style scoped>
.async-chart-container {
  position: relative;
  width: 100%;
  min-height: 200px;
}

.chart-container {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: inherit;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-ready {
  display: block !important;
}

.chart-loading {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: rgba(255, 255, 255, 0.95);
  z-index: 10;
}

.loading-spinner {
  margin-bottom: 1rem;
}

.loading-text {
  color: #6c757d;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}

.loading-progress {
  width: 200px;
}

.progress {
  height: 4px;
  background-color: #e9ecef;
  border-radius: 2px;
  overflow: hidden;
}

.progress-bar {
  background-color: #007bff;
  transition: width 0.3s ease;
}

.chart-error {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #6c757d;
  z-index: 10;
}

.error-icon {
  font-size: 2rem;
  margin-bottom: 1rem;
}

.error-message {
  margin-bottom: 1rem;
  text-align: center;
}

.chart-toolbar {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 20;
  display: flex;
  gap: 0.5rem;
}

.chart-toolbar .btn {
  background-color: rgba(255, 255, 255, 0.9);
  border: 1px solid #dee2e6;
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
}

.chart-toolbar .btn:hover {
  background-color: #fff;
}

/* 确保canvas能正确占用空间 */
.chart-container canvas {
  max-width: 100% !important;
  max-height: 100% !important;
}
</style> 
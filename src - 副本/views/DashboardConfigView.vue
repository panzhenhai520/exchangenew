<template>
  <div class="container-fluid py-2">
    <div class="row">
      <div class="col-12">
        <div class="d-flex justify-content-between align-items-center mb-3">
          <h2>
            <font-awesome-icon :icon="['fas', 'tv']" class="me-2" />
            汇率展示配置
          </h2>
        </div>

        <!-- 配置区域 -->
        <div class="row g-3">
          <!-- 左侧：汇率列表 -->
          <div class="col-md-5">
            <div class="card">
              <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="mb-0">汇率列表</h5>
                <div class="d-flex gap-2">
                  <button 
                    class="btn btn-outline-primary btn-sm" 
                    @click="refreshRates"
                    :disabled="loading"
                  >
                    <font-awesome-icon :icon="['fas', 'sync']" :spin="loading" class="me-1" />
                    刷新汇率
                  </button>
                </div>
              </div>
              <div class="card-body">
                <!-- 拖拽排序区域 -->
                <div class="mb-3">
                  <label class="form-label">币种显示顺序（拖拽调整）</label>
                  <div 
                    class="sortable-list"
                    ref="sortableContainer"
                  >
                    <div 
                      v-for="(rate, index) in sortableRates" 
                      :key="rate.currency_id"
                      class="rate-item"
                      :class="{ 'no-rate': !rate.has_rate }"
                      draggable="true"
                      @dragstart="handleDragStart(index)"
                      @dragover.prevent
                      @drop="handleDrop(index)"
                    >
                      <div class="rate-drag-handle">
                        <font-awesome-icon :icon="['fas', 'grip-vertical']" />
                      </div>
                      <div class="rate-flag">
                        <img 
                          :src="getFlagUrl(rate.flag_code || rate.currency_code)" 
                          :alt="rate.currency_code"
                          @error="handleFlagError"
                        />
                      </div>
                      <div class="rate-info">
                        <div class="rate-currency">{{ rate.currency_code }} - {{ rate.currency_name }}</div>
                        <div class="rate-values" v-if="rate.has_rate">
                          <span class="buy-rate">买入: {{ formatRate(rate.buy_rate) }}</span>
                          <span class="sell-rate">卖出: {{ formatRate(rate.sell_rate) }}</span>
                        </div>
                        <div class="rate-values no-data" v-else>
                          <span class="text-muted">暂无汇率数据</span>
                        </div>
                      </div>
                      <div class="rate-status">
                        <font-awesome-icon 
                          :icon="rate.has_rate ? ['fas', 'check-circle'] : ['fas', 'exclamation-triangle']"
                          :class="rate.has_rate ? 'text-success' : 'text-warning'"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 中间：主题配置和预览 -->
          <div class="col-md-3">
            <div class="card">
              <div class="card-header">
                <h5 class="mb-0">展示配置</h5>
              </div>
              <div class="card-body">
                <!-- 主题选择 -->
                <div class="mb-3">
                  <label class="form-label">主题设置</label>
                  <div class="form-check form-switch">
                    <input 
                      class="form-check-input" 
                      type="checkbox" 
                      id="themeSwitch"
                      v-model="isDarkTheme"
                    >
                    <label class="form-check-label" for="themeSwitch">
                      深色主题
                    </label>
                  </div>
                </div>

                <!-- 预览按钮 -->
                <div class="d-flex gap-2 mb-3">
                  <button 
                    class="btn btn-info w-100" 
                    @click="openPreview"
                  >
                    <font-awesome-icon :icon="['fas', 'eye']" class="me-1" />
                    预览效果
                  </button>
                </div>

                <!-- 发布区域 -->
                <div class="publish-section">
                  <h6 class="mb-3">发布设置</h6>
                  <div class="alert alert-info">
                    <small>
                      <i class="fas fa-info-circle me-1"></i>
                      发布后将生成汇率展示链接，供机顶盒等设备使用
                    </small>
                  </div>
                  <div class="mt-3">
                    <button 
                      class="btn btn-success w-100" 
                      @click="publishDashboard"
                      :disabled="publishing || sortableRates.length === 0"
                    >
                      <font-awesome-icon :icon="['fas', 'upload']" :spin="publishing" class="me-1" />
                      {{ publishing ? '发布中...' : '发布汇率展示' }}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 右侧：发布历史和链接 -->
          <div class="col-md-4">
            <div class="card">
              <div class="card-header">
                <h5 class="mb-0">发布记录</h5>
              </div>
              <div class="card-body">
                <!-- 当前有效链接 -->
                <div v-if="currentPublish" class="current-publish mb-3">
                  <h6 class="text-success">当前有效链接</h6>
                  <div class="publish-info">
                    <div class="mb-2">
                      <small class="text-muted">发布时间:</small><br>
                      {{ formatDateTime(currentPublish.created_at) }}
                    </div>
                    <div class="mb-2">
                      <small class="text-muted">主题:</small>
                      <span class="badge" :class="currentPublish.theme === 'dark' ? 'bg-dark' : 'bg-light text-dark'">
                        {{ currentPublish.theme === 'dark' ? '深色' : '浅色' }}
                      </span>
                    </div>
                    <div class="mb-2">
                      <small class="text-muted">展示链接:</small><br>
                      <div class="input-group input-group-sm">
                        <input 
                          type="text" 
                          class="form-control" 
                          :value="currentPublish.encrypted_url"
                          readonly
                        >
                        <button 
                          class="btn btn-outline-secondary" 
                          @click="copyToClipboard(currentPublish.encrypted_url)"
                        >
                          <font-awesome-icon :icon="['fas', 'copy']" />
                        </button>
                      </div>
                    </div>
                    <div class="mb-2">
                      <small class="text-muted">机顶盒API:</small><br>
                      <div class="input-group input-group-sm">
                        <input 
                          type="text" 
                          class="form-control" 
                          :value="getSetTopBoxUrl()"
                          readonly
                        >
                        <button 
                          class="btn btn-outline-secondary" 
                          @click="copyToClipboard(getSetTopBoxUrl())"
                        >
                          <font-awesome-icon :icon="['fas', 'copy']" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- 历史记录 -->
                <div class="publish-history">
                  <h6>历史记录</h6>
                  <div class="history-list">
                    <div 
                      v-for="record in publishHistory" 
                      :key="record.id"
                      class="history-item"
                      :class="{ active: record.is_active }"
                    >
                      <div class="d-flex justify-content-between">
                        <span class="fw-bold">{{ formatDate(record.publish_date) }}</span>
                        <span class="badge" :class="record.is_active ? 'bg-success' : 'bg-secondary'">
                          {{ record.is_active ? '有效' : '已过期' }}
                        </span>
                      </div>
                      <div class="text-muted small">
                        {{ formatTime(record.created_at) }} | {{ record.theme === 'dark' ? '深色' : '浅色' }}主题
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Toast 通知 -->
    <div class="toast-container position-fixed bottom-0 end-0 p-3">
      <div 
        class="toast" 
        :class="{ show: toast.show }"
        ref="toastElement"
      >
        <div class="toast-header" :class="getToastHeaderClass()">
          <strong class="me-auto">{{ getToastTitle() }}</strong>
          <button type="button" class="btn-close" @click="hideToast"></button>
        </div>
        <div class="toast-body">
          {{ toast.message }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue'
import rateService from '@/services/api/rateService'
import dashboardService from '@/services/api/dashboardService'
import { useI18n } from 'vue-i18n'

export default {
  name: 'DashboardConfigView',
  setup() {
    const { t } = useI18n();
    
    // 响应式数据
    const loading = ref(false)
    const publishing = ref(false)
    const isDarkTheme = ref(false)
    const sortableRates = ref([])
    const currentPublish = ref(null)
    const publishHistory = ref([])
    const draggedIndex = ref(null)
    
    const publishSettings = reactive({
      expiryDays: 7
    })
    
    const toast = reactive({
      show: false,
      message: '',
      type: 'success'
    })

    // 计算属性
    const theme = computed(() => isDarkTheme.value ? 'dark' : 'light')

    // 方法
    const showToast = (message, type = 'success') => {
      toast.message = message
      toast.type = type
      toast.show = true
      setTimeout(() => {
        toast.show = false
      }, 3000)
    }

    const hideToast = () => {
      toast.show = false
    }

    const getToastHeaderClass = () => {
      return toast.type === 'error' ? 'bg-danger text-white' : 'bg-success text-white'
    }

    const getToastTitle = () => {
      switch (toast.type) {
        case 'success':
          return t('common.success_title');
        case 'error':
          return t('common.error_title');
        case 'warning':
          return t('common.warning_title');
        default:
          return t('common.info_title');
      }
    }

    const refreshRates = async () => {
      loading.value = true
      try {
        const response = await rateService.getCurrentRates(true)
        if (response.data.success) {
          const rates = response.data.rates || []
          
          if (sortableRates.value.length === 0) {
            // 第一次加载，直接使用所有汇率数据
            sortableRates.value = rates.map(rate => ({
              ...rate,
              has_rate: true
            }))
          } else {
            // 合并汇率数据和现有排序
            const existingOrder = sortableRates.value.map(r => r.currency_id)
            const newRates = []
            
            // 保持现有顺序
            existingOrder.forEach(currencyId => {
              const rate = rates.find(r => r.currency_id === currencyId)
              if (rate) {
                newRates.push({
                  ...rate,
                  has_rate: true
                })
              }
            })
            
            // 添加新币种
            rates.forEach(rate => {
              if (!existingOrder.includes(rate.currency_id)) {
                newRates.push({
                  ...rate,
                  has_rate: true
                })
              }
            })
            
            sortableRates.value = newRates
          }
          
          showToast('汇率数据已更新')
        } else {
          showToast(response.data.message || '获取汇率失败', 'error')
        }
      } catch (error) {
        console.error('Failed to refresh rates:', error)
        showToast('刷新汇率失败', 'error')
      } finally {
        loading.value = false
      }
    }

    const formatRate = (rate) => {
      return rate ? Number(rate).toFixed(4) : '0.0000'
    }

    const getFlagUrl = (code) => {
      return `/flags/${(code || 'unknown').toLowerCase()}.svg`
    }

    const handleFlagError = (event) => {
      event.target.src = '/flags/unknown.svg'
    }

    // 拖拽功能
    const handleDragStart = (index) => {
      draggedIndex.value = index
    }

    const handleDrop = (dropIndex) => {
      if (draggedIndex.value !== null && draggedIndex.value !== dropIndex) {
        const draggedItem = sortableRates.value[draggedIndex.value]
        sortableRates.value.splice(draggedIndex.value, 1)
        sortableRates.value.splice(dropIndex, 0, draggedItem)
      }
      draggedIndex.value = null
    }

    // 预览功能
    const openPreview = () => {
      const currencyOrder = sortableRates.value.map(r => r.currency_id)
      const url = `/rates-preview?theme=${theme.value}&currencies=${currencyOrder.join(',')}`
      window.open(url, '_blank')
    }

    // 发布功能
    const publishDashboard = async () => {
      if (sortableRates.value.length === 0) {
        showToast('请先添加币种汇率数据', 'error')
        return
      }

      publishing.value = true
      try {
        const currencyOrder = sortableRates.value.map(r => r.currency_id)
        console.log('Publishing dashboard with currency order:', currencyOrder)
        console.log('Theme:', theme.value)
        
        const response = await dashboardService.publishDashboard({
          currency_order: currencyOrder,
          theme: theme.value,
          expiry_days: 0  // 永久有效，不设置过期时间
        })
        
        console.log('Publish response:', response.data)
        
        if (response.data.success) {
          showToast('汇率展示发布成功')
          await loadPublishRecords()
        } else {
          showToast(response.data.message || '发布失败', 'error')
        }
      } catch (error) {
        console.error('Failed to publish dashboard:', error)
        let errorMsg = '发布失败'
        
        if (error.response) {
          // 服务器返回错误响应
          errorMsg += ': ' + (error.response.data?.message || `HTTP ${error.response.status}`)
          console.error('Error response:', error.response.data)
        } else if (error.request) {
          // 网络错误
          errorMsg += ': 网络连接失败'
          console.error('Network error:', error.request)
        } else {
          // 其他错误
          errorMsg += ': ' + error.message
        }
        
        showToast(errorMsg, 'error')
      } finally {
        publishing.value = false
      }
    }

    // 加载发布记录
    const loadPublishRecords = async () => {
      try {
        const response = await dashboardService.getPublishRecords()
        if (response.data.success) {
          publishHistory.value = response.data.data.records || []
          currentPublish.value = publishHistory.value.find(r => r.is_active) || null
        }
      } catch (error) {
        console.error('Failed to load publish records:', error)
      }
    }

    // 复制到剪贴板
    const copyToClipboard = async (text) => {
      try {
        await navigator.clipboard.writeText(text)
        showToast('链接已复制到剪贴板')
      } catch (error) {
        showToast('复制失败', 'error')
      }
    }

    // 获取机顶盒URL
    const getSetTopBoxUrl = () => {
      return `${window.location.origin}/api/dashboard/settop-box/auto-url?branch_code=A005`
    }

    // 格式化日期时间
    const formatDateTime = (dateStr) => {
      if (!dateStr) return ''
      const date = new Date(dateStr)
      return date.toLocaleString('zh-CN')
    }

    const formatDate = (dateStr) => {
      if (!dateStr) return ''
      const date = new Date(dateStr)
      return date.toLocaleDateString('zh-CN')
    }

    const formatTime = (dateStr) => {
      if (!dateStr) return ''
      const date = new Date(dateStr)
      return date.toLocaleTimeString('zh-CN')
    }

    // 生命周期
    onMounted(async () => {
      await refreshRates()
      await loadPublishRecords()
    })

    return {
      loading,
      publishing,
      isDarkTheme,
      sortableRates,
      currentPublish,
      publishHistory,
      publishSettings,
      toast,
      theme,
      showToast,
      hideToast,
      getToastHeaderClass,
      getToastTitle,
      refreshRates,
      formatRate,
      getFlagUrl,
      handleFlagError,
      handleDragStart,
      handleDrop,
      openPreview,
      publishDashboard,
      copyToClipboard,
      getSetTopBoxUrl,
      formatDateTime,
      formatDate,
      formatTime
    }
  }
}
</script>

<style scoped>
/* 整体容器优化 */
.container-fluid {
  padding-top: 1rem !important;
  padding-bottom: 1rem !important;
}

/* 汇率列表优化 */
.sortable-list {
  border: 1px solid #dee2e6;
  border-radius: 0.375rem;
  max-height: 70vh; /* 增加高度，使用视口高度 */
  overflow-y: auto;
  min-height: 400px; /* 设置最小高度 */
}

.rate-item {
  display: flex;
  align-items: center;
  padding: 10px 12px; /* 减少垂直内边距 */
  border-bottom: 1px solid #dee2e6;
  background: white;
  cursor: move;
  transition: all 0.2s;
}

.rate-item:hover {
  background: #f8f9fa;
}

.rate-item:last-child {
  border-bottom: none;
}

.rate-item.no-rate {
  opacity: 0.6;
  background: #fff3cd;
}

.rate-drag-handle {
  color: #6c757d;
  margin-right: 12px;
  cursor: grab;
}

.rate-drag-handle:active {
  cursor: grabbing;
}

.rate-flag {
  margin-right: 12px;
}

.rate-flag img {
  width: 32px;
  height: 24px;
  object-fit: cover;
  border-radius: 2px;
}

.rate-info {
  flex: 1;
}

.rate-currency {
  font-weight: 600;
  margin-bottom: 2px; /* 减少间距 */
  font-size: 0.95rem;
}

.rate-values {
  display: flex;
  gap: 16px;
  font-size: 0.875rem;
}

.buy-rate {
  color: #28a745;
}

.sell-rate {
  color: #007bff;
}

.rate-values.no-data {
  color: #6c757d;
}

.rate-status {
  margin-left: 12px;
}

/* 发布区域优化 */
.publish-section {
  border-top: 1px solid #dee2e6;
  padding-top: 15px; /* 减少上边距 */
  margin-top: 15px; /* 减少上边距 */
}

.current-publish {
  border: 1px solid #28a745;
  border-radius: 0.375rem;
  padding: 12px;
  background: #f8fff9;
}

.publish-info {
  font-size: 0.875rem;
}

/* 历史记录优化 */
.history-list {
  max-height: 400px; /* 增加历史记录高度 */
  overflow-y: auto;
}

.history-item {
  padding: 6px 8px; /* 减少内边距 */
  border-bottom: 1px solid #dee2e6;
}

.history-item:last-child {
  border-bottom: none;
}

.history-item.active {
  background: #f8fff9;
  border-left: 3px solid #28a745;
}

/* 卡片优化 */
.card {
  margin-bottom: 1rem; /* 减少卡片间距 */
}

.card-body {
  padding: 1rem; /* 减少卡片内边距 */
}

.card-header {
  padding: 0.75rem 1rem; /* 减少头部内边距 */
}

/* 表单组件优化 */
.mb-3 {
  margin-bottom: 1rem !important; /* 减少表单组件间距 */
}

.mb-4 {
  margin-bottom: 1.5rem !important; /* 减少大间距 */
}

/* Toast样式 */
.toast {
  opacity: 0;
  transition: opacity 0.3s;
}

.toast.show {
  opacity: 1;
}

/* 响应式优化 */
@media (max-width: 768px) {
  .sortable-list {
    max-height: 50vh;
  }
  
  .history-list {
    max-height: 250px;
  }
}
</style> 
<template>
  <div class="card h-100 shadow-sm">
    <div class="card-header bg-light">
      <h6 class="mb-0 text-primary">
        <font-awesome-icon :icon="['fas', 'history']" class="me-2" />
        {{ t('eod.history_list.title') }}
      </h6>
    </div>
    <div class="card-body d-flex flex-column">
      <!-- 月份选择器 -->
      <div class="mb-3">
        <label class="form-label small text-muted">{{ t('eod.history_list.select_month') }}</label>
        <input 
          type="month" 
          class="form-control form-control-sm"
          v-model="selectedMonth"
          @change="loadHistory"
        />
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="text-center py-3">
        <div class="spinner-border spinner-border-sm text-primary" role="status">
          <span class="visually-hidden">{{ t('common.loading') }}</span>
        </div>
        <div class="small text-muted mt-1">{{ t('common.loading') }}</div>
      </div>

      <!-- 错误提示 -->
      <div v-else-if="error" class="alert alert-danger alert-sm">
        <font-awesome-icon :icon="['fas', 'exclamation-circle']" class="me-1" />
        <small>{{ error }}</small>
      </div>

      <!-- 历史记录列表 -->
      <div v-else-if="historyList.length > 0" class="history-list">
        <div 
          v-for="record in displayedHistoryList" 
          :key="record.id"
          class="history-item"
          @click="viewReports(record)"
        >
          <div class="d-flex justify-content-between align-items-center">
            <div class="flex-grow-1">
              <div class="fw-bold text-primary small">EOD #{{ record.id }}</div>
              <div class="text-muted small">{{ formatDate(record.date) }}</div>
              <!-- 添加日结时间范围显示 -->
              <div v-if="record.business_start_time && record.business_end_time" class="text-muted small mt-1">
                <font-awesome-icon :icon="['fas', 'clock']" class="me-1" />
                {{ t('eod.history_list.business_period') }}: {{ formatDateTime(record.business_start_time) }} - {{ formatDateTime(record.business_end_time) }}
              </div>
              <div class="d-flex align-items-center mt-1">
                <span :class="getStatusClass(record.status)" class="badge badge-sm">
                  {{ getStatusText(record.status) }}
                </span>
                <span v-if="record.print_count > 0" class="text-muted small ms-2">
                  <font-awesome-icon :icon="['fas', 'print']" class="me-1" />
                  {{ record.print_count }}
                </span>
              </div>
            </div>
            <div class="text-end">
              <div class="text-muted small">{{ formatTime(record.start_time) }}</div>
              <div v-if="record.end_time" class="text-muted small">{{ formatTime(record.end_time) }}</div>
            </div>
          </div>
        </div>
        
        <!-- 展开/收起按钮 -->
        <div v-if="historyList.length > defaultDisplayCount" class="text-center mt-2">
          <button 
            class="btn btn-link btn-sm text-primary p-0 border-0"
            @click="toggleExpanded"
            style="text-decoration: none;"
          >
            <font-awesome-icon 
              :icon="['fas', isExpanded ? 'chevron-up' : 'chevron-down']" 
              class="me-1" 
            />
            {{ isExpanded ? t('eod.history_list.collapse') : t('eod.history_list.expand_more', { count: historyList.length - defaultDisplayCount }) }}
          </button>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="text-center py-3">
        <font-awesome-icon :icon="['fas', 'inbox']" class="text-muted mb-2" />
        <div class="small text-muted">{{ t('eod.history_list.no_records') }}</div>
      </div>

      <!-- 查看更多按钮 -->
      <div v-if="historyList.length > 0" class="mt-auto pt-2">
        <button 
          class="btn btn-outline-primary btn-sm w-100"
          @click="viewAllHistory"
        >
          <font-awesome-icon :icon="['fas', 'external-link-alt']" class="me-1" />
          {{ t('eod.history_list.view_all') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import endOfDayService from '../../services/api/endOfDayService'

export default {
  name: 'EODHistoryList',
  setup() {
    const { t } = useI18n()
    const router = useRouter()
    
    // 响应式数据
    const selectedMonth = ref('')
    const historyList = ref([])
    const loading = ref(false)
    const error = ref('')
    const defaultDisplayCount = 2
    const isExpanded = ref(false)
    
    // 计算属性：根据展开状态显示不同数量的记录
    const displayedHistoryList = computed(() => {
      if (isExpanded.value) {
        return historyList.value
      }
      return historyList.value.slice(0, defaultDisplayCount)
    })
    
    // 切换展开状态
    const toggleExpanded = () => {
      isExpanded.value = !isExpanded.value
    }
    
    // 初始化月份选择器为当前月份
    const initMonthSelector = () => {
      const now = new Date()
      const year = now.getFullYear()
      const month = String(now.getMonth() + 1).padStart(2, '0')
      selectedMonth.value = `${year}-${month}`
    }
    
    // 加载历史记录
    const loadHistory = async () => {
      if (!selectedMonth.value) return
      
      loading.value = true
      error.value = ''
      
      try {
        const [year, month] = selectedMonth.value.split('-')
        const startDate = `${year}-${month}-01`
        const endDate = new Date(parseInt(year), parseInt(month), 0).toISOString().split('T')[0]
        
        const response = await endOfDayService.getEodHistory({
          start_date: startDate,
          end_date: endDate,
          per_page: 10 // 只显示最近10条记录
        })
        
        if (response.data && response.data.success) {
          historyList.value = response.data.data.records || []
        } else {
          error.value = response.data?.message || t('eod.history_list.load_failed')
        }
      } catch (err) {
        console.error('加载日结历史失败:', err)
        error.value = err.response?.data?.message || err.message || t('eod.history_list.load_failed')
      } finally {
        loading.value = false
      }
    }
    
    // 查看报表
    const viewReports = (record) => {
      router.push({
        name: 'EODReportViewer',
        params: { eodId: record.id },
        query: { 
          date: record.date,
          returnTo: 'EndOfDay'
        }
      })
    }
    
    // 查看所有历史
    const viewAllHistory = () => {
      router.push({
        name: 'eod-history',
        query: { 
          month: selectedMonth.value,
          returnTo: 'EndOfDay'
        }
      })
    }
    
    // 格式化日期
    const formatDate = (dateStr) => {
      if (!dateStr) return ''
      const date = new Date(dateStr)
      return date.toLocaleDateString('zh-CN', { 
        year: 'numeric', 
        month: '2-digit', 
        day: '2-digit' 
      })
    }
    
    // 格式化时间
    const formatTime = (timeStr) => {
      if (!timeStr) return ''
      const time = new Date(timeStr)
      return time.toLocaleTimeString('zh-CN', { 
        hour: '2-digit', 
        minute: '2-digit' 
      })
    }

    // 格式化日期时间
    const formatDateTime = (dateTimeStr) => {
      if (!dateTimeStr) return ''
      const date = new Date(dateTimeStr)
      return date.toLocaleString('zh-CN', { 
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit'
      })
    }
    
    // 获取状态样式
    const getStatusClass = (status) => {
      switch (status) {
        case 'completed':
          return 'bg-success'
        case 'cancelled':
          return 'bg-danger'
        case 'processing':
          return 'bg-warning'
        default:
          return 'bg-secondary'
      }
    }
    
    // 获取状态文本
    const getStatusText = (status) => {
      switch (status) {
        case 'completed':
          return t('common.completed')
        case 'cancelled':
          return t('common.cancelled')
        case 'processing':
          return t('common.processing')
        default:
          return t('common.unknown')
      }
    }
    
    // 组件挂载时初始化
    onMounted(() => {
      initMonthSelector()
      loadHistory()
    })
    
    return {
      selectedMonth,
      historyList,
      loading,
      error,
      loadHistory,
      viewReports,
      viewAllHistory,
      formatDate,
      formatTime,
      formatDateTime,
      getStatusClass,
      getStatusText,
      t,
      defaultDisplayCount,
      isExpanded,
      displayedHistoryList,
      toggleExpanded
    }
  }
}
</script>

<style scoped>
.history-list {
  max-height: 200px;
  overflow-y: auto;
}

.history-item {
  padding: 8px 12px;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.history-item:hover {
  background-color: #f8f9fa;
  border-color: #dee2e6;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.history-item:last-child {
  margin-bottom: 0;
}

.badge-sm {
  font-size: 0.75em;
  padding: 0.25em 0.5em;
}

.alert-sm {
  padding: 0.5rem;
  font-size: 0.875rem;
}

.form-control-sm {
  font-size: 0.875rem;
  padding: 0.375rem 0.75rem;
}

.btn-sm {
  font-size: 0.875rem;
  padding: 0.375rem 0.75rem;
}
</style> 
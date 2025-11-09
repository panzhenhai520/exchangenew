<template>
  <div class="eod-history-panel">
    <div class="card shadow-sm">
      <div class="card-header bg-light">
        <h6 class="mb-0 text-info">
          <font-awesome-icon :icon="['fas', 'history']" class="me-2" />
          {{ t('eod.history_view.title') }}
        </h6>
      </div>
      <div class="card-body">
        <!-- 月份选择器 -->
        <div class="mb-3">
          <label class="form-label small">{{ t('eod.history_view.select_month') }}</label>
          <div class="row">
            <div class="col-6">
              <select 
                v-model="selectedYear" 
                class="form-select form-select-sm"
              >
                <option v-for="year in availableYears" :key="year" :value="year">
                  {{ year }}{{ t('eod.history_view.year_suffix') }}
                </option>
              </select>
            </div>
            <div class="col-6">
              <select 
                v-model="selectedMonth" 
                class="form-select form-select-sm"
              >
                <option v-for="month in availableMonths" :key="month.value" :value="month.value">
                  {{ month.label }}
                </option>
              </select>
            </div>
          </div>
          <div class="mt-2">
            <button 
              class="btn btn-sm btn-outline-primary"
              @click="loadHistoryData"
              :disabled="loading"
            >
              <span v-if="loading">
                <span class="spinner-border spinner-border-sm me-1" role="status"></span>
                {{ t('eod.history_view.loading') }}
              </span>
              <span v-else>
                <font-awesome-icon :icon="['fas', 'sync']" class="me-1" />
                {{ t('eod.history_view.manual_refresh') }}
              </span>
            </button>
          </div>
        </div>

        <!-- 加载状态 -->
        <div v-if="loading" class="text-center py-3">
          <div class="spinner-border spinner-border-sm" role="status">
            <span class="visually-hidden">加载中...</span>
          </div>
          <div class="small text-muted mt-2">{{ t('eod.history_view.loading_records') }}</div>
        </div>

        <!-- 错误提示 -->
        <div v-if="error" class="alert alert-danger alert-sm">
          <font-awesome-icon :icon="['fas', 'exclamation-triangle']" class="me-2" />
          {{ error }}
        </div>

        <!-- 历史记录列表 -->
        <div v-if="!loading && !error" class="history-list">
          <div v-if="historyRecords.length === 0" class="text-center py-3 text-muted">
            <font-awesome-icon :icon="['fas', 'calendar-times']" class="mb-2" />
            <div class="small">{{ t('eod.history_view.no_records') }}</div>
          </div>
          
          <div v-else class="history-records">
            <div 
              v-for="(record, index) in paginatedRecords" 
              :key="record.id"
              class="history-record-item compact"
              @click="viewRecordDetail(record)"
            >
              <div class="d-flex justify-content-between align-items-center w-100">
                <div class="d-flex flex-column flex-grow-1">
                  <div class="d-flex align-items-center mb-1">
                    <span class="record-id me-3 flex-shrink-0">EOD #{{ record.id }}</span>
                    <span class="record-date me-3 flex-shrink-0">{{ formatDate(record.date) }}</span>
                    <span class="text-muted me-3 flex-shrink-0">
                      <font-awesome-icon :icon="['fas', 'user']" class="me-1" />
                      {{ getUserName(record.started_by) }}
                    </span>
                    <span class="text-muted me-3 flex-shrink-0">
                      <font-awesome-icon :icon="['fas', 'clock']" class="me-1" />
                      {{ formatTime(record.started_at) }}-{{ formatTime(record.completed_at) }}
                    </span>
                  </div>
                  <div class="d-flex align-items-center">
                    <span class="text-info me-3 flex-shrink-0 time-range-label">
                      <font-awesome-icon :icon="['fas', 'chart-line']" class="me-1" />
                      {{ t('eod.history_view.statistics_period') }}：{{ getStatisticsPeriod(record, index) }}
                    </span>
                  </div>
                </div>
                <div class="record-actions">
                  <small class="text-muted me-2 hover-tip">{{ t('eod.history_view.click_to_view') }}</small>
                  <font-awesome-icon :icon="['fas', 'chevron-right']" class="text-muted" />
                </div>
              </div>
            </div>
          </div>
          
          <!-- 分页控件 -->
          <div v-if="!loading && !error && historyRecords.length > 0" class="pagination-container mt-3">
            <div class="d-flex justify-content-between align-items-center">
              <div class="text-muted small">
                {{ t('eod.history_view.pagination_info', { total: totalRecords, current: currentPage, pages: totalPages }) }}
              </div>
              <div class="btn-group btn-group-sm">
                <button 
                  class="btn btn-outline-secondary"
                  @click="goToPage(currentPage - 1)"
                  :disabled="currentPage <= 1"
                >
                  <font-awesome-icon :icon="['fas', 'chevron-left']" />
                </button>
                <button 
                  v-for="page in visiblePages"
                  :key="page"
                  class="btn"
                  :class="page === currentPage ? 'btn-primary' : 'btn-outline-secondary'"
                  @click="goToPage(page)"
                >
                  {{ page }}
                </button>
                <button 
                  class="btn btn-outline-secondary"
                  @click="goToPage(currentPage + 1)"
                  :disabled="currentPage >= totalPages"
                >
                  <font-awesome-icon :icon="['fas', 'chevron-right']" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import api from '../../services/api'

export default {
  name: 'EODHistoryPanel',
  setup() {
    const router = useRouter()
    const { t } = useI18n()
    
    // 响应式数据
    const loading = ref(false)
    const error = ref('')
    const historyRecords = ref([])
    const selectedYear = ref(new Date().getFullYear())
    const selectedMonth = ref(new Date().getMonth() + 1)
    const currentPage = ref(1)
    const itemsPerPage = ref(10)
    
    // 计算属性
    const availableYears = computed(() => {
      const currentYear = new Date().getFullYear()
      const years = []
      for (let i = currentYear; i >= currentYear - 2; i--) {
        years.push(i)
      }
      return years
    })
    
    const availableMonths = computed(() => {
      return [
        { value: 1, label: `1${t('eod.history_view.month_suffix')}` },
        { value: 2, label: `2${t('eod.history_view.month_suffix')}` },
        { value: 3, label: `3${t('eod.history_view.month_suffix')}` },
        { value: 4, label: `4${t('eod.history_view.month_suffix')}` },
        { value: 5, label: `5${t('eod.history_view.month_suffix')}` },
        { value: 6, label: `6${t('eod.history_view.month_suffix')}` },
        { value: 7, label: `7${t('eod.history_view.month_suffix')}` },
        { value: 8, label: `8${t('eod.history_view.month_suffix')}` },
        { value: 9, label: `9${t('eod.history_view.month_suffix')}` },
        { value: 10, label: `10${t('eod.history_view.month_suffix')}` },
        { value: 11, label: `11${t('eod.history_view.month_suffix')}` },
        { value: 12, label: `12${t('eod.history_view.month_suffix')}` }
      ]
    })

    // 分页相关计算属性
    const totalRecords = computed(() => historyRecords.value.length)
    const totalPages = computed(() => Math.ceil(totalRecords.value / itemsPerPage.value))
    
    const paginatedRecords = computed(() => {
      const start = (currentPage.value - 1) * itemsPerPage.value
      const end = start + itemsPerPage.value
      return historyRecords.value.slice(start, end)
    })
    
    const visiblePages = computed(() => {
      const pages = []
      const total = totalPages.value
      const current = currentPage.value
      
      if (total <= 5) {
        // 如果总页数小于等于5，显示所有页
        for (let i = 1; i <= total; i++) {
          pages.push(i)
        }
      } else {
        // 否则显示当前页附近的页码
        const start = Math.max(1, current - 2)
        const end = Math.min(total, current + 2)
        
        for (let i = start; i <= end; i++) {
          pages.push(i)
        }
      }
      
      return pages
    })
    
    // 方法
    const loadHistoryData = async () => {
      try {
        loading.value = true
        error.value = ''
        
        // 构建日期范围
        const startDate = `${selectedYear.value}-${selectedMonth.value.toString().padStart(2, '0')}-01`
        const lastDay = new Date(selectedYear.value, selectedMonth.value, 0).getDate()
        const endDate = `${selectedYear.value}-${selectedMonth.value.toString().padStart(2, '0')}-${lastDay.toString().padStart(2, '0')}`
        
        // 尝试直接使用fetch API进行调用（优先方式）
        const token = localStorage.getItem('token')
        const url = `http://localhost:5001/api/end_of_day/history?start_date=${startDate}&end_date=${endDate}&per_page=50`
        
        const fetchResponse = await fetch(url, {
          method: 'GET',
          headers: {
            'Authorization': token ? `Bearer ${token}` : '',
            'Content-Type': 'application/json'
          }
        })
        
        if (fetchResponse.ok) {
          const fetchData = await fetchResponse.json()
          
          if (fetchData.success) {
            // 按日期降序排序（最新的在前面）
            historyRecords.value = fetchData.data.records.sort((a, b) => {
              return new Date(b.date) - new Date(a.date)
            })
            console.log(`获取历史记录成功，数量: ${historyRecords.value.length}`)
            // 重置到第一页
            currentPage.value = 1
            return // 直接返回，不再尝试axios
          } else {
            console.error('API返回错误:', fetchData.message)
          }
        } else {
          console.error('API调用失败:', fetchResponse.status, fetchResponse.statusText)
        }
        
        // 如果fetch失败，继续尝试axios作为备用方案
        console.log('使用axios备用方案...')
        
        const response = await api.get('/end_of_day/history', {
          params: {
            start_date: startDate,
            end_date: endDate,
            per_page: 50  // 获取足够的记录
          }
        })
        
        if (response.data.success) {
          // 按日期降序排序（最新的在前面）
          historyRecords.value = response.data.data.records.sort((a, b) => {
            return new Date(b.date) - new Date(a.date)
          })
          console.log(`获取历史记录成功，数量: ${historyRecords.value.length}`)
          // 重置到第一页
          currentPage.value = 1
        } else {
          error.value = response.data.message || '获取历史记录失败'
        }
      } catch (err) {
        console.error('获取历史记录失败:', err.message)
        if (err.response) {
          console.error('响应状态:', err.response.status)
          console.error('响应数据:', err.response.data)
        }
        
        error.value = err.response?.data?.message || err.message || '获取历史记录失败'
      } finally {
        loading.value = false
      }
    }
    
    const viewRecordDetail = (record) => {
      // 跳转到PDF查看页面
      router.push({
        name: 'EODReportViewer',
        params: { eodId: record.id }
      })
    }
    
    const formatDate = (dateString) => {
      if (!dateString) return ''
      const date = new Date(dateString)
      const month = (date.getMonth() + 1).toString().padStart(2, '0')
      const day = date.getDate().toString().padStart(2, '0')
      const weekdays = t('eod.weekdays')
      const weekday = weekdays[date.getDay()]
      return `${month}/${day}${weekday}`
    }
    
    const formatTime = (dateString) => {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit'
      })
    }
    
    const getUserName = (userIdOrName) => {
      if (!userIdOrName) return '未知用户'
      
      // 如果是数字ID，尝试获取用户名
      if (typeof userIdOrName === 'number' || /^\d+$/.test(userIdOrName)) {
        try {
          const user = JSON.parse(localStorage.getItem('user') || '{}')
          // 如果是当前用户的ID，返回当前用户名
          if (user.id && user.id.toString() === userIdOrName.toString()) {
            return user.name || user.login_code || `用户${userIdOrName}`
          }
          // 否则返回格式化的用户ID
          return `用户${userIdOrName}`
        } catch {
          return `用户${userIdOrName}`
        }
      }
      
      // 如果已经是用户名，直接返回
      return userIdOrName
    }
    
    const goToPage = (page) => {
      if (page >= 1 && page <= totalPages.value) {
        currentPage.value = page
      }
    }
    
    const getStatisticsPeriod = (record, index) => {
      // 获取上一次日结的完成时间作为本次统计开始时间
      const currentPageStartIndex = (currentPage.value - 1) * itemsPerPage.value
      const globalIndex = currentPageStartIndex + index
      
      // 由于数组是按日期倒序排列的，需要找到时间上的下一个记录（即数组中的上一个记录）
      const nextRecordIndex = globalIndex + 1
      
      if (nextRecordIndex < historyRecords.value.length) {
        // 有上一次日结记录
        const prevRecord = historyRecords.value[nextRecordIndex]
        const statsStart = prevRecord.completed_at
        const statsEnd = record.started_at
        
        const startTime = formatTime(statsStart)
        const endTime = formatTime(statsEnd)
        const startDate = formatDate(prevRecord.date)
        const endDate = formatDate(record.date)
        
        if (startDate === endDate) {
          // 同一天
          return `${startTime}-${endTime}`
        } else {
          // 跨天
          return `${startDate} ${startTime} - ${endDate} ${endTime}`
        }
      } else {
        // 没有上一次日结记录，这是第一次日结
        const statsEnd = record.started_at
        const endTime = formatTime(statsEnd)
        const endDate = formatDate(record.date)
        
        return `营业开始 - ${endDate} ${endTime}`
      }
    }
    
    // 监听月份变化，重置分页
    watch([selectedYear, selectedMonth], () => {
      currentPage.value = 1
      loadHistoryData()
    })
    
    // 生命周期
    onMounted(() => {
      loadHistoryData()
    })
    
    return {
      t,
      loading,
      error,
      historyRecords,
      selectedYear,
      selectedMonth,
      currentPage,
      availableYears,
      availableMonths,
      totalRecords,
      totalPages,
      paginatedRecords,
      visiblePages,
      loadHistoryData,
      viewRecordDetail,
      formatDate,
      formatTime,
      getUserName,
      goToPage,
      getStatisticsPeriod
    }
  }
}
</script>

<style scoped>
.eod-history-panel {
  height: 100%;
}

.history-list {
  max-height: 450px;
  overflow-y: auto;
}

.history-record-item {
  padding: 8px 12px;
  border-bottom: 1px solid #e9ecef;
  cursor: pointer;
  transition: background-color 0.2s;
  font-size: 0.85rem;
}

.history-record-item.compact {
  padding: 8px 12px;
  font-size: 0.8rem;
}

.history-record-item:hover {
  background-color: #f8f9fa;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.history-record-item:last-child {
  border-bottom: none;
}

.record-id {
  font-weight: 600;
  color: #0d6efd;
  font-size: 0.85rem;
}

.record-date {
  font-size: 0.75rem;
  color: #6c757d;
  font-weight: 500;
}

.record-actions {
  display: flex;
  align-items: center;
  font-size: 0.7rem;
  white-space: nowrap;
}

.hover-tip {
  opacity: 0;
  transition: opacity 0.2s ease;
}

.history-record-item:hover .hover-tip {
  opacity: 1;
}

.time-range-label {
  font-size: 0.7rem;
  color: #6c757d;
  font-weight: 500;
}

.alert-sm {
  font-size: 0.8rem;
  padding: 0.5rem;
}

.form-select-sm {
  font-size: 0.8rem;
  padding: 0.25rem 0.5rem;
}

.card-header h6 {
  font-size: 0.9rem;
}

.card-body {
  padding: 0.75rem;
}

.history-records {
  border: 1px solid #e9ecef;
  border-radius: 0.375rem;
  background-color: #fff;
  max-height: 320px;
  overflow-y: auto;
}

.history-records::-webkit-scrollbar {
  width: 4px;
}

.history-records::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.history-records::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 2px;
}

.history-records::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.pagination-container {
  border-top: 1px solid #e9ecef;
  padding-top: 0.75rem;
}

.btn-group-sm > .btn {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
}

/* 响应式设计 */
@media (max-width: 576px) {
  .history-record-item.compact {
    font-size: 0.75rem;
  }
  
  .record-actions .hover-tip {
    display: none;
  }
  
  .d-flex.align-items-center.flex-grow-1 > span {
    margin-right: 0.5rem !important;
  }
}

@media (max-width: 768px) {
  .history-records {
    max-height: 280px;
  }
}
</style> 
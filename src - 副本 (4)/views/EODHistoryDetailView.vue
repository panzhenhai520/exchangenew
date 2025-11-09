<template>
  <div class="container-fluid py-4">
    <div class="row">
      <div class="col-12">
        <!-- 页面标题 -->
        <div class="d-flex justify-content-between align-items-center mb-4">
          <div>
            <h2 class="page-title-bold">
              <font-awesome-icon :icon="['fas', 'file-alt']" class="me-2" />
              {{ $t('eod.history.detail_title') }}
            </h2>
            <p class="text-muted mb-0">
              {{ $t('eod.history.date') }}: {{ eodDate }} | 
              {{ $t('eod.history.eod_id') }}: {{ eodId }}
            </p>
          </div>
          <div>
            <button 
              class="btn btn-outline-secondary"
              @click="goBack"
            >
              <font-awesome-icon :icon="['fas', 'arrow-left']" class="me-2" />
              {{ $t('common.back') }}
            </button>
          </div>
        </div>

        <!-- 加载状态 -->
        <div v-if="loading" class="text-center py-5">
          <font-awesome-icon :icon="['fas', 'spinner']" spin size="2x" class="text-primary mb-3" />
          <p class="text-muted">{{ $t('common.loading') }}</p>
        </div>

        <!-- 错误状态 -->
        <div v-else-if="error" class="alert alert-danger">
          <font-awesome-icon :icon="['fas', 'exclamation-circle']" class="me-2" />
          {{ error }}
          <button class="btn btn-outline-danger btn-sm ms-3" @click="retryLoad">
            <font-awesome-icon :icon="['fas', 'redo']" class="me-1" />
            {{ $t('common.retry') }}
          </button>
        </div>

        <!-- PDF显示区域 -->
        <div v-else class="row g-4">
          <!-- 左侧：收入报表 -->
          <div class="col-md-6">
            <div class="card h-100 shadow-sm">
              <div class="card-header bg-primary text-white">
                <h5 class="mb-0">
                  <font-awesome-icon :icon="['fas', 'chart-line']" class="me-2" />
                  {{ $t('eod.history.income_report') }}
                </h5>
              </div>
              <div class="card-body p-0">
                <div v-if="loadingIncome" class="text-center py-5">
                  <font-awesome-icon :icon="['fas', 'spinner']" spin class="text-primary mb-2" />
                  <p class="text-muted">{{ $t('common.loading') }}</p>
                </div>
                <div v-else-if="incomePdfUrl" class="pdf-container">
                  <iframe 
                    :src="incomePdfUrl" 
                    class="pdf-iframe"
                    frameborder="0"
                  ></iframe>
                </div>
                <div v-else class="text-center py-5 text-muted">
                  <font-awesome-icon :icon="['fas', 'file-excel']" size="2x" class="mb-2" />
                  <p>{{ $t('eod.history.no_income_report') }}</p>
                </div>
              </div>
              <div class="card-footer">
                <div class="d-flex justify-content-between align-items-center">
                  <small class="text-muted">
                    {{ $t('eod.history.income_report_desc') }}
                  </small>
                  <button 
                    v-if="incomePdfUrl"
                    class="btn btn-sm btn-outline-primary"
                    @click="downloadIncomePdf"
                  >
                    <font-awesome-icon :icon="['fas', 'download']" class="me-1" />
                    {{ $t('common.download') }}
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- 右侧：交款报表 -->
          <div class="col-md-6">
            <div class="card h-100 shadow-sm">
              <div class="card-header bg-success text-white">
                <h5 class="mb-0">
                  <font-awesome-icon :icon="['fas', 'money-bill-wave']" class="me-2" />
                  {{ $t('eod.history.cashout_report') }}
                </h5>
              </div>
              <div class="card-body p-0">
                <div v-if="loadingCashout" class="text-center py-5">
                  <font-awesome-icon :icon="['fas', 'spinner']" spin class="text-success mb-2" />
                  <p class="text-muted">{{ $t('common.loading') }}</p>
                </div>
                <div v-else-if="cashoutPdfUrl" class="pdf-container">
                  <iframe 
                    :src="cashoutPdfUrl" 
                    class="pdf-iframe"
                    frameborder="0"
                  ></iframe>
                </div>
                <div v-else class="text-center py-5 text-muted">
                  <font-awesome-icon :icon="['fas', 'file-excel']" size="2x" class="mb-2" />
                  <p>{{ $t('eod.history.no_cashout_report') }}</p>
                </div>
              </div>
              <div class="card-footer">
                <div class="d-flex justify-content-between align-items-center">
                  <small class="text-muted">
                    {{ $t('eod.history.cashout_report_desc') }}
                  </small>
                  <button 
                    v-if="cashoutPdfUrl"
                    class="btn btn-sm btn-outline-success"
                    @click="downloadCashoutPdf"
                  >
                    <font-awesome-icon :icon="['fas', 'download']" class="me-1" />
                    {{ $t('common.download') }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 日结信息 -->
        <div v-if="eodInfo" class="row mt-4">
          <div class="col-12">
            <div class="card shadow-sm">
              <div class="card-header bg-light">
                <h6 class="mb-0">
                  <font-awesome-icon :icon="['fas', 'info-circle']" class="me-2" />
                  {{ $t('eod.history.eod_info') }}
                </h6>
              </div>
              <div class="card-body">
                <div class="row">
                  <div class="col-md-3">
                    <p class="mb-1"><strong>{{ $t('eod.history.completed_at') }}:</strong></p>
                    <p class="text-muted">{{ formatDateTime(eodInfo.completed_at) }}</p>
                  </div>
                  <div class="col-md-3">
                    <p class="mb-1"><strong>{{ $t('eod.history.completed_by') }}:</strong></p>
                    <p class="text-muted">{{ eodInfo.completed_by || 'N/A' }}</p>
                  </div>
                  <div class="col-md-3">
                    <p class="mb-1"><strong>{{ $t('eod.history.total_transactions') }}:</strong></p>
                    <p class="text-muted">{{ eodInfo.total_transactions || 0 }}</p>
                  </div>
                </div>
                <div class="row mt-3">
                  <div class="col-12">
                    <p class="mb-1"><strong>{{ $t('eod.history.cash_out_amount') }}:</strong></p>
                    <div v-if="eodInfo.cash_out_by_currency && eodInfo.cash_out_by_currency.length > 0" class="row">
                      <div v-for="cashOut in eodInfo.cash_out_by_currency" :key="cashOut.currency_code" class="col-md-4 mb-2">
                        <div class="border rounded p-2 bg-light">
                          <div class="text-muted small">{{ cashOut.currency_name }} ({{ cashOut.currency_code }})</div>
                          <div class="h5 mb-0 text-primary">{{ formatCurrency(cashOut.amount) }}</div>
                        </div>
                      </div>
                    </div>
                    <div v-else class="text-muted">
                      {{ formatCurrency(eodInfo.cash_out_amount) }}
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
</template>

<script>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import api from '../services/api'

export default {
  name: 'EODHistoryDetailView',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const { t } = useI18n()
    
    // 响应式数据
    const loading = ref(true)
    const error = ref('')
    const eodInfo = ref(null)
    const loadingIncome = ref(false)
    const loadingCashout = ref(false)
    const incomePdfUrl = ref('')
    const cashoutPdfUrl = ref('')
    
    // 计算属性
    const eodId = computed(() => route.params.id)
    const eodDate = computed(() => route.query.date || '')
    const currentLanguage = computed(() => {
      // 语言代码映射：前端存储格式 -> 后端期望格式
      const langMap = {
        'zh-CN': 'zh',
        'en-US': 'en',
        'th-TH': 'th'
      };
      const storedLang = localStorage.getItem('language') || 'zh-CN';
      return langMap[storedLang] || 'zh';
    })
    
    // 方法
    const loadEODDetail = async () => {
      loading.value = true
      error.value = ''
      
      try {
        const response = await api.get(`/end_of_day/history/${eodId.value}`)
        if (response.data.success) {
          eodInfo.value = response.data.eod_info
          await loadPDFs()
        } else {
          error.value = response.data.message || t('eod.history.load_error')
        }
      } catch (err) {
        console.error('加载日结详情失败:', err)
        error.value = err.response?.data?.message || t('eod.history.load_error')
      } finally {
        loading.value = false
      }
    }
    
    const loadPDFs = async () => {
      if (!eodInfo.value) return
      
      // 加载收入报表PDF
      await loadIncomePdf()
      
      // 加载交款报表PDF
      await loadCashoutPdf()
    }
    
    const loadIncomePdf = async () => {
      loadingIncome.value = true
      try {
        console.log(`正在加载收入报表PDF，语言: ${currentLanguage.value}`)
        // 直接下载PDF文件并创建blob URL
        const response = await api.get(`/end_of_day/history/${eodId.value}/income-pdf/download`, {
          params: { language: currentLanguage.value },
          responseType: 'blob'
        })
        
        // 创建blob URL用于iframe显示
        const blob = new Blob([response.data], { type: 'application/pdf' })
        incomePdfUrl.value = URL.createObjectURL(blob)
        console.log('收入报表PDF加载成功')
      } catch (err) {
        console.error('加载收入报表PDF失败:', err)
      } finally {
        loadingIncome.value = false
      }
    }
    
    const loadCashoutPdf = async () => {
      loadingCashout.value = true
      try {
        console.log(`正在加载交款报表PDF，语言: ${currentLanguage.value}`)
        // 直接下载PDF文件并创建blob URL
        const response = await api.get(`/end_of_day/history/${eodId.value}/cashout-pdf/download`, {
          params: { language: currentLanguage.value },
          responseType: 'blob'
        })
        
        // 创建blob URL用于iframe显示
        const blob = new Blob([response.data], { type: 'application/pdf' })
        cashoutPdfUrl.value = URL.createObjectURL(blob)
        console.log('交款报表PDF加载成功')
      } catch (err) {
        console.error('加载交款报表PDF失败:', err)
      } finally {
        loadingCashout.value = false
      }
    }
    
    const downloadIncomePdf = async () => {
      try {
        const response = await api.get(`/end_of_day/history/${eodId.value}/income-pdf/download`, {
          params: { language: currentLanguage.value },
          responseType: 'blob'
        })
        
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `income_report_${eodDate.value}_${currentLanguage.value}.pdf`)
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
      } catch (err) {
        console.error('下载收入报表失败:', err)
      }
    }
    
    const downloadCashoutPdf = async () => {
      try {
        const response = await api.get(`/end_of_day/history/${eodId.value}/cashout-pdf/download`, {
          params: { language: currentLanguage.value },
          responseType: 'blob'
        })
        
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `cashout_report_${eodDate.value}_${currentLanguage.value}.pdf`)
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
      } catch (err) {
        console.error('下载交款报表失败:', err)
      }
    }
    
    const goBack = () => {
      router.go(-1)
    }
    
    const retryLoad = () => {
      loadEODDetail()
    }
    
    const formatDateTime = (dateTime) => {
      if (!dateTime) return 'N/A'
      const date = new Date(dateTime)
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    }
    
    const formatCurrency = (amount) => {
      if (!amount) return '0.00'
      return parseFloat(amount).toFixed(2)
    }
    
    // 生命周期
    onMounted(() => {
      if (eodId.value) {
        loadEODDetail()
      } else {
        error.value = t('eod.history.invalid_id')
        loading.value = false
      }
    })
    
    onUnmounted(() => {
      // 清理blob URL，避免内存泄漏
      if (incomePdfUrl.value && incomePdfUrl.value.startsWith('blob:')) {
        URL.revokeObjectURL(incomePdfUrl.value)
      }
      if (cashoutPdfUrl.value && cashoutPdfUrl.value.startsWith('blob:')) {
        URL.revokeObjectURL(cashoutPdfUrl.value)
      }
    })
    
    return {
      loading,
      error,
      eodInfo,
      loadingIncome,
      loadingCashout,
      incomePdfUrl,
      cashoutPdfUrl,
      eodId,
      eodDate,
      loadEODDetail,
      loadIncomePdf,
      loadCashoutPdf,
      downloadIncomePdf,
      downloadCashoutPdf,
      goBack,
      retryLoad,
      formatDateTime,
      formatCurrency
    }
  }
}
</script>

<style scoped>
.pdf-container {
  height: 600px;
  overflow: hidden;
}

.pdf-iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.page-title-bold {
  font-weight: 600;
  color: #2c3e50;
}

@media (max-width: 768px) {
  .pdf-container {
    height: 400px;
  }
  
  .row .col-md-6 {
    margin-bottom: 1rem;
  }
}

@media (max-width: 576px) {
  .pdf-container {
    height: 300px;
  }
}
</style> 
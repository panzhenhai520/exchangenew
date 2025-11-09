<template>
  <div class="eod-report-viewer">
    <div class="container-fluid">
      <!-- 页面标题 -->
      <div class="row">
        <div class="col-12">
          <div class="d-flex justify-content-between align-items-center mb-3">
            <div>
              <h4 class="mb-0">{{ $t('eod.report_viewer.title') }}</h4>
              <div class="text-muted">
                <span v-if="eodInfo.date">{{ formatDate(eodInfo.date) }}</span>
                <span v-if="eodInfo.id" class="ms-2">EOD #{{ eodInfo.id }}</span>
              </div>
            </div>
            <div class="btn-toolbar">
              <button 
                class="btn btn-outline-secondary btn-sm me-2"
                @click="goBack"
              >
                <font-awesome-icon :icon="['fas', 'arrow-left']" class="me-1" />
                {{ $t('eod.report_viewer.back') }}
              </button>
              <button 
                class="btn btn-outline-primary btn-sm"
                @click="refreshReports"
                :disabled="loading"
              >
                <font-awesome-icon :icon="['fas', 'sync-alt']" class="me-1" />
                {{ $t('eod.report_viewer.refresh') }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 错误提示 -->
      <div v-if="error" class="row">
        <div class="col-12">
          <div class="alert alert-danger">
            <font-awesome-icon :icon="['fas', 'exclamation-triangle']" class="me-2" />
            {{ error }}
          </div>
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="row">
        <div class="col-12">
          <div class="text-center py-5">
            <div class="spinner-border" role="status">
              <span class="visually-hidden">加载中...</span>
            </div>
            <div class="mt-3">{{ $t('eod.report_viewer.loading_reports') }}</div>
          </div>
        </div>
      </div>

      <!-- PDF查看区域 -->
      <div v-if="!loading && !error" class="row">
        <!-- 左侧：收入统计表 -->
        <div class="col-md-6">
          <div class="card h-100">
            <div class="card-header">
              <h6 class="mb-0">
                <font-awesome-icon :icon="['fas', 'chart-line']" class="me-2" />
                {{ $t('eod.income_statistics_title') }}
              </h6>
            </div>
            <div class="card-body p-2">
              <div v-if="incomeReportUrl" class="pdf-container">
                <iframe
                  :src="incomeReportUrl"
                  class="pdf-frame"
                  frameborder="0"
                  :title="$t('eod.income_statistics_title')"
                >
                </iframe>
                <!-- Fallback for browsers that don't support PDF -->
                <div v-if="showPdfFallback" class="pdf-fallback-overlay">
                  <div class="text-center p-4">
                    <font-awesome-icon :icon="['fas', 'file-pdf']" size="3x" class="text-muted mb-3" />
                    <p class="text-muted">{{ $t('eod.report_viewer.browser_not_support_pdf') }}</p>
                    <a :href="incomeReportUrl" target="_blank" class="btn btn-primary">
                      {{ $t('eod.report_viewer.click_to_download') }}
                    </a>
                  </div>
                </div>
              </div>
              <div v-else class="text-center py-4 text-muted">
                <font-awesome-icon :icon="['fas', 'file-alt']" size="3x" class="mb-3" />
                <div>{{ $t('eod.report_viewer.income_report_not_found') }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧：交款统计表 -->
        <div class="col-md-6">
          <div class="card h-100">
            <div class="card-header">
              <h6 class="mb-0">
                <font-awesome-icon :icon="['fas', 'money-bill-wave']" class="me-2" />
                {{ $t('eod.report_viewer.cashout_statistics_title') }}
              </h6>
            </div>
            <div class="card-body p-2">
              <div v-if="cashoutReportUrl" class="pdf-container">
                <iframe
                  :src="cashoutReportUrl"
                  class="pdf-frame"
                  frameborder="0"
                  :title="$t('eod.report_viewer.cashout_statistics_title')"
                >
                </iframe>
                <!-- Fallback for browsers that don't support PDF -->
                <div v-if="showPdfFallback" class="pdf-fallback-overlay">
                  <div class="text-center p-4">
                    <font-awesome-icon :icon="['fas', 'file-pdf']" size="3x" class="text-muted mb-3" />
                    <p class="text-muted">{{ $t('eod.report_viewer.browser_not_support_pdf') }}</p>
                    <a :href="cashoutReportUrl" target="_blank" class="btn btn-primary">
                      {{ $t('eod.report_viewer.click_to_download') }}
                    </a>
                  </div>
                </div>
              </div>
              <div v-else class="text-center py-4 text-muted">
                <font-awesome-icon :icon="['fas', 'file-alt']" size="3x" class="mb-3" />
                <div>{{ $t('eod.report_viewer.cashout_report_not_found') }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 差额报告区域 -->
      <div v-if="!loading && !error && differenceReportUrl" class="row mt-3">
        <div class="col-12">
          <div class="card">
            <div class="card-header">
              <h6 class="mb-0">
                <font-awesome-icon :icon="['fas', 'balance-scale']" class="me-2" />
                {{ $t('eod.report_viewer.difference_reports_title') }}
              </h6>
            </div>
            <div class="card-body">
              <div class="row">
                <!-- 差额报告 -->
                <div class="col-md-12">
                  <div class="card">
                    <div class="card-header">
                      <h6 class="mb-0">
                        <font-awesome-icon :icon="['fas', 'exclamation-triangle']" class="me-2" />
                        {{ getDifferenceReportTitle() }}
                      </h6>
                    </div>
                    <div class="card-body p-2">
                      <div class="pdf-container">
                        <iframe
                          :src="differenceReportUrl"
                          class="pdf-frame"
                          frameborder="0"
                          :title="getDifferenceReportTitle()"
                        >
                        </iframe>
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
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import endOfDayService from '../services/api/endOfDayService'
import i18n from '../i18n'

export default {
  name: 'EODReportViewer',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const { t } = useI18n()
    
    // 响应式数据
    const loading = ref(false)
    const error = ref('')
    const eodInfo = ref({})
    const pdfFiles = ref([])
    const incomeReportUrl = ref('')
    const cashoutReportUrl = ref('')
    const differenceReportUrl = ref('')
    const differenceAdjustmentReportUrl = ref('')
    const showPdfFallback = ref(false)
    const hasAdjustment = ref(false) // 是否有差额调节
    
    // 方法
    const loadReportData = async () => {
      try {
        loading.value = true
        error.value = ''
        
        const eodId = route.params.eodId
        
        // 使用endOfDayService获取PDF文件列表
        console.log('请求PDF文件列表，EOD ID:', eodId)
        
        const response = await endOfDayService.getEodPdfFiles(eodId)
        
        if (response.data && response.data.success) {
          const data = response.data.data
          eodInfo.value = {
            id: data.eod_id,
            date: data.eod_date
          }
          pdfFiles.value = data.pdf_files
          hasAdjustment.value = data.has_adjustment || false // 获取差额调节状态
          
          // 查找收入统计表和交款统计表
          findReportUrls(data.pdf_files)
        } else {
          error.value = response.data?.message || '获取报表文件失败'
        }
      } catch (err) {
        console.error('获取报表文件失败:', err)
        error.value = err.response?.data?.message || '获取报表文件失败'
      } finally {
        loading.value = false
      }
    }
    
    const findReportUrls = (files) => {
      // 重置URL和fallback状态
      incomeReportUrl.value = ''
      cashoutReportUrl.value = ''
      differenceReportUrl.value = ''
      differenceAdjustmentReportUrl.value = ''
      showPdfFallback.value = false
      
      console.log('=== PDF文件查找调试信息 ===')
      console.log('EOD信息:', eodInfo.value)
      console.log('文件列表:', files)
      
      // 获取当前语言
      const currentLanguage = localStorage.getItem('language') || 'zh-CN'
      const langMap = {
        'zh-CN': 'zh',
        'en-US': 'en', 
        'th-TH': 'th'
      }
      const lang = langMap[currentLanguage] || 'zh'
      
      console.log('当前语言:', currentLanguage, '映射为:', lang)
      
      // 构建完整的baseURL
      const baseURL = process.env.VUE_APP_API_URL || (process.env.NODE_ENV === 'development' ? 'http://localhost:5001' : '')
      
      // 获取当前用户的token
      const token = localStorage.getItem('token') || sessionStorage.getItem('token')
      
      // 按照新的命名规范查找文件
      const eodDate = eodInfo.value.date
      const eodId = eodInfo.value.id
      
      if (eodDate && eodId) {
        const dateStr = new Date(eodDate).toISOString().split('T')[0].replace(/-/g, '')
        
        console.log('日期字符串:', dateStr, 'EOD ID:', eodId)
        
        // 查找收入统计表：根据语言选择正确的文件
        let incomePattern = `${dateStr}EOD${eodId}income`
        let incomeFile = null
        
        // 优先查找当前语言的文件
        if (lang === 'en') {
          incomePattern += '_en'
          incomeFile = files.find(f => f.filename.includes(incomePattern))
        } else if (lang === 'th') {
          incomePattern += '_th'
          incomeFile = files.find(f => f.filename.includes(incomePattern))
        } else {
          // 中文：优先查找无后缀的文件，如果没有则查找其他语言
          incomeFile = files.find(f => f.filename.includes(incomePattern) && !f.filename.includes('_en') && !f.filename.includes('_th'))
          if (!incomeFile) {
            // 如果找不到无后缀的中文文件，尝试查找其他语言
            incomeFile = files.find(f => f.filename.includes(incomePattern))
          }
        }
        
        console.log('收入表查找模式:', incomePattern, '找到:', incomeFile)
        if (incomeFile) {
          incomeReportUrl.value = baseURL + incomeFile.url + `&token=${token}`
        }
        
        // 查找交款统计表：根据语言选择正确的文件
        let cashoutPattern = `${dateStr}EOD${eodId}cashout`
        let cashoutFile = null
        
        // 优先查找当前语言的文件
        if (lang === 'en') {
          cashoutPattern += '_en'
          cashoutFile = files.find(f => f.filename.includes(cashoutPattern))
        } else if (lang === 'th') {
          cashoutPattern += '_th'
          cashoutFile = files.find(f => f.filename.includes(cashoutPattern))
        } else {
          // 中文：优先查找无后缀的文件，如果没有则查找其他语言
          cashoutFile = files.find(f => f.filename.includes(cashoutPattern) && !f.filename.includes('_en') && !f.filename.includes('_th'))
          if (!cashoutFile) {
            // 如果找不到无后缀的中文文件，尝试查找其他语言
            cashoutFile = files.find(f => f.filename.includes(cashoutPattern))
          }
        }
        
        console.log('交款表查找模式:', cashoutPattern, '找到:', cashoutFile)
        if (cashoutFile) {
          cashoutReportUrl.value = baseURL + cashoutFile.url + `&token=${token}`
        }
        
        // 查找差额报告：根据语言选择正确的文件
        let diffPattern = `${dateStr}EOD${eodId}Diff`
        let diffFile = null
        
        // 优先查找当前语言的文件
        if (lang === 'en') {
          diffPattern += '_en'
          diffFile = files.find(f => f.filename.includes(diffPattern))
        } else if (lang === 'th') {
          diffPattern += '_th'
          diffFile = files.find(f => f.filename.includes(diffPattern))
        } else {
          // 中文：优先查找无后缀的文件，如果没有则查找其他语言
          diffFile = files.find(f => f.filename.includes(diffPattern) && !f.filename.includes('_en') && !f.filename.includes('_th'))
          if (!diffFile) {
            // 如果找不到无后缀的中文文件，尝试查找其他语言
            diffFile = files.find(f => f.filename.includes(diffPattern))
          }
        }
        
        console.log('差额报告查找模式:', diffPattern, '找到:', diffFile)
        if (diffFile) {
          differenceReportUrl.value = baseURL + diffFile.url + `&token=${token}`
        }
      }
      
      // 如果按新规范找不到，尝试按旧规范和其他模式查找
      if (!incomeReportUrl.value || !cashoutReportUrl.value) {
        console.log('按新规范未找到，尝试其他方式...')
        
        files.forEach(file => {
          console.log('检查文件:', file.filename, '类型:', file.type)
          
          // 按type字段查找
          if (file.type === 'income' && !incomeReportUrl.value) {
            incomeReportUrl.value = baseURL + file.url + `&token=${token}`
            console.log('按type找到收入表:', file.filename)
          }
          if (file.type === 'eod_report' && !cashoutReportUrl.value) {
            cashoutReportUrl.value = baseURL + file.url + `&token=${token}`
            console.log('按type找到交款表:', file.filename)
          }
          
          // 按文件名关键词查找
          const filename = file.filename.toLowerCase()
          if (filename.includes('detailed') && !incomeReportUrl.value) {
            incomeReportUrl.value = baseURL + file.url + `&token=${token}`
            console.log('按detailed关键词找到收入表:', file.filename)
          }
          if (filename.includes('comprehensive') && !cashoutReportUrl.value) {
            cashoutReportUrl.value = baseURL + file.url + `&token=${token}`
            console.log('按comprehensive关键词找到交款表:', file.filename)
          }
        })
      }
      
      console.log('最终结果 - 收入表URL:', incomeReportUrl.value)
      console.log('最终结果 - 交款表URL:', cashoutReportUrl.value)
    }
    
    const refreshReports = () => {
      loadReportData()
    }
    
    const goBack = () => {
      router.go(-1)
    }
    
    const formatDate = (dateString) => {
      if (!dateString) return ''
      const date = new Date(dateString)
      
      // 获取当前语言
      const currentLanguage = localStorage.getItem('language') || 'zh-CN'
      
      // 根据语言设置不同的格式
      if (currentLanguage === 'en-US') {
        return date.toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'long',
          day: 'numeric',
          weekday: 'long'
        })
      } else if (currentLanguage === 'th-TH') {
        return date.toLocaleDateString('th-TH', {
          year: 'numeric',
          month: 'long',
          day: 'numeric',
          weekday: 'long'
        })
      } else {
        // 默认中文格式
        return date.toLocaleDateString('zh-CN', {
          year: 'numeric',
          month: 'long',
          day: 'numeric',
          weekday: 'long'
        })
      }
    }
    
    const formatDateTime = (dateString) => {
      if (!dateString) return ''
      const date = new Date(dateString)
      
      // 获取当前语言
      const currentLanguage = localStorage.getItem('language') || 'zh-CN'
      
      // 根据语言设置不同的格式
      if (currentLanguage === 'en-US') {
        return date.toLocaleString('en-US')
      } else if (currentLanguage === 'th-TH') {
        return date.toLocaleString('th-TH')
      } else {
        // 默认中文格式
        return date.toLocaleString('zh-CN')
      }
    }
    
    const formatFileSize = (bytes) => {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }
    
    const getFileTypeLabel = (type) => {
      // 使用i18n翻译
      const translationKey = `eod.report_viewer.file_types.${type}`
      const translation = i18n.global.t(translationKey)
      return translation !== translationKey ? translation : type
    }
    
    const getFileTypeBadgeClass = (type) => {
      const classes = {
        'income': 'bg-success',
        'eod_report': 'bg-info',
        'eod_simple': 'bg-primary',
        'eod_detailed': 'bg-primary',
        'comprehensive': 'bg-warning',
        'stock': 'bg-secondary',
        'unknown': 'bg-light text-dark'
      }
      return classes[type] || 'bg-light text-dark'
    }

    const getDifferenceReportTitle = () => {
      if (hasAdjustment.value) {
        return t('eod.report_viewer.difference_adjustment_report_title')
      }
      return t('eod.report_viewer.difference_report_title')
    }
    
    // 生命周期
    onMounted(() => {
      loadReportData()
    })
    
    return {
      loading,
      error,
      eodInfo,
      pdfFiles,
      incomeReportUrl,
      cashoutReportUrl,
      showPdfFallback,
      loadReportData,
      refreshReports,
      goBack,
      formatDate,
      formatDateTime,
      formatFileSize,
      getFileTypeLabel,
      getFileTypeBadgeClass,
      getDifferenceReportTitle
    }
  }
}
</script>

<style scoped>
.eod-report-viewer {
  min-height: 100vh;
  background-color: #f8f9fa;
  padding: 1rem;
}

.pdf-frame {
  width: 100%;
  height: 100%;
}

.pdf-fallback-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.95);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.pdf-container {
  position: relative;
  height: 70vh;
  border: 1px solid #dee2e6;
  border-radius: 0.375rem;
  overflow: hidden;
}

.card {
  box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
}

.card-header {
  background-color: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
}

.card-header h6 {
  color: #495057;
}

.table-responsive {
  font-size: 0.9rem;
}

.btn-toolbar {
  display: flex;
  gap: 0.5rem;
}

@media (max-width: 768px) {
  .pdf-container {
    height: 50vh;
  }
  
  .col-md-6 {
    margin-bottom: 1rem;
  }
}
</style> 
<template>
  <div class="container-fluid py-4">
    <div class="row">
      <div class="col-12">
        <div class="d-flex justify-content-between align-items-center mb-4">
          <h2>
            <font-awesome-icon :icon="['fas', 'history']" class="me-2" />
            {{ $t('eod.history_page.title') }}
          </h2>
          <div>
            <button @click="refreshHistory" class="btn btn-outline-primary">
              <font-awesome-icon :icon="['fas', 'sync-alt']" class="me-1" />
              {{ $t('eod.history_page.refresh') }}
            </button>
          </div>
        </div>

        <!-- 搜索筛选区域 -->
        <div class="card mb-4">
          <div class="card-body">
            <div class="row g-3">
              <div class="col-md-4">
                <label class="form-label">{{ $t('eod.history_page.start_date') }}</label>
                <input 
                  type="date" 
                  class="form-control" 
                  v-model="filters.start_date"
                  @change="searchHistory"
                />
              </div>
              <div class="col-md-4">
                <label class="form-label">{{ $t('eod.history_page.end_date') }}</label>
                <input 
                  type="date" 
                  class="form-control" 
                  v-model="filters.end_date"
                  @change="searchHistory"
                />
              </div>
              <div class="col-md-4">
                <label class="form-label">{{ $t('eod.history_page.status') }}</label>
                <select class="form-control" v-model="filters.status" @change="searchHistory">
                  <option value="">{{ $t('eod.history_page.all') }}</option>
                  <option value="completed">{{ $t('eod.history_page.completed') }}</option>
                  <option value="cancelled">{{ $t('eod.history_page.cancelled') }}</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <!-- 历史记录列表 -->
        <div class="card">
          <div class="card-header">
            <h5 class="mb-0">{{ $t('eod.history_page.title') }}</h5>
          </div>
          <div class="card-body">
            <div v-if="loading" class="text-center py-4">
              <font-awesome-icon :icon="['fas', 'spinner']" spin class="fa-2x text-primary" />
              <p class="mt-2">{{ $t('eod.history_page.loading') }}</p>
            </div>

            <div v-else-if="error" class="alert alert-danger">
              <font-awesome-icon :icon="['fas', 'exclamation-circle']" class="me-2" />
              {{ error }}
            </div>

            <div v-else-if="historyList.length === 0" class="text-center py-4">
              <font-awesome-icon :icon="['fas', 'inbox']" class="fa-3x text-muted mb-3" />
              <p class="text-muted">{{ $t('eod.history_page.no_data') }}</p>
            </div>

            <div v-else>
              <div class="table-responsive">
                <table class="table table-hover eod-history-table">
                  <thead>
                    <tr>
                      <th>{{ isMobile ? 'ID' : $t('eod.eod_id') }}</th>
                      <th>{{ $t('eod.date') }}</th>
                      <th>{{ $t('common.start_time') }}</th>
                      <th>{{ $t('common.end_time') }}</th>
                      <th v-if="!isMobile">{{ $t('eod.history_page.operator') }}</th>
                      <th v-if="!isMobile">{{ $t('eod.history_page.print_count') }}</th>
                      <th>{{ $t('eod.history_page.status') }}</th>
                      <th>{{ $t('eod.history_page.actions') }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="record in historyList" :key="record.id">
                      <td class="fw-bold text-primary">{{ record.id }}</td>
                      <td>{{ formatDate(record.date) }}</td>
                      <td>{{ formatDateTime(record.started_at) }}</td>
                      <td>{{ formatDateTime(record.completed_at) }}</td>
                      <td v-if="!isMobile">{{ record.started_by }}</td>
                      <td v-if="!isMobile">
                        <span class="badge bg-secondary">{{ record.print_count }}</span>
                      </td>
                      <td>
                        <span :class="getStatusClass(record.status)">
                          {{ getStatusText(record.status) }}
                        </span>
                      </td>
                      <td>
                        <div class="btn-group" role="group">
                          <button 
                            @click="reprintReports(record.id)"
                            class="btn btn-sm btn-outline-success"
                            :title="$t('eod.history_page.view_pdf_reports')"
                            :disabled="record.status !== 'completed'"
                          >
                            <font-awesome-icon :icon="['fas', 'eye']" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <!-- 分页 -->
              <nav v-if="pagination.pages > 1" class="mt-4">
                <ul class="pagination justify-content-center">
                  <li class="page-item" :class="{ disabled: pagination.page <= 1 }">
                    <button 
                      @click="changePage(pagination.page - 1)"
                      class="page-link"
                      :disabled="pagination.page <= 1"
                    >
                      {{ $t('eod.history_page.previous') }}
                    </button>
                  </li>
                  
                  <li 
                    v-for="page in getPageNumbers()" 
                    :key="page"
                    class="page-item"
                    :class="{ active: page === pagination.page }"
                  >
                    <button @click="changePage(page)" class="page-link">{{ page }}</button>
                  </li>
                  
                  <li class="page-item" :class="{ disabled: pagination.page >= pagination.pages }">
                    <button 
                      @click="changePage(pagination.page + 1)"
                      class="page-link"
                      :disabled="pagination.page >= pagination.pages"
                    >
                      {{ $t('eod.history_page.next') }}
                    </button>
                  </li>
                </ul>
              </nav>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 移动端PDF查看器模态框 -->
    <div v-if="showMobilePdfModal" class="mobile-pdf-modal" @click="closeMobilePdfModal">
      <div class="mobile-pdf-container" @click.stop>
        <div class="mobile-pdf-header">
          <div class="header-left">
            <button @click="closeMobilePdfModal" class="back-btn">
              <i class="fas fa-arrow-left"></i>
              <span>{{ $t('common.back') }}</span>
            </button>
            <h4>{{ $t('eod.history_page.report_view') }}</h4>
          </div>
          <button @click="closeMobilePdfModal" class="close-btn">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="mobile-pdf-content">
          <div v-if="mobilePdfLoading" class="loading-container">
            <div class="spinner"></div>
            <p>正在加载PDF...</p>
          </div>
          <div v-else-if="mobilePdfError" class="error-container">
            <i class="fas fa-exclamation-circle"></i>
            <p>{{ mobilePdfError }}</p>
            <button @click="loadMobilePdfs" class="retry-btn">重试</button>
          </div>
          <div v-else-if="mobilePdfUrls.length > 0" class="pdf-list">
            <div 
              v-for="(pdfUrl, index) in mobilePdfUrls" 
              :key="index"
              class="pdf-item"
            >
              <h5>{{ $t('eod.history_page.report') }} {{ index + 1 }}</h5>
              <div class="pdf-container" :ref="el => { if (el) pdfContainers[index] = el }">
                <iframe 
                  :src="pdfUrl" 
                  class="pdf-iframe"
                  frameborder="0"
                  :title="`${$t('eod.history_page.report')} ${index + 1}`"
                  @load="adjustPdfScale(index)"
                ></iframe>
              </div>
            </div>
          </div>
          <div v-else class="empty-container">
            <i class="fas fa-file-alt"></i>
            <p>暂无PDF文件</p>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import endOfDayService from '@/services/api/endOfDayService'

export default {
  name: 'EODHistoryView',
  data() {
    return {
      loading: false,
      error: null,
      historyList: [],
      filters: {
        start_date: '',
        end_date: '',
        status: ''
      },
      pagination: {
        page: 1,
        per_page: 20,
        total: 0,
        pages: 0
      },
      // 移动端PDF查看器相关数据
      showMobilePdfModal: false,
      mobilePdfLoading: false,
      mobilePdfError: null,
      mobilePdfUrls: [],
      currentEodId: null,
      pdfContainers: []
    }
  },
  computed: {
    isMobile() {
      return window.innerWidth <= 768
    }
  },
  mounted() {
    this.initDateFilter()
    this.loadHistory()
  },
  methods: {
    initDateFilter() {
      // 默认显示最近30天的记录
      const endDate = new Date()
      const startDate = new Date()
      startDate.setDate(startDate.getDate() - 30)
      
      this.filters.end_date = endDate.toISOString().split('T')[0]
      this.filters.start_date = startDate.toISOString().split('T')[0]
    },

    async loadHistory() {
      this.loading = true
      this.error = null

      try {
        const params = {
          page: this.pagination.page,
          per_page: this.pagination.per_page,
          start_date: this.filters.start_date,
          end_date: this.filters.end_date
        }

        const response = await endOfDayService.getEodHistory(params)
        
        if (response.data && response.data.success) {
          this.historyList = response.data.data.records
          this.pagination = response.data.data.pagination
        } else {
          throw new Error(response.data?.message || '获取历史记录失败')
        }
      } catch (error) {
        console.error('加载日结历史失败:', error)
        this.error = error.response?.data?.message || error.message || '获取历史记录失败'
      } finally {
        this.loading = false
      }
    },

    async reprintReports(eodId) {
      if (!eodId) return

      // 检查是否为移动端
      const isMobile = window.innerWidth <= 768
      
      if (isMobile) {
        // 移动端直接在当前页面显示PDF，无需跳转
        this.showMobilePdfViewer(eodId)
        return
      }

      // 桌面端直接跳转到已经实现的PDF查看页面
      this.$router.push({
        name: 'EODReportViewer',
        params: { eodId: eodId }
      })
    },

    // 移动端PDF查看器
    showMobilePdfViewer(eodId) {
      this.currentEodId = eodId
      this.showMobilePdfModal = true
      this.pdfContainers = []
      this.loadMobilePdfs()
    },

    // 加载移动端PDF
    async loadMobilePdfs() {
      if (!this.currentEodId) return
      
      this.mobilePdfLoading = true
      this.mobilePdfError = null
      this.mobilePdfUrls = []
      
      try {
        const response = await endOfDayService.getEodPdfFiles(this.currentEodId)
        
        if (response.data && response.data.success) {
          const pdfFiles = response.data.data.pdf_files || []
          
          if (pdfFiles.length === 0) {
            this.mobilePdfError = '没有找到相关的PDF文件'
            return
          }
          
          // 调试信息：打印所有PDF文件
          console.log('所有PDF文件:', pdfFiles.map(f => f.filename))
          console.log('当前EOD ID:', this.currentEodId)
          console.log('查找的EOD模式:', `EOD${this.currentEodId}`)
          
          // 获取当前语言
          const currentLanguage = this.$i18n.locale || 'zh'
          console.log('当前语言代码:', currentLanguage)
          
          // 根据当前语言过滤PDF文件
          const currentEodFiles = pdfFiles.filter(file => {
            console.log(`检查文件: ${file.filename}`)
            
            if (!file.filename) {
              console.log(`  - 文件名为空，跳过`)
              return false
            }
            
            // 检查文件名是否包含EOD ID（支持EOD和E0D两种格式）
            const eodPattern = `E[O0]D${this.currentEodId}`
            if (!file.filename.includes(`EOD${this.currentEodId}`) && !file.filename.includes(`E0D${this.currentEodId}`)) {
              console.log(`  - 不包含EOD模式 "${eodPattern}"，跳过`)
              return false
            }
            
            console.log(`  - 包含EOD模式，继续检查语言`)
            
            // 根据当前语言选择对应的PDF文件
            if (currentLanguage === 'zh' || currentLanguage === 'zh-CN' || currentLanguage === 'zh-TW') {
              // 中文：选择没有语言后缀的文件（文件名以.pdf结尾，不包含_en或_th）
              const isChinese = file.filename.endsWith('.pdf') && 
                               !file.filename.includes('_en') && 
                               !file.filename.includes('_th')
              console.log(`  - 中文检查结果: ${isChinese}`)
              return isChinese
            } else if (currentLanguage === 'en' || currentLanguage === 'en-US' || currentLanguage === 'en-GB') {
              // 英文：选择_en后缀的文件
              const isEnglish = file.filename.includes('_en') && file.filename.endsWith('.pdf')
              console.log(`  - 英文检查结果: ${isEnglish}`)
              return isEnglish
            } else if (currentLanguage === 'th' || currentLanguage === 'th-TH') {
              // 泰文：选择_th后缀的文件
              const isThai = file.filename.includes('_th') && file.filename.endsWith('.pdf')
              console.log(`  - 泰文检查结果: ${isThai}`)
              return isThai
            }
            
            console.log(`  - 未知语言，跳过`)
            return false
          }).slice(0, 2)
          
          // 调试信息：打印过滤后的文件
          console.log(`当前语言(${currentLanguage})过滤后的文件:`, currentEodFiles.map(f => f.filename))
          
          if (currentEodFiles.length === 0) {
            this.mobilePdfError = `没有找到当前语言(${currentLanguage})的PDF文件`
            return
          }
          
          // 为每个PDF文件创建blob URL
          for (const file of currentEodFiles) {
            try {
              const pdfResponse = await endOfDayService.getEodPdfFile(this.currentEodId, file.filename)
              if (pdfResponse.data instanceof Blob) {
                const blobUrl = window.URL.createObjectURL(pdfResponse.data)
                this.mobilePdfUrls.push(blobUrl)
              }
            } catch (err) {
              console.error('加载PDF文件失败:', err)
            }
          }
          
          if (this.mobilePdfUrls.length === 0) {
            this.mobilePdfError = '无法加载PDF文件'
          }
        } else {
          throw new Error(response.data?.message || '获取PDF文件列表失败')
        }
      } catch (error) {
        console.error('加载PDF失败:', error)
        this.mobilePdfError = error.response?.data?.message || error.message || '加载PDF失败'
      } finally {
        this.mobilePdfLoading = false
      }
    },

    // 动态调整PDF缩放比例 - 保守缩放
    adjustPdfScale(index) {
      this.$nextTick(() => {
        // 延迟执行，确保PDF完全加载
        setTimeout(() => {
          try {
            const container = this.pdfContainers[index]
            
            if (!container) {
              console.log(`PDF ${index + 1} 容器未找到`)
              return
            }
            
            const iframe = container.querySelector('.pdf-iframe')
            
            if (!iframe) {
              console.log(`PDF ${index + 1} iframe未找到`)
              return
            }
            
            // 获取容器实际尺寸
            const containerWidth = container.offsetWidth
            const containerHeight = container.offsetHeight
            
            console.log(`PDF ${index + 1} 容器尺寸: ${containerWidth}x${containerHeight}`)
            
                      // 使用更保守的缩放比例，确保不出现横向滚动
          const scale = Math.min(containerWidth / 700, 0.65)
            
            // 应用缩放
            iframe.style.transform = `scale(${scale})`
            iframe.style.transformOrigin = 'center center'
            
            // 减少内部边距
            iframe.style.margin = '0'
            iframe.style.padding = '0'
            
            // 确保iframe不会超出容器边界
            iframe.style.maxWidth = '100%'
            iframe.style.maxHeight = '100%'
            iframe.style.overflow = 'auto'
            
            console.log(`PDF ${index + 1} 应用缩放: ${scale} (容器宽度: ${containerWidth})`)
            
          } catch (error) {
            console.error(`PDF ${index + 1} 缩放调整失败:`, error)
          }
        }, 1500) // 等待1.5秒确保PDF完全加载
      })
    },

    // 关闭移动端PDF查看器
    closeMobilePdfModal() {
      this.showMobilePdfModal = false
      this.mobilePdfLoading = false
      this.mobilePdfError = null
      // 清理blob URLs
      this.mobilePdfUrls.forEach(url => {
        window.URL.revokeObjectURL(url)
      })
      this.mobilePdfUrls = []
      this.pdfContainers = []
      this.currentEodId = null
    },

    searchHistory() {
      this.pagination.page = 1
      this.loadHistory()
    },

    refreshHistory() {
      this.loadHistory()
    },

    changePage(page) {
      if (page >= 1 && page <= this.pagination.pages) {
        this.pagination.page = page
        this.loadHistory()
      }
    },

    getPageNumbers() {
      const current = this.pagination.page
      const total = this.pagination.pages
      const delta = 2
      const range = []
      
      for (let i = Math.max(1, current - delta); i <= Math.min(total, current + delta); i++) {
        range.push(i)
      }
      
      return range
    },

    // 格式化函数
    formatDate(dateStr) {
      if (!dateStr) return '-'
      
      // 获取当前语言
      const currentLanguage = localStorage.getItem('language') || 'zh-CN'
      
      // 根据语言设置不同的格式
      if (currentLanguage === 'en-US') {
        return new Date(dateStr).toLocaleDateString('en-US')
      } else if (currentLanguage === 'th-TH') {
        return new Date(dateStr).toLocaleDateString('th-TH')
      } else {
        // 默认中文格式
        return new Date(dateStr).toLocaleDateString('zh-CN')
      }
    },

    formatDateTime(dateStr) {
      if (!dateStr) return '-'
      
      // 获取当前语言
      const currentLanguage = localStorage.getItem('language') || 'zh-CN'
      
      // 根据语言设置不同的格式
      if (currentLanguage === 'en-US') {
        return new Date(dateStr).toLocaleString('en-US')
      } else if (currentLanguage === 'th-TH') {
        return new Date(dateStr).toLocaleString('th-TH')
      } else {
        // 默认中文格式
        return new Date(dateStr).toLocaleString('zh-CN')
      }
    },

    getEodDate(eodId) {
      // 从历史记录中找到对应的日期
      const record = this.historyList.find(item => item.id === eodId)
      return record ? record.date : ''
    },

    formatCurrency(amount) {
      if (typeof amount !== 'number') {
        amount = parseFloat(amount) || 0
      }
      return new Intl.NumberFormat('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(amount)
    },

    getStatusClass(status) {
      const classes = {
        'completed': 'badge bg-success',
        'cancelled': 'badge bg-danger',
        'processing': 'badge bg-warning',
        'failed': 'badge bg-danger'
      }
      return classes[status] || 'badge bg-secondary'
    },

    getStatusText(status) {
      const texts = {
        'completed': this.$t('common.completed'),
        'cancelled': this.$t('common.cancelled'),
        'processing': this.$t('common.processing'),
        'failed': this.$t('common.failed')
      }
      return texts[status] || status
    },

    getDifferenceClass(difference) {
      const amount = parseFloat(difference) || 0
      if (amount > 0) return 'text-success'
      if (amount < 0) return 'text-danger'
      return 'text-muted'
    },

    getCurrencyCode(currencyId) {
      // 这里可以从store获取货币信息
      return `Currency-${currencyId}`
    },

    // PDF文件相关方法
    openPdfFile(url) {
      window.open(url, '_blank')
    },

    // 差额报告相关方法
    hasDifferenceReport(eodId) {
      // 检查是否存在差额报告文件
      // 这里可以根据EOD记录的状态或其他条件来判断
      // 暂时返回true，实际应该根据文件存在性来判断
      console.log('检查差额报告是否存在，EOD ID:', eodId)
      return true
    },

    viewDifferenceReport(eodId) {
      // 获取当前语言
      const currentLanguage = localStorage.getItem('language') || 'zh-CN'
      let languageSuffix = ''
      
      if (currentLanguage === 'en-US') {
        languageSuffix = '_en'
      } else if (currentLanguage === 'th-TH') {
        languageSuffix = '_th'
      }
      
      // 构建差额报告文件路径
      const reportPath = `/manager/2025/07/${eodId.toString().padStart(3, '0')}EOD${eodId}Diff${languageSuffix}.pdf`
      
      // 打开差额报告
      this.openPdfFile(reportPath)
    },

    getFileTypeLabel(type) {
      const typeLabels = {
        'eod_simple': '日结简单报表',
        'eod_detailed': '日结详细报表',
        'eod_report': '日结报表',
        'comprehensive': '综合报表',
        'income': '收入报表',
        'stock': '库存报表',
        'difference': '差额报告',
        'difference_adjustment': '差额调节报告',
        'unknown': '其他报表'
      }
      return typeLabels[type] || '报表文件'
    },

    formatFileSize(bytes) {
      if (bytes === 0) return '0 B'
      const k = 1024
      const sizes = ['B', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    },


  }
}
</script>

<style scoped>
.table th {
  background-color: #f8f9fa;
  font-weight: 600;
  border-top: none;
}

.card {
  box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
  border: 1px solid rgba(0, 0, 0, 0.125);
}

.btn-group .btn {
  border-radius: 0.25rem;
  margin-right: 0.25rem;
}

.btn-group .btn:last-child {
  margin-right: 0;
}

.modal-xl {
  max-width: 1200px;
}

.table-responsive {
  max-height: 400px;
  overflow-y: auto;
}

@media (max-width: 768px) {
  .btn-group {
    display: flex;
    flex-direction: column;
  }
  
  .btn-group .btn {
    margin-right: 0;
    margin-bottom: 0.25rem;
  }
  
  .table-responsive {
    font-size: 0.875rem;
  }
  
  /* 修复移动端绿色条问题 */
  .eod-history-table {
    border-collapse: collapse !important;
  }
  
  .eod-history-table th,
  .eod-history-table td {
    border: 1px solid #dee2e6 !important;
    padding: 8px;
    vertical-align: middle;
  }
  
  .eod-history-table .table-responsive {
    border: none !important;
  }
  
  /* 移除可能的绿色边框 */
  .eod-history-table * {
    border-color: #dee2e6 !important;
  }
  
  /* 确保操作列没有特殊样式 */
  .eod-history-table td:last-child {
    border-right: 1px solid #dee2e6 !important;
  }
  
  /* 强制移除所有绿色边框 */
  .table-responsive {
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
  }
  
  .table {
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
  }
  
  .table th,
  .table td {
    border-color: #dee2e6 !important;
    outline: none !important;
    box-shadow: none !important;
  }
  
  /* 特别针对操作列的边框处理 */
  .table th:last-child,
  .table td:last-child {
    border-right: 1px solid #dee2e6 !important;
    border-left: 1px solid #dee2e6 !important;
    outline: none !important;
    box-shadow: none !important;
  }
  
  /* 移除所有可能的绿色样式 */
  .table th:last-child *,
  .table td:last-child * {
    border-color: #dee2e6 !important;
    outline: none !important;
    box-shadow: none !important;
    background-color: transparent !important;
  }
  
  /* 确保按钮组没有绿色边框 */
  .btn-group {
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
  }
  
  .btn-group .btn {
    border-color: #dee2e6 !important;
    outline: none !important;
    box-shadow: none !important;
  }
  
  /* 移除可能的滚动条样式 */
  .table-responsive::-webkit-scrollbar {
    width: 0 !important;
    background: transparent !important;
  }
  
  .table-responsive::-webkit-scrollbar-track {
    background: transparent !important;
  }
  
  .table-responsive::-webkit-scrollbar-thumb {
    background: transparent !important;
  }
  
  /* 全局移除所有绿色边框和样式 */
  .eod-history-table,
  .eod-history-table *,
  .table-responsive,
  .table-responsive *,
  .table,
  .table * {
    border-color: #dee2e6 !important;
    outline-color: transparent !important;
    box-shadow: none !important;
  }
  
  /* 特别处理可能的绿色背景 */
  .eod-history-table,
  .eod-history-table *,
  .table-responsive,
  .table-responsive *,
  .table,
  .table * {
    background-color: transparent !important;
  }
  
  /* 确保操作列按钮没有绿色边框 */
  .btn-success,
  .btn-success * {
    border-color: #198754 !important;
    background-color: #198754 !important;
  }
  
  /* 特别处理outline-success按钮 */
  .btn-outline-success {
    border-color: #198754 !important;
    color: #198754 !important;
    background-color: transparent !important;
  }
  
  .btn-outline-success:hover {
    border-color: #198754 !important;
    background-color: #198754 !important;
    color: white !important;
  }
  
  /* 确保按钮组容器没有绿色边框 */
  .btn-group {
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    background-color: transparent !important;
  }
  
  /* 移除按钮组内所有可能的绿色边框 */
  .btn-group * {
    border-color: #198754 !important;
    outline: none !important;
    box-shadow: none !important;
  }
  
  /* 移除所有可能的绿色高亮 */
  .table-hover tbody tr:hover {
    background-color: rgba(0, 123, 255, 0.1) !important;
  }
  
  /* 彻底移除所有绿色边框 - 最强规则 */
  .eod-history-table,
  .eod-history-table *,
  .table-responsive,
  .table-responsive *,
  .table,
  .table *,
  .card,
  .card * {
    border-right-color: #dee2e6 !important;
    border-left-color: #dee2e6 !important;
    border-top-color: #dee2e6 !important;
    border-bottom-color: #dee2e6 !important;
    outline: none !important;
    box-shadow: none !important;
  }
  
  /* 特别处理表格右边框 */
  .table-responsive {
    border-right: none !important;
  }
  
  .table {
    border-right: none !important;
  }
  
  .table th:last-child,
  .table td:last-child {
    border-right: 1px solid #dee2e6 !important;
  }
  
  /* 移除所有可能的绿色背景和边框 */
  * {
    border-color: #dee2e6 !important;
  }
  
  /* 确保没有绿色边框 */
  .eod-history-table td:last-child,
  .eod-history-table th:last-child {
    border-right: 1px solid #dee2e6 !important;
    border-left: 1px solid #dee2e6 !important;
    border-top: 1px solid #dee2e6 !important;
    border-bottom: 1px solid #dee2e6 !important;
  }
  
  /* 修复按钮圆角边框问题 */
  .btn-group {
    border-radius: 0 !important;
    overflow: hidden !important;
  }
  
  .btn-group .btn {
    border-radius: 0 !important;
    margin: 0 !important;
    border-right: none !important;
  }
  
  .btn-group .btn:last-child {
    border-right: 1px solid #198754 !important;
  }
  
  /* 确保按钮没有放大的圆角 */
  .btn-outline-success {
    border-radius: 4px !important;
    overflow: hidden !important;
  }
  
  /* 移除可能的伪元素边框 */
  .btn-group::before,
  .btn-group::after,
  .btn::before,
  .btn::after {
    display: none !important;
    content: none !important;
  }
  
  /* 确保按钮组容器没有额外的边框 */
  .btn-group {
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    background: transparent !important;
  }
  
  /* 彻底修复按钮边框问题 */
  .eod-history-table td:last-child .btn-group {
    position: relative !important;
    overflow: visible !important;
  }
  
  .eod-history-table td:last-child .btn-group .btn {
    position: relative !important;
    z-index: 1 !important;
    border: 1px solid #198754 !important;
    border-radius: 4px !important;
    background: transparent !important;
    color: #198754 !important;
  }
  
  /* 移除任何可能的边框放大效果 */
  .eod-history-table td:last-child .btn-group .btn:hover,
  .eod-history-table td:last-child .btn-group .btn:focus,
  .eod-history-table td:last-child .btn-group .btn:active {
    border: 1px solid #198754 !important;
    border-radius: 4px !important;
    transform: none !important;
    scale: 1 !important;
  }
  
  /* 确保没有伪元素造成边框问题 */
  .eod-history-table td:last-child .btn-group .btn::before,
  .eod-history-table td:last-child .btn-group .btn::after {
    display: none !important;
    content: none !important;
    border: none !important;
    background: none !important;
  }
  
  /* 直接移除操作列的右边框 */
  .eod-history-table td:last-child {
    border-right: none !important;
    padding-right: 0 !important;
  }
  
  /* 移动端PDF查看器样式 */
  .mobile-pdf-modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.8);
    z-index: 9999;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 5px;
    box-sizing: border-box;
  }
  
  .mobile-pdf-container {
    width: 98%;
    height: 95%;
    background: white;
    border-radius: 4px;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    margin: 10px auto;
  }
  
  .mobile-pdf-header {
    background: #007bff;
    color: white;
    padding: 8px 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 4px;
  }
  
  .mobile-pdf-header .header-left {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .mobile-pdf-header .back-btn {
    background: rgba(255, 255, 255, 0.2);
    border: none;
    color: white;
    font-size: 14px;
    cursor: pointer;
    padding: 6px 10px;
    border-radius: 4px;
    transition: background-color 0.2s;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  
  .mobile-pdf-header .back-btn:hover {
    background-color: rgba(255, 255, 255, 0.1);
  }
  
  .mobile-pdf-header h4 {
    margin: 0;
    font-size: 18px;
  }
  
  .mobile-pdf-header .close-btn {
    background: none;
    border: none;
    color: white;
    font-size: 20px;
    cursor: pointer;
  }
  
  .mobile-pdf-content {
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    padding: 0;
    margin: 0;
    width: 100%;
    background: #fff;
  }
  
  /* 确保PDF在移动端自适应 */
  @media (max-width: 768px) {
    .pdf-container {
      height: 55vh;
      min-height: 300px;
      margin: 0;
      padding: 0;
      border-radius: 0;
      background: #fff;
      justify-content: center;
    }
    
    .pdf-iframe {
      transform: scale(0.7);
      transform-origin: center center;
      width: 100%;
      height: 100%;
    }
    
    .pdf-item {
      margin-bottom: 12px;
      border-radius: 4px;
    }
    
    .pdf-item h5 {
      padding: 8px 12px;
      font-size: 14px;
    }
  }
  
  .loading-container,
  .error-container,
  .empty-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 200px;
    text-align: center;
  }
  
  .spinner {
    width: 40px;
    height: 40px;
    border: 4px solid #f3f3f3;
    border-top: 4px solid #007bff;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  .pdf-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
    width: 100%;
  }
  
  .pdf-item {
    border: 1px solid #dee2e6;
    border-radius: 4px;
    overflow: hidden;
    width: 100%;
    margin-bottom: 12px;
  }
  
  .pdf-item h5 {
    background: #f8f9fa;
    margin: 0;
    padding: 4px 8px;
    border-bottom: 1px solid #dee2e6;
    font-size: 12px;
  }
  
  .pdf-iframe {
    width: 100%;
    height: 100%;
    border: none;
    display: block;
    transform-origin: center center;
    transition: transform 0.3s ease;
    background: #fff;
  }
  

  
  .pdf-container {
    width: 100%;
    height: 60vh;
    overflow: auto;
    position: relative;
    background: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 400px;
    padding: 0;
    margin: 0;
  }
  
  .retry-btn {
    background: #007bff;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    cursor: pointer;
    margin-top: 10px;
  }
  
  .eod-history-table th:last-child {
    border-right: none !important;
    padding-right: 0 !important;
  }
  
  /* 确保表格容器没有右边框 */
  .eod-history-table {
    border-right: none !important;
  }
  
  .table-responsive {
    border-right: none !important;
    padding-right: 0 !important;
  }
  
  /* 移除所有可能的右边框 */
  .eod-history-table * {
    border-right: none !important;
  }
  
  /* 特别处理操作列 */
  .eod-history-table td:last-child * {
    border-right: none !important;
    border-left: none !important;
    border-top: none !important;
    border-bottom: none !important;
  }
  
  /* 恢复状态列的正常显示 */
  .eod-history-table td .badge {
    border-radius: 3px !important;
    padding: 2px 6px !important;
    font-size: 10px !important;
    line-height: 1.2 !important;
  }
  
  /* 不同状态的颜色 */
  .eod-history-table td .badge.bg-success {
    background-color: #198754 !important;
    color: white !important;
    border: 1px solid #198754 !important;
  }
  
  .eod-history-table td .badge.bg-warning {
    background-color: #ffc107 !important;
    color: #000 !important;
    border: 1px solid #ffc107 !important;
  }
  
  .eod-history-table td .badge.bg-danger {
    background-color: #dc3545 !important;
    color: white !important;
    border: 1px solid #dc3545 !important;
  }
  
  .eod-history-table td .badge.bg-secondary {
    background-color: #6c757d !important;
    color: white !important;
    border: 1px solid #6c757d !important;
  }
  
  /* 恢复操作按钮的正常显示 */
  .eod-history-table td:last-child .btn-outline-success {
    border: 1px solid #198754 !important;
    background-color: transparent !important;
    color: #198754 !important;
    border-radius: 4px !important;
    padding: 6px 12px !important;
    font-size: 12px !important;
    transition: all 0.2s ease !important;
    min-width: 40px !important;
    width: auto !important;
  }
  
  .eod-history-table td:last-child .btn-outline-success:hover {
    background-color: #198754 !important;
    color: white !important;
    border-color: #198754 !important;
  }
  
  /* 确保眼睛图标显示正常 */
  .eod-history-table td:last-child .btn-outline-success .fa-eye {
    font-size: 12px !important;
    width: 12px !important;
    height: 12px !important;
  }
  
  .eod-history-table td:last-child .btn-outline-success:focus {
    background-color: #198754 !important;
    color: white !important;
    border-color: #198754 !important;
    box-shadow: 0 0 0 0.2rem rgba(25, 135, 84, 0.25) !important;
  }
  
  .eod-history-table td:last-child .btn-outline-success:active {
    background-color: #146c43 !important;
    color: white !important;
    border-color: #146c43 !important;
  }
  
  /* 恢复按钮组容器的正常显示 */
  .eod-history-table td:last-child .btn-group {
    border: none !important;
    background: transparent !important;
  }
}
</style> 
<template>
  <div class="mobile-eod-report-viewer">
    <!-- 顶部导航 -->
    <div class="viewer-header">
      <div class="header-left">
        <button @click="goBack" class="back-btn">
          <i class="fas fa-arrow-left"></i>
        </button>
        <h3 class="viewer-title">日结报表查看器</h3>
      </div>
      <div class="header-right">
        <button @click="refreshReports" class="refresh-btn" :disabled="loading">
          <i class="fas fa-sync-alt" :class="{ 'fa-spin': loading }"></i>
        </button>
      </div>
    </div>

    <!-- 报表信息 -->
    <div class="report-info">
      <div class="info-item">
        <span class="label">日结编号:</span>
        <span class="value">{{ eodId }}</span>
      </div>
      <div class="info-item">
        <span class="label">日期:</span>
        <span class="value">{{ formatDate(eodDate) }}</span>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p>正在加载报表...</p>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-container">
      <i class="fas fa-exclamation-circle"></i>
      <p>{{ error }}</p>
      <button @click="loadReports" class="retry-btn">重试</button>
    </div>

    <!-- 报表列表 -->
    <div v-else-if="reports.length > 0" class="reports-list">
      <div 
        v-for="report in reports" 
        :key="report.filename"
        class="report-item"
        @click="viewReport(report)"
      >
        <div class="report-icon">
          <i class="fas fa-file-pdf"></i>
        </div>
        <div class="report-info">
          <div class="report-name">{{ report.displayName }}</div>
          <div class="report-meta">
            <span class="file-size">{{ formatFileSize(report.size) }}</span>
            <span class="file-date">{{ formatDate(report.modified) }}</span>
          </div>
        </div>
        <div class="report-actions">
          <button @click.stop="downloadReport(report)" class="download-btn">
            <i class="fas fa-download"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-container">
      <i class="fas fa-file-alt"></i>
      <p>暂无报表文件</p>
    </div>

    <!-- PDF查看模态框 -->
    <div v-if="showPdfViewer" class="pdf-modal" @click="closePdfViewer">
      <div class="pdf-container" @click.stop>
        <div class="pdf-header">
          <h4>{{ currentReport?.displayName }}</h4>
          <button @click="closePdfViewer" class="close-btn">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="pdf-content">
          <iframe 
            v-if="pdfUrl" 
            :src="pdfUrl" 
            class="pdf-iframe"
            frameborder="0"
          ></iframe>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import endOfDayService from '@/services/api/endOfDayService'

export default {
  name: 'MobileEODReportViewer',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const { locale } = useI18n()
    
    const eodId = ref(route.params.eodId)
    const eodDate = ref(route.query.date || '')
    const loading = ref(false)
    const error = ref(null)
    const reports = ref([])
    const showPdfViewer = ref(false)
    const currentReport = ref(null)
    const pdfUrl = ref('')

    // 根据当前语言过滤PDF文件
    const filterFilesByLanguage = (files) => {
      const currentLang = locale.value
      console.log('当前语言:', currentLang)
      
      return files.filter(file => {
        const filename = file.filename || file.name || ''
        console.log('检查文件:', filename)
        
        // 根据当前语言过滤文件
        if (currentLang === 'zh-CN') {
          // 中文版：只显示没有语言后缀或中文后缀的文件
          return !filename.includes('_en.') && !filename.includes('_th.')
        } else if (currentLang === 'th-TH') {
          // 泰语版：只显示泰语后缀的文件
          return filename.includes('_th.')
        } else if (currentLang === 'en-US') {
          // 英语版：只显示英语后缀的文件
          return filename.includes('_en.')
        } else {
          // 默认：显示没有语言后缀的文件
          return !filename.includes('_en.') && !filename.includes('_th.')
        }
      })
    }

    // 加载报表列表
    const loadReports = async () => {
      if (!eodId.value) return
      
      loading.value = true
      error.value = null
      
      try {
        const response = await endOfDayService.getEodPdfFiles(eodId.value)
        
        if (response.data && response.data.success) {
          // 检查数据格式，支持多种可能的响应结构
          let filesData = []
          if (response.data.data && Array.isArray(response.data.data)) {
            filesData = response.data.data
          } else if (response.data.data && response.data.data.pdf_files && Array.isArray(response.data.data.pdf_files)) {
            filesData = response.data.data.pdf_files
          } else if (response.data.pdf_files && Array.isArray(response.data.pdf_files)) {
            filesData = response.data.pdf_files
          } else if (Array.isArray(response.data)) {
            filesData = response.data
          }
          
          // 根据当前语言过滤文件
          const filteredFiles = filterFilesByLanguage(filesData)
          console.log('过滤后的文件:', filteredFiles)
          
          reports.value = filteredFiles.map(file => ({
            ...file,
            displayName: getDisplayName(file.filename || file.name || '未知文件')
          }))
        } else {
          throw new Error(response.data?.message || '获取报表文件失败')
        }
      } catch (err) {
        console.error('加载报表失败:', err)
        error.value = err.response?.data?.message || err.message || '获取报表文件失败'
      } finally {
        loading.value = false
      }
    }

    // 获取显示名称
    const getDisplayName = (filename) => {
      if (!filename) return '未知文件'
      
      const nameMap = {
        'income_report.pdf': '收入统计报表',
        'inventory_report.pdf': '库存统计报表',
        'summary_report.pdf': '汇总报表',
        'balance_report.pdf': '余额汇总报表',
        'eod_report.pdf': '日结报表',
        'comprehensive_report.pdf': '综合报表'
      }
      return nameMap[filename] || filename
    }

    // 查看报表
    const viewReport = async (report) => {
      try {
        const response = await endOfDayService.getEodPdfFile(eodId.value, report.filename)
        
        // 检查响应类型
        if (response.data instanceof Blob) {
          // 直接处理blob数据
          const blob = response.data
          const url = window.URL.createObjectURL(blob)
          pdfUrl.value = url
          currentReport.value = report
          showPdfViewer.value = true
        } else if (response.data && response.data.success) {
          // 检查URL格式，支持多种可能的响应结构
          let pdfUrlData = ''
          if (response.data.data && response.data.data.url) {
            pdfUrlData = response.data.data.url
          } else if (response.data.data && response.data.data.file_url) {
            pdfUrlData = response.data.data.file_url
          } else if (response.data.url) {
            pdfUrlData = response.data.url
          } else if (response.data.file_url) {
            pdfUrlData = response.data.file_url
          }
          
          if (pdfUrlData) {
            pdfUrl.value = pdfUrlData
            currentReport.value = report
            showPdfViewer.value = true
          } else {
            throw new Error('未找到PDF文件URL')
          }
        } else {
          throw new Error(response.data?.message || '获取报表文件失败')
        }
      } catch (err) {
        console.error('查看报表失败:', err)
        error.value = err.response?.data?.message || err.message || '查看报表失败'
      }
    }

    // 下载报表
    const downloadReport = async (report) => {
      try {
        console.log('开始下载报表:', report.filename)
        const response = await endOfDayService.getEodPdfFile(eodId.value, report.filename)
        
        console.log('API响应:', response)
        console.log('响应类型:', typeof response.data)
        console.log('是否为Blob:', response.data instanceof Blob)
        
        // 检查响应类型
        if (response.data instanceof Blob) {
          // 直接处理blob数据
          const blob = response.data
          console.log('Blob大小:', blob.size)
          console.log('Blob类型:', blob.type)
          
          const url = window.URL.createObjectURL(blob)
          const link = document.createElement('a')
          link.href = url
          link.download = report.filename || 'report.pdf'
          document.body.appendChild(link)
          link.click()
          document.body.removeChild(link)
          window.URL.revokeObjectURL(url)
          
          console.log('下载完成')
        } else if (response.data && response.data.success) {
          // 检查URL格式，支持多种可能的响应结构
          let downloadUrl = ''
          if (response.data.data && response.data.data.url) {
            downloadUrl = response.data.data.url
          } else if (response.data.data && response.data.data.file_url) {
            downloadUrl = response.data.data.file_url
          } else if (response.data.url) {
            downloadUrl = response.data.url
          } else if (response.data.file_url) {
            downloadUrl = response.data.file_url
          }
          
          if (downloadUrl) {
            const link = document.createElement('a')
            link.href = downloadUrl
            link.download = report.filename || 'report.pdf'
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
          } else {
            throw new Error('未找到下载URL')
          }
        } else {
          console.error('响应数据:', response.data)
          throw new Error(response.data?.message || '下载报表失败')
        }
      } catch (err) {
        console.error('下载报表失败:', err)
        console.error('错误详情:', err.response)
        error.value = err.response?.data?.message || err.message || '下载报表失败'
      }
    }

    // 刷新报表
    const refreshReports = () => {
      loadReports()
    }

    // 关闭PDF查看器
    const closePdfViewer = () => {
      showPdfViewer.value = false
      currentReport.value = null
      pdfUrl.value = ''
    }

    // 返回上一页
    const goBack = () => {
      router.back()
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

    // 格式化文件大小
    const formatFileSize = (bytes) => {
      if (!bytes) return '0 B'
      const k = 1024
      const sizes = ['B', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }

    onMounted(() => {
      loadReports()
    })

    return {
      eodId,
      eodDate,
      loading,
      error,
      reports,
      showPdfViewer,
      currentReport,
      pdfUrl,
      loadReports,
      viewReport,
      downloadReport,
      refreshReports,
      closePdfViewer,
      goBack,
      formatDate,
      formatFileSize
    }
  }
}
</script>

<style scoped>
.mobile-eod-report-viewer {
  min-height: 100vh;
  background: #f8f9fa;
}

.viewer-header {
  background: #007bff;
  color: white;
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.back-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
}

.viewer-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.refresh-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.report-info {
  background: white;
  padding: 16px;
  margin: 16px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.info-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.info-item:last-child {
  margin-bottom: 0;
}

.label {
  color: #666;
  font-weight: 500;
}

.value {
  color: #333;
  font-weight: 600;
}

.loading-container,
.error-container,
.empty-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-container i,
.empty-container i {
  font-size: 48px;
  color: #dc3545;
  margin-bottom: 16px;
}

.empty-container i {
  color: #6c757d;
}

.retry-btn {
  background: #007bff;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 6px;
  cursor: pointer;
  margin-top: 16px;
}

.reports-list {
  padding: 16px;
}

.report-item {
  background: white;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.report-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.report-icon {
  width: 48px;
  height: 48px;
  background: #f8f9fa;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #dc3545;
  font-size: 24px;
}

.report-info {
  flex: 1;
}

.report-name {
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.report-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #666;
}

.download-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.pdf-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pdf-container {
  background: white;
  border-radius: 8px;
  width: 95%;
  height: 90%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.pdf-header {
  padding: 16px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pdf-header h4 {
  margin: 0;
  font-size: 16px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #666;
}

.pdf-content {
  flex: 1;
  overflow: hidden;
}

.pdf-iframe {
  width: 100%;
  height: 100%;
  border: none;
}

@media (max-width: 480px) {
  .viewer-title {
    font-size: 16px;
  }
  
  .report-item {
    padding: 12px;
  }
  
  .report-icon {
    width: 40px;
    height: 40px;
    font-size: 20px;
  }
}
</style> 
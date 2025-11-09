<template>
  <div class="log-management">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2 class="page-title-bold">
        <font-awesome-icon :icon="['fas', 'file-alt']" class="me-2" />
        {{ $t('common.log_management') }}
      </h2>
    </div>

    <div class="row">
      <!-- 左侧主要区域：操作日志查询 (8列) -->
      <div class="col-lg-8">
        <!-- 操作日志查询条件 -->
        <div class="card mb-4">
          <div class="card-header">
            <h5 class="mb-0">{{ $t('logs.log_query') }}</h5>
          </div>
          <div class="card-body">
            <form @submit.prevent="handleSearch">
              <div class="row mb-3">
                <div class="col-md-3">
                  <div class="mb-3">
                    <label for="start-date" class="form-label">{{ $t('logs.start_date') }}</label>
                    <input
                      type="date"
                      id="start-date"
                      class="form-control"
                      v-model="searchForm.startDate"
                    />
                  </div>
                </div>
                <div class="col-md-3">
                  <div class="mb-3">
                    <label for="end-date" class="form-label">{{ $t('logs.end_date') }}</label>
                    <input
                      type="date"
                      id="end-date"
                      class="form-control"
                      v-model="searchForm.endDate"
                    />
                  </div>
                </div>
                <div class="col-md-3">
                  <div class="mb-3">
                    <label for="log-type" class="form-label">{{ $t('logs.log_type') }}</label>
                    <select
                      id="log-type"
                      class="form-select"
                      v-model="searchForm.logType"
                    >
                      <option value="all">{{ $t('logs.log_types.all') }}</option>
                      <option value="system">{{ $t('logs.log_types.system') }}</option>
                      <option value="login">{{ $t('logs.log_types.login') }}</option>
                      <option value="exchange">{{ $t('logs.log_types.exchange') }}</option>
                      <option value="rate">{{ $t('logs.log_types.rate') }}</option>
                      <option value="balance">{{ $t('logs.log_types.balance') }}</option>
                      <option value="end_of_day">{{ $t('logs.log_types.end_of_day') }}</option>
                      <option value="branch_management">{{ $t('logs.log_types.branch_management') }}</option>
                      <option value="system_manage">{{ $t('logs.log_types.system_manage') }}</option>
                    </select>
                  </div>
                </div>
                <div class="col-md-3">
                  <div class="mb-3">
                    <label for="operator" class="form-label">{{ $t('logs.operator') }}</label>
                    <input
                      type="text"
                      id="operator"
                      class="form-control"
                      :placeholder="$t('logs.enter_operator_name')"
                      v-model="searchForm.operator"
                    />
                  </div>
                </div>
              </div>
              
              <div class="d-flex justify-content-end">
                <button type="submit" class="btn btn-primary" :disabled="loading">
                  <i class="fas fa-search me-2"></i>
                  {{ loading ? $t('logs.searching') : $t('logs.search') }}
                </button>
              </div>
            </form>
          </div>
        </div>
        
        <!-- 操作日志查询结果表格 -->
        <div class="card">
          <div class="card-header d-flex justify-content-between align-items-center">
            <h5 class="mb-0">{{ $t('logs.log_list') }}</h5>
            <button type="button" class="btn btn-outline-secondary btn-sm" @click="exportLogs" :disabled="logs.length === 0">
              <i class="fas fa-file-export me-2"></i>
              {{ $t('logs.export_logs') }}
            </button>
          </div>
          <div class="card-body">
            <div v-if="loading" class="text-center py-4">
              <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">{{ $t('logs.loading') }}</span>
              </div>
            </div>
            <div v-else-if="error" class="alert alert-danger">
              {{ error }}
            </div>
            <div v-else class="table-responsive">
              <table class="table table-striped table-bordered table-hover">
                <thead>
                  <tr>
                    <th style="width: 5%">#</th>
                    <th style="width: 15%">{{ $t('logs.time') }}</th>
                    <th style="width: 10%">{{ $t('logs.type') }}</th>
                    <th style="width: 10%">{{ $t('logs.operator') }}</th>
                    <th style="width: 25%">{{ $t('logs.operation') }}</th>
                    <th style="width: 35%">{{ $t('logs.details') }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="logs.length === 0">
                    <td colspan="6" class="text-center py-3">{{ $t('logs.no_matching_records') }}</td>
                  </tr>
                  <tr v-for="log in logs" :key="log.id">
                    <td>{{ log.id }}</td>
                    <td>
                      {{ formatDateTime(log.created_at) }}
                      <br>
                      <small class="time-badge">{{ getTimeAgo(log.created_at) }}</small>
                    </td>
                    <td>
                      <span 
                        class="badge"
                        :class="getLogTypeBadgeClass(log.log_type)"
                      >
                        {{ getLogTypeText(log.log_type) }}
                      </span>
                    </td>
                    <td>{{ log.operator_name || $t('logs.unknown') }}</td>
                    <td>{{ log.action }}</td>
                    <td><small>{{ log.details || '-' }}</small></td>
                  </tr>
                </tbody>
              </table>
            </div>
            
            <div class="d-flex justify-content-between align-items-center mt-3" v-if="!loading && !error">
              <div>
                <small class="text-muted">{{ $t('logs.total_records', { count: total }) }}</small>
              </div>
              <div class="d-flex align-items-center gap-2">
                <button 
                  type="button" 
                  class="btn btn-outline-secondary btn-sm" 
                  @click="goToPage(1)"
                  :disabled="currentPage <= 1"
                >
                  {{ $t('logs.first_page') }}
                </button>
                <button 
                  type="button" 
                  class="btn btn-outline-primary btn-sm" 
                  @click="previousPage"
                  :disabled="currentPage <= 1"
                >
                  {{ $t('logs.previous_page') }}
                </button>
                <span class="mx-2">{{ $t('logs.page_info', { current: currentPage, total: totalPages }) }}</span>
                <button 
                  type="button" 
                  class="btn btn-outline-primary btn-sm" 
                  @click="nextPage"
                  :disabled="currentPage >= totalPages"
                >
                  {{ $t('logs.next_page') }}
                </button>
                <button 
                  type="button" 
                  class="btn btn-outline-secondary btn-sm" 
                  @click="goToPage(totalPages)"
                  :disabled="currentPage >= totalPages"
                >
                  {{ $t('logs.last_page') }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧辅助区域：统计、管理操作和文件列表 (4列) -->
      <div class="col-lg-4">
        <!-- 日志统计卡片（紧凑版） -->
        <div class="row mb-2">
          <div class="col-6">
            <div class="card text-white bg-primary">
              <div class="card-body text-center py-2">
                <h6 class="card-title mb-0">{{ logStats?.current_log_size || '0 MB' }}</h6>
                <small class="card-text">{{ $t('logManagement.current_log_size') }}</small>
              </div>
            </div>
          </div>
          <div class="col-6">
            <div class="card text-white bg-info">
              <div class="card-body text-center py-2">
                <h6 class="card-title mb-0">{{ logStats?.total_logs_count || 0 }}</h6>
                <small class="card-text">{{ $t('logManagement.total_logs_count') }}</small>
              </div>
            </div>
          </div>
        </div>
        <div class="row mb-3">
          <div class="col-6">
            <div class="card text-white bg-warning">
              <div class="card-body text-center py-2">
                <h6 class="card-title mb-0">{{ logStats?.total_size || '0 MB' }}</h6>
                <small class="card-text">{{ $t('logManagement.total_size') }}</small>
              </div>
            </div>
          </div>
          <div class="col-6">
            <div class="card text-white bg-success">
              <div class="card-body text-center py-2">
                <h6 class="card-title mb-0">{{ logStats?.archived_count || 0 }}</h6>
                <small class="card-text">{{ $t('logManagement.archived_count') }}</small>
              </div>
            </div>
          </div>
        </div>

        <!-- 管理操作（紧凑版） -->
        <div class="card mb-3">
          <div class="card-header py-2">
            <h6 class="card-title mb-0">{{ $t('logManagement.operations') }}</h6>
          </div>
          <div class="card-body py-2">
            <div class="row g-2">
              <div class="col-6">
                <button class="btn btn-primary btn-sm w-100 d-flex flex-column align-items-center py-2" @click="cleanupLogs" :disabled="isOperating">
                  <i class="fas fa-broom mb-1"></i>
                  <small>{{ $t('logManagement.cleanup_logs') }}</small>
                </button>
              </div>
              <div class="col-6">
                <button class="btn btn-info btn-sm w-100 d-flex flex-column align-items-center py-2" @click="archiveLogs" :disabled="isOperating">
                  <i class="fas fa-archive mb-1"></i>
                  <small>{{ $t('logManagement.archive_logs') }}</small>
                </button>
              </div>
              <div class="col-6">
                <button class="btn btn-warning btn-sm w-100 d-flex flex-column align-items-center py-2" @click="compressLogs" :disabled="isOperating">
                  <i class="fas fa-compress-alt mb-1"></i>
                  <small>{{ $t('logManagement.compress_logs') }}</small>
                </button>
              </div>
              <div class="col-6">
                <button class="btn btn-success btn-sm w-100 d-flex flex-column align-items-center py-2" @click="exportLogs" :disabled="isOperating">
                  <i class="fas fa-download mb-1"></i>
                  <small>{{ $t('logManagement.export_logs') }}</small>
                </button>
              </div>
            </div>

            <!-- 清理设置（紧凑版） -->
            <div class="mt-3 pt-2 border-top">
              <h6 class="mb-2 small">{{ $t('logManagement.cleanup_settings') }}</h6>
              <div class="row g-2">
                <div class="col-6">
                  <label class="form-label small mb-1">{{ $t('logManagement.retention_days') }}</label>
                  <input type="number" class="form-control form-control-sm" v-model="retentionDays" min="1" max="365">
                </div>
                <div class="col-6">
                  <label class="form-label small mb-1">{{ $t('logManagement.max_size_mb') }}</label>
                  <input type="number" class="form-control form-control-sm" v-model="maxSizeMB" min="1" max="1000">
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 日志文件列表（紧凑版） -->
        <div class="card">
          <div class="card-header py-2">
            <h6 class="card-title mb-0">{{ $t('logManagement.log_files') }}</h6>
          </div>
          <div class="card-body py-2">
            <div v-if="logFiles.length > 0">
              <div class="table-responsive">
                <table class="table table-sm table-hover mb-0" style="font-size: 0.75rem;">
                  <thead>
                    <tr>
                      <th class="small">{{ $t('logManagement.file_name') }}</th>
                      <th class="small">{{ $t('logManagement.file_size') }}</th>
                      <th class="small">{{ $t('logManagement.modified_time') }}</th>
                      <th class="small">{{ $t('logManagement.actions') }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="file in logFiles" :key="file.name">
                      <td class="small">
                        <i class="fas fa-file-alt text-info me-1"></i>
                        {{ file.name }}
                        <span v-if="file.is_current" class="badge bg-success badge-sm ms-1" style="font-size: 0.6rem;">
                          {{ $t('logManagement.current') }}
                        </span>
                      </td>
                      <td class="small">{{ file.size }}</td>
                      <td class="small">{{ formatDateTime(file.modified_time) }}</td>
                      <td>
                        <button class="btn btn-outline-info btn-sm me-1" 
                                @click="viewLogFile(file.name)"
                                :title="$t('logManagement.view_log')"
                                style="padding: 3px 8px; font-size: 0.8rem; min-width: 32px;">
                          <i class="fas fa-eye"></i>
                        </button>
                        <button v-if="!file.is_current" 
                                class="btn btn-outline-danger btn-sm" 
                                @click="deleteLogFile(file.name)"
                                :title="$t('logManagement.delete_log')"
                                style="padding: 3px 8px; font-size: 0.8rem; min-width: 32px;">
                          <i class="fas fa-trash"></i>
                        </button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            <div v-else class="text-center text-muted py-3">
              <i class="fas fa-file-alt fa-2x mb-2"></i>
              <p class="small">{{ $t('common.no_data') }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 导出成功Modal -->
    <div class="modal fade" id="exportSuccessModal" tabindex="-1" aria-labelledby="exportSuccessModalLabel" aria-hidden="true">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="exportSuccessModalLabel">
              <i class="fas fa-check-circle text-success me-2"></i>
              {{ $t('logManagement.export_success_title') }}
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <div class="alert alert-success">
              <i class="fas fa-file-export me-2"></i>
              {{ $t('logManagement.export_success_message') }}
            </div>
            <div class="mb-3">
              <strong>{{ $t('logManagement.file_path') }}:</strong>
              <div class="mt-1 p-2 bg-light rounded">
                <code class="text-break">{{ exportInfo.filePath }}</code>
              </div>
            </div>
            <div class="mb-3">
              <strong>{{ $t('logManagement.download_link') }}:</strong>
              <div class="mt-2">
                <a :href="exportInfo.downloadUrl" 
                   class="btn btn-primary btn-sm"
                   target="_blank"
                   download>
                  <i class="fas fa-download me-1"></i>
                  {{ $t('logManagement.click_to_download') }}
                </a>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
              {{ $t('logManagement.close') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 日志查看模态框 -->
    <div class="modal fade" id="logViewModal" tabindex="-1" ref="logViewModal">
      <div class="modal-dialog modal-xl">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              {{ $t('logManagement.view_log') }}: {{ currentLogFile }}
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body">
            <div class="log-content" v-if="logContent">
              <pre class="log-text">{{ cleanLogContent(logContent) }}</pre>
            </div>
            <div v-else class="text-center">
              <div class="spinner-border" role="status">
                <span class="visually-hidden">{{ $t('common.loading') }}</span>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
              {{ $t('common.close') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed, getCurrentInstance } from 'vue'
import { useI18n } from 'vue-i18n'
import { formatDateTime } from '@/utils/formatters'
import api from '@/services/api'
import logService from '@/services/api/logService'
import { Modal } from 'bootstrap'

export default {
  name: 'LogManagementView',
  setup() {
    const { t } = useI18n()
    const instance = getCurrentInstance()
    
    // 响应式数据
    const logStats = ref(null)
    const logFiles = ref([])
    const recentOperations = ref([])
    const isOperating = ref(false)
    const retentionDays = ref(30)
    const maxSizeMB = ref(100)
    const currentLogFile = ref('')
    const logContent = ref('')
    const logViewModal = ref(null)
    const searchKeyword = ref('')
    const selectedType = ref('')
    const selectedOperator = ref('')
    const selectedTimeRange = ref('')
    const availableOperators = ref([])
    const filteredOperations = ref([])
    
    // 导出相关信息
    const exportInfo = ref({
      filePath: '',
      downloadUrl: ''
    })

    // 操作日志查询相关数据
    const searchForm = ref({
      startDate: getDefaultStartDate(),
      endDate: getDefaultEndDate(),
      logType: 'all',
      operator: ''
    })
    const logs = ref([])
    const loading = ref(false)
    const error = ref(null)
    const total = ref(0)
    const currentPage = ref(1)
    const perPage = ref(15)

    // 计算总页数
    const totalPages = computed(() => {
      return Math.ceil(total.value / perPage.value)
    })

    // 获取默认日期
    function getDefaultStartDate() {
      const date = new Date()
      date.setDate(date.getDate() - 7) // 默认查询最近7天
      return date.toISOString().split('T')[0]
    }

    function getDefaultEndDate() {
      return new Date().toISOString().split('T')[0]
    }

    // 获取时间标识（刚刚、3分钟前等）
    const getTimeAgo = (dateStr) => {
      const now = new Date()
      const time = new Date(dateStr)
      const diff = now - time
      const seconds = Math.floor(diff / 1000)
      const minutes = Math.floor(seconds / 60)
      const hours = Math.floor(minutes / 60)
      const days = Math.floor(hours / 24)
      
      if (seconds < 60) {
        return t('common.just_now')
      } else if (minutes < 60) {
        return t('common.minutes_ago', { minutes })
      } else if (hours < 24) {
        return t('common.hours_ago', { hours })
      } else {
        return t('common.days_ago', { days })
      }
    }

    // 操作日志查询功能
    const loadLogs = async () => {
      loading.value = true
      error.value = null
      
      try {
        const params = {
          page: currentPage.value,
          per_page: perPage.value,
          start_date: searchForm.value.startDate,
          end_date: searchForm.value.endDate
        }
        
        if (searchForm.value.logType && searchForm.value.logType !== 'all') {
          params.log_type = searchForm.value.logType
        }
        
        if (searchForm.value.operator) {
          params.operator_name = searchForm.value.operator
        }
        
        const response = await api.get('system/logs', { params })
        
        if (response.data.success) {
          logs.value = response.data.logs
          total.value = response.data.total
        } else {
          error.value = response.data.message || t('logs.get_logs_failed')
        }
      } catch (err) {
        console.error(t('logs.get_logs_failed'), err)
        error.value = err.response?.data?.message || t('logs.get_logs_failed')
      } finally {
        loading.value = false
      }
    }

    const handleSearch = async () => {
      currentPage.value = 1 // 重置到第一页
      await loadLogs()
    }

    const previousPage = async () => {
      if (currentPage.value > 1) {
        currentPage.value--
        await loadLogs()
      }
    }

    const nextPage = async () => {
      if (currentPage.value < totalPages.value) {
        currentPage.value++
        await loadLogs()
      }
    }

    const goToPage = async (page) => {
      if (page >= 1 && page <= totalPages.value) {
        currentPage.value = page
        await loadLogs()
      }
    }

    const getLogTypeText = (type) => {
      const typeMap = {
        'system': t('logs.log_types.system'),
        'login': t('logs.log_types.login'),
        'exchange': t('logs.log_types.exchange'),
        'rate': t('logs.log_types.rate'),
        'balance': t('logs.log_types.balance'),
        'end_of_day': t('logs.log_types.end_of_day'),
        'branch_management': t('logs.log_types.branch_management'),
        'system_manage': t('logs.log_types.system_manage')
      }
      return typeMap[type] || type
    }

    const getLogTypeBadgeClass = (type) => {
      const classMap = {
        'system': 'bg-primary',
        'login': 'bg-info',
        'exchange': 'bg-success',
        'rate': 'bg-warning',
        'balance': 'bg-primary',
        'end_of_day': 'bg-danger',
        'branch_management': 'bg-secondary',
        'system_manage': 'bg-dark'
      }
      return classMap[type] || 'bg-secondary'
    }

    // 系统日志管理功能
    const fetchLogStats = async () => {
      try {
        const response = await logService.getLogStats()
        logStats.value = response.data.data.stats
      } catch (err) {
        console.error(t('logs.load_stats_failed'), err)
      }
    }

    const fetchLogFiles = async () => {
      try {
        const response = await logService.getLogFiles()
        logFiles.value = response.data.data
      } catch (err) {
        console.error(t('logs.load_files_failed'), err)
      }
    }

    const fetchRecentOperations = async () => {
      try {
        const response = await logService.getRecentOperations()
        recentOperations.value = response.data.data
        filteredOperations.value = response.data.data
        const operators = [...new Set(response.data.data.map(op => op.operator_name))]
        availableOperators.value = operators
      } catch (err) {
        console.error(t('logs.load_operations_failed'), err)
      }
    }

    const cleanupLogs = async () => {
      if (confirm(t('logManagement.confirm_cleanup'))) {
        isOperating.value = true
        try {
          await logService.cleanupLogs(retentionDays.value, maxSizeMB.value)
          instance.proxy.$toast.success(t('logManagement.cleanup_success'))
          await Promise.all([fetchLogStats(), fetchLogFiles()])
        } catch (err) {
          instance.proxy.$toast.error(t('logManagement.cleanup_failed'))
        } finally {
          isOperating.value = false
        }
      }
    }

    const archiveLogs = async () => {
      isOperating.value = true
              try {
          await logService.archiveLogs()
          if (instance?.proxy?.$toast) {
            instance.proxy.$toast.success(t('logManagement.archive_success'))
          } else {
            alert(t('logManagement.archive_success'))
          }
          await Promise.all([fetchLogStats(), fetchLogFiles()])
        } catch (err) {
          if (instance?.proxy?.$toast) {
            instance.proxy.$toast.error(t('logManagement.archive_failed'))
          } else {
            alert(t('logManagement.archive_failed'))
          }
        } finally {
        isOperating.value = false
      }
    }

    const compressLogs = async () => {
      isOperating.value = true
      try {
        await logService.compressLogs()
        if (instance?.proxy?.$toast) {
          instance.proxy.$toast.success(t('logManagement.compress_success'))
        } else {
          alert(t('logManagement.compress_success'))
        }
        await Promise.all([fetchLogStats(), fetchLogFiles()])
      } catch (err) {
        if (instance?.proxy?.$toast) {
          instance.proxy.$toast.error(t('logManagement.compress_failed'))
        } else {
          alert(t('logManagement.compress_failed'))
        }
      } finally {
        isOperating.value = false
      }
    }

    const exportLogs = async () => {
      isOperating.value = true
      try {
        const response = await logService.exportLogFiles()
        
        if (response.data.success) {
          // 设置导出信息
          exportInfo.value = {
            filePath: response.data.file_path,
            downloadUrl: `${window.location.origin.replace(':8080', ':5001')}${response.data.download_url}`
          }
          
          // 显示导出成功Modal
          const modal = new Modal(document.getElementById('exportSuccessModal'))
          modal.show()
        } else {
          instance.proxy.$toast.error(response.data.message || t('logManagement.export_failed'))
        }
      } catch (err) {
        console.error('导出失败:', err)
        instance.proxy.$toast.error(t('logManagement.export_failed'))
      } finally {
        isOperating.value = false
      }
    }

    const viewLogFile = async (filename) => {
      try {
        currentLogFile.value = filename
        logContent.value = ''
        
        const modal = new Modal(logViewModal.value)
        modal.show()
        
        const response = await logService.getLogContent(filename)
        logContent.value = response.data.data
      } catch (err) {
        instance.proxy.$toast.error(t('logManagement.view_log_failed'))
      }
    }

    const deleteLogFile = async (filename) => {
      if (confirm(t('logManagement.confirm_delete_file', { filename }))) {
        try {
          await logService.deleteLogFile(filename)
          instance.proxy.$toast.success(t('logManagement.delete_file_success'))
          await fetchLogFiles()
        } catch (err) {
          instance.proxy.$toast.error(t('logManagement.delete_file_failed'))
        }
      }
    }

    // 清理日志内容，移除图标字符
    const cleanLogContent = (content) => {
      if (!content) return ''
      
      // 移除常见的图标字符和Unicode图标
      return content
        .replace(/[\u{1F300}-\u{1F9FF}]/gu, '') // 移除表情符号
        .replace(/[\u{2600}-\u{26FF}]/gu, '') // 移除杂项符号
        .replace(/[\u{2700}-\u{27BF}]/gu, '') // 移除装饰符号
        .replace(/[\u{1F000}-\u{1F02F}]/gu, '') // 移除麻将牌
        .replace(/[\u{1F0A0}-\u{1F0FF}]/gu, '') // 移除扑克牌
        .replace(/[\u{1F100}-\u{1F64F}]/gu, '') // 移除交通和地图符号
        .replace(/[\u{1F680}-\u{1F6FF}]/gu, '') // 移除交通和地图符号
        .replace(/[\u{1F1E0}-\u{1F1FF}]/gu, '') // 移除区域指示符
        .replace(/[\u{1F200}-\u{1F2FF}]/gu, '') // 移除封闭字母数字补充
        .replace(/[\u{1F300}-\u{1F5FF}]/gu, '') // 移除杂项符号和象形文字
        .replace(/[\u{1F600}-\u{1F64F}]/gu, '') // 移除表情符号
        .replace(/[\u{1F650}-\u{1F67F}]/gu, '') // 移除装饰符号
        .replace(/[\u{1F680}-\u{1F6FF}]/gu, '') // 移除交通和地图符号
        .replace(/[\u{1F700}-\u{1F77F}]/gu, '') // 移除炼金术符号
        .replace(/[\u{1F780}-\u{1F7FF}]/gu, '') // 移除几何图形
        .replace(/[\u{1F800}-\u{1F8FF}]/gu, '') // 移除补充箭头
        .replace(/[\u{1F900}-\u{1F9FF}]/gu, '') // 移除补充符号和象形文字
        .replace(/[\u{1FA00}-\u{1FA6F}]/gu, '') // 移除象棋符号
        .replace(/[\u{1FA70}-\u{1FAFF}]/gu, '') // 移除符号和象形文字扩展
        .replace(/[\u{1FB00}-\u{1FBFF}]/gu, '') // 移除传统符号
        .trim()
    }

    // 初始化
    onMounted(async () => {
      // 检查权限
      const userPermissions = JSON.parse(localStorage.getItem('userPermissions') || '[]')
      if (!userPermissions.includes('end_of_day') && !userPermissions.includes('system_manage')) {
        error.value = t('logs.no_permission')
        return
      }
      
      // 加载数据
      await Promise.all([
        loadLogs(),
        fetchLogStats(),
        fetchLogFiles(),
        fetchRecentOperations()
      ])
    })

    return {
      // 操作日志查询
      searchForm,
      logs,
      loading,
      error,
      total,
      currentPage,
      perPage,
      handleSearch,
      previousPage,
      nextPage,
      getLogTypeText,
      getLogTypeBadgeClass,
      getTimeAgo,
      
      // 系统日志管理
      logStats,
      logFiles,
      recentOperations,
      isOperating,
      retentionDays,
      maxSizeMB,
      currentLogFile,
      logContent,
      logViewModal,
      searchKeyword,
      selectedType,
      selectedOperator,
      selectedTimeRange,
      availableOperators,
      filteredOperations,
      cleanupLogs,
      archiveLogs,
      compressLogs,
      exportLogs,
      viewLogFile,
      deleteLogFile,
      cleanLogContent,
      
      // 工具函数
      formatDateTime,
      totalPages,
      goToPage,
      
      // 导出相关
      exportInfo
    }
  }
}
</script>

<style scoped>
.log-management {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h1 {
  margin-bottom: 10px;
}

.subtitle {
  color: #6c757d;
  margin-bottom: 0;
}

.operation-item:hover {
  background-color: #f8f9fa;
}

.hover-bg:hover {
  background-color: #f8f9fa;
}

.badge {
  font-size: 0.75rem;
}

.log-content {
  max-height: 500px;
  overflow-y: auto;
}

.log-text {
  background-color: #f8f9fa;
  padding: 15px;
  border-radius: 4px;
  font-size: 0.85rem;
  line-height: 1.4;
}

.btn:disabled {
  opacity: 0.6;
}

.table th {
  white-space: nowrap;
}

.time-badge {
  background-color: #d4edda !important;
  color: #155724 !important;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 0.75rem;
}
</style>
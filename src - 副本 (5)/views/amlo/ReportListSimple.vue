<template>
  <div class="container-fluid py-4">
    <div class="row">
      <div class="col-12">
        <div class="d-flex justify-content-between align-items-center flex-wrap gap-3 mb-4">
          <div class="d-flex align-items-center gap-3">
            <h2 class="page-title-bold mb-0 d-flex align-items-center gap-2">
              <font-awesome-icon :icon="['fas', 'file-alt']" />
              {{ t('amlo.report.title') }}
            </h2>
            <span class="amlo-tag badge rounded-pill d-inline-flex align-items-center gap-2">
              <font-awesome-icon :icon="['fas', 'bookmark']" />
              <span>{{ t('amlo.report.management') }}</span>
            </span>
          </div>
          <button
            type="button"
            class="btn btn-outline-primary"
            @click="loadReports"
            :disabled="loading"
          >
            <font-awesome-icon :icon="['fas', 'rotate-right']" :spin="loading" class="me-2" />
            {{ t('amlo.report.refresh') }}
          </button>
        </div>

        <div class="card mb-4 filter-card">
          <div class="card-header">
            <h5 class="mb-0 d-flex align-items-center">
              <font-awesome-icon :icon="['fas', 'filter']" class="me-2" />
              {{ t('amlo.report.filtersTitle') }}
            </h5>
          </div>
          <div class="card-body">
            <!-- 筛选器 -->
            <div class="row g-3">
              <div class="col-sm-6 col-lg-2">
                <label class="form-label">{{ t('amlo.report.year') }}</label>
                <select class="form-select" v-model="filter.year" @change="onYearChange">
                  <option value="">{{ t('amlo.report.selectYear') }}</option>
                  <option v-for="year in availableYears" :key="year" :value="year">
                    {{ year }}
                  </option>
                </select>
              </div>
              <div class="col-sm-6 col-lg-2">
                <label class="form-label">{{ t('amlo.report.month') }}</label>
                <select class="form-select" v-model="filter.month" :disabled="!filter.year">
                  <option value="">{{ t('amlo.report.selectMonth') }}</option>
                  <option v-for="month in availableMonths" :key="month" :value="month">
                    {{ month }}
                  </option>
                </select>
              </div>
              <div class="col-sm-6 col-lg-2">
                <label class="form-label">{{ t('amlo.report.reportType') }}</label>
                <select class="form-select" v-model="filter.report_type">
                  <option value="">{{ t('amlo.report.allTypes') }}</option>
                  <option value="AMLO-1-01">AMLO-1-01</option>
                  <option value="AMLO-1-02">AMLO-1-02</option>
                  <option value="AMLO-1-03">AMLO-1-03</option>
                </select>
              </div>
              <div class="col-sm-6 col-lg-3">
                <label class="form-label">{{ t('amlo.report.customerId') }}</label>
                <input
                  type="text"
                  class="form-control"
                  v-model="filter.customer_id"
                  :placeholder="t('amlo.report.customerIdPlaceholder')"
                />
              </div>
              <div class="col-sm-6 col-lg-2">
                <label class="form-label">&nbsp;</label>
                <button class="btn btn-primary w-100 d-block" @click="loadReports">
                  <font-awesome-icon :icon="['fas', 'search']" class="me-1" />
                  {{ t('amlo.report.search') }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- 报告列表 -->
        <div class="card">
          <div class="card-body">
            <div class="table-responsive">
              <table class="table table-hover">
                <thead class="table-light">
                  <tr>
                    <th>{{ t('amlo.report.reportId') }}</th>
                    <th>{{ t('amlo.report.reportNo') }}</th>
                    <th>{{ t('amlo.report.type') }}</th>
                    <th>{{ t('amlo.report.customer') }}</th>
                    <th>{{ t('amlo.report.reporter') }}</th>
                    <th>{{ t('amlo.report.direction') }}</th>
                    <th class="text-end">{{ t('amlo.report.amount') }}</th>
                    <th>{{ t('amlo.report.status') }}</th>
                    <th>{{ t('amlo.report.createdAt') }}</th>
                    <th class="text-center">{{ t('amlo.report.actions') }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="loading">
                    <td colspan="10" class="text-center py-5">
                      <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">{{ t('common.loading') }}</span>
                      </div>
                    </td>
                  </tr>
                  <tr v-else-if="reports.length === 0">
                    <td colspan="10" class="text-center text-muted py-5">
                      {{ t('amlo.report.noData') }}
                    </td>
                  </tr>
                  <tr v-else v-for="report in reports" :key="report.id">
                    <td>{{ report.id }}</td>
                    <td>
                      <span class="text-monospace">{{ report.report_no || report.id }}</span>
                    </td>
                    <td>
                      <span class="badge" :class="report.is_reported ? 'bg-success' : 'bg-primary'">
                        {{ report.report_type }}
                      </span>
                    </td>
                    <td>{{ report.customer_name }}</td>
                    <td>{{ report.created_by || '-' }}</td>
                    <td>{{ formatDirection(report.direction) }}</td>
                    <td class="text-end">{{ formatAmount(report.amount) }} THB</td>
                    <td>
                      <span
                        class="badge"
                        :class="{
                          'bg-warning': !report.is_reported,
                          'bg-success': report.is_reported
                        }"
                      >
                        <font-awesome-icon :icon="['fas', report.is_reported ? 'check-circle' : 'clock']" class="me-1" />
                        {{ report.is_reported ? t('amlo.report.reported') : t('amlo.report.pending') }}
                      </span>
                    </td>
                    <td>{{ formatDateTime(report.created_at) }}</td>
                    <td class="text-center">
                      <div class="btn-group" role="group">
                        <button
                          class="btn btn-outline-info btn-sm"
                          @click="viewPDF(report)"
                          :title="t('amlo.report.viewPDF')"
                        >
                          <font-awesome-icon :icon="['fas', 'eye']" class="fa-lg" />
                        </button>
                        <button
                          class="btn btn-outline-primary btn-sm"
                          @click="downloadPDF(report)"
                          :title="t('amlo.report.downloadPDF')"
                          :disabled="downloading"
                        >
                          <font-awesome-icon :icon="['fas', 'download']" class="fa-lg" />
                        </button>
                        <button
                          v-if="!report.is_reported"
                          class="btn btn-outline-success btn-sm"
                          @click="markSingleReported(report)"
                          :title="t('amlo.report.markReported')"
                          :disabled="submittingReportId === report.id"
                        >
                          <font-awesome-icon
                            :icon="['fas', submittingReportId === report.id ? 'spinner' : 'flag']"
                            class="fa-lg"
                            :spin="submittingReportId === report.id"
                          />
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import api from '@/services/api'
import { useOpenOnDisplay } from '@/utils/useOpenOnDisplay'

export default {
  name: 'ReportListSimple',
  setup() {
    const { t } = useI18n()
    const { openOnDisplay } = useOpenOnDisplay()

    const loading = ref(false)
    const downloading = ref(false)
    const submittingReportId = ref(null)
    const reports = ref([])
    const pagination = ref({
      total: 0,
      page: 1,
      page_size: 20,
      total_pages: 1
    })
    const hasSelected = computed(() => reports.value.some(r => r.selected))
    const filter = ref({
      year: '',
      month: '',
      report_type: '',
      customer_id: ''
    })

    // 年份和月份选项
    const availableYears = computed(() => {
      const currentYear = new Date().getFullYear()
      const years = []
      // 提供最近5年的选项
      for (let i = 0; i < 5; i++) {
        years.push(currentYear - i)
      }
      return years
    })

    const availableMonths = computed(() => {
      return [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    })

    // 年份变化时重置月份
    const onYearChange = () => {
      filter.value.month = ''
    }

    const loadReports = async () => {
      loading.value = true
      try {
        const params = { ...filter.value }

        // 如果选择了年月，构建start_date和end_date
        if (filter.value.year && filter.value.month) {
          const year = parseInt(filter.value.year)
          const month = parseInt(filter.value.month)
          const startDate = new Date(year, month - 1, 1)
          const endDate = new Date(year, month, 0, 23, 59, 59)

          params.start_date = startDate.toISOString().split('T')[0]
          params.end_date = endDate.toISOString().split('T')[0]
        } else if (filter.value.year && !filter.value.month) {
          // 只选择了年份，查询整年
          const year = parseInt(filter.value.year)
          params.start_date = `${year}-01-01`
          params.end_date = `${year}-12-31`
        }

        // 移除year和month字段（后端不需要）
        delete params.year
        delete params.month

        const response = await api.get('/amlo/reports', { params })
        
        if (response.data?.success) {
          const payload = response.data.data
          const items = Array.isArray(payload) ? payload : payload?.items || []
          
          reports.value = items.map(item => ({
            ...item,
            selected: false
          }))

          if (payload && !Array.isArray(payload)) {
            const total = payload.total ?? items.length
            const pageSize = payload.page_size ?? (items.length || 20)
            const totalPages = payload.total_pages ?? Math.max(1, Math.ceil(total / (pageSize || 1)))

            pagination.value = {
              total,
              page: payload.page ?? 1,
              page_size: pageSize,
              total_pages: totalPages
            }
          } else {
            pagination.value = {
              total: items.length,
              page: 1,
              page_size: items.length || 20,
              total_pages: 1
            }
          }
        } else {
          reports.value = []
        }
      } catch (error) {
        console.error('加载报告列表失败:', error)
        reports.value = []
      } finally {
        loading.value = false
      }
    }

    const viewPDF = async (report) => {
      try {
        console.log('[ReportList] Opening PDF viewer for report:', report)

        // 构建PDF查看器URL
        const baseUrl = window.location.origin
        const pdfViewerPath = '/amlo/pdf-viewer'
        const params = new URLSearchParams({
          id: report.reservation_id,  // 使用reservation_id
          title: `${report.report_type} - ${report.report_no || report.id}`,
          reportType: report.report_type,
          readonly: 'true'  // 报告管理页面查看时为只读模式
        })
        const url = `${baseUrl}${pdfViewerPath}?${params.toString()}`

        console.log('[ReportList] PDF Viewer URL:', url)

        // 使用useOpenOnDisplay在扩展显示器上打开PDF
        const pdfWindow = await openOnDisplay({
          url: url,
          target: 'AMLOPDFViewer',
          preferNonPrimary: true,         // 优先扩展显示器
          includeTaskbarArea: false,      // 避开任务栏
          fallbackGuess: 'right',         // 兜底猜测
          features: 'noopener=no'
        })

        if (!pdfWindow) {
          alert(t('amlo.reservation.popupBlocked') || '弹出窗口被阻止，请允许弹出窗口后重试')
          console.error('[ReportList] PDF窗口打开失败 - 弹窗被阻止')
        } else {
          console.log('[ReportList] ✅ PDF查看器窗口已在扩展显示器上打开')
        }
      } catch (error) {
        console.error('[ReportList] 查看PDF失败:', error)
        alert('查看失败: ' + error.message)
      }
    }

    const downloadPDF = async (report) => {
      if (downloading.value) return

      downloading.value = true
      try {
        console.log('[ReportList] Downloading PDF for report:', report)

        // 使用reservation_id通过后端API获取PDF
        const reservationId = report.reservation_id
        if (!reservationId) {
          alert('无法下载：缺少预约ID')
          return
        }

        // 构造文件名
        const reportType = report.report_type
        const reportNo = (report.report_no || report.id).toString().replace(/\//g, '-')
        const filename = `${reportType}_${reportNo}.pdf`

        console.log('[ReportList] Fetching PDF from backend:', reservationId)

        // 通过后端API获取PDF（使用blob响应类型）
        const response = await api.get(
          `/amlo/reservations/${reservationId}/generate-pdf`,
          { responseType: 'blob' }
        )

        console.log('[ReportList] PDF response received, size:', response.data.size)

        // 创建Blob URL
        const blob = new Blob([response.data], { type: 'application/pdf' })
        const url = window.URL.createObjectURL(blob)

        // 创建临时下载链接
        const link = document.createElement('a')
        link.href = url
        link.download = filename
        document.body.appendChild(link)
        link.click()

        // 清理
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)

        console.log('[ReportList] ✅ PDF downloaded successfully:', filename)
      } catch (error) {
        console.error('[ReportList] 下载PDF失败:', error)
        alert('下载失败: ' + (error.response?.data?.message || error.message))
      } finally {
        downloading.value = false
      }
    }

    const formatAmount = (amount) => {
      if (!amount) return '0.00'
      return parseFloat(amount).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      })
    }

    const formatDateTime = (dt) => {
      if (!dt) return '-'
      return new Date(dt).toLocaleString('zh-CN')
    }

    // 格式化交易方向
    const formatDirection = (direction) => {
      if (!direction) return '-'
      const directionMap = {
        'buy': t('amlo.report.buyForeign'),
        'sell': t('amlo.report.sellForeign'),
        'dual_direction': t('amlo.report.dualDirection'),
        'buy_foreign': t('amlo.report.buyForeign'),
        'sell_foreign': t('amlo.report.sellForeign')
      }
      return directionMap[direction] || direction
    }

    // 获取报告行的CSS类（空函数，避免缓存错误）
    const getReportRowClass = () => {
      return ''
    }

    // 标记单个报告为已上报
    const markSingleReported = async (report) => {
      if (submittingReportId.value) return

      if (!confirm(t('amlo.report.confirmMarkReported'))) {
        return
      }

      submittingReportId.value = report.id

      try {
        const response = await api.post('/amlo/reports/mark-reported', {
          ids: [report.id]
        })

        if (response.data.success) {
          console.log('[ReportList] ✅ 报告已标记为已上报')
          loadReports()  // 重新加载数据
        }
      } catch (error) {
        console.error('[ReportList] 标记失败:', error)
        alert(t('amlo.report.markFailed') + ': ' + (error.response?.data?.message || error.message))
      } finally {
        submittingReportId.value = null
      }
    }

    // 批量标记为已上报（保留旧功能，以防需要）
    const markReported = async () => {
      const selectedIds = reports.value
        .filter(r => r.selected)
        .map(r => r.id)

      if (selectedIds.length === 0) {
        alert(t('amlo.report.pleaseSelect'))
        return
      }

      if (!confirm(t('amlo.report.confirmMarkReportedBatch', { count: selectedIds.length }))) {
        return
      }

      try {
        const response = await api.post('/amlo/reports/mark-reported', {
          ids: selectedIds
        })

        if (response.data.success) {
          alert(t('amlo.report.markSuccess', { count: response.data.updated_count }))
          loadReports()  // 重新加载数据
        }
      } catch (error) {
        console.error('[ReportList] 标记失败:', error)
        alert(t('amlo.report.markFailed') + ': ' + (error.response?.data?.message || error.message))
      }
    }

    onMounted(() => {
      loadReports()
    })

    return {
      t,
      loading,
      downloading,
      submittingReportId,
      reports,
      pagination,
      hasSelected,
      filter,
      availableYears,
      availableMonths,
      onYearChange,
      currentReservation: ref(null),
      detailModalRef: ref(null),
      loadReports,
      viewPDF,
      downloadPDF,
      markSingleReported,
      markReported,
      formatAmount,
      formatDateTime,
      formatDirection,
      getReportRowClass
    }
  }
}
</script>


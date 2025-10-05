<template>
  <div class="report-list-view">
    <a-card>
      <template #title>
        <span>{{ $t('amlo.report.title') }}</span>
      </template>

      <template #extra>
        <a-space>
          <a-button
            v-if="selectedReportIds.length > 0"
            type="primary"
            @click="handleBatchReport"
          >
            {{ $t('amlo.report.batchReport') }} ({{ selectedReportIds.length }})
          </a-button>
          <a-button
            v-if="selectedReportIds.length > 0"
            @click="handleBatchDownloadPDF"
          >
            {{ $t('amlo.report.batchDownloadPDF') }} ({{ selectedReportIds.length }})
          </a-button>
        </a-space>
      </template>

      <!-- 筛选器 -->
      <ReportFilter
        @filter="handleFilter"
        @reset="handleResetFilter"
      />

      <!-- 报告表格 -->
      <ReportTable
        :loading="loading"
        :reports="reports"
        :total="total"
        :current-page="currentPage"
        :page-size="pageSize"
        :selected-ids="selectedReportIds"
        @page-change="handlePageChange"
        @selection-change="handleSelectionChange"
        @download-pdf="handleDownloadPDF"
      />
    </a-card>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { useAMLOStore } from '@/stores/amlo'
import ReportFilter from './components/ReportFilter.vue'
import ReportTable from './components/ReportTable.vue'

export default {
  name: 'ReportListView',
  components: {
    ReportFilter,
    ReportTable
  },
  setup() {
    const { t } = useI18n()
    const amloStore = useAMLOStore()

    // 状态
    const loading = ref(false)
    const reports = ref([])
    const total = ref(0)
    const currentPage = ref(1)
    const pageSize = ref(20)
    const filterParams = ref({})
    const selectedReportIds = ref([])

    // 加载报告列表
    const loadReports = async () => {
      loading.value = true
      try {
        const response = await amloStore.fetchReports({
          ...filterParams.value,
          page: currentPage.value,
          page_size: pageSize.value
        })

        if (response.success) {
          reports.value = response.data.items
          total.value = response.data.total
        } else {
          message.error(response.message)
        }
      } catch (error) {
        console.error('加载报告列表失败:', error)
        message.error(t('amlo.report.loadFailed'))
      } finally {
        loading.value = false
      }
    }

    // 筛选
    const handleFilter = (params) => {
      filterParams.value = params
      currentPage.value = 1
      loadReports()
    }

    // 重置筛选
    const handleResetFilter = () => {
      filterParams.value = {}
      currentPage.value = 1
      loadReports()
    }

    // 分页变化
    const handlePageChange = (page, size) => {
      currentPage.value = page
      pageSize.value = size
      loadReports()
    }

    // 选择变化
    const handleSelectionChange = (selectedIds) => {
      selectedReportIds.value = selectedIds
    }

    // 下载单个PDF
    const handleDownloadPDF = async (reportId) => {
      try {
        await amloStore.generatePDF(reportId)
        message.success(t('amlo.report.downloadSuccess'))
      } catch (error) {
        console.error('下载PDF失败:', error)
        message.error(t('amlo.report.downloadFailed'))
      }
    }

    // 批量下载PDF
    const handleBatchDownloadPDF = async () => {
      if (selectedReportIds.value.length === 0) {
        message.warning(t('common.pleaseSelect'))
        return
      }

      try {
        await amloStore.batchGeneratePDF(selectedReportIds.value)
        message.success(t('amlo.report.batchDownloadSuccess'))
      } catch (error) {
        console.error('批量下载PDF失败:', error)
        message.error(t('amlo.report.batchDownloadFailed'))
      }
    }

    // 批量上报
    const handleBatchReport = async () => {
      if (selectedReportIds.value.length === 0) {
        message.warning(t('common.pleaseSelect'))
        return
      }

      try {
        const response = await amloStore.batchReportSubmit(selectedReportIds.value)
        if (response.success) {
          message.success(t('amlo.report.batchReportSuccess'))
          selectedReportIds.value = []
          loadReports()
        } else {
          message.error(response.message)
        }
      } catch (error) {
        console.error('批量上报失败:', error)
        message.error(t('amlo.report.batchReportFailed'))
      }
    }

    // 组件挂载
    onMounted(() => {
      loadReports()
    })

    return {
      loading,
      reports,
      total,
      currentPage,
      pageSize,
      selectedReportIds,
      handleFilter,
      handleResetFilter,
      handlePageChange,
      handleSelectionChange,
      handleDownloadPDF,
      handleBatchDownloadPDF,
      handleBatchReport
    }
  }
}
</script>

<style scoped>
.report-list-view {
  padding: 24px;
}
</style>

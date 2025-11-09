<template>
  <div class="report-table">
    <a-table
      :columns="columns"
      :data-source="reports"
      :loading="loading"
      :pagination="paginationConfig"
      :row-selection="rowSelection"
      row-key="report_id"
      @change="handleTableChange"
    >
      <!-- 报告类型列 -->
      <template #reportType="{ text }">
        <a-tag color="blue">{{ text }}</a-tag>
      </template>

      <!-- 上报状态列 -->
      <template #isReported="{ text }">
        <a-tag :color="text ? 'green' : 'orange'">
          {{ text ? $t('amlo.report.reported') : $t('amlo.report.notReported') }}
        </a-tag>
      </template>

      <!-- 操作列 -->
      <template #action="{ record }">
        <a-space>
          <a-button
            type="link"
            size="small"
            @click="handleDownloadPDF(record.report_id)"
          >
            {{ $t('amlo.report.downloadPDF') }}
          </a-button>
        </a-space>
      </template>
    </a-table>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

export default {
  name: 'ReportTable',
  props: {
    loading: {
      type: Boolean,
      default: false
    },
    reports: {
      type: Array,
      default: () => []
    },
    total: {
      type: Number,
      default: 0
    },
    currentPage: {
      type: Number,
      default: 1
    },
    pageSize: {
      type: Number,
      default: 20
    },
    selectedIds: {
      type: Array,
      default: () => []
    }
  },
  emits: ['page-change', 'selection-change', 'download-pdf'],
  setup(props, { emit }) {
    const { t } = useI18n()

    const columns = [
      {
        title: t('amlo.report.id'),
        dataIndex: 'report_id',
        key: 'report_id',
        width: 100
      },
      {
        title: t('amlo.report.reportNumber'),
        dataIndex: 'report_number',
        key: 'report_number',
        width: 150
      },
      {
        title: t('amlo.report.reportType'),
        dataIndex: 'report_type',
        key: 'report_type',
        slots: { customRender: 'reportType' },
        width: 120
      },
      {
        title: t('amlo.report.reportDate'),
        dataIndex: 'report_date',
        key: 'report_date',
        width: 120
      },
      {
        title: t('amlo.report.isReported'),
        dataIndex: 'is_reported',
        key: 'is_reported',
        slots: { customRender: 'isReported' },
        width: 100
      },
      {
        title: t('amlo.report.reportedAt'),
        dataIndex: 'reported_at',
        key: 'reported_at',
        width: 150
      },
      {
        title: t('common.action'),
        key: 'action',
        slots: { customRender: 'action' },
        width: 150,
        fixed: 'right'
      }
    ]

    const paginationConfig = computed(() => ({
      total: props.total,
      current: props.currentPage,
      pageSize: props.pageSize,
      showSizeChanger: true,
      showQuickJumper: true,
      showTotal: (total) => t('common.totalItems', { total })
    }))

    const rowSelection = computed(() => ({
      selectedRowKeys: props.selectedIds,
      onChange: (selectedRowKeys) => {
        emit('selection-change', selectedRowKeys)
      },
      getCheckboxProps: (record) => ({
        disabled: record.is_reported
      })
    }))

    const handleTableChange = (pagination) => {
      emit('page-change', pagination.current, pagination.pageSize)
    }

    const handleDownloadPDF = (reportId) => {
      emit('download-pdf', reportId)
    }

    return {
      columns,
      paginationConfig,
      rowSelection,
      handleTableChange,
      handleDownloadPDF
    }
  }
}
</script>

<style scoped>
.report-table {
  margin-top: 16px;
}
</style>

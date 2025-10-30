<template>
  <div class="reservation-list">
    <a-table
      :columns="columns"
      :data-source="reservations"
      :loading="loading"
      :pagination="paginationConfig"
      row-key="id"
      @change="handleTableChange"
    >
      <!-- 状态列 -->
      <template #status="{ text }">
        <a-tag :color="getStatusColor(text)">
          {{ getStatusText(text) }}
        </a-tag>
      </template>

      <!-- 报告类型列 -->
      <template #reportType="{ text }">
        <a-tag color="blue">{{ text }}</a-tag>
      </template>

      <!-- 交易方向列 -->
      <template #direction="{ text }">
        <a-tag :color="text === 'buy' ? 'green' : 'orange'">
          {{ getDirectionText(text) }}
        </a-tag>
      </template>

      <!-- 操作列 -->
      <template #action="{ record }">
        <a-space>
          <a-button type="link" size="small" @click="handleViewDetail(record)">
            {{ $t('common.view') }}
          </a-button>

          <a-button
            v-if="record.status === 'pending' && hasAuditPermission"
            type="link"
            size="small"
            @click="handleAudit(record)"
          >
            {{ $t('amlo.reservation.audit') }}
          </a-button>

          <a-popconfirm
            v-if="record.status === 'approved' && hasAuditPermission"
            :title="$t('amlo.reservation.reverseAuditConfirm')"
            @confirm="handleReverseAudit(record)"
          >
            <a-button type="link" size="small" danger>
              {{ $t('amlo.reservation.reverseAudit') }}
            </a-button>
          </a-popconfirm>

          <!-- PDF下载按钮 - 任何状态都显示，便于调试 -->
          <a-button
            type="link"
            size="small"
            @click="handleDownloadPdf(record)"
            :loading="downloadingPdf[record.id]"
          >
            <DownloadOutlined /> {{ $t('common.downloadPdf') }}
          </a-button>
        </a-space>
      </template>
    </a-table>
  </div>
</template>

<script>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { DownloadOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/stores/auth'

export default {
  name: 'ReservationList',
  components: {
    DownloadOutlined
  },
  props: {
    loading: {
      type: Boolean,
      default: false
    },
    reservations: {
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
    }
  },
  emits: ['page-change', 'view-detail', 'audit', 'reverse-audit'],
  setup(props, { emit }) {
    const { t } = useI18n()
    const authStore = useAuthStore()
    const downloadingPdf = ref({})

    // TODO: 从权限系统获取
    const hasAuditPermission = computed(() => true)

    // 🔧 将columns改为computed，确保i18n更新后列标题也会更新
    const columns = computed(() => [
      {
        title: t('amlo.reservation.id'),
        dataIndex: 'id',
        key: 'id',
        width: 100
      },
      {
        title: t('amlo.reservation.reportType'),
        dataIndex: 'report_type',
        key: 'report_type',
        slots: { customRender: 'reportType' },
        width: 120
      },
      {
        title: t('amlo.reservation.direction'),
        dataIndex: 'direction',
        key: 'direction',
        slots: { customRender: 'direction' },
        width: 130
      },
      {
        title: t('amlo.reservation.customerName'),
        dataIndex: 'customer_name',
        key: 'customer_name',
        width: 150
      },
      {
        title: t('amlo.reservation.createdAt'),
        dataIndex: 'created_at',
        key: 'created_at',
        width: 150
      },
      {
        title: t('amlo.reservation.status'),
        dataIndex: 'status',
        key: 'status',
        slots: { customRender: 'status' },
        width: 100
      },
      {
        title: t('common.action'),
        key: 'action',
        slots: { customRender: 'action' },
        width: 200,
        fixed: 'right'
      }
    ])

    const paginationConfig = computed(() => ({
      total: props.total,
      current: props.currentPage,
      pageSize: props.pageSize,
      showSizeChanger: true,
      showQuickJumper: true,
      showTotal: (total) => t('common.totalItems', { total })
    }))

    const getStatusColor = (status) => {
      const colorMap = {
        'pending': 'orange',
        'approved': 'green',
        'rejected': 'red',
        'completed': 'blue'
      }
      return colorMap[status] || 'default'
    }

    const getStatusText = (status) => {
      return t(`amlo.reservation.${status}`)
    }

    const getDirectionText = (direction) => {
      // direction='buy' = 网点买入外币
      // direction='sell' = 网点卖出外币
      if (direction === 'buy') {
        return t('amlo.reservation.buyForeign')  // 网点买入外币
      } else if (direction === 'sell') {
        return t('amlo.reservation.sellForeign')  // 网点卖出外币
      }
      return direction || t('common.unknown')
    }

    const handleTableChange = (pagination) => {
      emit('page-change', pagination.current, pagination.pageSize)
    }

    const handleViewDetail = (record) => {
      emit('view-detail', record)
    }

    const handleAudit = (record) => {
      emit('audit', record)
    }

    const handleReverseAudit = (record) => {
      emit('reverse-audit', record)
    }

    const handleDownloadPdf = async (record) => {
      try {
        downloadingPdf.value[record.id] = true

        // 使用运行时配置（优先）或环境变量（回退）
        const backendUrl = (typeof window !== 'undefined' && window.ENV_CONFIG && window.ENV_CONFIG.API_BASE_URL)
          ? window.ENV_CONFIG.API_BASE_URL
          : (import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001')

        console.log('[ReservationList] 下载PDF - 使用后端URL:', backendUrl)
        const url = `${backendUrl}/api/amlo/reports/${record.id}/generate-pdf`
        console.log('[ReservationList] 请求URL:', url)

        const response = await fetch(url, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${authStore.token}`
          }
        })

        if (!response.ok) {
          const errorText = await response.text()
          console.error('[ReservationList] PDF生成失败 - 状态码:', response.status)
          console.error('[ReservationList] 错误内容:', errorText)
          throw new Error(`PDF生成失败 (${response.status}): ${errorText}`)
        }

        // 检查响应类型
        const contentType = response.headers.get('content-type')
        console.log('[ReservationList] 响应Content-Type:', contentType)

        // 下载PDF文件
        const blob = await response.blob()
        console.log('[ReservationList] PDF文件大小:', blob.size, 'bytes')

        const downloadUrl = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = downloadUrl
        link.download = `${record.report_type}_${record.reservation_no || record.id}.pdf`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(downloadUrl)

        console.log('[ReservationList] PDF下载成功')
        message.success(t('common.downloadSuccess'))
      } catch (error) {
        console.error('[ReservationList] 下载PDF失败:', error)
        message.error(`下载失败: ${error.message}`)
      } finally {
        downloadingPdf.value[record.id] = false
      }
    }

    return {
      hasAuditPermission,
      downloadingPdf,
      columns,
      paginationConfig,
      getStatusColor,
      getStatusText,
      getDirectionText,
      handleTableChange,
      handleViewDetail,
      handleAudit,
      handleReverseAudit,
      handleDownloadPdf
    }
  }
}
</script>

<style scoped>
.reservation-list {
  margin-top: 16px;
}
</style>

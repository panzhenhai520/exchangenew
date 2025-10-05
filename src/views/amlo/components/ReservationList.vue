<template>
  <div class="reservation-list">
    <a-table
      :columns="columns"
      :data-source="reservations"
      :loading="loading"
      :pagination="paginationConfig"
      row-key="reservation_id"
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
        </a-space>
      </template>
    </a-table>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

export default {
  name: 'ReservationList',
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

    // TODO: 从权限系统获取
    const hasAuditPermission = computed(() => true)

    const columns = [
      {
        title: t('amlo.reservation.id'),
        dataIndex: 'reservation_id',
        key: 'reservation_id',
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
    ]

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

    return {
      hasAuditPermission,
      columns,
      paginationConfig,
      getStatusColor,
      getStatusText,
      handleTableChange,
      handleViewDetail,
      handleAudit,
      handleReverseAudit
    }
  }
}
</script>

<style scoped>
.reservation-list {
  margin-top: 16px;
}
</style>

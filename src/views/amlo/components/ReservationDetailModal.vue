<template>
  <a-modal
    v-model:visible="modalVisible"
    :title="$t('amlo.reservation.detail')"
    width="800px"
    :footer="null"
  >
    <div v-if="reservation" class="reservation-detail">
      <!-- 基本信息 -->
      <a-descriptions :title="$t('amlo.reservation.basicInfo')" bordered :column="2">
        <a-descriptions-item :label="$t('amlo.reservation.id')">
          {{ reservation.reservation_id }}
        </a-descriptions-item>
        <a-descriptions-item :label="$t('amlo.reservation.reportType')">
          <a-tag color="blue">{{ reservation.report_type }}</a-tag>
        </a-descriptions-item>
        <a-descriptions-item :label="$t('amlo.reservation.status')">
          <a-tag :color="getStatusColor(reservation.status)">
            {{ $t(`amlo.reservation.${reservation.status}`) }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item :label="$t('amlo.reservation.createdAt')">
          {{ reservation.created_at }}
        </a-descriptions-item>
        <a-descriptions-item :label="$t('amlo.reservation.customerName')" :span="2">
          {{ reservation.customer_name }}
        </a-descriptions-item>
      </a-descriptions>

      <!-- 表单数据 -->
      <a-divider />
      <h4>{{ $t('amlo.reservation.formData') }}</h4>
      <a-descriptions bordered :column="1">
        <a-descriptions-item
          v-for="(value, key) in formDataDisplay"
          :key="key"
          :label="key"
        >
          {{ value }}
        </a-descriptions-item>
      </a-descriptions>

      <!-- 审核历史 -->
      <a-divider v-if="reservation.audit_history" />
      <div v-if="reservation.audit_history">
        <h4>{{ $t('amlo.reservation.auditHistory') }}</h4>
        <a-timeline>
          <a-timeline-item
            v-for="(item, index) in auditHistory"
            :key="index"
            :color="getTimelineColor(item.action)"
          >
            <p>{{ item.action_text }} - {{ item.operator }}</p>
            <p class="timeline-time">{{ item.timestamp }}</p>
            <p v-if="item.remarks">{{ $t('common.remarks') }}: {{ item.remarks }}</p>
          </a-timeline-item>
        </a-timeline>
      </div>
    </div>
  </a-modal>
</template>

<script>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

export default {
  name: 'ReservationDetailModal',
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    reservation: {
      type: Object,
      default: null
    }
  },
  emits: ['update:visible'],
  setup(props, { emit }) {
    const { t } = useI18n()

    const modalVisible = computed({
      get: () => props.visible,
      set: (value) => emit('update:visible', value)
    })

    const formDataDisplay = computed(() => {
      if (!props.reservation || !props.reservation.form_data) {
        return {}
      }
      try {
        return typeof props.reservation.form_data === 'string'
          ? JSON.parse(props.reservation.form_data)
          : props.reservation.form_data
      } catch (e) {
        return {}
      }
    })

    const auditHistory = computed(() => {
      if (!props.reservation || !props.reservation.audit_history) {
        return []
      }
      try {
        const history = typeof props.reservation.audit_history === 'string'
          ? JSON.parse(props.reservation.audit_history)
          : props.reservation.audit_history
        return Array.isArray(history) ? history : []
      } catch (e) {
        return []
      }
    })

    const getStatusColor = (status) => {
      const colorMap = {
        'pending': 'orange',
        'approved': 'green',
        'rejected': 'red',
        'completed': 'blue'
      }
      return colorMap[status] || 'default'
    }

    const getTimelineColor = (action) => {
      const colorMap = {
        'created': 'blue',
        'approved': 'green',
        'rejected': 'red',
        'reversed': 'orange',
        'completed': 'purple'
      }
      return colorMap[action] || 'gray'
    }

    return {
      modalVisible,
      formDataDisplay,
      auditHistory,
      getStatusColor,
      getTimelineColor
    }
  }
}
</script>

<style scoped>
.reservation-detail {
  max-height: 600px;
  overflow-y: auto;
}

.timeline-time {
  color: #999;
  font-size: 12px;
  margin-top: 4px;
}
</style>

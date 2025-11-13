<template>
  <div class="card mb-4 amlo-reservation-card">
    <div class="card-header py-2 bg-info text-white">
      <h6 class="mb-0">
        <font-awesome-icon :icon="['fas', 'file-alt']" class="me-2" />
        AMLO预约审核列表
      </h6>
    </div>
    <div class="card-body p-2" style="max-height: 500px; overflow-y: auto;">
      <!-- 加载状态 -->
      <div v-if="loading" class="text-center py-3">
        <div class="spinner-border spinner-border-sm text-primary" role="status">
          <span class="visually-hidden">加载中...</span>
        </div>
      </div>

      <!-- 无数据 -->
      <div v-else-if="!reservations || reservations.length === 0" class="text-center text-muted py-3 small">
        暂无预约记录
      </div>

      <!-- 预约列表 -->
      <div v-else class="reservation-list">
        <div
          v-for="item in reservations"
          :key="item.id"
          class="reservation-item"
          :class="{ 'clickable': isClickable(item) }"
          @click="handleItemClick(item)"
        >
          <!-- 状态标签 -->
          <div class="d-flex justify-content-between align-items-center mb-1">
            <span class="badge small" :class="getStatusClass(item.status)">
              {{ getStatusText(item.status) }}
            </span>
            <span class="text-muted small">{{ formatDate(item.created_at) }}</span>
          </div>

          <!-- 报告编号和客户名 -->
          <div class="small mb-1">
            <strong>{{ item.reservation_no || `#${item.id}` }}</strong>
          </div>
          <div class="small text-truncate mb-1" :title="item.customer_name">
            <font-awesome-icon :icon="['fas', 'user']" class="me-1" />
            {{ item.customer_name }}
          </div>

          <!-- 报告类型 -->
          <div class="small">
            <span class="badge bg-secondary" style="font-size: 0.65rem;">
              {{ item.report_type }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import api from '@/services/api'

export default {
  name: 'AMLOReservationCard',
  emits: ['load-reservation', 'edit-reservation'],
  setup(props, { emit }) {
    const loading = ref(false)
    const reservations = ref([])

    const loadReservations = async () => {
      loading.value = true
      try {
        // 计算最近1个月的日期范围
        const today = new Date()
        const oneMonthAgo = new Date()
        oneMonthAgo.setMonth(today.getMonth() - 1)

        const response = await api.get('/amlo/reservations', {
          params: {
            page: 1,
            page_size: 10,  // 只显示最近10条
            // 可以添加日期范围过滤如果后端支持
          }
        })

        if (response.data.success) {
          reservations.value = response.data.data.items || []
          console.log(`[AMLOReservationCard] 加载了 ${reservations.value.length} 条预约记录`)
        }
      } catch (error) {
        console.error('[AMLOReservationCard] 加载预约列表失败:', error)
        reservations.value = []
      } finally {
        loading.value = false
      }
    }

    const isClickable = (item) => {
      // 审核通过和未通过的都可以点击
      return item.status === 'approved' || item.status === 'rejected'
    }

    const handleItemClick = (item) => {
      if (!isClickable(item)) {
        return
      }

      if (item.status === 'approved') {
        // 审核通过：加载兑换信息
        emit('load-reservation', item)
      } else if (item.status === 'rejected') {
        // 审核未通过：编辑报告（修改模式）
        emit('edit-reservation', item)
      }
    }

    const getStatusClass = (status) => {
      const classMap = {
        'pending': 'bg-warning text-dark',
        'approved': 'bg-success',
        'rejected': 'bg-danger'
      }
      return classMap[status] || 'bg-secondary'
    }

    const getStatusText = (status) => {
      const textMap = {
        'pending': '等待审核',
        'approved': '审核通过',
        'rejected': '审核未通过'
      }
      return textMap[status] || status
    }

    const formatDate = (dateStr) => {
      if (!dateStr) return '-'
      const date = new Date(dateStr)
      const now = new Date()
      const diffMs = now - date
      const diffMins = Math.floor(diffMs / 60000)
      const diffHours = Math.floor(diffMs / 3600000)
      const diffDays = Math.floor(diffMs / 86400000)

      if (diffMins < 60) {
        return `${diffMins}分钟前`
      } else if (diffHours < 24) {
        return `${diffHours}小时前`
      } else if (diffDays < 7) {
        return `${diffDays}天前`
      } else {
        return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
      }
    }

    onMounted(() => {
      loadReservations()
    })

    return {
      loading,
      reservations,
      loadReservations,
      isClickable,
      handleItemClick,
      getStatusClass,
      getStatusText,
      formatDate
    }
  }
}
</script>

<style scoped>
.amlo-reservation-card .card-header {
  font-size: 0.9rem;
}

.reservation-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.reservation-item {
  padding: 0.5rem;
  border: 1px solid #e9ecef;
  border-radius: 0.25rem;
  background-color: #f8f9fa;
  transition: all 0.2s;
}

.reservation-item.clickable {
  cursor: pointer;
}

.reservation-item.clickable:hover {
  background-color: #e9ecef;
  border-color: #dee2e6;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.text-truncate {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.badge.small {
  font-size: 0.7rem;
  padding: 0.25rem 0.4rem;
}
</style>

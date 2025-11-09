<template>
  <div class="reservation-audit-view">
    <a-card>
      <template #title>
        <span>{{ $t('amlo.reservation.title') }}</span>
      </template>

      <!-- 筛选器 -->
      <ReservationFilter
        @filter="handleFilter"
        @reset="handleResetFilter"
      />

      <!-- 预约列表 -->
      <ReservationList
        :loading="loading"
        :reservations="reservations"
        :total="total"
        :current-page="currentPage"
        :page-size="pageSize"
        @page-change="handlePageChange"
        @view-detail="handleViewDetail"
        @audit="handleAudit"
        @reverse-audit="handleReverseAudit"
      />

      <!-- 详情弹窗 -->
      <ReservationDetailModal
        v-model:visible="detailModalVisible"
        :reservation="currentReservation"
      />

      <!-- 审核操作弹窗 -->
      <AuditActionModal
        v-model:visible="auditModalVisible"
        :reservation="currentReservation"
        @submit="handleSubmitAudit"
      />
    </a-card>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { useAMLOStore } from '@/stores/amlo'
import ReservationFilter from './components/ReservationFilter.vue'
import ReservationList from './components/ReservationList.vue'
import ReservationDetailModal from './components/ReservationDetailModal.vue'
import AuditActionModal from './components/AuditActionModal.vue'

export default {
  name: 'ReservationAuditView',
  components: {
    ReservationFilter,
    ReservationList,
    ReservationDetailModal,
    AuditActionModal
  },
  setup() {
    const { t } = useI18n()
    const amloStore = useAMLOStore()

    // 状态
    const loading = ref(false)
    const reservations = ref([])
    const total = ref(0)
    const currentPage = ref(1)
    const pageSize = ref(20)
    const filterParams = ref({})

    // 弹窗状态
    const detailModalVisible = ref(false)
    const auditModalVisible = ref(false)
    const currentReservation = ref(null)

    // 加载预约列表
    const loadReservations = async () => {
      loading.value = true
      try {
        const response = await amloStore.fetchReservations({
          ...filterParams.value,
          page: currentPage.value,
          page_size: pageSize.value
        })

        if (response.success) {
          reservations.value = response.data.items
          total.value = response.data.total
        } else {
          message.error(response.message)
        }
      } catch (error) {
        console.error('加载预约列表失败:', error)
        message.error(t('amlo.reservation.loadFailed'))
      } finally {
        loading.value = false
      }
    }

    // 筛选
    const handleFilter = (params) => {
      filterParams.value = params
      currentPage.value = 1
      loadReservations()
    }

    // 重置筛选
    const handleResetFilter = () => {
      filterParams.value = {}
      currentPage.value = 1
      loadReservations()
    }

    // 分页变化
    const handlePageChange = (page, size) => {
      currentPage.value = page
      pageSize.value = size
      loadReservations()
    }

    // 查看详情
    const handleViewDetail = (reservation) => {
      currentReservation.value = reservation
      detailModalVisible.value = true
    }

    // 审核
    const handleAudit = (reservation) => {
      currentReservation.value = reservation
      auditModalVisible.value = true
    }

    // 反审核
    const handleReverseAudit = async (reservation) => {
      try {
        const response = await amloStore.reverseAuditReservation(reservation.reservation_id)
        if (response.success) {
          message.success(t('amlo.reservation.reverseAuditSuccess'))
          loadReservations()
        } else {
          message.error(response.message)
        }
      } catch (error) {
        console.error('反审核失败:', error)
        message.error(t('amlo.reservation.reverseAuditFailed'))
      }
    }

    // 提交审核
    const handleSubmitAudit = async (auditData) => {
      try {
        const response = await amloStore.auditReservation(
          currentReservation.value.reservation_id,
          auditData.action,
          auditData
        )

        if (response.success) {
          message.success(t('amlo.reservation.auditSuccess'))
          auditModalVisible.value = false
          loadReservations()
        } else {
          message.error(response.message)
        }
      } catch (error) {
        console.error('审核失败:', error)
        message.error(t('amlo.reservation.auditFailed'))
      }
    }

    // 组件挂载
    onMounted(() => {
      loadReservations()
    })

    return {
      loading,
      reservations,
      total,
      currentPage,
      pageSize,
      detailModalVisible,
      auditModalVisible,
      currentReservation,
      handleFilter,
      handleResetFilter,
      handlePageChange,
      handleViewDetail,
      handleAudit,
      handleReverseAudit,
      handleSubmitAudit
    }
  }
}
</script>

<style scoped>
.reservation-audit-view {
  padding: 24px;
}
</style>

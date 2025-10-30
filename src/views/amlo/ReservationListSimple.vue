<template>
  <div class="container-fluid py-4">
    <div class="row">
      <div class="col-12">
        <div class="d-flex justify-content-between align-items-center flex-wrap gap-3 mb-4">
          <div class="d-flex align-items-center gap-3">
            <h2 class="page-title-bold mb-0 d-flex align-items-center gap-2">
              <font-awesome-icon :icon="['fas', 'calendar-check']" />
              {{ t('amlo.reservation.title') }}
            </h2>
            <span class="amlo-tag badge rounded-pill d-inline-flex align-items-center gap-2">
              <font-awesome-icon :icon="['fas', 'bookmark']" />
              <span>{{ t('amlo.reservation.title') }}</span>
            </span>
          </div>
          <button
            type="button"
            class="btn btn-outline-primary"
            @click="loadReservations"
            :disabled="loading"
          >
            <font-awesome-icon :icon="['fas', 'rotate-right']" :spin="loading" class="me-2" />
            {{ t('amlo.reservation.refresh') }}
          </button>
        </div>

        <div class="card mb-4 filter-card">
          <div class="card-header">
            <h5 class="mb-0 d-flex align-items-center">
              <font-awesome-icon :icon="['fas', 'filter']" class="me-2" />
              {{ t('amlo.reservation.filtersTitle') }}
            </h5>
          </div>
          <div class="card-body">
            <form @submit.prevent="handleSearch">
              <div class="row g-3 align-items-end">
                <div class="col-sm-6 col-lg-3">
                  <label class="form-label">{{ t('amlo.reservation.customerId') }}</label>
                  <input
                    type="text"
                    class="form-control"
                    v-model="filter.customer_id"
                    :placeholder="t('amlo.reservation.customerIdPlaceholder')"
                  />
                </div>
                <div class="col-sm-6 col-lg-3">
                  <label class="form-label">{{ t('amlo.reservation.status') }}</label>
                  <select class="form-select" v-model="filter.status">
                    <option value="">{{ t('amlo.reservation.allStatus') }}</option>
                    <option value="pending">{{ t('amlo.reservation.pending') }}</option>
                    <option value="approved">{{ t('amlo.reservation.approved') }}</option>
                    <option value="rejected">{{ t('amlo.reservation.rejected') }}</option>
                  </select>
                </div>
                <div class="col-12 col-lg-6">
                  <div class="d-flex flex-wrap gap-2 justify-content-lg-end">
                    <button type="submit" class="btn btn-primary">
                      <font-awesome-icon :icon="['fas', 'search']" class="me-2" />
                      {{ t('common.search') }}
                    </button>
                    <button type="button" class="btn btn-secondary" @click="resetFilter">
                      <font-awesome-icon :icon="['fas', 'redo']" class="me-2" />
                      {{ t('common.reset') }}
                    </button>
                  </div>
                </div>
              </div>
            </form>
          </div>
        </div>

        <div class="card reservation-card">
          <div class="card-header d-flex flex-wrap justify-content-between align-items-center gap-2">
            <div class="d-flex align-items-center gap-2">
              <span class="amlo-tag badge rounded-pill d-inline-flex align-items-center gap-2">
                <font-awesome-icon :icon="['fas', 'bookmark']" />
                <span>{{ t('amlo.reservation.title') }}</span>
              </span>
              <h5 class="mb-0 d-flex align-items-center gap-2">
                <font-awesome-icon :icon="['fas', 'clipboard-list']" />
                {{ t('amlo.reservation.recordsTitle') }}
              </h5>
            </div>
            <span class="text-muted small">
              {{ t('amlo.reservation.totalCount', { count: total }) }}
            </span>
          </div>
          <div class="card-body p-0">
            <div class="table-responsive">
              <table class="table table-hover align-middle mb-0">
                <thead class="table-light">
                  <tr>
                    <th>{{ t('amlo.reservation.id') }}</th>
                    <th>{{ t('amlo.reservation.reportType') }}</th>
                    <th>{{ t('amlo.reservation.direction') }}</th>
                    <th>{{ t('amlo.reservation.customerName') }}</th>
                    <th>{{ t('amlo.reservation.customerIdShort') }}</th>
                    <th class="text-end">{{ t('amlo.reservation.transactionAmount') }}</th>
                    <th>{{ t('amlo.reservation.status') }}</th>
                    <th>{{ t('amlo.reservation.createdAt') }}</th>
                    <th>{{ t('common.action') }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="loading">
                    <td colspan="9" class="text-center py-5">
                      <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">{{ t('common.loading') }}</span>
                      </div>
                    </td>
                  </tr>
                  <tr v-else-if="reservations.length === 0">
                    <td colspan="9" class="text-center text-muted py-5">
                      {{ t('amlo.reservation.empty') }}
                    </td>
                  </tr>
                  <tr v-else v-for="item in reservations" :key="item.id">
                    <td>{{ item.reservation_id || item.reservation_no || item.id }}</td>
                    <td>
                      <span class="badge bg-info">{{ item.report_type }}</span>
                    </td>
                    <td>
                      <span
                        class="badge"
                        :class="{
                          'bg-success': item.direction === 'buy',
                          'bg-warning': item.direction === 'sell',
                          'bg-info': item.direction === 'dual_direction'
                        }"
                      >
                        {{ getDirectionText(item.direction) }}
                      </span>
                    </td>
                    <td>{{ item.customer_name }}</td>
                    <td>{{ item.customer_id }}</td>
                    <td class="text-end">{{ formatAmount(item.local_amount) }} THB</td>
                    <td>
                      <span
                        class="badge"
                        :class="{
                          'bg-warning': item.status === 'pending',
                          'bg-success': item.status === 'approved',
                          'bg-danger': item.status === 'rejected'
                        }"
                      >
                        {{ getStatusText(item.status) }}
                      </span>
                    </td>
                    <td>{{ formatDateTime(item.created_at) }}</td>
                    <td>
                      <div class="d-flex gap-2 flex-wrap">
                        <button
                          class="btn btn-info btn-sm"
                          @click="viewPDF(item)"
                          style="min-width: 120px;"
                        >
                          <i class="fas fa-file-pdf me-1"></i>{{ t('amlo.reservation.viewReport') }}
                        </button>
                        <button
                          class="btn btn-primary btn-sm"
                          @click="viewDetail(item)"
                          style="min-width: 120px;"
                        >
                          <i class="fas fa-clipboard-check me-1"></i>{{ t('amlo.reservation.openAudit') }}
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          <div
            class="card-footer bg-white d-flex justify-content-end"
            v-if="total > pageSize"
          >
            <nav>
              <ul class="pagination mb-0">
                <li class="page-item" :class="{ disabled: currentPage === 1 }">
                  <a
                    class="page-link"
                    href="#"
                    role="button"
                    @click.prevent="changePage(currentPage - 1)"
                  >
                    {{ t('amlo.reservation.prevPage') }}
                  </a>
                </li>
                <li class="page-item active">
                  <span class="page-link">{{ currentPage }} / {{ totalPages }}</span>
                </li>
                <li class="page-item" :class="{ disabled: currentPage === totalPages }">
                  <a
                    class="page-link"
                    href="#"
                    role="button"
                    @click.prevent="changePage(currentPage + 1)"
                  >
                    {{ t('amlo.reservation.nextPage') }}
                  </a>
                </li>
              </ul>
            </nav>
          </div>
        </div>
      </div>
    </div>

    <!-- 详情模态框 -->
    <div class="modal fade" id="detailModal" tabindex="-1" ref="detailModalRef">
      <div class="modal-dialog modal-lg">
        <div class="modal-content" v-if="currentReservation">
          <div class="modal-header bg-light">
            <h5 class="modal-title">
              <i class="fas fa-clipboard-list me-2"></i>{{ t('amlo.reservation.detail') }}
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body">
            <!-- 基本信息 -->
            <h6 class="border-bottom pb-2 mb-3">
              <i class="fas fa-info-circle me-1 text-primary"></i>{{ t('amlo.reservation.basicInfo') }}
            </h6>
            <div class="row mb-3">
              <div class="col-md-6 mb-2">
                <label class="text-muted small">{{ t('amlo.reservation.reservationNo') }}</label>
                <div class="fw-bold">{{ currentReservation.reservation_no || currentReservation.id }}</div>
              </div>
              <div class="col-md-6 mb-2">
                <label class="text-muted small">{{ t('amlo.reservation.reportType') }}</label>
                <div>
                  <span class="badge bg-info">{{ currentReservation.report_type }}</span>
                </div>
              </div>
              <div class="col-md-6 mb-2">
                <label class="text-muted small">{{ t('amlo.reservation.createdAt') }}</label>
                <div>{{ formatDateTime(currentReservation.created_at) }}</div>
              </div>
              <div class="col-md-6 mb-2">
                <label class="text-muted small">{{ t('amlo.reservation.status') }}</label>
                <div>
                  <span
                    class="badge fs-6"
                    :class="{
                      'bg-warning text-dark': currentReservation.status === 'pending',
                      'bg-success': currentReservation.status === 'approved',
                      'bg-danger': currentReservation.status === 'rejected'
                    }"
                  >
                    {{ getStatusText(currentReservation.status) }}
                  </span>
                </div>
              </div>
            </div>

            <!-- 客户信息 -->
            <h6 class="border-bottom pb-2 mb-3">
              <i class="fas fa-user me-1 text-primary"></i>{{ t('amlo.reservation.customerInfo') }}
            </h6>
            <div class="row mb-3">
              <div class="col-md-6 mb-2">
                <label class="text-muted small">{{ t('amlo.reservation.customerName') }}</label>
                <div class="fw-bold">{{ currentReservation.customer_name }}</div>
              </div>
              <div class="col-md-6 mb-2">
                <label class="text-muted small">{{ t('amlo.reservation.customerId') }}</label>
                <div>{{ currentReservation.customer_id }}</div>
              </div>
              <div class="col-md-6 mb-2">
                <label class="text-muted small">{{ t('amlo.reservation.country') }}</label>
                <div>{{ currentReservation.customer_country_code || '-' }}</div>
              </div>
            </div>

            <!-- 交易信息 -->
            <h6 class="border-bottom pb-2 mb-3">
              <i class="fas fa-money-bill-wave me-1 text-primary"></i>{{ t('amlo.reservation.transactionInfo') }}
            </h6>
            <div class="row mb-3">
              <div class="col-md-6 mb-2">
                <label class="text-muted small">{{ t('amlo.reservation.localAmount') }}</label>
                <div class="fw-bold fs-5 text-success">{{ formatAmount(currentReservation.local_amount) }} THB</div>
              </div>
              <div class="col-md-6 mb-2">
                <label class="text-muted small">{{ t('amlo.reservation.currency') }}</label>
                <div>{{ currentReservation.currency_id || '-' }}</div>
              </div>
              <div class="col-md-6 mb-2">
                <label class="text-muted small">{{ t('amlo.reservation.direction') }}</label>
                <div>
                  <span class="badge bg-secondary">{{ getDirectionText(currentReservation.direction) }}</span>
                </div>
              </div>
              <div class="col-md-6 mb-2">
                <label class="text-muted small">{{ t('amlo.reservation.foreignAmount') }}</label>
                <div>{{ formatAmount(currentReservation.amount) }}</div>
              </div>
            </div>

            <!-- 审核信息 -->
            <div v-if="currentReservation.status !== 'pending'">
              <h6 class="border-bottom pb-2 mb-3">
                <i class="fas fa-check-circle me-1 text-primary"></i>{{ t('amlo.reservation.auditInfo') }}
              </h6>
              <div class="row mb-3">
                <div class="col-md-6 mb-2">
                  <label class="text-muted small">{{ t('amlo.reservation.auditedAt') }}</label>
                  <div>{{ formatDateTime(currentReservation.audit_time) || '-' }}</div>
                </div>
                <div class="col-md-6 mb-2">
                  <label class="text-muted small">{{ t('amlo.reservation.auditor') }}</label>
                  <div>{{ currentReservation.auditor_id || '-' }}</div>
                </div>
                <div class="col-12 mb-2" v-if="currentReservation.rejection_reason">
                  <label class="text-muted small">{{ t('amlo.reservation.rejectionReason') }}</label>
                  <div class="alert alert-danger mb-0">{{ currentReservation.rejection_reason }}</div>
                </div>
                <div class="col-12 mb-2" v-if="currentReservation.remarks">
                  <label class="text-muted small">{{ t('amlo.reservation.remarks') }}</label>
                  <div class="alert alert-info mb-0">{{ currentReservation.remarks }}</div>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer d-flex flex-wrap gap-2 justify-content-end">
            <button
              v-if="currentReservation && currentReservation.status === 'pending'"
              type="button"
              class="btn btn-success"
              @click="openAuditModal(currentReservation, 'approve')"
            >
              <i class="fas fa-check me-1"></i>{{ t('amlo.reservation.approve') }}
            </button>
            <button
              v-if="currentReservation && currentReservation.status === 'pending'"
              type="button"
              class="btn btn-danger"
              @click="openAuditModal(currentReservation, 'reject')"
            >
              <i class="fas fa-times me-1"></i>{{ t('amlo.reservation.reject') }}
            </button>
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
              <i class="fas fa-times me-1"></i>{{ t('common.close') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 审核模态框 -->
    <div class="modal fade" id="auditModal" tabindex="-1" ref="auditModalRef">
      <div class="modal-dialog">
        <div class="modal-content" v-if="auditingItem">
          <div class="modal-header" :class="auditAction === 'approve' ? 'bg-success text-white' : 'bg-danger text-white'">
            <h5 class="modal-title">
              <i class="fas me-2" :class="auditAction === 'approve' ? 'fa-check-circle' : 'fa-times-circle'"></i>
              {{ auditModalTitle }}
            </h5>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body">
            <!-- 显示预约基本信息 -->
            <div class="alert alert-light border">
              <div class="mb-2">
                <strong>{{ t('amlo.reservation.reservationNo') }}：</strong>{{ auditingItem.reservation_no || auditingItem.id }}
              </div>
              <div class="mb-2">
                <strong>{{ t('amlo.reservation.customerName') }}：</strong>{{ auditingItem.customer_name }}
              </div>
              <div class="mb-2">
                <strong>{{ t('amlo.reservation.localAmount') }}：</strong>
                <span class="text-success fw-bold">{{ formatAmount(auditingItem.local_amount) }} THB</span>
              </div>
            </div>

            <!-- 拒绝时需要填写原因 -->
            <div v-if="auditAction === 'reject'" class="mb-3">
              <label class="form-label text-danger fw-bold">
                <i class="fas fa-exclamation-triangle me-1"></i>{{ t('amlo.reservation.rejectionReason') }} <span class="text-danger">*</span>
              </label>
              <textarea
                class="form-control"
                v-model="auditForm.rejection_reason"
                rows="4"
                :placeholder="t('amlo.reservation.rejectionReasonPlaceholder')"
                required
              ></textarea>
              <div class="form-text">{{ t('amlo.reservation.rejectionReasonHelper') }}</div>
            </div>

            <!-- 通过时可选填备注 -->
            <div class="mb-3">
              <label class="form-label">{{ t('amlo.reservation.reviewRemarkOptional') }}</label>
              <textarea
                class="form-control"
                v-model="auditForm.remarks"
                rows="3"
                :placeholder="t('amlo.reservation.reviewRemarkPlaceholder')"
              ></textarea>
            </div>

            <!-- 确认提示 -->
            <div class="alert" :class="auditAction === 'approve' ? 'alert-success' : 'alert-danger'">
              <i class="fas fa-info-circle me-1"></i>
              {{ auditAction === 'approve' ? t('amlo.reservation.approveNotice') : t('amlo.reservation.rejectNotice') }}
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
              <i class="fas fa-times me-1"></i>{{ t('common.cancel') }}
            </button>
            <button
              type="button"
              class="btn"
              :class="auditAction === 'approve' ? 'btn-success' : 'btn-danger'"
              @click="submitAudit"
              :disabled="auditAction === 'reject' && !auditForm.rejection_reason"
            >
              <i class="fas me-1" :class="auditAction === 'approve' ? 'fa-check' : 'fa-times'"></i>
              {{ auditAction === 'approve' ? t('amlo.reservation.confirmApprove') : t('amlo.reservation.confirmReject') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Modal } from 'bootstrap'
import api from '@/services/api'

export default {
  name: 'ReservationListSimple',
  setup() {
    const { t } = useI18n()
    const loading = ref(false)
    const reservations = ref([])
    const total = ref(0)
    const currentPage = ref(1)
    const pageSize = ref(20)
    const filter = ref({
      customer_id: '',
      status: ''
    })
    
    const currentReservation = ref(null)
    const detailModalRef = ref(null)
    let detailModal = null

    // 审核相关状态
    const auditingItem = ref(null)
    const auditAction = ref('approve') // 'approve' or 'reject'
    const auditForm = ref({
      rejection_reason: '',
      remarks: ''
    })
    const auditModalRef = ref(null)
    let auditModal = null

    const totalPages = computed(() => Math.ceil(total.value / pageSize.value))
    const auditModalTitle = computed(() =>
      auditAction.value === 'approve'
        ? t('amlo.reservation.approveTitle')
        : t('amlo.reservation.rejectTitle')
    )

    const loadReservations = async () => {
      loading.value = true
      try {
        const params = {
          page: currentPage.value,
          page_size: pageSize.value,
          ...filter.value
        }
        
        const response = await api.get('/amlo/reservations', { params })
        
        if (response.data.success) {
          reservations.value = response.data.data.items || []
          total.value = response.data.data.total || 0
        }
      } catch (error) {
        console.error('[ReservationListSimple] Failed to load reservations:', error)
      } finally {
        loading.value = false
      }
    }

    const resetFilter = () => {
      filter.value = { customer_id: '', status: '' }
      currentPage.value = 1
      loadReservations()
    }

    const changePage = (page) => {
      if (page >= 1 && page <= totalPages.value) {
        currentPage.value = page
        loadReservations()
      }
    }

    const handleSearch = () => {
      currentPage.value = 1
      loadReservations()
    }

    const viewDetail = (item) => {
      currentReservation.value = item
      if (!detailModal && detailModalRef.value) {
        detailModal = new Modal(detailModalRef.value)
      }
      detailModal.show()
    }

    const openAuditModal = (item, action) => {
      auditingItem.value = item
      auditAction.value = action
      // 重置表单
      auditForm.value = {
        rejection_reason: '',
        remarks: ''
      }
      // 先关闭详情模态框，避免遮挡
      // 打开审核模态框
      if (!auditModal && auditModalRef.value) {
        auditModal = new Modal(auditModalRef.value)
      }
      auditModal.show()
    }

    const submitAudit = async () => {
      if (!auditingItem.value) return

      // 验证拒绝原因
      if (auditAction.value === 'reject' && !auditForm.value.rejection_reason) {
        alert(t('amlo.reservation.rejectionReasonRequired'))
        return
      }

      try {
        const payload = {
          action: auditAction.value,
          rejection_reason: auditForm.value.rejection_reason || undefined,
          remarks: auditForm.value.remarks || undefined
        }

        const response = await api.post(
          `/amlo/reservations/${auditingItem.value.id}/audit`,
          payload
        )

        if (response.data.success) {
          // 关闭模态框
          auditModal.hide()

          // 静默刷新列表，不显示弹窗
          await loadReservations()

          // 显示简洁的Toast通知（可选）
          showToast(auditAction.value === 'approve' ? t('amlo.reservation.toastApprove') : t('amlo.reservation.toastReject'))
        } else {
          alert(`${t('amlo.reservation.auditFailed')}: ${response.data.message || t('amlo.reservation.unknownError')}`)
        }
      } catch (error) {
        console.error('[ReservationListSimple] Audit failed:', error)
        alert(`${t('amlo.reservation.auditFailed')}: ${error.response?.data?.message || error.message || t('amlo.reservation.unknownError')}`)
      }
    }

    // 显示Toast通知
    const showToast = (message) => {
      // 创建Toast元素
      const toastEl = document.createElement('div')
      toastEl.className = 'toast-notification'
      toastEl.textContent = message
      document.body.appendChild(toastEl)

      // 显示Toast
      setTimeout(() => {
        toastEl.classList.add('show')
      }, 10)

      // 2秒后隐藏并移除
      setTimeout(() => {
        toastEl.classList.remove('show')
        setTimeout(() => {
          document.body.removeChild(toastEl)
        }, 300)
      }, 2000)
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
      return new Date(dt).toLocaleString()
    }
    
    const viewPDF = async (item) => {
      if (!item.id) {
        alert(t('amlo.reservation.invalidReservation'))
        return
      }

      try {
        // Generate PDF directly from reservation (no need to wait for approval)
        console.log('[ReservationListSimple] Generating PDF - reservation ID:', item.id)

        // Download PDF via API (token automatically attached)
        const response = await api.get(`/amlo/reports/${item.id}/generate-pdf`, {
          responseType: 'blob'  // Receive binary data
        })

        console.log('[ReservationListSimple] PDF response:', response)

        // 创建Blob对象
        const blob = new Blob([response.data], { type: 'application/pdf' })
        const blobUrl = window.URL.createObjectURL(blob)

        console.log('[ReservationListSimple] PDF file size:', blob.size, 'bytes')

        // 在新窗口打开PDF
        const pdfWindow = window.open(blobUrl, '_blank')

        if (!pdfWindow) {
          // Fallback to download when popup blocked
          const link = document.createElement('a')
          link.href = blobUrl
          link.download = `${item.report_type}_${item.reservation_no || item.id}.pdf`
          document.body.appendChild(link)
          link.click()
          document.body.removeChild(link)
          console.log('[ReservationListSimple] Popup blocked, triggered download')
        }

        // Delay revoke to allow browser load
        setTimeout(() => {
          window.URL.revokeObjectURL(blobUrl)
        }, 60000)  // 60秒后释放
      } catch (error) {
        console.error('[ReservationListSimple] Failed to open PDF:', error)
        const errorMsg = error.response?.data?.message || error.message
        alert(`${t('amlo.reservation.viewReportFailed')}: ${errorMsg}`)
      }
    }

    const getStatusText = (status) => {
      const keyMap = {
        'pending': 'pending',
        'approved': 'approved',
        'rejected': 'rejected',
        'completed': 'completed'
      }
      const key = keyMap[status]
      return key ? t(`amlo.reservation.${key}`) : (status || '-')
    }

    const getDirectionText = (direction) => {
      const keyMap = {
        'buy': 'buyForeign',
        'sell': 'sellForeign',
        'dual_direction': 'dualDirection'
      }
      const key = keyMap[direction]
      return key ? t(`amlo.reservation.${key}`) : (direction || '-')
    }

    onMounted(() => {
      loadReservations()
    })

    return {
      loading,
      reservations,
      total,
      currentPage,
      pageSize,
      totalPages,
      auditModalTitle,
      t,
      filter,
      currentReservation,
      detailModalRef,
      auditingItem,
      auditAction,
      auditForm,
      auditModalRef,
      loadReservations,
      resetFilter,
      handleSearch,
      changePage,
      viewDetail,
      viewPDF,
      openAuditModal,
      submitAudit,
      showToast,
      formatAmount,
      formatDateTime,
      getStatusText,
      getDirectionText
    }
  }
}
</script>

<style scoped>
.page-title-bold {
  font-weight: 700;
  color: #212529;
}

.amlo-tag {
  background-color: rgba(33, 37, 41, 0.04);
  color: #495057;
  padding: 0.35rem 1rem;
  font-size: 0.85rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  border: 1px solid rgba(73, 80, 87, 0.2);
}

.filter-card .card-header {
  background-color: #f8f9fa;
  border-bottom: 0;
}

.filter-card .btn {
  min-width: 120px;
}

.reservation-card .card-header {
  background-color: #f8f9fa;
  border-bottom: 0;
}

.reservation-card .card-footer {
  border-top: 1px solid #f1f3f5;
}

.card-footer .page-link {
  cursor: pointer;
}

.card-footer .page-link:focus {
  box-shadow: none;
}

.card-footer .page-item.disabled .page-link {
  cursor: not-allowed;
}

.table th {
  white-space: nowrap;
}

pre {
  max-height: 300px;
  overflow-y: auto;
  font-size: 0.875rem;
}

/* 操作按钮样式优化 */
.btn-sm {
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
  border-radius: 0.25rem;
}

/* 确保按钮文字不换行 */
.d-flex.gap-2 .btn {
  white-space: nowrap;
}

/* 详情模态框标签样式 */
.modal-body label.text-muted {
  font-weight: 500;
  margin-bottom: 0.25rem;
  display: block;
}

/* 分组标题样式 */
.modal-body h6 {
  color: #495057;
  font-weight: 600;
  margin-top: 1rem;
}

.modal-body h6:first-child {
  margin-top: 0;
}

/* 审核模态框按钮禁用状态 */
.modal-footer .btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .filter-card .btn {
    width: 100%;
  }

  .d-flex.gap-2 {
    flex-direction: column;
    gap: 0.5rem !important;
  }

  .d-flex.gap-2 .btn {
    width: 100%;
  }
}
</style>

<style>
/* Toast通知样式 - 全局样式，不使用scoped */
.toast-notification {
  position: fixed;
  top: 80px;
  right: 20px;
  background-color: #28a745;
  color: white;
  padding: 12px 24px;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  font-size: 14px;
  font-weight: 500;
  z-index: 9999;
  opacity: 0;
  transform: translateX(400px);
  transition: all 0.3s ease-in-out;
}

.toast-notification.show {
  opacity: 1;
  transform: translateX(0);
}

/* 响应式：移动端Toast位置调整 */
@media (max-width: 768px) {
  .toast-notification {
    top: 60px;
    right: 10px;
    left: 10px;
    text-align: center;
  }
}
</style>


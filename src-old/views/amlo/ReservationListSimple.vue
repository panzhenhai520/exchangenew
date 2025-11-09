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
              <table class="table table-hover align-middle mb-0 compact-table">
                <thead class="table-light">
                  <tr>
                    <th style="width: 60px;">{{ t('amlo.reservation.id') }}</th>
                    <th style="width: 150px;">{{ t('amlo.reservation.reportNo') }}</th>
                    <th style="width: 90px;">{{ t('amlo.reservation.reportType') }}</th>
                    <th style="width: 70px;">{{ t('amlo.reservation.direction') }}</th>
                    <th style="width: 100px;">{{ t('amlo.reservation.customerName') }}</th>
                    <th style="width: 110px;">{{ t('amlo.reservation.customerIdShort') }}</th>
                    <th style="width: 110px;" class="text-end">{{ t('amlo.reservation.transactionAmount') }}</th>
                    <th style="width: 70px;">{{ t('amlo.reservation.status') }}</th>
                    <th style="width: 130px;">{{ t('amlo.reservation.createdAt') }}</th>
                    <th style="min-width: 280px;">{{ t('common.action') }}</th>
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
                  <tr v-else-if="reservations.length === 0">
                    <td colspan="10" class="text-center text-muted py-5">
                      {{ t('amlo.reservation.empty') }}
                    </td>
                  </tr>
                  <tr v-else v-for="item in reservations" :key="item.id">
                    <td class="text-truncate" style="max-width: 60px;">{{ item.id }}</td>
                    <td class="text-truncate" style="max-width: 150px;" :title="item.report_no">
                      <span v-if="item.report_no" class="badge bg-secondary" style="font-size: 0.65rem; font-family: monospace;">
                        {{ item.report_no }}
                      </span>
                      <span v-else class="text-muted" style="font-size: 0.75rem;">-</span>
                    </td>
                    <td>
                      <span class="badge bg-info" style="font-size: 0.7rem;">{{ item.report_type }}</span>
                    </td>
                    <td>
                      <span
                        class="badge"
                        style="font-size: 0.7rem;"
                        :class="{
                          'bg-success': item.direction === 'buy',
                          'bg-warning': item.direction === 'sell',
                          'bg-info': item.direction === 'dual_direction'
                        }"
                      >
                        {{ getDirectionText(item.direction) }}
                      </span>
                    </td>
                    <td class="text-truncate" style="max-width: 100px;" :title="item.customer_name">{{ item.customer_name }}</td>
                    <td class="text-truncate" style="max-width: 110px;" :title="item.customer_id">{{ item.customer_id }}</td>
                    <td class="text-end" style="white-space: nowrap;">{{ formatAmount(item.local_amount) }}</td>
                    <td>
                      <span
                        class="badge"
                        style="font-size: 0.7rem;"
                        :class="{
                          'bg-warning': item.status === 'pending',
                          'bg-success': item.status === 'approved',
                          'bg-danger': item.status === 'rejected'
                        }"
                      >
                        {{ getStatusText(item.status) }}
                      </span>
                    </td>
                    <td style="font-size: 0.85rem; white-space: nowrap;">{{ formatDateTime(item.created_at) }}</td>
                    <td>
                      <div class="d-flex gap-1 flex-nowrap action-buttons">
                        <button
                          class="btn btn-warning btn-sm"
                          @click="editReservation(item)"
                          :title="t('amlo.reservation.editForm')"
                        >
                          <i class="fas fa-edit"></i>
                          <span class="btn-text">{{ t('common.edit') }}</span>
                        </button>
                        <button
                          class="btn btn-info btn-sm"
                          @click="viewPDF(item)"
                          :title="t('amlo.reservation.viewReport')"
                        >
                          <i class="fas fa-file-pdf"></i>
                          <span class="btn-text">{{ t('amlo.reservation.viewReport') }}</span>
                        </button>
                        <button
                          class="btn btn-primary btn-sm"
                          @click="viewDetail(item)"
                          :title="t('amlo.reservation.openAudit')"
                        >
                          <i class="fas fa-clipboard-check"></i>
                          <span class="btn-text">{{ t('amlo.reservation.openAudit') }}</span>
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

    <!-- 编辑模态框 🆕 子任务9.3: 加载预约数据到DynamicForm -->
    <div class="modal fade" id="editModal" tabindex="-1" ref="editModalRef">
      <div class="modal-dialog modal-xl modal-dialog-scrollable">
        <div class="modal-content" v-if="editingReservation">
          <div class="modal-header bg-warning text-dark">
            <h5 class="modal-title">
              <i class="fas fa-edit me-2"></i>{{ t('amlo.reservation.editForm') }}
              <span class="badge bg-dark ms-2">{{ editingReservation.report_type }}</span>
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body" style="max-height: 70vh; overflow-y: auto;">
            <!-- DynamicForm组件 -->
            <DynamicFormImproved
              v-if="editFormData"
              :report-type="editingReservation.report_type"
              :initial-data="editFormData"
              :submit-button-text="t('amlo.reservation.saveChanges')"
              @submit="handleFormSubmit"
              @view-pdf="handleViewPDF"
            />
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
              <i class="fas fa-times me-1"></i>{{ t('common.cancel') }}
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
import DynamicFormImproved from '@/components/amlo/DynamicForm/DynamicFormImproved.vue'

export default {
  name: 'ReservationListSimple',
  components: {
    DynamicFormImproved
  },
  setup() {
    const { t } = useI18n()
    const loading = ref(false)
    const reservations = ref([])
    const total = ref(0)
    const currentPage = ref(1)
    const pageSize = ref(8)  // Changed from 20 to 8 per requirements
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

    // 编辑相关状态 🆕 子任务9.3
    const editingReservation = ref(null)
    const editFormData = ref(null)
    const editModalRef = ref(null)
    let editModal = null

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
          // 🆕 关闭所有模态框（审核、详情、编辑）
          if (auditModal) {
            auditModal.hide()
          }

          if (detailModal) {
            detailModal.hide()
          }

          if (editModal) {
            editModal.hide()
          }

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
        console.log('[ReservationListSimple] Opening PDF viewer window - reservation ID:', item.id)

        // Build URL with query parameters
        const baseUrl = window.location.origin
        const pdfViewerPath = '/amlo/pdf-viewer'
        const params = new URLSearchParams({
          id: item.id,
          title: `${item.report_type} - ${item.reservation_no || item.id}`,
          reportType: item.report_type
        })
        const url = `${baseUrl}${pdfViewerPath}?${params.toString()}`

        console.log('[ReservationListSimple] PDF Viewer URL:', url)

        // 检测扩展显示器并计算窗口参数
        const screenWidth = window.screen.width
        const screenHeight = window.screen.height
        const screenAvailWidth = window.screen.availWidth
        const screenAvailHeight = window.screen.availHeight

        console.log('[ReservationListSimple] 屏幕信息:', {
          width: screenWidth,
          height: screenHeight,
          availWidth: screenAvailWidth,
          availHeight: screenAvailHeight,
          availLeft: window.screen.availLeft,
          availTop: window.screen.availTop
        })

        // 用户的主屏幕宽度
        const primaryScreenWidth = 1620  // 修改为用户实际的主屏宽度

        // 强制启用扩展显示器模式
        let hasSecondScreen = true
        let secondScreenLeft = primaryScreenWidth
        let secondScreenTop = 0
        let secondScreenWidth = 1920  // 假设副屏是1920宽
        let secondScreenHeight = 1080

        console.log('[ReservationListSimple] 🖥️ 启用扩展显示器模式')
        console.log('[ReservationListSimple] 主屏宽度:', primaryScreenWidth, 'px')
        console.log('[ReservationListSimple] 副屏位置: left=' + secondScreenLeft + 'px')

        // 窗口参数
        let windowLeft = hasSecondScreen ? secondScreenLeft : 0
        let windowTop = hasSecondScreen ? secondScreenTop : 0
        let windowWidth = hasSecondScreen ? secondScreenWidth : screenAvailWidth
        let windowHeight = hasSecondScreen ? secondScreenHeight : screenAvailHeight

        // 窗口特性
        const windowFeatures = `width=${windowWidth},height=${windowHeight},left=${windowLeft},top=${windowTop},resizable=yes,scrollbars=yes,toolbar=no,menubar=no,location=no,status=no`

        console.log('[ReservationListSimple] Window features:', windowFeatures)

        // Open new window
        const pdfWindow = window.open(url, 'AMLOPDFViewer', windowFeatures)

        if (!pdfWindow) {
          alert(t('amlo.reservation.popupBlocked') || '弹出窗口被阻止，请允许弹出窗口后重试')
          console.error('[ReservationListSimple] Failed to open window - popup blocked')
        } else {
          console.log('[ReservationListSimple] ✅ PDF查看器窗口已打开')

          // 等待窗口加载完成后，尝试移动和调整大小
          setTimeout(() => {
            try {
              console.log('[ReservationListSimple] 尝试移动窗口到扩展显示器...')

              // 移动窗口到副屏
              pdfWindow.moveTo(windowLeft, windowTop)

              // 调整窗口大小为最大化
              pdfWindow.resizeTo(windowWidth, windowHeight)

              // 再次聚焦
              pdfWindow.focus()

              console.log('[ReservationListSimple] 窗口已移动和调整大小')
              console.log(`[ReservationListSimple] 位置: (${windowLeft}, ${windowTop})`)
              console.log(`[ReservationListSimple] 大小: ${windowWidth}x${windowHeight}`)

              // 提示用户使用快捷键（如果自动移动失败）
              setTimeout(() => {
                console.log('[ReservationListSimple] 💡 提示：如果窗口未在扩展显示器上，请按 Win + Shift + → 移动窗口')
              }, 1000)

            } catch (e) {
              console.error('[ReservationListSimple] 移动窗口失败:', e)
              console.log('[ReservationListSimple] 💡 提示：请按 Win + Shift + → 将窗口移动到扩展显示器')
            }
          }, 500)

          pdfWindow.focus()
        }

      } catch (error) {
        console.error('[ReservationListSimple] Open PDF viewer failed:', error)
        alert(t('amlo.reservation.viewReportFailed') || 'PDF查看器打开失败: ' + (error.message || 'Unknown error'))
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

    const editReservation = async (item) => {
      /**
       * 🆕 子任务9.2 & 9.3: 编辑预约 - 加载完整表单数据到DynamicForm
       *
       * 功能：
       * 1. 调用新的API获取完整预约详情（包括form_data）
       * 2. 打开编辑模态框
       * 3. 将form_data加载到DynamicFormImproved组件
       */
      if (!item.id) {
        alert(t('amlo.reservation.invalidReservation'))
        return
      }

      try {
        console.log('[ReservationListSimple] 加载预约详情 - ID:', item.id)

        // 调用新的API获取完整数据
        const response = await api.get(`/amlo/reservations/${item.id}`)

        if (response.data.success) {
          const reservationData = response.data.data

          console.log('[ReservationListSimple] 预约详情加载成功:', reservationData)

          // 设置编辑状态
          editingReservation.value = reservationData

          // 提取form_data用于DynamicForm
          // form_data是JSON对象，包含所有表单字段的值
          editFormData.value = reservationData.form_data || {}

          console.log('[ReservationListSimple] 表单数据:', editFormData.value)

          // 打开编辑模态框
          if (!editModal && editModalRef.value) {
            editModal = new Modal(editModalRef.value)
          }
          editModal.show()
        } else {
          alert(`${t('amlo.reservation.loadDetailFailed')}: ${response.data.message}`)
        }
      } catch (error) {
        console.error('[ReservationListSimple] 加载预约详情失败:', error)
        alert(`${t('amlo.reservation.loadDetailFailed')}: ${error.response?.data?.message || error.message}`)
      }
    }

    const handleFormSubmit = async (formData) => {
      /**
       * 🆕 子任务9.3: 处理表单提交
       *
       * 功能：保存编辑后的表单数据
       * TODO: 需要实现后端API来更新预约的form_data
       */
      try {
        console.log('[ReservationListSimple] 提交表单数据:', formData)

        // 调用API更新预约数据
        // 注意：这需要后端提供一个PATCH或PUT端点来更新预约的form_data
        const response = await api.put(
          `/amlo/reservations/${editingReservation.value.id}`,
          { form_data: formData }
        )

        if (response.data.success) {
          showToast(t('amlo.reservation.updateSuccess'))
          editModal.hide()
          // 刷新列表
          await loadReservations()
        } else {
          alert(`${t('amlo.reservation.updateFailed')}: ${response.data.message}`)
        }
      } catch (error) {
        console.error('[ReservationListSimple] 更新预约失败:', error)
        // 如果是404错误，说明后端还没有这个端点
        if (error.response?.status === 404) {
          alert(t('amlo.reservation.updateEndpointNotImplemented'))
        } else {
          alert(`${t('amlo.reservation.updateFailed')}: ${error.response?.data?.message || error.message}`)
        }
      }
    }

    const handleViewPDF = async (data) => {
      /**
       * 🆕 处理查看PDF事件
       * 从DynamicForm触发，在新窗口显示已填写的PDF
       */
      try {
        console.log('[ReservationListSimple] ===== handleViewPDF 被调用 =====')
        console.log('[ReservationListSimple] 接收到的data:', data)
        console.log('[ReservationListSimple] editingReservation.value:', editingReservation.value)
        console.log('[ReservationListSimple] reservation ID:', editingReservation.value?.id)

        if (!editingReservation.value?.id) {
          console.error('[ReservationListSimple] ❌ 没有找到有效的reservation ID')
          alert(t('amlo.reservation.invalidReservation') || '无效的预约信息')
          return
        }

        // Use same window opening logic as viewPDF
        const item = editingReservation.value
        item.report_type = data.reportType  // Ensure report_type is set

        console.log('[ReservationListSimple] Opening PDF viewer window from DynamicForm')

        // Build URL with query parameters
        const baseUrl = window.location.origin
        const pdfViewerPath = '/amlo/pdf-viewer'
        const params = new URLSearchParams({
          id: item.id,
          title: `${data.reportType} - ${item.reservation_no || item.id}`,
          reportType: data.reportType
        })
        const url = `${baseUrl}${pdfViewerPath}?${params.toString()}`

        console.log('[ReservationListSimple] PDF Viewer URL:', url)

        // 检测扩展显示器并计算窗口参数 (from DynamicForm)
        const screenWidth = window.screen.width
        const screenHeight = window.screen.height
        const screenAvailWidth = window.screen.availWidth
        const screenAvailHeight = window.screen.availHeight

        console.log('[ReservationListSimple] 屏幕信息 (from DynamicForm):', {
          width: screenWidth,
          height: screenHeight,
          availWidth: screenAvailWidth,
          availHeight: screenAvailHeight,
          availLeft: window.screen.availLeft,
          availTop: window.screen.availTop
        })

        // 用户的主屏幕宽度
        const primaryScreenWidth = 1620  // 修改为用户实际的主屏宽度

        // 强制启用扩展显示器模式
        let hasSecondScreen = true
        let secondScreenLeft = primaryScreenWidth
        let secondScreenTop = 0
        let secondScreenWidth = 1920  // 假设副屏是1920宽
        let secondScreenHeight = 1080

        console.log('[ReservationListSimple] 🖥️ 启用扩展显示器模式 (from DynamicForm)')
        console.log('[ReservationListSimple] 主屏宽度:', primaryScreenWidth, 'px')
        console.log('[ReservationListSimple] 副屏位置: left=' + secondScreenLeft + 'px')

        // 窗口参数
        let windowLeft = hasSecondScreen ? secondScreenLeft : 0
        let windowTop = hasSecondScreen ? secondScreenTop : 0
        let windowWidth = hasSecondScreen ? secondScreenWidth : screenAvailWidth
        let windowHeight = hasSecondScreen ? secondScreenHeight : screenAvailHeight

        // 窗口特性
        const windowFeatures = `width=${windowWidth},height=${windowHeight},left=${windowLeft},top=${windowTop},resizable=yes,scrollbars=yes,toolbar=no,menubar=no,location=no,status=no`

        console.log('[ReservationListSimple] Window features (from DynamicForm):', windowFeatures)

        // Open new window
        const pdfWindow = window.open(url, 'AMLOPDFViewer', windowFeatures)

        if (!pdfWindow) {
          alert(t('amlo.reservation.popupBlocked') || '弹出窗口被阻止，请允许弹出窗口后重试')
          console.error('[ReservationListSimple] Failed to open window - popup blocked')
        } else {
          console.log('[ReservationListSimple] ✅ PDF查看器窗口已打开 (from DynamicForm)')

          // 等待窗口加载完成后，尝试移动和调整大小
          setTimeout(() => {
            try {
              console.log('[ReservationListSimple] 尝试移动窗口到扩展显示器... (from DynamicForm)')

              // 移动窗口到副屏
              pdfWindow.moveTo(windowLeft, windowTop)

              // 调整窗口大小为最大化
              pdfWindow.resizeTo(windowWidth, windowHeight)

              // 再次聚焦
              pdfWindow.focus()

              console.log('[ReservationListSimple] 窗口已移动和调整大小 (from DynamicForm)')
              console.log(`[ReservationListSimple] 位置: (${windowLeft}, ${windowTop})`)
              console.log(`[ReservationListSimple] 大小: ${windowWidth}x${windowHeight}`)

              // 提示用户使用快捷键（如果自动移动失败）
              setTimeout(() => {
                console.log('[ReservationListSimple] 💡 提示：如果窗口未在扩展显示器上，请按 Win + Shift + → 移动窗口')
              }, 1000)

            } catch (e) {
              console.error('[ReservationListSimple] 移动窗口失败:', e)
              console.log('[ReservationListSimple] 💡 提示：请按 Win + Shift + → 将窗口移动到扩展显示器')
            }
          }, 500)

          pdfWindow.focus()
        }

      } catch (error) {
        console.error('[ReservationListSimple] ❌ 查看PDF失败:', error)
        console.error('[ReservationListSimple] 错误详情:', error.response?.data || error.message)
        alert(t('amlo.reservation.viewReportFailed') || 'PDF查看器打开失败: ' + (error.message || 'Unknown error'))
      }
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
      getDirectionText,
      editReservation,
      editingReservation,
      editFormData,
      editModalRef,
      handleFormSubmit,
      handleViewPDF
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
  min-width: 100px;  /* Widen buttons to prevent text wrapping in Chinese/English/Thai */
  text-align: center;
  padding: 0.5rem 1rem;  /* Increase padding for better spacing */
}

.card-footer .page-link:focus {
  box-shadow: none;
}

.card-footer .page-item.disabled .page-link {
  cursor: not-allowed;
}

/* Specific styling for previous/next page buttons */
.pagination .page-item:first-child .page-link,
.pagination .page-item:last-child .page-link {
  min-width: 110px;  /* Extra width for "Previous Page" / "Next Page" / "上一页" / "下一页" */
}

/* Center pagination page indicator */
.pagination .page-item.active .page-link {
  min-width: 90px;
  font-weight: 600;
}

.table th {
  white-space: nowrap;
}

pre {
  max-height: 300px;
  overflow-y: auto;
  font-size: 0.875rem;
}

/* 紧凑表格样式 */
.compact-table {
  font-size: 0.875rem;
}

.compact-table th {
  padding: 0.5rem 0.3rem;
  font-size: 0.8rem;
}

.compact-table td {
  padding: 0.4rem 0.3rem;
  vertical-align: middle;
}

/* 操作按钮紧凑样式 */
.action-buttons {
  gap: 0.25rem !important;
}

.action-buttons .btn-sm {
  padding: 0.25rem 0.4rem;
  font-size: 0.75rem;
  border-radius: 0.2rem;
  white-space: nowrap;
}

.action-buttons .btn-sm i {
  font-size: 0.8rem;
}

.action-buttons .btn-text {
  margin-left: 0.25rem;
}

/* 文本截断 */
.text-truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 徽章样式优化 */
.badge {
  padding: 0.25rem 0.4rem;
  font-size: 0.7rem;
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


<template>
  <div class="container-fluid py-4">
    <div class="card">
      <div class="card-header bg-primary text-white">
        <h5 class="mb-0">
          <i class="fas fa-clipboard-list me-2"></i>
          AMLO预约审核
        </h5>
      </div>
      <div class="card-body">
        <!-- 筛选器 -->
        <div class="row mb-3">
          <div class="col-md-3">
            <input 
              type="text" 
              class="form-control" 
              v-model="filter.customer_id"
              placeholder="客户证件号"
            />
          </div>
          <div class="col-md-3">
            <select class="form-select" v-model="filter.status">
              <option value="">全部状态</option>
              <option value="pending">待审核</option>
              <option value="approved">已通过</option>
              <option value="rejected">已拒绝</option>
            </select>
          </div>
          <div class="col-md-2">
            <button class="btn btn-primary w-100" @click="loadReservations">
              <i class="fas fa-search me-1"></i>查询
            </button>
          </div>
          <div class="col-md-2">
            <button class="btn btn-secondary w-100" @click="resetFilter">
              <i class="fas fa-redo me-1"></i>重置
            </button>
          </div>
        </div>

        <!-- 预约列表 -->
        <div class="table-responsive">
          <table class="table table-hover">
            <thead class="table-light">
              <tr>
                <th>预约ID</th>
                <th>报告类型</th>
                <th>客户</th>
                <th>证件号</th>
                <th>交易金额</th>
                <th>状态</th>
                <th>创建时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="loading">
                <td colspan="8" class="text-center py-5">
                  <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">加载中...</span>
                  </div>
                </td>
              </tr>
              <tr v-else-if="reservations.length === 0">
                <td colspan="8" class="text-center text-muted py-5">
                  暂无预约记录
                </td>
              </tr>
              <tr v-else v-for="item in reservations" :key="item.id">
                <td>{{ item.reservation_id }}</td>
                <td>
                  <span class="badge bg-info">{{ item.report_type }}</span>
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
                    <!-- 查看详情按钮 - 总是显示 -->
                    <button
                      class="btn btn-primary btn-sm"
                      @click="viewDetail(item)"
                      style="min-width: 90px;"
                    >
                      <i class="fas fa-eye me-1"></i>查看详情
                    </button>

                    <!-- 审核按钮 - 仅待审核状态显示 -->
                    <button
                      v-if="item.status === 'pending'"
                      class="btn btn-success btn-sm"
                      @click="openAuditModal(item, 'approve')"
                      style="min-width: 90px;"
                    >
                      <i class="fas fa-check me-1"></i>审核通过
                    </button>

                    <button
                      v-if="item.status === 'pending'"
                      class="btn btn-danger btn-sm"
                      @click="openAuditModal(item, 'reject')"
                      style="min-width: 90px;"
                    >
                      <i class="fas fa-times me-1"></i>审核拒绝
                    </button>

                    <!-- PDF按钮 - 已通过状态显示 -->
                    <button
                      v-if="item.status === 'approved'"
                      class="btn btn-info btn-sm"
                      @click="viewPDF(item)"
                      style="min-width: 90px;"
                    >
                      <i class="fas fa-file-pdf me-1"></i>查看PDF
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 分页 -->
        <nav v-if="total > pageSize">
          <ul class="pagination justify-content-end mb-0">
            <li class="page-item" :class="{ disabled: currentPage === 1 }">
              <a class="page-link" @click="changePage(currentPage - 1)">上一页</a>
            </li>
            <li class="page-item active">
              <span class="page-link">{{ currentPage }} / {{ totalPages }}</span>
            </li>
            <li class="page-item" :class="{ disabled: currentPage === totalPages }">
              <a class="page-link" @click="changePage(currentPage + 1)">下一页</a>
            </li>
          </ul>
        </nav>
      </div>
    </div>

    <!-- 详情模态框 -->
    <div class="modal fade" id="detailModal" tabindex="-1" ref="detailModalRef">
      <div class="modal-dialog modal-lg">
        <div class="modal-content" v-if="currentReservation">
          <div class="modal-header bg-light">
            <h5 class="modal-title">
              <i class="fas fa-clipboard-list me-2"></i>预约详情
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body">
            <!-- 基本信息 -->
            <h6 class="border-bottom pb-2 mb-3">
              <i class="fas fa-info-circle me-1 text-primary"></i>基本信息
            </h6>
            <div class="row mb-3">
              <div class="col-md-6 mb-2">
                <label class="text-muted small">预约编号</label>
                <div class="fw-bold">{{ currentReservation.reservation_no || currentReservation.id }}</div>
              </div>
              <div class="col-md-6 mb-2">
                <label class="text-muted small">报告类型</label>
                <div>
                  <span class="badge bg-info">{{ currentReservation.report_type }}</span>
                </div>
              </div>
              <div class="col-md-6 mb-2">
                <label class="text-muted small">创建时间</label>
                <div>{{ formatDateTime(currentReservation.created_at) }}</div>
              </div>
              <div class="col-md-6 mb-2">
                <label class="text-muted small">状态</label>
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
              <i class="fas fa-user me-1 text-primary"></i>客户信息
            </h6>
            <div class="row mb-3">
              <div class="col-md-6 mb-2">
                <label class="text-muted small">客户姓名</label>
                <div class="fw-bold">{{ currentReservation.customer_name }}</div>
              </div>
              <div class="col-md-6 mb-2">
                <label class="text-muted small">证件号码</label>
                <div>{{ currentReservation.customer_id }}</div>
              </div>
              <div class="col-md-6 mb-2">
                <label class="text-muted small">国家/地区</label>
                <div>{{ currentReservation.customer_country_code || '-' }}</div>
              </div>
            </div>

            <!-- 交易信息 -->
            <h6 class="border-bottom pb-2 mb-3">
              <i class="fas fa-money-bill-wave me-1 text-primary"></i>交易信息
            </h6>
            <div class="row mb-3">
              <div class="col-md-6 mb-2">
                <label class="text-muted small">交易金额（本币）</label>
                <div class="fw-bold fs-5 text-success">{{ formatAmount(currentReservation.local_amount) }} THB</div>
              </div>
              <div class="col-md-6 mb-2">
                <label class="text-muted small">交易币种</label>
                <div>{{ currentReservation.currency_id || '-' }}</div>
              </div>
              <div class="col-md-6 mb-2">
                <label class="text-muted small">交易方向</label>
                <div>
                  <span class="badge bg-secondary">{{ currentReservation.direction === 'buy' ? '买入' : '卖出' }}</span>
                </div>
              </div>
              <div class="col-md-6 mb-2">
                <label class="text-muted small">外币金额</label>
                <div>{{ formatAmount(currentReservation.amount) }}</div>
              </div>
            </div>

            <!-- 审核信息 -->
            <div v-if="currentReservation.status !== 'pending'">
              <h6 class="border-bottom pb-2 mb-3">
                <i class="fas fa-check-circle me-1 text-primary"></i>审核信息
              </h6>
              <div class="row mb-3">
                <div class="col-md-6 mb-2">
                  <label class="text-muted small">审核时间</label>
                  <div>{{ formatDateTime(currentReservation.audit_time) || '-' }}</div>
                </div>
                <div class="col-md-6 mb-2">
                  <label class="text-muted small">审核人</label>
                  <div>{{ currentReservation.auditor_id || '-' }}</div>
                </div>
                <div class="col-12 mb-2" v-if="currentReservation.rejection_reason">
                  <label class="text-muted small">拒绝原因</label>
                  <div class="alert alert-danger mb-0">{{ currentReservation.rejection_reason }}</div>
                </div>
                <div class="col-12 mb-2" v-if="currentReservation.remarks">
                  <label class="text-muted small">备注</label>
                  <div class="alert alert-info mb-0">{{ currentReservation.remarks }}</div>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
              <i class="fas fa-times me-1"></i>关闭
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
              {{ auditAction === 'approve' ? '审核通过' : '审核拒绝' }}
            </h5>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body">
            <!-- 显示预约基本信息 -->
            <div class="alert alert-light border">
              <div class="mb-2">
                <strong>预约编号：</strong>{{ auditingItem.reservation_no || auditingItem.id }}
              </div>
              <div class="mb-2">
                <strong>客户姓名：</strong>{{ auditingItem.customer_name }}
              </div>
              <div class="mb-2">
                <strong>交易金额：</strong>
                <span class="text-success fw-bold">{{ formatAmount(auditingItem.local_amount) }} THB</span>
              </div>
            </div>

            <!-- 拒绝时需要填写原因 -->
            <div v-if="auditAction === 'reject'" class="mb-3">
              <label class="form-label text-danger fw-bold">
                <i class="fas fa-exclamation-triangle me-1"></i>拒绝原因 <span class="text-danger">*</span>
              </label>
              <textarea
                class="form-control"
                v-model="auditForm.rejection_reason"
                rows="4"
                placeholder="请详细说明拒绝审核的原因..."
                required
              ></textarea>
              <div class="form-text">此信息将反馈给操作员</div>
            </div>

            <!-- 通过时可选填备注 -->
            <div class="mb-3">
              <label class="form-label">审核备注（可选）</label>
              <textarea
                class="form-control"
                v-model="auditForm.remarks"
                rows="3"
                placeholder="填写审核备注信息..."
              ></textarea>
            </div>

            <!-- 确认提示 -->
            <div class="alert" :class="auditAction === 'approve' ? 'alert-success' : 'alert-danger'">
              <i class="fas fa-info-circle me-1"></i>
              {{ auditAction === 'approve' ? '审核通过后，该预约将进入已通过状态，允许完成交易' : '审核拒绝后，该预约将被驳回，需重新提交' }}
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
              <i class="fas fa-times me-1"></i>取消
            </button>
            <button
              type="button"
              class="btn"
              :class="auditAction === 'approve' ? 'btn-success' : 'btn-danger'"
              @click="submitAudit"
              :disabled="auditAction === 'reject' && !auditForm.rejection_reason"
            >
              <i class="fas me-1" :class="auditAction === 'approve' ? 'fa-check' : 'fa-times'"></i>
              {{ auditAction === 'approve' ? '确认通过' : '确认拒绝' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { Modal } from 'bootstrap'
import api from '@/services/api'

export default {
  name: 'ReservationListSimple',
  setup() {
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

    const loadReservations = async () => {
      loading.value = true
      try {
        const params = {
          page: currentPage.value,
          page_size: pageSize.value,
          ...filter.value
        }
        
        const response = await api.get('amlo/reservations', { params })
        
        if (response.data.success) {
          reservations.value = response.data.data.items || []
          total.value = response.data.data.total || 0
        }
      } catch (error) {
        console.error('加载预约列表失败:', error)
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
        alert('请填写拒绝原因')
        return
      }

      try {
        const payload = {
          action: auditAction.value,
          rejection_reason: auditForm.value.rejection_reason || undefined,
          remarks: auditForm.value.remarks || undefined
        }

        const response = await api.post(
          `amlo/reservations/${auditingItem.value.id}/audit`,
          payload
        )

        if (response.data.success) {
          // 关闭模态框
          auditModal.hide()

          // 静默刷新列表，不显示弹窗
          await loadReservations()

          // 显示简洁的Toast通知（可选）
          showToast(auditAction.value === 'approve' ? '审核通过' : '审核已拒绝')
        } else {
          alert('审核失败: ' + (response.data.message || '未知错误'))
        }
      } catch (error) {
        console.error('审核失败:', error)
        alert('审核失败: ' + (error.response?.data?.message || error.message))
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
      return new Date(dt).toLocaleString('zh-CN')
    }
    
    const viewPDF = async (item) => {
      if (!item.id) {
        alert('无效的预约记录')
        return
      }
      
      try {
        // 查找该预约对应的AMLO报告
        const reportResponse = await api.get('amlo/reports', {
          params: {
            reservation_id: item.id
          }
        })

        if (reportResponse.data.success && reportResponse.data.data && reportResponse.data.data.length > 0) {
          const report = reportResponse.data.data[0]
          const pdfUrl = `amlo/reports/${report.id}/generate-pdf`
          window.open(pdfUrl, '_blank')
        } else {
          alert('该预约暂无关联的PDF报告\n\n可能原因：\n1. 预约尚未审核\n2. 尚未完成交易\n3. PDF尚未生成')
        }
      } catch (error) {
        console.error('打开PDF失败:', error)
        alert('打开PDF失败: ' + (error.response?.data?.message || error.message))
      }
    }

    const getStatusText = (status) => {
      const map = {
        'pending': '待审核',
        'approved': '已通过',
        'rejected': '已拒绝'
      }
      return map[status] || status
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
      filter,
      currentReservation,
      detailModalRef,
      auditingItem,
      auditAction,
      auditForm,
      auditModalRef,
      loadReservations,
      resetFilter,
      changePage,
      viewDetail,
      viewPDF,
      openAuditModal,
      submitAudit,
      showToast,
      formatAmount,
      formatDateTime,
      getStatusText
    }
  }
}
</script>

<style scoped>
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


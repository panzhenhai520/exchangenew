<template>
  <div class="modal fade" id="customerHistoryModal" tabindex="-1" ref="modalRef">
    <div class="modal-dialog modal-lg modal-dialog-scrollable">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">
            <font-awesome-icon :icon="['fas', 'history']" class="me-2" />
            {{ $t('compliance.customerHistory') }}
          </h5>
          <button type="button" class="btn-close" @click="closeModal"></button>
        </div>
        <div class="modal-body">
          <!-- 客户信息 -->
          <div class="card mb-3">
            <div class="card-body">
              <div class="row">
                <div class="col-md-6">
                  <small class="text-muted">{{ $t('compliance.customerId') }}:</small>
                  <div><strong>{{ customerId }}</strong></div>
                </div>
                <div class="col-md-6" v-if="historyData">
                  <small class="text-muted">{{ $t('compliance.customerName') }}:</small>
                  <div><strong>{{ historyData.customer_name || '-' }}</strong></div>
                </div>
              </div>
            </div>
          </div>

          <!-- 统计信息 -->
          <div v-if="historyData" class="row mb-3">
            <div class="col-md-4 col-6 mb-2">
              <div class="card text-center">
                <div class="card-body py-2">
                  <small class="text-muted">{{ $t('compliance.totalTransactions') }}</small>
                  <h4 class="mb-0 text-primary">{{ historyData.transaction_count || 0 }}</h4>
                </div>
              </div>
            </div>
            <div class="col-md-4 col-6 mb-2">
              <div class="card text-center">
                <div class="card-body py-2">
                  <small class="text-muted">{{ $t('compliance.cumulativeAmount') }}</small>
                  <h4 class="mb-0 text-success">{{ formatCurrency(historyData.cumulative_amount) }}</h4>
                </div>
              </div>
            </div>
            <div class="col-md-4 col-6 mb-2">
              <div class="card text-center">
                <div class="card-body py-2">
                  <small class="text-muted">{{ $t('compliance.lastTransactionDate') }}</small>
                  <h6 class="mb-0 text-info">{{ historyData.last_transaction_date || '-' }}</h6>
                </div>
              </div>
            </div>
          </div>

          <!-- 交易历史列表 -->
          <div class="card">
            <div class="card-header">
              <h6 class="mb-0">{{ $t('compliance.transactionHistory') }}</h6>
            </div>
            <div class="card-body p-0">
              <div v-if="loading" class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                  <span class="visually-hidden">{{ $t('common.loading') }}</span>
                </div>
              </div>

              <div v-else-if="!historyData || !historyData.transactions || historyData.transactions.length === 0" class="text-center py-4 text-muted">
                {{ $t('compliance.noTransactionHistory') }}
              </div>

              <div v-else class="table-responsive">
                <table class="table table-sm table-hover mb-0">
                  <thead class="table-light">
                    <tr>
                      <th width="50">#</th>
                      <th width="100">{{ $t('compliance.date') }}</th>
                      <th width="80">{{ $t('compliance.direction') }}</th>
                      <th width="80">{{ $t('compliance.currency') }}</th>
                      <th width="120" class="text-end">{{ $t('compliance.foreignAmount') }}</th>
                      <th width="120" class="text-end">{{ $t('compliance.localAmount') }}</th>
                      <th width="100">{{ $t('compliance.type') }}</th>
                      <th width="80">{{ $t('compliance.status') }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(transaction, index) in paginatedTransactions" :key="transaction.id">
                      <td>{{ (currentPage - 1) * pageSize + index + 1 }}</td>
                      <td>{{ formatDate(transaction.transaction_date) }}</td>
                      <td>
                        <span class="badge" :class="transaction.direction === 'buy' ? 'bg-success' : 'bg-primary'">
                          {{ transaction.direction === 'buy' ? $t('transaction.buy') : $t('transaction.sell') }}
                        </span>
                      </td>
                      <td>{{ transaction.currency_code }}</td>
                      <td class="text-end">{{ formatCurrency(transaction.amount) }}</td>
                      <td class="text-end">{{ formatCurrency(transaction.local_amount) }}</td>
                      <td>{{ transaction.transaction_type || '-' }}</td>
                      <td>
                        <span class="badge bg-info">{{ transaction.status || $t('compliance.completed') }}</span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <!-- 分页 -->
              <nav v-if="totalPages > 1" class="px-3 py-2" aria-label="Page navigation">
                <ul class="pagination pagination-sm justify-content-center mb-0">
                  <li class="page-item" :class="{ disabled: currentPage === 1 }">
                    <a class="page-link" href="#" @click.prevent="currentPage = Math.max(1, currentPage - 1)">
                      {{ $t('common.previous') }}
                    </a>
                  </li>
                  <li
                    v-for="page in displayPages"
                    :key="page"
                    class="page-item"
                    :class="{ active: currentPage === page }"
                  >
                    <a class="page-link" href="#" @click.prevent="currentPage = page">{{ page }}</a>
                  </li>
                  <li class="page-item" :class="{ disabled: currentPage === totalPages }">
                    <a class="page-link" href="#" @click.prevent="currentPage = Math.min(totalPages, currentPage + 1)">
                      {{ $t('common.next') }}
                    </a>
                  </li>
                </ul>
              </nav>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-primary" @click="closeModal">
            {{ $t('common.close') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { Modal } from 'bootstrap'
import repformService from '@/services/api/repformService'

export default {
  name: 'CustomerHistoryModal',
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    customerId: {
      type: String,
      required: true
    }
  },
  emits: ['update:visible'],
  setup(props, { emit }) {
    const modalRef = ref(null)
    let modalInstance = null

    const loading = ref(false)
    const historyData = ref(null)
    const currentPage = ref(1)
    const pageSize = ref(10)

    // 计算属性
    const totalPages = computed(() => {
      if (!historyData.value || !historyData.value.transactions) return 0
      return Math.ceil(historyData.value.transactions.length / pageSize.value)
    })

    const displayPages = computed(() => {
      const pages = []
      const maxDisplay = 5
      let start = Math.max(1, currentPage.value - Math.floor(maxDisplay / 2))
      let end = Math.min(totalPages.value, start + maxDisplay - 1)

      if (end - start < maxDisplay - 1) {
        start = Math.max(1, end - maxDisplay + 1)
      }

      for (let i = start; i <= end; i++) {
        pages.push(i)
      }
      return pages
    })

    const paginatedTransactions = computed(() => {
      if (!historyData.value || !historyData.value.transactions) return []
      const start = (currentPage.value - 1) * pageSize.value
      const end = start + pageSize.value
      return historyData.value.transactions.slice(start, end)
    })

    // 格式化日期
    const formatDate = (dateStr) => {
      if (!dateStr) return '-'
      return new Date(dateStr).toLocaleDateString()
    }

    // 格式化货币
    const formatCurrency = (value) => {
      if (!value) return '0.00'
      return Math.abs(parseFloat(value)).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      })
    }

    // 加载客户历史
    const loadHistory = async () => {
      if (!props.customerId) return

      loading.value = true
      try {
        const response = await repformService.getCustomerHistory(props.customerId, 365)

        if (response.data.success) {
          historyData.value = response.data.data || response.data
          currentPage.value = 1
        } else {
          console.error('加载客户历史失败:', response.data.message)
        }
      } catch (error) {
        console.error('Load customer history error:', error)
      } finally {
        loading.value = false
      }
    }

    // 打开模态框
    const openModal = () => {
      if (modalRef.value) {
        modalInstance = new Modal(modalRef.value)
        modalInstance.show()
        loadHistory()
      }
    }

    // 关闭模态框
    const closeModal = () => {
      if (modalInstance) {
        modalInstance.hide()
      }
      emit('update:visible', false)
    }

    // 监听visible变化
    watch(() => props.visible, (newValue) => {
      if (newValue) {
        nextTick(() => {
          openModal()
        })
      } else {
        if (modalInstance) {
          modalInstance.hide()
        }
      }
    })

    // 监听customerId变化
    watch(() => props.customerId, () => {
      if (props.visible && props.customerId) {
        loadHistory()
      }
    })

    onMounted(() => {
      if (props.visible) {
        openModal()
      }
    })

    return {
      modalRef,
      loading,
      historyData,
      currentPage,
      pageSize,
      totalPages,
      displayPages,
      paginatedTransactions,
      formatDate,
      formatCurrency,
      closeModal
    }
  }
}
</script>

<style scoped>
/* 响应式设计：手机端优化 */
@media (max-width: 768px) {
  .modal-dialog {
    margin: 0.5rem;
    max-width: calc(100% - 1rem);
  }

  .table {
    font-size: 0.75rem;
  }

  .card-body .row > div {
    margin-bottom: 0.5rem;
  }
}
</style>

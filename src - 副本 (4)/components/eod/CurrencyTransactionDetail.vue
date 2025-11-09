<template>
  <div class="currency-detail-panel">
    <div v-if="loading" class="text-center py-3">
      <span class="spinner-border spinner-border-sm me-2" role="status"></span>
      {{ $t('eod.step3.loading_transactions') }}
    </div>
    <div v-else-if="error" class="alert alert-danger m-3">
      {{ error }}
    </div>
    <div v-else-if="data" class="p-3">
      <div class="row mb-3">
        <div class="col-md-6">
          <h6>{{ $t('eod.step3.calculation_summary') }}</h6>
                                      <div class="row">
                              <div class="col-6">
                                <small class="text-muted">{{ $t('eod.step3.opening_balance') }}:</small>
                                <div class="fw-bold">{{ formatAmount(data.opening_balance) }}</div>
                              </div>
                              <div class="col-6">
                                <small class="text-muted">{{ $t('eod.step3.daily_change') }}:</small>
                                <div class="fw-bold" :class="getAdjustmentClass(data.daily_change)">
                                  {{ formatAdjustment(data.daily_change) }}
                                </div>
                              </div>
                            </div>
        </div>
        <div class="col-md-6">
          <div class="d-flex align-items-center justify-content-between">
            <div>
              <small class="text-muted">{{ $t('eod.step3.selected_total') }}:</small>
              <div class="fw-bold" :class="getAdjustmentClass(selectedTotal)">
                {{ formatAdjustment(selectedTotal) }}
              </div>
            </div>
            <div class="btn-group btn-group-sm">
              <button 
                class="btn btn-outline-secondary"
                @click="selectAll"
              >
                {{ $t('eod.step3.select_all') }}
              </button>
              <button 
                class="btn btn-outline-secondary"
                @click="deselectAll"
              >
                {{ $t('eod.step3.deselect_all') }}
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <div class="table-responsive">
        <table class="table table-sm table-bordered">
          <thead class="table-light">
            <tr>
              <th style="width: 40px;">
                <input 
                  type="checkbox" 
                  :checked="isAllSelected"
                  @change="toggleSelectAll"
                  class="form-check-input"
                />
              </th>
              <th>{{ $t('eod.step3.transaction_time') }}</th>
              <th>{{ $t('eod.step3.transaction_type') }}</th>
              <th>{{ $t('eod.step3.column_description') }}</th>
              <th class="text-end">{{ $t('eod.step3.amount') }}</th>
              <th class="text-end">{{ $t('eod.step3.rate') }}</th>
              <th class="text-end">{{ $t('eod.step3.local_amount') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="tx in data.transactions" :key="tx.id">
              <td>
                <input 
                  type="checkbox" 
                  :checked="selectedTransactions.includes(tx.id)"
                  @change="toggleTransactionSelection(tx.id, tx.amount)"
                  class="form-check-input"
                />
              </td>
              <td>{{ formatDateTime(tx.created_at) }}</td>
              <td>
                <span class="badge" :class="getTransactionTypeClass(tx.type)">
                  {{ getTransactionTypeLabel(tx.type) }}
                </span>
              </td>
              <td>{{ tx.description }}</td>
              <td class="text-end">{{ formatAmount(tx.foreign_amount) }}</td>
              <td class="text-end">{{ formatRate(tx.rate) }}</td>
              <td class="text-end" :class="getAdjustmentClass(tx.amount)">
                {{ formatAdjustment(tx.amount) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'

export default {
  name: 'CurrencyTransactionDetail',
  props: {
    currencyCode: {
      type: String,
      required: true
    },
    eodId: {
      type: Number,
      required: true
    },
    data: {
      type: Object,
      default: null
    },
    loading: {
      type: Boolean,
      default: false
    },
    error: {
      type: String,
      default: null
    }
  },
  emits: ['update:selectedTransactions', 'update:selectedTotal'],
  setup(props, { emit }) {
    const { t } = useI18n()
    
    const selectedTransactions = ref([])
    
    const selectedTotal = computed(() => {
      if (!props.data?.transactions) return 0
      return props.data.transactions
        .filter(tx => selectedTransactions.value.includes(tx.id))
        .reduce((sum, tx) => sum + tx.amount, 0)
    })
    
    const isAllSelected = computed(() => {
      if (!props.data?.transactions?.length) return false
      return props.data.transactions.every(tx => selectedTransactions.value.includes(tx.id))
    })
    
    // 监听选中状态变化，向父组件发送更新
    watch(selectedTransactions, (newVal) => {
      emit('update:selectedTransactions', newVal)
    }, { deep: true })
    
    watch(selectedTotal, (newVal) => {
      emit('update:selectedTotal', newVal)
    })
    
    const selectAll = () => {
      if (props.data?.transactions) {
        selectedTransactions.value = props.data.transactions.map(tx => tx.id)
      }
    }
    
    const deselectAll = () => {
      selectedTransactions.value = []
    }
    
    const toggleSelectAll = () => {
      if (isAllSelected.value) {
        deselectAll()
      } else {
        selectAll()
      }
    }
    
    const toggleTransactionSelection = (txId, amount) => {
      const index = selectedTransactions.value.indexOf(txId)
      if (index > -1) {
        selectedTransactions.value.splice(index, 1)
      } else {
        selectedTransactions.value.push(txId)
      }
    }
    
    const formatAmount = (amount) => {
      return new Intl.NumberFormat('zh-CN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(amount || 0)
    }
    
    const formatAdjustment = (amount) => {
      if (!amount) return '0.00'
      const sign = amount > 0 ? '+' : ''
      return `${sign}${formatAmount(amount)}`
    }
    
    const formatRate = (rate) => {
      return new Intl.NumberFormat('zh-CN', {
        minimumFractionDigits: 4,
        maximumFractionDigits: 4
      }).format(rate || 0)
    }
    
    const formatDateTime = (dateTime) => {
      if (!dateTime) return ''
      const date = new Date(dateTime)
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    }
    
    const getAdjustmentClass = (amount) => {
      if (!amount) return ''
      return amount > 0 ? 'text-success' : 'text-danger'
    }
    
    const getTransactionTypeClass = (type) => {
      const typeClasses = {
        'buy': 'bg-primary',
        'sell': 'bg-success',
        'adjust_balance': 'bg-warning',
        'reversal': 'bg-danger',
        'initial_balance': 'bg-info',
        'cash_out': 'bg-secondary'
      }
      return typeClasses[type] || 'bg-secondary'
    }
    
    const getTransactionTypeLabel = (type) => {
      const typeLabels = {
        'buy': t('common.buy'),
        'sell': t('common.sell'),
        'adjust_balance': t('common.adjustment'),
        'reversal': t('common.reversal'),
        'initial_balance': t('eod.step3.initial_balance'),
        'cash_out': t('common.cash_out')
      }
      return typeLabels[type] || type
    }
    
    return {
      selectedTransactions,
      selectedTotal,
      isAllSelected,
      selectAll,
      deselectAll,
      toggleSelectAll,
      toggleTransactionSelection,
      formatAmount,
      formatAdjustment,
      formatRate,
      formatDateTime,
      getAdjustmentClass,
      getTransactionTypeClass,
      getTransactionTypeLabel
    }
  }
}
</script>

<style scoped>
.currency-detail-panel {
  background-color: #f8f9fa;
  border-top: 1px solid #dee2e6;
}

.table-sm th,
.table-sm td {
  padding: 0.5rem;
  font-size: 0.875rem;
}

.badge {
  font-size: 0.75rem;
}
</style> 
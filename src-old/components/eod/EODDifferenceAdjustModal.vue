<template>
  <div class="modal fade" id="eodDifferenceAdjustModal" tabindex="-1" aria-labelledby="eodDifferenceAdjustModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-lg">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="eodDifferenceAdjustModalLabel">
            <font-awesome-icon :icon="['fas', 'balance-scale']" class="me-2" />
            {{ $t('eod.difference_adjust.title') }}
          </h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <div class="alert alert-info">
            <h6 class="alert-heading">
              <font-awesome-icon :icon="['fas', 'info-circle']" class="me-2" />
              {{ $t('eod.difference_adjust.instructions_title') }}
            </h6>
            <p class="mb-0">{{ $t('eod.difference_adjust.instructions_text') }}</p>
          </div>

          <div class="table-responsive">
            <table class="table table-striped table-hover">
              <thead class="table-dark-custom">
                <tr>
                  <th>{{ $t('eod.difference_adjust.currency') }}</th>
                  <th class="text-end">{{ $t('eod.difference_adjust.theoretical_balance') }}</th>
                  <th class="text-end">{{ $t('eod.difference_adjust.actual_balance') }}</th>
                  <th class="text-end">{{ $t('eod.difference_adjust.difference') }}</th>
                  <th class="text-end adjust-amount-col">{{ $t('eod.difference_adjust.adjust_amount') }}</th>
                  <th>{{ $t('eod.difference_adjust.adjust_reason') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in differenceItems" :key="item.currency_id">
                  <td>
                    <div class="d-flex align-items-center">
                      <CurrencyFlag :code="item.currency_code" :custom-filename="item.custom_flag_filename" class="me-2" />
                      <div>
                        <strong>{{ item.currency_code }}</strong>
                        <span class="text-muted small ms-2">{{ getCurrencyDisplayName(item) }}</span>
                      </div>
                    </div>
                  </td>
                  <td class="text-end">{{ formatAmount(item.theoretical_balance) }}</td>
                  <td class="text-end">{{ formatAmount(item.actual_balance) }}</td>
                  <td class="text-end" :class="getDifferenceClass(item.difference)">
                    {{ formatDifference(item.difference) }}
                  </td>
                  <td class="text-end adjust-amount-col">
                    <input 
                      type="number" 
                      class="form-control form-control-sm text-end"
                      v-model="item.adjust_amount"
                      :placeholder="formatAmount(item.difference)"
                      step="0.01"
                    />
                  </td>
                  <td>
                    <input 
                      type="text" 
                      class="form-control form-control-sm"
                      v-model="item.adjust_reason"
                      :placeholder="$t('eod.difference_adjust.default_reason')"
                    />
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="alert alert-warning mt-3">
            <h6 class="alert-heading">
              <font-awesome-icon :icon="['fas', 'exclamation-triangle']" class="me-2" />
              {{ $t('eod.difference_adjust.notes_title') }}
            </h6>
            <ul class="mb-0">
              <li>{{ $t('eod.difference_adjust.note_1') }}</li>
              <li>{{ $t('eod.difference_adjust.note_2') }}</li>
              <li>{{ $t('eod.difference_adjust.note_3') }}</li>
              <li>{{ $t('eod.difference_adjust.note_4') }}</li>
            </ul>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
            <font-awesome-icon :icon="['fas', 'times']" class="me-1" />
            {{ $t('common.cancel') }}
          </button>
          <button 
            type="button" 
            class="btn btn-primary"
            @click="confirmAdjust"
            :disabled="isAdjusting"
          >
            <span v-if="isAdjusting">
              <span class="spinner-border spinner-border-sm me-2" role="status"></span>
              {{ $t('eod.difference_adjust.adjusting') }}
            </span>
            <span v-else>
              <font-awesome-icon :icon="['fas', 'check']" class="me-1" />
              {{ $t('eod.difference_adjust.confirm_adjust') }}
            </span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import CurrencyFlag from '../CurrencyFlag.vue'
import { eodAPI } from '../../api/eod'
import { getCurrencyName } from '../../utils/currencyI18nHelper'

export default {
  name: 'EODDifferenceAdjustModal',
  components: {
    CurrencyFlag
  },
  props: {
    eodId: {
      type: [Number, String],
      required: true
    },
    verificationResults: {
      type: Array,
      required: true
    }
  },
  emits: ['adjust-completed', 'error'],
  setup(props, { emit }) {
    const { t } = useI18n()
    const isAdjusting = ref(false)
    
    // 处理差额项目数据
    const differenceItems = ref([])
    
    // 初始化差额项目
    const initDifferenceItems = () => {
      differenceItems.value = props.verificationResults
        .filter(item => !item.is_match) // 只处理有差异的币种
        .map(item => ({
          ...item,
          adjust_amount: item.difference, // 默认调节金额为差异值
          adjust_reason: t('eod.difference_adjust.default_reason') // 使用翻译的默认调节原因
        }))
    }
    
    // 计算属性
    const hasValidAdjustments = computed(() => {
      return differenceItems.value.every(item => 
        item.adjust_amount !== null && 
        item.adjust_amount !== undefined && 
        item.adjust_amount !== '' &&
        item.adjust_reason && 
        item.adjust_reason.trim() !== ''
      )
    })
    
    // 方法
    const formatAmount = (amount) => {
      if (amount === null || amount === undefined || isNaN(amount)) {
        return '0.00'
      }
      return new Intl.NumberFormat('zh-CN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(amount)
    }
    
    const formatDifference = (difference) => {
      if (difference === null || difference === undefined || isNaN(difference)) {
        return '0.00'
      }
      if (difference === 0) return '0.00'
      const formatted = formatAmount(Math.abs(difference))
      return difference > 0 ? `+${formatted}` : `-${formatted}`
    }
    
    const getDifferenceClass = (difference) => {
      if (difference === 0) return 'text-success'
      if (Math.abs(difference) < 0.01) return 'text-warning'
      return 'text-danger'
    }
    
    // 获取翻译后的币种名称
    const getTranslatedCurrencyName = (currencyCode) => {
      return getCurrencyName(currencyCode)
    }
    
    const confirmAdjust = async () => {
      if (!hasValidAdjustments.value) {
        emit('error', t('eod.difference_adjust.incomplete_info'))
        return
      }
      
      try {
        isAdjusting.value = true
        
        // 准备调节数据
        const adjustData = differenceItems.value.map(item => ({
          currency_id: item.currency_id,
          adjust_amount: parseFloat(item.adjust_amount),
          adjust_reason: item.adjust_reason.trim()
        }))
        
        // 调用差额调节API
        const result = await eodAPI.adjustEODDifference(props.eodId, adjustData)
        
        if (result.success) {
                  // 关闭模态框
        const modal = document.getElementById('eodDifferenceAdjustModal')
        if (modal) {
          const bootstrapModal = window.bootstrap?.Modal?.getInstance(modal)
          if (bootstrapModal) {
            bootstrapModal.hide()
          }
        }
          
          // 通知父组件调节完成
          emit('adjust-completed', result)
        } else {
          emit('error', result.message || t('eod.difference_adjust.adjustment_failed'))
        }
      } catch (error) {
        console.error('差额调节失败:', error)
        emit('error', error.response?.data?.message || error.message || t('eod.difference_adjust.adjustment_failed'))
      } finally {
        isAdjusting.value = false
      }
    }
    
    // 获取币种显示名称，支持自定义币种
    const getCurrencyDisplayName = (item) => {
      if (!item) return ''
      
      // 检查是否是自定义币种（有custom_flag_filename）
      if (item.custom_flag_filename) {
        // console.log(`[自定义币种] ${item.currency_code} 使用数据库名称: ${item.currency_name}`)
        return item.currency_name || item.currency_code
      }
      
      // 使用翻译
      return getTranslatedCurrencyName(item.currency_code)
    }
    
    // 初始化
    initDifferenceItems()
    
    return {
      isAdjusting,
      differenceItems,
      hasValidAdjustments,
      formatAmount,
      formatDifference,
      getDifferenceClass,
      getTranslatedCurrencyName,
      getCurrencyDisplayName,
      confirmAdjust
    }
  }
}
</script>

<style scoped>
.modal-lg {
  max-width: 1000px;
}

/* 自定义黑色表头样式 */
.table-dark-custom {
  background-color: #212529 !important;
  color: #ffffff !important;
}

.table-dark-custom th {
  background-color: #212529 !important;
  border-color: #32383e !important;
  color: #ffffff !important;
  font-weight: 600;
  border-top: none;
}

.table-dark-custom th,
.table-dark-custom td {
  border-color: #32383e !important;
}

/* 调节金额列宽度限制 */
.adjust-amount-col {
  width: 120px;
  max-width: 120px;
}

.adjust-amount-col input {
  width: 100px;
  max-width: 100px;
}

/* 表格紧凑布局 */
.table {
  font-size: 0.9rem;
}

.table td {
  padding: 0.5rem 0.25rem;
  vertical-align: middle;
}

.table th {
  padding: 0.5rem 0.25rem;
  font-weight: 600;
}

.form-control-sm {
  font-size: 0.875rem;
  padding: 0.25rem 0.5rem;
}

.alert ul {
  padding-left: 1.2rem;
}

.alert li {
  margin-bottom: 0.25rem;
}

/* 模态框紧凑布局 */
.modal-body {
  padding: 1rem;
}

.alert {
  padding: 0.75rem;
  margin-bottom: 1rem;
}
</style> 
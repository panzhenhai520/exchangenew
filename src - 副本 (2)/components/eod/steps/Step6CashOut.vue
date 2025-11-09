<template>
  <div class="step-content">
    <div class="step-header mb-4">
      <h4>{{ $t("eod.step6.title") }}</h4>
      <p class="text-muted">{{ $t("eod.step6.description") }}</p>
    </div>

    <div v-if="!balanceData" class="text-center py-4">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">{{ $t("common.loading") }}</span>
      </div>
      <p class="mt-2">{{ $t("eod.step6.loading_balance") }}</p>
    </div>

    <div v-else>
      <!-- 交款模式选择 -->
      <div class="card mb-4">
        <div class="card-header">
          <h6 class="mb-0">{{ $t("eod.step6.cash_out_mode") }}</h6>
        </div>
        <div class="card-body">
          <div class="row">
            <div class="col-md-4">
              <div class="form-check">
                <input
                  class="form-check-input"
                  type="radio"
                  id="mode-all"
                  value="all"
                  v-model="cashOutMode"
                  @change="updateCashOutMode"
                />
                <label class="form-check-label" for="mode-all">
                  <strong>{{ $t("eod.step6.mode_all") }}</strong>
                  <br>
                  <small class="text-muted">{{ $t("eod.step6.mode_all_desc") }}</small>
                </label>
              </div>
            </div>
            <div class="col-md-4">
              <div class="form-check">
                <input
                  class="form-check-input"
                  type="radio"
                  id="mode-zero"
                  value="zero"
                  v-model="cashOutMode"
                  @change="updateCashOutMode"
                />
                <label class="form-check-label" for="mode-zero">
                  <strong>{{ $t("eod.step6.mode_zero") }}</strong>
                  <br>
                  <small class="text-muted">{{ $t("eod.step6.mode_zero_desc") }}</small>
                </label>
              </div>
            </div>
            <div class="col-md-4">
              <div class="form-check">
                <input
                  class="form-check-input"
                  type="radio"
                  id="mode-custom"
                  value="custom"
                  v-model="cashOutMode"
                  @change="updateCashOutMode"
                />
                <label class="form-check-label" for="mode-custom">
                  <strong>{{ $t("eod.step6.mode_custom") }}</strong>
                  <br>
                  <small class="text-muted">{{ $t("eod.step6.mode_custom_desc") }}</small>
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- {{ $t("eod.step6.cash_out_details") }}表格 -->
      <div class="card">
        <div class="card-header d-flex justify-content-between align-items-center">
          <h6 class="mb-0">{{ $t("eod.step6.cash_out_summary") }}</h6>
          <div>
            <span class="badge bg-info me-2">{{ $t("eod.step6.total_currencies") }} {{ totalCurrencies }} {{ $t("eod.step6.currencies_unit") }}</span>
            <span class="badge bg-warning">{{ $t("eod.step6.cash_out_currencies") }} {{ cashOutCurrencies }} {{ $t("eod.step6.currencies_unit") }}</span>
          </div>
        </div>
        <div class="card-body p-0">
          <div class="table-responsive">
            <table class="table table-striped table-hover mb-0">
              <thead class="table-light">
                <tr>
                  <th class="text-dark fw-bold">{{ $t("common.currency") }}</th>
                  <th class="text-end text-dark fw-bold">{{ $t("common.current_balance") }}</th>
                  <th class="text-end text-dark fw-bold">{{ $t("eod.step6.cash_out_status") }}{{ $t("common.amount") }}</th>
                  <th class="text-end text-dark fw-bold">{{ $t("common.remaining_balance") }}</th>
                  <th class="text-center text-dark fw-bold">{{ $t("common.status") }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in cashOutItems" :key="item.currency_id">
                  <td>
                    <div class="d-flex align-items-center">
                      <CurrencyFlag :code="item.currency_code" :custom-filename="item.custom_flag_filename" class="me-2" />
                      <div class="d-flex align-items-center">
                        <strong class="me-2">{{ item.currency_code }}</strong>
                        <small class="text-muted">{{ getCurrencyDisplayName(item) }}</small>
                      </div>
                    </div>
                  </td>
                  <td class="text-end">
                    <span class="fw-bold" :class="getBalanceClass(item.current_balance)">
                      {{ formatAmount(item.current_balance) }}
                    </span>
                  </td>
                  <td class="text-end">
                    <div class="input-group input-group-sm">
                      <input
                        type="number"
                        class="form-control text-end"
                        :value="item.cash_out_amount"
                        @input="updateCashOutAmount(item.currency_id, $event.target.value)"
                        :disabled="cashOutMode !== 'custom'"
                        :max="item.current_balance"
                        min="0"
                        step="0.01"
                        :class="{
                          'is-invalid': item.cash_out_amount > item.current_balance,
                          'is-valid': item.cash_out_amount > 0 && item.cash_out_amount <= item.current_balance
                        }"
                      />
                    </div>
                    <div v-if="item.cash_out_amount > item.current_balance" class="invalid-feedback d-block">
                      <small>{{ $t("eod.step6.amount_exceed_error") }}</small>
                    </div>
                  </td>
                  <td class="text-end">
                    <span class="fw-bold" :class="getBalanceClass(item.remaining_balance)">
                      {{ formatAmount(item.remaining_balance) }}
                    </span>
                  </td>
                  <td>
                    <span v-if="item.cash_out_amount > 0" class="badge bg-success">
                      <font-awesome-icon :icon="['fas', 'check']" class="me-1" />
                      {{ $t("eod.step6.cash_out_status") }}
                    </span>
                    <span v-else class="badge bg-secondary">
                      <font-awesome-icon :icon="['fas', 'minus']" class="me-1" />
                      {{ $t("eod.step6.keep_status") }}
                    </span>
                  </td>
                  <td>
                    <div class="btn-group btn-group-sm" role="group">
                      <button
                        type="button"
                        class="btn btn-outline-primary"
                        @click="setCashOutAmount(item.currency_id, item.current_balance)"
                        :disabled="cashOutMode !== 'custom' || item.current_balance <= 0"
                        :title="`${t('common.all')}${t('eod.step6.cash_out_status')}`"
                      >
                        <font-awesome-icon :icon="['fas', 'coins']" />
                      </button>
                      <button
                        type="button"
                        class="btn btn-outline-secondary"
                        @click="setCashOutAmount(item.currency_id, 0)"
                        :disabled="cashOutMode !== 'custom'"
                        :title="t('eod.step6.clear_amount')"
                      >
                        <font-awesome-icon :icon="['fas', 'times']" />
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- 交款汇总 -->
      <div class="row mt-4">
        <div class="col-md-6">
          <div class="card bg-light">
            <div class="card-body">
              <h6 class="card-title">
                <font-awesome-icon :icon="['fas', 'calculator']" class="me-2 text-primary" />
                {{ $t("eod.step6.cash_out_summary") }}
              </h6>
              <div class="row">
                <div class="col-6">
                  <p class="mb-1"><strong>{{ $t("eod.step6.cash_out_currencies") }}</strong></p>
                  <p class="mb-1"><strong>{{ $t("eod.step6.keep_currencies") }}</strong></p>
                  <p class="mb-0"><strong>{{ $t("eod.step6.total_currencies") }}</strong></p>
                </div>
                <div class="col-6 text-end">
                  <p class="mb-1">{{ cashOutCurrencies }} {{ $t("eod.step6.currencies_unit") }}</p>
                  <p class="mb-1">{{ remainingCurrencies }} {{ $t("eod.step6.currencies_unit") }}</p>
                  <p class="mb-0">{{ totalCurrencies }} {{ $t("eod.step6.currencies_unit") }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="col-md-6">
          <div class="card bg-light">
            <div class="card-body">
              <h6 class="card-title">
                <font-awesome-icon :icon="['fas', 'exclamation-triangle']" class="me-2 text-warning" />
                {{ $t("eod.step6.important_tips") }}
              </h6>
              <ul class="mb-0 small">
                <li>{{ $t("eod.step6.tip_generate_record") }}</li>
                <li>{{ $t("eod.step6.tip_update_balance") }}</li>
                <li>{{ $t("eod.step6.tip_remaining_balance") }}</li>
                <li>{{ $t("eod.step6.tip_unlock_business") }}</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- 收款人信息 -->
      <div class="row mt-4">
        <div class="col-md-6">
          <div class="card">
            <div class="card-header">
              <h6 class="mb-0">
                <font-awesome-icon :icon="['fas', 'user-check']" class="me-2 text-primary" />
                {{ $t("eod.step6.receiver_info") }}
              </h6>
            </div>
            <div class="card-body">
              <div class="form-group">
                <label for="cashReceiver" class="form-label">{{ $t("eod.step6.receiver_name") }} <span class="text-danger">*</span></label>
                <input
                  id="cashReceiver"
                  type="text"
                  class="form-control"
                  v-model="cashReceiverName"
                  :placeholder="t('eod.step6.receiver_name_placeholder')"
                  :disabled="loading || isProcessing"
                  required
                />
                <div v-if="!cashReceiverName" class="form-text text-muted">
                  {{ $t("eod.step6.receiver_name_help") }}
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="col-md-6">
          <div class="card">
            <div class="card-header">
              <h6 class="mb-0">
                <font-awesome-icon :icon="['fas', 'clipboard-list']" class="me-2 text-secondary" />
                {{ $t("eod.step6.remark_info") }}
              </h6>
            </div>
            <div class="card-body">
              <div class="form-group">
                <label for="cashOutRemark" class="form-label">{{ $t("eod.step6.remark_label") }}</label>
                <textarea
                  id="cashOutRemark"
                  class="form-control"
                  v-model="cashOutRemark"
                  rows="3"
                  :placeholder="t('eod.step6.remark_placeholder')"
                  :disabled="loading || isProcessing"
                ></textarea>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="d-flex justify-content-end mt-4">
        <button 
          class="btn btn-outline-secondary me-2"
          @click="resetCashOut"
          :disabled="loading || isProcessing"
        >
          <font-awesome-icon :icon="['fas', 'undo']" class="me-1" />
          {{ $t("eod.step6.reset") }}
        </button>
        <button 
          class="btn btn-success"
          @click="processCashOut"
          :disabled="loading || isProcessing || !isValidCashOut || !cashReceiverName || !cashReceiverName.trim()"
        >
          <span v-if="isProcessing">
            <span class="spinner-border spinner-border-sm me-2" role="status"></span>
            {{ $t("eod.step6.processing_cash_out") }}
          </span>
          <span v-else>
            <font-awesome-icon :icon="['fas', 'hand-holding-usd']" class="me-1" />
            {{ $t("eod.step6.confirm_cash_out") }}
          </span>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { eodAPI } from '../../../api/eod'
import CurrencyFlag from '../../CurrencyFlag.vue'
import { getCurrencyName } from '@/utils/currencyTranslator'

export default {
  name: 'Step6CashOut',
  components: {
    CurrencyFlag
  },
  emits: ['next', 'error'],
  props: {
    eodId: {
      type: [Number, String],
      required: true
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  setup(props, { emit }) {
    const { t, i18n } = useI18n()

    // 响应式数据
    const balanceData = ref(null)
    const cashOutItems = ref([])
    const cashOutMode = ref('all')
    const isProcessing = ref(false)
    const cashReceiverName = ref('')
    const cashOutRemark = ref('')
    
    // 计算属性
    const totalCurrencies = computed(() => cashOutItems.value.length)
    
    const cashOutCurrencies = computed(() => {
      return cashOutItems.value.filter(item => item.cash_out_amount > 0).length
    })
    
    const remainingCurrencies = computed(() => {
      return cashOutItems.value.filter(item => item.remaining_balance > 0).length
    })
    
    const isValidCashOut = computed(() => {
      return cashOutItems.value.every(item => 
        item.cash_out_amount >= 0 && 
        item.cash_out_amount <= item.current_balance
      )
    })
    
    // 方法
    const loadBalanceData = async () => {
      try {
        const result = await eodAPI.extractBalance(props.eodId)
        
        if (result.success && result.balances) {
          balanceData.value = result
          initializeCashOutItems()
        } else {
          emit('error', t('eod.step6.get_balance_data_failed'))
        }
      } catch (error) {
        console.error('Get balance data failed:', error)
        emit('error', error.response?.data?.message || error.message || t('eod.step6.get_balance_data_failed'))
      }
    }
    
    const initializeCashOutItems = () => {
      cashOutItems.value = balanceData.value.balances.map(balance => ({
        currency_id: balance.currency_id,
        currency_code: balance.currency_code,
        currency_name: balance.currency_name,
        current_balance: balance.current_balance,
        cash_out_amount: balance.current_balance, // 默认全部交款
        remaining_balance: 0
      }))
    }
    
    const updateCashOutMode = () => {
      switch (cashOutMode.value) {
        case 'all':
          // 全部交清
          cashOutItems.value.forEach(item => {
            item.cash_out_amount = item.current_balance
            item.remaining_balance = 0
          })
          break
        case 'zero':
          // 零交款
          cashOutItems.value.forEach(item => {
            item.cash_out_amount = 0
            item.remaining_balance = item.current_balance
          })
          break
        case 'custom':
          // 自定义模式，保持当前值
          break
      }
    }
    
    const updateCashOutAmount = (currencyId, value) => {
      const amount = parseFloat(value) || 0
      const item = cashOutItems.value.find(item => item.currency_id === currencyId)
      if (item) {
        item.cash_out_amount = amount
        item.remaining_balance = item.current_balance - amount
        
        // 如果手动修改了金额，切换到自定义模式
        if (cashOutMode.value !== 'custom') {
          cashOutMode.value = 'custom'
        }
      }
    }
    
    const setCashOutAmount = (currencyId, amount) => {
      const item = cashOutItems.value.find(item => item.currency_id === currencyId)
      if (item) {
        item.cash_out_amount = amount
        item.remaining_balance = item.current_balance - amount
      }
    }
    
    const resetCashOut = () => {
      cashOutMode.value = 'all'
      updateCashOutMode()
    }
    
    const processCashOut = async () => {
      if (!isValidCashOut.value) {
        emit('error', t('eod.step6.amount_validation_error'))
        return
      }
      
      try {
        isProcessing.value = true
        
        // 准备交款数据
        const cashOutData = cashOutItems.value
          .filter(item => item.cash_out_amount > 0)
          .map(item => ({
            currency_id: item.currency_id,
            amount: item.cash_out_amount
          }))
        
        const result = await eodAPI.processCashOut(props.eodId, {
          cash_out_data: cashOutData,
          cash_receiver_name: cashReceiverName.value.trim(),
          cash_out_remark: cashOutRemark.value.trim()
        })
        
        if (result.success) {
          emit('next', {
            cash_out_records: result.cash_out_records,
            step: result.step || 7,
            step_status: result.step_status || 'processing',
            from_api_call: true
          })
        } else {
          emit('error', result.message || t('eod.step6.cash_out_process_failed'))
        }
      } catch (error) {
        console.error('交款处理失败:', error)
        emit('error', error.response?.data?.message || error.message || t('eod.step6.cash_out_process_failed'))
      } finally {
        isProcessing.value = false
      }
    }
    
    const getBalanceClass = (amount) => {
      if (amount > 0) return 'text-success'
      if (amount < 0) return 'text-danger'
      return 'text-muted'
    }
    
    const formatAmount = (amount) => {
      // 根据当前语言设置数字格式
      const localeMap = {
        'zh-CN': 'zh-CN',
        'zh': 'zh-CN',
        'en-US': 'en-US',
        'en': 'en-US',
        'th-TH': 'th-TH',
        'th': 'th-TH'
      }
      
      // 安全地获取当前语言，如果i18n未初始化则使用默认值
      let currentLocale = 'zh-CN'
      try {
        if (i18n && i18n.locale && i18n.locale.value) {
          currentLocale = i18n.locale.value
        } else if (i18n && i18n.global && i18n.global.locale && i18n.global.locale.value) {
          // 备用方案：尝试从global对象获取
          currentLocale = i18n.global.locale.value
        } else {
          // 从localStorage获取语言设置
          const storedLanguage = localStorage.getItem('language')
          if (storedLanguage && localeMap[storedLanguage]) {
            currentLocale = storedLanguage
          }
        }
      } catch (error) {
        console.warn('无法获取i18n locale，使用默认值:', error)
        // 从localStorage获取语言设置作为备用
        const storedLanguage = localStorage.getItem('language')
        if (storedLanguage && localeMap[storedLanguage]) {
          currentLocale = storedLanguage
        }
      }
      
      const locale = localeMap[currentLocale] || 'zh-CN'
      
      return new Intl.NumberFormat(locale, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(amount)
    }
    
    // 监听交款模式变化
    watch(cashOutMode, updateCashOutMode)
    
    // 获取币种显示名称，支持自定义币种
    const getCurrencyDisplayName = (item) => {
      if (!item) return ''
      
      // 检查是否是自定义币种（有custom_flag_filename）
      if (item.custom_flag_filename) {
        // console.log(`[自定义币种] ${item.currency_code} 使用数据库名称: ${item.currency_name}`)
        return item.currency_name || item.currency_code
      }
      
      // 使用翻译
      return getCurrencyName(item.currency_code)
    }
    
    // 生命周期
    onMounted(() => {
      if (props.eodId) {
        loadBalanceData()
      }
    })
    
    return {
      balanceData,
      cashOutItems,
      cashOutMode,
      isProcessing,
      cashReceiverName,
      cashOutRemark,
      totalCurrencies,
      cashOutCurrencies,
      remainingCurrencies,
      isValidCashOut,
      updateCashOutMode,
      updateCashOutAmount,
      setCashOutAmount,
      resetCashOut,
      processCashOut,
      getBalanceClass,
      t,
      formatAmount,
      getCurrencyName,
      getCurrencyDisplayName
    }
  }
}
</script>

<style scoped>
.step-content {
  padding: 1rem 0;
}

.step-header h4 {
  color: #495057;
  margin-bottom: 0.5rem;
}

.currency-flag {
  display: inline-block;
  width: 24px;
  height: 18px;
  background: linear-gradient(45deg, #007bff, #0056b3);
  border-radius: 2px;
  text-align: center;
  line-height: 18px;
  color: white;
  font-size: 10px;
  font-weight: bold;
}

.table th {
  border-top: none;
  font-weight: 600;
  font-size: 0.9rem;
  padding: 0.5rem 0.75rem;
}

.table td {
  vertical-align: middle;
  padding: 0.5rem 0.75rem;
}

.table tbody tr {
  height: 2.5rem;
}

.input-group-sm .form-control {
  font-size: 0.875rem;
}

.btn-group-sm > .btn {
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
}

.card.bg-light {
  border: 1px solid #e9ecef;
}

.badge {
  font-size: 0.75rem;
}

.form-check-label strong {
  color: #495057;
}

.invalid-feedback {
  font-size: 0.75rem;
}
</style> 

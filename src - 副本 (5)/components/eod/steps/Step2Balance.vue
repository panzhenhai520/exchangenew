<template>
  <div class="step-content">
    <div class="step-header mb-4">
      <h4>{{ t('eod.step2.title') }}</h4>
      <p class="text-muted">{{ t('eod.step2.description') }}</p>
    </div>

    <div v-if="!balanceData" class="text-center py-4">
      <button 
        class="btn btn-primary"
        @click="extractBalance"
        :disabled="loading || isProcessing"
      >
        <span v-if="isProcessing">
          <span class="spinner-border spinner-border-sm me-2" role="status"></span>
          {{ t('eod.step2.extracting') }}
        </span>
        <span v-else>
          <font-awesome-icon :icon="['fas', 'download']" class="me-2" />
          {{ t('eod.step2.extract_balance') }}
        </span>
      </button>
    </div>

    <div v-else>
      <div class="row">
        <div class="col-12">
          <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
              <h6 class="mb-0">{{ t('eod.step2.current_balance_info') }}</h6>
              <span class="badge bg-success">{{ t('eod.step2.extracted') }}</span>
            </div>
            <div class="card-body">
              <div v-if="balanceData.balances && balanceData.balances.length > 0">
                <div class="table-responsive">
                  <table class="table table-striped table-hover">
                    <thead class="table-dark-custom">
                      <tr>
                        <th>{{ t('eod.step2.currency_code') }}</th>
                        <th>{{ t('eod.step2.currency_name') }}</th>
                        <th class="text-end">{{ t('eod.step2.current_balance') }}</th>
                        <th>{{ t('eod.step2.last_updated') }}</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="balance in balanceData.balances" :key="balance.currency_id">
                        <td>
                          <div class="d-flex align-items-center">
                            <currency-flag :code="balance.currency_code || 'USD'" :custom-filename="balance.custom_flag_filename" class="me-2" />
                            <strong>{{ balance.currency_code }}</strong>
                          </div>
                        </td>
                        <td>{{ getCurrencyDisplayName(balance) }}</td>
                        <td class="text-end">
                          <span class="fw-bold" :class="getBalanceClass(balance.current_balance)">
                            {{ formatAmount(balance.current_balance) }}
                          </span>
                        </td>
                        <td>
                          <small class="text-muted">
                            {{ formatDateTime(balance.last_updated) }}
                          </small>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                <div class="row mt-4">
                  <div class="col-md-6">
                    <div class="card bg-light">
                      <div class="card-body">
                        <h6 class="card-title">
                          <font-awesome-icon :icon="['fas', 'coins']" class="me-2 text-primary" />
                          {{ t('eod.step2.balance_statistics') }}
                        </h6>
                        <p class="mb-1">
                          <strong>{{ t('eod.step2.total_currencies') }}:</strong> {{ balanceData.balances.length }} {{ t('eod.step2.currencies_unit') }}
                        </p>
                        <p class="mb-1">
                          <strong>{{ t('eod.step2.currencies_with_balance') }}:</strong> {{ balancesWithAmount }} {{ t('eod.step2.currencies_unit') }}
                        </p>
                        <p class="mb-0">
                          <strong>{{ t('eod.step2.zero_balance_currencies') }}:</strong> {{ balancesWithZero }} {{ t('eod.step2.currencies_unit') }}
                        </p>
                      </div>
                    </div>
                  </div>
                  <div class="col-md-6">
                    <div class="card bg-light">
                      <div class="card-body">
                        <h6 class="card-title">
                          <font-awesome-icon :icon="['fas', 'clock']" class="me-2 text-info" />
                          {{ t('eod.step2.extraction_info') }}
                        </h6>
                        <p class="mb-1">
                          <strong>{{ t('eod.step2.extraction_time') }}:</strong> {{ formatDateTime(new Date()) }}
                        </p>
                        <p class="mb-1">
                          <strong>{{ t('eod.step2.business_status') }}:</strong> 
                          <span class="badge bg-danger">{{ t('eod.step2.locked') }}</span>
                        </p>
                        <p class="mb-0">
                          <strong>{{ t('eod.step2.data_status') }}:</strong> 
                          <span class="badge bg-success">{{ t('eod.step2.frozen') }}</span>
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div v-else class="alert alert-info">
                <font-awesome-icon :icon="['fas', 'info-circle']" class="me-2" />
                {{ t('eod.step2.no_balance_records') }}
              </div>

              <div class="d-flex justify-content-end mt-4">
                <button 
                  class="btn btn-outline-secondary me-2"
                  @click="refreshBalance"
                  :disabled="loading || isProcessing"
                >
                  <font-awesome-icon :icon="['fas', 'sync']" class="me-1" />
                  {{ t('eod.step2.re_extract') }}
                </button>
                <button 
                  class="btn btn-success"
                  @click="proceedToNext"
                  :disabled="loading || isProcessing"
                >
                  <span v-if="isProcessing">
                    <span class="spinner-border spinner-border-sm me-2" role="status"></span>
                    {{ t('eod.step2.processing') }}
                  </span>
                  <span v-else>
                    <font-awesome-icon :icon="['fas', 'check']" class="me-1" />
                    {{ t('eod.step2.complete_extraction') }}
                  </span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { eodAPI } from '../../../api/eod'
import { formatDateTime, formatAmount } from '@/utils/formatters'
import CurrencyFlag from '../../CurrencyFlag.vue'
import { useI18n } from 'vue-i18n'
import { getCurrencyName } from '@/utils/currencyTranslator'

export default {
  name: 'Step2Balance',
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
    const { t } = useI18n()
    
    // 响应式数据
    const balanceData = ref(null)
    const isProcessing = ref(false)
    
    // 计算属性
    const balancesWithAmount = computed(() => {
      if (!balanceData.value?.balances) return 0
      return balanceData.value.balances.filter(b => b.current_balance > 0).length
    })
    
    const balancesWithZero = computed(() => {
      if (!balanceData.value?.balances) return 0
      return balanceData.value.balances.filter(b => b.current_balance === 0).length
    })
    
    // 方法
    const extractBalance = async () => {
      try {
        isProcessing.value = true
        
        const result = await eodAPI.extractBalance(props.eodId)
        
        if (result.success) {
          balanceData.value = result
        } else {
          emit('error', result.message || t('eod.step2.extract_balance_failed'))
        }
      } catch (error) {
        console.error(t('eod.step2.extract_balance_failed'), error)
        emit('error', error.response?.data?.message || error.message || t('eod.step2.extract_balance_failed'))
      } finally {
        isProcessing.value = false
      }
    }
    
    const refreshBalance = async () => {
      balanceData.value = null
      await extractBalance()
    }
    
    const proceedToNext = async () => {
      try {
        isProcessing.value = true
        
        // 先调用步骤3的API（计算理论余额）
        const result = await eodAPI.calculateBalance(props.eodId)
        
        if (result.success) {
          // 等待1秒确保操作完成
          await new Promise(resolve => setTimeout(resolve, 1000))
          
          emit('next', {
            balances: balanceData.value.balances,
            calculations: result.calculations,
            step: 3,  // 进入步骤3
            from_api_call: true  // 标识这是API调用完成
          })
        } else {
          emit('error', result.message || t('eod.step3.calculate_balance_failed'))
        }
      } catch (error) {
        console.error('计算理论余额失败:', error)
        emit('error', error.response?.data?.message || error.message || t('eod.step3.calculate_balance_failed'))
      } finally {
        isProcessing.value = false
      }
    }
    
    const getBalanceClass = (amount) => {
      if (amount > 0) return 'text-success'
      if (amount < 0) return 'text-danger'
      return 'text-muted'
    }
    
    // 获取币种显示名称，支持自定义币种
    const getCurrencyDisplayName = (balance) => {
      if (!balance) return ''
      
      // 检查是否是自定义币种（有custom_flag_filename）
      if (balance.custom_flag_filename) {
        // console.log(`[自定义币种] ${balance.currency_code} 使用数据库名称: ${balance.currency_name}`)
        return balance.currency_name || balance.currency_code
      }
      
      // 使用翻译
      return getCurrencyName(balance.currency_code)
    }
    
    // 生命周期
    onMounted(() => {
      if (props.eodId) {
        extractBalance()
      }
    })
    
    return {
      balanceData,
      isProcessing,
      balancesWithAmount,
      balancesWithZero,
      extractBalance,
      refreshBalance,
      proceedToNext,
      getBalanceClass,
      formatAmount,
      formatDateTime,
      getCurrencyName,
      getCurrencyDisplayName,
      t
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
}

.table-dark-custom th,
.table-dark-custom td {
  border-color: #32383e !important;
}

.card.bg-light {
  border: 1px solid #e9ecef;
}

.badge {
  font-size: 0.75rem;
}
</style> 
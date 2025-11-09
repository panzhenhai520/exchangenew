<template>
  <div class="step-content">
    <div class="step-header mb-4">
      <p class="text-muted" v-if="calculationData?.change_period">
        {{ $t('eod.step3.description_with_period', { 
          startDate: formatDateShort(calculationData.change_period.start_time),
          endDate: formatDateShort(calculationData.change_period.end_time)
        }) }}
      </p>
      <p class="text-muted" v-else>
        {{ $t('eod.step3.description_general') }}
      </p>
    </div>

    <div v-if="!calculationData" class="text-center py-4">
      <button 
        class="btn btn-primary"
        @click="calculateBalance"
        :disabled="loading || isCalculating"
      >
        <span v-if="isCalculating">
          <span class="spinner-border spinner-border-sm me-2" role="status"></span>
          {{ $t('eod.step3.calculating') }}
        </span>
        <span v-else>
          <font-awesome-icon :icon="['fas', 'calculator']" class="me-2" />
          {{ $t('eod.step3.calculate_theoretical_balance') }}
        </span>
      </button>
    </div>

    <div v-else>
      <div class="card">
        <div class="card-header d-flex justify-content-between align-items-center">
          <h6 class="mb-0">{{ $t('eod.step3.calculation_result') }}</h6>
          <span class="badge bg-success">{{ $t('eod.step3.calculation_completed') }}</span>
        </div>
        <div class="card-body">
          <div class="table-responsive">
            <table class="table table-striped table-hover">
              <thead class="table-dark-custom">
                <tr>
                  <th>{{ $t('eod.step3.table_header.currency') }}</th>
                  <th class="text-end">{{ $t('eod.step3.table_header.opening_balance') }}</th>
                  <th class="text-end">{{ $t('eod.step3.table_header.daily_change') }}</th>
                  <th class="text-end">{{ $t('eod.step3.table_header.theoretical_balance') }}</th>
                  <th class="text-end">{{ $t('eod.step3.table_header.actual_balance') }}</th>
                  <th class="text-end">{{ $t('eod.step3.table_header.difference') }}</th>
                </tr>
              </thead>
              <tbody>

                
                <template v-for="item in filteredCalculations" :key="item?.currency_id || `currency-${Math.random()}`">
                  <tr 
                    class="currency-row"
                  >
                  <td>
                    <div class="d-flex align-items-center">
                      <CurrencyFlag :code="item ? (item.currency_code || 'USD') : 'USD'" :custom-filename="item ? item.custom_flag_filename : null" class="me-2" />
                      <div class="flex-grow-1">
                        <div class="d-flex align-items-center justify-content-between">
                          <div>
                            <strong>{{ item ? (item.currency_code || 'N/A') : 'N/A' }}</strong>
                            <span class="text-muted small ms-2">{{ item ? getCurrencyDisplayName(item) : '' }}</span>
                            <span class="text-muted ms-2" style="font-size: 0.65em;">
                              <font-awesome-icon :icon="['fas', 'clock']" class="me-1" />
                              {{ item ? formatTimeRange(item.change_start_time, item.change_end_time) : '时间范围未知' }}
                            </span>
                          </div>
                          <button 
                            v-if="item && item.daily_change !== 0"
                            class="btn btn-sm btn-outline-secondary"
                            @click="item && item.currency_code ? toggleCurrencyDetail(item.currency_code) : null"
                            :disabled="!item || !item.currency_code || loadingDetail === item.currency_code"
                            title="查看明细"
                          >
                            <span v-if="item && loadingDetail === item.currency_code">
                              <span class="spinner-border spinner-border-sm" role="status"></span>
                            </span>
                            <font-awesome-icon 
                              v-else
                              :icon="['fas', item && item.currency_code && expandedCurrencies.includes(item.currency_code) ? 'chevron-up' : 'chevron-down']" 
                            />
                          </button>
                        </div>
                      </div>
                    </div>
                  </td>
                  <td class="text-end">{{ item ? formatAmount(item.opening_balance) : 'N/A' }}</td>
                  <td class="text-end" :class="item ? getAdjustmentClass(item.daily_change) : ''">
                    {{ item ? formatAdjustment(item.daily_change) : 'N/A' }}
                  </td>
                  <td class="text-end">
                    <strong :class="item ? getBalanceClass(item.theoretical_balance) : ''">
                      {{ item ? formatAmount(item.theoretical_balance) : 'N/A' }}
                    </strong>
                  </td>
                  <td class="text-end">{{ item ? formatAmount(item.actual_balance) : 'N/A' }}</td>
                  <td class="text-end" :class="item ? getDifferenceClass(item.difference) : ''">
                    {{ item ? formatDifference(item.difference) : 'N/A' }}
                  </td>
                </tr>
                
                <!-- 明细展开行，紧跟在主行后面 -->
                <tr v-if="item && item.currency_code && expandedCurrencies.includes(item.currency_code)" :key="`${item.currency_id}-detail`">
                  <td colspan="6" class="p-0">
                    <div class="currency-detail-panel">

                      <div v-if="item && item.currency_code && currencyDetails[item.currency_code]?.loading" class="text-center py-3">
                        <span class="spinner-border spinner-border-sm me-2" role="status"></span>
                        {{ $t('eod.step3.loading_transactions') }}
                      </div>
                      <div v-else-if="item && item.currency_code && currencyDetails[item.currency_code]?.error" class="alert alert-danger m-3">
                        {{ item && item.currency_code ? currencyDetails[item.currency_code].error : '' }}
                      </div>
                      <div v-else-if="item && item.currency_code && currencyDetails[item.currency_code]?.data && (!currencyDetails[item.currency_code]?.data?.transactions || currencyDetails[item.currency_code]?.data?.transactions?.length === 0)" class="alert alert-info m-3">
                        <font-awesome-icon :icon="['fas', 'info-circle']" class="me-2" />
                        该币种在统计时间范围内没有交易记录
                      </div>
                      <div v-else-if="item && item.currency_code && currencyDetails[item.currency_code]?.data && currencyDetails[item.currency_code]?.data?.transactions && currencyDetails[item.currency_code]?.data?.transactions?.length > 0" class="p-3">
                        <div class="row mb-3">
                          <div class="col-md-6">
                            <h6>{{ $t('eod.step3.calculation_summary') }}</h6>
                            <div class="row">
                              <div class="col-6">
                                <small class="text-muted">{{ $t('eod.step3.opening_balance') }}:</small>
                                <div class="fw-bold">{{ item && item.currency_code && currencyDetails[item.currency_code]?.data ? formatAmount(currencyDetails[item.currency_code].data.opening_balance) : 'N/A' }}</div>
                              </div>
                              <div class="col-6">
                                <small class="text-muted">{{ $t('eod.step3.daily_change') }}:</small>
                                <div class="fw-bold" :class="item ? getAdjustmentClass(item.daily_change) : ''">
                                  {{ item ? formatAdjustment(item.daily_change) : 'N/A' }}
                                </div>
                              </div>
                            </div>
                          </div>
                          <div class="col-md-6">
                            <div class="d-flex align-items-center justify-content-between">
                              <div>
                                <small class="text-muted">{{ $t('eod.step3.selected_total') }}:</small>
                                <div class="fw-bold" :class="item && item.currency_code && selectedTransactionsTotal[item.currency_code] ? getAdjustmentClass(selectedTransactionsTotal[item.currency_code]) : ''">
                                  {{ item && item.currency_code && selectedTransactionsTotal[item.currency_code] ? formatAdjustment(selectedTransactionsTotal[item.currency_code]) : '0.00' }}
                                </div>
                              </div>
                              <div class="btn-group btn-group-sm">
                                <button 
                                  class="btn btn-outline-secondary"
                                  @click="item && item.currency_code ? selectAllTransactions(item.currency_code) : null"
                                >
                                  {{ $t('eod.step3.select_all') }}
                                </button>
                                <button 
                                  class="btn btn-outline-secondary"
                                  @click="item && item.currency_code ? deselectAllTransactions(item.currency_code) : null"
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
                                    :checked="item && item.currency_code && isAllSelected(item.currency_code)"
                                    @change="item && item.currency_code ? toggleSelectAll(item.currency_code) : null"
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
                              <tr v-for="tx in (item && item.currency_code && currencyDetails[item.currency_code]?.data?.transactions || [])" :key="tx?.id || `tx-${Math.random()}`">
                                <td>
                                  <input 
                                    type="checkbox" 
                                    :checked="item && item.currency_code && selectedTransactions[item.currency_code]?.includes(tx?.id)"
                                    @change="item && item.currency_code && tx ? toggleTransactionSelection(item.currency_code, tx.id, tx.amount) : null"
                                    class="form-check-input"
                                  />
                                </td>
                                <td>{{ formatDateTime(tx?.created_at) }}</td>
                                <td>
                                  <span class="badge" :class="getTransactionTypeClass(tx?.type)">
                                    {{ getTransactionTypeLabel(tx?.type) }}
                                  </span>
                                </td>
                                <td>{{ getTransactionDescription(tx?.description) }}</td>
                                <td class="text-end">{{ formatAmount(tx?.foreign_amount) }}</td>
                                <td class="text-end">{{ formatRate(tx?.rate) }}</td>
                                <td class="text-end" :class="getAdjustmentClass(tx?.amount)">
                                  {{ formatAdjustment(tx?.amount) }}
                                </td>
                              </tr>
                            </tbody>
                          </table>
                        </div>
                        
                        <!-- 分页控件 -->
                        <div v-if="currencyDetails[item.currency_code]?.data?.pagination" class="d-flex justify-content-between align-items-center mt-3 p-2 bg-light">
                          <div class="text-muted small">
                            {{ $t('common.showing') }} {{ (currencyDetails[item.currency_code].data.pagination.current_page - 1) * currencyDetails[item.currency_code].data.pagination.per_page + 1 }} - 
                            {{ Math.min(currencyDetails[item.currency_code].data.pagination.current_page * currencyDetails[item.currency_code].data.pagination.per_page, currencyDetails[item.currency_code].data.pagination.total_count) }} 
                            {{ $t('common.of') }} {{ currencyDetails[item.currency_code].data.pagination.total_count }} {{ $t('common.records') }}
                          </div>
                          <div class="btn-group btn-group-sm">
                            <button 
                              class="btn btn-outline-secondary"
                              :disabled="!currencyDetails[item.currency_code].data.pagination.has_prev"
                              @click="loadCurrencyTransactionsPage(item.currency_code, currencyDetails[item.currency_code].data.pagination.current_page - 1)"
                            >
                              <font-awesome-icon :icon="['fas', 'chevron-left']" />
                            </button>
                            <button class="btn btn-outline-secondary disabled">
                              {{ currencyDetails[item.currency_code].data.pagination.current_page }} / {{ currencyDetails[item.currency_code].data.pagination.total_pages }}
                            </button>
                            <button 
                              class="btn btn-outline-secondary"
                              :disabled="!currencyDetails[item.currency_code].data.pagination.has_next"
                              @click="loadCurrencyTransactionsPage(item.currency_code, currencyDetails[item.currency_code].data.pagination.current_page + 1)"
                            >
                              <font-awesome-icon :icon="['fas', 'chevron-right']" />
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </td>
                </tr>
                </template>
              </tbody>
            </table>
          </div>

          <div class="row mt-3">
            <div class="col-md-6">
              <div class="card bg-light" style="height: 120px;">
                <div class="card-body py-2">
                  <h6 class="card-title mb-2" style="font-size: 0.9rem;">
                    <font-awesome-icon :icon="['fas', 'chart-line']" class="me-2 text-primary" />
                    {{ $t('eod.step3.calculation_statistics') }}
                  </h6>
                  <div style="font-size: 0.85rem; line-height: 1.3;">
                    <div><strong>{{ $t('eod.step3.calculated_currencies') }}:</strong> {{ calculationData?.calculations?.length || 0 }} {{ $t('eod.step2.currencies_unit') }}</div>
                    <div><strong>{{ $t('eod.step3.currencies_with_changes') }}:</strong> {{ currenciesWithChanges }} {{ $t('eod.step2.currencies_unit') }}</div>
                    <div><strong>{{ $t('eod.step3.calculation_time') }}:</strong> {{ formatDateTime(new Date()) }}</div>
                  </div>
                </div>
              </div>
            </div>
            <div class="col-md-6">
              <div class="card bg-light" style="height: 120px;">
                <div class="card-body py-2">
                  <h6 class="card-title mb-2" style="font-size: 0.9rem;">
                    <font-awesome-icon :icon="['fas', 'info-circle']" class="me-2 text-info" />
                    {{ $t('eod.step3.calculation_explanation') }}
                  </h6>
                  <div style="font-size: 0.85rem; line-height: 1.3;">
                    <div>{{ $t('eod.step3.formula_description') }}</div>
                    <div>{{ $t('eod.step3.opening_balance_note') }}</div>
                    <div>{{ $t('eod.step3.daily_change_note') }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="d-flex justify-content-end mt-4">
            <button 
              class="btn btn-outline-secondary me-2"
              @click="recalculate"
              :disabled="loading || isCalculating"
            >
              <font-awesome-icon :icon="['fas', 'sync']" class="me-1" />
              {{ $t('eod.step3.recalculate') }}
            </button>
            <button 
              class="btn btn-success"
              @click="proceedToNext"
              :disabled="loading || isCalculating"
            >
              <span v-if="isCalculating">
                <span class="spinner-border spinner-border-sm me-2" role="status"></span>
                {{ $t('eod.step3.processing') }}
              </span>
              <span v-else>
                <font-awesome-icon :icon="['fas', 'check']" class="me-1" />
                {{ $t('eod.step3.complete_calculation') }}
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { eodAPI } from '../../../api/eod'
import CurrencyFlag from '../../CurrencyFlag.vue'
import { formatDateTime, formatAmount } from '@/utils/formatters'
import { getCurrencyName, getCurrencyDisplayName as getCurrencyDisplayNameFromUtils } from '@/utils/currencyTranslator'

export default {
  name: 'Step3Calculate',
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
    const calculationData = ref(null)
    const isCalculating = ref(false)
    
    // 币种展开功能相关数据
    const expandedCurrencies = ref([])
    const currencyDetails = ref({})
    const loadingDetail = ref(null)
    const selectedTransactions = ref({})
    const selectedTransactionsTotal = ref({})
    

    
    // 计算属性
    const currenciesWithChanges = computed(() => {
      if (!calculationData.value?.calculations) return 0
      return calculationData.value.calculations.filter(item => 
        item.daily_change !== 0
      ).length
    })
    
    // 过滤后的计算数据，确保每个item都存在且有效
    const filteredCalculations = computed(() => {
      if (!calculationData.value?.calculations) return []
      const filtered = calculationData.value.calculations.filter(item => 
        item != null && 
        item.currency_code != null && 
        item.currency_id != null
      )
      return filtered
    })
    
    // 方法
    const calculateBalance = async () => {
      try {
        isCalculating.value = true
        
        const result = await eodAPI.calculateBalance(props.eodId)
        
        if (result.success) {
          calculationData.value = result
        } else {
          emit('error', result.message || t('eod.step3.calculation_failed'))
        }
      } catch (error) {
        console.error('计算理论余额失败:', error)
        emit('error', error.response?.data?.message || error.message || t('eod.step3.calculation_failed'))
      } finally {
        isCalculating.value = false
      }
    }
    

    
    const recalculate = async () => {
      calculationData.value = null
      await calculateBalance()
    }
    
    const proceedToNext = async () => {
      try {
        isCalculating.value = true
        
        // 调用API来完成第3步计算（重新调用计算API确保状态同步）
        const result = await eodAPI.calculateBalance(props.eodId)
        
        if (result.success) {
          emit('next', {
            calculation_data: result,
            step: 4,  // 第3步完成后，应该进入第4步
            from_api_call: true  // 标识这是API调用触发的事件
          })
        } else {
          emit('error', result.message || t('eod.step3.complete_calculation_failed'))
        }
      } catch (error) {
        console.error('完成计算失败:', error)
        emit('error', error.response?.data?.message || error.message || t('eod.step3.complete_calculation_failed'))
      } finally {
        isCalculating.value = false
      }
    }
    

    
    const formatTimeRange = (startTime, endTime) => {
      if (!startTime || !endTime) return '时间范围未知'
      
      try {
        const start = new Date(startTime)
        const end = new Date(endTime)
        
        const startStr = start.toLocaleString('zh-CN', {
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit'
        })
        
        const endStr = end.toLocaleString('zh-CN', {
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit'
        })
        
        return `${startStr} ~ ${endStr}`
      } catch (error) {
        console.warn('格式化时间范围失败:', error)
        return '时间范围未知'
      }
    }
    
    const formatDateTimeDetailed = (dateStr) => {
      if (!dateStr) return '未知时间'
      const date = new Date(dateStr)
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit', 
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    }
    
    const getBalanceClass = (amount) => {
      if (amount > 0) return 'text-success'
      if (amount < 0) return 'text-danger'
      return 'text-muted'
    }
    
    const getAdjustmentClass = (amount) => {
      if (amount > 0) return 'text-success'
      if (amount < 0) return 'text-danger'
      return 'text-muted'
    }
    
    const getDifferenceClass = (amount) => {
      if (amount > 0) return 'text-success'
      if (amount < 0) return 'text-danger'
      return 'text-muted'
    }
    
    const formatAdjustment = (amount) => {
      const formatted = formatAmount(Math.abs(amount))
      if (amount > 0) return `+${formatted}`
      if (amount < 0) return `-${formatted}`
      return formatted
    }
    
    const formatDifference = (amount) => {
      const formatted = formatAmount(Math.abs(amount))
      if (amount > 0) return `+${formatted}`
      if (amount < 0) return `-${formatted}`
      return formatted
    }
    
    const formatDateShort = (dateStr) => {
      if (!dateStr) return ''
      const date = new Date(dateStr)
      return date.toLocaleDateString('zh-CN', { 
        year: 'numeric', 
        month: '2-digit', 
        day: '2-digit' 
      }).replace(/\//g, '/')
    }
    
    // 获取币种显示名称，支持自定义币种
    const getCurrencyDisplayName = (item) => {
      if (!item || typeof item !== 'object') return ''
      
      // 使用新的币种显示函数
      return getCurrencyDisplayNameFromUtils(item.currency_code || '', item)
    }
    
    // 币种展开功能相关方法
    const toggleCurrencyDetail = async (currencyCode) => {
      if (!currencyCode) {
        console.warn('currencyCode is undefined or null')
        return
      }
      
      const index = expandedCurrencies.value.indexOf(currencyCode)
      if (index > -1) {
        // 收起
        expandedCurrencies.value.splice(index, 1)
        // 清理数据
        if (currencyDetails.value && currencyDetails.value[currencyCode]) {
          delete currencyDetails.value[currencyCode]
        }
        if (selectedTransactions.value && selectedTransactions.value[currencyCode]) {
          delete selectedTransactions.value[currencyCode]
        }
        if (selectedTransactionsTotal.value && selectedTransactionsTotal.value[currencyCode]) {
          delete selectedTransactionsTotal.value[currencyCode]
        }
      } else {
        // 展开
        expandedCurrencies.value.push(currencyCode)
        await loadCurrencyTransactions(currencyCode)
      }
      
      // 强制触发响应式更新
      await nextTick()
    }
    
    const loadCurrencyTransactions = async (currencyCode, page = 1) => {
      if (!currencyCode) return
      
      try {
        loadingDetail.value = currencyCode
        if (page === 1) {
          currencyDetails.value[currencyCode] = { loading: true, error: null, data: null }
        }
        
        // 【优化】添加分页参数，限制查询数量
        const result = await eodAPI.getCurrencyTransactionsDetail(props.eodId, currencyCode, {
          page: page,
          per_page: 20  // 设置为20条记录一页
        })
        
        if (result.success) {
          currencyDetails.value[currencyCode] = { 
            loading: false, 
            error: null, 
            data: result.data 
          }
          // 初始化选中状态（仅在第一页时）
          if (page === 1) {
            selectedTransactions.value[currencyCode] = []
            selectedTransactionsTotal.value[currencyCode] = 0
          }
        } else {
          currencyDetails.value[currencyCode] = { 
            loading: false, 
            error: result.message || '加载失败', 
            data: null 
          }
        }
      } catch (error) {
        console.error('加载币种交易详情失败:', error)
        currencyDetails.value[currencyCode] = { 
          loading: false, 
          error: error.response?.data?.message || error.message || '加载失败', 
          data: null 
        }
      } finally {
        loadingDetail.value = null
      }
    }
    
    // 翻页方法
    const loadCurrencyTransactionsPage = async (currencyCode, page) => {
      if (!currencyCode || page < 1) return
      await loadCurrencyTransactions(currencyCode, page)
    }
    
    const toggleTransactionSelection = (currencyCode, txId, amount) => {
      if (!currencyCode || !txId) return
      
      if (!selectedTransactions.value[currencyCode]) {
        selectedTransactions.value[currencyCode] = []
      }
      if (!selectedTransactionsTotal.value[currencyCode]) {
        selectedTransactionsTotal.value[currencyCode] = 0
      }
      
      const index = selectedTransactions.value[currencyCode].indexOf(txId)
      if (index > -1) {
        selectedTransactions.value[currencyCode].splice(index, 1)
        selectedTransactionsTotal.value[currencyCode] -= (amount || 0)
      } else {
        selectedTransactions.value[currencyCode].push(txId)
        selectedTransactionsTotal.value[currencyCode] += (amount || 0)
      }
    }
    
    const selectAllTransactions = (currencyCode) => {
      if (!currencyCode || !currencyDetails.value[currencyCode]?.data?.transactions) return
      
      selectedTransactions.value[currencyCode] = currencyDetails.value[currencyCode].data.transactions.map(tx => tx?.id).filter(id => id != null)
      selectedTransactionsTotal.value[currencyCode] = currencyDetails.value[currencyCode].data.transactions.reduce((sum, tx) => sum + (tx?.amount || 0), 0)
    }
    
    const deselectAllTransactions = (currencyCode) => {
      if (!currencyCode) return
      selectedTransactions.value[currencyCode] = []
      selectedTransactionsTotal.value[currencyCode] = 0
    }
    
    const isAllSelected = (currencyCode) => {
      if (!currencyCode || !currencyDetails.value[currencyCode]?.data?.transactions?.length) return false
      return currencyDetails.value[currencyCode].data.transactions.every(tx => 
        selectedTransactions.value[currencyCode]?.includes(tx?.id)
      )
    }
    
    const toggleSelectAll = (currencyCode) => {
      if (!currencyCode) return
      if (isAllSelected(currencyCode)) {
        deselectAllTransactions(currencyCode)
      } else {
        selectAllTransactions(currencyCode)
      }
    }
    
    const getTransactionTypeClass = (type) => {
      if (!type || typeof type !== 'string') return 'bg-secondary'
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
      if (!type || typeof type !== 'string') return '未知'
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
    
    const getTransactionDescription = (description) => {
      if (!description || typeof description !== 'string') return ''
      
      // 检查是否是翻译键格式
      if (description.startsWith('eod.step5.')) {
        // 解析翻译键和参数
        const parts = description.split(' ')
        const translationKey = parts[0]
        const currencyCode = parts[1] || ''
        const amount = parts[2] || ''
        
        // 尝试翻译
        try {
          const translated = t(translationKey, { currency: currencyCode, amount: amount })
          return translated
        } catch (e) {
          // 如果翻译失败，返回原始描述
          return description
        }
      }
      
      return description
    }
    
    const formatRate = (rate) => {
      return new Intl.NumberFormat('zh-CN', {
        minimumFractionDigits: 4,
        maximumFractionDigits: 4
      }).format(rate || 0)
    }
    
    // 生命周期
    onMounted(() => {
      if (props.eodId) {
        calculateBalance()
      }
    })
    
    // 组件卸载时清理数据
    onUnmounted(() => {
      try {
        // 清理所有响应式数据，避免内存泄漏和null访问错误
        if (currencyDetails.value) currencyDetails.value = {}
        if (selectedTransactions.value) selectedTransactions.value = {}
        if (selectedTransactionsTotal.value) selectedTransactionsTotal.value = {}
        if (expandedCurrencies.value) expandedCurrencies.value = []
        loadingDetail.value = null
      } catch (error) {
        console.warn('组件卸载时清理数据出错:', error)
      }
    })
    
    return {
      t,
      calculationData,
      isCalculating,
      currenciesWithChanges,
      filteredCalculations,
      calculateBalance,
      recalculate,
      proceedToNext,
      getBalanceClass,
      getAdjustmentClass,
      getDifferenceClass,

      formatTimeRange,
      formatDateTimeDetailed,
      formatAmount,
      formatAdjustment,
      formatDifference,
      formatDateTime,
      formatDateShort,
      getCurrencyName,
      getCurrencyDisplayName,
      expandedCurrencies,
      currencyDetails,
      loadingDetail,
      selectedTransactions,
      selectedTransactionsTotal,
      toggleCurrencyDetail,
      loadCurrencyTransactions,
      toggleTransactionSelection,
      selectAllTransactions,
      deselectAllTransactions,
      isAllSelected,
      toggleSelectAll,
      getTransactionTypeClass,
      getTransactionTypeLabel,
      getTransactionDescription,
      formatRate,
      loadCurrencyTransactionsPage
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

/* 币种行悬停效果 */
.currency-row {
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.currency-row:hover {
  background-color: #f8f9fa !important;
}

/* 时间范围提示样式 */
.time-range-hint {
  font-size: 0.75rem;
  color: #6c757d;
  margin-top: 2px;
}

/* 响应式表格 */
@media (max-width: 768px) {
  .time-range-hint {
    display: none;
  }
}

/* 币种展开面板样式 */
.currency-detail-panel {
  background-color: #f8f9fa;
  border-top: 1px solid #dee2e6;
}

.currency-detail-panel .table {
  margin-bottom: 0;
}

.currency-detail-panel .table th {
  background-color: #e9ecef;
  border-color: #dee2e6;
  font-size: 0.875rem;
  font-weight: 600;
}

.currency-detail-panel .table td {
  font-size: 0.875rem;
  vertical-align: middle;
}

.currency-detail-panel .form-check-input {
  margin: 0;
}

.currency-detail-panel .badge {
  font-size: 0.75rem;
}

/* 选中合计样式 */
.selected-total {
  background-color: #e3f2fd;
  border: 1px solid #bbdefb;
  border-radius: 4px;
  padding: 8px 12px;
}

/* 展开按钮样式 */
.expand-button {
  transition: all 0.2s ease;
}

.expand-button:hover {
  transform: scale(1.05);
}

/* 交易类型徽章样式 */
.transaction-type-badge {
  font-size: 0.75rem;
  padding: 2px 6px;
}
</style> 
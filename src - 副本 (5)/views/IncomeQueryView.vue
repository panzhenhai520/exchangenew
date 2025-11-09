<template>
  <div class="income-query-page">
    <div class="page-header">
      <h2 class="page-title-bold">
        <font-awesome-icon :icon="['fas', 'chart-bar']" class="me-2" />
        {{ $t('reports.income_query') }}
      </h2>
      <div class="operation-buttons">
        <button 
          class="btn btn-primary" 
          @click="refreshData"
          :disabled="loading"
        >
          <i class="fas fa-sync-alt"></i>
          {{ $t('common.refresh') }}
        </button>

      </div>
    </div>

    <div class="loading-container" v-if="loading">
      <div class="spinner-border" role="status">
        <span class="sr-only">{{ $t('common.loading') }}</span>
      </div>
      <p>{{ $t('reports.loading_data') }}</p>
    </div>

    <div class="content-container" v-else>
      <!-- 报表信息 -->
      <div class="report-info" v-if="reportData">
        <div class="info-card">
          <div class="info-inline">
            <span class="info-item">
              <strong>{{ $t('reports.branch') }}:</strong> {{ reportData.branch_name }}
            </span>
            <span class="info-item">
              <strong>{{ $t('reports.base_currency') }}:</strong> {{ reportData.base_currency }}
            </span>
            <span class="info-item">
              <strong>{{ $t('reports.time_range') }}:</strong> {{ formatTimeRange(reportData.start_time, reportData.end_time) }}
            </span>
            <span class="info-item">
              <strong>{{ $t('reports.total_income') }}:</strong> 
              <span class="income-amount">{{ formatCurrency(reportData.total_income) }}</span>
            </span>
            <span class="info-item">
              <strong>{{ $t('reports.total_spread_income') }}:</strong> 
              <span class="spread-amount">{{ formatCurrency(reportData.total_spread_income) }}</span>
            </span>
          </div>
          <!-- 点差收入计算公式 -->
          <div class="formula-info">
            <div class="formula-text">
              <i class="fas fa-info-circle"></i>
              <strong>{{ $t('reports.spread_formula') }}</strong>
              {{ $t('reports.spread_formula_desc') }}
            </div>
          </div>
        </div>
      </div>

      <!-- 币种收入统计表 -->
      <div class="data-table-container" v-if="reportData && reportData.currencies.length > 0">
        <h4>{{ $t('reports.currency_income_stats') }}</h4>
        <div class="table-responsive">
          <table class="table table-striped">
            <thead>
              <tr>
                <th>{{ $t('reports.currency') }}</th>
                <th>{{ $t('reports.buy_volume') }}</th>
                <th>{{ $t('reports.sell_volume') }}</th>
                <th>{{ $t('reports.reversal_amount') }}</th>
                <th>{{ $t('reports.buy_rate') }}</th>
                <th>{{ $t('reports.sell_rate') }}</th>
                <th>{{ $t('reports.actual_income') }}</th>
                <th>{{ $t('reports.spread_income') }}</th>
              </tr>
            </thead>
            <tbody>
              <template v-for="currency in reportData.currencies" :key="currency.currency_code">
                <tr class="currency-row" 
                    @click="toggleCurrencyDetails(currency.currency_code)"
                    :class="{ 'expanded': expandedCurrency === currency.currency_code }">
                  <td>
                    <div class="currency-info-cell">
                      <CurrencyFlag 
                        v-if="currency.currency_code"
                        :code="currency.currency_code" 
                        :custom-filename="currency.custom_flag_filename"
                        :width="20"
                        :height="14"
                        class="currency-flag"
                      />
                      <div class="currency-details">
                        <div class="currency-code">{{ currency.currency_code }}</div>
                        <div class="currency-name">{{ getCurrencyDisplayName(currency) }}</div>
                      </div>
                      <i class="fas fa-chevron-down detail-arrow" 
                         :class="{ 'rotated': expandedCurrency === currency.currency_code }"></i>
                    </div>
                  </td>
                  <td>{{ formatNumber(currency.total_buy) }}</td>
                  <td>{{ formatNumber(currency.total_sell) }}</td>
                  <td>{{ formatNumber(currency.reversal_amount || 0) }}</td>
                  <td>{{ formatRate(currency.buy_rate) }}</td>
                  <td>{{ formatRate(currency.sell_rate) }}</td>
                  <td :class="getIncomeClass(currency.income)">
                    {{ formatCurrency(currency.income) }}
                  </td>
                  <td :class="getIncomeClass(currency.spread_income)">
                    {{ formatCurrency(currency.spread_income) }}
                  </td>
                </tr>
                <!-- 明细展开区域 -->
                <tr v-if="expandedCurrency === currency.currency_code" class="details-row">
                  <td colspan="8" class="details-cell">
                    <div class="transaction-details-compact">
                      <div class="details-header-compact">
                        <div class="details-title">
                          <CurrencyFlag 
                            v-if="currency.currency_code"
                            :code="currency.currency_code" 
                            :custom-filename="currency.custom_flag_filename"
                            :width="18"
                            :height="12"
                            class="detail-flag"
                          />
                          <span class="currency-title">{{ currency.currency_code }} {{ $t('reports.transaction_details') }}</span>
                          <button class="btn-collapse" @click="expandedCurrency = null">
                            <i class="fas fa-times"></i>
                          </button>
                        </div>
                        <div class="details-summary-compact">
                          <!-- 第一行：期初余额和当前余额 -->
                          <div class="balance-summary-row">
                            <span class="balance-info">{{ $t('reports.opening_balance') }}: <strong class="opening-balance">{{ formatBalanceAmount(currency.currency_code, 'opening') }} {{ currency.currency_code }}</strong></span>
                            <span class="balance-separator">→</span>
                            <span class="balance-info">{{ $t('reports.current_balance') }}: <strong class="current-balance" :class="getCurrentBalanceClass(currency.currency_code)">{{ formatBalanceAmount(currency.currency_code, 'current') }} {{ currency.currency_code }}</strong></span>
                            <span class="balance-change" :class="getBalanceChangeClass(currency.currency_code)">({{ formatBalanceChange(currency.currency_code) }})</span>
                          </div>
                          
                          <!-- 第二行：交易统计 -->
                          <div class="transaction-summary-row">
                            <span class="summary-compact">{{ $t('common.transaction_count') }}: {{ paginatedTransactions[currency.currency_code]?.totalCount || 0 }}</span>
                            <span class="summary-compact">{{ $t('common.foreign_total') }}: <span :class="getForeignTotalClass(currency.currency_code)">{{ formatForeignTotal(currency.currency_code) }}</span></span>
                            <span class="summary-compact">{{ $t('common.local_total') }}: {{ formatLocalTotal(currency.currency_code) }}</span>
                            <span class="period-method-info" :title="getPeriodMethodTooltip(currency.currency_code)">
                              <i class="fas fa-info-circle"></i>
                              {{ getPeriodMethodText(currency.currency_code) }}
                            </span>
                          </div>
                          
                          <!-- 动态勾选计算区域 -->
                          <div v-if="hasSelectedTransactions" class="selected-summary-compact">
                            <div class="selected-divider"></div>
                            <span class="selected-label">{{ $t('common.selected') }}:</span>
                            <span class="selected-count">{{ selectedCount }}{{ $t('common.transactions_unit') }}</span>
                            <span class="selected-foreign">{{ $t('common.foreign_currency') }} <span :class="selectedForeignTotal >= 0 ? 'text-success' : 'text-danger'">{{ formatSignedAmount(selectedForeignTotal) }}</span></span>
                            <span class="selected-local">{{ $t('common.local_currency') }} {{ formatCurrency(selectedLocalTotal) }}</span>
                            <button class="btn-clear-selections" @click="clearAllSelections" :title="$t('common.clear_selection')">
                              <i class="fas fa-times"></i>
                            </button>
                          </div>
                        </div>
                      </div>
                      
                      <div class="transactions-container-compact" v-if="currencyDetails[currency.currency_code]">
                        <!-- 全选控制 -->
                        <div class="transaction-control-row">
                          <label class="checkbox-container">
                            <input type="checkbox" 
                                   :checked="isCurrentPageAllSelected(currency.currency_code)"
                                   @change="toggleAllCurrentPage(currency.currency_code)">
                            <span class="checkmark"></span>
                            <span class="checkbox-label">
                              {{ isCurrentPageAllSelected(currency.currency_code) ? $t('eod.deselect_all') : $t('eod.select_all_current_page') }}
                            </span>
                          </label>
                        </div>
                        
                        <div class="transaction-row-compact" 
                             v-for="transaction in getCurrentPageTransactions(currency.currency_code)" 
                             :key="transaction.transaction_no"
                             :class="{ 'transaction-selected': isTransactionSelected(currency.currency_code, transaction) }">
                          <div class="transaction-line">
                            <label class="checkbox-container">
                              <input type="checkbox" 
                                     :checked="isTransactionSelected(currency.currency_code, transaction)"
                                     @change="toggleTransactionSelection(currency.currency_code, transaction)">
                              <span class="checkmark"></span>
                            </label>
                            <span class="tx-no">{{ getShortTransactionNo(transaction.transaction_no) }}</span>
                            <span class="tx-time">{{ getCompactDateTime(transaction.created_at) }}</span>
                            <span class="tx-separator">|</span>
                            <span class="tx-type" :class="getTransactionTypeClass(transaction.type)">
                              {{ getTransactionTypeText(transaction.type) }}:
                            </span>
                            <span class="tx-foreign" :class="getTransactionAmountClass(transaction.amount)">
                              {{ formatSignedForeignAmount(transaction.amount) }} {{ transaction.currency_code }}
                            </span>
                            <span class="tx-rate">× {{ formatRate(transaction.rate) }}</span>
                            <span class="tx-equals">=</span>
                            <span class="tx-local">{{ formatCurrency(transaction.local_amount) }}</span>
                            <span class="tx-separator">|</span>
                            <span class="tx-customer">{{ transaction.customer_name }}</span>
                          </div>
                        </div>
                        
                        <!-- 分页控制 -->
                        <div class="pagination-controls" v-if="needsPagination(currency.currency_code)">
                          <div class="pagination-info">
                            {{ $t('common.page_info', { 
                              current: getCurrentPage(currency.currency_code),
                              total: getTotalPages(currency.currency_code),
                              count: getTotalTransactions(currency.currency_code)
                            }) }}
                          </div>
                          <div class="pagination-buttons">
                            <button class="btn-page" 
                                    @click="prevPage(currency.currency_code)"
                                    :disabled="getCurrentPage(currency.currency_code) === 1">
                              <i class="fas fa-chevron-left"></i>
                            </button>
                            <button class="btn-page" 
                                    @click="nextPage(currency.currency_code)"
                                    :disabled="getCurrentPage(currency.currency_code) === getTotalPages(currency.currency_code)">
                              <i class="fas fa-chevron-right"></i>
                            </button>
                          </div>
                        </div>
                        
                        <!-- 页面小计/总计 -->
                        <div class="subtotal-row">
                          <div class="subtotal-content">
                            <span v-if="needsPagination(currency.currency_code) && getCurrentPage(currency.currency_code) < getTotalPages(currency.currency_code)">
                              {{ $t('common.page_subtotal') }}: {{ $t('common.foreign_currency') }} <span :class="getForeignPageTotalClass(currency.currency_code)">{{ formatForeignPageTotal(currency.currency_code) }}</span>，
                              {{ $t('common.local_currency') }} {{ formatLocalPageTotal(currency.currency_code) }}
                            </span>
                            <span v-else>
                              <strong>{{ $t('common.total') }}: {{ $t('common.foreign_currency') }} <span :class="getForeignTotalClass(currency.currency_code)">{{ formatForeignTotal(currency.currency_code) }}</span>，
                              {{ $t('common.local_currency') }} {{ formatLocalTotal(currency.currency_code) }}</strong>
                            </span>
                          </div>
                        </div>
                      </div>
                      
                      <div class="loading-details" v-else-if="loadingDetails">
                        <i class="fas fa-spinner fa-spin"></i>
                        {{ $t('reports.loading_details') }}
                      </div>
                    </div>
                  </td>
                </tr>
              </template>
              <!-- 合计行 -->
              <tr class="total-row">
                                  <td><strong>{{ $t('common.total') }}</strong></td>
                <td><strong>{{ formatNumber(totalBuyVolume) }}</strong></td>
                <td><strong>{{ formatNumber(totalSellVolume) }}</strong></td>
                <td><strong>{{ formatNumber(totalReversalVolume) }}</strong></td>
                <td>-</td>
                <td>-</td>
                <td class="total-income" :class="getIncomeClass(totalActualIncome)">
                  <strong>{{ formatCurrency(totalActualIncome) }}</strong>
                </td>
                <td class="total-spread-income" :class="getIncomeClass(totalSpreadIncome)">
                  <strong>{{ formatCurrency(totalSpreadIncome) }}</strong>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 无数据提示 -->
      <div class="no-data-container" v-else-if="!loading">
        <div class="no-data-card">
          <i class="fas fa-chart-line fa-3x text-muted"></i>
          <h4>{{ $t('reports.no_data') }}</h4>
          <p>{{ $t('reports.no_income_data_today') }}</p>
        </div>
      </div>
    </div>

    <!-- 错误提示 -->
    <div class="alert alert-danger" v-if="error">
      <i class="fas fa-exclamation-triangle"></i>
      {{ error }}
    </div>
  </div>
</template>

<script>
// import { useUserStore } from '@/stores/user'
import api from '@/services/api'
import CurrencyFlag from '@/components/CurrencyFlag.vue'
import { getCurrencyName, getCurrencyDisplayName } from '@/utils/currencyTranslator'

export default {
  name: 'IncomeQueryView',
  
  components: {
    CurrencyFlag
  },
  
  data() {
    return {
      loading: false,
      error: null,
      reportData: null,
      expandedCurrency: null,
      currencyDetails: {},
      loadingDetails: false,
      // 分页数据
      paginatedTransactions: {},
      pageSize: 20, // 每页显示记录数
      // 勾选状态和动态计算
      selectedTransactions: {}, // 存储勾选的交易：{ currencyCode: { transactionNo: transaction } }
      showSelectedSummary: false // 是否显示勾选汇总
    }
  },
  
  computed: {
    currentUser() {
      // 从localStorage获取用户信息
      const userStr = localStorage.getItem('user')
      return userStr ? JSON.parse(userStr) : null
    },
    
    // 总买入量
    totalBuyVolume() {
      if (!this.reportData || !this.reportData.currencies) return 0
      return this.reportData.currencies.reduce((sum, currency) => sum + (currency.total_buy || 0), 0)
    },
    
    // 总卖出量
    totalSellVolume() {
      if (!this.reportData || !this.reportData.currencies) return 0
      return this.reportData.currencies.reduce((sum, currency) => sum + (currency.total_sell || 0), 0)
    },
    
    // 总冲正金额
    totalReversalVolume() {
      if (!this.reportData || !this.reportData.currencies) return 0
      return this.reportData.currencies.reduce((sum, currency) => sum + (currency.reversal_amount || 0), 0)
    },
    
    // 总实际收入
    totalActualIncome() {
      if (!this.reportData || !this.reportData.currencies) return 0
      return this.reportData.currencies.reduce((sum, currency) => sum + (currency.income || 0), 0)
    },
    
    // 总点差收入
    totalSpreadIncome() {
      if (!this.reportData || !this.reportData.currencies) return 0
      return this.reportData.currencies.reduce((sum, currency) => sum + (currency.spread_income || 0), 0)
    },
    
    // 勾选项目的动态计算
    selectedCount() {
      let count = 0
      Object.values(this.selectedTransactions).forEach(currencyTxs => {
        count += Object.keys(currencyTxs).length
      })
      return count
    },
    
    selectedForeignTotal() {
      let total = 0
      Object.values(this.selectedTransactions).forEach(currencyTxs => {
        Object.values(currencyTxs).forEach(tx => {
          total += parseFloat(tx.amount || 0)
        })
      })
      return total
    },
    
    selectedLocalTotal() {
      let total = 0
      Object.values(this.selectedTransactions).forEach(currencyTxs => {
        Object.values(currencyTxs).forEach(tx => {
          total += parseFloat(tx.local_amount || 0)
        })
      })
      return total
    },
    
    // 是否显示勾选汇总
    hasSelectedTransactions() {
      return this.selectedCount > 0
    }
  },
  
  mounted() {
    this.loadData()
  },
  
  methods: {
    async loadData() {
      this.loading = true
      this.error = null
      
      try {
        const response = await api.get('/reports/income')
        
        if (response.data.success) {
          this.reportData = response.data.data
        } else {
          this.error = this.$t('reports.load_failed')
        }
      } catch (error) {
        console.error('Load income report error:', error)
        this.error = this.$t('reports.load_failed')
      } finally {
        this.loading = false
      }
    },
    
    refreshData() {
      this.loadData()
    },
    
    // 勾选处理方法
    toggleTransactionSelection(currencyCode, transaction) {
      if (!this.selectedTransactions[currencyCode]) {
        // Vue 3: 直接赋值即可触发响应式更新
        this.selectedTransactions[currencyCode] = {}
      }
      
      const txKey = transaction.transaction_no
      if (this.selectedTransactions[currencyCode][txKey]) {
        // Vue 3: 使用delete操作符删除属性
        delete this.selectedTransactions[currencyCode][txKey]
        // 如果币种下没有选中项了，删除整个币种
        if (Object.keys(this.selectedTransactions[currencyCode]).length === 0) {
          delete this.selectedTransactions[currencyCode]
        }
      } else {
        // Vue 3: 直接赋值即可触发响应式更新
        this.selectedTransactions[currencyCode][txKey] = transaction
      }
    },
    
    // 检查交易是否被选中
    isTransactionSelected(currencyCode, transaction) {
      return !!(this.selectedTransactions[currencyCode] && 
                this.selectedTransactions[currencyCode][transaction.transaction_no])
    },
    
    // 全选/取消全选当前页面的交易
    toggleAllCurrentPage(currencyCode) {
      const transactions = this.getCurrentPageTransactions(currencyCode)
      if (!transactions || transactions.length === 0) return
      
      const allSelected = transactions.every(tx => this.isTransactionSelected(currencyCode, tx))
      
      if (allSelected) {
        // 取消全选
        transactions.forEach(tx => {
          if (this.isTransactionSelected(currencyCode, tx)) {
            this.toggleTransactionSelection(currencyCode, tx)
          }
        })
      } else {
        // 全选
        transactions.forEach(tx => {
          if (!this.isTransactionSelected(currencyCode, tx)) {
            this.toggleTransactionSelection(currencyCode, tx)
          }
        })
      }
    },
    
    // 检查当前页面是否全选
    isCurrentPageAllSelected(currencyCode) {
      const transactions = this.getCurrentPageTransactions(currencyCode)
      if (!transactions || transactions.length === 0) return false
      
      return transactions.every(tx => this.isTransactionSelected(currencyCode, tx))
    },
    
    // 清空所有选中项
    clearAllSelections() {
      this.selectedTransactions = {}
    },
    
    // 格式化有符号金额
    formatSignedAmount(amount) {
      const num = parseFloat(amount) || 0
      const formatted = this.formatNumber(Math.abs(num))
      return num >= 0 ? `+${formatted}` : `-${formatted}`
    },
    
    // 【新增】期初余额相关方法
    formatBalanceAmount(currencyCode, type) {
      const details = this.currencyDetails[currencyCode]
      if (!details || !details.balance_summary) return '0.00'
      
      const amount = details.balance_summary[type === 'opening' ? 'opening_balance' : 'current_balance'] || 0
      return this.formatNumber(Math.abs(amount))
    },
    
    getCurrentBalanceClass(currencyCode) {
      const details = this.currencyDetails[currencyCode]
      if (!details || !details.balance_summary) return 'text-muted'
      
      const currentBalance = details.balance_summary.current_balance || 0
      if (currentBalance > 0) return 'text-success'
      if (currentBalance < 0) return 'text-danger'
      return 'text-muted'
    },
    
    formatBalanceChange(currencyCode) {
      const details = this.currencyDetails[currencyCode]
      if (!details || !details.balance_summary) return this.$t('common.no_change')
      
      const netChange = details.balance_summary.net_change || 0
      if (netChange === 0) return this.$t('common.no_change')
      
      // 【修正】净变动计算：当前余额 - 期初余额
      const openingBalance = details.balance_summary.opening_balance || 0
      const currentBalance = details.balance_summary.current_balance || 0
      const actualNetChange = currentBalance - openingBalance
      
      if (actualNetChange === 0) return this.$t('common.no_change')
      
      const sign = actualNetChange > 0 ? '+' : ''
      return `${sign}${this.formatNumber(actualNetChange)}`
    },
    
    getBalanceChangeClass(currencyCode) {
      const details = this.currencyDetails[currencyCode]
      if (!details || !details.balance_summary) return 'text-muted'
      
      // 【修正】净变动计算：当前余额 - 期初余额
      const openingBalance = details.balance_summary.opening_balance || 0
      const currentBalance = details.balance_summary.current_balance || 0
      const actualNetChange = currentBalance - openingBalance
      
      if (actualNetChange > 0) return 'text-success'
      if (actualNetChange < 0) return 'text-danger'
      return 'text-muted'
    },
    
    getPeriodMethodText(currencyCode) {
      const details = this.currencyDetails[currencyCode]
      if (!details) return ''
      
      return details.period_balance_method === 'EODBalanceVerification' ? this.$t('common.balance_method_new') : this.$t('common.balance_method_traditional')
    },
    
    getPeriodMethodTooltip(currencyCode) {
      const details = this.currencyDetails[currencyCode]
      if (!details) return ''
      
      const source = details.opening_balance_source || ''
      
      return `${this.$t('common.balance_method_tooltip')}: ${this.getPeriodMethodText(currencyCode)}\n${this.$t('common.data_source')}: ${source}`
    },

    
    formatTimeRange(startTime, endTime) {
      const start = new Date(startTime)
      const end = new Date(endTime)
      
      const formatDate = (date) => {
        return date.toLocaleDateString(this.$i18n.locale, {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit'
        })
      }
      
      const formatTime = (date) => {
        return date.toLocaleTimeString(this.$i18n.locale, {
          hour: '2-digit',
          minute: '2-digit'
        })
      }
      
      const startDate = formatDate(start)
      const endDate = formatDate(end)
      
      if (startDate === endDate) {
        return `${startDate} ${formatTime(start)} - ${formatTime(end)}`
      } else {
        return `${startDate} ${formatTime(start)} - ${endDate} ${formatTime(end)}`
      }
    },
    
    formatNumber(value) {
      if (value === null || value === undefined || value === 0) return '0'
      return new Intl.NumberFormat(this.$i18n.locale, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(value)
    },
    
    formatCurrency(value) {
      if (value === null || value === undefined || value === 0) return '0.00'
      return new Intl.NumberFormat(this.$i18n.locale, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(value)
    },
    
    formatRate(value) {
      if (value === null || value === undefined || value === 0) return '-'
      return new Intl.NumberFormat(this.$i18n.locale, {
        minimumFractionDigits: 4,
        maximumFractionDigits: 4
      }).format(value)
    },
    
    getIncomeClass(income) {
      if (income > 0) return 'text-success'
      if (income < 0) return 'text-danger'
      return 'text-muted'
    },
    
    getCurrencyDisplayName(currency) {
      if (!currency) return ''
      
      // 使用新的币种显示函数
      return getCurrencyDisplayName(currency.currency_code, currency)
    },
    
    getCurrencyName(currencyCode) {
      return getCurrencyName(currencyCode)
    },
    
    async toggleCurrencyDetails(currencyCode) {
      if (this.expandedCurrency === currencyCode) {
        this.expandedCurrency = null
      } else {
        // 切换到新币种时，清除之前的所有勾选项目
        this.clearAllSelections()
        
        this.expandedCurrency = currencyCode
        if (!this.currencyDetails[currencyCode]) {
          await this.loadCurrencyDetails(currencyCode)
        }
      }
    },
    
    async checkPermissions() {
      try {
        const response = await api.get('/reports/check-permissions')
        if (response.data.success) {
          console.log('用户权限信息:', response.data.data)
          return response.data.data
        }
      } catch (error) {
        console.error('权限检查失败:', error)
        return null
      }
    },
    
    async loadCurrencyDetails(currencyCode) {
      this.loadingDetails = true
      try {
        console.log('🔍 开始加载币种明细:', currencyCode)
        console.log('🔑 Token存在:', !!localStorage.getItem('token'))
        console.log('👤 当前用户:', this.currentUser)
        
        const response = await api.get(`/reports/income/currency/${currencyCode}/transactions`)
        
        if (response.data.success) {
          this.currencyDetails[currencyCode] = response.data.data
          this.initializePagination(currencyCode)
          console.log('✅ 明细加载成功')
        } else {
          console.error('❌ API返回失败:', response.data.message)
          this.error = response.data.message || this.$t('reports.load_details_failed')
        }
      } catch (error) {
        console.error('❌ 请求失败:', error)
        console.error('📋 错误详情:', {
          status: error.response?.status,
          statusText: error.response?.statusText,
          message: error.response?.data?.message,
          url: error.config?.url,
          headers: error.config?.headers
        })
        
        if (error.response?.status === 401) {
          // 先测试其他API是否工作
          console.log('🧪 测试其他API是否正常...')
          this.testOtherApis()
          
          this.error = `认证失败！URL: ${error.config?.url}，状态码: ${error.response?.status}。请检查后端API是否正常工作。`
        } else if (error.response?.status === 403) {
          // 权限不足时，检查用户权限并显示详细信息
          const permInfo = await this.checkPermissions()
          if (permInfo) {
            this.error = `权限不足！当前用户：${permInfo.username}，拥有权限：${permInfo.permissions.join(', ') || '无'}。查看交易明细需要"分支管理"或"系统管理"权限。`
          } else {
            this.error = '权限不足，需要分支管理或系统管理权限才能查看交易明细'
          }
        } else if (error.response?.status === 404) {
          this.error = `API接口不存在: ${error.config?.url}`
        } else {
          this.error = error.response?.data?.message || `请求失败 (${error.response?.status}): ${error.response?.statusText}`
        }
      } finally {
        this.loadingDetails = false
      }
    },
    
    formatDateTime(dateTime) {
      if (!dateTime) return ''
      const date = new Date(dateTime)
      return date.toLocaleString(this.$i18n.locale, {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    },
    
    getTransactionTypeClass(type) {
      switch (type) {
        case 'buy':
          return 'type-buy'
        case 'sell':
          return 'type-sell'
        default:
          return 'type-other'
      }
    },
    
    getTransactionTypeText(type) {
      switch (type) {
        case 'buy':
          return this.$t('reports.buy')
        case 'sell':
          return this.$t('reports.sell')
        case 'reversal':
          return this.$t('reports.reversal_amount')
        default:
          return type
      }
    },

    
    async testOtherApis() {
      console.log('🔍 开始测试其他API...')
      
      // 测试1: 权限检查API
      try {
        const permResponse = await api.get('/reports/check-permissions')
        console.log('✅ 权限检查API正常:', permResponse.data)
      } catch (error) {
        console.error('❌ 权限检查API失败:', error.response?.status, error.response?.data)
      }
      
      // 测试2: 收入报表API
      try {
        const incomeResponse = await api.get('/reports/income')
        console.log('✅ 收入报表API正常:', incomeResponse.data.success)
      } catch (error) {
        console.error('❌ 收入报表API失败:', error.response?.status, error.response?.data)
      }
      
      // 测试3: 健康检查API
      try {
        const healthResponse = await api.get('/reports/health')
        console.log('✅ 健康检查API正常:', healthResponse.data)
      } catch (error) {
        console.error('❌ 健康检查API失败:', error.response?.status, error.response?.data)
      }
      
      // 测试4: 认证测试API
      try {
        const authTestResponse = await api.get('/reports/test-auth')
        console.log('✅ 认证测试API正常:', authTestResponse.data)
      } catch (error) {
        console.error('❌ 认证测试API失败:', error.response?.status, error.response?.data)
      }
      
      // 测试5: 简化收入测试API
      try {
        const incomeTestResponse = await api.get('/reports/test-income')
        console.log('✅ 简化收入测试API正常:', incomeTestResponse.data)
      } catch (error) {
        console.error('❌ 简化收入测试API失败:', error.response?.status, error.response?.data)
      }
      
      // 测试6: 简化币种测试API
      try {
        const currencyTestResponse = await api.get('/reports/test-currency/CNY')
        console.log('✅ 简化币种测试API正常:', currencyTestResponse.data)
      } catch (error) {
        console.error('❌ 简化币种测试API失败:', error.response?.status, error.response?.data)
      }
    },

    // 新增方法：紧凑显示和分页功能
    initializePagination(currencyCode) {
      if (!this.currencyDetails[currencyCode]) return
      
      const transactions = this.currencyDetails[currencyCode].transactions || []
      // Vue 3兼容性：直接赋值而不是使用$set
      this.paginatedTransactions[currencyCode] = {
        currentPage: 1,
        totalCount: transactions.length,
        transactions: transactions
      }
    },

    getCurrentPageTransactions(currencyCode) {
      const pagination = this.paginatedTransactions[currencyCode]
      if (!pagination) return []
      
      const start = (pagination.currentPage - 1) * this.pageSize
      const end = start + this.pageSize
      return pagination.transactions.slice(start, end)
    },

    needsPagination(currencyCode) {
      const pagination = this.paginatedTransactions[currencyCode]
      return pagination && pagination.totalCount > this.pageSize
    },

    getCurrentPage(currencyCode) {
      return this.paginatedTransactions[currencyCode]?.currentPage || 1
    },

    getTotalPages(currencyCode) {
      const pagination = this.paginatedTransactions[currencyCode]
      if (!pagination) return 1
      return Math.ceil(pagination.totalCount / this.pageSize)
    },

    getTotalTransactions(currencyCode) {
      return this.paginatedTransactions[currencyCode]?.totalCount || 0
    },

    prevPage(currencyCode) {
      const pagination = this.paginatedTransactions[currencyCode]
      if (pagination && pagination.currentPage > 1) {
        pagination.currentPage--
      }
    },

    nextPage(currencyCode) {
      const pagination = this.paginatedTransactions[currencyCode]
      if (pagination && pagination.currentPage < this.getTotalPages(currencyCode)) {
        pagination.currentPage++
      }
    },

    // 格式化方法
    getShortTransactionNo(transactionNo) {
      return transactionNo.slice(-8) // 显示后8位
    },

    getCompactDateTime(dateTime) {
      const date = new Date(dateTime)
      return date.toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    },

    formatSignedForeignAmount(amount) {
      // 直接使用原始金额，保持正负符号
      const numAmount = parseFloat(amount)
      const sign = numAmount >= 0 ? '+' : ''  // 负数会自动显示-号
      return `${sign}${this.formatNumber(numAmount)}`
    },

    getTransactionAmountClass(amount) {
      // 根据金额的正负决定颜色
      return parseFloat(amount) >= 0 ? 'amount-positive' : 'amount-negative'
    },

    // 合计计算方法
    formatForeignTotal(currencyCode) {
      const transactions = this.currencyDetails[currencyCode]?.transactions || []
      let total = 0
      
      transactions.forEach(tx => {
        // 直接使用amount的值，因为数据库中已经存储了正确的正负符号
        // buy: 正数（银行买入外币，外币增加）
        // sell: 负数（银行卖出外币，外币减少）  
        // reversal: 根据被冲正的交易类型，amount已经有正确的正负符号
        const amount = parseFloat(tx.amount)
        total += amount
      })
      
      // 对于外币合计，如果是负数表示净卖出，如果是正数表示净买入
      if (total === 0) {
        return `0.00 ${currencyCode}`
      } else if (total > 0) {
        return `${this.$t('exchange.buy')} ${this.formatNumber(total)} ${currencyCode}`
      } else {
        return `${this.$t('exchange.sell')} ${this.formatNumber(Math.abs(total))} ${currencyCode}`
      }
    },

    formatLocalTotal(currencyCode) {
      const transactions = this.currencyDetails[currencyCode]?.transactions || []
      const total = transactions.reduce((sum, tx) => sum + parseFloat(tx.local_amount), 0)
      return this.formatCurrency(total)
    },

    formatForeignPageTotal(currencyCode) {
      const pageTransactions = this.getCurrentPageTransactions(currencyCode)
      let total = 0
      
      pageTransactions.forEach(tx => {
        // 直接使用amount的值，因为数据库中已经存储了正确的正负符号
        const amount = parseFloat(tx.amount)
        total += amount
      })
      
      // 对于外币页面小计，如果是负数表示净卖出，如果是正数表示净买入
      if (total === 0) {
        return `0.00 ${currencyCode}`
      } else if (total > 0) {
        return `${this.$t('exchange.buy')} ${this.formatNumber(total)} ${currencyCode}`
      } else {
        return `${this.$t('exchange.sell')} ${this.formatNumber(Math.abs(total))} ${currencyCode}`
      }
    },

    formatLocalPageTotal(currencyCode) {
      const pageTransactions = this.getCurrentPageTransactions(currencyCode)
      const total = pageTransactions.reduce((sum, tx) => sum + parseFloat(tx.local_amount), 0)
      return this.formatCurrency(total)
    },

    getForeignTotalClass(currencyCode) {
      const transactions = this.currencyDetails[currencyCode]?.transactions || []
      let total = 0
      
      transactions.forEach(tx => {
        // 直接使用amount的值，因为数据库中已经存储了正确的正负符号
        const amount = parseFloat(tx.amount)
        total += amount
      })
      
      return total >= 0 ? 'amount-positive' : 'amount-negative'
    },

    getForeignPageTotalClass(currencyCode) {
      const pageTransactions = this.getCurrentPageTransactions(currencyCode)
      let total = 0
      
      pageTransactions.forEach(tx => {
        // 直接使用amount的值，因为数据库中已经存储了正确的正负符号
        const amount = parseFloat(tx.amount)
        total += amount
      })
      
      return total >= 0 ? 'amount-positive' : 'amount-negative'
    }
  }
}
</script>

<style scoped>
.income-query-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e9ecef;
}

.page-header h2 {
  margin: 0;
  color: #333;
}

.operation-buttons {
  display: flex;
  gap: 10px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 5px;
  transition: all 0.2s;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #0056b3;
}

.btn-success {
  background-color: #28a745;
  color: white;
}

.btn-success:hover:not(:disabled) {
  background-color: #1e7e34;
}

.btn-info {
  background-color: #17a2b8;
  color: white;
}

.btn-info:hover:not(:disabled) {
  background-color: #138496;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 20px;
}

.spinner-border {
  width: 3rem;
  height: 3rem;
  margin-bottom: 20px;
}

.content-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.report-info {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
}

.info-card {
  padding-top: 5px;
}

.info-inline {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  margin-top: 15px;
  align-items: center;
}

.info-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 1em;
}

.info-item strong {
  color: #6c757d;
  font-weight: 600;
}

.info-item span {
  color: #333;
}

.income-amount {
  font-size: 1.2em;
  font-weight: bold;
  color: #28a745;
}

.data-table-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.data-table-container h4 {
  margin: 0;
  padding: 15px 20px;
  background: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
  color: #495057;
}

.table-responsive {
  overflow-x: auto;
}

.table {
  width: 100%;
  margin-bottom: 0;
  background-color: transparent;
  border-collapse: collapse;
}

.table th,
.table td {
  padding: 12px;
  vertical-align: top;
  border-top: 1px solid #dee2e6;
  text-align: left;
}

.table thead th {
  background-color: #f8f9fa;
  border-bottom: 2px solid #dee2e6;
  font-weight: 600;
  color: #495057;
}

.table-striped tbody tr:nth-of-type(odd) {
  background-color: rgba(0, 0, 0, 0.05);
}

.currency-info-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.currency-flag {
  width: 24px;
  height: 16px;
  border-radius: 2px;
  border: 1px solid #ddd;
  flex-shrink: 0;
}

.detail-flag {
  width: 18px;
  height: 12px;
  border-radius: 2px;
  border: 1px solid #ddd;
  flex-shrink: 0;
  margin-right: 5px;
}

.currency-details {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8px;
}

.currency-code {
  font-weight: 600;
  color: #333;
  font-size: 0.95em;
}

.currency-name {
  font-size: 0.85em;
  color: #6c757d;
}

.text-muted {
  color: #6c757d;
}

.text-success {
  color: #28a745;
  font-weight: 600;
}

.text-danger {
  color: #dc3545;
  font-weight: 600;
}

.no-data-container {
  display: flex;
  justify-content: center;
  padding: 60px 20px;
}

.no-data-card {
  text-align: center;
  max-width: 400px;
}

.no-data-card i {
  margin-bottom: 20px;
}

.no-data-card h4 {
  color: #6c757d;
  margin-bottom: 10px;
}

.no-data-card p {
  color: #adb5bd;
  margin: 0;
}

.alert {
  padding: 15px;
  margin-bottom: 20px;
  border: 1px solid transparent;
  border-radius: 4px;
}

.alert-danger {
  color: #721c24;
  background-color: #f8d7da;
  border-color: #f5c6cb;
}

.alert i {
  margin-right: 8px;
}

/* 点差收入公式样式 */
.spread-amount {
  color: #17a2b8;
  font-weight: bold;
}

.formula-info {
  margin-top: 12px;
  padding: 10px 15px;
  background: #e3f2fd;
  border-radius: 6px;
  border-left: 4px solid #2196f3;
}

.formula-text {
  font-size: 0.9em;
  color: #1976d2;
  display: flex;
  align-items: center;
  gap: 8px;
}

.formula-text i {
  color: #2196f3;
}

/* 可点击行样式 */
.currency-row {
  cursor: pointer;
  transition: background-color 0.2s;
}

.currency-row:hover {
  background-color: #f0f8ff !important;
}

.currency-row.expanded {
  background-color: #e3f2fd !important;
}

.detail-arrow {
  margin-left: 8px;
  color: #666;
  transition: transform 0.3s;
  font-size: 0.8em;
}

.detail-arrow.rotated {
  transform: rotate(180deg);
}

/* 明细展开区域样式 */
.details-row {
  background-color: #f8f9fa !important;
}

.details-cell {
  padding: 0 !important;
}

.transaction-details {
  padding: 20px;
  border-top: 2px solid #e9ecef;
}

.details-header {
  margin-bottom: 15px;
  border-bottom: 1px solid #dee2e6;
  padding-bottom: 10px;
}

.details-header h5 {
  margin: 0 0 8px 0;
  color: #495057;
  font-size: 1.1em;
}

.details-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  font-size: 0.9em;
  color: #6c757d;
}

.summary-item strong {
  color: #495057;
}

/* 交易明细容器 */
.transactions-container {
  max-height: 400px;
  overflow-y: auto;
}

.transaction-item {
  border: 1px solid #e9ecef;
  border-radius: 6px;
  margin-bottom: 12px;
  padding: 12px;
  background: white;
}

.transaction-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f1f3f4;
}

.transaction-no {
  font-family: monospace;
  font-weight: bold;
  color: #495057;
  font-size: 0.9em;
}

.transaction-time {
  color: #6c757d;
  font-size: 0.85em;
}

.transaction-type {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.75em;
  font-weight: bold;
  text-transform: uppercase;
}

.type-buy {
  background-color: #d4edda;
  color: #155724;
}

.type-sell {
  background-color: #cce5ff;
  color: #004085;
}

.type-other {
  background-color: #f8f9fa;
  color: #6c757d;
}

.transaction-details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.detail-item label {
  font-size: 0.8em;
  color: #6c757d;
  font-weight: 600;
}

.detail-item span {
  font-size: 0.9em;
  color: #333;
}

.loading-details {
  text-align: center;
  padding: 20px;
  color: #6c757d;
}

.loading-details i {
  margin-right: 8px;
}

/* 移动端响应式样式 */
@media (max-width: 768px) {
  .income-query-page {
    padding: 10px;
  }
  
  .info-inline {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
  
  .info-item {
    width: 100%;
    justify-content: space-between;
  }
  
  .formula-info {
    margin-top: 8px;
    padding: 8px 12px;
  }
  
  .formula-text {
    font-size: 0.8em;
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .table-responsive {
    border: none;
    overflow-x: auto;
  }
  
  .table {
    min-width: 800px;
    font-size: 0.9em;
  }
  
  .table th,
  .table td {
    padding: 8px 6px;
    white-space: nowrap;
  }
  
  .currency-details {
    gap: 4px;
  }
  
  .currency-name {
    font-size: 0.75em;
  }
  
  .details-summary {
    flex-direction: column;
    gap: 8px;
  }
  
  .transaction-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .transaction-details-grid {
    grid-template-columns: 1fr;
    gap: 8px;
  }
  
  .detail-item {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }
}

@media (max-width: 480px) {
  .income-query-page {
    padding: 5px;
  }
  
  .page-header h2 {
    font-size: 1.3em;
  }
  
  .operation-buttons {
    flex-direction: column;
    width: 100%;
  }
  
  .btn {
    width: 100%;
    justify-content: center;
  }
  
  .info-card {
    padding: 10px;
  }
  
  .transaction-details {
    padding: 12px;
  }
  
  .details-header h5 {
    font-size: 1em;
  }
  
  .transaction-item {
    padding: 8px;
  }
}

/* 新增：紧凑布局样式 */
.transaction-details-compact {
  background: #f8f9fa;
  border-radius: 6px;
  overflow: hidden;
  margin: 8px;
}

.details-header-compact {
  background: #e9ecef;
  padding: 10px 15px;
  border-bottom: 1px solid #dee2e6;
}

.details-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.detail-flag {
  width: 20px;
  height: 14px;
}

.currency-title {
  font-weight: 600;
  color: #333;
  flex: 1;
}

.btn-collapse {
  background: none;
  border: none;
  color: #6c757d;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 3px;
  transition: all 0.2s;
}

.btn-collapse:hover {
  background: #dee2e6;
  color: #333;
}

.details-summary-compact {
  display: flex;
  gap: 15px;
  font-size: 0.9em;
}

.summary-compact {
  color: #495057;
}

.transactions-container-compact {
  max-height: 400px;
  overflow-y: auto;
  background: white;
}

.transaction-row-compact {
  border-bottom: 1px solid #f1f3f4;
  transition: background-color 0.2s;
}

.transaction-row-compact:hover {
  background-color: #f8f9fa;
}

.transaction-line {
  display: flex;
  align-items: center;
  padding: 6px 15px;
  font-size: 0.85em;
  gap: 8px;
  line-height: 1.2;
}

.tx-no {
  font-family: monospace;
  color: #6c757d;
  min-width: 70px;
}

.tx-time {
  color: #6c757d;
  min-width: 80px;
}

.tx-separator {
  color: #dee2e6;
}

.tx-type {
  min-width: 40px;
  font-weight: 500;
}

.tx-foreign {
  font-weight: 600;
  min-width: 100px;
}

.tx-rate {
  color: #6c757d;
  min-width: 60px;
}

.tx-equals {
  color: #6c757d;
}

.tx-local {
  font-weight: 500;
  min-width: 80px;
}

.tx-customer {
  color: #495057;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.amount-positive {
  color: #28a745;
}

.amount-negative {
  color: #dc3545;
}

.pagination-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 15px;
  background: #f8f9fa;
  border-top: 1px solid #e9ecef;
  font-size: 0.85em;
}

.pagination-info {
  color: #6c757d;
}

.pagination-buttons {
  display: flex;
  gap: 5px;
}

.btn-page {
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 3px;
  padding: 4px 8px;
  cursor: pointer;
  color: #495057;
  transition: all 0.2s;
}

.btn-page:hover:not(:disabled) {
  background: #e9ecef;
  border-color: #adb5bd;
}

.btn-page:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.subtotal-row {
  background: #f8f9fa;
  border-top: 1px solid #e9ecef;
  padding: 8px 15px;
}

.subtotal-content {
  font-size: 0.9em;
  color: #495057;
}

/* 勾选框样式 */
.checkbox-container {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  position: relative;
}

.checkbox-container input[type="checkbox"] {
  appearance: none;
  width: 16px;
  height: 16px;
  border: 2px solid #dee2e6;
  border-radius: 3px;
  background: white;
  cursor: pointer;
  position: relative;
  transition: all 0.2s;
}

.checkbox-container input[type="checkbox"]:checked {
  background: #007bff;
  border-color: #007bff;
}

.checkbox-container input[type="checkbox"]:checked::before {
  content: "✓";
  position: absolute;
  top: -1px;
  left: 1px;
  color: white;
  font-size: 12px;
  font-weight: bold;
}

.checkbox-container:hover input[type="checkbox"] {
  border-color: #007bff;
}

.checkbox-label {
  font-size: 0.85em;
  color: #495057;
  user-select: none;
}

.transaction-control-row {
  padding: 8px 15px;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
}

.transaction-selected {
  background-color: #e3f2fd !important;
}

.transaction-selected:hover {
  background-color: #bbdefb !important;
}

/* 动态勾选汇总区域样式 */
.selected-summary-compact {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 10px;
  padding: 8px 12px;
  background: #e3f2fd;
  border-radius: 4px;
  font-size: 0.85em;
  border-left: 4px solid #2196f3;
}

.selected-divider {
  width: 1px;
  height: 16px;
  background: #dee2e6;
  margin: 0 5px;
}

.selected-label {
  font-weight: 600;
  color: #1976d2;
}

.selected-count {
  color: #1976d2;
  font-weight: 500;
}

.selected-foreign {
  color: #495057;
}

.selected-local {
  color: #495057;
}

.btn-clear-selections {
  background: none;
  border: none;
  color: #dc3545;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 3px;
  transition: all 0.2s;
  font-size: 0.8em;
}

.btn-clear-selections:hover {
  background: #f8d7da;
  color: #721c24;
}

.subtotal-content strong {
  color: #333;
}

/* 买卖类型样式 */
.type-buy {
  color: #28a745;
}

.type-sell {
  color: #dc3545;
}

/* 合计行样式 */
.total-row {
  background: #e9ecef;
  border-top: 2px solid #dee2e6;
  font-weight: bold;
}

.total-row td {
  padding: 12px 8px;
  vertical-align: middle;
}

.total-income,
.total-spread-income {
  font-size: 1.1em;
  font-weight: bold;
}

/* 【新增】期初余额相关样式 */
.balance-summary-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
  padding: 10px 15px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 6px;
  border: 1px solid #dee2e6;
  font-size: 0.9em;
}

.balance-info {
  color: #495057;
}

.opening-balance {
  color: #6c757d;
  font-weight: 600;
}

.current-balance {
  font-weight: 600;
}

.balance-separator {
  color: #6c757d;
  font-weight: bold;
  font-size: 1.2em;
}

.balance-change {
  font-size: 0.85em;
  font-weight: 500;
  margin-left: 5px;
}

.transaction-summary-row {
  display: flex;
  align-items: center;
  gap: 15px;
  flex-wrap: wrap;
  padding: 0 5px;
}

.period-method-info {
  color: #6c757d;
  font-size: 0.8em;
  cursor: help;
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 4px;
}

.period-method-info:hover {
  color: #495057;
}

.period-method-info i {
  font-size: 0.7em;
}
</style> 
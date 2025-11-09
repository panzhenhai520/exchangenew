<template>
  <div class="local-stock-query-page">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2 class="page-title-bold">
        <font-awesome-icon :icon="['fas', 'coins']" class="me-2" />
        {{ $t('local_stock_query.title') }}
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
      <p>{{ $t('local_stock_query.loading') }}</p>
    </div>

    <div class="content-container" v-else>
      <!-- 查询条件 -->
      <div class="query-header" v-if="stockData">
        <div class="query-info">
          <span class="info-item">
            <strong>{{ $t('local_stock_query.branch') }}:</strong> 
            {{ stockData.branch_name }}
          </span>
          <span class="info-item">
            <strong>{{ $t('local_stock_query.time_range') }}:</strong> 
            {{ formatTimeRange(stockData.start_time, stockData.end_time) }}
          </span>
        </div>
        
        <div class="base-currency-info">
          <div class="currency-section">
            <div class="currency-display">
              <strong>{{ $t('local_stock_query.base_currency') }}:</strong>
              <CurrencyFlag 
                :code="stockData.base_currency_code" 
                :custom-filename="stockData.base_currency_custom_flag_filename"
                class="currency-flag"
              />
              <span class="currency-code">{{ stockData.base_currency_code }}</span>
              <span class="currency-name">{{ getCurrencyDisplayName(stockData) }}</span>
            </div>
            <div class="opening-balance">
              <strong>{{ $t('local_stock_query.opening_balance') }}:</strong>
              <span class="opening-amount">{{ formatNumber(stockData.opening_balance) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 交易明细表 -->
      <div class="transaction-table" v-if="stockData && stockData.transactions.length > 0">
        <div class="table-responsive">
          <table class="table table-striped">
            <thead>
              <tr>
                <th style="width: 15px;" :title="$t('common.select_all')">
                  <input 
                    type="checkbox" 
                    v-model="selectAll"
                    @change="toggleSelectAll"
                    class="form-check-input"
                    :title="$t('common.select_all')"
                  />
                </th>
                <th style="width: 55px;">{{ $t('local_stock_query.transaction_time') }}</th>
                <th style="width: 35px;">{{ $t('local_stock_query.transaction_type') }}</th>
                <th class="amount-column" style="width: 60px;">{{ $t('local_stock_query.amount_change') }}</th>
                <th v-if="!isMobile" style="width: 300px;">{{ $t('local_stock_query.transaction_content') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="transaction in stockData.transactions" :key="transaction.id">
                <td>
                  <input 
                    type="checkbox" 
                    v-model="selectedTransactions"
                    :value="transaction.id"
                    @change="calculateSelectedTotal"
                    class="form-check-input"
                  />
                </td>
                <td>{{ formatTransactionTime(transaction.transaction_time) }}</td>
                <td class="transaction-type" 
                    :class="{ 'mobile-clickable': isMobile }"
                    @click="isMobile ? showTransactionDetail(transaction) : null"
                    :title="isMobile ? formatTransactionDetail(transaction) : ''">
                  <strong>{{ getTransactionTypeText(transaction.type) }}</strong>
                </td>
                <td :class="getAmountChangeClass(transaction.local_amount_change)" class="amount-column">
                  {{ formatSignedNumber(transaction.local_amount_change) }}
                </td>
                <td v-if="!isMobile" class="transaction-detail">
                  {{ formatTransactionDetail(transaction) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        
        <!-- 表格下方的合计行 -->
        <div class="table-summary">
          <div class="summary-row">
            <span class="summary-label">{{ $t('local_stock_query.change_total') }}:</span>
            <span class="summary-amount">{{ formatSignedNumber(selectedTotal) }}</span>
          </div>
        </div>
      </div>

      <!-- 汇总信息 -->
      <div class="summary-section" v-if="stockData">
        <div class="calculation-steps">
          <div class="step-row">
            <span class="step-label">{{ $t('local_stock_query.opening_balance') }}:</span>
            <span class="step-value">{{ formatNumber(stockData.opening_balance) }}</span>
          </div>
          
          <div class="step-row">
            <span class="step-label">{{ $t('local_stock_query.change_total') }}:</span>
            <span class="step-value">{{ formatSignedNumber(selectedTotal) }}</span>
          </div>
          
          <div class="calculation-formula">
            <span class="formula-text">
              {{ formatNumber(stockData.opening_balance) }} 
              <span class="operator">{{ selectedTotal >= 0 ? '+' : '-' }}</span>
              {{ formatNumber(Math.abs(selectedTotal)) }}
              <span class="equals">=</span>
              <span class="result">{{ formatNumber(stockData.opening_balance + selectedTotal) }}</span>
            </span>
          </div>
          

        </div>
      </div>

      <!-- 无数据提示 -->
      <div class="no-data-container" v-else-if="!loading">
        <div class="no-data-card">
          <i class="fas fa-coins fa-3x text-muted"></i>
          <h4>{{ $t('local_stock_query.no_data') }}</h4>
          <p>{{ $t('local_stock_query.no_data_today') }}</p>
        </div>
      </div>
    </div>

    <!-- 错误提示 -->
    <div class="alert alert-danger" v-if="error">
      <i class="fas fa-exclamation-triangle"></i>
      {{ error }}
    </div>
    
    <!-- 手机端浮动提示 -->
    <div v-if="showToast" class="mobile-toast" @click="hideToast">
      <div class="toast-content">
        <div class="toast-header">
          <span class="toast-title">交易详情</span>
          <button class="toast-close" @click="hideToast">&times;</button>
        </div>
        <div class="toast-body">
          {{ toastMessage }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'
import CurrencyFlag from '@/components/CurrencyFlag.vue'
import { getCurrencyName, getCurrencyDisplayName } from '@/utils/currencyTranslator'

export default {
  name: 'LocalStockQueryView',
  
  components: {
    CurrencyFlag
  },
  
  data() {
    return {
      loading: false,
      error: null,
      stockData: null,
      selectedTransactions: [],
      selectAll: true,
      selectedTotal: 0,
      isMobile: false,
      showToast: false,
      toastMessage: ''
    }
  },
  
  mounted() {
    this.checkMobile()
    this.loadData()
    
    // 监听窗口大小变化
    window.addEventListener('resize', this.checkMobile)
  },
  
  beforeUnmount() {
    // 移除事件监听器
    window.removeEventListener('resize', this.checkMobile)
  },
  
  methods: {
    getCurrencyDisplayName(stockData) {
      if (!stockData) return ''
      
      // 使用新的币种显示函数
      return getCurrencyDisplayName(stockData.base_currency_code, stockData)
    },
    
    getCurrencyName,
    
    checkMobile() {
      this.isMobile = window.innerWidth <= 768
    },
    
    showTransactionDetail(transaction) {
      const detail = this.formatTransactionDetail(transaction)
      this.toastMessage = detail
      this.showToast = true
      
      // 3秒后自动隐藏
      setTimeout(() => {
        this.hideToast()
      }, 3000)
    },
    
    hideToast() {
      this.showToast = false
      this.toastMessage = ''
    },
    
    async loadData() {
      this.loading = true
      this.error = null
      
      try {
        const response = await api.get('/reports/local-stock')
        
        if (response.data.success) {
          this.stockData = response.data.data
          
          // 默认全选
          this.selectedTransactions = this.stockData.transactions.map(t => t.id)
          this.selectAll = true
          this.calculateSelectedTotal()
        } else {
          this.error = response.data.message || this.$t('local_stock_query.load_failed')
        }
      } catch (error) {
        console.error('Load local stock report error:', error)
        this.error = this.$t('local_stock_query.load_failed')
      } finally {
        this.loading = false
      }
    },
    
    refreshData() {
      this.loadData()
    },
    
    toggleSelectAll() {
      if (this.selectAll) {
        this.selectedTransactions = this.stockData.transactions.map(t => t.id)
      } else {
        this.selectedTransactions = []
      }
      this.calculateSelectedTotal()
    },
    
    calculateSelectedTotal() {
      if (!this.stockData || !this.stockData.transactions) {
        this.selectedTotal = 0
        return
      }
      
      this.selectedTotal = this.stockData.transactions
        .filter(t => this.selectedTransactions.includes(t.id))
        .reduce((sum, t) => sum + (parseFloat(t.local_amount_change) || 0), 0)
      
      // 更新全选状态
      this.selectAll = this.selectedTransactions.length === this.stockData.transactions.length
    },
    
    formatTimeRange(startTime, endTime) {
      if (!startTime || !endTime) return ''
      
      const formatDateTime = (dateTime) => {
        if (!dateTime) return ''
        const date = new Date(dateTime)
        const year = date.getFullYear()
        const month = String(date.getMonth() + 1).padStart(2, '0')
        const day = String(date.getDate()).padStart(2, '0')
        const hour = String(date.getHours()).padStart(2, '0')
        const minute = String(date.getMinutes()).padStart(2, '0')
        return `${year}-${month}-${day} ${hour}:${minute}`
      }
      
      return `${formatDateTime(startTime)} - ${formatDateTime(endTime)}`
    },
    
    formatTransactionTime(transactionTime) {
      if (!transactionTime) return ''
      const date = new Date(transactionTime)
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      const hour = String(date.getHours()).padStart(2, '0')
      const minute = String(date.getMinutes()).padStart(2, '0')
      return `${year}-${month}-${day} ${hour}:${minute}`
    },
    
    getTransactionTypeText(type) {
      const typeMap = {
        'buy': this.$t('local_stock_query.buy_foreign'),
        'sell': this.$t('local_stock_query.sell_foreign'),
        'balance_adjustment_increase': this.$t('local_stock_query.balance_adjustment_increase'),
        'balance_adjustment_decrease': this.$t('local_stock_query.balance_adjustment_decrease'),
        'balance_adjustment': this.$t('local_stock_query.balance_adjustment_increase'),
        'adjust_balance': this.$t('local_stock_query.balance_adjustment_increase'),
        'initial_balance': this.$t('local_stock_query.initial_balance'),
        'cash_handover': this.$t('local_stock_query.cash_handover'),
        'reversal': this.$t('local_stock_query.reversal')
      }
      return typeMap[type] || type
    },
    
    formatTransactionDetail(transaction) {
      const amount = parseFloat(transaction.amount) || 0;
      const rate = parseFloat(transaction.rate) || 0;
      const transactionNo = transaction.transaction_no || '';
      const originalTransactionNo = transaction.original_transaction_no || '';
      const foreignCurrencyCode = transaction.foreign_currency_code || '';
      
      // 根据实际的交易类型显示
      switch (transaction.type) {
        case 'adjust_balance':
        case 'balance_adjustment_increase':
        case 'balance_adjustment_decrease':
          // 余额调节 - 显示本币金额
          if (amount > 0) {
            return `${this.$t('local_stock_query.transaction_description.document_no')}${transactionNo} ${this.$t('local_stock_query.transaction_description.balance_adjustment_increase')} +${amount.toFixed(2)}`;
          } else if (amount < 0) {
            return `${this.$t('local_stock_query.transaction_description.document_no')}${transactionNo} ${this.$t('local_stock_query.transaction_description.balance_adjustment_decrease')} ${amount.toFixed(2)}`;
          } else {
            return `${this.$t('local_stock_query.transaction_description.document_no')}${transactionNo} ${this.$t('local_stock_query.transaction_description.balance_adjustment')}`;
          }
          
        case 'sell':
          // 卖出外币 - 显示外币金额和外币代码
          return `${this.$t('local_stock_query.transaction_description.document_no')}${transactionNo} ${this.$t('local_stock_query.transaction_description.sell_foreign', {rate: rate, amount: Math.abs(amount).toFixed(2)})}${foreignCurrencyCode}`;
          
        case 'buy':
          // 买入外币 - 显示外币金额和外币代码
          return `${this.$t('local_stock_query.transaction_description.document_no')}${transactionNo} ${this.$t('local_stock_query.transaction_description.buy_foreign', {rate: rate, amount: Math.abs(amount).toFixed(2)})}${foreignCurrencyCode}`;
          
        case 'reversal':
          // 冲正交易 - 显示外币金额和外币代码
          if (originalTransactionNo) {
            return `${this.$t('local_stock_query.transaction_description.document_no')}${transactionNo} ${this.$t('local_stock_query.transaction_description.reversal', {amount: Math.abs(amount).toFixed(2)})}${foreignCurrencyCode}`;
          } else {
            return `${this.$t('local_stock_query.transaction_description.document_no')}${transactionNo} ${this.$t('local_stock_query.transaction_description.reversal', {amount: Math.abs(amount).toFixed(2)})}${foreignCurrencyCode}`;
          }
          
        default:
          // 其他类型
          return `${this.$t('local_stock_query.transaction_description.document_no')}${transactionNo} ${transaction.type} ${Math.abs(amount).toFixed(2)}${foreignCurrencyCode}`;
      }
    },
    
    getAmountChangeClass(amount) {
      const value = parseFloat(amount)
      if (value > 0) return 'text-success'
      if (value < 0) return 'text-danger'
      return ''
    },
    

    
    formatNumber(value) {
      if (value === null || value === undefined || value === 0) return '0.00'
      return new Intl.NumberFormat(this.$i18n.locale, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(value)
    },
    
    formatSignedNumber(value) {
      if (value === null || value === undefined || value === 0) return '0.00'
      const formatted = new Intl.NumberFormat(this.$i18n.locale, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(Math.abs(value))
      return value >= 0 ? `+${formatted}` : `-${formatted}`
    }
  }
}
</script>

<style scoped>
.local-stock-query-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  color: #2c3e50;
}

.operation-buttons {
  display: flex;
  gap: 10px;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}

.query-header {
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.query-info {
  display: flex;
  flex-wrap: wrap;
  gap: 30px;
  margin-bottom: 15px;
}

.info-item {
  white-space: nowrap;
}

.base-currency-info {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.currency-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.currency-display {
  display: flex;
  align-items: center;
  gap: 8px;
}

.currency-flag {
  width: 24px;
  height: 18px;
}

.currency-code {
  font-weight: bold;
  color: #2c3e50;
}

.currency-name {
  color: #6c757d;
}

.opening-balance {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 4px solid #dee2e6;
}

.opening-amount {
  font-family: 'Consolas', 'Monaco', 'Roboto Mono', 'Liberation Mono', 'Courier New', monospace;
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  letter-spacing: 0.5px;
  text-align: right;
}

.transaction-table {
  margin-bottom: 20px;
  overflow-x: auto;
  min-width: 700px;
}

.table {
  background: white;
  border-radius: 8px 8px 0 0;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  margin-bottom: 0;
  min-width: 700px;
  table-layout: fixed;
}

.table th {
  background: #f8f9fa;
  border-bottom: 2px solid #dee2e6;
  font-weight: 600;
  color: #495057;
}

.table td {
  vertical-align: middle;
  padding: 10px 8px;
}

.amount-column {
  text-align: right;
  width: 150px;
  font-family: 'Consolas', 'Monaco', 'Roboto Mono', 'Liberation Mono', 'Courier New', monospace;
  font-weight: 600;
  font-size: 16px;
  letter-spacing: 0.5px;
}

.transaction-type {
  font-size: 14px;
  font-weight: 600;
  color: #495057;
}

.transaction-detail {
  font-size: 14px;
  color: #6c757d;
  word-break: break-word;
  line-height: 1.4;
}

.table-summary {
  border-top: 2px solid #dee2e6;
  background: #f8f9fa;
  padding: 15px 20px;
  margin-top: 0;
  border-left: 1px solid #dee2e6;
  border-right: 1px solid #dee2e6;
  border-bottom: 1px solid #dee2e6;
  border-radius: 0 0 8px 8px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
}

.summary-label {
  color: #495057;
}

.summary-amount {
  color: #2c3e50;
  font-family: 'Consolas', 'Monaco', 'Roboto Mono', 'Liberation Mono', 'Courier New', monospace;
  font-weight: 600;
  font-size: 16px;
  text-align: right;
  width: 150px;
  letter-spacing: 0.5px;
}

.summary-section {
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  padding: 20px;
  margin-top: 20px;
}

.summary-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 15px;
}

.summary-label {
  color: #495057;
}

.summary-value {
  color: #2c3e50;
  font-family: monospace;
}

.calculation-steps {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.step-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  border-radius: 6px;
  background: #f8f9fa;
  border-left: 4px solid #dee2e6;
}

.step-row.theoretical-balance {
  background: #e7f3ff;
  border-left-color: #007bff;
}

.step-row.actual-balance {
  background: #f0f9ff;
  border-left-color: #17a2b8;
}

.step-label {
  font-weight: 600;
  color: #495057;
  min-width: 120px;
}

.step-value {
  font-family: 'Consolas', 'Monaco', 'Roboto Mono', 'Liberation Mono', 'Courier New', monospace;
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
  margin-right: 10px;
  letter-spacing: 0.5px;
}

.step-calculation {
  font-size: 14px;
  color: #6c757d;
  font-family: 'Consolas', 'Monaco', 'Roboto Mono', 'Liberation Mono', 'Courier New', monospace;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.calculation-formula {
  margin: 20px 0;
  padding: 20px;
  background: linear-gradient(135deg, #fff3cd 0%, #fef6d8 100%);
  border: 2px solid #ffc107;
  border-radius: 12px;
  text-align: right;
  box-shadow: 0 4px 8px rgba(255, 193, 7, 0.2);
}

.formula-text {
  font-family: 'Consolas', 'Monaco', 'Roboto Mono', 'Liberation Mono', 'Courier New', monospace;
  font-size: 20px;
  font-weight: 700;
  color: #856404;
  letter-spacing: 1px;
  line-height: 1.5;
}

.formula-text .operator {
  margin: 0 12px;
  color: #007bff;
  font-size: 24px;
  font-weight: 900;
}

.formula-text .equals {
  margin: 0 15px;
  color: #28a745;
  font-size: 26px;
  font-weight: 900;
}

.formula-text .result {
  color: #dc3545;
  font-size: 22px;
  font-weight: 900;
  text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
}

.comparison-result {
  margin-top: 20px;
  padding: 15px;
  background: #e9ecef;
  border-radius: 8px;
  text-align: center;
  border: 2px solid #dee2e6;
}

.comparison-text {
  font-weight: 600;
  color: #495057;
  margin-right: 10px;
}

.comparison-formula {
  font-family: monospace;
  font-size: 18px;
  font-weight: bold;
  color: #2c3e50;
}

.comparison-operator {
  font-size: 24px;
  font-weight: bold;
  color: #007bff;
  margin: 0 15px;
  display: inline-block;
}

.no-data-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.no-data-card {
  text-align: center;
  padding: 40px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #dee2e6;
}

.no-data-card h4 {
  color: #6c757d;
  margin: 20px 0 10px 0;
}

.no-data-card p {
  color: #6c757d;
  margin: 0;
}

.text-success {
  color: #28a745 !important;
}

.text-danger {
  color: #dc3545 !important;
}

.transaction-type {
  font-size: 14px;
  font-weight: bold;
  color: #2c3e50;
  margin-bottom: 4px;
  white-space: nowrap;
}

.transaction-detail {
  font-size: 12px;
  color: #6c757d;
  line-height: 1.3;
  white-space: nowrap;
  overflow: visible;
  text-overflow: clip;
  width: 100%;
}

/* 统一金额字体样式 */
.amount-text {
  font-family: 'Consolas', 'Monaco', 'Roboto Mono', 'Liberation Mono', 'Courier New', monospace;
  font-weight: 600;
  font-size: 16px;
  letter-spacing: 0.5px;
}

/* 手机端样式 */
@media (max-width: 768px) {
  .mobile-clickable {
    cursor: pointer;
    position: relative;
    transition: background-color 0.2s ease;
  }
  
  .mobile-clickable:hover {
    background-color: rgba(0, 123, 255, 0.1);
  }
  
  .mobile-clickable:active {
    background-color: rgba(0, 123, 255, 0.2);
  }
  
  /* 确保表格在手机端不会出现横向滚动 */
  .transaction-table {
    overflow-x: hidden;
    width: 100%;
  }
  
  .table-responsive {
    overflow-x: hidden !important;
    border: none !important;
    width: 100%;
  }
  
  .table {
    font-size: 12px;
    table-layout: fixed;
    width: 100%;
    margin: 0;
  }
  
  .table th,
  .table td {
    padding: 2px 1px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    vertical-align: middle;
  }
  
  /* 确保所有表头字体一致 */
  .table th {
    font-size: 12px !important;
    font-weight: 600 !important;
    color: #333 !important;
    background-color: #f8f9fa !important;
    border-bottom: 2px solid #dee2e6 !important;
    font-family: inherit !important;
    text-transform: none !important;
    letter-spacing: normal !important;
    line-height: 1.2 !important;
  }
  
  /* 强制覆盖任何可能的字体差异 */
  .table th * {
    font-size: 12px !important;
    font-weight: 600 !important;
    font-family: inherit !important;
  }
  
  /* 手机端列宽优化 - 紧凑布局，确保金额列紧邻交易类型 */
  .table th:nth-child(1), .table td:nth-child(1) { width: 15px !important; }  /* 选择框 */
  .table th:nth-child(2), .table td:nth-child(2) { width: 55px !important; }  /* 时间 */
  .table th:nth-child(3), .table td:nth-child(3) { width: 35px !important; }  /* 交易类型 */
  .table th:nth-child(4), .table td:nth-child(4) { width: 60px !important; }  /* 金额变化 - 固定宽度 */
  
  /* 强制表格在手机端紧凑显示 */
  .transaction-table .table-responsive {
    max-width: 100% !important;
    overflow-x: hidden !important;
  }
  
  /* 确保所有列都紧凑排列 */
  .table th,
  .table td {
    min-width: auto !important;
    max-width: none !important;
  }
  
  /* 强制移除所有可能的间距 */
  .table th,
  .table td {
    padding: 0px !important;
    margin: 0 !important;
    border: none !important;
    border-spacing: 0 !important;
    border-collapse: collapse !important;
  }
  
  /* 确保表格容器完全紧凑 */
  .table {
    width: 100% !important;
    max-width: 100% !important;
    table-layout: fixed !important;
    border-collapse: collapse !important;
    border-spacing: 0 !important;
  }
  
  /* 强制设置表格布局 */
  .table {
    table-layout: fixed !important;
    width: 100% !important;
  }
  
  /* 确保列间距最小 */
  .table th,
  .table td {
    padding: 1px 0px !important;
    margin: 0 !important;
    border: none !important;
  }
  
  /* 确保金额列内容右对齐且突出显示 */
  .amount-column {
    text-align: right !important;
    font-weight: 600;
    font-size: 12px;
  }
  
  /* 金额列标题与其他表头保持一致 */
  .table th.amount-column {
    font-size: 12px !important;
    font-weight: 600 !important;
    color: #333 !important;
    font-family: inherit !important;
    background-color: #f8f9fa !important;
    border-bottom: 2px solid #dee2e6 !important;
  }
  
  /* 优化表格容器 */
  .transaction-table {
    width: 100%;
    margin: 0;
    padding: 0;
  }
  
  /* 调整表格行高，使布局更紧凑 */
  .table tbody tr {
    height: 32px;
  }
  
  /* 强制减少列间距 */
  .table th,
  .table td {
    border-spacing: 0 !important;
    border-collapse: collapse !important;
  }
  
  /* 确保表格容器紧凑 */
  .table {
    border-collapse: collapse !important;
    border-spacing: 0 !important;
    width: 100% !important;
    max-width: 100% !important;
  }
  
  /* 强制表格在手机端紧凑显示 */
  .transaction-table .table-responsive {
    max-width: 100% !important;
    overflow-x: hidden !important;
  }
  
  /* 确保所有列都紧凑排列 */
  .table th,
  .table td {
    min-width: auto !important;
    max-width: none !important;
  }
  
  /* 确保选择框居中 */
  .table td:first-child {
    text-align: center;
  }
  
  /* 优化时间列显示 */
  .table td:nth-child(2) {
    font-size: 11px;
  }
  
  /* 优化交易类型列 */
  .table td:nth-child(3) {
    font-size: 11px;
    font-weight: 600;
  }
  
  /* 强制移除所有可能的横向滚动 */
  .table-responsive::-webkit-scrollbar {
    display: none !important;
  }
  
  .table-responsive {
    -ms-overflow-style: none !important;
    scrollbar-width: none !important;
  }
}

/* 手机端浮动提示样式 */
.mobile-toast {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
}

.toast-content {
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  max-width: 90%;
  width: 100%;
  max-height: 80%;
  overflow: hidden;
  animation: toastSlideIn 0.3s ease-out;
}

.toast-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background: #007bff;
  color: white;
  border-bottom: 1px solid #e9ecef;
}

.toast-title {
  font-weight: 600;
  font-size: 16px;
}

.toast-close {
  background: none;
  border: none;
  color: white;
  font-size: 24px;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background-color 0.2s;
}

.toast-close:hover {
  background: rgba(255, 255, 255, 0.2);
}

.toast-body {
  padding: 20px;
  font-size: 14px;
  line-height: 1.5;
  color: #333;
  word-break: break-word;
}

@keyframes toastSlideIn {
  from {
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}
</style> 
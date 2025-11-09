<template>
  <div class="foreign-stock-page">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2 class="page-title-bold">
        <font-awesome-icon :icon="['fas', 'boxes']" class="me-2" />
        {{ $t('reports.foreign_stock_query') }}
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
              <strong>{{ $t('reports.currency_count') }}:</strong> {{ reportData.currencies.length }}
            </span>
          </div>
        </div>
      </div>

      <!-- 库存统计表 -->
      <div class="data-table-container" v-if="reportData && reportData.currencies.length > 0">
        <h4>{{ $t('reports.stock_stats') }}</h4>
        <div class="table-responsive">
          <table class="table table-striped">
            <thead>
              <tr>
                <th>{{ $t('reports.currency') }}</th>
                <th>{{ $t('reports.opening_balance') }}</th>
                <th>{{ $t('reports.buy_volume') }}</th>
                <th>{{ $t('reports.sell_volume') }}</th>
                <th>{{ $t('reports.change_amount') }}</th>
                <th>{{ $t('reports.current_balance') }}</th>
                <th>{{ $t('reports.stock_status') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="currency in reportData.currencies" :key="currency.currency_code">
                <td>
                  <div class="currency-info-cell">
                    <CurrencyFlag 
                      :code="currency.currency_code" 
                      :custom-filename="currency.custom_flag_filename"
                      class="currency-flag"
                    />
                    <div class="currency-details">
                      <div class="currency-code">{{ currency.currency_code }}</div>
                      <div class="currency-name">{{ getCurrencyDisplayName(currency) }}</div>
                    </div>
                  </div>
                </td>
                <td>{{ formatNumber(currency.opening_balance || 0) }}</td>
                <td class="text-success">{{ formatNumber(currency.total_buy) }}</td>
                <td class="text-info">{{ formatNumber(currency.total_sell) }}</td>
                <td :class="getChangeClass(currency.change_amount || 0)">
                  {{ formatSignedNumber(currency.change_amount || 0) }}
                </td>
                <td :class="getStockClass(currency.current_balance || currency.stock_balance)">
                  {{ formatNumber(currency.current_balance || currency.stock_balance) }}
                </td>
                <td>
                  <span :class="getStockStatusClass(currency.current_balance || currency.stock_balance)">
                    {{ getStockStatusText(currency.current_balance || currency.stock_balance) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 库存汇总 -->
      <div class="summary-container" v-if="reportData && reportData.currencies.length > 0">
        <div class="summary-card">
          <h4>{{ $t('reports.stock_summary') }}</h4>
          <div class="summary-grid">
            <div class="summary-item">
              <div class="summary-value text-success">{{ positiveStockCount }}</div>
              <div class="summary-label">{{ $t('reports.positive_stock') }}</div>
            </div>
            <div class="summary-item">
              <div class="summary-value text-warning">{{ zeroStockCount }}</div>
              <div class="summary-label">{{ $t('reports.zero_stock') }}</div>
            </div>
            <div class="summary-item">
              <div class="summary-value text-danger">{{ negativeStockCount }}</div>
              <div class="summary-label">{{ $t('reports.negative_stock') }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 无数据提示 -->
      <div class="no-data-container" v-else-if="!loading">
        <div class="no-data-card">
          <i class="fas fa-boxes fa-3x text-muted"></i>
          <h4>{{ $t('reports.no_data') }}</h4>
          <p>{{ $t('reports.no_stock_data_today') }}</p>
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
import { useUserStore } from '@/stores/user'
import api from '@/services/api'
import CurrencyFlag from '@/components/CurrencyFlag.vue'
import { getCurrencyName, getCurrencyDisplayName } from '@/utils/currencyTranslator'

export default {
  name: 'ForeignStockQueryView',
  
  components: {
    CurrencyFlag
  },
  
  setup() {
    const userStore = useUserStore()
    
    return {
      currentUser: userStore.user
    }
  },
  
  data() {
    return {
      loading: false,
      error: null,
      reportData: null
    }
  },
  
  computed: {
    positiveStockCount() {
      if (!this.reportData || !this.reportData.currencies) return 0
      return this.reportData.currencies.filter(c => c.stock_balance > 0).length
    },
    
    zeroStockCount() {
      if (!this.reportData || !this.reportData.currencies) return 0
      return this.reportData.currencies.filter(c => c.stock_balance === 0).length
    },
    
    negativeStockCount() {
      if (!this.reportData || !this.reportData.currencies) return 0
      return this.reportData.currencies.filter(c => c.stock_balance < 0).length
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
        const response = await api.get('/reports/stock')
        
        if (response.data.success) {
          this.reportData = response.data.data
        } else {
          this.error = this.$t('reports.load_failed')
        }
      } catch (error) {
        console.error('Load stock report error:', error)
        this.error = this.$t('reports.load_failed')
      } finally {
        this.loading = false
      }
    },
    
    refreshData() {
      this.loadData()
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
    
    getStockClass(stockBalance) {
      if (stockBalance > 0) return 'text-success'
      if (stockBalance < 0) return 'text-danger'
      return 'text-warning'
    },
    
    getStockStatusClass(stockBalance) {
      if (stockBalance > 0) return 'badge badge-success'
      if (stockBalance < 0) return 'badge badge-danger'
      return 'badge badge-warning'
    },
    
    getStockStatusText(stockBalance) {
      if (stockBalance > 0) return this.$t('reports.surplus')
      if (stockBalance < 0) return this.$t('reports.insufficient')
      return this.$t('reports.balance')
    },
    
    getChangeClass(changeAmount) {
      if (changeAmount > 0) return 'text-success'
      if (changeAmount < 0) return 'text-danger'
      return 'text-muted'
    },
    
    formatSignedNumber(value) {
      if (value === null || value === undefined || value === 0) return '0.00'
      const formatted = new Intl.NumberFormat(this.$i18n.locale, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(Math.abs(value))
      return value >= 0 ? `+${formatted}` : `-${formatted}`
    },
    
    getCurrencyDisplayName(currency) {
      if (!currency) return ''
      
      // 使用新的币种显示函数
      return getCurrencyDisplayName(currency.currency_code, currency)
    },
    
    getCurrencyName(currencyCode) {
      return getCurrencyName(currencyCode)
    }
  }
}
</script>

<style scoped>
.foreign-stock-page {
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

.text-info {
  color: #17a2b8;
  font-weight: 600;
}

.text-warning {
  color: #ffc107;
  font-weight: 600;
}

.text-danger {
  color: #dc3545;
  font-weight: 600;
}

.badge {
  padding: 4px 8px;
  font-size: 12px;
  font-weight: 600;
  border-radius: 4px;
  text-transform: uppercase;
}

.badge-success {
  background-color: #28a745;
  color: white;
}

.badge-warning {
  background-color: #ffc107;
  color: #212529;
}

.badge-danger {
  background-color: #dc3545;
  color: white;
}

.summary-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  padding: 20px;
}

.summary-card h4 {
  margin-bottom: 15px;
  color: #495057;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 20px;
}

.summary-item {
  text-align: center;
}

.summary-value {
  font-size: 2rem;
  font-weight: bold;
  margin-bottom: 8px;
}

.summary-label {
  font-size: 0.9rem;
  color: #6c757d;
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

/* 移动端响应式样式 */
@media (max-width: 768px) {
  .foreign-stock-page {
    padding: 10px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }
  
  .operation-buttons {
    flex-direction: column;
    width: 100%;
    gap: 10px;
  }
  
  .btn {
    width: 100%;
    justify-content: center;
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
  
  .table-responsive {
    border: none;
    overflow-x: auto;
  }
  
  .table {
    min-width: 700px;
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
  
  .summary-grid {
    grid-template-columns: 1fr;
    gap: 15px;
  }
  
  .summary-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 0;
    border-bottom: 1px solid #eee;
  }
  
  .summary-value {
    font-size: 1.5rem;
  }
  
  .summary-label {
    font-size: 0.95rem;
  }
}

@media (max-width: 480px) {
  .foreign-stock-page {
    padding: 5px;
  }
  
  .page-header h2 {
    font-size: 1.3em;
  }
  
  .info-card {
    padding: 10px;
  }
  
  .summary-container {
    padding: 15px;
  }
  
  .summary-card h4 {
    font-size: 1.1em;
  }
  
  .summary-value {
    font-size: 1.3rem;
  }
  
  .summary-label {
    font-size: 0.85rem;
  }
  
  .no-data-container {
    padding: 40px 10px;
  }
  
  .no-data-card h4 {
    font-size: 1.1em;
  }
}
</style> 
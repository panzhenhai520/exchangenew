<template>
  <div class="rates-display-container">
    <!-- 页面标题 -->
    <div class="container-fluid py-4">
      <div class="row">
        <div class="col-12">
          <div class="d-flex justify-content-between align-items-center mb-4">
            <h2 class="page-title-bold">
              <font-awesome-icon :icon="['fas', 'exchange-alt']" class="me-2" />
              今日汇率
            </h2>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 头部信息 -->
    <div class="header-section">
      <div class="branch-info">
        <h3>{{ branchInfo.name || 'TEST' }}</h3>
        <p>网点代码: {{ branchInfo.code || 'A005' }}</p>
      </div>
      
      <div class="currency-info">
        <div class="base-currency">
                          <CurrencyFlag 
            v-if="baseCurrency.code" 
            :code="baseCurrency.code || 'THB'" 
            class="base-flag"
          />
          <div>
            <div class="base-currency-name">{{ baseCurrency.name || '泰铢' }}</div>
            <div class="base-currency-code">{{ baseCurrency.code || 'THB' }}</div>
          </div>
        </div>
      </div>
      
      <div class="update-info">
        <p class="last-update">
          最后更新: {{ formatTime(lastUpdated) }}
        </p>
        <button 
          class="refresh-btn" 
          @click="refreshRates"
          :disabled="loading"
        >
          <i class="fas fa-sync-alt" :class="{ 'fa-spin': loading }"></i>
          {{ loading ? '更新中...' : '刷新汇率' }}
        </button>
      </div>
    </div>

    <!-- 汇率展示区域 -->
    <div class="rates-section">
      <div class="rates-header">
        <h2>外币兑换汇率牌</h2>
        <p class="rates-subtitle">FOREIGN EXCHANGE RATES</p>
      </div>

      <!-- 汇率表格 -->
      <div class="rates-table-container">
        <table class="rates-table">
          <thead>
            <tr>
              <th class="currency-column">币种 / Currency</th>
              <th class="rate-column">银行买入 / We Buy</th>
              <th class="rate-column">银行卖出 / We Sell</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="rate in displayRates" :key="rate.currency_code" class="rate-row">
              <td class="currency-cell">
                <div class="currency-info-cell">
                  <CurrencyFlag 
                    :code="rate.currency_code || 'USD'" 
                    class="currency-flag"
                  />
                  <div class="currency-details">
                    <div class="currency-code">{{ rate.currency_code }}</div>
                    <div class="currency-name">{{ rate.currency_name }}</div>
                  </div>
                </div>
              </td>
              <td class="rate-cell buy-rate">
                {{ formatRate(rate.buy_rate) }}
              </td>
              <td class="rate-cell sell-rate">
                {{ formatRate(rate.sell_rate) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 底部信息 -->
    <div class="footer-section">
      <div class="notice">
        <p>汇率仅供参考，实际交易汇率以柜台报价为准</p>
        <p>Exchange rates are for reference only. Actual rates are subject to counter quotation</p>
      </div>
      <div class="auto-refresh-info" v-if="autoRefresh">
        <i class="fas fa-clock"></i>
        <span>自动刷新：每{{ autoRefreshInterval / 1000 }}秒</span>
      </div>
    </div>

    <!-- 加载遮罩 -->
    <div v-if="loading && !rates.length" class="loading-overlay">
      <div class="loading-content">
        <i class="fas fa-spinner fa-spin fa-2x"></i>
        <p>正在加载汇率数据...</p>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="error" class="error-message">
      <i class="fas fa-exclamation-triangle"></i>
      <span>{{ error }}</span>
      <button @click="refreshRates" class="retry-btn">重试</button>
    </div>

    <!-- 功能按钮 -->
    <div class="action-buttons">
      <button 
        class="action-btn print-btn" 
        @click="printRates"
        title="打印汇率表"
      >
        <i class="fas fa-print"></i>
      </button>
      <button 
        class="action-btn auto-refresh-btn" 
        @click="toggleAutoRefresh"
        :class="{ active: autoRefresh }"
        title="自动刷新"
      >
        <i class="fas fa-sync-alt"></i>
      </button>
    </div>
  </div>
</template>

<script>
import CurrencyFlag from '@/components/CurrencyFlag.vue'
import axios from 'axios'

export default {
  name: 'RatesDisplayView',
  components: {
    CurrencyFlag
  },
  data() {
    return {
      rates: [],
      branchInfo: {},
      baseCurrency: {},
      lastUpdated: '',
      loading: false,
      error: '',
      autoRefresh: false,
      autoRefreshInterval: 30000,
      refreshTimer: null
    }
  },
  computed: {
    displayRates() {
      return [...this.rates].sort((a, b) => a.currency_code.localeCompare(b.currency_code))
    }
  },
  mounted() {
    this.loadRatesData()
    document.addEventListener('keydown', this.handleKeydown)
  },
  beforeUnmount() {
    this.clearAutoRefresh()
    document.removeEventListener('keydown', this.handleKeydown)
  },
  methods: {
    async loadRatesData() {
      this.loading = true
      this.error = ''
      
      try {
        const response = await axios.get('/api/rates-display/current-rates', {
          params: { branch: 'A005' }
        })
        
        if (response.data.success) {
          const data = response.data.data
          this.rates = data.rates || []
          this.branchInfo = data.branch || {}
          this.baseCurrency = data.base_currency || {}
          this.lastUpdated = data.last_updated || new Date().toISOString()
        } else {
          this.error = response.data.message || '获取汇率数据失败'
        }
      } catch (error) {
        console.error('加载汇率数据失败:', error)
        this.error = '网络连接失败，请检查网络连接'
      } finally {
        this.loading = false
      }
    },
    
    async refreshRates() {
      await this.loadRatesData()
    },
    
    formatRate(rate) {
      if (!rate || rate === 0) return '-'
      return parseFloat(rate).toFixed(4)
    },
    
    formatTime(timeStr) {
      if (!timeStr) return ''
      try {
        const date = new Date(timeStr)
        return date.toLocaleString('zh-CN', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit'
        })
      } catch (error) {
        return timeStr
      }
    },
    
    toggleAutoRefresh() {
      this.autoRefresh = !this.autoRefresh
      
      if (this.autoRefresh) {
        this.startAutoRefresh()
      } else {
        this.clearAutoRefresh()
      }
    },
    
    startAutoRefresh() {
      this.clearAutoRefresh()
      this.refreshTimer = setInterval(() => {
        this.refreshRates()
      }, this.autoRefreshInterval)
    },
    
    clearAutoRefresh() {
      if (this.refreshTimer) {
        clearInterval(this.refreshTimer)
        this.refreshTimer = null
      }
    },
    
    printRates() {
      window.print()
    },
    
    handleKeydown(event) {
      if (event.key === 'F5' || (event.ctrlKey && event.key === 'r')) {
        event.preventDefault()
        this.refreshRates()
      }
      else if (event.ctrlKey && event.key === 'p') {
        event.preventDefault()
        this.printRates()
      }
    }
  }
}
</script>

<style scoped>
.rates-display-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #2d5a27 0%, #4a7c59 100%);
  color: white;
  font-family: 'Arial', sans-serif;
  padding: 20px;
  position: relative;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  flex-wrap: wrap;
  gap: 20px;
}

.branch-info h1 {
  font-size: 2.5rem;
  margin: 0;
  font-weight: bold;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

.branch-info p {
  font-size: 1.2rem;
  margin: 5px 0 0 0;
  opacity: 0.9;
}

.currency-info {
  text-align: center;
}

.base-currency {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 1.1rem;
}

.base-flag {
  width: 32px;
  height: 24px;
}

.base-currency-name {
  font-weight: bold;
}

.base-currency-code {
  opacity: 0.9;
}

.update-info {
  text-align: right;
}

.last-update {
  font-size: 0.9rem;
  margin: 0 0 10px 0;
  opacity: 0.8;
}

.refresh-btn {
  background: rgba(255,255,255,0.2);
  border: 1px solid rgba(255,255,255,0.3);
  color: white;
  padding: 8px 16px;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.refresh-btn:hover:not(:disabled) {
  background: rgba(255,255,255,0.3);
  transform: translateY(-1px);
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.rates-section {
  background: rgba(255,255,255,0.95);
  border-radius: 15px;
  padding: 30px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.2);
  color: #333;
}

.rates-header {
  text-align: center;
  margin-bottom: 30px;
  border-bottom: 3px solid #2d5a27;
  padding-bottom: 20px;
}

.rates-header h2 {
  font-size: 2.2rem;
  margin: 0 0 10px 0;
  color: #2d5a27;
  font-weight: bold;
}

.rates-subtitle {
  font-size: 1.1rem;
  color: #666;
  margin: 0;
  font-style: italic;
}

.rates-table-container {
  overflow-x: auto;
}

.rates-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 1.1rem;
}

.rates-table th {
  background: linear-gradient(135deg, #2d5a27, #4a7c59);
  color: white;
  padding: 15px 10px;
  text-align: center;
  font-weight: bold;
  font-size: 1.1rem;
}

.rates-table th.currency-column {
  width: 40%;
  text-align: left;
  padding-left: 20px;
}

.rates-table th.rate-column {
  width: 30%;
}

.rate-row {
  border-bottom: 1px solid #e0e0e0;
  transition: background-color 0.2s ease;
}

.rate-row:hover {
  background-color: #f8f9fa;
}

.rate-row:nth-child(even) {
  background-color: #f9f9f9;
}

.rate-row:nth-child(even):hover {
  background-color: #f0f0f0;
}

.currency-cell {
  padding: 15px 20px;
}

.currency-info-cell {
  display: flex;
  align-items: center;
  gap: 15px;
}

.currency-flag {
  width: 32px;
  height: 24px;
  border-radius: 4px;
  border: 1px solid #ddd;
  flex-shrink: 0;
}

.currency-details {
  flex: 1;
}

.currency-code {
  font-weight: bold;
  font-size: 1.2rem;
  color: #2d5a27;
}

.currency-name {
  font-size: 0.9rem;
  color: #666;
  margin-top: 2px;
}

.rate-cell {
  padding: 15px 10px;
  text-align: center;
  font-weight: bold;
  font-size: 1.3rem;
  font-family: 'Courier New', monospace;
}

.buy-rate {
  color: #d73527;
  background-color: rgba(215, 53, 39, 0.05);
}

.sell-rate {
  color: #2e7d32;
  background-color: rgba(46, 125, 50, 0.05);
}

.footer-section {
  margin-top: 30px;
  text-align: center;
}

.notice {
  background: rgba(255,255,255,0.1);
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 20px;
}

.notice p {
  margin: 5px 0;
  font-size: 0.9rem;
  opacity: 0.9;
}

.auto-refresh-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 0.9rem;
  opacity: 0.8;
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.loading-content {
  text-align: center;
  color: white;
}

.loading-content p {
  margin-top: 20px;
  font-size: 1.1rem;
}

.error-message {
  position: fixed;
  top: 20px;
  right: 20px;
  background: #f44336;
  color: white;
  padding: 15px 20px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.3);
  display: flex;
  align-items: center;
  gap: 10px;
  z-index: 1001;
  max-width: 400px;
}

.retry-btn {
  background: rgba(255,255,255,0.2);
  border: 1px solid rgba(255,255,255,0.3);
  color: white;
  padding: 5px 10px;
  border-radius: 4px;
  cursor: pointer;
  margin-left: 10px;
}

.retry-btn:hover {
  background: rgba(255,255,255,0.3);
}

.action-buttons {
  position: fixed;
  bottom: 30px;
  right: 30px;
  display: flex;
  flex-direction: column;
  gap: 15px;
  z-index: 999;
}

.action-btn {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  border: none;
  background: #2d5a27;
  color: white;
  font-size: 1.2rem;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0,0,0,0.3);
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-btn:hover {
  background: #4a7c59;
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0,0,0,0.4);
}

.auto-refresh-btn.active {
  background: #4caf50;
}

.auto-refresh-btn.active:hover {
  background: #66bb6a;
}

@media print {
  .rates-display-container {
    background: white !important;
    color: black !important;
    padding: 20px !important;
  }
  
  .header-section,
  .footer-section {
    color: black !important;
  }
  
  .rates-section {
    background: white !important;
    box-shadow: none !important;
  }
  
  .rates-header h2 {
    color: black !important;
  }
  
  .currency-code {
    color: black !important;
  }
  
  .action-buttons,
  .error-message,
  .loading-overlay {
    display: none !important;
  }
  
  .refresh-btn {
    display: none !important;
  }
}

@media (max-width: 768px) {
  .rates-display-container {
    padding: 10px;
  }
  
  .header-section {
    flex-direction: column;
    text-align: center;
    gap: 15px;
  }
  
  .branch-info h1 {
    font-size: 2rem;
  }
  
  .rates-section {
    padding: 20px 15px;
  }
  
  .rates-header h2 {
    font-size: 1.8rem;
  }
  
  .rates-table {
    font-size: 1rem;
  }
  
  .currency-flag {
    width: 24px;
    height: 18px;
  }
  
  .currency-code {
    font-size: 1.1rem;
  }
  
  .rate-cell {
    font-size: 1.1rem;
    padding: 12px 8px;
  }
  
  .action-buttons {
    bottom: 20px;
    right: 20px;
  }
  
  .action-btn {
    width: 45px;
    height: 45px;
    font-size: 1.1rem;
  }
}
</style> 
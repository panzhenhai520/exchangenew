<template>
  <div class="denomination-preview-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <i class="fas fa-eye me-2"></i>
          面值汇率发布预览
        </h1>
        <p class="page-subtitle">预览所有币种的面值汇率，确认无误后发布到机顶盒</p>
      </div>
    </div>

    <!-- 预览内容 -->
    <div class="preview-content">
      <!-- 统计信息 -->
      <div class="stats-card">
        <div class="row">
          <div class="col-md-3">
            <div class="stat-item">
              <div class="stat-value">{{ totalCurrencies }}</div>
              <div class="stat-label">币种数量</div>
            </div>
          </div>
          <div class="col-md-3">
            <div class="stat-item">
              <div class="stat-value">{{ totalDenominations }}</div>
              <div class="stat-label">面值数量</div>
            </div>
          </div>
          <div class="col-md-3">
            <div class="stat-item">
              <div class="stat-value">{{ totalRates }}</div>
              <div class="stat-label">汇率数量</div>
            </div>
          </div>
          <div class="col-md-3">
            <div class="stat-item">
              <div class="stat-value">{{ lastUpdated }}</div>
              <div class="stat-label">最后更新</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 币种列表 -->
      <div class="currencies-list">
        <div v-for="currency in currenciesWithDenominations" :key="currency.id" class="currency-card">
          <div class="currency-header">
            <div class="currency-info">
              <img 
                :src="getCurrencyFlag(currency)" 
                :alt="currency.currency_code"
                class="currency-flag"
                @error="handleImageError"
              />
              <div class="currency-details">
                <h3 class="currency-code">{{ currency.currency_code }}</h3>
                <p class="currency-name">{{ currency.currency_name }}</p>
              </div>
            </div>
            <div class="currency-stats">
              <span class="denomination-count">{{ currency.denominations.length }} 个面值</span>
            </div>
          </div>
          
          <div class="denominations-grid">
            <div 
              v-for="denom in currency.denominations" 
              :key="denom.id"
              class="denomination-item"
              v-show="denom.buy_rate && denom.sell_rate && denom.buy_rate > 0 && denom.sell_rate > 0"
            >
              <div class="denomination-value">
                {{ formatDenominationValue(denom.denomination_value) }}
                <span class="denomination-type">{{ denom.denomination_type === 'bill' ? '纸币' : '硬币' }}</span>
              </div>
              <div class="denomination-rates">
                <div class="rate-item buy-rate">
                  <i class="fas fa-arrow-up"></i>
                  {{ parseFloat(denom.buy_rate).toFixed(4) }}
                </div>
                <div class="rate-item sell-rate">
                  <i class="fas fa-arrow-down"></i>
                  {{ parseFloat(denom.sell_rate).toFixed(4) }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="action-buttons">
        <button 
          class="btn btn-secondary"
          @click="goBack"
        >
          <i class="fas fa-arrow-left me-1"></i>
          返回
        </button>
        <button 
          class="btn btn-info"
          @click="refreshData"
          :disabled="loading"
        >
          <i class="fas fa-sync-alt me-1"></i>
          刷新数据
        </button>
        <button 
          class="btn btn-success btn-lg"
          @click="confirmPublish"
          :disabled="loading || currenciesWithDenominations.length === 0"
        >
          <i class="fas fa-broadcast-tower me-2"></i>
          确认发布到机顶盒
        </button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-overlay">
      <div class="loading-spinner">
        <i class="fas fa-spinner fa-spin"></i>
        <p>正在处理中...</p>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../services/api'

export default {
  name: 'DenominationPreviewView',
  data() {
    return {
      loading: false,
      currenciesWithDenominations: []
    }
  },
  computed: {
    totalCurrencies() {
      return this.currenciesWithDenominations.length
    },
    totalDenominations() {
      return this.currenciesWithDenominations.reduce((sum, currency) => {
        return sum + currency.denominations.filter(denom => 
          denom.buy_rate && denom.sell_rate && denom.buy_rate > 0 && denom.sell_rate > 0
        ).length
      }, 0)
    },
    totalRates() {
      return this.totalDenominations * 2 // 买入价和卖出价
    },
    lastUpdated() {
      if (this.currenciesWithDenominations.length === 0) return '无'
      const dates = this.currenciesWithDenominations.map(currency => 
        currency.denominations.map(denom => denom.updated_at).filter(Boolean)
      ).flat()
      if (dates.length === 0) return '无'
      const latestDate = new Date(Math.max(...dates.map(d => new Date(d))))
      return latestDate.toLocaleString('zh-CN')
    }
  },
  async mounted() {
    await this.loadData()
  },
  methods: {
    async loadData() {
      this.loading = true
      try {
        const response = await api.get('/denominations-api/currencies-with-denominations')
        if (response.data.success) {
          this.currenciesWithDenominations = response.data.data || []
        } else {
          this.$toast.error(response.data.message || '加载数据失败')
        }
      } catch (error) {
        console.error('加载面值汇率数据失败:', error)
        this.$toast.error('加载数据失败')
      } finally {
        this.loading = false
      }
    },
    
    async confirmPublish() {
      if (this.currenciesWithDenominations.length === 0) {
        this.$toast.warning('没有可发布的币种')
        return
      }
      
      if (!confirm(`确定要发布所有 ${this.currenciesWithDenominations.length} 个币种的面值汇率到机顶盒吗？\n\n注意：这将覆盖今日已有的面值汇率发布。`)) {
        return
      }
      
      this.loading = true
      try {
        // 准备所有币种的面值汇率数据
        const currenciesData = []
        
        for (const currency of this.currenciesWithDenominations) {
          const denominationRates = currency.denominations
            .filter(denom => denom.buy_rate && denom.sell_rate && denom.buy_rate > 0 && denom.sell_rate > 0)
            .map(denom => ({
              denomination_id: denom.id,
              denomination_value: denom.denomination_value,
              denomination_type: denom.denomination_type,
              buy_rate: parseFloat(denom.buy_rate),
              sell_rate: parseFloat(denom.sell_rate)
            }))
          
          if (denominationRates.length > 0) {
            currenciesData.push({
              currency_id: currency.id,
              denomination_rates: denominationRates
            })
          }
        }
        
        if (currenciesData.length === 0) {
          this.$toast.warning('没有有效的面值汇率数据')
          return
        }
        
        const response = await api.post('/dashboard/publish-multi-currency-denomination-rates', {
          currencies: currenciesData
        })
        
        if (response.data.success) {
          this.$toast.success(`成功发布 ${currenciesData.length} 个币种的面值汇率`)
          // 跳转到机顶盒显示页面
          const displayUrl = response.data.data.display_url
          window.open(displayUrl, '_blank')
        } else {
          this.$toast.error(response.data.message || '发布失败')
        }
      } catch (error) {
        console.error('发布多币种面值汇率失败:', error)
        this.$toast.error('发布失败')
      } finally {
        this.loading = false
      }
    },
    
    async refreshData() {
      await this.loadData()
    },
    
    goBack() {
      this.$router.go(-1)
    },
    
    getCurrencyFlag(currency) {
      if (currency.custom_flag_filename) {
        return `/flags/${currency.custom_flag_filename}`
      } else if (currency.flag_code) {
        return `/flags/${currency.flag_code}.svg`
      } else {
        return '/flags/unknown.svg'
      }
    },
    
    handleImageError(event) {
      event.target.src = '/flags/unknown.svg'
    },
    
    formatDenominationValue(value) {
      return parseFloat(value).toLocaleString('zh-CN')
    }
  }
}
</script>

<style scoped>
.denomination-preview-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.page-header {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 15px;
  padding: 30px;
  margin-bottom: 30px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.page-title {
  color: #2c3e50;
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 10px;
}

.page-subtitle {
  color: #7f8c8d;
  font-size: 1.1rem;
  margin: 0;
}

.preview-content {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 15px;
  padding: 30px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.stats-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 15px;
  padding: 30px;
  margin-bottom: 30px;
  color: white;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 1rem;
  opacity: 0.9;
}

.currencies-list {
  margin-bottom: 30px;
}

.currency-card {
  background: #f8f9fa;
  border-radius: 15px;
  padding: 25px;
  margin-bottom: 20px;
  border: 1px solid #e9ecef;
  transition: all 0.3s ease;
}

.currency-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

.currency-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.currency-info {
  display: flex;
  align-items: center;
}

.currency-flag {
  width: 40px;
  height: 30px;
  border-radius: 5px;
  margin-right: 15px;
  object-fit: cover;
  border: 1px solid #dee2e6;
}

.currency-code {
  font-size: 1.5rem;
  font-weight: 700;
  color: #2c3e50;
  margin: 0 0 5px 0;
}

.currency-name {
  color: #6c757d;
  margin: 0;
  font-size: 1rem;
}

.currency-stats {
  background: #e3f2fd;
  padding: 8px 16px;
  border-radius: 20px;
  color: #1976d2;
  font-weight: 600;
}

.denominations-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 15px;
}

.denomination-item {
  background: white;
  border-radius: 10px;
  padding: 15px;
  border: 1px solid #e9ecef;
  transition: all 0.3s ease;
}

.denomination-item:hover {
  border-color: #007bff;
  box-shadow: 0 2px 8px rgba(0, 123, 255, 0.15);
}

.denomination-value {
  font-size: 1.2rem;
  font-weight: 700;
  color: #2c3e50;
  margin-bottom: 10px;
}

.denomination-type {
  font-size: 0.8rem;
  color: #6c757d;
  margin-left: 8px;
}

.denomination-rates {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.rate-item {
  flex: 1;
  text-align: center;
  padding: 8px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.9rem;
}

.buy-rate {
  background: #d4edda;
  color: #155724;
}

.sell-rate {
  background: #f8d7da;
  color: #721c24;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 15px;
  padding-top: 20px;
  border-top: 1px solid #e9ecef;
}

.btn {
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.btn-lg {
  padding: 15px 30px;
  font-size: 1.1rem;
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.loading-spinner {
  background: white;
  padding: 40px;
  border-radius: 15px;
  text-align: center;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.loading-spinner i {
  font-size: 2rem;
  color: #007bff;
  margin-bottom: 15px;
}

.loading-spinner p {
  margin: 0;
  color: #6c757d;
  font-size: 1.1rem;
}

@media (max-width: 768px) {
  .denomination-preview-container {
    padding: 10px;
  }
  
  .page-title {
    font-size: 2rem;
  }
  
  .denominations-grid {
    grid-template-columns: 1fr;
  }
  
  .action-buttons {
    flex-direction: column;
  }
  
  .btn {
    width: 100%;
  }
}
</style>
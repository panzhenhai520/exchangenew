<template>
  <div class="app-home-view">
    <!-- 独立的蓝色指标区域 -->
    <div class="metrics-container">
      <div class="metrics-grid">
        <div class="metric-card">
          <div class="metric-title">{{ $t('app.home.local_balance') }}</div>
          <div class="metric-value">{{ localBalance }}</div>
        </div>
        <div class="metric-card">
          <div class="metric-title">{{ $t('app.home.dynamic_income') }}</div>
          <div class="metric-value">{{ dynamicIncome }}</div>
        </div>
        <div class="metric-card">
          <div class="metric-title">{{ $t('app.home.spread_income') }}</div>
          <div class="metric-value">{{ spreadIncome }}</div>
        </div>
      </div>
    </div>



    <!-- 汇率趋势图区域 -->
    <div class="chart-section">
      <div class="chart-header">
        <h3 class="chart-title">{{ $t('app.home.rate_trend') }}</h3>
        <div class="currency-selector">
          <select v-model="selectedCurrency" @change="loadRateTrends">
            <option value="">{{ $t('app.home.select_currency') }}</option>
            <option v-for="currency in currencies" :key="currency.id" :value="currency.id">
              {{ currency.currency_code }} - {{ getCurrencyDisplayName(currency.currency_code, currency.currency_name, currency.custom_flag_filename) }}
            </option>
          </select>
        </div>
      </div>
      <div class="chart-container">
        <div v-if="!selectedCurrency" class="chart-placeholder">
          {{ $t('app.home.select_currency_tip') }}
        </div>
        <AsyncChart 
          v-else
          :chartData="chartData"
          :options="chartOptions"
          height="200px"
        />
      </div>
    </div>

    <!-- 每日汇率发布区域 -->
    <div class="rates-section">
      <h3 class="rates-header">{{ $t('app.home.rate_publish') }}</h3>
      <div class="rate-table-container">
        <div v-if="ratesLoading" class="loading-placeholder">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">加载中...</span>
          </div>
          <div class="mt-2">{{ $t('app.home.loading_rates') }}</div>
        </div>
        
        <div v-else-if="rates.length === 0" class="empty-placeholder">
          <i class="fas fa-chart-line fa-2x text-muted mb-2"></i>
          <div>{{ $t('app.home.no_rates') }}</div>
        </div>
        
        <div v-else class="rate-table">
          <div 
            v-for="(rate, index) in rates" 
            :key="rate.currency_id"
            class="rate-item"
            :class="{ 'editing': rate.isEditing }"
          >
            <!-- 币种信息 -->
            <div class="currency-info">
              <div class="currency-flag">
                <CurrencyFlag :code="rate.currency_code" :custom-filename="rate.custom_flag_filename" :width="32" :height="24" />
              </div>
                              <div class="currency-details">
                  <div class="currency-code">{{ rate.currency_code }}</div>
                  <div class="currency-name">{{ getCurrencyDisplayName(rate.currency_code, rate.currency_name, rate.custom_flag_filename) }}</div>
                </div>
            </div>
            
            <!-- 汇率输入和操作按钮 -->
            <div class="rate-content">
            <div class="rate-inputs">
              <div class="input-row">
                <label class="inline-label">{{ $t('app.home.buy_rate') }}:</label>
                <input 
                  v-if="rate.isEditing"
                  type="number" 
                  v-model="rate.buy_rate" 
                  class="rate-input"
                  step="0.0001"
                  min="0"
                >
                <span v-else class="rate-display">{{ parseFloat(rate.buy_rate).toFixed(4) }}</span>
              </div>
              
              <div class="input-row">
                <label class="inline-label">{{ $t('app.home.sell_rate') }}:</label>
                <input 
                  v-if="rate.isEditing"
                  type="number" 
                  v-model="rate.sell_rate" 
                  class="rate-input"
                  step="0.0001"
                  min="0"
                >
                <span v-else class="rate-display">{{ parseFloat(rate.sell_rate).toFixed(4) }}</span>
              </div>
            </div>
            
            <!-- 操作按钮 -->
            <div class="rate-actions">
              <button 
                v-if="!rate.isEditing"
                @click="startEdit(index)"
                class="mobile-btn"
              >
                <i class="fas fa-edit"></i>
              </button>
              <div v-else class="edit-actions">
                <button @click="saveRate(index)" class="mobile-btn btn-success">
                  <i class="fas fa-check"></i>
                </button>
                <button @click="cancelEdit(index)" class="mobile-btn btn-secondary">
                  <i class="fas fa-times"></i>
                </button>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 功能按钮 -->
        <div class="action-buttons">
          <button @click="saveAllRates" class="btn btn-primary">{{ $t('app.home.save') }}</button>
          <button @click="publishToSetTopBox" class="btn btn-success">{{ $t('app.home.publish') }}</button>
          <button @click="clearCache" class="btn btn-warning">{{ $t('app.home.clear_cache') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import AsyncChart from '@/components/AsyncChart.vue'
import CurrencyFlag from '@/components/CurrencyFlag.vue'
import api from '@/services/api'
import { getCurrencyName } from '@/utils/currencyTranslator'

export default {
  name: 'AppHomeView',
  components: {
    AsyncChart,
    CurrencyFlag
  },
  setup() {
    // 获取i18n实例
    const { locale } = useI18n()
    
    // 调试翻译加载
    console.log('AppHomeView setup开始')
    console.log('当前语言:', locale.value)
    
    // 响应式数据
    const selectedCurrency = ref('')
    const currencies = ref([])
    const chartData = ref({})
    const chartOptions = ref({})
    
    // 三个指标数据
    const localBalance = ref('¥0.00')
    const dynamicIncome = ref('¥0.00')
    const spreadIncome = ref('¥0.00')
    const metricsLoading = ref(false)
    
    // 汇率表格数据
    const rates = ref([])
    const ratesLoading = ref(false)
    const originalRates = ref([]) // 保存原始数据用于取消编辑
    
    // 获取币种显示名称
    const getCurrencyDisplayName = (currencyCode, currencyName, customFlagFilename) => {
      // 检查是否是自定义币种（有custom_flag_filename）
      if (customFlagFilename) {
        // console.log(`[自定义币种] ${currencyCode} 使用数据库名称: ${currencyName}`);
        return currencyName || currencyCode;
      }
      
      // 使用翻译
      const currentLang = locale.value === 'zh-CN' ? 'zh' : locale.value === 'en-US' ? 'en' : 'th';
      const translatedName = getCurrencyName(currencyCode, currentLang, null);
      if (translatedName && translatedName !== currencyCode) {
        return translatedName;
      }
      return currencyName || currencyCode;
    };
    
    // 方法
    const loadCurrencies = async () => {
      try {
        const response = await api.get('/rates/currencies')
        console.log('币种API响应:', response)
        if (response.data.success) {
          currencies.value = response.data.currencies || []
          // 如果有币种，默认选择第一个
          if (currencies.value.length > 0) {
            selectedCurrency.value = currencies.value[0].id
            loadRateTrends()
          }
        } else {
          console.error('币种API返回失败:', response.data)
          currencies.value = []
        }
      } catch (error) {
        console.error('加载币种失败:', error)
        currencies.value = []
      }
    }
    
    const loadRateTrends = async () => {
      if (!selectedCurrency.value) return
      
      try {
        const response = await api.get(`/rates/currency/${selectedCurrency.value}/history`)
        console.log('汇率趋势API响应:', response)
        if (response.data.success && response.data.history && response.data.history.length > 0) {
          const data = response.data.history
          chartData.value = {
            labels: data.map(item => {
              const date = new Date(item.date);
              return date.toLocaleDateString('zh-CN', {
                month: 'short',
                day: 'numeric'
              });
            }),
            datasets: [
              {
                label: '买入价',
                data: data.map(item => item.buy_rate),
                borderColor: '#28a745',
                backgroundColor: 'rgba(40, 167, 69, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointHoverRadius: 6,
                pointBackgroundColor: '#28a745',
                pointBorderColor: '#fff',
                pointBorderWidth: 2
              },
              {
                label: '卖出价',
                data: data.map(item => item.sell_rate),
                borderColor: '#007bff',
                backgroundColor: 'rgba(0, 123, 255, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointHoverRadius: 6,
                pointBackgroundColor: '#007bff',
                pointBorderColor: '#fff',
                pointBorderWidth: 2
              }
            ]
          }
          
          chartOptions.value = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                display: true,
                position: 'top',
                labels: {
                  usePointStyle: true,
                  padding: 15,
                  font: {
                    size: 12
                  }
                }
              },
              tooltip: {
                mode: 'index',
                intersect: false,
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                titleColor: '#333',
                bodyColor: '#666',
                borderColor: '#ddd',
                borderWidth: 1,
                cornerRadius: 6,
                padding: 12,
                displayColors: true,
                callbacks: {
                  title: function(tooltipItems) {
                    return '日期: ' + tooltipItems[0].label;
                  },
                  label: function(context) {
                    return context.dataset.label + ': ' + Number(context.parsed.y).toFixed(4);
                  }
                }
              }
            },
            hover: {
              mode: 'index',
              intersect: false
            },
            scales: {
              y: {
                beginAtZero: false,
                grid: {
                  color: 'rgba(0,0,0,0.1)'
                },
                ticks: {
                  callback: function(value) {
                    return Number(value).toFixed(4);
                  }
                }
              },
              x: {
                grid: {
                  display: false
                }
              }
            }
          }
        } else {
          console.error('汇率趋势API返回失败或数据为空:', response.data)
          chartData.value = {}
          chartOptions.value = {}
        }
      } catch (error) {
        console.error('加载汇率趋势失败:', error)
        chartData.value = {}
        chartOptions.value = {}
      }
    }
    
    const loadMetrics = async () => {
      metricsLoading.value = true
      try {
        console.log('开始加载指标数据...')
        
        // 1. 加载本币余额 - 通过branch_id查询base_currency_id，再查询余额
        try {
          // 先获取当前网点信息（包含本币ID）
          const branchResponse = await api.get('/system/branches/current')
          console.log('网点信息API响应:', branchResponse)
          
          if (branchResponse.data.success) {
            const baseCurrencyId = branchResponse.data.branch?.base_currency_id
            const baseCurrencyCode = branchResponse.data.branch?.base_currency?.code || 'THB'
            console.log('本币ID:', baseCurrencyId, '本币代码:', baseCurrencyCode)
            
            if (baseCurrencyId) {
              // 根据本币ID查询余额
          const balanceResponse = await api.get('/balance-management/query')
          console.log('本币余额API响应:', balanceResponse)
              
          if (balanceResponse.data.success) {
                console.log('余额API返回成功，所有余额数据:', balanceResponse.data.balances)
                // 优先通过currency.id查找，如果没有则通过currency.code查找
                let localBalanceData = balanceResponse.data.balances.find(b => b.currency?.id === baseCurrencyId)
                console.log('通过currency.id查找结果:', localBalanceData, '查找的ID:', baseCurrencyId)
                
                if (!localBalanceData) {
                  localBalanceData = balanceResponse.data.balances.find(b => b.currency?.code === baseCurrencyCode)
                  console.log('通过currency.code查找结果:', localBalanceData, '查找的代码:', baseCurrencyCode)
                }
                
            if (localBalanceData) {
                  localBalance.value = `${parseFloat(localBalanceData.balance).toFixed(2)}`
                  console.log('找到本币余额:', localBalance.value, '币种:', localBalanceData.currency?.code)
            } else {
                  console.log('未找到本币余额，使用默认值')
                  console.log('所有可用余额:', balanceResponse.data.balances.map(b => ({ id: b.currency?.id, code: b.currency?.code, balance: b.balance })))
                  localBalance.value = '0.00'
                }
              } else {
                console.error('余额API返回失败:', balanceResponse.data)
                localBalance.value = '0.00'
              }
            } else {
              console.error('网点未设置本币ID')
              localBalance.value = '0.00'
            }
          } else {
            console.error('网点信息API返回失败:', branchResponse.data)
            localBalance.value = '0.00'
          }
        } catch (error) {
          console.error('加载本币余额失败:', error)
          localBalance.value = '0.00'
        }
        
        // 2. 加载动态收入 - 使用收入报表API
        try {
          const incomeResponse = await api.get('/reports/income')
          console.log('动态收入API完整响应:', incomeResponse)
          if (incomeResponse.data.success) {
            console.log('动态收入数据结构:', incomeResponse.data)
            // 直接从data中获取total_income
            const totalIncome = incomeResponse.data.data?.total_income || incomeResponse.data.total_income || 0
            console.log('解析到的总收入:', totalIncome)
            // 显示实际收入，包括负数
            dynamicIncome.value = `${totalIncome.toFixed(2)}`
            console.log('最终显示的收入:', dynamicIncome.value)
          } else {
            console.error('收入API返回失败:', incomeResponse.data)
            // 如果是权限问题，记录详细信息
            if (incomeResponse.data.message && incomeResponse.data.message.includes('权限不足')) {
              console.error('权限不足，需要view_transactions权限')
            }
            dynamicIncome.value = '0.00'
          }
        } catch (error) {
          console.error('加载动态收入失败:', error)
          // 如果是权限错误，记录详细信息
          if (error.response && error.response.status === 403) {
            console.error('权限不足，无法访问收入报表')
          }
          dynamicIncome.value = '0.00'
        }
        
        // 3. 加载点差收入 - 使用收入报表API
        try {
          const spreadResponse = await api.get('/reports/income')
          console.log('点差收入API完整响应:', spreadResponse)
          if (spreadResponse.data.success) {
            console.log('点差收入数据结构:', spreadResponse.data)
            // 直接从data中获取total_spread_income
            const totalSpread = spreadResponse.data.data?.total_spread_income || spreadResponse.data.total_spread_income || 0
            console.log('解析到的总点差收入:', totalSpread)
            // 显示实际点差收入，包括负数
            spreadIncome.value = `${totalSpread.toFixed(2)}`
            console.log('最终显示的点差收入:', spreadIncome.value)
          } else {
            console.error('点差收入API返回失败:', spreadResponse.data)
            spreadIncome.value = '0.00'
          }
        } catch (error) {
          console.error('加载点差收入失败:', error)
          spreadIncome.value = '0.00'
        }
      } catch (error) {
        console.error('加载指标数据失败:', error)
      } finally {
        metricsLoading.value = false
      }
    }
    
    // 汇率表格相关方法
    const loadRates = async () => {
      ratesLoading.value = true
      try {
        console.log('开始加载汇率数据...')
        // 使用正确的API调用，获取所有可发布的币种（包括未发布的）
        const response = await api.get('/rates/all', {
          params: {
            include_publish_info: true,
            published_only: false  // 获取所有币种，包括未发布的
          }
        })
        console.log('汇率API响应:', response)
        
        if (response.data.success) {
          console.log('汇率API返回成功，数据:', response.data)
          // 检查数据格式，支持多种可能的响应结构
          let ratesData = []
          if (response.data.rates && Array.isArray(response.data.rates)) {
            ratesData = response.data.rates
            console.log('使用response.data.rates，长度:', ratesData.length)
          } else if (response.data.data && Array.isArray(response.data.data)) {
            ratesData = response.data.data
            console.log('使用response.data.data，长度:', ratesData.length)
          } else if (Array.isArray(response.data)) {
            ratesData = response.data
            console.log('使用response.data，长度:', ratesData.length)
          }
          
          console.log('解析后的汇率数据:', ratesData)
          
          if (ratesData.length > 0) {
            rates.value = ratesData.map(rate => ({
              ...rate,
              isEditing: false
            }))
            originalRates.value = JSON.parse(JSON.stringify(rates.value))
            console.log('成功加载汇率数据，rates数组长度:', rates.value.length)
            console.log('汇率数据详情:', rates.value)
          } else {
            console.log('汇率API返回成功但数据为空，可能是今日没有汇率数据')
            console.log('尝试初始化今日汇率...')
            
            // 尝试初始化今日汇率
            try {
              const initResponse = await api.post('/rates/publish_daily_rates', {
                target_date: new Date().toISOString().split('T')[0]
              })
              
              if (initResponse.data.success) {
                console.log('成功初始化今日汇率，重新加载数据...')
                // 重新加载汇率数据
                await loadRates()
                return
              } else {
                console.log('初始化汇率失败:', initResponse.data.message)
              }
            } catch (initError) {
              console.log('初始化汇率出错:', initError.response?.data || initError.message)
            }
            
            rates.value = []
          }
        } else {
          console.error('汇率API返回失败:', response.data)
          rates.value = []
        }
      } catch (error) {
        console.error('加载汇率失败:', error)
        console.error('错误详情:', error.response?.data || error.message)
        rates.value = []
      } finally {
        ratesLoading.value = false
      }
    }
    
    const startEdit = (index) => {
      rates.value[index].isEditing = true
    }
    
    const saveRate = async (index) => {
      const rate = rates.value[index]
      try {
        const response = await api.put(`/rates/${rate.currency_id}`, {
          buy_rate: rate.buy_rate,
          sell_rate: rate.sell_rate
        })
        if (response.data.success) {
          rate.isEditing = false
          originalRates.value[index] = JSON.parse(JSON.stringify(rate))
        }
      } catch (error) {
        console.error('保存汇率失败:', error)
      }
    }
    
    const cancelEdit = (index) => {
      rates.value[index] = JSON.parse(JSON.stringify(originalRates.value[index]))
      rates.value[index].isEditing = false
    }
    
    const saveAllRates = async () => {
      try {
        const response = await api.post('/rates/set_rate', {
          rates: rates.value.map(rate => ({
            currency_id: rate.currency_id,
            buy_rate: rate.buy_rate,
            sell_rate: rate.sell_rate
          }))
        })
        
        if (response.data.success) {
          console.log('汇率保存成功')
          // 重新加载汇率数据
          loadRates()
        } else {
          console.error('汇率保存失败:', response.data.message)
        }
      } catch (error) {
        console.error('保存汇率失败:', error)
      }
    }
    
    const publishToSetTopBox = async () => {
      try {
        const response = await api.post('/rates/publish_daily_rates', {
          rates: rates.value.map(rate => ({
            currency_id: rate.currency_id,
            buy_rate: rate.buy_rate,
            sell_rate: rate.sell_rate
          }))
        })
        
        if (response.data.success) {
          console.log('汇率发布成功')
        } else {
          console.error('汇率发布失败:', response.data.message)
        }
      } catch (error) {
        console.error('发布汇率失败:', error)
      }
    }
    
    const clearCache = async () => {
      try {
        const response = await api.post('/dashboard/clear-publish-cache')
        
        if (response.data.success) {
          console.log('缓存清除成功')
        } else {
          console.error('缓存清除失败:', response.data.message)
        }
      } catch (error) {
        console.error('清除缓存失败:', error)
      }
    }
    
    onMounted(() => {
      loadCurrencies()
      loadMetrics()
      loadRates()
    })
    
    return {
      selectedCurrency,
      currencies,
      chartData,
      chartOptions,
      localBalance,
      dynamicIncome,
      spreadIncome,
      metricsLoading,
      rates,
      ratesLoading,
      getCurrencyDisplayName, // 添加自定义币种显示函数
      loadRateTrends,
      startEdit,
      saveRate,
      cancelEdit,
      saveAllRates,
      publishToSetTopBox,
      clearCache
    }
  }
}
</script>

<style scoped>
.app-home-view {
  min-height: 100vh;
  background: white;
  padding: 0;
  margin: 0;
  width: 100%;
  overflow-x: hidden;
  position: relative;
}

/* 独立的蓝色指标区域 */
.metrics-container {
  background: #007bff;
  width: 100vw;
  margin-left: calc(-50vw + 50%);
  padding: 40px 0;
  position: relative;
  overflow: hidden;
  box-sizing: border-box;
}

/* 确保完全填满屏幕宽度 */
.metrics-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: #007bff;
  z-index: -1;
}

/* 确保完全填满屏幕宽度 */
.metrics-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: #007bff;
  z-index: -1;
}

/* 指标卡片网格 */
.metrics-grid {
  display: flex;
  gap: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  overflow: hidden;
}

.metric-card {
  background: rgba(255, 255, 255, 0.15);
  border: none;
  border-radius: 0;
  padding: 40px 8px;
  text-align: center;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
  flex: 1;
  min-width: 0;
  position: relative;
  margin: 0 !important;
}

/* 第一个卡片的左边圆角 */
.metric-card:first-child {
  border-top-left-radius: 8px;
  border-bottom-left-radius: 8px;
}

/* 最后一个卡片的右边圆角 */
.metric-card:last-child {
  border-top-right-radius: 8px;
  border-bottom-right-radius: 8px;
}



.metric-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 123, 255, 0.4);
}

.metric-title {
  color: rgba(255, 255, 255, 0.9);
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 12px;
}

.metric-value {
  color: white;
  font-size: 22px;
  font-weight: bold;
  margin: 0;
  line-height: 1.2;
}



/* 汇率趋势图区域 */
.chart-section {
  background: white;
  border-radius: 0;
  padding: 20px;
  margin: 0;
  box-shadow: none;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.chart-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.currency-selector {
  min-width: 120px;
}

/* 汇率发布区域 */
.rates-section {
  background: white;
  border-radius: 0;
  padding: 20px;
  box-shadow: none;
  min-height: 400px;
  display: flex !important;
  flex-direction: column;
  overflow: visible;
  margin-bottom: 20px;
  visibility: visible !important;
  opacity: 1 !important;
}

.rates-header {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin-bottom: 20px;
  flex-shrink: 0;
}

.rate-table-container {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 20px;
  padding-right: 10px;
  max-height: 400px;
}

.rate-table-container::-webkit-scrollbar {
  width: 6px;
}

.rate-table-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.rate-table-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.rate-table-container::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.rate-item {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 10px;
  padding: 15px;
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  gap: 15px;
  min-height: 80px;
}

.rate-item.editing {
  background: #fff;
  border-color: #007bff;
  box-shadow: 0 2px 8px rgba(0, 123, 255, 0.2);
}

.currency-info {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 120px;
}

.currency-flag {
  width: 32px;
  height: 24px;
  border-radius: 4px;
}

.currency-details {
  display: flex;
  flex-direction: column;
}

.currency-code {
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.currency-name {
  color: #666;
  font-size: 12px;
}

.rate-content {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 15px;
}

.rate-inputs {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.input-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.inline-label {
  font-size: 12px;
  color: #666;
  min-width: 50px;
  text-align: right;
}

.rate-input {
  width: 80px;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 6px 10px;
  font-size: 14px;
}

.rate-display {
  width: 80px;
  padding: 6px 10px;
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  font-size: 14px;
  color: #333;
}

.rate-actions {
  display: flex;
  gap: 5px;
  flex-shrink: 0;
}

.edit-actions {
  display: flex;
  gap: 5px;
}

.mobile-btn {
  padding: 8px 12px;
  font-size: 14px;
  border-radius: 6px;
  min-width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #ddd;
  background: white;
  color: #333;
  cursor: pointer;
  transition: all 0.3s ease;
}

.mobile-btn:hover {
  background: #f8f9fa;
  border-color: #007bff;
}

.mobile-btn.btn-outline-primary {
  border-color: #007bff;
  color: #007bff;
}

.mobile-btn.btn-outline-primary:hover {
  background: #007bff;
  color: white;
}

.mobile-btn.btn-success {
  background: #28a745;
  border-color: #28a745;
  color: white;
}

.mobile-btn.btn-success:hover {
  background: #218838;
  border-color: #1e7e34;
}

.mobile-btn.btn-secondary {
  background: #6c757d;
  border-color: #6c757d;
  color: white;
}

.mobile-btn.btn-secondary:hover {
  background: #5a6268;
  border-color: #545b62;
}

.mobile-btn i {
  font-size: 16px;
}

/* 功能按钮 */
.action-buttons {
  display: flex;
  gap: 10px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 10px;
  border-top: 1px solid #e9ecef;
  flex-shrink: 0;
}

.action-buttons .btn {
  flex: 1;
  padding: 12px;
  font-size: 14px;
  border-radius: 8px;
}

/* 功能按钮 */
.action-buttons .btn-primary {
  background: #007bff;
  color: white;
  border: 1px solid #007bff;
}

.action-buttons .btn-primary:hover {
  background: #007bff;
  border-color: #007bff;
}

.action-buttons .btn-success {
  background: #28a745;
  color: white;
  border: 1px solid #28a745;
}

.action-buttons .btn-success:hover {
  background: #218838;
  border-color: #1e7e34;
}

.action-buttons .btn-warning {
  background: #ffc107;
  color: #212529;
  border: 1px solid #ffc107;
}

.action-buttons .btn-warning:hover {
  background: #e0a800;
  border-color: #d39e00;
}

/* 恢复选择框样式 */
.form-check-input {
  width: 1em;
  height: 1em;
  margin-top: 0.25em;
  margin-right: 0.5em;
  vertical-align: top;
  background-color: #fff;
  background-repeat: no-repeat;
  background-position: center;
  background-size: contain;
  border: 1px solid rgba(0, 0, 0, 0.25);
  appearance: none;
  color-adjust: exact;
}

.form-check-input[type="checkbox"] {
  border-radius: 0.25em;
}

.form-check-input[type="checkbox"]:checked {
  background-color: #007bff;
  border-color: #007bff;
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 20 20'%3e%3cpath fill='none' stroke='%23fff' stroke-linecap='round' stroke-linejoin='round' stroke-width='3' d='m6 10 3 3 6-6'/%3e%3c/svg%3e");
}

.form-check-input[type="radio"] {
  border-radius: 50%;
}

.form-check-input[type="radio"]:checked {
  background-color: #007bff;
  border-color: #007bff;
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='-4 -4 8 8'%3e%3ccircle r='2' fill='%23fff'/%3e%3c/svg%3e");
}

.form-check-input:focus {
  border-color: #86b7fe;
  outline: 0;
  box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
}

.form-check-input:disabled {
  pointer-events: none;
  filter: none;
  opacity: 0.5;
}

.form-check-input[type="checkbox"]:disabled:checked {
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 20 20'%3e%3cpath fill='none' stroke='%23fff' stroke-linecap='round' stroke-linejoin='round' stroke-width='3' d='m6 10 3 3 6-6'/%3e%3c/svg%3e");
}

.form-check-input[type="radio"]:disabled:checked {
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='-4 -4 8 8'%3e%3ccircle r='2' fill='%23fff'/%3e%3c/svg%3e");
}

/* 响应式设计 */
@media (max-width: 768px) {
  .app-home-view {
    padding: 10px;
  }
  
  .blue-section {
    border-radius: 10px;
    margin: 0 0 15px 0;
  }
  
  .metrics-grid {
    flex-direction: row;
    gap: 0;
    padding: 15px;
  }
  
  .metric-card {
    flex: 1;
    min-width: 80px;
    padding: 15px 10px;
  }
  
  .metric-title {
    font-size: 12px;
    margin-bottom: 6px;
  }
  
  .metric-value {
    font-size: 14px;
  }
  
  .rates-cards {
    grid-template-columns: 1fr;
    gap: 10px;
  }
  
  .rate-card {
    padding: 12px;
  }
  
  .rate-card-header {
    margin-bottom: 8px;
  }
  
  .rate-currency-code {
    font-size: 13px;
  }
  
  .rate-label {
    font-size: 11px;
  }
  
  .rate-value {
    font-size: 13px;
  }
  
  .rate-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .currency-info {
    min-width: auto;
  }
  
  .rate-inputs {
    width: 100%;
  }
  
  .action-buttons {
    flex-direction: column;
  }
}
</style>

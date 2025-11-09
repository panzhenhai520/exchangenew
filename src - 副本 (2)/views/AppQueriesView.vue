<template>
  <div class="app-queries-view">
    <div class="container-fluid py-3">
      <!-- 页面头部 -->
      <div class="row mb-3">
        <div class="col-12">
          <div class="d-flex justify-content-between align-items-center">
            <h4 class="mb-0 text-primary">
              <i class="fas fa-search me-2"></i>
              {{ currentQueryTitle }}
            </h4>
            <button 
              v-if="currentQueryType !== 'main'" 
              class="btn btn-outline-secondary btn-sm"
              @click="backToMain"
            >
              <i class="fas fa-arrow-left me-1"></i>
              返回
            </button>
          </div>
        </div>
      </div>

      <!-- 主查询菜单 -->
      <div v-if="currentQueryType === 'main'" class="row g-3">
        <div class="col-6">
          <div class="card border-0 shadow-sm h-100" @click="showBalanceQuery">
            <div class="card-body p-3 text-center">
              <div class="query-icon bg-primary mb-3">
                <i class="fas fa-wallet text-white"></i>
              </div>
              <h6 class="card-title">余额查询</h6>
              <p class="card-text small text-muted">查看各币种余额信息</p>
            </div>
          </div>
        </div>

        <div class="col-6">
          <div class="card border-0 shadow-sm h-100" @click="showBalanceAdjustQuery">
            <div class="card-body p-3 text-center">
              <div class="query-icon bg-warning mb-3">
                <i class="fas fa-adjust text-white"></i>
              </div>
              <h6 class="card-title">余额调节查询</h6>
              <p class="card-text small text-muted">查看余额调节记录</p>
            </div>
          </div>
        </div>

        <div class="col-6">
          <div class="card border-0 shadow-sm h-100" @click="showIncomeQuery">
            <div class="card-body p-3 text-center">
              <div class="query-icon bg-success mb-3">
                <i class="fas fa-chart-line text-white"></i>
              </div>
              <h6 class="card-title">动态收入查询</h6>
              <p class="card-text small text-muted">查看收入统计信息</p>
            </div>
          </div>
        </div>

        <div class="col-6">
          <div class="card border-0 shadow-sm h-100" @click="showForeignStockQuery">
            <div class="card-body p-3 text-center">
              <div class="query-icon bg-info mb-3">
                <i class="fas fa-globe text-white"></i>
              </div>
              <h6 class="card-title">库存外币查询</h6>
              <p class="card-text small text-muted">查看外币库存情况</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 余额查询界面 -->
      <div v-else-if="currentQueryType === 'balance'" class="row">
        <div class="col-12">
          <div class="card border-0 shadow-sm">
            <div class="card-header bg-light py-2">
              <h6 class="mb-0">
                <i class="fas fa-wallet text-primary me-2"></i>
                币种余额
              </h6>
            </div>
            <div class="card-body p-0">
              <div v-if="balanceLoading" class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                  <span class="visually-hidden">加载中...</span>
                </div>
              </div>
              <div v-else-if="balanceData.length === 0" class="text-center py-4 text-muted">
                <i class="fas fa-inbox fa-2x mb-2"></i>
                <div>暂无余额数据</div>
              </div>
              <div v-else class="balance-list">
                <div 
                  v-for="balance in balanceData" 
                  :key="balance.currency_code" 
                  class="balance-item"
                >
                  <div class="balance-currency">
                    <CurrencyFlag 
                      :code="balance.currency_code" 
                      :custom-filename="balance.custom_flag_filename"
                      class="me-2" 
                    />
                    <span>{{ getCurrencyDisplayName(balance) }}</span>
                  </div>
                  <div class="balance-amount">
                    {{ formatNumber(balance.balance) }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 余额调节查询界面 -->
      <div v-else-if="currentQueryType === 'balance-adjust'" class="row">
        <div class="col-12">
          <div class="card border-0 shadow-sm">
            <div class="card-header bg-light py-2">
              <h6 class="mb-0">
                <i class="fas fa-adjust text-warning me-2"></i>
                余额调节记录
              </h6>
            </div>
            <div class="card-body p-0">
              <div v-if="adjustLoading" class="text-center py-4">
                <div class="spinner-border text-warning" role="status">
                  <span class="visually-hidden">加载中...</span>
                </div>
              </div>
              <div v-else-if="adjustData.length === 0" class="text-center py-4 text-muted">
                <i class="fas fa-history fa-2x mb-2"></i>
                <div>暂无调节记录</div>
              </div>
              <div v-else class="adjust-list">
                <div 
                  v-for="adjust in adjustData.slice(0, 10)" 
                  :key="adjust.id" 
                  class="adjust-item"
                >
                  <div class="adjust-info">
                    <div class="adjust-currency">
                      <CurrencyFlag 
                        :code="adjust.currency_code" 
                        :custom-filename="adjust.custom_flag_filename"
                        class="me-2" 
                      />
                      <span>{{ getCurrencyDisplayName(adjust) }}</span>
                    </div>
                    <div class="adjust-amount" :class="adjust.adjustment_type === 'increase' ? 'text-success' : 'text-danger'">
                      {{ adjust.adjustment_type === 'increase' ? '+' : '-' }}{{ formatNumber(adjust.adjustment_amount) }}
                    </div>
                  </div>
                  <div class="adjust-details">
                    <div class="adjust-reason">{{ adjust.reason || '无说明' }}</div>
                    <div class="adjust-time">{{ formatDateTime(adjust.created_at) }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 动态收入查询界面 -->
      <div v-else-if="currentQueryType === 'income'" class="row">
        <div class="col-12">
          <div class="card border-0 shadow-sm">
            <div class="card-header bg-light py-2">
              <h6 class="mb-0">
                <i class="fas fa-chart-line text-success me-2"></i>
                收入统计
              </h6>
            </div>
            <div class="card-body p-0">
              <div v-if="incomeLoading" class="text-center py-4">
                <div class="spinner-border text-success" role="status">
                  <span class="visually-hidden">加载中...</span>
                </div>
              </div>
              <div v-else-if="incomeData.length === 0" class="text-center py-4 text-muted">
                <i class="fas fa-chart-bar fa-2x mb-2"></i>
                <div>暂无收入数据</div>
              </div>
              <div v-else class="income-list">
                <div 
                  v-for="income in incomeData.slice(0, 10)" 
                  :key="income.currency_code" 
                  class="income-item"
                >
                  <div class="income-currency">
                    <CurrencyFlag 
                      :code="income.currency_code" 
                      :custom-filename="income.custom_flag_filename"
                      class="me-2" 
                    />
                    <span>{{ getCurrencyDisplayName(income) }}</span>
                  </div>
                  <div class="income-amount text-success">
                    {{ formatNumber(income.total_income) }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 库存外币查询界面 -->
      <div v-else-if="currentQueryType === 'foreign-stock'" class="row">
        <div class="col-12">
          <div class="card border-0 shadow-sm">
            <div class="card-header bg-light py-2">
              <h6 class="mb-0">
                <i class="fas fa-globe text-info me-2"></i>
                外币库存
              </h6>
            </div>
            <div class="card-body p-0">
              <div v-if="stockLoading" class="text-center py-4">
                <div class="spinner-border text-info" role="status">
                  <span class="visually-hidden">加载中...</span>
                </div>
              </div>
              <div v-else-if="stockData.length === 0" class="text-center py-4 text-muted">
                <i class="fas fa-boxes fa-2x mb-2"></i>
                <div>暂无库存数据</div>
              </div>
              <div v-else class="stock-list">
                <div 
                  v-for="stock in stockData.slice(0, 10)" 
                  :key="stock.currency_code" 
                  class="stock-item"
                >
                  <div class="stock-currency">
                    <CurrencyFlag 
                      :code="stock.currency_code" 
                      :custom-filename="stock.custom_flag_filename"
                      class="me-2" 
                    />
                    <span>{{ getCurrencyDisplayName(stock) }}</span>
                  </div>
                  <div class="stock-amount">
                    {{ formatNumber(stock.stock_amount) }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- App角色底部Tab导航 -->

  </div>
</template>

<script>
import { ref, computed } from 'vue'

import CurrencyFlag from '@/components/CurrencyFlag.vue'
import api from '@/services/api'
import { formatDateTime } from '@/utils/formatters'
import { getCurrencyDisplayName as getCurrencyDisplayNameFromUtils } from '@/utils/currencyTranslator'

export default {
  name: 'AppQueriesView',
  components: {
    CurrencyFlag
  },
  setup() {
    // 当前查询类型
    const currentQueryType = ref('main')
    
    // 查询标题映射
    const queryTitles = {
      'main': '查询功能',
      'balance': '余额查询',
      'balance-adjust': '余额调节查询',
      'income': '动态收入查询',
      'foreign-stock': '库存外币查询'
    }
    
    // 计算当前查询标题
    const currentQueryTitle = computed(() => {
      return queryTitles[currentQueryType.value] || '查询功能'
    })
    
    // 查询数据
    const balanceData = ref([])
    const balanceLoading = ref(false)
    const adjustData = ref([])
    const adjustLoading = ref(false)
    const incomeData = ref([])
    const incomeLoading = ref(false)
    const stockData = ref([])
    const stockLoading = ref(false)
    
    // 获取币种显示名称
    const getCurrencyDisplayName = (item) => {
      if (!item) return ''
      
      // 使用新的币种显示函数
      return getCurrencyDisplayNameFromUtils(item.currency_code, item)
    }
    
    // 显示查询界面
    const showBalanceQuery = () => {
      currentQueryType.value = 'balance'
      loadBalanceData()
    }
    
    const showBalanceAdjustQuery = () => {
      currentQueryType.value = 'balance-adjust'
      loadAdjustData()
    }
    
    const showIncomeQuery = () => {
      currentQueryType.value = 'income'
      loadIncomeData()
    }
    
    const showForeignStockQuery = () => {
      currentQueryType.value = 'foreign-stock'
      loadStockData()
    }
    
    // 返回主菜单
    const backToMain = () => {
      currentQueryType.value = 'main'
    }
    
    // 加载余额数据
    const loadBalanceData = async () => {
      balanceLoading.value = true
      try {
        const response = await api.get('/queries/balances')
        if (response.data.success) {
          balanceData.value = response.data.balances || []
        }
      } catch (error) {
        console.error('加载余额数据失败:', error)
        balanceData.value = []
      } finally {
        balanceLoading.value = false
      }
    }
    
    // 加载余额调节数据
    const loadAdjustData = async () => {
      adjustLoading.value = true
      try {
        const response = await api.get('/queries/balance-adjustments')
        if (response.data.success) {
          adjustData.value = response.data.adjustments || []
        }
      } catch (error) {
        console.error('加载余额调节数据失败:', error)
        adjustData.value = []
      } finally {
        adjustLoading.value = false
      }
    }
    
    // 加载收入数据
    const loadIncomeData = async () => {
      incomeLoading.value = true
      try {
        const response = await api.get('/queries/income')
        if (response.data.success) {
          incomeData.value = response.data.income || []
        }
      } catch (error) {
        console.error('加载收入数据失败:', error)
        incomeData.value = []
      } finally {
        incomeLoading.value = false
      }
    }
    
    // 加载库存数据
    const loadStockData = async () => {
      stockLoading.value = true
      try {
        const response = await api.get('/queries/foreign-stock')
        if (response.data.success) {
          stockData.value = response.data.stock || []
        }
      } catch (error) {
        console.error('加载库存数据失败:', error)
        stockData.value = []
      } finally {
        stockLoading.value = false
      }
    }
    
    // 格式化数字
    const formatNumber = (num) => {
      if (num === null || num === undefined) return '0'
      return new Intl.NumberFormat('zh-CN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(num)
    }
    
    return {
      currentQueryType,
      currentQueryTitle,
      balanceData,
      balanceLoading,
      adjustData,
      adjustLoading,
      incomeData,
      incomeLoading,
      stockData,
      stockLoading,
      showBalanceQuery,
      showBalanceAdjustQuery,
      showIncomeQuery,
      showForeignStockQuery,
      backToMain,
      formatNumber,
      formatDateTime,
      getCurrencyDisplayName
    }
  }
}
</script>

<style scoped>
.app-queries-view {
  background: white;
  min-height: 100vh;
  padding-bottom: 80px;
  overflow-y: auto;
  padding: 0;
}

.app-queries-view .card {
  border-radius: 15px;
  border: none;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  cursor: pointer;
}

.app-queries-view .card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

.query-icon {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  margin: 0 auto;
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.card-text {
  font-size: 0.8rem;
  line-height: 1.3;
}

/* 余额列表样式 */
.balance-list {
  max-height: 400px;
  overflow-y: auto;
}

.balance-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  transition: background-color 0.2s ease;
}

.balance-item:last-child {
  border-bottom: none;
}

.balance-item:hover {
  background-color: #f8f9fa;
}

.balance-currency {
  display: flex;
  align-items: center;
  font-weight: 600;
  color: #495057;
}

.balance-amount {
  font-size: 1rem;
  font-weight: 600;
  color: #28a745;
}

/* 余额调节列表样式 */
.adjust-list {
  max-height: 400px;
  overflow-y: auto;
}

.adjust-item {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  transition: background-color 0.2s ease;
}

.adjust-item:last-child {
  border-bottom: none;
}

.adjust-item:hover {
  background-color: #f8f9fa;
}

.adjust-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.adjust-currency {
  display: flex;
  align-items: center;
  font-weight: 600;
  color: #495057;
}

.adjust-amount {
  font-size: 1rem;
  font-weight: 600;
}

.adjust-details {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  color: #6c757d;
}

/* 收入列表样式 */
.income-list {
  max-height: 400px;
  overflow-y: auto;
}

.income-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  transition: background-color 0.2s ease;
}

.income-item:last-child {
  border-bottom: none;
}

.income-item:hover {
  background-color: #f8f9fa;
}

.income-currency {
  display: flex;
  align-items: center;
  font-weight: 600;
  color: #495057;
}

.income-amount {
  font-size: 1rem;
  font-weight: 600;
}

/* 库存列表样式 */
.stock-list {
  max-height: 400px;
  overflow-y: auto;
}

.stock-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  transition: background-color 0.2s ease;
}

.stock-item:last-child {
  border-bottom: none;
}

.stock-item:hover {
  background-color: #f8f9fa;
}

.stock-currency {
  display: flex;
  align-items: center;
  font-weight: 600;
  color: #495057;
}

.stock-amount {
  font-size: 1rem;
  font-weight: 600;
  color: #17a2b8;
}

/* 手机端响应式调整 */
@media (max-width: 768px) {
  .app-queries-view .container-fluid {
    padding-left: 10px;
    padding-right: 10px;
  }
  
  .app-queries-view .card-body {
    padding: 1rem;
  }
  
  .query-icon {
    width: 40px;
    height: 40px;
    font-size: 16px;
  }
  
  .card-title {
    font-size: 0.9rem;
  }
  
  .card-text {
    font-size: 0.75rem;
  }
}
</style> 
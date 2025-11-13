<template>
  <div class="container-fluid py-4">
    <div class="card">
      <div class="card-header bg-info text-white">
        <h5 class="mb-0">
          <i class="fas fa-chart-line me-2"></i>
          BOT报告管理
        </h5>
      </div>
      <div class="card-body">
        <!-- 年月选择 -->
        <div class="row mb-3">
          <div class="col-md-2">
            <label class="form-label">年份</label>
            <select class="form-select" v-model="queryYear" @change="loadData">
              <option v-for="y in availableYears" :key="y" :value="y">{{ y }}</option>
            </select>
          </div>
          <div class="col-md-2">
            <label class="form-label">月份</label>
            <select class="form-select" v-model="queryMonth" @change="loadData">
              <option v-for="m in 12" :key="m" :value="m">{{ m }}月</option>
            </select>
          </div>
          <div class="col-md-3 d-flex align-items-end">
            <button class="btn btn-primary me-2" @click="loadData">
              <i class="fas fa-search me-1"></i>查询
            </button>
            <button class="btn btn-success" @click="downloadReport">
              <i class="fas fa-download me-1"></i>下载完整报表
            </button>
          </div>
        </div>

        <!-- 统计汇总 -->
        <div class="row mb-4">
          <div class="col-md-6">
            <div class="card border-success">
              <div class="card-body">
                <h6 class="text-success mb-3">
                  <i class="fas fa-arrow-down me-2"></i>买入外币汇总
                </h6>
                <div class="row">
                  <div class="col-6">
                    <div class="text-muted small">交易笔数</div>
                    <h4 class="mb-0">{{ buyFXSummary.count }}</h4>
                  </div>
                  <div class="col-6">
                    <div class="text-muted small">交易金额</div>
                    <h4 class="mb-0">{{ formatAmount(buyFXSummary.amount) }}</h4>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="col-md-6">
            <div class="card border-danger">
              <div class="card-body">
                <h6 class="text-danger mb-3">
                  <i class="fas fa-arrow-up me-2"></i>卖出外币汇总
                </h6>
                <div class="row">
                  <div class="col-6">
                    <div class="text-muted small">交易笔数</div>
                    <h4 class="mb-0">{{ sellFXSummary.count }}</h4>
                  </div>
                  <div class="col-6">
                    <div class="text-muted small">交易金额</div>
                    <h4 class="mb-0">{{ formatAmount(sellFXSummary.amount) }}</h4>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 标签切换 -->
        <ul class="nav nav-tabs mb-3" role="tablist">
          <li class="nav-item">
            <button 
              class="nav-link" 
              :class="{ active: activeTab === 'buy' }"
              @click="activeTab = 'buy'"
            >
              <i class="fas fa-arrow-down me-1"></i>买入外币 (Buy FX)
            </button>
          </li>
          <li class="nav-item">
            <button 
              class="nav-link" 
              :class="{ active: activeTab === 'sell' }"
              @click="activeTab = 'sell'"
            >
              <i class="fas fa-arrow-up me-1"></i>卖出外币 (Sell FX)
            </button>
          </li>
        </ul>

        <!-- 买入外币表格 -->
        <div v-show="activeTab === 'buy'">
          <div class="d-flex justify-content-between align-items-center mb-3">
            <h6 class="mb-0">买入外币明细</h6>
            <button class="btn btn-sm btn-success" @click="exportExcel('buy')">
              <i class="fas fa-file-excel me-1"></i>导出Excel
            </button>
          </div>
          
          <div class="table-responsive">
            <table class="table table-striped table-hover">
              <thead class="table-light">
                <tr>
                  <th>交易号</th>
                  <th>币种</th>
                  <th>外币金额</th>
                  <th>汇率</th>
                  <th>泰铢金额</th>
                  <th>交易时间</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="loadingBuy">
                  <td colspan="6" class="text-center py-4">
                    <div class="spinner-border text-primary" role="status"></div>
                  </td>
                </tr>
                <tr v-else-if="!buyFXData || buyFXData.length === 0">
                  <td colspan="6" class="text-center text-muted py-4">
                    暂无数据
                  </td>
                </tr>
                <tr v-else v-for="item in buyFXData" :key="item.transaction_no">
                  <td>{{ item.transaction_no }}</td>
                  <td><span class="badge bg-primary">{{ item.currency_code }}</span></td>
                  <td class="text-end">{{ formatAmount(item.foreign_amount) }}</td>
                  <td class="text-end">{{ item.exchange_rate }}</td>
                  <td class="text-end">{{ formatAmount(item.local_amount) }}</td>
                  <td>{{ formatDateTime(item.transaction_date) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- 卖出外币表格 -->
        <div v-show="activeTab === 'sell'">
          <div class="d-flex justify-content-between align-items-center mb-3">
            <h6 class="mb-0">卖出外币明细</h6>
            <button class="btn btn-sm btn-success" @click="exportExcel('sell')">
              <i class="fas fa-file-excel me-1"></i>导出Excel
            </button>
          </div>
          
          <div class="table-responsive">
            <table class="table table-striped table-hover">
              <thead class="table-light">
                <tr>
                  <th>交易号</th>
                  <th>币种</th>
                  <th>外币金额</th>
                  <th>汇率</th>
                  <th>泰铢金额</th>
                  <th>交易时间</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="loadingSell">
                  <td colspan="6" class="text-center py-4">
                    <div class="spinner-border text-primary" role="status"></div>
                  </td>
                </tr>
                <tr v-else-if="!sellFXData || sellFXData.length === 0">
                  <td colspan="6" class="text-center text-muted py-4">
                    暂无数据
                  </td>
                </tr>
                <tr v-else v-for="item in sellFXData" :key="item.transaction_no">
                  <td>{{ item.transaction_no }}</td>
                  <td><span class="badge bg-danger">{{ item.currency_code }}</span></td>
                  <td class="text-end">{{ formatAmount(item.foreign_amount) }}</td>
                  <td class="text-end">{{ item.exchange_rate }}</td>
                  <td class="text-end">{{ formatAmount(item.local_amount) }}</td>
                  <td>{{ formatDateTime(item.transaction_date) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'

export default {
  name: 'BOTReportSimple',
  setup() {
    const today = new Date()
    const queryYear = ref(today.getFullYear())
    const queryMonth = ref(today.getMonth() + 1)
    const availableYears = ref([2023, 2024, 2025, 2026])
    const activeTab = ref('buy')
    const loadingBuy = ref(false)
    const loadingSell = ref(false)
    const buyFXData = ref([])
    const sellFXData = ref([])

    const buyFXSummary = computed(() => {
      // 确保是数组类型
      if (!Array.isArray(buyFXData.value) || buyFXData.value.length === 0) {
        return { count: 0, amount: 0 }
      }
      return {
        count: buyFXData.value.length,
        amount: buyFXData.value.reduce((sum, item) => sum + parseFloat(item.local_amount || 0), 0)
      }
    })

    const sellFXSummary = computed(() => {
      // 确保是数组类型
      if (!Array.isArray(sellFXData.value) || sellFXData.value.length === 0) {
        return { count: 0, amount: 0 }
      }
      return {
        count: sellFXData.value.length,
        amount: sellFXData.value.reduce((sum, item) => sum + parseFloat(item.local_amount || 0), 0)
      }
    })

    const loadBuyFX = async () => {
      loadingBuy.value = true
      try {
        const response = await api.get('bot/t1-buy-fx', {
          params: {
            year: queryYear.value,
            month: queryMonth.value
          }
        })
        if (response.data.success) {
          // 后端直接返回data数组
          const data = response.data.data
          buyFXData.value = Array.isArray(data) ? data : []
          console.log(`加载买入外币成功: ${buyFXData.value.length} 条记录`)
        }
      } catch (error) {
        console.error('加载买入外币失败:', error)
        buyFXData.value = []
      } finally {
        loadingBuy.value = false
      }
    }

    const loadSellFX = async () => {
      loadingSell.value = true
      try {
        const response = await api.get('bot/t1-sell-fx', {
          params: {
            year: queryYear.value,
            month: queryMonth.value
          }
        })
        if (response.data.success) {
          // 后端直接返回data数组
          const data = response.data.data
          sellFXData.value = Array.isArray(data) ? data : []
          console.log(`加载卖出外币成功: ${sellFXData.value.length} 条记录`)
        }
      } catch (error) {
        console.error('加载卖出外币失败:', error)
        sellFXData.value = []
      } finally {
        loadingSell.value = false
      }
    }

    const loadData = () => {
      loadBuyFX()
      loadSellFX()
    }

    const exportExcel = () => {
      // 导出完整BOT报表（包含所有工作表）
      downloadReport()
    }
    
    const downloadReport = async () => {
      try {
        const response = await api.get('bot/export-buy-fx', {
          params: {
            month: queryMonth.value,
            year: queryYear.value
          },
          responseType: 'blob'
        })
        
        // 创建下载链接
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `BOT_Report_${queryYear.value}${String(queryMonth.value).padStart(2, '0')}.xlsx`)
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
        
        alert('BOT报表下载成功！')
      } catch (error) {
        console.error('下载失败:', error)
        alert('下载失败: ' + (error.response?.data?.message || error.message))
      }
    }

    const formatAmount = (amount) => {
      if (!amount) return '0.00'
      return parseFloat(amount).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      })
    }

    const formatDateTime = (dt) => {
      if (!dt) return '-'
      // 后端已经返回格式化的字符串，直接显示
      if (typeof dt === 'string') return dt
      return new Date(dt).toLocaleString('zh-CN')
    }

    onMounted(() => {
      loadData()
    })

    return {
      queryYear,
      queryMonth,
      availableYears,
      activeTab,
      loadingBuy,
      loadingSell,
      buyFXData,
      sellFXData,
      buyFXSummary,
      sellFXSummary,
      loadData,
      exportExcel,
      downloadReport,
      formatAmount,
      formatDateTime
    }
  }
}
</script>

<style scoped>
.nav-tabs .nav-link {
  cursor: pointer;
}

.card-body h4 {
  font-size: 1.5rem;
  font-weight: 600;
}
</style>


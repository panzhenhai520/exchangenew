<template>
  <div class="container-fluid t1-submit-page">
    <div class="row">
      <div class="col-12">
        <div class="d-flex justify-content-between align-items-center mb-4" style="margin-top: 20px;">
          <h2 class="page-title-bold">
            <font-awesome-icon :icon="['fas', 'calendar-day']" class="me-2" />
            {{ $t('bot.t1_submit.title') }}
          </h2>
        </div>

        <!-- 年月选择卡片 -->
        <div class="card mb-4">
          <div class="card-body">
            <div class="row align-items-end">
              <div class="col-md-2">
                <label class="form-label">年份</label>
                <select class="form-select" v-model="selectedYear" @change="loadData">
                  <option v-for="y in availableYears" :key="y" :value="y">{{ y }}</option>
                </select>
              </div>
              <div class="col-md-2">
                <label class="form-label">月份</label>
                <select class="form-select" v-model="selectedMonth" @change="loadData">
                  <option v-for="m in 12" :key="m" :value="m">{{ m }}月</option>
                </select>
              </div>
              <div class="col-md-4">
                <button class="btn btn-primary me-2" @click="loadData">
                  <font-awesome-icon :icon="['fas', 'search']" class="me-2" />
                  {{ $t('bot.t1_submit.query_button') }}
                </button>
                <button class="btn btn-success" @click="downloadBOTReport">
                  <font-awesome-icon :icon="['fas', 'download']" class="me-1" />
                  下载完整BOT报表
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- 数据加载状态 -->
        <div v-if="loading" class="text-center py-5">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">{{ $t('common.loading') }}</span>
          </div>
          <p class="mt-2 text-muted">{{ $t('bot.t1_submit.loading') }}</p>
        </div>

        <!-- 数据展示区域 -->
        <div v-else-if="buyFXData || sellFXData">
          <!-- 买入外币报表 -->
          <div class="card mb-4">
            <div class="card-header bg-success text-white d-flex justify-content-between align-items-center">
              <h5 class="mb-0">
                <font-awesome-icon :icon="['fas', 'arrow-down']" class="me-2" />
                买入外币 (Buy FX)
                <span v-if="buyFXData && buyFXData.overdue_count > 0" class="badge bg-danger ms-2">
                  {{ buyFXData.overdue_count }} 条超期
                </span>
              </h5>
              <div>
                <button class="btn btn-warning btn-sm me-2" @click="markBuyFXReported" 
                        :disabled="!hasSelectedBuyFX"
                        v-if="buyFXData && buyFXData.unreported_count > 0">
                  <font-awesome-icon :icon="['fas', 'check']" class="me-1" />
                  标记已上报
                </button>
                <button class="btn btn-light btn-sm" @click="exportBuyFX" :disabled="!buyFXData || buyFXData.total_count === 0">
                  <font-awesome-icon :icon="['fas', 'file-excel']" class="me-1" />
                  导出Excel
                </button>
              </div>
            </div>
            <div class="card-body">
              <div v-if="buyFXData && buyFXData.total_count > 0">
                <div class="row mb-3">
                  <div class="col-md-3">
                    <div class="stat-box">
                      <div class="stat-label">总记录数</div>
                      <div class="stat-value">{{ buyFXData.total_count }}</div>
                    </div>
                  </div>
                  <div class="col-md-3">
                    <div class="stat-box">
                      <div class="stat-label">总金额(THB)</div>
                      <div class="stat-value">{{ formatAmount(buyFXData.total_amount_thb) }}</div>
                    </div>
                  </div>
                  <div class="col-md-3">
                    <div class="stat-box bg-primary text-white">
                      <div class="stat-label">未上报</div>
                      <div class="stat-value">{{ buyFXData.unreported_count || 0 }}</div>
                    </div>
                  </div>
                  <div class="col-md-3">
                    <div class="stat-box bg-danger text-white">
                      <div class="stat-label">⚠️ 超期未报</div>
                      <div class="stat-value">{{ buyFXData.overdue_count || 0 }}</div>
                    </div>
                  </div>
                </div>

                <div class="table-responsive">
                  <table class="table table-striped table-hover">
                    <thead>
                      <tr>
                        <th>{{ $t('bot.t1_submit.transaction_no') }}</th>
                        <th>{{ $t('bot.t1_submit.transaction_time') }}</th>
                        <th>{{ $t('bot.t1_submit.customer_id') }}</th>
                        <th>{{ $t('bot.t1_submit.currency') }}</th>
                        <th class="text-end">{{ $t('bot.t1_submit.foreign_amount') }}</th>
                        <th class="text-end">{{ $t('bot.t1_submit.local_amount') }}</th>
                        <th class="text-end">{{ $t('bot.t1_submit.rate') }}</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="item in buyFXData.items" :key="item.id" 
                          :class="getRowClass(item)">
                        <td>
                          <input type="checkbox" v-model="item.selected" class="form-check-input me-2" v-if="!item.is_reported" />
                          <small>{{ item.transaction_no }}</small>
                        </td>
                        <td><small>{{ formatDate(item.transaction_date) }}</small></td>
                        <td>{{ item.customer_id }}</td>
                        <td><strong>{{ item.currency_code }}</strong></td>
                        <td class="text-end">{{ formatAmount(item.foreign_amount) }}</td>
                        <td class="text-end">{{ formatAmount(item.local_amount) }}</td>
                        <td class="text-end"><small>{{ formatRate(item.exchange_rate) }}</small></td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
              <div v-else class="text-center py-4 text-muted">
                <font-awesome-icon :icon="['fas', 'inbox']" size="2x" class="mb-2" />
                <p>{{ $t('bot.t1_submit.no_buy_data') }}</p>
              </div>
            </div>
          </div>

          <!-- 卖出外币报表 -->
          <div class="card">
            <div class="card-header bg-danger text-white d-flex justify-content-between align-items-center">
              <h5 class="mb-0">
                <font-awesome-icon :icon="['fas', 'arrow-up']" class="me-2" />
                卖出外币 (Sell FX)
                <span v-if="sellFXData && sellFXData.overdue_count > 0" class="badge bg-warning ms-2">
                  {{ sellFXData.overdue_count }} 条超期
                </span>
              </h5>
              <div>
                <button class="btn btn-warning btn-sm me-2" @click="markSellFXReported" 
                        :disabled="!hasSelectedSellFX"
                        v-if="sellFXData && sellFXData.unreported_count > 0">
                  <font-awesome-icon :icon="['fas', 'check']" class="me-1" />
                  标记已上报
                </button>
                <button class="btn btn-light btn-sm" @click="exportSellFX" :disabled="!sellFXData || sellFXData.total_count === 0">
                  <font-awesome-icon :icon="['fas', 'file-excel']" class="me-1" />
                  导出Excel
                </button>
              </div>
            </div>
            <div class="card-body">
              <div v-if="sellFXData && sellFXData.total_count > 0">
                <div class="row mb-3">
                  <div class="col-md-4">
                    <div class="stat-box">
                      <div class="stat-label">{{ $t('bot.t1_submit.total_count') }}</div>
                      <div class="stat-value">{{ sellFXData.total_count }}</div>
                    </div>
                  </div>
                  <div class="col-md-4">
                    <div class="stat-box">
                      <div class="stat-label">{{ $t('bot.t1_submit.total_amount_thb') }}</div>
                      <div class="stat-value">{{ formatAmount(sellFXData.total_amount_thb) }}</div>
                    </div>
                  </div>
                  <div class="col-md-4">
                    <div class="stat-box">
                      <div class="stat-label">{{ $t('bot.t1_submit.report_date') }}</div>
                      <div class="stat-value">{{ sellFXData.date }}</div>
                    </div>
                  </div>
                </div>

                <div class="table-responsive">
                  <table class="table table-striped table-hover">
                    <thead>
                      <tr>
                        <th>{{ $t('bot.t1_submit.transaction_no') }}</th>
                        <th>{{ $t('bot.t1_submit.transaction_time') }}</th>
                        <th>{{ $t('bot.t1_submit.customer_id') }}</th>
                        <th>{{ $t('bot.t1_submit.currency') }}</th>
                        <th class="text-end">{{ $t('bot.t1_submit.foreign_amount') }}</th>
                        <th class="text-end">{{ $t('bot.t1_submit.local_amount') }}</th>
                        <th class="text-end">{{ $t('bot.t1_submit.rate') }}</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="item in sellFXData.items" :key="item.id"
                          :class="getRowClass(item)">
                        <td>
                          <input type="checkbox" v-model="item.selected" class="form-check-input me-2" v-if="!item.is_reported" />
                          <small>{{ item.transaction_no }}</small>
                        </td>
                        <td><small>{{ formatDate(item.transaction_date) }}</small></td>
                        <td>{{ item.customer_id }}</td>
                        <td><strong>{{ item.currency_code }}</strong></td>
                        <td class="text-end">{{ formatAmount(item.foreign_amount) }}</td>
                        <td class="text-end">{{ formatAmount(item.local_amount) }}</td>
                        <td class="text-end"><small>{{ formatRate(item.exchange_rate) }}</small></td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
              <div v-else class="text-center py-4 text-muted">
                <font-awesome-icon :icon="['fas', 'inbox']" size="2x" class="mb-2" />
                <p>{{ $t('bot.t1_submit.no_sell_data') }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 初始提示 -->
        <div v-else class="card">
          <div class="card-body text-center py-5">
            <font-awesome-icon :icon="['fas', 'search']" size="3x" class="text-muted mb-3" />
            <p class="text-muted">{{ $t('bot.t1_submit.select_date_hint') }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import botService from '@/services/api/botService';
import api from '@/services/api';

export default {
  name: 'T1SubmitView',
  setup() {
    const loading = ref(false);
    const today = new Date();
    const selectedYear = ref(today.getFullYear());
    const selectedMonth = ref(today.getMonth() + 1);
    const availableYears = ref([2023, 2024, 2025, 2026]);
    const buyFXData = ref(null);
    const sellFXData = ref(null);

    // 格式化日期
    const formatDate = (dateStr) => {
      if (!dateStr) return '';
      const date = new Date(dateStr);
      return date.toISOString().split('T')[0];
    };
    
    // 格式化金额
    const formatAmount = (amount) => {
      if (!amount) return '0.00';
      return parseFloat(amount).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      });
    };

    // 格式化汇率
    const formatRate = (rate) => {
      if (!rate) return '0.0000';
      return parseFloat(rate).toFixed(4);
    };

    // 格式化日期时间
    const formatDateTime = (datetime) => {
      if (!datetime) return '';
      const date = new Date(datetime);
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    };

    // 加载数据
    const loadData = async () => {
      loading.value = true;
      try {
        const yearMonth = `${selectedYear.value}-${String(selectedMonth.value).padStart(2, '0')}`;
        
        const [buyResponse, sellResponse] = await Promise.all([
          botService.getT1BuyFX(yearMonth),
          botService.getT1SellFX(yearMonth)
        ]);

        if (buyResponse.data.success) {
          buyFXData.value = buyResponse.data.data;
        }

        if (sellResponse.data.success) {
          sellFXData.value = sellResponse.data.data;
        }
      } catch (error) {
        console.error('加载数据失败:', error);
        alert('加载数据失败: ' + (error.response?.data?.message || error.message));
      } finally {
        loading.value = false;
      }
    };

    // 导出买入外币Excel
    const exportBuyFX = async () => {
      downloadBOTReport();
    };

    // 导出卖出外币Excel
    const exportSellFX = async () => {
      downloadBOTReport();
    };
    
    // 下载完整BOT报表（从manager目录）
    const downloadBOTReport = async () => {
      try {
        const response = await botService.exportBuyFX(
          null,  // date参数不再使用
          selectedMonth.value,
          selectedYear.value
        );

        // 创建下载链接
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        const filename = `BOT_Report_${selectedYear.value}${String(selectedMonth.value).padStart(2, '0')}.xlsx`;
        link.setAttribute('download', filename);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
        
        alert('BOT完整报表下载成功！');
      } catch (error) {
        console.error('导出Excel失败:', error);
        alert('导出Excel失败: ' + (error.response?.data?.message || error.message));
      }
    };

    // 计算是否有选中的记录
    const hasSelectedBuyFX = computed(() => {
      return buyFXData.value && buyFXData.value.items && 
             buyFXData.value.items.some(item => item.selected);
    });
    
    const hasSelectedSellFX = computed(() => {
      return sellFXData.value && sellFXData.value.items && 
             sellFXData.value.items.some(item => item.selected);
    });
    
    // 获取行的CSS类（颜色标记）
    const getRowClass = (item) => {
      if (item.is_reported) {
        return '';  // 已上报：正常显示
      }
      if (item.days_diff > 1) {
        return 'table-danger';  // 超期未报：红色
      }
      return 'table-info';  // 未上报：蓝色
    };
    
    // 标记Buy FX为已上报
    const markBuyFXReported = async () => {
      if (!buyFXData.value || !buyFXData.value.items) return;
      
      const selectedIds = buyFXData.value.items
        .filter(item => item.selected)
        .map(item => item.id);
      
      if (selectedIds.length === 0) {
        alert('请先选择要标记的记录');
        return;
      }
      
      if (!confirm(`确定要标记 ${selectedIds.length} 条记录为已上报吗？`)) {
        return;
      }
      
      try {
        const response = await api.post('bot/mark-reported', {
          table: 'BOT_BuyFX',
          ids: selectedIds
        });
        
        if (response.data.success) {
          alert(`成功标记${response.data.updated_count}条记录为已上报`);
          loadData();  // 重新加载数据
        }
      } catch (error) {
        console.error('标记失败:', error);
        alert('标记失败: ' + (error.response?.data?.message || error.message));
      }
    };
    
    // 标记Sell FX为已上报
    const markSellFXReported = async () => {
      if (!sellFXData.value || !sellFXData.value.items) return;
      
      const selectedIds = sellFXData.value.items
        .filter(item => item.selected)
        .map(item => item.id);
      
      if (selectedIds.length === 0) {
        alert('请先选择要标记的记录');
        return;
      }
      
      if (!confirm(`确定要标记 ${selectedIds.length} 条记录为已上报吗？`)) {
        return;
      }
      
      try {
        const response = await api.post('bot/mark-reported', {
          table: 'BOT_SellFX',
          ids: selectedIds
        });
        
        if (response.data.success) {
          alert(`成功标记${response.data.updated_count}条记录为已上报`);
          loadData();  // 重新加载数据
        }
      } catch (error) {
        console.error('标记失败:', error);
        alert('标记失败: ' + (error.response?.data?.message || error.message));
      }
    };

    onMounted(() => {
      // 页面加载时自动查询当前月数据
      loadData();
    });

    return {
      loading,
      selectedYear,
      selectedMonth,
      availableYears,
      buyFXData,
      sellFXData,
      hasSelectedBuyFX,
      hasSelectedSellFX,
      getRowClass,
      formatDate,
      formatAmount,
      formatRate,
      formatDateTime,
      loadData,
      exportBuyFX,
      exportSellFX,
      downloadBOTReport,
      markBuyFXReported,
      markSellFXReported
    };
  }
};
</script>

<style scoped>
.t1-submit-page {
  padding: 0 1rem;
}

.page-title-bold {
  font-weight: 700;
  color: #212529;
}

.stat-box {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1rem;
  text-align: center;
}

.stat-label {
  font-size: 0.875rem;
  color: #6c757d;
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #212529;
}

.table th {
  background-color: #f8f9fa;
  font-weight: 600;
}
</style>

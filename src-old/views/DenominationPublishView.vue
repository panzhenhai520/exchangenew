<template>
  <div class="denomination-publish-view">
    <div class="container-fluid">
      <!-- 页面标题 -->
      <div class="row mb-4">
        <div class="col-12">
          <div class="d-flex justify-content-between align-items-center">
            <h2 class="mb-0">
              <i class="fas fa-tv me-2"></i>
              面值汇率发布管理
            </h2>
            <div class="btn-group">
              <button 
                class="btn btn-primary"
                @click="publishAllSelected"
                :disabled="loading || selectedCurrencies.length === 0"
              >
                <i class="fas fa-broadcast-tower me-1"></i>
                发布选中币种到机顶盒
              </button>
              <button 
                class="btn btn-success"
                @click="goToPreview"
                :disabled="loading || currenciesWithDenominations.length === 0"
              >
                <i class="fas fa-magic me-1"></i>
                发布到机顶盒
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 统计信息 -->
      <div class="row mb-4">
        <div class="col-md-3">
          <div class="card bg-primary text-white">
            <div class="card-body">
              <div class="d-flex justify-content-between">
                <div>
                  <h6 class="card-title">已设置面值汇率</h6>
                  <h3 class="mb-0">{{ currenciesWithDenominations.length }}</h3>
                </div>
                <div class="align-self-center">
                  <i class="fas fa-coins fa-2x"></i>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="card bg-success text-white">
            <div class="card-body">
              <div class="d-flex justify-content-between">
                <div>
                  <h6 class="card-title">已选中发布</h6>
                  <h3 class="mb-0">{{ selectedCurrencies.length }}</h3>
                </div>
                <div class="align-self-center">
                  <i class="fas fa-check-circle fa-2x"></i>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="card bg-info text-white">
            <div class="card-body">
              <div class="d-flex justify-content-between">
                <div>
                  <h6 class="card-title">总面值数量</h6>
                  <h3 class="mb-0">{{ totalDenominations }}</h3>
                </div>
                <div class="align-self-center">
                  <i class="fas fa-list fa-2x"></i>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="card bg-warning text-white">
            <div class="card-body">
              <div class="d-flex justify-content-between">
                <div>
                  <h6 class="card-title">今日发布次数</h6>
                  <h3 class="mb-0">{{ todayPublishCount }}</h3>
                </div>
                <div class="align-self-center">
                  <i class="fas fa-history fa-2x"></i>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 币种列表 -->
      <div class="row">
        <div class="col-12">
          <div class="card">
            <div class="card-header">
              <div class="d-flex justify-content-between align-items-center">
                <h5 class="mb-0">面值汇率设置情况</h5>
                <div class="btn-group">
                  <button 
                    class="btn btn-sm btn-outline-primary"
                    @click="selectAll"
                    :disabled="currenciesWithDenominations.length === 0"
                  >
                    <i class="fas fa-check-square me-1"></i>
                    全选
                  </button>
                  <button 
                    class="btn btn-sm btn-outline-secondary"
                    @click="selectNone"
                  >
                    <i class="fas fa-square me-1"></i>
                    全不选
                  </button>
                  <button 
                    class="btn btn-sm btn-outline-info"
                    @click="refreshData"
                    :disabled="loading"
                  >
                    <i class="fas fa-sync-alt me-1"></i>
                    刷新
                  </button>
                </div>
              </div>
            </div>
            <div class="card-body p-0">
              <div v-if="loading" class="text-center p-4">
                <div class="spinner-border" role="status">
                  <span class="visually-hidden">加载中...</span>
                </div>
                <p class="mt-2">正在加载面值汇率数据...</p>
              </div>
              
              <div v-else-if="currenciesWithDenominations.length === 0" class="text-center p-4">
                <i class="fas fa-info-circle fa-3x text-muted mb-3"></i>
                <h5 class="text-muted">暂无面值汇率设置</h5>
                <p class="text-muted">请先在各币种中设置面值汇率</p>
                <button class="btn btn-primary" @click="$router.push('/rates')">
                  <i class="fas fa-cog me-1"></i>
                  去设置面值汇率
                </button>
              </div>
              
              <div v-else class="table-responsive">
                <table class="table table-hover mb-0">
                  <thead class="table-light">
                    <tr>
                      <th width="50">
                        <input 
                          type="checkbox" 
                          :checked="isAllSelected"
                          @change="toggleSelectAll"
                          class="form-check-input"
                        >
                      </th>
                      <th>币种</th>
                      <th>面值设置</th>
                      <th>汇率范围</th>
                      <th>最后更新</th>
                      <th>今日状态</th>
                      <th>操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="currency in currenciesWithDenominations" :key="currency.id">
                      <td>
                        <input 
                          type="checkbox" 
                          :value="currency.id"
                          v-model="selectedCurrencies"
                          class="form-check-input"
                        >
                      </td>
                      <td>
                        <div class="d-flex align-items-center">
                          <img 
                            :src="getCurrencyFlag(currency)" 
                            :alt="currency.currency_code"
                            class="currency-flag me-2"
                            @error="handleFlagError"
                          >
                          <div>
                            <div class="fw-bold">{{ currency.currency_code }}</div>
                            <div class="text-muted small">{{ currency.currency_name }}</div>
                          </div>
                        </div>
                      </td>
                      <td>
                        <div class="denomination-list">
                          <span 
                            v-for="denom in currency.denominations" 
                            :key="denom.id"
                            class="badge bg-primary me-1 mb-1"
                          >
                            {{ formatDenominationValue(denom.denomination_value) }}
                            {{ denom.denomination_type === 'bill' ? '纸币' : '硬币' }}
                          </span>
                        </div>
                      </td>
                      <td>
                        <div class="rate-range">
                          <div class="text-success">
                            <i class="fas fa-arrow-up me-1"></i>
                            买入: {{ currency.min_buy_rate }} - {{ currency.max_buy_rate }}
                          </div>
                          <div class="text-danger">
                            <i class="fas fa-arrow-down me-1"></i>
                            卖出: {{ currency.min_sell_rate }} - {{ currency.max_sell_rate }}
                          </div>
                        </div>
                      </td>
                      <td>
                        <div class="text-muted small">
                          {{ formatDateTime(currency.last_updated) }}
                        </div>
                      </td>
                      <td>
                        <span v-if="currency.published_today" class="badge bg-success">
                          <i class="fas fa-check me-1"></i>
                          已发布
                        </span>
                        <span v-else class="badge bg-secondary">
                          <i class="fas fa-clock me-1"></i>
                          未发布
                        </span>
                      </td>
                      <td>
                        <div class="btn-group btn-group-sm">
                          <button 
                            class="btn btn-outline-primary"
                            @click="viewDetails(currency)"
                            title="查看详情"
                          >
                            <i class="fas fa-eye"></i>
                          </button>
                          <button 
                            class="btn btn-outline-success"
                            @click="publishSingle(currency)"
                            :disabled="loading"
                            title="单独发布"
                          >
                            <i class="fas fa-broadcast-tower"></i>
                          </button>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 详情模态框 -->
    <div class="modal fade" id="detailModal" tabindex="-1" aria-labelledby="detailModalLabel" aria-hidden="true">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="detailModalLabel">
              <i class="fas fa-info-circle me-2"></i>
              {{ selectedCurrency?.currency_code }} 面值汇率详情
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <div v-if="selectedCurrency">
              <div class="table-responsive">
                <table class="table table-bordered">
                  <thead class="table-light">
                    <tr>
                      <th>面值</th>
                      <th>类型</th>
                      <th>买入价</th>
                      <th>卖出价</th>
                      <th>价差</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="denom in selectedCurrency.denominations" :key="denom.id">
                      <td class="fw-bold">{{ formatDenominationValue(denom.denomination_value) }}</td>
                      <td>
                        <span class="badge" :class="denom.denomination_type === 'bill' ? 'bg-primary' : 'bg-success'">
                          {{ denom.denomination_type === 'bill' ? '纸币' : '硬币' }}
                        </span>
                      </td>
                      <td class="text-success">{{ denom.buy_rate?.toFixed(4) || '-' }}</td>
                      <td class="text-danger">{{ denom.sell_rate?.toFixed(4) || '-' }}</td>
                      <td :class="getSpreadClass(denom.buy_rate, denom.sell_rate)">
                        {{ getSpread(denom.buy_rate, denom.sell_rate) }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
            <button 
              type="button" 
              class="btn btn-primary"
              @click="publishSingle(selectedCurrency)"
              :disabled="loading"
            >
              <i class="fas fa-broadcast-tower me-1"></i>
              发布此币种
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DenominationPublishView',
  data() {
    return {
      loading: false,
      currenciesWithDenominations: [],
      selectedCurrencies: [],
      selectedCurrency: null,
      todayPublishCount: 0
    }
  },
  computed: {
    isAllSelected() {
      return this.currenciesWithDenominations.length > 0 && 
             this.selectedCurrencies.length === this.currenciesWithDenominations.length;
    },
    totalDenominations() {
      return this.currenciesWithDenominations.reduce((total, currency) => {
        return total + (currency.denominations?.length || 0);
      }, 0);
    }
  },
  mounted() {
    this.loadData();
  },
  methods: {
    async loadData() {
      this.loading = true;
      try {
        // 加载所有币种的面值汇率设置
        const response = await this.$api.get('/denominations-api/currencies-with-denominations');
        
        if (response.data.success) {
          this.currenciesWithDenominations = response.data.data;
          this.calculateRateRanges();
        } else {
          this.$toast.error('加载数据失败');
        }
        
        // 加载今日发布次数
        await this.loadTodayPublishCount();
        
      } catch (error) {
        console.error('加载数据失败:', error);
        this.$toast.error('加载数据失败');
      } finally {
        this.loading = false;
      }
    },
    
    async loadTodayPublishCount() {
      try {
        const response = await this.$api.get('/dashboard/denomination-publish-history', {
          params: {
            page: 1,
            per_page: 1
          }
        });
        
        if (response.data.success) {
          this.todayPublishCount = response.data.data.pagination.total;
        }
      } catch (error) {
        console.error('加载发布次数失败:', error);
      }
    },
    
    calculateRateRanges() {
      this.currenciesWithDenominations.forEach(currency => {
        if (currency.denominations && currency.denominations.length > 0) {
          const buyRates = currency.denominations
            .filter(d => d.buy_rate > 0)
            .map(d => d.buy_rate);
          const sellRates = currency.denominations
            .filter(d => d.sell_rate > 0)
            .map(d => d.sell_rate);
          
          currency.min_buy_rate = buyRates.length > 0 ? Math.min(...buyRates).toFixed(4) : '-';
          currency.max_buy_rate = buyRates.length > 0 ? Math.max(...buyRates).toFixed(4) : '-';
          currency.min_sell_rate = sellRates.length > 0 ? Math.min(...sellRates).toFixed(4) : '-';
          currency.max_sell_rate = sellRates.length > 0 ? Math.max(...sellRates).toFixed(4) : '-';
        }
      });
    },
    
    selectAll() {
      this.selectedCurrencies = this.currenciesWithDenominations.map(c => c.id);
    },
    
    selectNone() {
      this.selectedCurrencies = [];
    },
    
    toggleSelectAll() {
      if (this.isAllSelected) {
        this.selectNone();
      } else {
        this.selectAll();
      }
    },
    
    viewDetails(currency) {
      this.selectedCurrency = currency;
      // eslint-disable-next-line no-undef
      const modal = new bootstrap.Modal(document.getElementById('detailModal'));
      modal.show();
    },
    
    async publishSingle(currency) {
      if (!confirm(`确定要发布 ${currency.currency_code} 的面值汇率到机顶盒吗？`)) {
        return;
      }
      
      this.loading = true;
      try {
        // 准备面值汇率数据
        const denominationRates = currency.denominations
          .filter(denom => denom.buy_rate && denom.sell_rate && denom.buy_rate > 0 && denom.sell_rate > 0)
          .map(denom => ({
            denomination_id: denom.id,
            denomination_value: denom.denomination_value,
            denomination_type: denom.denomination_type,
            buy_rate: parseFloat(denom.buy_rate),
            sell_rate: parseFloat(denom.sell_rate)
          }));
        
        const response = await this.$api.post('/dashboard/publish-denomination-rates', {
          currency_id: currency.id,
          currency_code: currency.currency_code,
          denomination_rates: denominationRates
        });
        
        if (response.data.success) {
          this.$toast.success(`${currency.currency_code} 面值汇率发布成功`);
          await this.loadTodayPublishCount();
          await this.loadData(); // 重新加载币种列表以显示最新的发布状态
        } else {
          this.$toast.error(response.data.message || '发布失败');
        }
      } catch (error) {
        console.error('发布失败:', error);
        this.$toast.error('发布失败');
      } finally {
        this.loading = false;
      }
    },
    
    async publishAllSelected() {
      if (this.selectedCurrencies.length === 0) {
        this.$toast.warning('请先选择要发布的币种');
        return;
      }
      
      if (!confirm(`确定要发布选中的 ${this.selectedCurrencies.length} 个币种的面值汇率到机顶盒吗？`)) {
        return;
      }
      
      this.loading = true;
      let successCount = 0;
      let failCount = 0;
      
      try {
        for (const currencyId of this.selectedCurrencies) {
          const currency = this.currenciesWithDenominations.find(c => c.id === currencyId);
          if (currency) {
            try {
              await this.publishSingle(currency);
              successCount++;
            } catch (error) {
              failCount++;
              console.error(`发布 ${currency.currency_code} 失败:`, error);
            }
          }
        }
        
        if (successCount > 0) {
          this.$toast.success(`成功发布 ${successCount} 个币种`);
        }
        if (failCount > 0) {
          this.$toast.error(`${failCount} 个币种发布失败`);
        }

        await this.loadTodayPublishCount();
        await this.loadData(); // 重新加载币种列表以显示最新的发布状态
        
      } finally {
        this.loading = false;
      }
    },
    
    async publishAll() {
      this.selectAll();
      await this.publishAllSelected();
    },
    
    async publishAllMultiCurrency() {
      if (this.currenciesWithDenominations.length === 0) {
        this.$toast.warning('没有可发布的币种');
        return;
      }
      
      if (!confirm(`确定要发布所有 ${this.currenciesWithDenominations.length} 个币种的面值汇率到机顶盒吗？\n\n注意：这将覆盖今日已有的面值汇率发布。`)) {
        return;
      }
      
      this.loading = true;
      try {
        // 准备所有币种的面值汇率数据
        const currenciesData = [];
        
        for (const currency of this.currenciesWithDenominations) {
          const denominationRates = currency.denominations
            .filter(denom => denom.buy_rate && denom.sell_rate && denom.buy_rate > 0 && denom.sell_rate > 0)
            .map(denom => ({
              denomination_id: denom.id,
              denomination_value: denom.denomination_value,
              denomination_type: denom.denomination_type,
              buy_rate: parseFloat(denom.buy_rate),
              sell_rate: parseFloat(denom.sell_rate)
            }));
          
          if (denominationRates.length > 0) {
            currenciesData.push({
              currency_id: currency.id,
              denomination_rates: denominationRates
            });
          }
        }
        
        if (currenciesData.length === 0) {
          this.$toast.warning('没有有效的面值汇率数据');
          return;
        }
        
        const response = await this.$api.post('/dashboard/publish-multi-currency-denomination-rates', {
          currencies: currenciesData
        });
        
        if (response.data.success) {
          this.$toast.success(`成功发布 ${currenciesData.length} 个币种的面值汇率`);
          await this.loadTodayPublishCount();
        } else {
          this.$toast.error(response.data.message || '发布失败');
        }
      } catch (error) {
        console.error('发布多币种面值汇率失败:', error);
        this.$toast.error('发布失败');
      } finally {
        this.loading = false;
      }
    },
    
    async previewPublish() {
      if (this.currenciesWithDenominations.length === 0) {
        this.$toast.warning('没有可预览的币种');
        return;
      }
      
      // 准备预览数据
      const previewData = [];
      
      for (const currency of this.currenciesWithDenominations) {
        const denominationRates = currency.denominations
          .filter(denom => denom.buy_rate && denom.sell_rate && denom.buy_rate > 0 && denom.sell_rate > 0)
          .map(denom => ({
            denomination_id: denom.id,
            denomination_value: denom.denomination_value,
            denomination_type: denom.denomination_type,
            buy_rate: parseFloat(denom.buy_rate),
            sell_rate: parseFloat(denom.sell_rate)
          }));
        
        if (denominationRates.length > 0) {
          previewData.push({
            currency_code: currency.currency_code,
            currency_name: currency.currency_name,
            denomination_count: denominationRates.length,
            denominations: denominationRates
          });
        }
      }
      
      if (previewData.length === 0) {
        this.$toast.warning('没有有效的面值汇率数据');
        return;
      }
      
      // 显示预览信息
      let previewText = `预览发布效果：\n\n`;
      previewText += `共 ${previewData.length} 个币种，总面值数量：${previewData.reduce((sum, c) => sum + c.denomination_count, 0)} 个\n\n`;
      
      previewData.forEach(currency => {
        previewText += `• ${currency.currency_code} (${currency.currency_name}): ${currency.denomination_count} 个面值\n`;
      });
      
      previewText += `\n确认发布后将覆盖今日已有的面值汇率发布。`;
      
      if (confirm(previewText)) {
        await this.publishAllMultiCurrency();
      }
    },
    
    goToPreview() {
      this.$router.push('/system/denomination-preview');
    },
    
    async refreshData() {
      await this.loadData();
    },
    
    getCurrencyFlag(currency) {
      if (currency.custom_flag_filename) {
        return `/flags/${currency.custom_flag_filename}`;
      } else if (currency.flag_code) {
        return `/flags/${currency.flag_code.toLowerCase()}.svg`;
      } else {
        return '/flags/unknown.svg';
      }
    },
    
    handleFlagError(event) {
      event.target.src = '/images/chart-placeholder.svg';
    },
    
    formatDenominationValue(value) {
      if (value >= 1) {
        return value.toFixed(0);
      } else {
        return value.toFixed(2);
      }
    },
    
    formatDateTime(dateString) {
      if (!dateString) return '-';
      const date = new Date(dateString);
      return date.toLocaleString('zh-CN');
    },
    
    getSpread(buyRate, sellRate) {
      if (!buyRate || !sellRate) return '-';
      const spread = sellRate - buyRate;
      return spread > 0 ? `+${spread.toFixed(4)}` : spread.toFixed(4);
    },
    
    getSpreadClass(buyRate, sellRate) {
      if (!buyRate || !sellRate) return '';
      const spread = sellRate - buyRate;
      if (spread > 0) return 'text-success';
      if (spread < 0) return 'text-danger';
      return 'text-muted';
    }
  }
}
</script>

<style scoped>
.currency-flag {
  width: 32px;
  height: 24px;
  object-fit: cover;
  border-radius: 4px;
  border: 1px solid #dee2e6;
}

.denomination-list {
  max-width: 200px;
}

.rate-range {
  font-size: 0.9rem;
}

.rate-range > div {
  margin-bottom: 2px;
}

.table th {
  background-color: #f8f9fa;
  font-weight: 600;
}

.badge {
  font-size: 0.75em;
}

.card {
  box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
}

.btn-group .btn {
  margin-right: 0.25rem;
}

.btn-group .btn:last-child {
  margin-right: 0;
}
</style>
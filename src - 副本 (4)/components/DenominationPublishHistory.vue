<template>
  <div class="modal fade" id="publishHistoryModal" tabindex="-1" aria-labelledby="publishHistoryModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-xl">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="publishHistoryModalLabel">
            <i class="fas fa-history me-2"></i>
            面值汇率发布历史
          </h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <!-- 筛选条件 -->
          <div class="row mb-3">
            <div class="col-md-3">
              <label class="form-label">币种</label>
              <select v-model="filters.currency_id" class="form-select" @change="loadHistory">
                <option value="">全部币种</option>
                <option v-for="currency in currencies" :key="currency.id" :value="currency.id">
                  {{ currency.currency_name }} ({{ currency.currency_code }})
                </option>
              </select>
            </div>
            <div class="col-md-3">
              <label class="form-label">开始日期</label>
              <input v-model="filters.start_date" type="date" class="form-control" @change="loadHistory">
            </div>
            <div class="col-md-3">
              <label class="form-label">结束日期</label>
              <input v-model="filters.end_date" type="date" class="form-control" @change="loadHistory">
            </div>
            <div class="col-md-3">
              <label class="form-label">每页条数</label>
              <select v-model="filters.per_page" class="form-select" @change="loadHistory">
                <option value="10">10条</option>
                <option value="20">20条</option>
                <option value="50">50条</option>
              </select>
            </div>
          </div>
          
          <!-- 发布历史表格 -->
          <div class="table-responsive">
            <table class="table table-bordered table-hover">
              <thead class="table-light">
                <tr>
                  <th>发布时间</th>
                  <th>发布人</th>
                  <th>面值数量</th>
                  <th>访问令牌</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="loading">
                  <td colspan="5" class="text-center">
                    <div class="spinner-border spinner-border-sm" role="status">
                      <span class="visually-hidden">加载中...</span>
                    </div>
                    加载中...
                  </td>
                </tr>
                <tr v-else-if="historyRecords.length === 0">
                  <td colspan="5" class="text-center text-muted">暂无发布记录</td>
                </tr>
                <tr v-else v-for="record in historyRecords" :key="record.id">
                  <td>
                    <div>{{ record.publish_date }}</div>
                    <small class="text-muted">{{ record.publish_time }}</small>
                  </td>
                  <td>{{ record.publisher_name }}</td>
                  <td>
                    <span class="badge bg-primary">{{ record.total_denominations }} 个面值</span>
                  </td>
                  <td>
                    <code class="small">{{ record.access_token.substring(0, 8) }}...</code>
                  </td>
                  <td>
                    <button 
                      class="btn btn-sm btn-outline-primary me-1"
                      @click="viewDetail(record.id)"
                      title="查看详情"
                    >
                      <i class="fas fa-eye"></i>
                    </button>
                    <button 
                      class="btn btn-sm btn-outline-info"
                      @click="copyToken(record.access_token)"
                      title="复制令牌"
                    >
                      <i class="fas fa-copy"></i>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <!-- 分页 -->
          <nav v-if="pagination.pages > 1">
            <ul class="pagination justify-content-center">
              <li class="page-item" :class="{ disabled: pagination.page === 1 }">
                <button class="page-link" @click="changePage(pagination.page - 1)" :disabled="pagination.page === 1">
                  上一页
                </button>
              </li>
              <li 
                v-for="page in visiblePages" 
                :key="page" 
                class="page-item" 
                :class="{ active: page === pagination.page }"
              >
                <button class="page-link" @click="changePage(page)">{{ page }}</button>
              </li>
              <li class="page-item" :class="{ disabled: pagination.page === pagination.pages }">
                <button class="page-link" @click="changePage(pagination.page + 1)" :disabled="pagination.page === pagination.pages">
                  下一页
                </button>
              </li>
            </ul>
          </nav>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
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
            发布详情
          </h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <div v-if="selectedRecord">
            <div class="row mb-3">
              <div class="col-md-6">
                <strong>发布时间：</strong>{{ selectedRecord.publish_date }} {{ selectedRecord.publish_time }}
              </div>
              <div class="col-md-6">
                <strong>发布人：</strong>{{ selectedRecord.publisher_name }}
              </div>
            </div>
            
            <!-- 面值汇率详情 -->
            <div v-if="selectedRecord.type === 'denomination'">
              <h6>面值汇率详情</h6>
              <div class="table-responsive">
                <table class="table table-sm table-bordered">
                  <thead class="table-light">
                    <tr>
                      <th>币种</th>
                      <th>面值</th>
                      <th>类型</th>
                      <th>买入价</th>
                      <th>卖出价</th>
                      <th>价差</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="rate in selectedRecord.denomination_rates" :key="rate.denomination_id">
                      <td>
                        <span class="badge bg-info">{{ rate.currency_code }}</span>
                        <br><small class="text-muted">{{ rate.currency_name }}</small>
                      </td>
                      <td>{{ formatDenominationValue(rate.denomination_value) }}</td>
                      <td>
                        <span class="badge" :class="rate.denomination_type === 'bill' ? 'bg-primary' : 'bg-success'">
                          {{ rate.denomination_type === 'bill' ? '纸币' : '硬币' }}
                        </span>
                      </td>
                      <td>{{ rate.buy_rate.toFixed(4) }}</td>
                      <td>{{ rate.sell_rate.toFixed(4) }}</td>
                      <td :class="rate.spread > 0 ? 'text-success' : 'text-danger'">
                        {{ rate.spread > 0 ? '+' : '' }}{{ rate.spread.toFixed(4) }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            
            <!-- 标准汇率详情 -->
            <div v-else-if="selectedRecord.type === 'standard'">
              <h6>标准汇率详情</h6>
              <div class="table-responsive">
                <table class="table table-sm table-bordered">
                  <thead class="table-light">
                    <tr>
                      <th>币种</th>
                      <th>买入价</th>
                      <th>卖出价</th>
                      <th>价差</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="rate in selectedRecord.rates" :key="rate.currency_id">
                      <td>
                        <span class="badge bg-info">{{ rate.currency_code }}</span>
                        <br><small class="text-muted">{{ rate.currency_name }}</small>
                      </td>
                      <td>{{ rate.buy_rate.toFixed(4) }}</td>
                      <td>{{ rate.sell_rate.toFixed(4) }}</td>
                      <td :class="rate.spread > 0 ? 'text-success' : 'text-danger'">
                        {{ rate.spread > 0 ? '+' : '' }}{{ rate.spread.toFixed(4) }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DenominationPublishHistory',
  data() {
    return {
      loading: false,
      historyRecords: [],
      currencies: [],
      selectedRecord: null,
      filters: {
        currency_id: '',
        start_date: '',
        end_date: '',
        per_page: 20
      },
      pagination: {
        page: 1,
        per_page: 20,
        total: 0,
        pages: 0
      }
    }
  },
  computed: {
    visiblePages() {
      const pages = [];
      const current = this.pagination.page;
      const total = this.pagination.pages;
      
      let start = Math.max(1, current - 2);
      let end = Math.min(total, current + 2);
      
      for (let i = start; i <= end; i++) {
        pages.push(i);
      }
      
      return pages;
    }
  },
  mounted() {
    this.loadCurrencies();
    this.loadHistory();
  },
  methods: {
    async loadCurrencies() {
      try {
        const response = await this.$api.get('/currencies');
        if (response.data.success) {
          this.currencies = response.data.data;
        }
      } catch (error) {
        console.error('加载币种列表失败:', error);
      }
    },
    
    async loadHistory() {
      this.loading = true;
      try {
        const params = {
          page: this.pagination.page,
          per_page: this.filters.per_page,
          ...this.filters
        };
        
        const response = await this.$api.get('/dashboard/denomination-publish-history', { params });
        
        if (response.data.success) {
          this.historyRecords = response.data.data.records;
          this.pagination = response.data.data.pagination;
        } else {
          this.$toast.error('加载发布历史失败');
        }
      } catch (error) {
        console.error('加载发布历史失败:', error);
        this.$toast.error('加载发布历史失败');
      } finally {
        this.loading = false;
      }
    },
    
    changePage(page) {
      if (page >= 1 && page <= this.pagination.pages) {
        this.pagination.page = page;
        this.loadHistory();
      }
    },
    
    async viewDetail(recordId) {
      try {
        const response = await this.$api.get(`/dashboard/publish-detail/${recordId}`);
        
        if (response.data.success) {
          this.selectedRecord = response.data.data.record;
          this.selectedRecord.type = response.data.data.type;
          
          if (response.data.data.type === 'denomination') {
            // 面值汇率
            this.selectedRecord.denomination_rates = response.data.data.denomination_rates;
          } else {
            // 标准汇率
            this.selectedRecord.rates = response.data.data.rates;
          }
          
          // 显示详情模态框
          const modal = new bootstrap.Modal(document.getElementById('detailModal'));
          modal.show();
        } else {
          this.$toast.error('获取详情失败');
        }
      } catch (error) {
        console.error('获取详情失败:', error);
        this.$toast.error('获取详情失败');
      }
    },
    
    copyToken(token) {
      navigator.clipboard.writeText(token).then(() => {
        this.$toast.success('令牌已复制到剪贴板');
      }).catch(() => {
        this.$toast.error('复制失败');
      });
    },
    
    formatDenominationValue(value) {
      return new Intl.NumberFormat('zh-CN', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
      }).format(value);
    }
  }
}
</script>

<style scoped>
.modal-xl {
  max-width: 90%;
}

.table th {
  background-color: #f8f9fa;
  font-weight: 600;
}

.badge {
  font-size: 0.75em;
}

code {
  font-size: 0.8em;
  background-color: #f8f9fa;
  padding: 0.2rem 0.4rem;
  border-radius: 0.25rem;
}

.pagination {
  margin-top: 1rem;
}
</style>
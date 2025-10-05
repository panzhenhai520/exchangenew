<template>
  <div class="container-fluid py-4">
    <div class="row">
      <div class="col-12">
        <div class="d-flex justify-content-between align-items-center mb-4">
          <h2 class="page-title-bold">
            <font-awesome-icon :icon="['fas', 'search']" class="me-2" />
            {{ $t('transactions.title') }}
          </h2>
        </div>
        
        <div class="card mb-4">
          <div class="card-header">
            <h5 class="mb-0">{{ $t('transactions.search_conditions') }}</h5>
          </div>
          <div class="card-body">
            <form @submit.prevent="handleSearch">
              <div class="row g-2">
                <!-- 第一行 -->
                <div class="col-md-4">
                  <div class="d-flex align-items-center gap-2">
                    <label class="form-label mb-0 text-nowrap" style="min-width: 80px;">{{ $t('transactions.transaction_time_range') }}</label>
                    <div class="d-flex gap-1 flex-grow-1">
                      <input 
                        type="date" 
                        class="form-control form-control-sm" 
                        v-model="searchForm.startDate"
                      >
                      <span class="align-self-center small">{{ $t('transactions.to') }}</span>
                      <input 
                        type="date" 
                        class="form-control form-control-sm" 
                        v-model="searchForm.endDate"
                      >
                    </div>
                  </div>
                </div>
                
                <div class="col-md-3">
                  <div class="d-flex align-items-center gap-2">
                    <label class="form-label mb-0 text-nowrap" style="min-width: 60px;">{{ $t('transactions.transaction_no') }}</label>
                    <input
                      type="text"
                      class="form-control form-control-sm flex-grow-1" 
                      v-model="searchForm.transactionNo" 
                      :placeholder="$t('transactions.transaction_no_placeholder')"
                    >
                  </div>
                </div>
                
                <div class="col-md-5">
                  <div class="d-flex align-items-center gap-2">
                    <label class="form-label mb-0 text-nowrap" style="min-width: 60px;">{{ $t('transactions.amount_range') }}</label>
                    <div class="d-flex gap-1 flex-grow-1">
                      <input 
                        type="number" 
                        class="form-control form-control-sm" 
                        v-model="searchForm.minAmount" 
                        :placeholder="$t('transactions.min_amount')"
                      >
                      <span class="align-self-center small">-</span>
                      <input 
                        type="number" 
                        class="form-control form-control-sm"
                        v-model="searchForm.maxAmount" 
                        :placeholder="$t('transactions.max_amount')"
                      >
                    </div>
                  </div>
                </div>
                
                <!-- 第二行 -->
                <div class="col-md-3">
                  <div class="d-flex align-items-center gap-2">
                    <label class="form-label mb-0 text-nowrap" style="min-width: 60px;">{{ $t('transactions.customer_name') }}</label>
                    <input 
                      type="text" 
                      class="form-control form-control-sm flex-grow-1" 
                      v-model="searchForm.customerName" 
                      :placeholder="$t('transactions.customer_name_placeholder')"
                    >
                  </div>
                </div>
                
                <div class="col-md-3">
                  <div class="d-flex align-items-center gap-2">
                    <label class="form-label mb-0 text-nowrap" style="min-width: 50px;">{{ $t('transactions.operator') }}</label>
                    <input 
                      type="text" 
                      class="form-control form-control-sm flex-grow-1" 
                      v-model="searchForm.operatorName" 
                      :placeholder="$t('transactions.operator_placeholder')"
                    >
                  </div>
                </div>

                <div class="col-md-3">
                  <div class="d-flex align-items-center gap-2">
                    <label class="form-label mb-0 text-nowrap" style="min-width: 40px;">{{ $t('transactions.currency') }}</label>
                    <select 
                      class="form-select form-select-sm flex-grow-1" 
                      v-model="searchForm.currencyCode"
                    >
                      <option value="">{{ $t('transactions.all_currencies') }}</option>
                      <option v-for="currency in currencies" 
                              :key="currency.currency_id" 
                              :value="currency.currency_code">
                        {{ currency.currency_code }} ({{ currency.currency_name }})
                      </option>
                    </select>
                  </div>
                </div>
                
                <!-- 查询按钮组 -->
                <div class="col-md-3">
                  <div class="d-flex gap-1">
                    <button type="submit" class="btn btn-primary btn-sm">
                      <font-awesome-icon :icon="['fas', 'search']" class="me-1" />
                      {{ $t('transactions.search') }}
                    </button>
                    <button type="button" class="btn btn-secondary btn-sm" @click="resetSearch">
                      <font-awesome-icon :icon="['fas', 'undo']" class="me-1" />
                      {{ $t('transactions.reset') }}
                    </button>
                    <button type="button" class="btn btn-outline-primary btn-sm" @click="refreshTransactions">
                      <font-awesome-icon :icon="['fas', 'sync']" class="me-1" :spin="loading" />
                      {{ $t('transactions.refresh') }}
                    </button>
                    <button type="button" class="btn btn-success btn-sm" @click="exportToCSV">
                      <font-awesome-icon :icon="['fas', 'download']" class="me-1" />
                      {{ $t('transactions.export_csv') }}
                    </button>
                  </div>
                </div>
              </div>
            </form>
          </div>
        </div>

        <div class="card mb-4">
          <div class="card-header d-flex justify-content-between align-items-center">
            <h5 class="mb-0">{{ $t('transactions.transaction_list') }}</h5>
            <div class="d-flex align-items-center gap-3">
              <!-- 本币累加显示 -->
              <div v-if="selectedTransactions.length > 0" class="badge bg-success fs-6">
                {{ $t('transactions.selected_count', { count: selectedTransactions.length }) }}，{{ $t('transactions.local_currency_total', { amount: formatAmount(totalLocalAmount) }) }}
              </div>
              <div class="text-muted">
                {{ $t('transactions.total_records', { count: totalRecords }) }}
              </div>
            </div>
          </div>
          <div class="card-body">
            <div v-if="loading" class="text-center py-4">
              <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">{{ $t('transactions.loading') }}</span>
              </div>
              <p class="mt-2">{{ $t('transactions.loading_transactions') }}</p>
            </div>
            
            <div v-else-if="error" class="alert alert-danger">
              {{ error }}
            </div>
            
            <div v-else>
              <div class="table-responsive">
                <table class="table table-hover">
                  <thead>
                    <tr>
                      <th style="width: 50px;">
                        <input 
                          type="checkbox" 
                          class="form-check-input" 
                          :checked="isAllSelected"
                          @change="toggleAllSelection"
                          :title="$t('transactions.select_all')"
                        >
                      </th>
                      <th>{{ $t('transactions.headers.transaction_time') }}</th>
                      <th>{{ $t('transactions.headers.transaction_no') }}</th>
                      <th>{{ $t('transactions.headers.type') }}</th>
                      <th>{{ $t('transactions.headers.currency') }}</th>
                      <th>{{ $t('transactions.headers.amount') }}</th>
                      <th>{{ $t('transactions.headers.rate') }}</th>
                      <th>{{ $t('transactions.headers.local_currency') }}</th>
                      <th>{{ $t('transactions.headers.customer_name') }}</th>
                      <th>{{ $t('transactions.headers.operator') }}</th>
                      <th>{{ $t('transactions.headers.actions') }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="tx in transactions" :key="tx.id" :class="{'table-danger': tx.type === 'reversal', 'table-info': selectedTransactions.includes(tx.id)}">
                      <td>
                        <input 
                          type="checkbox" 
                          class="form-check-input" 
                          :value="tx.id"
                          v-model="selectedTransactions"
                          @change="updateTotalAmount"
                          :title="$t('transactions.select_transaction')"
                        >
                      </td>
                      <td>{{ formatTransactionTime(tx.transaction_time) }}</td>
                      <td>{{ tx.transaction_no }}</td>
                      <td>
                        <span :class="getTypeClass(tx.type)">
                          {{ getTypeText(tx.type) }}
                        </span>
                      </td>
                      <td>
                        <div class="d-flex align-items-center">
                          <CurrencyFlag 
                            :code="tx.currency_code" 
                            :custom-filename="tx.custom_flag_filename"
                            class="me-1" 
                          />
                          {{ getCurrencyDisplayName(tx) }}
                        </div>
                      </td>
                      <td>{{ formatAmount(tx.amount) }}</td>
                      <td>{{ tx.rate }}</td>
                      <td>{{ formatAmount(tx.local_amount) }}</td>
                      <td>{{ getCustomerNameText(tx.customer_name) }}</td>
                      <td>{{ tx.operator_name }}</td>
                      <td>
                        <button 
                          type="button" 
                          class="btn btn-outline-primary btn-sm"
                          @click="reprintReceipt(tx)"
                          :disabled="loading"
                        >
                          <font-awesome-icon :icon="['fas', 'print']" class="me-1" />
                          {{ $t('transactions.pagination.reprint') }}
                        </button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <!-- 分页器 -->
              <div v-if="totalRecords > 0" class="d-flex justify-content-between align-items-center mt-4">
                <div class="text-muted">
                  {{ $t('transactions.pagination.items_per_page', { size: pageSize }) }}，{{ $t('transactions.pagination.total_pages', { pages: totalPages }) }}
                </div>
                <nav aria-label="Page navigation">
                  <ul class="pagination mb-0">
                    <li class="page-item" :class="{ disabled: currentPage === 1 }">
                      <a class="page-link" href="#" @click.prevent="handlePageChange(currentPage - 1)">
                        {{ $t('transactions.pagination.previous_page') }}
                      </a>
                    </li>
                    <li v-for="page in displayedPages" :key="page" class="page-item" :class="{ active: currentPage === page }">
                      <a class="page-link" href="#" @click.prevent="handlePageChange(page)">
                        {{ page }}
                      </a>
                    </li>
                    <li class="page-item" :class="{ disabled: currentPage === totalPages }">
                      <a class="page-link" href="#" @click.prevent="handlePageChange(currentPage + 1)">
                        {{ $t('transactions.pagination.next_page') }}
                      </a>
                    </li>
                  </ul>
                </nav>
              </div>
              
              <div v-if="transactions.length === 0" class="text-center py-4">
                <p class="text-muted mb-0">{{ $t('transactions.messages.no_transactions') }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 重新打印模态框 -->
    <div class="modal fade" id="reprintModal" tabindex="-1" aria-labelledby="reprintModalLabel" aria-hidden="true">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header bg-success text-white">
            <h5 class="modal-title" id="reprintModalLabel">
              <font-awesome-icon :icon="['fas', 'print']" class="me-2" />
              重新打印收据
            </h5>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body" v-if="selectedTransaction">
            <div class="alert alert-info">
              <font-awesome-icon :icon="['fas', 'info-circle']" class="me-2" />
              您正在重新打印以下交易的收据：
            </div>
            
            <div class="row mb-3">
              <div class="col-md-6">
                <strong>交易号：</strong>{{ selectedTransaction.transaction_no }}
              </div>
              <div class="col-md-6">
                <strong>交易时间：</strong>{{ formatTransactionTime(selectedTransaction.transaction_time) }}
              </div>
            </div>
            
            <div class="row mb-3">
              <div class="col-md-6">
                <strong>交易类型：</strong>{{ getTypeText(selectedTransaction.type) }}
              </div>
              <div class="col-md-6">
                <strong>币种：</strong>{{ selectedTransaction.currency_code }}
              </div>
            </div>
            
            <div class="row mb-3">
              <div class="col-md-6">
                <strong>金额：</strong>{{ formatAmount(selectedTransaction.amount) }}
              </div>
              <div class="col-md-6">
                <strong>客户姓名：</strong>{{ getCustomerNameText(selectedTransaction.customer_name) }}
              </div>
            </div>
            
            <div class="alert alert-warning">
              <font-awesome-icon :icon="['fas', 'exclamation-triangle']" class="me-2" />
              重新打印的收据将标注重新打印时间：{{ new Date().toLocaleString() }}
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeReprintModal">取消</button>
            <button type="button" class="btn btn-success" @click="confirmReprint" :disabled="reprinting">
              <font-awesome-icon :icon="['fas', 'print']" class="me-1" :spin="reprinting" />
              {{ reprinting ? '打印中...' : '确认打印' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import CurrencyFlag from '@/components/CurrencyFlag.vue'
import { formatAmount } from '@/utils/format'
import { formatTransactionTime } from '@/utils/formatters'
import { useEnhancedApi } from '@/services/api/enhancedApiService'
import { usePerformance } from '@/utils/performance'
import api from '@/services/api'
import { formatDate } from '@/utils/dateUtils'
import { getCurrencyDisplayName } from '@/utils/currencyTranslator'

export default {
  name: 'TransactionsView',
  components: {
    CurrencyFlag
  },
  data() {
    return {
      // 搜索条件
      searchForm: {
        startDate: formatDate(new Date()),
        endDate: formatDate(new Date()),
        transactionNo: '',
        minAmount: '',
        maxAmount: '',
        customerName: '',
        operatorName: '',
        currencyCode: ''
      },
      
      // 数据状态
      transactions: [],
      loading: false,
      error: null,
      hasMore: true,
      currentPage: 1,
      pageSize: 20,
      totalRecords: 0,
      
      // 虚拟滚动配置
      virtualScrollConfig: {
        itemHeight: 60,
        containerHeight: 500,
        buffer: 10
      },
      
      // 性能优化
      searchDebounceDelay: 500,
      lastSearchTime: 0,
      
      // 选项数据
      currencies: [],
      operators: [],
      transactionTypes: [
        { value: '', label: '全部类型' },
                              { value: 'buy', label: 'buy' },
                      { value: 'sell', label: 'sell' }
      ],
      
      // 重新打印相关
      selectedTransaction: null,
      reprinting: false,
      
      // 本币累加相关
      selectedTransactions: [],
      totalLocalAmount: 0
    };
  },
  computed: {
    totalPages() {
      return Math.ceil(this.totalRecords / this.pageSize)
    },
    displayedPages() {
      const pages = []
      const maxDisplayed = 5
      let start = Math.max(1, this.currentPage - Math.floor(maxDisplayed / 2))
      let end = Math.min(this.totalPages, start + maxDisplayed - 1)
      
      if (end - start + 1 < maxDisplayed) {
        start = Math.max(1, end - maxDisplayed + 1)
      }
      
      for (let i = start; i <= end; i++) {
        pages.push(i)
      }
      
      return pages
    },
    
    // 是否全选
    isAllSelected() {
      return this.transactions.length > 0 && this.selectedTransactions.length === this.transactions.length
    }
  },
  async created() {
    // 初始化性能优化工具
    this.initPerformanceTools();
    
    // 并行加载初始数据
    await Promise.all([
      this.loadAvailableCurrencies(),
      this.loadOperators()
    ]);
    
    // 加载交易数据
    await this.fetchTransactions(true);
  },
  methods: {
    formatAmount,
    formatTransactionTime,
    
    getCurrencyDisplayName(tx) {
      if (!tx) return ''
      
      // 使用新的币种显示函数
      return getCurrencyDisplayName(tx.currency_code, tx)
    },
    
    // 初始化性能优化工具
    initPerformanceTools() {
      const { debounce, performanceMonitor } = usePerformance();
      const transactionApi = useEnhancedApi('transaction');
      
      this.performanceMonitor = performanceMonitor;
      this.transactionApi = transactionApi;
      
      // 创建防抖搜索函数
      this.debouncedSearch = debounce(this.performSearch, this.searchDebounceDelay);
    },
    
    async fetchTransactions(reset = false) {
      if (this.loading) return;
      
      this.performanceMonitor?.mark('transactions_fetch_start');
      this.loading = true;
      this.error = null;
      
      try {
        if (reset) {
          this.currentPage = 1;
          this.transactions = [];
          this.hasMore = true;
        }
        
        const params = {
          page: this.currentPage,
          per_page: this.pageSize,
          start_date: this.searchForm.startDate,
          end_date: this.searchForm.endDate
        };
        
        // 添加可选搜索条件
        if (this.searchForm.transactionNo) {
          params.transaction_no = this.searchForm.transactionNo;
        }
        if (this.searchForm.customerName) {
          params.customer_name = this.searchForm.customerName;
        }
        if (this.searchForm.operatorName) {
          params.operator_name = this.searchForm.operatorName;
        }
        if (this.searchForm.minAmount) {
          params.min_amount = parseFloat(this.searchForm.minAmount);
        }
        if (this.searchForm.maxAmount) {
          params.max_amount = parseFloat(this.searchForm.maxAmount);
        }
        if (this.searchForm.currencyCode) {
          params.currency_code = this.searchForm.currencyCode;
        }
        
        // 使用增强API服务
        const response = await (this.transactionApi || api).get('transactions/query', {
          params,
          cache: false // 交易数据不缓存
        });
        
        if (response.data.success) {
          const newTransactions = response.data.transactions || [];
          
          if (reset) {
            this.transactions = newTransactions;
          } else {
            this.transactions.push(...newTransactions);
          }
          
          this.totalRecords = response.data.pagination?.total_count || response.data.total || 0;
          this.hasMore = newTransactions.length === this.pageSize;
          
          if (!reset) {
            this.currentPage++;
          }
          
          this.performanceMonitor?.mark('transactions_fetch_success');
        } else {
          throw new Error(response.data.message || '查询失败');
        }
      } catch (error) {
        console.error('获取交易记录失败:', error);
        this.error = error.message || '获取交易记录失败';
        this.performanceMonitor?.mark('transactions_fetch_error');
      } finally {
        this.loading = false;
        this.performanceMonitor?.measure('transactions_fetch_duration', 'transactions_fetch_start');
      }
    },
    
    // 执行搜索
    async performSearch() {
      this.lastSearchTime = Date.now();
      this.resetSelection(); // 搜索时重置选择
      await this.fetchTransactions(true);
    },
    
    // 防抖搜索
    handleSearch() {
      if (this.debouncedSearch) {
        this.debouncedSearch();
      } else {
        this.performSearch();
      }
    },
    
    // 重置搜索
    resetSearch() {
      this.searchForm = {
        startDate: formatDate(new Date()),
        endDate: formatDate(new Date()),
        transactionNo: '',
        minAmount: '',
        maxAmount: '',
        customerName: '',
        operatorName: '',
        currencyCode: ''
      };
      this.resetSelection(); // 重置搜索时重置选择
      this.performSearch();
    },
    
    // 加载更多数据（虚拟滚动触发）
    async loadMore() {
      if (!this.hasMore || this.loading) return;
      await this.fetchTransactions(false);
    },
    
    // 虚拟滚动事件处理
    onVirtualScroll(scrollInfo) {
      // 可以在这里添加滚动相关的逻辑
      console.log('Virtual scroll:', scrollInfo);
    },
    
    onVisibleRangeChange(range) {
      // 可见范围变化时的处理
      console.log('Visible range changed:', range);
    },
    
    // 刷新交易数据
    refreshTransactions() {
      this.resetSelection(); // 刷新时重置选择
      this.performSearch();
    },
    
    // 页面变化处理（兼容原有分页）
    handlePageChange(page) {
      this.currentPage = page;
      this.resetSelection(); // 换页时重置选择
      this.fetchTransactions(true);
    },
    
    async loadAvailableCurrencies() {
      try {
        console.log('开始加载币种数据...');
        // 【修复】正确的API路径：balance-management/available-currencies
        const response = await api.get('balance-management/available-currencies', {
          params: {
            branch_id: this.getCurrentBranchId(),
            include_base: true,
            require_rate: false
          }
        });
        
        console.log('币种API响应:', response.data);
        
        if (response.data.success) {
          this.currencies = response.data.data.sort((a, b) => 
            a.currency_code.localeCompare(b.currency_code)
          );
          console.log('币种数据加载成功，数量:', this.currencies.length);
          console.log('币种列表:', this.currencies);
        } else {
          console.error('币种API返回失败:', response.data.message);
        }
      } catch (error) {
        console.error('加载可用币种失败:', error);
        console.error('错误详情:', error.response?.data || error.message);
      }
    },
    
    async loadOperators() {
      try {
          const response = await api.get('users');
        if (response.data.success) {
            this.operators = response.data.users || [];
        }
      } catch (error) {
        console.error('获取操作员列表失败:', error);
      }
    },
    
    // 获取当前分支ID
    getCurrentBranchId() {
      try {
        const user = JSON.parse(localStorage.getItem('user') || '{}')
        return user.branch_id
      } catch {
        return null
      }
    },
    
    // 本币累加相关方法
    toggleAllSelection() {
      if (this.isAllSelected) {
        this.selectedTransactions = []
      } else {
        this.selectedTransactions = this.transactions.map(tx => tx.id)
      }
      this.updateTotalAmount()
    },
    
    updateTotalAmount() {
      this.totalLocalAmount = this.transactions
        .filter(tx => this.selectedTransactions.includes(tx.id))
        .reduce((sum, tx) => sum + (parseFloat(tx.local_amount) || 0), 0)
    },
    
    // 重置选择
    resetSelection() {
      this.selectedTransactions = []
      this.totalLocalAmount = 0
    },
    
    // 导出交易记录
    async exportTransactions() {
      this.performanceMonitor?.mark('transactions_export_start');
      
      try {
        const params = {
          start_date: this.searchForm.startDate,
          end_date: this.searchForm.endDate,
          format: 'excel'
        };
        
        // 添加搜索条件
        Object.keys(this.searchForm).forEach(key => {
          if (this.searchForm[key] && key !== 'startDate' && key !== 'endDate') {
            params[key] = this.searchForm[key];
          }
        });
        
        const response = await api.get('transactions/export', {
          params,
          responseType: 'blob'
        });
        
        // 创建下载链接
        const blob = new Blob([response.data], {
          type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        });
        
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `transaction_records_${this.searchForm.startDate}_${this.searchForm.endDate}.xlsx`;
        link.click();
        
        window.URL.revokeObjectURL(url);
        
        this.$toast?.success('导出成功');
        this.performanceMonitor?.mark('transactions_export_success');
      } catch (error) {
        console.error('导出失败:', error);
        this.$toast?.error('导出失败');
        this.performanceMonitor?.mark('transactions_export_error');
      } finally {
        this.performanceMonitor?.measure('transactions_export_duration', 'transactions_export_start');
      }
    },
    
    // 获取交易类型样式
    getTypeClass(type) {
      const classes = {
        buy: 'text-success',
        sell: 'text-danger',
        reversal: 'text-warning',
        cash_out: 'text-info'
      };
      return classes[type] || '';
    },
    
    // 获取交易类型文本
    getTypeText(type) {
      // 使用翻译显示交易类型
      return this.$t(`transactions.types.${type}`) || type;
    },
    
    // 获取客户姓名文本
    getCustomerNameText(customerName) {
      // 处理特殊的翻译key
      if (customerName === 'balance.system_initial_balance_setup') {
        return this.$t('balance.system_initial_balance_setup')
      }
      return customerName
    },
    
    // 获取交易状态样式
    getTransactionStatusClass(status) {
      const statusMap = {
        'completed': 'badge bg-success',
        'pending': 'badge bg-warning',
        'cancelled': 'badge bg-danger',
        'failed': 'badge bg-secondary'
      };
      return statusMap[status] || 'badge bg-secondary';
    },
    
    // 获取交易状态文本
    getTransactionStatusText(status) {
      const statusMap = {
        'completed': '已完成',
        'pending': '处理中',
        'cancelled': '已取消',
        'failed': '失败'
      };
      return statusMap[status] || status;
    },
    
    // 重新打印收据
    reprintReceipt(transaction) {
      this.selectedTransaction = transaction;
      // 使用Bootstrap Modal API
      const modalElement = document.getElementById('reprintModal');
      if (modalElement) {
        // 检查Bootstrap是否可用
        if (typeof window.bootstrap !== 'undefined') {
          const modal = new window.bootstrap.Modal(modalElement);
          modal.show();
        } else {
          // 降级处理：直接显示模态框
          modalElement.style.display = 'block';
          modalElement.classList.add('show');
          document.body.classList.add('modal-open');
        }
      }
    },
    
    async confirmReprint() {
      if (!this.selectedTransaction) return;
      
      try {
        this.reprinting = true;
        
        // 调用重新打印API
        const response = await api.post(`transactions/${this.selectedTransaction.id}/reprint-receipt`);
        
        if (response.data.success) {
          // 获取PDF内容并创建blob
          const pdfContent = response.data.pdf_content;
          const binaryString = atob(pdfContent);
          const bytes = new Uint8Array(binaryString.length);
          for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
          }
          
          const blob = new Blob([bytes], { type: 'application/pdf' });
          const blobUrl = window.URL.createObjectURL(blob);
          
          console.log('PDF blob URL创建成功，准备静默打印...');
          
          // 使用iframe方式进行静默打印（与兑换业务保持一致）
          this.printWithIframe(blobUrl);
          
          this.$toast?.success('收据重新打印成功');
          // 关闭模态框
          this.closeReprintModal();
        } else {
          throw new Error(response.data.message || '重新打印失败');
        }
      } catch (error) {
        console.error('重新打印失败:', error);
        this.$toast?.error('重新打印失败：' + (error.response?.data?.message || error.message));
      } finally {
        this.reprinting = false;
      }
    },
    
    // 使用iframe进行静默打印
    printWithIframe(blobUrl) {
      // 创建完全隐藏的iframe
      const iframe = document.createElement('iframe');
      iframe.style.display = 'none';
      iframe.style.position = 'absolute';
      iframe.style.width = '0px';
      iframe.style.height = '0px';
      iframe.style.border = 'none';
      iframe.style.visibility = 'hidden';
      iframe.src = blobUrl;
      
      // 添加到body
      document.body.appendChild(iframe);

      // 设置iframe属性以优化打印
      iframe.onload = () => {
        try {
          console.log('PDF iframe加载完成，准备打印...');
          
          // 延迟确保PDF完全渲染
          setTimeout(() => {
            try {
              // 获取iframe的window对象
              const iframeWindow = iframe.contentWindow;
              
              if (iframeWindow) {
                // 聚焦到iframe
                iframeWindow.focus();
                
                // 触发打印
                iframeWindow.print();
                
                console.log('打印预览已触发，等待用户操作...');
                
                // 设置清理机制
                this.setupIframeCleanup(iframe, blobUrl);
              } else {
                console.error('无法访问iframe的window对象');
                this.cleanupIframe(iframe, blobUrl);
              }
            } catch (error) {
              console.error('触发打印时出错:', error);
              this.cleanupIframe(iframe, blobUrl);
            }
          }, 1000);
          
        } catch (error) {
          console.error('iframe onload处理失败:', error);
          this.cleanupIframe(iframe, blobUrl);
        }
      };

      // 错误处理
      iframe.onerror = () => {
        console.error('iframe加载失败');
        this.cleanupIframe(iframe, blobUrl);
      };
    },
    
    // 设置iframe清理机制
    setupIframeCleanup(iframe, blobUrl) {
      let isCleanedUp = false;

      // 监听页面可见性变化
      const handleVisibilityChange = () => {
        if (!document.hidden) {
          setTimeout(() => {
            console.log('页面重新获得焦点，清理打印资源');
            if (!isCleanedUp) {
              isCleanedUp = true;
              this.cleanupIframe(iframe, blobUrl);
              removeAllListeners();
            }
          }, 2000);
        }
      };

      // 监听窗口焦点变化
      const handleWindowFocus = () => {
        setTimeout(() => {
          console.log('窗口重新获得焦点，清理打印资源');
          if (!isCleanedUp) {
            isCleanedUp = true;
            this.cleanupIframe(iframe, blobUrl);
            removeAllListeners();
          }
        }, 2000);
      };

      // 键盘事件监听（ESC键取消打印）
      const handleKeydown = (event) => {
        if (event.key === 'Escape') {
          console.log('检测到ESC键，用户可能取消了打印');
          if (!isCleanedUp) {
            isCleanedUp = true;
            this.cleanupIframe(iframe, blobUrl);
            removeAllListeners();
          }
        }
      };

      // 移除所有事件监听器的函数
      const removeAllListeners = () => {
        document.removeEventListener('visibilitychange', handleVisibilityChange);
        window.removeEventListener('focus', handleWindowFocus);
        document.removeEventListener('keydown', handleKeydown);
        if (timeoutId) {
          clearTimeout(timeoutId);
        }
      };

      // 添加事件监听器
      document.addEventListener('visibilitychange', handleVisibilityChange);
      window.addEventListener('focus', handleWindowFocus);
      document.addEventListener('keydown', handleKeydown);

      // 设置超时时间作为最后的清理保障（10分钟）
      const timeoutId = setTimeout(() => {
        console.log('打印超时，强制清理资源');
        if (!isCleanedUp) {
          isCleanedUp = true;
          this.cleanupIframe(iframe, blobUrl);
          removeAllListeners();
        }
      }, 10 * 60 * 1000);
    },
    
    // 清理iframe和相关资源
    cleanupIframe(iframe, blobUrl) {
      try {
        if (iframe && iframe.parentNode) {
          document.body.removeChild(iframe);
        }
        if (blobUrl) {
          window.URL.revokeObjectURL(blobUrl);
        }
        console.log('iframe和blob资源已清理');
      } catch (error) {
        console.error('清理资源时出错:', error);
      }
    },
    
    // CSV导出功能
    async exportToCSV() {
      try {
        this.loading = true;
        
        // 获取所有符合条件的交易记录（不分页）
        const params = {
          start_date: this.searchForm.startDate,
          end_date: this.searchForm.endDate,
          export: true // 标识为导出请求
        };
        
        // 添加搜索条件
        if (this.searchForm.transactionNo) {
          params.transaction_no = this.searchForm.transactionNo;
        }
        if (this.searchForm.customerName) {
          params.customer_name = this.searchForm.customerName;
        }
        if (this.searchForm.operatorName) {
          params.operator_name = this.searchForm.operatorName;
        }
        if (this.searchForm.minAmount) {
          params.min_amount = parseFloat(this.searchForm.minAmount);
        }
        if (this.searchForm.maxAmount) {
          params.max_amount = parseFloat(this.searchForm.maxAmount);
        }
        if (this.searchForm.currencyCode) {
          params.currency_code = this.searchForm.currencyCode;
        }
        
        const response = await api.get('transactions/export-csv', { params });
        
        if (response.data.success) {
          // 生成CSV内容
          const csvContent = this.generateCSV(response.data.transactions);
          
          // 创建下载链接
          const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
          const link = document.createElement('a');
          const url = URL.createObjectURL(blob);
          link.setAttribute('href', url);
          link.setAttribute('download', `transaction_records_${this.searchForm.startDate}_${this.searchForm.endDate}.csv`);
          link.style.visibility = 'hidden';
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          
          this.$toast?.success('CSV导出成功');
        } else {
          throw new Error(response.data.message || 'CSV导出失败');
        }
      } catch (error) {
        console.error('CSV导出失败:', error);
        this.error = '导出失败：' + (error.response?.data?.message || error.message);
      } finally {
        this.loading = false;
      }
    },
    
    // 生成CSV内容
    generateCSV(transactions) {
      const headers = [
        '交易时间',
        '交易号', 
        '类型',
        '币种',
        '金额',
        '汇率',
        '本币金额',
        '客户姓名',
        '操作员'
      ];
      
      let csvContent = '\uFEFF' + headers.join(',') + '\n'; // 添加BOM以支持中文
      
      transactions.forEach(tx => {
        const row = [
          `"${this.formatTransactionTime(tx.transaction_time)}"`,
          `"${tx.transaction_no}"`,
          `"${tx.type}"`, // 使用原始数据库值，不进行中文翻译
          `"${tx.currency_code}"`,
          `"${this.formatAmount(tx.amount)}"`,
          `"${tx.rate}"`,
          `"${this.formatAmount(tx.local_amount)}"`,
          `"${tx.customer_name || ''}"`,
          `"${tx.operator_name || ''}"`
        ];
        csvContent += row.join(',') + '\n';
      });
      
      return csvContent;
    },
    closeReprintModal() {
      if (window.bootstrap && window.bootstrap.Modal) {
        const modal = window.bootstrap.Modal.getInstance(document.getElementById('reprintModal'));
        if (modal) {
          modal.hide();
        }
      } else {
        // 降级处理 - 直接移除模态框
        const modal = document.getElementById('reprintModal');
        if (modal) {
          modal.style.display = 'none';
          modal.classList.remove('show');
          modal.setAttribute('aria-hidden', 'true');
          modal.removeAttribute('aria-modal');
          modal.removeAttribute('role');
          
          // 移除背景遮罩
          const backdrop = document.querySelector('.modal-backdrop');
          if (backdrop) {
            backdrop.remove();
          }
          
          // 恢复body的滚动
          document.body.classList.remove('modal-open');
          document.body.style.overflow = '';
          document.body.style.paddingRight = '';
        }
      }
    }
  }
}
</script>

<style scoped>
/* 选中行的样式 */
.table-info {
  background-color: rgba(13, 202, 240, 0.1) !important;
}

/* 累加显示徽章样式 */
.badge.fs-6 {
  font-size: 0.9rem !important;
  padding: 0.5rem 0.75rem;
}

/* 勾选框样式 */
.form-check-input {
  transform: scale(1.1);
}

/* 表格紧凑样式 */
.table td, .table th {
  padding: 0.5rem;
  vertical-align: middle;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .badge.fs-6 {
    font-size: 0.8rem !important;
    padding: 0.4rem 0.6rem;
  }
  
  .table-responsive {
    font-size: 0.9rem;
  }
}

.currency-flag {
  width: 20px;
  height: 15px;
  object-fit: cover;
  border-radius: 2px;
}

.pagination {
  margin-bottom: 0;
}

.page-link {
  padding: 0.375rem 0.75rem;
}

/* 分页按钮宽度调整 */
.page-link:has-text {
  min-width: 100px;
  white-space: nowrap;
  text-align: center;
  padding: 0.5rem 1rem !important;
}

.form-control:focus {
  box-shadow: none;
  border-color: #80bdff;
}

.btn:focus {
  box-shadow: none;
}

/* 紧凑查询条件样式 */
.form-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #495057;
}

.form-control-sm, .form-select-sm {
  font-size: 0.875rem;
  padding: 0.25rem 0.5rem;
}

.card-body {
  padding: 1rem;
}

.card-header {
  padding: 0.75rem 1rem;
}

/* 表格紧凑样式 */
.table th, .table td {
  padding: 0.5rem;
  font-size: 0.875rem;
}

.table th {
  background-color: #f8f9fa;
  border-bottom: 2px solid #dee2e6;
  font-weight: 600;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .d-flex.align-items-center {
    flex-direction: column;
    align-items: flex-start !important;
  }
  
  .form-label {
    margin-bottom: 0.25rem;
  }
}
</style>

<template>
  <div class="container-fluid py-4">
    <div class="row">
      <div class="col-12">
        <!-- 紧凑的标题和查询条件布局 -->
        <div class="card mb-4">
          <div class="card-body">
            <!-- 标题和查询条件在同一行 -->
            <div class="row align-items-end g-3">
              <!-- 标题 -->
              <div class="col-auto">
                <h2 class="page-title-bold mb-0">
                  <font-awesome-icon :icon="['fas', 'undo-alt']" class="me-2" />
                  {{ $t('reversal_query.title') }}
                </h2>
              </div>
              
              <!-- 查询条件 -->
              <div class="col">
                <form @submit.prevent="handleSearch">
                  <div class="row g-2 align-items-end">
                    <!-- 交易时间范围 -->
                    <div class="col-auto">
                      <label class="form-label small mb-1">{{ $t('reversal_query.search_form.transaction_time_range') }}</label>
                      <div class="d-flex gap-1 align-items-center">
                        <input 
                          type="date" 
                          class="form-control form-control-sm" 
                          v-model="searchForm.startDate"
                          style="width: 140px;"
                        >
                        <span class="text-muted small">{{ $t('reversal_query.search_form.to') }}</span>
                        <input 
                          type="date" 
                          class="form-control form-control-sm" 
                          v-model="searchForm.endDate"
                          style="width: 140px;"
                        >
                      </div>
                    </div>
                    
                    <!-- 交易号 -->
                    <div class="col-auto">
                      <label class="form-label small mb-1">{{ $t('reversal_query.search_form.transaction_no') }}</label>
                      <input 
                        type="text" 
                        class="form-control form-control-sm" 
                        v-model="searchForm.originalNo" 
                        :placeholder="$t('reversal_query.search_form.transaction_no_placeholder')"
                        style="width: 150px;"
                      >
                    </div>
                    
                    <!-- 金额范围 -->
                    <div class="col-auto">
                      <label class="form-label small mb-1">{{ $t('reversal_query.search_form.amount_range') }}</label>
                      <div class="d-flex gap-1 align-items-center">
                        <input 
                          type="number" 
                          class="form-control form-control-sm" 
                          v-model="searchForm.minAmount" 
                          :placeholder="$t('reversal_query.search_form.min_amount')"
                          style="width: 100px;"
                        >
                        <span class="text-muted small">-</span>
                        <input 
                          type="number" 
                          class="form-control form-control-sm"
                          v-model="searchForm.maxAmount" 
                          :placeholder="$t('reversal_query.search_form.max_amount')"
                          style="width: 100px;"
                        >
                      </div>
                    </div>
                    
                    <!-- 客户姓名 -->
                    <div class="col-auto">
                      <label class="form-label small mb-1">{{ $t('reversal_query.search_form.customer_name') }}</label>
                      <input 
                        type="text" 
                        class="form-control form-control-sm" 
                        v-model="searchForm.customerName" 
                        :placeholder="$t('reversal_query.search_form.customer_name_placeholder')"
                        style="width: 120px;"
                      >
                    </div>
                    
                    <!-- 操作员 -->
                    <div class="col-auto">
                      <label class="form-label small mb-1">{{ $t('reversal_query.search_form.operator') }}</label>
                      <input 
                        type="text" 
                        class="form-control form-control-sm" 
                        v-model="searchForm.operatorName" 
                        :placeholder="$t('reversal_query.search_form.operator_placeholder')"
                        style="width: 120px;"
                      >
                    </div>
                    
                    <!-- 币种 -->
                    <div class="col-auto">
                      <label class="form-label small mb-1">{{ $t('reversal_query.search_form.currency') }}</label>
                      <select 
                        class="form-select form-select-sm" 
                        v-model="searchForm.currencyCode"
                        style="width: 100px;"
                      >
                        <option value="">{{ $t('reversal_query.search_form.all_currencies') }}</option>
                        <option v-for="currency in availableCurrencies" :key="currency.code" :value="currency.code">
                          {{ currency.code }} - {{ $t(`currencies.${currency.code}`) }}
                        </option>
                      </select>
                    </div>
                    
                    <!-- 查询按钮组 -->
                    <div class="col-auto">
                      <div class="d-flex gap-1">
                        <button type="submit" class="btn btn-primary btn-sm">
                          <font-awesome-icon :icon="['fas', 'search']" class="me-1" />
                          {{ $t('reversal_query.search_form.search') }}
                        </button>
                        <button type="button" class="btn btn-secondary btn-sm" @click="resetSearch">
                          <font-awesome-icon :icon="['fas', 'undo']" class="me-1" />
                          {{ $t('reversal_query.search_form.reset') }}
                        </button>
                        <button type="button" class="btn btn-outline-primary btn-sm" @click="refreshData">
                          <font-awesome-icon :icon="['fas', 'sync']" class="me-1" :spin="loading" />
                          {{ $t('reversal_query.search_form.refresh') }}
                        </button>
                      </div>
                    </div>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>

                    <div class="card">
              <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="mb-0">{{ $t('reversal_query.results.title') }}</h5>
                <div class="text-muted">
                  {{ $t('reversal_query.results.total_records', { count: totalRecords }) }}
                </div>
              </div>
          <div class="card-body">
            <div v-if="loading" class="text-center py-4">
              <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">{{ $t('reversal_query.results.loading') }}</span>
              </div>
              <p class="mt-2">{{ $t('reversal_query.results.loading_data') }}</p>
            </div>
            
            <div v-else-if="error" class="alert alert-danger">
              {{ error }}
            </div>
            
            <div v-else>
              <div class="table-responsive">
                <table class="table table-hover">
                  <thead>
                    <tr>
                      <th>{{ $t('reversal_query.results.headers.reversal_time') }}</th>
                      <th>{{ $t('reversal_query.results.headers.reversal_no') }}</th>
                      <th>{{ $t('reversal_query.results.headers.original_no') }}</th>
                      <th>{{ $t('reversal_query.results.headers.currency') }}</th>
                      <th>{{ $t('reversal_query.results.headers.amount') }}</th>
                      <th>{{ $t('reversal_query.results.headers.operator') }}</th>
                      <th>{{ $t('reversal_query.results.headers.reason') }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="record in records" :key="record.id">
                      <td>{{ record.reversal_time }}</td>
                      <td>{{ record.reversal_no }}</td>
                      <td>{{ record.original_no }}</td>
                      <td>
                        <div class="d-flex align-items-center">
                          <CurrencyFlag 
                            :code="record.currency_code" 
                            :custom-filename="record.custom_flag_filename"
                            class="me-1" 
                          />
                          {{ getCurrencyDisplayName(record) }}
                        </div>
                      </td>
                      <td>{{ formatAmount(record.amount) }}</td>
                      <td>{{ record.operator_name }}</td>
                      <td>{{ record.reason }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              
              <!-- 分页器 -->
              <div v-if="totalRecords > 0" class="d-flex justify-content-between align-items-center mt-4">
                <div class="text-muted">
                  {{ $t('reversal_query.pagination.info', { pageSize: pageSize, totalPages: totalPages }) }}
                </div>
                <nav aria-label="Page navigation">
                  <ul class="pagination mb-0">
                    <li class="page-item" :class="{ disabled: currentPage === 1 }">
                      <a class="page-link pagination-btn" href="#" @click.prevent="handlePageChange(currentPage - 1)">
                        {{ $t('reversal_query.pagination.previous_page') }}
                      </a>
                    </li>
                    <li v-for="page in displayedPages" :key="page" class="page-item" :class="{ active: currentPage === page }">
                      <a class="page-link" href="#" @click.prevent="handlePageChange(page)">
                        {{ page }}
                      </a>
                    </li>
                    <li class="page-item" :class="{ disabled: currentPage === totalPages }">
                      <a class="page-link pagination-btn" href="#" @click.prevent="handlePageChange(currentPage + 1)">
                        {{ $t('reversal_query.pagination.next_page') }}
                      </a>
                    </li>
                  </ul>
                </nav>
              </div>
              
              <div v-if="records.length === 0" class="text-center py-4">
                <p class="text-muted mb-0">{{ $t('reversal_query.results.no_records') }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { formatAmount } from '@/utils/format'
import { formatDate } from '@/utils/dateUtils'
import api from '@/services/api'
import CurrencyFlag from '@/components/CurrencyFlag.vue'
import { getCurrencyDisplayName } from '@/utils/currencyTranslator'

export default {
  name: 'ReversalQueryView',
  components: {
    CurrencyFlag
  },
  data() {
    return {
      loading: false,
      error: null,
      records: [],
      availableCurrencies: [],
      searchForm: {
        startDate: formatDate(new Date()),
        endDate: formatDate(new Date()),
        minAmount: '',
        maxAmount: '',
        operatorName: '',
        reversalNo: '',
        originalNo: '',
        reason: '',
        customerName: '',
        currencyCode: ''
      },
      currentPage: 1,
      pageSize: 20,
      totalRecords: 0
    }
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
    }
  },
  async created() {
    await this.loadCurrencies()
    this.fetchData()
  },
  methods: {
    formatAmount,
    
    getCurrencyDisplayName(record) {
      if (!record) return ''
      
      // 使用新的币种显示函数
      return getCurrencyDisplayName(record.currency_code, record)
    },
    async loadCurrencies() {
      try {
        // 使用正确的API路径，与其他页面保持一致
        const response = await api.get('balance-management/available-currencies', {
          params: {
            branch_id: this.getCurrentBranchId(),
            include_base: true,
            require_rate: false
          }
        })
        if (response.data.success) {
          this.availableCurrencies = response.data.data.map(currency => ({
            code: currency.currency_code,
            name: currency.currency_name || this.$t(`currencies.${currency.currency_code}`)
          }))
        }
      } catch (error) {
        console.error(this.$t('reversal_query.errors.load_currencies_failed'), error)
        // 失败时使用默认币种列表，但使用翻译
        this.availableCurrencies = [
          { code: 'USD', name: this.$t('currencies.USD') },
          { code: 'EUR', name: this.$t('currencies.EUR') },
          { code: 'JPY', name: this.$t('currencies.JPY') },
          { code: 'GBP', name: this.$t('currencies.GBP') },
          { code: 'HKD', name: this.$t('currencies.HKD') },
          { code: 'SGD', name: this.$t('currencies.SGD') },
          { code: 'THB', name: this.$t('currencies.THB') },
          { code: 'CNY', name: this.$t('currencies.CNY') },
          { code: 'AUD', name: this.$t('currencies.AUD') },
          { code: 'CAD', name: this.$t('currencies.CAD') },
          { code: 'CHF', name: this.$t('currencies.CHF') }
        ]
      }
    },
    async fetchData() {
      this.loading = true
      this.error = null
      try {
        const params = {
          page: this.currentPage,
          page_size: this.pageSize,
          start_date: this.searchForm.startDate,
          end_date: this.searchForm.endDate,
          min_amount: this.searchForm.minAmount || null,
          max_amount: this.searchForm.maxAmount || null,
          operator_name: this.searchForm.operatorName || null,
          reversal_no: this.searchForm.reversalNo || null,
          original_no: this.searchForm.originalNo || null,
          reason: this.searchForm.reason || null,
          customer_name: this.searchForm.customerName || null,
          currency_code: this.searchForm.currencyCode || null
        }
        
        const response = await api.get('transactions/reversal-query', { params })
        if (response.data.success) {
          this.records = response.data.records || []
          this.totalRecords = response.data.pagination?.total_count || 0
        } else {
          this.error = response.data.message
          this.records = []
          this.totalRecords = 0
        }
      } catch (error) {
        this.error = this.$t('reversal_query.results.load_failed', { message: error.response?.data?.message || error.message })
        this.records = []
        this.totalRecords = 0
      } finally {
        this.loading = false
      }
    },
    handleSearch() {
      this.currentPage = 1
      this.fetchData()
    },
    resetSearch() {
      this.searchForm = {
        startDate: formatDate(new Date()),
        endDate: formatDate(new Date()),
        minAmount: '',
        maxAmount: '',
        operatorName: '',
        reversalNo: '',
        originalNo: '',
        reason: '',
        customerName: '',
        currencyCode: ''
      }
      this.currentPage = 1
      this.fetchData()
    },
    handlePageChange(page) {
      if (page >= 1 && page <= this.totalPages) {
        this.currentPage = page
        this.fetchData()
      }
    },
    refreshData() {
      this.fetchData()
    },
    
    // 获取当前分支ID
    getCurrentBranchId() {
      try {
        const user = JSON.parse(localStorage.getItem('user') || '{}')
        return user.branch_id
      } catch {
        return null
      }
    }
  }
}
</script>

<style scoped>
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

.form-control:focus {
  box-shadow: none;
  border-color: #80bdff;
}

.btn:focus {
  box-shadow: none;
}

/* 紧凑布局样式 */
.form-label.small {
  font-size: 0.875rem;
  font-weight: 500;
  color: #6c757d;
}

.form-control-sm, .form-select-sm {
  font-size: 0.875rem;
}

.btn-sm {
  font-size: 0.875rem;
}

/* 分页按钮宽度调整 */
.pagination-btn {
  min-width: 100px;
  white-space: nowrap;
  text-align: center;
  padding: 0.5rem 1rem !important;
}

/* 响应式调整 */
@media (max-width: 1400px) {
  .row.g-2 {
    flex-wrap: wrap;
  }
  
  .col-auto {
    margin-bottom: 0.5rem;
  }
}

@media (max-width: 1200px) {
  .row.align-items-end.g-3 {
    flex-direction: column;
    align-items: stretch !important;
  }
  
  .col-auto h4 {
    margin-bottom: 1rem;
  }
}
</style> 
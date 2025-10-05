<template>
  <div class="container-fluid py-4">
    <div class="row">
      <div class="col-12">
        <div class="d-flex justify-content-between align-items-center mb-4">
          <h2 class="page-title-bold">
            <font-awesome-icon :icon="['fas', 'balance-scale']" class="me-2" />
            {{ $t('balance_adjust_query.title') }}
          </h2>
        </div>
        
        <div class="row">
          <div class="col-md-12">
            <div class="card mb-4">
              <div class="card-header">
                <h5 class="mb-0">{{ $t('balance_adjust_query.search_form.title') }}</h5>
              </div>
              <div class="card-body">
                <form @submit.prevent="handleSearch">
                  <div class="row g-3">
                    <!-- 调节时间范围 -->
                    <div class="col-md-6">
                      <label class="form-label">{{ $t('balance_adjust_query.search_form.adjustment_time_range') }}</label>
                      <div class="d-flex gap-2">
                        <input 
                          type="date" 
                          class="form-control" 
                          v-model="searchForm.startDate"
                        >
                        <span class="align-self-center">{{ $t('balance_adjust_query.search_form.to') }}</span>
                        <input 
                          type="date" 
                          class="form-control" 
                          v-model="searchForm.endDate"
                        >
                      </div>
                    </div>
                    
                    <!-- 调节金额范围 -->
                    <div class="col-md-6">
                      <label class="form-label">{{ $t('balance_adjust_query.search_form.adjustment_amount_range') }}</label>
                      <div class="d-flex gap-2">
                        <input 
                          type="number" 
                          class="form-control" 
                          v-model="searchForm.minAmount" 
                          :placeholder="$t('balance_adjust_query.search_form.min_amount')"
                        >
                        <span class="align-self-center">-</span>
                        <input 
                          type="number" 
                          class="form-control"
                          v-model="searchForm.maxAmount" 
                          :placeholder="$t('balance_adjust_query.search_form.max_amount')"
                        >
                      </div>
                    </div>
                    
                    <!-- 操作员 -->
                    <div class="col-md-3">
                      <label class="form-label">{{ $t('balance_adjust_query.search_form.operator') }}</label>
                      <input 
                        type="text" 
                        class="form-control" 
                        v-model="searchForm.operatorName" 
                        :placeholder="$t('balance_adjust_query.search_form.operator_placeholder')"
                      >
                    </div>

                    <!-- 调节原因 -->
                    <div class="col-md-3">
                      <label class="form-label">{{ $t('balance_adjust_query.search_form.adjustment_reason') }}</label>
                      <input 
                        type="text" 
                        class="form-control" 
                        v-model="searchForm.reason" 
                        :placeholder="$t('balance_adjust_query.search_form.reason_placeholder')"
                      >
                    </div>
                    
                    <!-- 查询按钮组 -->
                    <div class="col-12">
                      <div class="d-flex gap-2">
                        <button type="submit" class="btn btn-primary">
                          <font-awesome-icon :icon="['fas', 'search']" class="me-1" />
                          {{ $t('balance_adjust_query.search_form.search') }}
                        </button>
                        <button type="button" class="btn btn-secondary" @click="resetSearch">
                          <font-awesome-icon :icon="['fas', 'undo']" class="me-1" />
                          {{ $t('balance_adjust_query.search_form.reset') }}
                        </button>
                        <button type="button" class="btn btn-outline-primary" @click="refreshData">
                          <font-awesome-icon :icon="['fas', 'sync']" class="me-1" :spin="loading" />
                          {{ $t('balance_adjust_query.search_form.refresh') }}
                        </button>
                      </div>
                    </div>
                  </div>
                </form>
              </div>
            </div>

            <div class="card">
              <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="mb-0">{{ $t('balance_adjust_query.results.title') }}</h5>
                <div class="text-muted">
                  {{ $t('balance_adjust_query.results.total_records', { count: totalRecords }) }}
                </div>
              </div>
              <div class="card-body">
                <div v-if="loading" class="text-center py-4">
                  <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">{{ $t('balance_adjust_query.results.loading') }}</span>
                  </div>
                  <p class="mt-2">{{ $t('balance_adjust_query.results.loading_data') }}</p>
                </div>
                
                <div v-else-if="error" class="alert alert-danger">
                  {{ error }}
                </div>
                
                <div v-else>
                  <div class="table-responsive">
                    <table class="table table-hover">
                      <thead>
                        <tr>
                          <th>{{ $t('balance_adjust_query.results.headers.adjustment_time') }}</th>
                          <th>{{ $t('balance_adjust_query.results.headers.adjustment_no') }}</th>
                          <th>{{ $t('balance_adjust_query.results.headers.currency') }}</th>
                          <th>{{ $t('balance_adjust_query.results.headers.adjustment_amount') }}</th>
                          <th>{{ $t('balance_adjust_query.results.headers.balance_before') }}</th>
                          <th>{{ $t('balance_adjust_query.results.headers.balance_after') }}</th>
                          <th>{{ $t('balance_adjust_query.results.headers.operator') }}</th>
                          <th>{{ $t('balance_adjust_query.results.headers.reason') }}</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="record in records" :key="record.id">
                          <td>{{ record.adjust_time }}</td>
                          <td>{{ record.adjust_no }}</td>
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
                          <td>{{ formatAmount(record.adjust_amount) }}</td>
                          <td>{{ formatAmount(record.balance_before) }}</td>
                          <td>{{ formatAmount(record.balance_after) }}</td>
                          <td>{{ record.operator_name }}</td>
                          <td>{{ record.reason }}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  
                  <!-- 分页器 -->
                  <div v-if="totalRecords > 0" class="d-flex justify-content-between align-items-center mt-4">
                    <div class="text-muted">
                      {{ $t('balance_adjust_query.pagination.info', { pageSize: pageSize, totalPages: totalPages }) }}
                    </div>
                    <nav aria-label="Page navigation">
                      <ul class="pagination mb-0">
                        <li class="page-item" :class="{ disabled: currentPage === 1 }">
                          <a class="page-link" href="#" @click.prevent="handlePageChange(currentPage - 1)">
                            {{ $t('balance_adjust_query.pagination.previous_page') }}
                          </a>
                        </li>
                        <li v-for="page in displayedPages" :key="page" class="page-item" :class="{ active: currentPage === page }">
                          <a class="page-link" href="#" @click.prevent="handlePageChange(page)">
                            {{ page }}
                          </a>
                        </li>
                        <li class="page-item" :class="{ disabled: currentPage === totalPages }">
                          <a class="page-link" href="#" @click.prevent="handlePageChange(currentPage + 1)">
                            {{ $t('balance_adjust_query.pagination.next_page') }}
                          </a>
                        </li>
                      </ul>
                    </nav>
                  </div>
                  
                  <div v-if="records.length === 0" class="text-center py-4">
                    <p class="text-muted mb-0">{{ $t('balance_adjust_query.results.no_records') }}</p>
                  </div>
                </div>
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
import CurrencyFlag from '@/components/CurrencyFlag.vue'
import api from '@/services/api'
import { getCurrencyDisplayName } from '@/utils/currencyTranslator'

export default {
  name: 'BalanceAdjustQueryView',
  components: {
    CurrencyFlag
  },
  data() {
    return {
      loading: false,
      error: null,
      records: [],
      searchForm: {
        startDate: formatDate(new Date()),
        endDate: formatDate(new Date()),
        minAmount: '',
        maxAmount: '',
        operatorName: '',
        reason: ''
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
  created() {
    this.fetchData()
  },
  methods: {
    formatAmount,
    getCurrencyDisplayName(record) {
      if (!record) return ''
      
      // 使用新的币种显示函数
      return getCurrencyDisplayName(record.currency_code, record)
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
          reason: this.searchForm.reason || null
        }
        
        const response = await api.get('balance-adjustments/adjustment-query', { params })
        if (response.data.success) {
          this.records = response.data.records || []
          this.totalRecords = response.data.pagination?.total_count || 0
        } else {
          this.error = response.data.message
          this.records = []
          this.totalRecords = 0
        }
      } catch (error) {
        this.error = this.$t('balance_adjust_query.results.load_failed', { message: error.response?.data?.message || error.message })
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
        reason: ''
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
</style> 
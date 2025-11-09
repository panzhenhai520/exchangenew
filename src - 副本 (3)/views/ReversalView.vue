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
                  {{ $t('reversals.title') }}
                </h2>
              </div>
              
              <!-- 查询条件 -->
              <div class="col">
                <form @submit.prevent="handleSearch">
                  <div class="row g-2 align-items-end">
                    <!-- 交易时间范围 -->
                    <div class="col-auto">
                      <label class="form-label small mb-1">{{ $t('reversals.transaction_time_range') }}</label>
                      <div class="d-flex gap-1 align-items-center">
                        <input 
                          type="date" 
                          class="form-control form-control-sm" 
                          v-model="searchForm.startDate"
                          style="width: 140px;"
                        >
                        <span class="text-muted small">{{ $t('reversals.to') }}</span>
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
                      <label class="form-label small mb-1">{{ $t('reversals.transaction_no') }}</label>
                      <input 
                        type="text" 
                        class="form-control form-control-sm" 
                        v-model="searchForm.transactionNo" 
                        :placeholder="$t('reversals.transaction_no_placeholder')"
                        style="width: 150px;"
                      >
                    </div>
                    
                    <!-- 金额范围 -->
                    <div class="col-auto">
                      <label class="form-label small mb-1">{{ $t('reversals.amount_range') }}</label>
                      <div class="d-flex gap-1 align-items-center">
                        <input 
                          type="number" 
                          class="form-control form-control-sm" 
                          v-model="searchForm.minAmount" 
                          :placeholder="$t('reversals.min_amount')"
                          style="width: 100px;"
                        >
                        <span class="text-muted small">-</span>
                        <input 
                          type="number" 
                          class="form-control form-control-sm"
                          v-model="searchForm.maxAmount" 
                          :placeholder="$t('reversals.max_amount')"
                          style="width: 100px;"
                        >
                      </div>
                    </div>
                    
                    <!-- 客户姓名 -->
                    <div class="col-auto">
                      <label class="form-label small mb-1">{{ $t('reversals.customer_name') }}</label>
                      <input 
                        type="text" 
                        class="form-control form-control-sm" 
                        v-model="searchForm.customerName" 
                        :placeholder="$t('reversals.customer_name_placeholder')"
                        style="width: 120px;"
                      >
                    </div>
                    
                    <!-- 操作员 -->
                    <div class="col-auto">
                      <label class="form-label small mb-1">{{ $t('reversals.operator') }}</label>
                      <input 
                        type="text" 
                        class="form-control form-control-sm" 
                        v-model="searchForm.operatorName" 
                        :placeholder="$t('reversals.operator_placeholder')"
                        style="width: 120px;"
                      >
                    </div>
                    
                    <!-- 币种 -->
                    <div class="col-auto">
                      <label class="form-label small mb-1">{{ $t('reversals.currency') }}</label>
                      <select 
                        class="form-select form-select-sm" 
                        v-model="searchForm.currencyCode"
                        style="width: 120px;"
                      >
                        <option value="">{{ $t('reversals.all_currencies') }}</option>
                        <option v-for="currency in availableCurrencies" 
                                :key="currency.currency_id" 
                                :value="currency.currency_code">
                          {{ currency.currency_code }} ({{ $t(`currencies.${currency.currency_code}`) }})
                        </option>
                      </select>
                    </div>
                    
                    <!-- 查询按钮组 -->
                    <div class="col-auto">
                      <div class="d-flex gap-1">
                        <button type="submit" class="btn btn-primary btn-sm">
                          <font-awesome-icon :icon="['fas', 'search']" class="me-1" />
                          {{ $t('reversals.search') }}
                        </button>
                        <button type="button" class="btn btn-secondary btn-sm" @click="resetSearch">
                          <font-awesome-icon :icon="['fas', 'undo']" class="me-1" />
                          {{ $t('reversals.reset') }}
                        </button>
                        <button type="button" class="btn btn-outline-primary btn-sm" @click="refreshTransactions">
                          <font-awesome-icon :icon="['fas', 'sync']" class="me-1" :spin="loading" />
                          {{ $t('reversals.refresh') }}
                        </button>
                      </div>
                    </div>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>

        <div class="card mb-4">
          <div class="card-header d-flex justify-content-between align-items-center">
            <h5 class="mb-0">{{ $t('reversals.transaction_list') }}</h5>
            <div class="text-muted">
              {{ $t('reversals.total_records', { count: totalRecords }) }}
            </div>
          </div>
          <div class="card-body">
            <div v-if="loading" class="text-center py-4">
              <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">{{ $t('reversals.loading') }}</span>
              </div>
              <p class="mt-2">{{ $t('reversals.loading_transactions') }}</p>
            </div>
            
            <div v-else-if="error" class="alert alert-danger">
              {{ error }}
            </div>
            
            <div v-else>
              <div class="table-responsive">
                <table class="table table-hover">
                  <thead>
                  <tr>
                    <th>{{ $t('reversals.headers.transaction_time') }}</th>
                      <th>{{ $t('reversals.headers.transaction_no') }}</th>
                      <th>{{ $t('reversals.headers.type') }}</th>
                      <th>{{ $t('reversals.headers.currency') }}</th>
                      <th>{{ $t('reversals.headers.amount') }}</th>
                    <th>{{ $t('reversals.headers.rate') }}</th>
                      <th>{{ $t('reversals.headers.local_currency') }}</th>
                      <th>{{ $t('reversals.headers.customer_name') }}</th>
                    <th>{{ $t('reversals.headers.operator') }}</th>
                      <th>{{ $t('reversals.headers.actions') }}</th>
                  </tr>
                  </thead>
                  <tbody>
                    <tr v-for="tx in transactions" :key="tx.id" :class="{'table-danger': tx.type === 'reversal'}">
                      <td>{{ formatTransactionTime(tx.transaction_time) }}</td>
                      <td>{{ tx.transaction_no }}</td>
                      <td>
                        <span :class="getTypeClass(tx.type)">
                          {{ getTypeText(tx.type) }}
                        </span>
                      </td>
                      <td>
                        <div class="d-flex align-items-center">
                          <CurrencyFlag :code="tx.currency_code" :custom-filename="tx.custom_flag_filename" class="me-1" />
                          {{ tx.currency_code }}
                        </div>
                      </td>
                      <td>{{ formatAmount(tx.amount) }}</td>
                      <td>{{ tx.rate }}</td>
                      <td>{{ formatAmount(tx.local_amount) }}</td>
                      <td>{{ getCustomerNameText(tx.customer_name) }}</td>
                      <td>{{ tx.operator_name }}</td>
                      <td>
                        <button 
                          v-if="canReverse(tx)"
                          class="btn btn-warning btn-sm"
                          @click="showReversalConfirm(tx)"
                        >
                          <font-awesome-icon :icon="['fas', 'undo']" class="me-1" />
                          {{ $t('reversals.actions.reverse') }}
                        </button>
                        <span v-else class="badge" :class="getReversalStatusClass(tx)">
                          {{ getReversalStatusText(tx) }}
                        </span>
                      </td>
                  </tr>
                </tbody>
              </table>
              </div>
              
              <!-- 分页器 -->
              <div v-if="totalRecords > 0" class="d-flex justify-content-between align-items-center mt-4">
                <div class="text-muted">
                  {{ $t('reversals.pagination_info', { pageSize: pageSize, totalPages: totalPages }) }}
                </div>
                <nav aria-label="Page navigation">
                  <ul class="pagination mb-0">
                    <li class="page-item" :class="{ disabled: currentPage === 1 }">
                      <a class="page-link" href="#" @click.prevent="handlePageChange(currentPage - 1)">
                        {{ $t('reversals.pagination.previous_page') }}
                      </a>
                    </li>
                    <li v-for="page in displayedPages" :key="page" class="page-item" :class="{ active: currentPage === page }">
                      <a class="page-link" href="#" @click.prevent="handlePageChange(page)">
                        {{ page }}
                      </a>
                    </li>
                    <li class="page-item" :class="{ disabled: currentPage === totalPages }">
                      <a class="page-link" href="#" @click.prevent="handlePageChange(currentPage + 1)">
                        {{ $t('reversals.pagination.next_page') }}
                      </a>
                    </li>
                </ul>
                </nav>
              </div>
              
              <div v-if="transactions.length === 0" class="text-center py-4">
                <p class="text-muted mb-0">{{ $t('reversals.messages.no_transactions') }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 冲减确认对话框 -->
    <div class="modal fade" id="reversalModal" tabindex="-1" ref="reversalModal">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ $t('reversals.modal.title') }}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body" v-if="selectedTransaction">
            <div class="alert alert-warning">
              <h6>{{ $t('reversals.modal.confirm_message') }}</h6>
              <p class="mb-2">{{ $t('reversals.transaction_no') }}：{{ selectedTransaction.transaction_no }}</p>
              <p class="mb-2">{{ $t('reversals.headers.type') }}：{{ getTypeText(selectedTransaction.type) }}</p>
              <p class="mb-2">{{ $t('reversals.headers.amount') }}：{{ formatAmount(selectedTransaction.amount) }} {{ selectedTransaction.currency_code }}</p>
              <p class="mb-2">{{ $t('reversals.headers.customer_name') }}：{{ getCustomerNameText(selectedTransaction.customer_name) }}</p>
            </div>
            
            <div class="mb-3">
              <label for="reversal-reason" class="form-label">{{ $t('reversals.modal.reason_label') }} <span class="text-danger">*</span></label>
              <textarea
                id="reversal-reason"
                class="form-control"
                v-model="reversalReason"
                rows="3"
                :placeholder="$t('reversals.modal.reason_placeholder')"
                required
              ></textarea>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">{{ $t('reversals.modal.cancel') }}</button>
            <button 
              type="button" 
              class="btn btn-warning" 
              @click="handleReversal"
              :disabled="!reversalReason || processing"
            >
              <span v-if="processing">
                <span class="spinner-border spinner-border-sm me-1"></span>
                {{ $t('reversals.processing') }}
              </span>
              <span v-else>
                <font-awesome-icon :icon="['fas', 'undo']" class="me-1" />
                {{ $t('reversals.modal.confirm') }}
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 冲正成功模态框 - 仿照兑换交易样式 -->
    <div class="modal fade show" 
         v-if="reversalSuccess" 
         tabindex="-1" 
         style="display: block; background: rgba(0,0,0,0.5)"
         @click.self="closeReversalSuccess">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header bg-success text-white">
            <h5 class="modal-title">{{ $t('reversals.success.title') }}</h5>
            <button type="button" class="btn-close btn-close-white" @click="closeReversalSuccess"></button>
          </div>
          <div class="modal-body">
            <div id="printArea">
              <div class="receipt-container">
                <div class="text-center mb-2">
                  <h5 class="mb-1">{{ $t('reversals.receipt.title') }}</h5>
                  <small>{{ $t('reversals.receipt.subtitle') }}</small>
                  <div class="small mt-1" style="color: #666;">
                    {{ getBranchDisplay() }} {{ $t('reversals.receipt.type') }}
                  </div>
                </div>
                
                <table class="receipt-table">
                  <tbody>
                    <tr>
                      <td width="35%">{{ $t('reversals.receipt.transaction_no') }}</td>
                      <td>{{ reversalDetails.transaction_no }}</td>
                    </tr>
                    <tr>
                      <td>{{ $t('reversals.receipt.date') }}</td>
                      <td>{{ formatDateTime(new Date()) }}</td>
                    </tr>
                    <tr>
                      <td>{{ $t('reversals.receipt.type') }}</td>
                      <td>{{ $t('reversals.receipt.reversal_type') }}</td>
                    </tr>
                    <tr>
                      <td>{{ $t('reversals.receipt.original_no') }}</td>
                      <td>{{ reversalDetails.original_transaction_no }}</td>
                    </tr>
                    <tr>
                      <td>{{ $t('reversals.receipt.currency') }}</td>
                      <td>{{ reversalDetails.currency_code }}</td>
                    </tr>
                    <tr>
                      <td>{{ $t('reversals.receipt.amount') }}</td>
                      <td>{{ formatAmount(reversalDetails.amount) }}</td>
                    </tr>
                    <tr>
                      <td>{{ $t('reversals.receipt.customer_name') }}</td>
                      <td>{{ reversalDetails.customer_name }}</td>
                    </tr>
                    <tr>
                      <td>{{ $t('reversals.receipt.reason') }}</td>
                      <td>{{ reversalDetails.reason }}</td>
                    </tr>
                    <tr>
                      <td>{{ $t('reversals.receipt.operator') }}</td>
                      <td>{{ operatorName }}</td>
                    </tr>
                  </tbody>
                </table>

                <div class="row g-2">
                  <div class="col-6">
                    <div class="signature-box text-center">
                      <div>{{ $t('reversals.receipt.customer_signature') }}</div>
                      <div class="signature-line"></div>
                      <small>{{ $t('reversals.receipt.date_signature') }}:_____________</small>
                    </div>
                  </div>
                  <div class="col-6">
                    <div class="signature-box text-center">
                      <div>{{ $t('reversals.receipt.teller_signature') }}</div>
                      <div class="signature-line"></div>
                      <small>{{ $t('reversals.receipt.date_signature') }}:_____________</small>
                    </div>
                  </div>
                </div>

                <div class="notice-section">
                  <div class="small">{{ $t('reversals.receipt.notice') }}</div>
                  <div class="small">{{ $t('reversals.receipt.notice_en') }}</div>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="closeReversalSuccess">{{ $t('reversals.success.close') }}</button>
            <button class="btn btn-primary" @click="printReversalReceipt">
              <font-awesome-icon :icon="['fas', 'print']" class="me-1" />
              {{ $t('reversals.success.print') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { Modal } from 'bootstrap'
import CurrencyFlag from '@/components/CurrencyFlag.vue'
import { formatAmount } from '@/utils/format'
import { formatTransactionTime, formatDateTime } from '@/utils/formatters'
import { formatDate } from '@/utils/dateUtils'
import api from '@/services/api'
import printService, { PrintService } from '@/services/printService'

export default {
  name: 'ReversalView',
  components: {
    CurrencyFlag
  },
  data() {
    return {
      loading: false,
      error: null,
      transactions: [],
      selectedTransaction: null,
      reversalReason: '',
      processing: false,
      modal: null,
      reversalSuccess: false,
      reversalDetails: null,
      branchName: '',
      operatorName: '',
      // 查询表单
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
      // 分页相关
      currentPage: 1,
      pageSize: 20,
      totalRecords: 0,
      availableCurrencies: [],
      // 日结完成日期列表
      eodCompletedDates: []
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
    await this.loadAvailableCurrencies()
    await this.fetchTransactions()
  },
  mounted() {
    this.modal = new Modal(this.$refs.reversalModal)
  },
  methods: {
    formatAmount,
    formatTransactionTime,
    formatDateTime,
    async fetchTransactions() {
      this.loading = true
      this.error = null
      try {
        const params = {
          page: this.currentPage,
          page_size: this.pageSize,
          start_date: this.searchForm.startDate,
          end_date: this.searchForm.endDate,
          transaction_no: this.searchForm.transactionNo,
          min_amount: this.searchForm.minAmount || null,
          max_amount: this.searchForm.maxAmount || null,
          customer_name: this.searchForm.customerName || null,
          operator_name: this.searchForm.operatorName || null,
          currency_code: this.searchForm.currencyCode || null
        }
        
        const response = await api.get('transactions/query', { params })
        if (response.data.success) {
          this.transactions = response.data.transactions
          this.totalRecords = response.data.pagination.total_count
          
          // 获取日结完成日期列表
          await this.fetchEODCompletedDates()
        } else {
          this.error = response.data.message
        }
      } catch (error) {
        this.error = '加载交易数据失败：' + (error.response?.data?.message || error.message)
      } finally {
        this.loading = false
      }
    },
    handleSearch() {
      this.currentPage = 1
      this.fetchTransactions()
    },
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
      }
      this.currentPage = 1
      this.fetchTransactions()
    },
    handlePageChange(page) {
      if (page >= 1 && page <= this.totalPages) {
        this.currentPage = page
        this.fetchTransactions()
      }
    },
    refreshTransactions() {
      this.fetchTransactions()
    },
    getTypeClass(type) {
      const classes = {
        buy: 'text-success',
        sell: 'text-danger',
        reversal: 'text-warning',
        cash_out: 'text-info'
      }
      return classes[type] || ''
    },
    getTypeText(type) {
      // 使用翻译显示交易类型
      return this.$t(`reversals.types.${type}`) || type
    },
    getCustomerNameText(customerName) {
      // 处理特殊的翻译key
      if (customerName === 'balance.system_initial_balance_setup') {
        return this.$t('balance.system_initial_balance_setup')
      }
      return customerName
    },
    canReverse(transaction) {
      // 1. 作废记录本身不能再次作废
      if (transaction.type === 'reversal') {
        return false
      }
      
      // 2. 只有原始交易（没有原始交易号的）才能作废
      if (transaction.original_transaction_no) {
        return false
      }
      
      // 3. 只有特定类型的交易可以作废
      const reversibleTypes = ['buy', 'sell', 'adjust_balance', 'initial_balance']
      if (!reversibleTypes.includes(transaction.type)) {
        return false
      }
      
      // 4. 【关键检查】已被冲正的交易不能再次作废
      if (transaction.status === 'reversed') {
        return false
      }
      
      // 5. 【双重保险】检查是否存在对应的冲正记录
      const hasReversalRecord = this.transactions.some(tx => 
        tx.type === 'reversal' && 
        tx.original_transaction_no === transaction.transaction_no
      )
      
      if (hasReversalRecord) {
        return false
      }
      
      // 6. 【日结检查】检查交易是否在日结之前
      if (this.eodCompletedDates && this.eodCompletedDates.length > 0) {
        const transactionDate = new Date(transaction.transaction_date)
        const hasCompletedEOD = this.eodCompletedDates.some(eodDate => {
          const eodDateObj = new Date(eodDate)
          return eodDateObj >= transactionDate
        })
        
        if (hasCompletedEOD) {
          return false
        }
      }
      
      return true
    },
    
    getReversalStatusClass(transaction) {
      if (transaction.type === 'reversal') {
        return 'bg-danger'
      } else if (transaction.original_transaction_no) {
        return 'bg-secondary'
      } else if (!['buy', 'sell', 'adjust_balance', 'initial_balance'].includes(transaction.type)) {
        return 'bg-info'
      } else if (transaction.status === 'reversed') {
        return 'bg-warning'
      }
      // 【增强检查】双重验证是否存在冲正记录
      const hasReversalRecord = this.transactions.some(tx => 
        tx.type === 'reversal' && 
        tx.original_transaction_no === transaction.transaction_no
      )
      
      if (hasReversalRecord) {
        return 'bg-warning'
      }
      
      // 【日结检查】检查交易是否在日结之前
      if (this.eodCompletedDates && this.eodCompletedDates.length > 0) {
        const transactionDate = new Date(transaction.transaction_date)
        const hasCompletedEOD = this.eodCompletedDates.some(eodDate => {
          const eodDateObj = new Date(eodDate)
          return eodDateObj >= transactionDate
        })
        
        if (hasCompletedEOD) {
          return 'bg-dark' // 使用深色背景表示日结完成
        }
      }
      
      return 'bg-success'
    },
    
    getReversalStatusText(transaction) {
      if (transaction.type === 'reversal') {
        return this.$t('reversals.status.reversal_record')
      } else if (transaction.original_transaction_no) {
        return this.$t('reversals.status.reversed')
      } else if (!['buy', 'sell', 'adjust_balance', 'initial_balance'].includes(transaction.type)) {
        return this.$t('reversals.status.not_reversible')
      } else if (transaction.status === 'reversed') {
        return this.$t('reversals.status.reversed')
      }
      // 【增强检查】双重验证是否存在冲正记录
      const hasReversalRecord = this.transactions.some(tx => 
        tx.type === 'reversal' && 
        tx.original_transaction_no === transaction.transaction_no
      )
      
      if (hasReversalRecord) {
        return this.$t('reversals.status.reversed')
      }
      
      // 【日结检查】检查交易是否在日结之前
      if (this.eodCompletedDates && this.eodCompletedDates.length > 0) {
        const transactionDate = new Date(transaction.transaction_date)
        const hasCompletedEOD = this.eodCompletedDates.some(eodDate => {
          const eodDateObj = new Date(eodDate)
          return eodDateObj >= transactionDate
        })
        
        if (hasCompletedEOD) {
          return this.$t('reversals.status.eod_completed') || '日结已完成，不可作废'
        }
      }
      
      return this.$t('reversals.status.can_reverse')
    },
    showReversalConfirm(transaction) {
      // 再次验证是否可以作废（双重保险）
      if (!this.canReverse(transaction)) {
        this.$toast?.error('该交易不能作废：' + this.getReversalStatusText(transaction))
        return
      }
      
      this.selectedTransaction = transaction
      this.reversalReason = ''
      this.modal.show()
    },
    async handleReversal() {
      if (!this.reversalReason) {
        return
      }
      
      this.processing = true
      try {
        const response = await api.post('transactions/reverse', {
          transaction_no: this.selectedTransaction.transaction_no,
          reason: this.reversalReason
        })
        
        if (response.data.success) {
          this.modal.hide()
          await this.fetchTransactions()
          
          // 构造冲正详细信息
          const userData = JSON.parse(localStorage.getItem('user') || '{}');
          this.reversalDetails = {
            transaction_no: response.data.reversal_transaction_no,
            transaction_id: response.data.reversal_transaction_id, // 保存交易ID用于PDF打印
            original_transaction_no: this.selectedTransaction.transaction_no,
            currency_code: this.selectedTransaction.currency_code,
            amount: this.selectedTransaction.amount,
            customer_name: this.selectedTransaction.customer_name,
            reason: this.reversalReason
          };
          this.branchName = userData.branch_name || '未知网点';
          this.operatorName = userData.username || this.$t('common.unknown_operator');
          this.reversalSuccess = true;
        } else {
          this.$toast?.error(response.data.message || '作废失败')
        }
      } catch (error) {
        this.$toast?.error('作废失败：' + (error.response?.data?.message || error.message))
      } finally {
        this.processing = false
      }
    },
    closeReversalSuccess() {
      this.reversalSuccess = false
      this.reversalDetails = null
      this.branchName = ''
      this.operatorName = ''
    },
    async loadAvailableCurrencies() {
      try {
        console.log('开始加载币种数据...');
        // 参考TransactionsView.vue的实现，使用正确的API路径
        const response = await api.get('balance-management/available-currencies', {
          params: {
            branch_id: this.getCurrentBranchId(),
            include_base: true,
            require_rate: false
          }
        });
        
        console.log('币种API响应:', response.data);
        
        if (response.data.success) {
          this.availableCurrencies = response.data.data.sort((a, b) => 
            a.currency_code.localeCompare(b.currency_code)
          );
          console.log('币种数据加载成功，数量:', this.availableCurrencies.length);
          console.log('币种列表:', this.availableCurrencies);
        } else {
          console.error('币种API返回失败:', response.data.message);
        }
      } catch (error) {
        console.error('加载可用币种失败:', error);
        console.error('错误详情:', error.response?.data || error.message);
      }
    },
    
    async fetchEODCompletedDates() {
      try {
        // 获取当前用户的分支ID
        const user = JSON.parse(localStorage.getItem('user') || '{}')
        const branchId = user.branch_id
        
        if (!branchId) {
          console.warn('无法获取分支ID，跳过日结日期检查')
          return
        }
        
        // 获取日结历史记录
        const response = await api.get('end_of_day/history', {
          params: {
            branch_id: branchId,
            status: 'completed'
          }
        })
        
        if (response.data.success) {
          // 提取已完成的日结日期
          this.eodCompletedDates = response.data.history.map(item => item.date)
          console.log('已完成的日结日期:', this.eodCompletedDates)
        }
      } catch (error) {
        console.error('获取日结完成日期失败:', error)
        this.eodCompletedDates = []
      }
    },
    
    async printReversalReceipt() {
      try {
        console.log('准备打印交易冲正PDF凭证...');
        
        if (!this.reversalDetails || !this.reversalDetails.transaction_id) {
          this.$toast?.error(this.$t('reversals.messages.transaction_info_missing') || '无法获取冲正交易信息，请重新操作');
          return;
        }
        
        // 使用统一打印服务的PDF打印功能，传递当前语言设置
        const currentLanguage = this.$i18n.locale || 'zh-CN';
        const languageCode = currentLanguage.split('-')[0]; // 将 'en-US' 转换为 'en'
        const config = PrintService.getReversalConfig(this.reversalDetails.transaction_id, this.$toast, languageCode);
        const success = await printService.printReversalPDF(config, this.reversalDetails.transaction_no);
        
        if (success) {
          console.log('交易冲正PDF凭证打印完成');
        }
      } catch (error) {
        console.error('打印交易冲正凭证失败:', error);
        this.$toast?.error(this.$t('reversals.messages.print_failed') || '打印失败，请重试');
      }
    },
    getBranchDisplay() {
      // 从localStorage获取用户信息中的网点名称和代码
      try {
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        const branchName = user.branch_name || '未知网点';
        const branchCode = user.branch_code || '';
        return branchCode ? `${branchName}(${branchCode})` : branchName;
      } catch (error) {
        console.error('获取网点信息失败:', error);
        return '未知网点';
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
  min-width: 60px; /* 确保按钮有足够的最小宽度 */
  white-space: nowrap; /* 防止文字换行 */
  text-align: center; /* 文字居中 */
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

/* 打印凭证样式 */
.receipt-container {
  background: white;
  padding: 15px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.4;
  border: 1px solid #ddd;
  margin-bottom: 10px;
}

.receipt-table {
  width: 100%;
  border-collapse: collapse;
  margin: 10px 0;
}

.receipt-table td {
  padding: 3px 5px;
  border-bottom: 1px dotted #ccc;
  vertical-align: top;
}

.receipt-table td:first-child {
  font-weight: bold;
}

.signature-box {
  border: 1px solid #ddd;
  padding: 12px 8px;
  margin: 8px 3px;
  min-height: 50px;
}

.signature-line {
  border-bottom: 1px solid #666;
  height: 20px;
  margin: 4px 0;
}

.notice-section {
  margin-top: 15px;
  padding-top: 10px;
  border-top: 1px solid #ddd;
  text-align: center;
}

@media print {
  .receipt-container {
    border: none;
    box-shadow: none;
  }
  
  .modal, .modal-backdrop {
    display: none !important;
  }
  
  body {
    margin: 0;
    padding: 10px;
  }
  
  #printArea {
    display: block !important;
  }
}
</style>

<template>
  <div class="container-fluid py-4">
    <div class="row">
      <div class="col-12">
        <div class="d-flex justify-content-between align-items-center mb-4">
          <h2 class="page-title-bold">
            <font-awesome-icon :icon="['fas', 'coins']" class="me-2" />
            {{ $t('queries.initial_balance.title') }}
          </h2>
        </div>
        
        <div v-if="showSuccess" class="alert alert-success d-flex align-items-center">
          <font-awesome-icon :icon="['fas', 'check-circle']" class="me-2" size="lg" />
          <div class="flex-grow-1">
          {{ $t('queries.initial_balance.messages.save_success') }}
            <div v-if="transactionRecords.length > 0" class="mt-2">
              <small class="text-muted">
                {{ $t('queries.initial_balance.transaction_records_generated', { count: transactionRecords.length }) }}
              </small>
              <button 
                class="btn btn-sm btn-outline-primary ms-2" 
                @click="openPrintModal"
              >
                <font-awesome-icon :icon="['fas', 'print']" class="me-1" />
                {{ $t('queries.common.print') }}
              </button>
            </div>
          </div>
        </div>

        <div v-if="showError" class="alert alert-danger d-flex align-items-center">
          <font-awesome-icon :icon="['fas', 'exclamation-circle']" class="me-2" size="lg" />
          {{ errorMessage }}
        </div>
        
        <div class="row">
          <div class="col-md-8">
            <div class="card mb-4">
              <div class="card-header">
                <h5 class="mb-0">{{ $t('queries.initial_balance.currency_balance_setting') }}</h5>
              </div>
              <div class="card-body">
                <div v-if="loading" class="text-center py-4">
                  <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                  </div>
                </div>
                <form v-else @submit.prevent="saveBalances">
                  <!-- 批量操作区域 -->
                  <div class="d-flex justify-content-between align-items-center mb-3">
                    <div>
                      <button type="button" class="btn btn-sm btn-outline-primary me-2" @click="selectAllPending">
                        <font-awesome-icon :icon="['fas', 'check-square']" class="me-1" />
                        {{ $t('queries.initial_balance.select_all_pending') }}
                      </button>
                      <button type="button" class="btn btn-sm btn-outline-secondary me-2" @click="clearSelection">
                        <font-awesome-icon :icon="['fas', 'square']" class="me-1" />
                        {{ $t('queries.initial_balance.clear_selection') }}
                      </button>
                      <button type="button" class="btn btn-sm btn-outline-warning me-2" @click="setSelectedToZero">
                                    <font-awesome-icon :icon="['fas', 'times']" class="me-1" />
            {{ $t('queries.initial_balance.set_to_zero') }}
                      </button>
                    </div>
                    <div class="text-muted small">
                      {{ $t('queries.initial_balance.selected_count', { count: selectedCurrencies.size, total: pendingCurrencies.length }) }}
                    </div>
                  </div>
                  
                  <table class="table table-striped table-bordered table-hover table-sm">
                    <thead>
                      <tr>
                        <th style="width: 5%">{{ $t('queries.initial_balance.table.select') }}</th>
                        <th style="width: 20%">{{ $t('queries.initial_balance.table.currency') }}</th>
                        <th style="width: 15%">{{ $t('queries.initial_balance.table.status') }}</th>
                        <th style="width: 25%">{{ $t('queries.initial_balance.table.initial_balance') }}</th>
                        <th style="width: 35%">{{ $t('queries.initial_balance.table.last_modified') }}</th>
                      </tr>
                    </thead>
                    <tbody>
                      <!-- 本币部分 -->
                      <tr v-for="currency in baseCurrencies" :key="currency.currency_id" 
                          :class="['table-info', { 'table-secondary': currency.has_initial }]">
                        <td class="py-1 text-center">
                          <input 
                            type="checkbox" 
                            class="form-check-input"
                            :checked="isSelectedForInitial(currency.currency_id)"
                            :disabled="currency.has_initial"
                            @change="toggleCurrencySelection(currency.currency_id, $event)"
                          />
                        </td>
                        <td class="py-1">
                          <div class="d-flex align-items-center">
                            <CurrencyFlag :code="currency.currency_code" :custom-filename="currency.custom_flag_filename" class="me-2" />
                            <span>{{ currency.currency_code }}</span>
                            <small class="text-muted ms-1">{{ getCurrencyDisplayName(currency) }}</small>
                            <span class="badge bg-primary ms-2">{{ $t('queries.initial_balance.table.base_currency') }}</span>
                          </div>
                        </td>
                        <td class="py-1">
                          <span v-if="currency.has_initial" class="badge bg-success">{{ $t('queries.initial_balance.table.initialized') }}</span>
                          <span v-else class="badge bg-warning">{{ $t('queries.initial_balance.table.pending') }}</span>
                        </td>
                        <td class="py-1">
                          <input
                            type="number"
                            class="form-control form-control-sm"
                            step="0.01"
                            :value="getDisplayBalance(currency)"
                            :disabled="currency.has_initial"
                            :readonly="currency.has_initial"
                            @input="handleBalanceChange(currency.currency_id, $event)"
                          />
                          <small v-if="currency.has_initial" class="text-muted">{{ $t('queries.initial_balance.table.cannot_modify') }}</small>
                        </td>
                        <td class="py-1">
                          <div v-if="currency.last_initial_time" class="text-muted small last-modified-info">
                            {{ formatDateTime(currency.last_initial_time) }} {{ currency.last_initial_operator || $t('queries.initial_balance.table.unknown_operator') }}
                          </div>
                          <div v-else class="text-muted small last-modified-info">
                            {{ $t('queries.initial_balance.table.no_modification_record') }}
                          </div>
                        </td>
                      </tr>
                      <!-- 外币部分 -->
                      <tr v-for="currency in foreignCurrencies" :key="currency.currency_id"
                          :class="{ 'table-secondary': currency.has_initial }">
                        <td class="py-1 text-center">
                          <input 
                            type="checkbox" 
                            class="form-check-input"
                            :checked="isSelectedForInitial(currency.currency_id)"
                            :disabled="currency.has_initial"
                            @change="toggleCurrencySelection(currency.currency_id, $event)"
                          />
                        </td>
                        <td class="py-1">
                          <div class="d-flex align-items-center">
                            <CurrencyFlag :code="currency.currency_code" :custom-filename="currency.custom_flag_filename" class="me-2" />
                            <span>{{ currency.currency_code }}</span>
                            <small class="text-muted ms-1">{{ getCurrencyDisplayName(currency) }}</small>
                          </div>
                        </td>
                        <td class="py-1">
                          <span v-if="currency.has_initial" class="badge bg-success">{{ $t('queries.initial_balance.table.initialized') }}</span>
                          <span v-else class="badge bg-warning">{{ $t('queries.initial_balance.table.pending') }}</span>
                        </td>
                        <td class="py-1">
                          <input
                            type="number"
                            class="form-control form-control-sm"
                            step="0.01"
                            :value="getDisplayBalance(currency)"
                            :disabled="currency.has_initial"
                            :readonly="currency.has_initial"
                            @input="handleBalanceChange(currency.currency_id, $event)"
                          />
                          <small v-if="currency.has_initial" class="text-muted">{{ $t('queries.initial_balance.table.cannot_modify') }}</small>
                        </td>
                        <td class="py-1">
                          <div v-if="currency.last_initial_time" class="text-muted small last-modified-info">
                            {{ formatDateTime(currency.last_initial_time) }} {{ currency.last_initial_operator || $t('queries.initial_balance.table.unknown_operator') }}
                          </div>
                          <div v-else class="text-muted small last-modified-info">
                            {{ $t('queries.initial_balance.table.no_modification_record') }}
                          </div>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                  
                  <div class="mt-4">
                    <button type="submit" class="btn btn-primary me-2" :disabled="saving || selectedCurrencies.size === 0">
                      <span v-if="saving" class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
                      {{ saving ? $t('queries.initial_balance.buttons.saving') : $t('queries.initial_balance.buttons.save_initial_setting') }}
                    </button>
                    <button type="button" class="btn btn-warning me-2" :disabled="settingZero || selectedCurrencies.size === 0" @click="confirmSetToZero">
                      <span v-if="settingZero" class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
                      <font-awesome-icon :icon="['fas', 'times']" class="me-1" />
                      {{ settingZero ? $t('queries.initial_balance.buttons.setting_zero') : $t('queries.initial_balance.buttons.batch_set_to_zero') }}
                    </button>
                    <button type="button" class="btn btn-secondary" @click="resetForm">{{ $t('queries.initial_balance.buttons.reset') }}</button>
                    <div v-if="selectedCurrencies.size === 0" class="text-muted small mt-2">
                      {{ $t('queries.initial_balance.buttons.please_select_currency') }}
                    </div>
                  </div>
                </form>
              </div>
            </div>
          </div>

          <div class="col-md-4">
            <div class="card">
              <div class="card-header">
                <h5 class="mb-0">{{ $t('queries.initial_balance.instructions_detail.title') }}</h5>
              </div>
              <div class="card-body">
                <p>{{ $t('queries.initial_balance.instructions_detail.description') }}</p>
                <p>{{ $t('queries.initial_balance.instructions_detail.steps.title') }}</p>
                <ol>
                  <li><strong>{{ $t('queries.initial_balance.instructions_detail.steps.step1') }}</strong></li>
                  <li><strong>{{ $t('queries.initial_balance.instructions_detail.steps.step2') }}</strong></li>
                  <li><strong>{{ $t('queries.initial_balance.instructions_detail.steps.step3') }}</strong>：
                    <ul>
                      <li>{{ $t('queries.initial_balance.instructions_detail.steps.step3_1') }}</li>
                      <li>{{ $t('queries.initial_balance.instructions_detail.steps.step3_2') }}</li>
                      <li>{{ $t('queries.initial_balance.instructions_detail.steps.step3_3') }}</li>
                    </ul>
                  </li>
                  <li><strong>{{ $t('queries.initial_balance.instructions_detail.steps.step4') }}</strong></li>
                </ol>
                <div class="alert alert-info">
                  <strong>{{ $t('queries.initial_balance.status_description.title') }}</strong>
                  <br>• <span class="badge bg-success">{{ $t('queries.initial_balance.table.initialized') }}</span>：{{ $t('queries.initial_balance.status_description.initialized_desc') }}
                  <br>• <span class="badge bg-warning">{{ $t('queries.initial_balance.table.pending') }}</span>：{{ $t('queries.initial_balance.status_description.pending_desc') }}
                </div>
                <div class="alert alert-warning">
                  <strong>{{ $t('queries.initial_balance.important_reminder.title') }}</strong>
                  <br>• {{ $t('queries.initial_balance.important_reminder.note1') }}
                  <br>• {{ $t('queries.initial_balance.important_reminder.note2') }}
                  <br>• {{ $t('queries.initial_balance.important_reminder.note3') }}
                  <router-link to="/data-clear" class="text-decoration-none fw-bold text-danger">
                    "{{ $t('queries.initial_balance.important_reminder.clear_business_data') }}"
                  </router-link>
                </div>
                <div class="alert alert-success">
                  <strong>{{ $t('queries.initial_balance.set_zero_function.title') }}</strong>
                  <br>• <span class="badge bg-warning">{{ $t('queries.initial_balance.set_to_zero') }}</span>：{{ $t('queries.initial_balance.set_zero_function.set_to_zero_desc') }}
                  <br>• <span class="badge bg-warning">{{ $t('queries.initial_balance.buttons.batch_set_to_zero') }}</span>：{{ $t('queries.initial_balance.set_zero_function.batch_set_to_zero_desc') }}
                  <br>• {{ $t('queries.initial_balance.set_zero_function.note1') }}
                  <br>• {{ $t('queries.initial_balance.set_zero_function.note2') }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- 打印单据模态框 -->
  <div class="modal fade" id="printModal" tabindex="-1" ref="printModal">
    <div class="modal-dialog modal-lg">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">
            <font-awesome-icon :icon="['fas', 'print']" class="me-2" />
            打印期初余额单据
          </h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
          <div class="alert alert-info">
            <strong>操作说明：</strong>
            <br>1. 推荐使用"批量打印全部"生成一个汇总PDF文件，包含所有币种信息
            <br>2. 也可以点击"生成PDF"按钮为单个币种创建独立的PDF单据文件
            <br>3. 点击"预览"按钮在浏览器中查看PDF内容
            <br>4. 点击"下载"按钮将PDF文件保存到本地
          </div>
          
          <div class="table-responsive">
            <table class="table table-striped">
              <thead>
                <tr>
                  <th>币种</th>
                  <th>单据号</th>
                  <th>调整前余额</th>
                  <th>调整后余额</th>
                  <th>调整金额</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="record in transactionRecords" :key="record.transaction_no">
                  <td>{{ record.currency_code }}</td>
                  <td>
                    <code class="text-primary">{{ record.transaction_no }}</code>
                  </td>
                  <td>{{ formatAmount(record.old_balance) }}</td>
                  <td>{{ formatAmount(record.new_balance) }}</td>
                  <td :class="record.change >= 0 ? 'text-success' : 'text-danger'">
                    {{ record.change >= 0 ? '+' : '' }}{{ formatAmount(record.change) }}
                  </td>
                  <td>
                    <button 
                      class="btn btn-sm btn-primary me-1" 
                      @click="printTransactionReceipt(record)"
                      :disabled="printingTransactions.has(record.transaction_no)"
                    >
                      <span v-if="printingTransactions.has(record.transaction_no)">
                        <span class="spinner-border spinner-border-sm me-1"></span>
                        打印中...
                      </span>
                      <span v-else>
                        <font-awesome-icon :icon="['fas', 'print']" class="me-1" />
                        生成PDF
                      </span>
                    </button>
                    <button 
                      class="btn btn-sm btn-outline-primary" 
                      @click="downloadReceipt(record.transaction_no)"
                      title="下载PDF文件"
                    >
                      <font-awesome-icon :icon="['fas', 'download']" class="me-1" />
                      下载
                    </button>
                    <button 
                      class="btn btn-sm btn-outline-info ms-1" 
                      @click="previewPdf(record.transaction_no)"
                      title="预览PDF文件"
                    >
                      <font-awesome-icon :icon="['fas', 'eye']" class="me-1" />
                      预览
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div class="modal-footer">
          <button 
            type="button" 
            class="btn btn-secondary" 
            data-bs-dismiss="modal"
          >
            关闭
          </button>
          <button 
            type="button" 
            class="btn btn-primary" 
            @click="printAllReceipts"
            :disabled="printingAll || transactionRecords.length === 0"
          >
            <span v-if="printingAll">
              <span class="spinner-border spinner-border-sm me-1"></span>
              批量打印中...
            </span>
            <span v-else>
              <font-awesome-icon :icon="['fas', 'print']" class="me-1" />
              批量打印全部
            </span>
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- PDF预览模态框 -->
  <div class="modal fade" id="pdfPreviewModal" tabindex="-1" ref="pdfPreviewModal">
    <div class="modal-dialog modal-xl">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">
            <font-awesome-icon :icon="['fas', 'file-alt']" class="me-2" />
            PDF预览
          </h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body p-0">
          <div v-if="previewLoading" class="text-center py-5">
            <div class="spinner-border text-primary" role="status"></div>
            <p class="mt-2">正在加载PDF预览...</p>
          </div>
          <iframe 
            v-else-if="pdfPreviewUrl" 
            :src="pdfPreviewUrl" 
            width="100%" 
            height="600"
            style="border: none;"
          ></iframe>
          <div v-else class="text-center py-5">
            <p class="text-muted">PDF预览不可用</p>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
            关闭
          </button>
          <button 
            type="button" 
            class="btn btn-primary" 
            @click="downloadCurrentPdf"
            :disabled="!pdfPreviewUrl"
          >
            <font-awesome-icon :icon="['fas', 'download']" class="me-1" />
            下载PDF
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- 期初余额设置成功模态框 - 仿照兑换交易样式 -->
  <div class="modal fade show" 
       v-if="showSuccessModal" 
       tabindex="-1" 
       style="display: block; background: rgba(0,0,0,0.5)"
       @click.self="closeSuccessModal">
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content">
        <div class="modal-header bg-success text-white">
          <h5 class="modal-title">{{ $t('queries.initial_balance.messages.transaction_success') }}</h5>
          <button type="button" class="btn-close btn-close-white" @click="closeSuccessModal"></button>
        </div>
        <div class="modal-body">
          <!-- 紧凑的成功信息显示 -->
          <div class="alert alert-success">
            <div class="d-flex align-items-center">
              <font-awesome-icon :icon="['fas', 'check-circle']" class="me-2 text-success" size="lg" />
              <div>
                <h6 class="mb-1">{{ $t('queries.initial_balance.messages.balance_set_success') }}</h6>
                <small class="text-muted">{{ $t('queries.initial_balance.messages.currencies_updated', { count: transactionRecords.length }) }}</small>
              </div>
            </div>
          </div>
          
          <!-- 紧凑的汇总信息 -->
          <div class="card">
            <div class="card-body p-3">
              <h6 class="card-title mb-2">{{ $t('queries.initial_balance.messages.operation_summary') }}</h6>
              <div class="row g-2 text-sm">
                <div class="col-4">
                  <strong>{{ $t('queries.initial_balance.messages.setting_time') }}:</strong><br>
                  <small>{{ formatDateTime(new Date()) }}</small>
                </div>
                <div class="col-4">
                  <strong>{{ $t('queries.initial_balance.messages.operator') }}:</strong><br>
                  <small>{{ operatorName }}</small>
                </div>
                <div class="col-4">
                  <strong>{{ $t('queries.initial_balance.messages.currency_count') }}:</strong><br>
                  <small>{{ transactionRecords.length }} {{ $t('queries.initial_balance.table.currency') }}</small>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 紧凑的币种列表 -->
          <div class="mt-3">
            <h6 class="mb-2">{{ $t('queries.initial_balance.messages.updated_currencies') }}:</h6>
            <div class="compact-currency-list">
              <div v-for="record in allCurrencySummary.slice(0, 6)" :key="record.currency_code" 
                   class="currency-item d-flex justify-content-between align-items-center py-1 px-2 border-bottom">
                <span class="fw-bold">{{ record.currency_code }}</span>
                <span class="text-muted small">{{ formatAmount(record.old_balance) }} → {{ formatAmount(record.new_balance) }}</span>
                <span :class="record.change >= 0 ? 'text-success' : 'text-danger'" class="small">
                  {{ record.change >= 0 ? '+' : '' }}{{ formatAmount(record.change) }}
                </span>
              </div>
              <div v-if="allCurrencySummary.length > 6" class="text-center py-2 text-muted small">
                {{ $t('queries.initial_balance.messages.more_currencies', { count: allCurrencySummary.length - 6 }) }}
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeSuccessModal">{{ $t('queries.initial_balance.messages.close') }}</button>
          <button class="btn btn-primary" @click="printAllReceipts">
            <font-awesome-icon :icon="['fas', 'print']" class="me-1" />
            {{ $t('queries.initial_balance.messages.print_voucher') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { formatDateTime } from '@/utils/formatters'
import api from '@/services/api'
import CurrencyFlag from '@/components/CurrencyFlag.vue';
import { Modal } from 'bootstrap'
import printService, { PrintService } from '@/services/printService'

export default {
  name: 'InitialBalanceView',
  components: {
    CurrencyFlag
  },
  data() {
    return {
      availableCurrencies: [],
      editedBalances: {},
      selectedCurrencies: new Set(), // 用户选择要期初的币种ID
      showSuccess: false,
      showError: false,
      errorMessage: '',
      loading: true,
      saving: false,
      settingZero: false,
      branchId: null,
      transactionRecords: [],
      showPrintModal: false,
      printingTransactions: new Set(),  // 用于跟踪正在打印的交易
      printingAll: false,  // 用于跟踪批量打印状态
      previewLoading: false,
      pdfPreviewUrl: null,
      currentTransactionNo: null,
      showSuccessModal: false,
      branchName: '',
      operatorName: ''
    };
  },
  computed: {
    baseCurrencies() {
      return this.availableCurrencies.filter(c => c.is_base);
    },
    foreignCurrencies() {
      return this.availableCurrencies.filter(c => !c.is_base);
    },
    pendingCurrencies() {
      return this.availableCurrencies.filter(c => !c.has_initial);
    },
    // 新增：所有币种的汇总单据显示数据
    allCurrencySummary() {
      return this.availableCurrencies.map((currency, index) => {
        // 查找是否有对应的交易记录
        const transactionRecord = this.transactionRecords.find(
          record => record.currency_code === currency.currency_code
        );
        
        if (transactionRecord) {
          // 有交易记录，使用实际数据
          return {
            sequence: index + 1,
            currency_code: currency.currency_code,
            old_balance: transactionRecord.old_balance,
            new_balance: transactionRecord.new_balance,
            change: transactionRecord.change,
            transaction_no: transactionRecord.transaction_no
          };
        } else {
          // 没有交易记录，显示当前余额，调整金额为0
          return {
            sequence: index + 1,
            currency_code: currency.currency_code,
            old_balance: currency.current_balance,
            new_balance: currency.current_balance,
            change: 0,
            transaction_no: '-'
          };
        }
      });
    }
  },
  async created() {
    try {
      const userStr = localStorage.getItem('user');
      const userPermissions = JSON.parse(localStorage.getItem('userPermissions') || '[]');
      const userData = userStr ? JSON.parse(userStr) : {};
      
      // 初始化用户和网点信息
      this.branchName = userData.branch_name || '未知网点';
              this.operatorName = userData.name || userData.username || this.$t('common.unknown_operator');
      
      // 如果是管理员或有余额管理权限则允许访问
      if (!userPermissions.includes('balance_manage') && userData.role !== 'admin') {
        this.showError = true;
        this.errorMessage = '您没有余额管理权限';
        return;
      }

      if (userStr) {
        this.branchId = userData.branch_id;
      }
      
      if (!this.branchId) {
        this.showError = true;
        this.errorMessage = '未找到网点信息，请重新登录';
        return;
      }
      
      await this.loadAvailableCurrencies();
    } catch (error) {
      console.error('Error in created hook:', error);
      this.showError = true;
      this.errorMessage = '初始化失败：' + (error.message || '未知错误');
    }
  },
  mounted() {
    // 监听PDF预览模态框关闭事件将在预览时添加
  },
  methods: {
    getCurrencyDisplayName(currency) {
      // 检查是否是自定义币种（有custom_flag_filename）
      if (currency.custom_flag_filename) {
        // console.log(`[自定义币种] ${currency.currency_code} 使用数据库名称: ${currency.currency_name}`);
        return currency.currency_name || currency.currency_code;
      }
      
      // 预设币种使用翻译
      return this.$t(`currencies.${currency.currency_code}`) || currency.currency_code;
    },
    async loadAvailableCurrencies() {
      try {
        this.loading = true;
        // 获取币种期初状态（新的API）
        const response = await api.get('balance-management/initial/currencies-status');
        console.log('Currencies initial status response:', response.data);

        if (!response.data) {
          throw new Error('服务器返回数据格式错误');
        }

        if (response.data.success) {
          if (!Array.isArray(response.data.data)) {
            throw new Error('币种数据格式错误');
          }
          
          // 使用新的API数据，包含期初状态信息
          this.availableCurrencies = response.data.data.map(currency => ({
            ...currency,
            // 移除硬编码：后端API已经正确返回is_base字段，表示是否为本币
            last_initial_time: currency.initial_date,
            last_initial_operator: currency.initial_operator
          }));
          
          console.log('Currencies loaded with initial status:', this.availableCurrencies);
          console.log('Summary:', response.data.summary);
          
          // 显示状态信息
          if (response.data.summary) {
            const { total_currencies, initialized_count, pending_count } = response.data.summary;
            console.log(`币种状态: 总数 ${total_currencies}, 已期初 ${initialized_count}, 待期初 ${pending_count}`);
          }
          
        } else {
          throw new Error(response.data.message || '获取币种期初状态失败');
        }
      } catch (error) {
        console.error('Failed to load currencies initial status:', error);
        this.showError = true;
        if (error.response) {
          // 服务器响应错误
          console.error('Server error response:', error.response.data);
          this.errorMessage = error.response.data.message || '服务器返回错误';
        } else if (error.request) {
          // 请求发送失败
          console.error('Request failed:', error.request);
          this.errorMessage = '网络请求失败，请检查网络连接';
        } else {
          // 其他错误
          console.error('Error:', error.message);
          this.errorMessage = error.message || '获取币种期初状态时发生错误';
        }
      } finally {
        this.loading = false;
      }
    },
    getDisplayBalance(currency) {
      if (currency.has_initial) {
        // 已期初的币种：显示期初金额，不允许编辑
        return currency.initial_amount || 0;
      } else {
        // 未期初的币种：显示用户编辑的值或当前余额
        return this.getEditedBalance(currency.currency_id, currency.current_balance);
      }
    },
    getEditedBalance(currencyId, originalAmount) {
      return this.editedBalances[currencyId] !== undefined ? this.editedBalances[currencyId] : originalAmount;
    },
    handleBalanceChange(currencyId, event) {
      const value = event.target.value;
      const numValue = parseFloat(value);
      if (isNaN(numValue)) return;
      
      this.editedBalances = {
        ...this.editedBalances,
        [currencyId]: numValue
      };
    },
    async saveBalances() {
      this.saving = true;
      this.showError = false;
      
      try {
        if (!this.branchId) {
          throw new Error('未找到网点信息');
        }

        console.log('Preparing initial balances for branch:', this.branchId);
        console.log('Selected currencies:', Array.from(this.selectedCurrencies));
        
        // 只处理用户选择的币种
        const initialBalances = [];
        for (const currencyId of this.selectedCurrencies) {
          const currency = this.availableCurrencies.find(c => c.currency_id === currencyId);
          if (!currency) continue;
          
          // 检查是否已期初
          if (currency.has_initial) {
            console.log(`跳过已期初币种: ${currency.currency_code}`);
            continue;
          }
          
          // 获取用户输入的余额
          const amount = this.getEditedBalance(currencyId, currency.current_balance);
          if (amount !== undefined && amount !== null) {
            initialBalances.push({
              currency_id: parseInt(currencyId),
              balance: parseFloat(amount)
            });
          }
        }
        
        console.log('Initial balances data:', initialBalances);

        if (initialBalances.length === 0) {
          throw new Error('没有选择任何币种进行期初设置，或所选币种已经期初过');
        }

        // 发送期初设置请求
        const response = await api.post('balance-management/initial', {
          branch_id: this.branchId,
          balances: initialBalances
        });

        if (response.data.success) {
          // 保存交易记录信息，用于后续打印单据
          this.transactionRecords = response.data.transaction_records || [];
          
          // 显示成功和跳过的币种信息
          console.log('期初设置成功:', response.data.message);
          if (response.data.skipped_currencies && response.data.skipped_currencies.length > 0) {
            console.log('跳过的币种:', response.data.skipped_currencies);
          }
          
          // 清空选择和编辑状态
          this.editedBalances = {};
          this.selectedCurrencies.clear();
          
          // 显示成功模态框而不是alert
          this.showSuccessModal = true;
          
          // 重新加载最新数据
          await this.loadAvailableCurrencies();
        } else {
          throw new Error(response.data.message || '期初设置失败');
        }
      } catch (error) {
        console.error('Failed to save balances:', error);
        this.showError = true;
        this.errorMessage = error.response?.data?.message || error.message || '保存余额时发生错误';
      } finally {
        this.saving = false;
      }
    },
    resetForm() {
      this.editedBalances = {};
      this.selectedCurrencies.clear();
      this.showError = false;
    },
    formatDateTime,
    
    // 新增：币种选择相关方法
    isSelectedForInitial(currencyId) {
      return this.selectedCurrencies.has(currencyId);
    },
    
    toggleCurrencySelection(currencyId, event) {
      if (event.target.checked) {
        this.selectedCurrencies.add(currencyId);
      } else {
        this.selectedCurrencies.delete(currencyId);
      }
    },
    
    selectAllPending() {
      // 选择所有待期初的币种
      this.pendingCurrencies.forEach(currency => {
        this.selectedCurrencies.add(currency.currency_id);
      });
    },
    
    clearSelection() {
      // 清空所有选择
      this.selectedCurrencies.clear();
    },
    
    setSelectedToZero() {
      // 直接设置选中币种的输入框为0（不保存）
      this.selectedCurrencies.forEach(currencyId => {
        this.editedBalances[currencyId] = 0;
      });
    },
    
    async confirmSetToZero() {
      // 确认对话框
      const selectedCount = this.selectedCurrencies.size;
      const selectedNames = [];
      
      // 获取选中币种的名称
      this.availableCurrencies.forEach(currency => {
        if (this.selectedCurrencies.has(currency.currency_id)) {
          selectedNames.push(currency.currency_code);
        }
      });
      
      const confirmed = confirm(
        `确认要将以下 ${selectedCount} 个币种的余额设置为0吗？\n\n` +
        `币种: ${selectedNames.join(', ')}\n\n` +
        `注意：此操作会直接保存到数据库，但不会标记为已期初状态。`
      );
      
      if (confirmed) {
        await this.batchSetToZero();
      }
    },
    
    async batchSetToZero() {
      // 批量设置为0并保存到数据库
      try {
        this.settingZero = true;
        
        // 准备要设置为0的币种数据
        const currenciesToSet = [];
        this.selectedCurrencies.forEach(currencyId => {
          const currency = this.availableCurrencies.find(c => c.currency_id === currencyId);
          if (currency && !currency.has_initial) {
            currenciesToSet.push({
              currency_id: currencyId,
              currency_code: currency.currency_code,
              balance: 0
            });
          }
        });
        
        if (currenciesToSet.length === 0) {
          throw new Error('没有可设置的币种');
        }
        
        // 调用API设置为0
        const response = await api.post('balance-management/set-to-zero', {
          branch_id: this.branchId,
          currencies: currenciesToSet
        });
        
        if (response.data.success) {
          // 成功后重新加载数据
          await this.loadAvailableCurrencies();
          this.clearSelection();
          this.editedBalances = {};
          
          // 显示成功消息
          if (this.$toast) {
            this.$toast.success(`成功将 ${currenciesToSet.length} 个币种的余额设置为0`);
          } else {
            alert(`成功将 ${currenciesToSet.length} 个币种的余额设置为0`);
          }
        } else {
          throw new Error(response.data.message || '设置失败');
        }
        
      } catch (error) {
        console.error('批量设置为0失败:', error);
        const errorMsg = error.response?.data?.message || error.message || '设置失败';
        
        if (this.$toast) {
          this.$toast.error(errorMsg);
        } else {
          alert('设置失败: ' + errorMsg);
        }
      } finally {
        this.settingZero = false;
      }
    },
    
    // 新增：打印单据相关方法
    formatAmount(amount) {
      if (amount == null || amount == undefined) return '0.00';
      return new Intl.NumberFormat('zh-CN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(amount);
    },
    
    async printTransactionReceipt(record) {
      try {
        this.printingTransactions.add(record.transaction_no);
        
        // 需要先获取交易的ID
        const transactionId = await this.getTransactionId(record.transaction_no);
        if (!transactionId) {
          throw new Error('无法找到交易记录ID');
        }
        
        console.log(`开始打印期初余额单据: ${record.transaction_no}, 交易ID: ${transactionId}`);
        
        // 使用统一打印服务
        const config = PrintService.getInitialBalanceConfig(transactionId, record.transaction_no, this.$toast);
        const success = await printService.printPDF(config);
        
        if (success) {
          console.log(`期初余额单据 ${record.transaction_no} 打印完成`);
        }
      } catch (error) {
        console.error('打印单据失败:', error);
        const errorMsg = error.message || '打印单据失败';
        const fullErrorMsg = `打印单据 ${record.transaction_no} 失败: ${errorMsg}`;
        
        if (this.$toast) {
          this.$toast.error(fullErrorMsg);
        } else {
          alert(fullErrorMsg);
        }
      } finally {
        this.printingTransactions.delete(record.transaction_no);
      }
    },
    
    async printAllReceipts() {
      try {
        this.printingAll = true;
        
        console.log('开始生成期初余额汇总PDF文件...');
        
        // 获取当前语言设置
        const currentLanguage = this.$i18n.locale || 'zh-CN';
        const languageCode = currentLanguage.split('-')[0]; // 从 'zh-CN' 提取 'zh'
        
        // 添加调试信息
        console.log('当前i18n语言设置:', this.$i18n.locale);
        console.log('localStorage中的语言设置:', localStorage.getItem('language'));
        console.log('提取的语言代码:', languageCode);
        
        // 使用统一打印服务的汇总打印方法
        const config = PrintService.getInitialBalanceSummaryConfig(this.allCurrencySummary, this.$toast, languageCode);
        const success = await printService.printSummaryPDF(config);
        
        if (success) {
          console.log('期初余额汇总打印完成');
        }
        
      } catch (error) {
        console.error('生成汇总PDF失败:', error);
        
        const errorMsg = error.message || '生成汇总PDF失败';
        if (this.$toast) {
          this.$toast.error(errorMsg);
        } else {
          alert(errorMsg);
        }
      } finally {
        this.printingAll = false;
      }
    },
    
    async getTransactionId(transactionNo) {
      try {
        // 这里需要调用API来根据交易号获取交易ID
        // 暂时使用一个简单的实现，实际项目中可能需要专门的API
        const response = await api.get(`balance-management/transactions/by-no/${transactionNo}`);
        if (response.data.success && response.data.transaction) {
          return response.data.transaction.id;
        }
        return null;
      } catch (error) {
        console.error('获取交易ID失败:', error);
        return null;
      }
    },
    openPrintModal() {
      // 使用Bootstrap的模态框API
      const modal = new Modal(this.$refs.printModal);
      modal.show();
    },
    async downloadReceipt(transactionNo) {
      try {
        console.log(`开始下载单据: ${transactionNo}`);
        
        // 构建下载URL
        const downloadUrl = `/api/balance-management/initial/transactions/${transactionNo}/download-receipt`;
        
        // 获取认证token
        const token = localStorage.getItem('token');
        if (!token) {
          throw new Error('未找到认证信息，请重新登录');
        }
        
        // 创建一个临时的a标签来触发下载
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = `initial_balance_receipt_${transactionNo}.pdf`;
        
        // 添加认证头 - 对于下载链接，我们需要使用window.open或fetch
        const response = await fetch(downloadUrl, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.message || '下载失败');
        }
        
        // 获取文件blob
        const blob = await response.blob();
        
        // 创建blob URL并触发下载
        const blobUrl = window.URL.createObjectURL(blob);
        link.href = blobUrl;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // 清理blob URL
        window.URL.revokeObjectURL(blobUrl);
        
        console.log(`单据 ${transactionNo} 下载成功`);
        
      } catch (error) {
        console.error('下载单据失败:', error);
        const errorMsg = error.message || '下载单据失败';
        if (this.$toast) {
          this.$toast.error(errorMsg);
        } else {
          alert(errorMsg);
        }
      }
    },
    async previewPdf(transactionNo) {
      try {
        this.previewLoading = true;
        
        console.log(`开始预览PDF: ${transactionNo}`);
        
        // 构建预览URL，通过下载API获取文件，但作为预览显示
        const downloadUrl = `/api/balance-management/initial/transactions/${transactionNo}/download-receipt`;
        
        // 获取认证token
        const token = localStorage.getItem('token');
        if (!token) {
          throw new Error('未找到认证信息，请重新登录');
        }
        
        // 首先检查文件是否存在
        const response = await fetch(downloadUrl, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (!response.ok) {
          throw new Error('PDF文件不存在或尚未生成，请先点击"生成PDF"按钮');
        }
        
        // 获取文件blob并创建URL
        const blob = await response.blob();
        const blobUrl = window.URL.createObjectURL(blob);
        
        // 设置预览URL
        this.pdfPreviewUrl = blobUrl;
        this.currentTransactionNo = transactionNo;
        
        // 打开预览模态框
        const previewModal = new Modal(this.$refs.pdfPreviewModal);
        previewModal.show();
        
        console.log(`PDF预览已准备就绪: ${transactionNo}`);
        
      } catch (error) {
        console.error('获取PDF预览失败:', error);
        const errorMsg = error.message || '获取PDF预览失败';
        if (this.$toast) {
          this.$toast.error(errorMsg);
        } else {
          alert(errorMsg);
        }
      } finally {
        this.previewLoading = false;
      }
    },
    async downloadCurrentPdf() {
      if (this.currentTransactionNo) {
        await this.downloadReceipt(this.currentTransactionNo);
      }
    },
    
    // 清理PDF预览资源
    cleanupPdfPreview() {
      if (this.pdfPreviewUrl && this.pdfPreviewUrl.startsWith('blob:')) {
        window.URL.revokeObjectURL(this.pdfPreviewUrl);
      }
      this.pdfPreviewUrl = null;
      this.currentTransactionNo = null;
    },
    closeSuccessModal() {
      this.showSuccessModal = false;
    }
  },
  
  // 组件销毁时清理资源
  beforeUnmount() {
    this.cleanupPdfPreview();
  }
};
</script>

<style scoped>
.container {
  padding: 20px;
}

.alert {
  margin-bottom: 20px;
}

.table {
  margin-bottom: 1rem;
}

.table th,
.table td {
  padding: 0.15rem 0.5rem;
  vertical-align: middle;
}

.table-sm th,
.table-sm td {
  padding: 0.1rem 0.3rem;
}

.py-1 {
  padding-top: 0.1rem !important;
  padding-bottom: 0.1rem !important;
}

.form-control-sm {
  height: calc(1.5em + 0.5rem + 2px);
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
}

.currency-flag {
  width: 1.25rem;
  height: 0.9375rem;
}

.badge {
  padding: 0.25em 0.5em;
  font-size: 0.75rem;
  font-weight: normal;
}

.card-body {
  padding: 1rem;
}

.card-header {
  padding: 0.75rem 1rem;
}

.alert {
  padding: 0.75rem 1rem;
  margin-bottom: 1rem;
}

.mb-4 {
  margin-bottom: 1rem !important;
}

.mt-4 {
  margin-top: 1rem !important;
}

.btn {
  padding: 0.375rem 0.75rem;
}

.text-muted {
  font-size: 0.875rem;
}

.last-modified-info {
  color: #adb5bd !important;
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
  padding: 10px 5px;
  margin: 5px 2px;
  min-height: 40px;
}

.signature-line {
  border-bottom: 1px solid #666;
  height: 20px;
  margin: 3px 0;
}

.notice-section {
  margin-top: 15px;
  padding-top: 10px;
  border-top: 1px solid #ddd;
  text-align: center;
}

@media print {
  /* 隐藏非打印元素 */
  body > *:not(.modal) {
    display: none !important;
  }
  
  .modal-backdrop,
  .modal-header,
  .modal-footer {
    display: none !important;
  }
  
  .modal {
    display: block !important;
    position: static !important;
    padding: 0 !important;
    background: none !important;
  }
  
  .modal-dialog,
  .modal-content,
  .modal-body {
    display: block !important;
    position: static !important;
    padding: 0 !important;
    margin: 0 !important;
    box-shadow: none !important;
    border: none !important;
    background: white !important;
  }
  
  /* 打印区域样式 */
  #printArea {
    display: block !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 10mm !important;
  }
  
  .receipt-container {
    border: none !important;
    box-shadow: none !important;
    font-family: 'SimSun', serif !important;
    font-size: 12pt !important;
    line-height: 1.4 !important;
    color: black !important;
    background: white !important;
  }
  
  /* 表格样式 */
  .summary-info-table,
  .currency-table {
    border-collapse: collapse !important;
    width: 100% !important;
  }
  
  .summary-info-table td {
    border-bottom: 1px solid black !important;
    padding: 2pt 4pt !important;
  }
  
  .currency-table th,
  .currency-table td {
    border: 1px solid black !important;
    padding: 2pt 1pt !important;
    font-size: 10pt !important;
  }
  
  .currency-table th {
    background-color: #f0f0f0 !important;
    font-weight: bold !important;
  }
  
  /* 签名框样式 */
  .signature-box {
    border: 1px solid black !important;
    padding: 10pt !important;
    margin: 5pt !important;
    min-height: 30pt !important;
  }
  
  .signature-line {
    border-bottom: 1px solid black !important;
    height: 15pt !important;
    margin: 5pt 0 !important;
  }
  
  /* 页面设置 */
  @page {
    size: A4;
    margin: 10mm;
  }
}

/* 新增：期初余额汇总表样式 */
.summary-info-table {
  width: 100%;
  border-collapse: collapse;
}

.summary-info-table td {
  padding: 3px 8px;
  border-bottom: 1px dotted #ccc;
  vertical-align: top;
}

.summary-info-table td:first-child {
  font-weight: bold;
  width: 35%;
}

.currency-list {
  margin: 15px 0;
}

.currency-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
  margin-top: 10px;
}

.currency-table th,
.currency-table td {
  padding: 5px 3px;
  border: 1px solid #ccc;
  text-align: center;
  vertical-align: middle;
}

.currency-table th {
  background-color: #f5f5f5;
  font-weight: bold;
}

.currency-table .transaction-no {
  font-family: 'Courier New', monospace;
  font-size: 10px;
}

.signature-box {
  border: 1px solid #ddd;
  padding: 10px 5px;
  margin: 5px 2px;
  min-height: 40px;
}

.signature-line {
  border-bottom: 1px solid #666;
  height: 20px;
  margin: 3px 0;
}

.notice-section {
  margin-top: 15px;
  padding-top: 10px;
  border-top: 1px solid #ddd;
  text-align: center;
}

/* 紧凑的币种列表样式 */
.compact-currency-list {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.currency-item {
  transition: background-color 0.2s;
}

.currency-item:hover {
  background-color: #f8f9fa;
}

.currency-item:last-child {
  border-bottom: none !important;
}
</style>

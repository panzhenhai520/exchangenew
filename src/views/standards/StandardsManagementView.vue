<template>
  <div class="container-fluid standards-management-page">
    <div class="row">
      <div class="col-12">
        <div class="d-flex justify-content-between align-items-center mb-4" style="margin-top: 20px !important;">
          <h2 class="page-title-bold">
            <font-awesome-icon :icon="['fas', 'clipboard-list']" class="me-2" />
            {{ $t('standards.title') }}
          </h2>
        </div>
        <div class="card">
          <div class="card-body">
            <!-- 选项卡导航 -->
            <ul class="nav nav-tabs" id="standardsTab" role="tablist">
              <li class="nav-item" role="presentation">
                <button
                  class="nav-link"
                  :class="{ active: activeTab === 'purpose-limits' }"
                  @click="activeTab = 'purpose-limits'"
                  type="button"
                >
                  <font-awesome-icon :icon="['fas', 'exclamation-triangle']" class="me-1" />
                  {{ $t('standards.tabs.purpose_limits') }}
                </button>
              </li>
              <li class="nav-item" role="presentation">
                <button
                  class="nav-link"
                  :class="{ active: activeTab === 'receipt-files' }"
                  @click="activeTab = 'receipt-files'"
                  type="button"
                >
                  <font-awesome-icon :icon="['fas', 'file-alt']" class="me-1" />
                  {{ $t('standards.tabs.receipt_files') }}
                </button>
              </li>
              <li class="nav-item" role="presentation">
                <button
                  class="nav-link"
                  :class="{ active: activeTab === 'balance-alerts' }"
                  @click="activeTab = 'balance-alerts'"
                  type="button"
                >
                  <font-awesome-icon :icon="['fas', 'bell']" class="me-1" />
                  {{ $t('standards.tabs.balance_alerts') }}
                </button>
              </li>
              <li class="nav-item" role="presentation">
                <button
                  class="nav-link"
                  :class="{ active: activeTab === 'field-management' }"
                  @click="activeTab = 'field-management'"
                  type="button"
                >
                  <font-awesome-icon :icon="['fas', 'table']" class="me-1" />
                  {{ $t('standards.tabs.field_management') }}
                </button>
              </li>
              <li class="nav-item" role="presentation">
                <button
                  class="nav-link"
                  :class="{ active: activeTab === 'trigger-rules' }"
                  @click="activeTab = 'trigger-rules'"
                  type="button"
                >
                  <font-awesome-icon :icon="['fas', 'cogs']" class="me-1" />
                  {{ $t('standards.tabs.trigger_rules') }}
                </button>
              </li>
              <li class="nav-item" role="presentation">
                <button
                  class="nav-link"
                  :class="{ active: activeTab === 'test-trigger' }"
                  @click="activeTab = 'test-trigger'"
                  type="button"
                >
                  <font-awesome-icon :icon="['fas', 'flask']" class="me-1" />
                  {{ $t('standards.tabs.test_trigger') }}
                </button>
              </li>
            </ul>

            <!-- 选项卡内容 -->
            <div class="tab-content mt-3" id="standardsTabContent">
              
              <!-- Exchange Reminder Information Maintenance -->
              <div v-if="activeTab === 'purpose-limits'" class="tab-pane fade show active">
                <div class="d-flex justify-content-between align-items-center mb-3">
                  <h6 class="mb-0">{{ $t('standards.purpose_limits.title') }}</h6>
                  <button class="btn btn-primary btn-sm" @click="showAddPurposeLimitModal">
                    <font-awesome-icon :icon="['fas', 'plus']" class="me-1" />
                    {{ $t('standards.purpose_limits.add_button') }}
                  </button>
                </div>
                
                <div v-if="purposeLimitsLoading" class="text-center py-4">
                  <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">{{ $t('standards.purpose_limits.loading') }}</span>
                  </div>
                </div>
                
                <div v-else-if="purposeLimits.length === 0" class="text-center py-4 text-muted">
                  {{ $t('standards.purpose_limits.no_data') }}
                </div>
                
                <!-- 按用途分组的树型结构 -->
                <div v-else class="purpose-tree">
                  <div v-for="(group, purposeName) in groupedPurposeLimits" :key="purposeName" class="purpose-group mb-3">
                    <!-- 用途标题行 -->
                    <div class="purpose-header card">
                      <div class="card-header py-2" @click="togglePurposeGroup(purposeName)" style="cursor: pointer;">
                        <div class="d-flex justify-content-between align-items-center">
                          <div class="d-flex align-items-center">
                            <font-awesome-icon 
                              :icon="['fas', expandedGroups[purposeName] ? 'chevron-down' : 'chevron-right']" 
                              class="me-2 text-muted"
                            />
                            <h6 class="mb-0 text-primary">
                              <font-awesome-icon :icon="['fas', 'tag']" class="me-2" />
                              {{ purposeName }}
                            </h6>
                            <span class="badge bg-secondary ms-2">{{ group.length }}{{ $t('standards.purpose_limits.currency_types') }}</span>
                          </div>
                          <div class="purpose-summary text-muted small">
                            {{ $t('standards.purpose_limits.expand_hint') }}
                          </div>
                        </div>
                      </div>
                      
                      <!-- 用途下的币种列表 -->
                      <div v-show="expandedGroups[purposeName]" class="card-body p-0">
                <div class="table-responsive">
                          <table class="table table-sm mb-0">
                            <thead class="table-light">
                      <tr>
                        <th width="60" class="text-center">{{ $t('standards.purpose_limits.headers.sequence') }}</th>
                                <th width="180">{{ $t('standards.purpose_limits.headers.currency') }}</th>
                                <th width="160" class="text-center">{{ $t('standards.purpose_limits.headers.max_amount') }}</th>
                        <th>{{ $t('standards.purpose_limits.headers.message') }}</th>
                        <th width="80" class="text-center">{{ $t('standards.purpose_limits.headers.status') }}</th>
                        <th width="120" class="text-center">{{ $t('standards.purpose_limits.headers.actions') }}</th>
                      </tr>
                    </thead>
                    <tbody>
                              <tr v-for="(limit, index) in group" :key="limit.id" class="purpose-item">
                                <td class="text-center align-middle">
                                  <span class="text-muted small">{{ index + 1 }}</span>
                                </td>
                                <td class="align-middle">
                                  <div class="d-flex align-items-center">
                                    <CurrencyFlag :code="limit.currency_code" :custom-filename="limit.custom_flag_filename" :width="32" :height="24" class="me-2" />
                                    <div style="min-width: 80px;">
                                      <div class="fw-bold text-nowrap">{{ limit.currency_code }}</div>
                                      <div class="text-muted small text-nowrap">{{ getCurrencyDisplayName(limit) }}</div>
                                    </div>
                          </div>
                        </td>
                                <td class="text-center align-middle amount-column">
                                  <span class="amount-text">{{ formatAmount(limit.max_amount) }}</span>
                        </td>
                                <td class="align-middle message-column">
                                  <div class="message-text text-truncate" style="max-width: 300px;" :title="limit.display_message">
                                    {{ limit.display_message }}
                                  </div>
                        </td>
                                <td class="text-center align-middle">
                          <span class="badge" :class="limit.is_active ? 'bg-success' : 'bg-secondary'">
                            {{ limit.is_active ? $t('standards.purpose_limits.status.active') : $t('standards.purpose_limits.status.inactive') }}
                          </span>
                        </td>
                                <td class="text-center align-middle">
                                  <div class="btn-group" role="group">
                                    <button class="btn btn-sm btn-outline-primary" @click="editPurposeLimit(limit)" :title="$t('standards.purpose_limits.actions.edit')">
                            <font-awesome-icon :icon="['fas', 'edit']" />
                          </button>
                                    <button class="btn btn-sm btn-outline-danger" @click="deletePurposeLimit(limit)" :title="$t('standards.purpose_limits.actions.delete')">
                            <font-awesome-icon :icon="['fas', 'trash']" />
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

              <!-- Receipt Files View -->
              <div v-if="activeTab === 'receipt-files'" class="tab-pane fade show active">
                <div class="row mb-3">
                  <div class="col-md-3">
                    <label class="form-label">{{ $t('standards.receipt_files.year_label') }}</label>
                    <select class="form-select" v-model="selectedYear" @change="onYearChange">
                      <option value="">{{ $t('standards.receipt_files.year_placeholder') }}</option>
                      <option v-for="year in availableYears" :key="year" :value="year">
                        {{ year }}{{ $t('standards.receipt_files.year_suffix') }}
                      </option>
                    </select>
                  </div>
                  <div class="col-md-3">
                    <label class="form-label">{{ $t('standards.receipt_files.month_label') }}</label>
                    <select class="form-select" v-model="selectedMonth" @change="onMonthChange" :disabled="!selectedYear">
                      <option value="">{{ $t('standards.receipt_files.month_placeholder') }}</option>
                      <option v-for="month in availableMonths" :key="month" :value="month">
                        {{ month }}{{ $t('standards.receipt_files.month_suffix') }}
                      </option>
                    </select>
                  </div>
                  <div class="col-md-6 d-flex align-items-end">
                    <button class="btn btn-outline-primary" @click="loadReceiptFiles" :disabled="!selectedYear || !selectedMonth">
                      <font-awesome-icon :icon="['fas', 'search']" class="me-1" />
                      {{ $t('standards.receipt_files.query_button') }}
                    </button>
                  </div>
                </div>

                <div class="table-responsive">
                  <table class="table table-striped table-hover">
                    <thead>
                      <tr>
                        <th width="60">{{ $t('standards.receipt_files.headers.sequence') }}</th>
                        <th>{{ $t('standards.receipt_files.headers.filename') }}</th>
                        <th width="140">{{ $t('standards.receipt_files.headers.transaction_no') }}</th>
                        <th width="120">{{ $t('standards.receipt_files.headers.customer_name') }}</th>
                        <th width="100" class="text-end">{{ $t('standards.receipt_files.headers.amount') }}</th>
                        <th width="150">{{ $t('standards.receipt_files.headers.created_time') }}</th>
                        <th width="80" class="text-center">{{ $t('standards.receipt_files.headers.print_count') }}</th>
                        <th width="120">{{ $t('standards.receipt_files.headers.actions') }}</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-if="receiptFilesLoading">
                        <td colspan="8" class="text-center py-3">
                          <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">{{ $t('standards.purpose_limits.loading') }}</span>
                          </div>
                        </td>
                      </tr>
                      <tr v-else-if="receiptFiles.length === 0">
                        <td colspan="8" class="text-center py-3 text-muted">
                          {{ selectedYear && selectedMonth ? $t('standards.receipt_files.no_data') : $t('standards.receipt_files.select_hint') }}
                        </td>
                      </tr>
                      <tr v-for="(file, index) in receiptFiles" :key="file.filename">
                        <td class="text-center">{{ index + 1 }}</td>
                        <td class="text-truncate" style="max-width: 200px;" :title="file.filename">{{ file.filename }}</td>
                        <td class="text-center">{{ file.transaction_no || '-' }}</td>
                        <td class="text-center">{{ file.customer_name || '-' }}</td>
                        <td class="text-end amount-cell">{{ formatAmount(file.amount) }}</td>
                        <td class="text-center">{{ formatDateTime(file.created_time) }}</td>
                        <td class="text-center">
                          <span class="badge bg-info">{{ file.print_count || 0 }}</span>
                        </td>
                        <td class="text-center">
                          <button class="btn btn-sm btn-primary me-1" @click="previewFile(file)">
                            <font-awesome-icon :icon="['fas', 'eye']" />
                          </button>
                          <button class="btn btn-sm btn-success" @click="printFile(file)">
                            <font-awesome-icon :icon="['fas', 'print']" />
                          </button>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <!-- Branch Balance Alert Settings -->
              <div v-if="activeTab === 'balance-alerts'" class="tab-pane fade show active">
                <div class="d-flex justify-content-between align-items-center mb-3">
                  <h6 class="mb-0">{{ $t('standards.balance_alerts.title') }}</h6>
                  <button class="btn btn-primary btn-sm" @click="showAddBalanceAlertModal">
                    <font-awesome-icon :icon="['fas', 'plus']" class="me-1" />
                    {{ $t('standards.balance_alerts.add_button') }}
                  </button>
                </div>

                <div class="table-responsive">
                  <table class="table table-striped table-hover">
                    <thead class="table-light">
                      <tr>
                        <th width="60" class="text-center">{{ $t('standards.balance_alerts.table.index') }}</th>
                        <th width="200">{{ $t('standards.balance_alerts.table.currency') }}</th>
                        <th width="120" class="text-center">{{ $t('standards.balance_alerts.table.min_threshold') }}</th>
                        <th width="120" class="text-center">{{ $t('standards.balance_alerts.table.max_threshold') }}</th>
                        <th width="80" class="text-center">{{ $t('standards.balance_alerts.table.status') }}</th>
                        <th width="120" class="text-center">{{ $t('standards.balance_alerts.table.actions') }}</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-if="balanceAlertsLoading">
                        <td colspan="6" class="text-center py-3">
                          <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">加载中...</span>
                          </div>
                        </td>
                      </tr>
                      <tr v-else-if="balanceAlerts.length === 0">
                        <td colspan="6" class="text-center py-3 text-muted">
                          {{ $t('standards.balance_alerts.no_data') }}
                        </td>
                      </tr>
                      <tr v-for="(alert, index) in balanceAlerts" :key="alert.id">
                        <td class="text-center">{{ index + 1 }}</td>
                        <td>
                          <div class="d-flex align-items-center">
                            <CurrencyFlag :code="alert.currency_code" :custom-filename="alert.custom_flag_filename" :width="32" :height="24" class="me-2" />
                            <div style="min-width: 80px;">
                              <div class="fw-bold text-nowrap">{{ alert.currency_code }}</div>
                              <div class="text-muted small text-nowrap">{{ getCurrencyDisplayName(alert) }}</div>
                            </div>
                          </div>
                        </td>
                        <td class="text-center">{{ formatAmount(alert.min_threshold) }}</td>
                        <td class="text-center">{{ formatAmount(alert.max_threshold) }}</td>
                        <td class="text-center">
                          <span class="badge" :class="alert.is_active ? 'bg-success' : 'bg-secondary'">
                            {{ alert.is_active ? $t('standards.balance_alerts.status.active') : $t('standards.balance_alerts.status.inactive') }}
                          </span>
                        </td>
                        <td class="text-center">
                          <button class="btn btn-sm btn-primary me-1" @click="editBalanceAlert(alert)">
                            <font-awesome-icon :icon="['fas', 'edit']" />
                          </button>
                          <button class="btn btn-sm btn-danger" @click="deleteBalanceAlert(alert)">
                            <font-awesome-icon :icon="['fas', 'trash']" />
                          </button>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <!-- Field Management -->
              <div v-if="activeTab === 'field-management'" class="tab-pane fade show active">
                <FieldManagementTab />
              </div>

              <!-- Trigger Rules Configuration -->
              <div v-if="activeTab === 'trigger-rules'" class="tab-pane fade show active">
                <TriggerRulesTab />
              </div>

              <!-- Test Trigger -->
              <div v-if="activeTab === 'test-trigger'" class="tab-pane fade show active">
                <TestTriggerTab />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 兑换提醒信息编辑模态框 -->
    <div v-if="showPurposeLimitModal" class="modal fade show" style="display: block; background: rgba(0,0,0,0.5)">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ $t('standards.purpose_limits.modal.title') }}</h5>
            <button type="button" class="btn-close" @click="closePurposeLimitModal"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="savePurposeLimit">
              <div class="mb-3">
                <label class="form-label">{{ $t('standards.purpose_limits.modal.purpose_name_label') }} <span class="text-danger">*</span></label>
                <input 
                  type="text" 
                  class="form-control" 
                  v-model="purposeLimitForm.purpose_name"
                  required
                />
              </div>
              <div class="mb-3">
                <label class="form-label">{{ $t('standards.purpose_limits.modal.currency_label') }} <span class="text-danger">*</span></label>
                <currency-select
                  id="purpose-limit-currency"
                  v-model="purposeLimitForm.currency_code"
                  :currencies="availableCurrencies"
                  @change="onPurposeLimitCurrencyChange"
                />
              </div>
              <div class="mb-3">
                <label class="form-label">{{ $t('standards.purpose_limits.modal.max_amount_label') }} <span class="text-danger">*</span></label>
                <input 
                  type="number" 
                  class="form-control" 
                  v-model="purposeLimitForm.max_amount"
                  min="0"
                  step="0.01"
                  :placeholder="$t('standards.purpose_limits.modal.max_amount_placeholder')"
                />
              </div>
              <div class="mb-3">
                <label class="form-label">{{ $t('standards.purpose_limits.modal.message_label') }} <span class="text-danger">*</span></label>
                <textarea 
                  v-model="purposeLimitForm.display_message" 
                  class="form-control" 
                  rows="3" 
                  :placeholder="$t('standards.purpose_limits.modal.message_placeholder')"
                  required
                ></textarea>
              </div>
              <div class="mb-3">
                <div class="form-check">
                  <input 
                    class="form-check-input" 
                    type="checkbox" 
                    id="purposeLimitActive"
                    v-model="purposeLimitForm.is_active"
                  />
                  <label class="form-check-label" for="purposeLimitActive">{{ $t('standards.purpose_limits.modal.active_label') }}</label>
                </div>
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closePurposeLimitModal">{{ $t('standards.purpose_limits.modal.cancel') }}</button>
            <button type="button" class="btn btn-primary" @click="savePurposeLimit" :disabled="purposeLimitSaving">
              {{ purposeLimitSaving ? $t('standards.purpose_limits.modal.saving') : $t('standards.purpose_limits.modal.save') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 余额报警编辑模态框 -->
    <div v-if="showBalanceAlertModal" class="modal fade show" style="display: block; background: rgba(0,0,0,0.5)">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ $t('standards.balance_alerts.modal.title') }}</h5>
            <button type="button" class="btn-close" @click="closeBalanceAlertModal"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="saveBalanceAlert">
              <div class="mb-3">
                <label class="form-label">{{ $t('standards.balance_alerts.modal.currency_label') }}</label>
                <currency-select
                  id="balance-alert-currency"
                  v-model="balanceAlertForm.currency_code"
                  :currencies="availableCurrencies"
                  @change="onBalanceAlertCurrencyChange"
                />
              </div>
              <div class="mb-3">
                <label class="form-label">{{ $t('standards.balance_alerts.modal.min_threshold_label') }}</label>
                <input 
                  type="number" 
                  class="form-control" 
                  v-model="balanceAlertForm.min_threshold"
                  min="0"
                  step="0.01"
                />
              </div>
              <div class="mb-3">
                <label class="form-label">{{ $t('standards.balance_alerts.modal.max_threshold_label') }}</label>
                <input 
                  type="number" 
                  class="form-control" 
                  v-model="balanceAlertForm.max_threshold"
                  min="0"
                  step="0.01"
                />
              </div>
              <div class="mb-3">
                <div class="form-check">
                  <input 
                    class="form-check-input" 
                    type="checkbox" 
                    id="balanceAlertActive"
                    v-model="balanceAlertForm.is_active"
                  />
                  <label class="form-check-label" for="balanceAlertActive">{{ $t('standards.balance_alerts.modal.active_label') }}</label>
                </div>
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeBalanceAlertModal">{{ $t('standards.balance_alerts.modal.cancel') }}</button>
            <button type="button" class="btn btn-primary" @click="saveBalanceAlert" :disabled="balanceAlertSaving">
              {{ balanceAlertSaving ? $t('standards.balance_alerts.modal.saving') : $t('standards.balance_alerts.modal.save') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 提示消息 -->
    <div class="toast-container position-fixed bottom-0 end-0 p-3">
      <div class="toast" :class="{ show: toast.show }" role="alert">
        <div class="toast-header" :class="getToastHeaderClass">
          <strong class="me-auto">{{ getToastTitle }}</strong>
          <button type="button" class="btn-close" @click="hideToast"></button>
        </div>
        <div class="toast-body">
          {{ toast.message }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import standardsService from '@/services/api/standardsService'
import { formatAmount, formatDateTime } from '@/utils/formatters'
import CurrencyFlag from '@/components/CurrencyFlag.vue'
import CurrencySelect from '@/components/CurrencySelect.vue'
import FieldManagementTab from '@/components/standards/FieldManagementTab.vue'
import TriggerRulesTab from '@/components/standards/TriggerRulesTab.vue'
import TestTriggerTab from '@/components/standards/TestTriggerTab.vue'
import { getCurrencyName, getCurrencyDisplayName as getCurrencyDisplayNameFromUtils } from '@/utils/currencyTranslator'

export default {
  name: 'StandardsManagementRoot',
  components: {
    CurrencyFlag,
    CurrencySelect,
    FieldManagementTab,
    TriggerRulesTab,
    TestTriggerTab
  },
  setup() {
    const { t } = useI18n();
    
    // 响应式数据
    const activeTab = ref('purpose-limits');
    
    // 兑换提醒信息相关
    const purposeLimits = ref([]);
    const purposeLimitsLoading = ref(false);
    const editingPurposeLimit = ref(null);
    const purposeLimitSaving = ref(false);
    const showPurposeLimitModal = ref(false);
    const expandedGroups = ref({}); // 用途分组展开状态
    const purposeLimitForm = ref({
      purpose_name: '',
      currency_code: '',
      max_amount: '',
      display_message: '',
      is_active: true
    });

    // 票据文件相关
    const availableYears = ref([]);
    const availableMonths = ref([]);
    const selectedYear = ref('');
    const selectedMonth = ref('');
    const receiptFiles = ref([]);
    const receiptFilesLoading = ref(false);

    // 余额报警相关
    const balanceAlerts = ref([]);
    const balanceAlertsLoading = ref(false);
    const showBalanceAlertModal = ref(false);
    const editingBalanceAlert = ref(null);
    const balanceAlertSaving = ref(false);
    
    const balanceAlertForm = ref({
      currency_code: '',
      min_threshold: '',
      max_threshold: '',
      is_active: true
    });

    // 通用数据
    const availableCurrencies = ref([]);
    const toast = ref({
      show: false,
      type: 'success',
      message: ''
    });

    // 计算属性
    const getToastHeaderClass = computed(() => {
      return {
        'bg-success text-white': toast.value.type === 'success',
        'bg-danger text-white': toast.value.type === 'error',
        'bg-warning': toast.value.type === 'warning'
      };
    });

    const getToastTitle = computed(() => {
      switch (toast.value.type) {
        case 'success': return t('common.success_title');
        case 'error': return t('common.error_title');
        case 'warning': return t('common.warning_title');
        default: return t('common.info_title');
      }
    });

    // 按用途分组的提醒信息
    const groupedPurposeLimits = computed(() => {
      const groups = {};
      purposeLimits.value.forEach(limit => {
        const purposeName = limit.purpose_name;
        if (!groups[purposeName]) {
          groups[purposeName] = [];
        }
        groups[purposeName].push(limit);
      });
      
      // 按币种代码排序每个分组内的数据
      Object.keys(groups).forEach(purposeName => {
        groups[purposeName].sort((a, b) => a.currency_code.localeCompare(b.currency_code));
      });
      
      return groups;
    });

    // 工具方法
    const showToast = (message, type = 'success') => {
      toast.value = {
        show: true,
        type,
        message
      }
      
      // 3秒后自动隐藏
      setTimeout(() => {
        toast.value.show = false
      }, 3000)
    }

    const hideToast = () => {
      toast.value.show = false;
    };

    // 切换用途分组展开状态
    const togglePurposeGroup = (purposeName) => {
      expandedGroups.value[purposeName] = !expandedGroups.value[purposeName];
    };

    // 初始化展开状态（默认展开第一个分组）
    const initializeExpandedGroups = () => {
      const groups = Object.keys(groupedPurposeLimits.value);
      if (groups.length > 0) {
        // 默认展开第一个分组
        expandedGroups.value[groups[0]] = true;
      }
    };

    // API调用方法
    const loadPurposeLimits = async () => {
      purposeLimitsLoading.value = true;
      try {
        const response = await standardsService.getPurposeLimits();
        if (response.data.success) {
          purposeLimits.value = response.data.purpose_limits;
          // 初始化展开状态
          setTimeout(() => {
            initializeExpandedGroups();
          }, 100);
        } else {
          showToast(response.data.message || '获取提醒信息失败', 'error');
        }
      } catch (error) {
        console.error('获取提醒信息失败:', error);
        showToast('获取提醒信息失败', 'error');
      } finally {
        purposeLimitsLoading.value = false;
      }
    };

    const loadAvailableCurrencies = async () => {
      try {
        // 获取所有币种（包括未使用的），这样规范管理可以提前设置所有币种的规范
        const response = await standardsService.getAvailableCurrencies();
        if (response.data.success) {
          const currencies = response.data.currencies || [];
          
          // 转换为币种选择器需要的格式，使用多语言翻译
          availableCurrencies.value = currencies.map(currency => ({
            id: currency.id,  // 未使用的币种ID为null
            currency_code: currency.currency_code,
            currency_name: getCurrencyName(currency.currency_code), // 使用多语言翻译
            flag_code: currency.currency_code.toLowerCase(), // 使用币种代码作为国旗代码
            symbol: currency.currency_code, // 使用币种代码作为符号
            is_in_use: currency.is_in_use // 标记是否已使用
          }));
          
          console.log('加载所有币种数据:', {
            total: currencies.length,
            currencies: availableCurrencies.value
          });
        }
      } catch (error) {
        console.error('获取币种列表失败:', error);
        showToast('获取币种列表失败', 'error');
      }
    };

    const loadAvailableYears = async () => {
      try {
        const response = await standardsService.getAvailableYears();
        if (response.data.success) {
          availableYears.value = response.data.years;
        }
      } catch (error) {
        console.error('获取年份列表失败:', error);
      }
    };

    const loadAvailableMonths = async (year) => {
      try {
        const response = await standardsService.getAvailableMonths(year);
        if (response.data.success) {
          availableMonths.value = response.data.months;
        }
      } catch (error) {
        console.error('获取月份列表失败:', error);
      }
    };

    const loadReceiptFiles = async () => {
      if (!selectedYear.value || !selectedMonth.value) return;
      
      receiptFilesLoading.value = true;
      try {
        const response = await standardsService.getReceiptFiles(selectedYear.value, selectedMonth.value);
        if (response.data.success) {
          receiptFiles.value = response.data.files;
        } else {
          showToast(response.data.message || '获取文件列表失败', 'error');
        }
      } catch (error) {
        console.error('获取文件列表失败:', error);
        showToast('获取文件列表失败', 'error');
      } finally {
        receiptFilesLoading.value = false;
      }
    };

    const loadBalanceAlerts = async () => {
      balanceAlertsLoading.value = true;
      try {
        const response = await standardsService.getBalanceAlerts();
        if (response.data.success) {
          balanceAlerts.value = response.data.balance_alerts;
        } else {
          showToast(response.data.message || '获取报警设置失败', 'error');
        }
      } catch (error) {
        console.error('获取报警设置失败:', error);
        showToast('获取报警设置失败', 'error');
      } finally {
        balanceAlertsLoading.value = false;
      }
    };

    // 事件处理方法
    const onYearChange = () => {
      selectedMonth.value = '';
      availableMonths.value = [];
      receiptFiles.value = [];
      
      if (selectedYear.value) {
        loadAvailableMonths(selectedYear.value);
      }
    };

    const onMonthChange = () => {
      receiptFiles.value = [];
    };

    const showAddPurposeLimitModal = () => {
      editingPurposeLimit.value = null;
      purposeLimitForm.value = {
        purpose_name: '',
        currency_code: '',
        max_amount: '',
        display_message: '',
        is_active: true
      };
      
      showPurposeLimitModal.value = true;
    };

    const editPurposeLimit = (limit) => {
      editingPurposeLimit.value = limit;
      purposeLimitForm.value = {
        purpose_name: limit.purpose_name,
        currency_code: limit.currency_code,
        max_amount: limit.max_amount,
        display_message: limit.display_message,
        is_active: limit.is_active
      };
      
      showPurposeLimitModal.value = true;
    };

    const closePurposeLimitModal = () => {
      showPurposeLimitModal.value = false;
    };

    const savePurposeLimit = async () => {
      // 前端验证
      if (!purposeLimitForm.value.purpose_name || !purposeLimitForm.value.purpose_name.trim()) {
        showToast('请输入用途名称', 'error');
        return;
      }
      if (!purposeLimitForm.value.currency_code) {
        showToast('请选择币种', 'error');
        return;
      }
      if (!purposeLimitForm.value.max_amount || purposeLimitForm.value.max_amount <= 0) {
        showToast('请输入有效的最大金额', 'error');
        return;
      }
      if (!purposeLimitForm.value.display_message || !purposeLimitForm.value.display_message.trim()) {
        showToast('请输入显示消息', 'error');
        return;
      }

      purposeLimitSaving.value = true;
      try {
        let response;
        if (editingPurposeLimit.value) {
          response = await standardsService.updatePurposeLimit(editingPurposeLimit.value.id, purposeLimitForm.value);
        } else {
          response = await standardsService.createPurposeLimit(purposeLimitForm.value);
        }

        if (response.data.success) {
          showToast(editingPurposeLimit.value ? '更新成功' : '创建成功');
          showPurposeLimitModal.value = false;
          await loadPurposeLimits();
        } else {
          showToast(response.data.message || '保存失败', 'error');
        }
      } catch (error) {
        console.error('保存提醒信息失败:', error);
        showToast('保存失败', 'error');
      } finally {
        purposeLimitSaving.value = false;
      }
    };

    const deletePurposeLimit = async (limit) => {
      if (!confirm(t('standards.purpose_limits.delete_confirm', { purpose: limit.purpose_name }))) {
        return;
      }

      try {
        const response = await standardsService.deletePurposeLimit(limit.id);
        if (response.data.success) {
          showToast(t('standards.toast.success'));
          await loadPurposeLimits();
        } else {
          throw new Error(response.data.message || t('standards.toast.error'));
        }
      } catch (error) {
        console.error('删除提醒信息失败:', error);
        showToast(t('standards.toast.error'));
      }
    };

    const previewFile = (file) => {
      // 在新窗口中打开PDF文件预览
      const url = `/static${file.relative_path}`;
      window.open(url, '_blank');
    };

    const printFile = async (file) => {
      try {
        // 记录打印操作
        const response = await standardsService.recordPrintAction(file.filename);
        if (response.data.success) {
          // 打开打印对话框
          const url = `/static${file.relative_path}`;
          const printWindow = window.open(url, '_blank');
          printWindow.onload = () => {
            printWindow.print();
          };
          
          // 重新加载文件列表以更新打印次数
          await loadReceiptFiles();
          showToast('打印记录成功');
        } else {
          showToast(response.data.message || '打印记录失败', 'error');
        }
      } catch (error) {
        console.error('打印操作失败:', error);
        showToast('打印操作失败', 'error');
      }
    };

    const showAddBalanceAlertModal = () => {
      editingBalanceAlert.value = null;
      balanceAlertForm.value = {
        currency_code: '',
        min_threshold: '',
        max_threshold: '',
        is_active: true
      };
      
      showBalanceAlertModal.value = true;
    };

    const editBalanceAlert = (alert) => {
      editingBalanceAlert.value = alert;
      balanceAlertForm.value = {
        currency_code: alert.currency_code,
        min_threshold: alert.min_threshold,
        max_threshold: alert.max_threshold,
        is_active: alert.is_active
      };
      
      showBalanceAlertModal.value = true;
    };

    const closeBalanceAlertModal = () => {
      showBalanceAlertModal.value = false;
    };

    const saveBalanceAlert = async () => {
      // 前端验证
      if (!balanceAlertForm.value.currency_code) {
        showToast('请选择币种', 'error');
        return;
      }
      if (!balanceAlertForm.value.min_threshold && !balanceAlertForm.value.max_threshold) {
        showToast('请至少设置一个阈值（最低或最高）', 'error');
        return;
      }
      if (balanceAlertForm.value.min_threshold && balanceAlertForm.value.max_threshold && 
          parseFloat(balanceAlertForm.value.min_threshold) >= parseFloat(balanceAlertForm.value.max_threshold)) {
        showToast('最低阈值必须小于最高阈值', 'error');
        return;
      }

      balanceAlertSaving.value = true;
      try {
        // 根据currency_code找到对应的币种信息
        const selectedCurrency = availableCurrencies.value.find(c => c.currency_code === balanceAlertForm.value.currency_code);
        if (!selectedCurrency) {
          showToast('请选择币种', 'error');
          return;
        }

        // 移除币种启用状态检查，允许为所有币种设置阈值
        // if (!selectedCurrency.is_in_use) {
        //   // 对于未使用的币种，需要先创建Currency记录
        //   showToast('该币种尚未启用，请先在币种管理中启用该币种', 'warning');
        //   return;
        // }

        const formData = {
          ...balanceAlertForm.value,
          currency_id: selectedCurrency.id,
          currency_code: balanceAlertForm.value.currency_code
        };

        const response = await standardsService.createOrUpdateBalanceAlert(formData);
        if (response.data.success) {
          showToast('保存成功');
          showBalanceAlertModal.value = false;
          await loadBalanceAlerts();
        } else {
          showToast(response.data.message || '保存失败', 'error');
        }
      } catch (error) {
        console.error('保存报警设置失败:', error);
        showToast('保存失败', 'error');
      } finally {
        balanceAlertSaving.value = false;
      }
    };

    const deleteBalanceAlert = async (alert) => {
      if (!confirm(t('standards.balance_alerts.delete_confirm', { currency: alert.currency_name }))) {
        return;
      }

      try {
        const response = await standardsService.deleteBalanceAlert(alert.id);
        if (response.data.success) {
          showToast('删除成功');
          await loadBalanceAlerts();
        } else {
          throw new Error(response.data.message || t('standards.toast.error'));
        }
      } catch (error) {
        console.error('删除报警设置失败:', error);
        showToast(t('standards.toast.error'));
      }
    };

    // 获取币种显示名称（支持多语言）
    const getCurrencyDisplayName = (currencyData) => {
      if (!currencyData) return '';
      
      // 使用新的币种显示函数
      return getCurrencyDisplayNameFromUtils(currencyData.currency_code, currencyData);
    };

    // 暂时移除语言变化监听，避免i18n对象访问错误
    // 币种名称的翻译通过getCurrencyName函数实时处理

    // 币种选择变化处理方法
    const onPurposeLimitCurrencyChange = (currencyCode) => {
      console.log('兑换提醒币种选择变化:', currencyCode);
      purposeLimitForm.value.currency_code = currencyCode;
    };

    const onBalanceAlertCurrencyChange = (currencyCode) => {
      console.log('余额报警币种选择变化:', currencyCode);
      balanceAlertForm.value.currency_code = currencyCode;
    };

    // 生命周期
    onMounted(async () => {
      await loadAvailableCurrencies();
      await loadPurposeLimits();
      await loadAvailableYears();
      await loadBalanceAlerts();
    });

    return {
      // 响应式数据
      activeTab,
      purposeLimits,
      purposeLimitsLoading,
      editingPurposeLimit,
      purposeLimitSaving,
      showPurposeLimitModal,
      purposeLimitForm,
      expandedGroups,
      availableYears,
      availableMonths,
      selectedYear,
      selectedMonth,
      receiptFiles,
      receiptFilesLoading,
      balanceAlerts,
      balanceAlertsLoading,
      showBalanceAlertModal,
      editingBalanceAlert,
      balanceAlertSaving,
      balanceAlertForm,
      availableCurrencies,
      toast,
      
      // 计算属性
      getToastHeaderClass,
      getToastTitle,
      groupedPurposeLimits,
      
      // 方法
      t,
      togglePurposeGroup,
      initializeExpandedGroups,
      loadPurposeLimits,
      loadAvailableCurrencies,
      loadAvailableYears,
      loadAvailableMonths,
      loadReceiptFiles,
      loadBalanceAlerts,
      onYearChange,
      onMonthChange,
      showAddPurposeLimitModal,
      closePurposeLimitModal,
      editPurposeLimit,
      savePurposeLimit,
      deletePurposeLimit,
      previewFile,
      printFile,
      showAddBalanceAlertModal,
      closeBalanceAlertModal,
      editBalanceAlert,
      saveBalanceAlert,
      deleteBalanceAlert,
      showToast,
      hideToast,
      formatAmount,
      formatDateTime,
      getCurrencyDisplayName,
      onPurposeLimitCurrencyChange,
      onBalanceAlertCurrencyChange
    };
  }
};
</script>

<style scoped>
.nav-tabs .nav-link {
  color: #495057;
  border: 1px solid transparent;
}

.nav-tabs .nav-link.active {
  color: #0d6efd;
  background-color: #fff;
  border-color: #dee2e6 #dee2e6 #fff;
}

.toast {
  opacity: 0;
  transition: opacity 0.3s ease;
}

.toast.show {
  opacity: 1;
}

.table th {
  background-color: #f8f9fa;
  font-weight: 600;
  white-space: nowrap;
  vertical-align: middle;
}

.table td {
  vertical-align: middle;
}

/* 确保数字列的对齐 */
.table .text-end {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  font-weight: 400;
  font-variant-numeric: tabular-nums;
}

/* 金额列特殊样式 */
.amount-cell {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

/* 文件名截断样式 */
.text-truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.badge {
  font-size: 0.875em;
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
}

/* 用途分组树型结构样式 */
.purpose-tree {
  margin-top: 1rem;
}

.purpose-group {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  transition: box-shadow 0.2s ease;
}

.purpose-group:hover {
  box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.purpose-header .card-header {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-bottom: 1px solid #dee2e6;
  transition: background-color 0.2s ease;
}

.purpose-header .card-header:hover {
  background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%);
}

.purpose-item:hover {
  background-color: #f8f9fa;
}

/* 币种图标样式优化 */
.currency-flag {
  border-radius: 4px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}

/* 按钮组样式 */
.btn-group .btn {
  border-radius: 4px;
}

.btn-group .btn:not(:last-child) {
  margin-right: 2px;
}

/* 表格样式优化 */
.table-light th {
  background-color: #f8f9fa;
  border-bottom: 2px solid #dee2e6;
  font-weight: 600;
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.purpose-item td {
  border-bottom: 1px solid #f1f3f4;
  padding: 0.75rem 0.5rem;
}

.purpose-item:last-child td {
  border-bottom: none;
}

/* 响应式优化 */
@media (max-width: 768px) {
  .purpose-summary {
    display: none;
  }
  
  .btn-group {
    flex-direction: column;
  }
  
  .btn-group .btn {
    margin-right: 0;
    margin-bottom: 2px;
  }
}

/* 统一字体样式 */
.amount-column .amount-text {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  font-size: 14px;
  font-weight: 400;
  color: #2c3e50;
  font-variant-numeric: tabular-nums;
}

.message-column .message-text {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  font-size: 14px;
  font-weight: 400;
  color: #2c3e50;
  line-height: 1.4;
}

/* 移除分隔列样式 */
.separator-column {
  display: none;
}

/* 交替行背景色 */
.purpose-item:nth-child(odd) td {
  background-color: #ffffff !important;
}

.purpose-item:nth-child(even) td {
  background-color: #f8f9fa !important;
}

.purpose-item:hover td {
  background-color: #e3f2fd !important;
}

/* 用途分组内的表格样式 */
.purpose-group .table tbody tr:nth-child(odd) {
  background-color: #ffffff;
}

.purpose-group .table tbody tr:nth-child(even) {
  background-color: #f8f9fa;
}

.purpose-group .table tbody tr:hover {
  background-color: #e3f2fd;
}

/* 余额报警设置表格样式统一 */
.table-striped thead.table-light th {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  font-size: 14px;
  font-weight: 600;
  color: #2c3e50;
  background-color: #f8f9fa;
  border-bottom: 2px solid #dee2e6;
  padding: 0.75rem 0.5rem;
  text-align: center;
  vertical-align: middle;
}

/* 余额报警数据行样式 */
.table-striped tbody td {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  font-size: 14px;
  font-weight: 400;
  color: #2c3e50;
  padding: 0.75rem 0.5rem;
  vertical-align: middle;
}


</style> 

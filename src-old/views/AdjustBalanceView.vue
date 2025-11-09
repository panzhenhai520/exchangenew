<template>
  <div class="container-fluid py-4">
    <div class="row">
      <div class="col-12">
        <div class="d-flex justify-content-between align-items-center mb-4">
          <h2 class="page-title-bold">
            <font-awesome-icon :icon="['fas', 'balance-scale-right']" class="me-2" />
            {{ $t('balance_adjust.title') }}
          </h2>
        </div>
        
        <div v-if="showSuccess" class="alert alert-success d-flex align-items-center">
          <font-awesome-icon :icon="['fas', 'check-circle']" class="me-2" size="lg" />
          {{ $t('balance_adjust.adjustment_success') }}
        </div>
        
        <div v-if="showError" class="alert alert-danger d-flex align-items-center">
          <font-awesome-icon :icon="['fas', 'exclamation-circle']" class="me-2" size="lg" />
          {{ errorMessage }}
        </div>
        
        <div class="row">
          <!-- 左侧：币种表格 -->
          <div class="col-md-6">
            <div class="card mb-4">
              <div class="card-header">
                <h5 class="mb-0">{{ $t('balance_adjust.current_currency_balance') }}</h5>
              </div>
              <div class="card-body">
                <!-- 搜索输入框 -->
                <div class="mb-3">
                  <div class="input-group">
                    <span class="input-group-text">
                      <font-awesome-icon :icon="['fas', 'search']" />
                    </span>
                    <input
                      type="text"
                      class="form-control"
                      :placeholder="$t('balance_adjust.search_currency_placeholder')"
                      v-model="searchCurrency"
                      @input="filterCurrencies"
                    />
                    <button 
                      v-if="searchCurrency" 
                      class="btn btn-outline-secondary" 
                      type="button" 
                      @click="clearSearch"
                    >
                      <font-awesome-icon :icon="['fas', 'times']" />
                    </button>
                  </div>
                </div>
                <div v-if="loading" class="text-center py-4">
                  <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">{{ $t('balance_adjust.loading') }}</span>
                  </div>
                </div>
                <table v-else class="table table-striped table-bordered table-hover">
                  <thead>
                    <tr>
                      <th>{{ $t('balance_adjust.currency') }}</th>
                      <th>{{ $t('balance_adjust.current_balance_table') }}</th>
                      <th>{{ $t('balance_adjust.operations') }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="currency in filteredCurrencies" :key="currency.currency_id">
                      <td class="align-middle">
                        <div class="d-flex align-items-center">
                          <CurrencyFlag :code="currency.currency_code" :custom-filename="currency.custom_flag_filename" class="me-2" />
                          <span class="fw-bold">{{ currency.currency_code }}</span>
                          <span class="text-muted ms-1">{{ getCurrencyName(currency.currency_code) }}</span>
                        </div>
                      </td>
                      <td class="align-middle">{{ currency.current_balance.toFixed(2) }}</td>
                      <td class="align-middle">
                        <button 
                          class="btn btn-outline-primary btn-sm me-1"
                          @click="selectCurrencyForAdjustment(currency.currency_id, 'increase')"
                        >
                          <font-awesome-icon :icon="['fas', 'plus']" />
                        </button>
                        <button 
                          class="btn btn-outline-danger btn-sm"
                          @click="selectCurrencyForAdjustment(currency.currency_id, 'decrease')"
                        >
                          <font-awesome-icon :icon="['fas', 'minus']" />
                        </button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
          
          <!-- 右侧：调整表单和操作说明 -->
          <div class="col-md-6">
            <div class="card mb-4">
              <div class="card-header">
                <h5 class="mb-0">{{ $t('balance_adjust.balance_adjustment_operation') }}</h5>
              </div>
              <div class="card-body">
                <form @submit.prevent="submitAdjustment">
                  <div class="mb-3">
                    <label for="currency-select" class="form-label">{{ $t('balance_adjust.select_currency') }}</label>
                    <select 
                      id="currency-select"
                      class="form-select"
                      v-model="selectedCurrency"
                      required
                    >
                      <option value="">{{ $t('balance_adjust.select_currency_placeholder') }}</option>
                      <option v-for="currency in currencies" :key="currency.currency_id" :value="currency.currency_id">
                        {{ getCurrencyName(currency.currency_code) }} ({{ currency.currency_code }})
                      </option>
                    </select>
                  </div>
                  
                  <div class="mb-3">
                    <label for="current-balance" class="form-label">{{ $t('balance_adjust.current_balance_label') }}</label>
                    <input
                      type="text"
                      id="current-balance"
                      class="form-control"
                      :value="currentBalance.toFixed(2)"
                      readonly
                    />
                  </div>
                  
                  <div class="mb-3">
                    <label class="form-label">{{ $t('balance_adjust.adjustment_type') }}</label>
                    <div>
                      <div class="form-check form-check-inline">
                        <input
                          class="form-check-input"
                          type="radio"
                          id="adjust-add"
                          name="adjustType"
                          value="increase"
                          v-model="adjustmentType"
                        />
                        <label class="form-check-label" for="adjust-add">{{ $t('balance_adjust.increase') }}</label>
                      </div>
                      <div class="form-check form-check-inline">
                        <input
                          class="form-check-input"
                          type="radio"
                          id="adjust-subtract"
                          name="adjustType"
                          value="decrease"
                          v-model="adjustmentType"
                        />
                        <label class="form-check-label" for="adjust-subtract">{{ $t('balance_adjust.decrease') }}</label>
                      </div>
                    </div>
                  </div>
                  
                  <div class="mb-3">
                    <label for="adjust-amount" class="form-label">{{ $t('balance_adjust.adjustment_amount') }}</label>
                    <input
                      type="number"
                      id="adjust-amount"
                      class="form-control"
                      step="0.01"
                      min="0.01"
                      :placeholder="$t('balance_adjust.adjustment_amount_placeholder')"
                      v-model="adjustmentAmount"
                      required
                    />
                  </div>
                  
                  <div class="mb-3">
                    <label for="adjust-reason" class="form-label">{{ $t('balance_adjust.adjustment_reason') }}</label>
                    <textarea
                      id="adjust-reason"
                      class="form-control"
                      rows="3"
                      :placeholder="$t('balance_adjust.adjustment_reason_placeholder')"
                      v-model="adjustmentReason"
                      required
                    ></textarea>
                  </div>
                  
                  <div class="mb-3">
                    <label for="adjusted-balance" class="form-label">{{ $t('balance_adjust.adjusted_balance') }}</label>
                    <input
                      type="text"
                      id="adjusted-balance"
                      class="form-control"
                      :value="finalBalance.toFixed(2)"
                      readonly
                    />
                  </div>
                  
                  <div class="d-flex justify-content-end mt-4">
                    <button type="reset" class="btn btn-secondary me-2" @click="resetForm">
                      <font-awesome-icon :icon="['fas', 'undo']" class="me-2" />
                      {{ $t('balance_adjust.reset') }}
                    </button>
                    <button type="submit" class="btn btn-primary" :disabled="loading">
                      <font-awesome-icon :icon="['fas', 'save']" class="me-2" />
                      {{ $t('balance_adjust.submit_adjustment') }}
                    </button>
                  </div>
                </form>
              </div>
            </div>
            
            <!-- 操作说明移动到右侧 -->
            <div class="card">
              <div class="card-header">
                <h5 class="mb-0">{{ $t('balance_adjust.operation_instructions') }}</h5>
              </div>
              <div class="card-body">
                <h6>{{ $t('balance_adjust.operation_steps') }}：</h6>
                <ol class="ps-3">
                  <li class="mb-2">{{ $t('balance_adjust.step1') }}</li>
                  <li class="mb-2">{{ $t('balance_adjust.step2') }}</li>
                  <li class="mb-2">{{ $t('balance_adjust.step3') }}</li>
                  <li class="mb-2">{{ $t('balance_adjust.step4') }}</li>
                  <li class="mb-2">{{ $t('balance_adjust.step5') }}</li>
                </ol>
                
                <div class="alert alert-warning mt-3">
                  <small>
                    <strong>{{ $t('balance_adjust.notice') }}</strong> {{ $t('balance_adjust.notice_text') }}
                  </small>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 调整成功打印凭证模态框 -->
        <div class="modal fade show" 
             v-if="showPrintModal" 
             tabindex="-1" 
             style="display: block; background: rgba(0,0,0,0.5)"
             @click.self="closePrintModal">
          <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
              <div class="modal-header bg-success text-white">
                <h5 class="modal-title">{{ $t('balance_adjust.adjustment_receipt') }}</h5>
                <button type="button" class="btn-close btn-close-white" @click="closePrintModal"></button>
              </div>
              <div class="modal-body">
                <div id="printArea">
                  <div class="receipt-container">
                    <div class="text-center mb-2">
                      <h5 class="mb-1">{{ $t('balance_adjust.adjustment_receipt') }}</h5>
                      <small>BALANCE ADJUSTMENT RECEIPT</small>
                      <div v-if="adjustmentDetails.branch_display" class="small mt-1" style="color: #666;">
                        {{ adjustmentDetails.branch_display }}
                      </div>
                    </div>
                    
                    <table class="receipt-table">
                      <tbody>
                        <tr>
                          <td width="30%">{{ $t('balance_adjust.adjustment_no') }}/No:</td>
                          <td>{{ adjustmentDetails.transaction_no }}</td>
                        </tr>
                        <tr>
                          <td>{{ $t('balance_adjust.adjustment_date') }}/Date:</td>
                          <td>{{ adjustmentDetails.adjustment_date }}</td>
                        </tr>
                        <tr>
                          <td>{{ $t('balance_adjust.adjustment_time') }}/Time:</td>
                          <td>{{ adjustmentDetails.adjustment_time }}</td>
                        </tr>
                        <tr>
                          <td>{{ $t('balance_adjust.currency') }}/Currency:</td>
                          <td>{{ getCurrencyName(adjustmentDetails.currency_code) }} ({{ adjustmentDetails.currency_code }})</td>
                        </tr>
                        <tr>
                          <td>{{ $t('balance_adjust.before_balance') }}/Before:</td>
                          <td>{{ formatAmount(adjustmentDetails.before_balance) }}</td>
                        </tr>
                        <tr>
                          <td>{{ $t('balance_adjust.adjustment_amount_label') }}/Amount:</td>
                          <td>{{ (adjustmentDetails.adjustment_type === 'increase' ? '+' : '-') + formatAmount(Math.abs(adjustmentDetails.adjustment_amount)) }}</td>
                        </tr>
                        <tr>
                          <td>{{ $t('balance_adjust.after_balance') }}/After:</td>
                          <td>{{ formatAmount(adjustmentDetails.after_balance) }}</td>
                        </tr>
                        <tr>
                          <td>{{ $t('balance_adjust.reason') }}/Reason:</td>
                          <td>{{ adjustmentDetails.reason }}</td>
                        </tr>
                        <tr>
                          <td>{{ $t('balance_adjust.operator') }}/Operator:</td>
                          <td>{{ getLocalizedOperatorName(adjustmentDetails.operator_name) }}</td>
                        </tr>
                      </tbody>
                    </table>

                    <!-- 动态签名区域 -->
                    <div v-if="signatureSettings.signature_style !== 'none'" class="row g-2 mt-4">
                      <!-- 单签名框 -->
                      <div v-if="signatureSettings.signature_style === 'single'" class="col-12">
                        <div class="signature-box text-center">
                          <div>{{ signatureSettings.single_label }}</div>
                          <div class="signature-line"></div>
                          <small v-if="signatureSettings.show_date_line">{{ $t('common.date') }}/Date:_____________</small>
                        </div>
                      </div>
                      
                      <!-- 双签名框 -->
                      <template v-else-if="signatureSettings.signature_style === 'double'">
                        <div class="col-6">
                          <div class="signature-box text-center">
                            <div>{{ signatureSettings.left_label }}</div>
                            <div class="signature-line"></div>
                            <small v-if="signatureSettings.show_date_line">{{ $t('common.date') }}/Date:_____________</small>
                          </div>
                        </div>
                        <div class="col-6">
                          <div class="signature-box text-center">
                            <div>{{ signatureSettings.right_label }}</div>
                            <div class="signature-line"></div>
                            <small v-if="signatureSettings.show_date_line">{{ $t('common.date') }}/Date:_____________</small>
                          </div>
                        </div>
                      </template>
                    </div>

                    <div class="notice-section">
                      <div class="small">{{ $t('balance_adjust.receipt_note') }}</div>
                      <div class="small">Note: This is valid proof of balance adjustment. Please keep it safe.</div>
                    </div>
                  </div>
                </div>
              </div>
              <div class="modal-footer">
                <button class="btn btn-secondary" @click="closePrintModal">{{ $t('balance_adjust.close') }}</button>
                <button class="btn btn-primary" @click="printReceipt">
                  <i class="fas fa-print me-1"></i> {{ $t('balance_adjust.print_receipt') }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import CurrencyFlag from '@/components/CurrencyFlag.vue';
import api from '@/services/api';
import printService, { PrintService } from '@/services/printService';

export default {
  name: 'AdjustBalanceView',
  components: {
    CurrencyFlag
  },
  data() {
    return {
      selectedCurrency: '',
      currentBalance: 0,
      adjustmentType: 'increase',
      adjustmentAmount: '',
      adjustmentReason: '',
      finalBalance: 0,
      loading: false,
      currencies: [],
      branchId: null,
      showError: false,
      errorMessage: '',
      showSuccess: false,
      showPrintModal: false,
      adjustmentDetails: {},
      signatureSettings: {
        signature_style: 'double',
        show_date_line: true,
        single_label: '签名/Signature',
        left_label: '调节人签名/Adjuster',
        right_label: '审核人签名/Reviewer'
      },
      searchCurrency: ''
    };
  },
  async created() {
    try {
      const userStr = localStorage.getItem('user');
      const userPermissions = JSON.parse(localStorage.getItem('userPermissions') || '[]');
      const userData = userStr ? JSON.parse(userStr) : {};
      
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
      
      await this.loadCurrencies();
      await this.loadSignatureSettings();
    } catch (error) {
      console.error('Error in created hook:', error);
      this.showError = true;
      this.errorMessage = '初始化失败：' + (error.message || '未知错误');
    }
  },
  computed: {
    filteredCurrencies() {
      if (!this.searchCurrency) {
        return this.currencies;
      }
      
      const searchTerm = this.searchCurrency.toLowerCase();
      return this.currencies.filter(currency => {
        const currencyCode = currency.currency_code.toLowerCase();
        const currencyName = this.getCurrencyName(currency.currency_code).toLowerCase();
        
        return currencyCode.includes(searchTerm) || currencyName.includes(searchTerm);
      });
    }
  },
  methods: {
    async loadCurrencies() {
      try {
        const response = await api.get('balance-management/available-currencies', {
          params: { branch_id: this.branchId }
        });
        
        if (response.data.success) {
          this.currencies = response.data.data;
        } else {
          throw new Error(response.data.message || '获取币种数据失败');
        }
      } catch (error) {
        console.error('Failed to load currencies:', error);
        this.showError = true;
        this.errorMessage = error.response?.data?.message || '获取币种数据时发生错误';
      } finally {
        this.loading = false;
      }
    },
    filterCurrencies() {
      // 这个方法会在搜索框输入时自动触发（通过computed属性）
      // 不需要额外的逻辑，因为filteredCurrencies computed属性会自动更新
    },
    clearSearch() {
      this.searchCurrency = '';
    },
    async loadSignatureSettings() {
      try {
        const response = await api.get('print-settings/templates');
        if (response.data.success && response.data.settings.signature_settings) {
          this.signatureSettings = response.data.settings.signature_settings.value;
          // 为余额调节设置默认的签名标签
          if (this.signatureSettings.signature_style === 'double') {
            this.signatureSettings.left_label = this.signatureSettings.left_label || '调节人签名/Adjuster';
            this.signatureSettings.right_label = this.signatureSettings.right_label || '审核人签名/Reviewer';
          }
          console.log('签名设置加载成功:', this.signatureSettings);
        } else {
          throw new Error(response.data.message || '获取签名设置失败');
        }
      } catch (error) {
        console.error('Failed to load signature settings:', error);
        // 使用默认设置，不显示错误
        this.signatureSettings = {
          signature_style: 'double',
          show_date_line: true,
          single_label: '签名/Signature',
          left_label: '调节人签名/Adjuster',
          right_label: '审核人签名/Reviewer'
        };
        console.warn('使用默认签名设置:', this.signatureSettings);
      }
    },
    async handleCurrencyChange() {
      if (!this.selectedCurrency) return;
      
      const currency = this.currencies.find(c => c.currency_id === this.selectedCurrency);
      if (currency) {
        this.currentBalance = currency.current_balance;
        this.updateFinalBalance();
      }
    },
    updateFinalBalance() {
      const amount = parseFloat(this.adjustmentAmount) || 0;
      if (this.adjustmentType === 'increase') {
        this.finalBalance = this.currentBalance + amount;
      } else {
        this.finalBalance = this.currentBalance - amount;
      }
    },
    async submitAdjustment() {
      // 验证所有必填字段
      if (!this.selectedCurrency || !this.adjustmentAmount || !this.adjustmentReason) {
        this.showError = true;
        this.errorMessage = this.$t('balance_adjust.please_fill_all_fields');
        return;
      }

      try {
        this.loading = true;
        const requestData = {
          branch_id: parseInt(this.branchId),
          currency_id: parseInt(this.selectedCurrency),
          adjustment_amount: parseFloat(this.adjustmentAmount),
          adjustment_type: this.adjustmentType,
          reason: this.adjustmentReason.trim()
        };

        // 保存当前币种信息，以便后续使用
        const selectedCurrency = this.currencies.find(c => c.currency_id === parseInt(this.selectedCurrency));
        if (!selectedCurrency) {
          throw new Error('币种信息不存在');
        }

        const response = await api.post('balance-management/adjust', requestData);

        if (response.data.success) {
          this.showSuccess = true;
          
          // 调试：查看API返回的数据结构
          console.log('API返回的完整数据:', JSON.stringify(response.data, null, 2));
          
          // 获取调整数据 - 修复：使用正确的数据结构
          const adjustmentData = response.data.transaction;  // 从transaction字段获取交易记录信息
          
          if (!adjustmentData) {
            console.error('无法获取调整数据，完整响应:', response.data);
            throw new Error('API响应数据格式错误：缺少交易记录信息');
          }
          
          const now = new Date();
          this.adjustmentDetails = {
            transaction_id: adjustmentData.id,  // 添加缺失的transaction_id字段
            transaction_no: adjustmentData.transaction_no,  // 使用返回的正确单据号
            adjustment_date: now.toLocaleDateString('zh-CN'),
            adjustment_time: now.toTimeString().slice(0, 8),
            currency_code: selectedCurrency.currency_code,
            currency_name: selectedCurrency.currency_name,
            before_balance: parseFloat(adjustmentData.balance_before || 0),
            adjustment_amount: Math.abs(parseFloat(this.adjustmentAmount || 0)),
            adjustment_type: this.adjustmentType,
            after_balance: parseFloat(adjustmentData.balance_after || 0),
            reason: this.adjustmentReason,
            operator_name: JSON.parse(localStorage.getItem('user') || '{}').name || '未知',
            // 修正网点信息获取 - 显示网点名称而不是操作员名称
            branch_display: (() => {
              const user = JSON.parse(localStorage.getItem('user') || '{}');
              const branchName = user.branch_name || '未知网点';
              const branchCode = user.branch_code || '';
              return branchCode ? `${branchName}(${branchCode})` : branchName;
            })()
          };
          
          // 显示打印模态框
          this.showPrintModal = true;
          
          // 重置表单
          this.resetForm();
          
          // 重新加载币种数据
          await this.loadCurrencies();
          
          setTimeout(() => {
            this.showSuccess = false;
          }, 3000);
        } else {
          throw new Error(response.data.message || '余额调整失败');
        }
      } catch (error) {
        console.error('Failed to adjust balance:', error);
        this.showError = true;
        this.errorMessage = error.response?.data?.message || error.message || '余额调整失败';
      } finally {
        this.loading = false;
      }
    },
    resetForm() {
      this.selectedCurrency = '';
      this.adjustmentAmount = '';
      this.adjustmentReason = '';
      this.currentBalance = 0;
      this.finalBalance = 0;
    },
    selectCurrencyForAdjustment(currencyId, type) {
      this.selectedCurrency = currencyId;
      this.adjustmentType = type;
      // 滚动到表单顶部
      window.scrollTo(0, 0);
      // 触发币种变更处理
      this.handleCurrencyChange();
      
      // 高亮显示金额输入区域并自动聚焦
      this.$nextTick(() => {
        const amountInput = document.getElementById('adjust-amount');
        if (amountInput) {
          amountInput.focus();
          amountInput.select();
          // 添加高亮样式
          amountInput.classList.add('highlight-input');
          // 3秒后移除高亮
          setTimeout(() => {
            amountInput.classList.remove('highlight-input');
          }, 3000);
        }
      });
    },
    formatAmount(amount) {
      return new Intl.NumberFormat('zh-CN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(amount);
    },
    getLocalizedOperatorName(operatorName) {
      // 本地化操作员名称
      const currentLang = this.$i18n?.locale || 'zh';
      const langMap = { 'zh-CN': 'zh', 'en-US': 'en', 'th-TH': 'th' };
      const lang = langMap[currentLang] || 'zh';
      
      // 操作员名称映射
      const operatorNames = {
        '系统管理员': { zh: '系统管理员', en: 'System Administrator', th: 'ผู้ดูแลระบบ' },
        'admin': { zh: '系统管理员', en: 'System Administrator', th: 'ผู้ดูแลระบบ' }
      };
      
      // 获取角色名称翻译映射
      const roleNames = this.$t('system_maintenance.user_management.role_names');
      if (roleNames && roleNames[operatorName]) {
        return roleNames[operatorName];
      }
      
      return operatorNames[operatorName]?.[lang] || operatorName;
    },
    getCurrencyName(currencyCode) {
      // 检查是否是自定义币种（在currencies数据中查找）
      const currencyData = this.currencies.find(c => c.currency_code === currencyCode);
      if (currencyData && currencyData.custom_flag_filename) {
        // console.log(`[自定义币种] ${currencyCode} 使用数据库名称: ${currencyData.currency_name}`);
        return currencyData.currency_name || currencyCode;
      }
      
      // 获取币种名称的多语言支持
      const currencyNames = {
        'CNY': { zh: '人民币', en: 'Chinese Yuan', th: 'หยวนจีน' },
        'USD': { zh: '美元', en: 'US Dollar', th: 'ดอลลาร์สหรัฐ' },
        'EUR': { zh: '欧元', en: 'Euro', th: 'ยูโร' },
        'GBP': { zh: '英镑', en: 'British Pound', th: 'ปอนด์อังกฤษ' },
        'JPY': { zh: '日元', en: 'Japanese Yen', th: 'เยนญี่ปุ่น' },
        'KRW': { zh: '韩元', en: 'Korean Won', th: 'วอนเกาหลี' },
        'THB': { zh: '泰铢', en: 'Thai Baht', th: 'บาทไทย' },
        'HKD': { zh: '港币', en: 'Hong Kong Dollar', th: 'ดอลลาร์ฮ่องกง' },
        'SGD': { zh: '新加坡元', en: 'Singapore Dollar', th: 'ดอลลาร์สิงคโปร์' },
        'AUD': { zh: '澳元', en: 'Australian Dollar', th: 'ดอลลาร์ออสเตรเลีย' },
        'CAD': { zh: '加元', en: 'Canadian Dollar', th: 'ดอลลาร์แคนาดา' },
        'CHF': { zh: '瑞士法郎', en: 'Swiss Franc', th: 'ฟรังก์สวิส' },
        'NZD': { zh: '新西兰元', en: 'New Zealand Dollar', th: 'ดอลลาร์นิวซีแลนด์' },
        'SEK': { zh: '瑞典克朗', en: 'Swedish Krona', th: 'โครนาสวีเดน' },
        'NOK': { zh: '挪威克朗', en: 'Norwegian Krone', th: 'โครนนอร์เวย์' },
        'DKK': { zh: '丹麦克朗', en: 'Danish Krone', th: 'โครนเดนมาร์ก' },
        'RUB': { zh: '俄罗斯卢布', en: 'Russian Ruble', th: 'รูเบิลรัสเซีย' },
        'INR': { zh: '印度卢比', en: 'Indian Rupee', th: 'รูปีอินเดีย' },
        'BRL': { zh: '巴西雷亚尔', en: 'Brazilian Real', th: 'เรียลบราซิล' },
        'MXN': { zh: '墨西哥比索', en: 'Mexican Peso', th: 'เปโซเม็กซิโก' },
        'ZAR': { zh: '南非兰特', en: 'South African Rand', th: 'แรนด์แอฟริกาใต้' },
        'TRY': { zh: '土耳其里拉', en: 'Turkish Lira', th: 'ลิราตุรกี' },
        'MYR': { zh: '马来西亚林吉特', en: 'Malaysian Ringgit', th: 'ริงกิตมาเลเซีย' },
        'PHP': { zh: '菲律宾比索', en: 'Philippine Peso', th: 'เปโซฟิลิปปินส์' },
        'IDR': { zh: '印尼盾', en: 'Indonesian Rupiah', th: 'รูเปียห์อินโดนีเซีย' },
        'VND': { zh: '越南盾', en: 'Vietnamese Dong', th: 'ดองเวียดนาม' },
        'LAK': { zh: '老挝基普', en: 'Lao Kip', th: 'กีบลาว' },
        'KHR': { zh: '柬埔寨瑞尔', en: 'Cambodian Riel', th: 'เรียลกัมพูชา' },
        'MMK': { zh: '缅甸元', en: 'Myanmar Kyat', th: 'จ๊าตพม่า' },
        'BND': { zh: '文莱元', en: 'Brunei Dollar', th: 'ดอลลาร์บรูไน' },
        'TWD': { zh: '台币', en: 'Taiwan Dollar', th: 'ดอลลาร์ไต้หวัน' },
        'SAR': { zh: '沙特里亚尔', en: 'Saudi Riyal', th: 'ริยาลซาอุดิอาระเบีย' },
        'AED': { zh: '阿联酋迪拉姆', en: 'UAE Dirham', th: 'ดีแรห์มสหรัฐอาหรับเอมิเรตส์' },
        'BHD': { zh: '巴林第纳尔', en: 'Bahraini Dinar', th: 'ดีนาร์บาห์เรน' },
        'QAR': { zh: '卡塔尔里亚尔', en: 'Qatari Riyal', th: 'ริยาลกาตาร์' },
        'KWD': { zh: '科威特第纳尔', en: 'Kuwaiti Dinar', th: 'ดีนาร์คูเวต' },
        'OMR': { zh: '阿曼里亚尔', en: 'Omani Rial', th: 'ริยาลโอมาน' },
        'JOD': { zh: '约旦第纳尔', en: 'Jordanian Dinar', th: 'ดีนาร์จอร์แดน' },
        'EGP': { zh: '埃及镑', en: 'Egyptian Pound', th: 'ปอนด์อียิปต์' },
        'MAD': { zh: '摩洛哥迪拉姆', en: 'Moroccan Dirham', th: 'ดีแรห์มโมร็อกโก' },
        'TND': { zh: '突尼斯第纳尔', en: 'Tunisian Dinar', th: 'ดีนาร์ตูนิเซีย' },
        'DZD': { zh: '阿尔及利亚第纳尔', en: 'Algerian Dinar', th: 'ดีนาร์แอลจีเรีย' },
        'LYD': { zh: '利比亚第纳尔', en: 'Libyan Dinar', th: 'ดีนาร์ลิเบีย' },
        'ILS': { zh: '以色列新谢克尔', en: 'Israeli New Shekel', th: 'นิวเชเกลอิสราเอล' },
        'PKR': { zh: '巴基斯坦卢比', en: 'Pakistani Rupee', th: 'รูปีปากีสถาน' },
        'BDT': { zh: '孟加拉塔卡', en: 'Bangladeshi Taka', th: 'ตากาบังกลาเทศ' },
        'LKR': { zh: '斯里兰卡卢比', en: 'Sri Lankan Rupee', th: 'รูปีศรีลังกา' },
        'NPR': { zh: '尼泊尔卢比', en: 'Nepalese Rupee', th: 'รูปีเนปาล' },
        'AFN': { zh: '阿富汗尼', en: 'Afghan Afghani', th: 'อัฟกานีอัฟกานิสถาน' },
        'MVR': { zh: '马尔代夫拉菲亚', en: 'Maldivian Rufiyaa', th: 'รูฟิยาห์มัลดีฟส์' },
        'BTN': { zh: '不丹努尔特鲁姆', en: 'Bhutanese Ngultrum', th: 'งูลตรูมภูฏาน' }
      };
      
      // 获取当前语言
      const currentLang = this.$i18n?.locale || 'zh';
      const langMap = { 'zh-CN': 'zh', 'en-US': 'en', 'th-TH': 'th' };
      const lang = langMap[currentLang] || 'zh';
      
      return currencyNames[currencyCode]?.[lang] || currencyCode;
    },
    closePrintModal() {
      this.showPrintModal = false;
      this.adjustmentDetails = {};
    },
    async printReceipt() {
      try {
        // 使用统一打印服务
        const config = PrintService.getBalanceAdjustConfig(this.adjustmentDetails, this.$toast);
        const success = await printService.printPDF(config);
        
        if (success) {
          console.log('余额调节凭证打印完成');
        }
      } catch (error) {
        console.error('余额调节打印失败:', error);
        const errorMsg = error.message || '未知错误';
        this.$toast ? this.$toast.error(`打印失败: ${errorMsg}`) : alert(`打印失败: ${errorMsg}`);
      }
    }
  },
  watch: {
    selectedCurrency: 'handleCurrencyChange',
    adjustmentAmount: 'updateFinalBalance',
    adjustmentType: 'updateFinalBalance'
  }
};
</script>

<style scoped>
.currency-flag {
  width: 24px;
  height: 16px;
  display: inline-block;
  vertical-align: middle;
}

/* 打印凭证样式 */
.receipt-container {
  padding: 10px;
}

.receipt-table {
  width: 100%;
  margin-bottom: 10px;
  border-collapse: collapse;
}

.receipt-table td {
  padding: 2px 0;
  vertical-align: top;
  border: none;
  font-size: 12px;
  line-height: 1.3;
}

.signature-box {
  border: 1px solid #dee2e6;
  border-radius: 4px;
  margin-top: 10px;
  padding: 8px;
  min-height: 50px;
}

.signature-line {
  height: 1px;
  background: #000;
  margin: 8px 0 4px;
}

.notice-section {
  margin-top: 10px;
  border-top: 1px dashed #dee2e6;
  padding-top: 5px;
  font-size: 11px;
}

@media print {
  @page {
    size: A4;
    margin: 10mm;
  }

  body * {
    visibility: hidden !important;
  }

  #printArea, #printArea * {
    visibility: visible !important;
  }

  #printArea {
    position: absolute;
    left: 0;
    top: 0;
    width: 100%;
    padding: 0;
    margin: 0;
  }

  .modal, .modal-dialog, .modal-content {
    visibility: hidden !important;
    display: none !important;
  }

  .modal-backdrop {
    display: none !important;
  }

  .modal-header,
  .modal-footer,
  .btn-close {
    display: none !important;
  }

  .print-content {
    padding: 0 !important;
  }

  .receipt-container {
    padding: 0 !important;
  }

  * {
    color: black !important;
    background: white !important;
    font-family: Arial, sans-serif !important;
  }
}

/* 高亮输入框样式 */
.highlight-input {
  border: 2px solid #007bff !important;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25) !important;
  animation: pulse-highlight 2s infinite;
}

@keyframes pulse-highlight {
  0% { box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25); }
  50% { box-shadow: 0 0 0 0.4rem rgba(0, 123, 255, 0.15); }
  100% { box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25); }
}
</style>

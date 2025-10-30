import rateService from '../../../services/api/rateService';
import repformService from '../../../services/api/repformService';
import botService from '../../../services/api/botService';
import complianceService from '@/services/api/complianceService';
import { formatTransactionTime, formatReceiptTime, formatAmount } from '@/utils/formatters';
import printService, { PrintService } from '@/services/printService';
import { balanceService } from '@/services/api/balanceService';
import { getCurrencyName } from '@/utils/currencyTranslator';
import customerReservationMixin from './customerReservationMixin';

export default {
  mixins: [customerReservationMixin],
  data() {
    const userInfo = JSON.parse(localStorage.getItem('user') || '{}');
    // 修复：不要硬编码任何币种，如果没有正确的本币信息，应该提示用户重新登录
    const branchCurrency = userInfo.branch_currency || null;
    
    return {
      userInfo: userInfo,
      userBranchCurrency: branchCurrency,
      baseCurrency: branchCurrency?.code || '',
      baseCurrencyName: branchCurrency?.name || '', // 将在mounted中使用统一翻译工具设置
      // 币种数据
      availableCurrencies: {},
      currencyIdMap: {}, // 新增：币种代码到ID的映射
      currencyNames: {}, // 新增: 币种的多语言名称映射
      foreignCurrency: '',

      
      // 汇率数据
      topRates: [],
      rateSearchKeyword: '', // 汇率搜索关键字
      
      // 状态变量
      exchangeMode: '',
      amountType: '', // 修改：移除默认'have'
      inputAmount: null,
      targetAmount: null,
      rateDisplay: '',
      resultDisplay: '',
      showConfirmation: false,
      customerName: '',
      customerId: '',
      customerAddress: '',
      customerStats: null,  // 新增：客户历史统计
      customerHistoryLoading: false,
      lastReservationStatusCode: null,
      selectedFundingSource: '',
      fundingSourceOptions: [],
      pendingTriggers: [],
      currentTrigger: null,
      activeTriggerReportType: null,
      activeTriggerMessage: '',
      lastTriggerData: null,
      
      // 交易成功
      transactionSuccess: false,
      transactionDetails: {},
      
      // 新增：上一笔交易信息
      lastTransaction: null,
      
      // 加载状态
      loading: {
        currencies: false,
        rates: false,
        transaction: false,
        fundingSources: false
      },
      
      // 错误状态
      error: {
        currencies: null,
        rates: null,
        transaction: null
      },
      messages: {
        zh: {
          customerSellForeign: this.$t('exchange.buy'),
          customerBuyForeign: this.$t('exchange.sell')
        },
        en: {
          customerSellForeign: this.$t('exchange.buy'),
          customerBuyForeign: this.$t('exchange.sell')
        }
      },
      
      // 新增：步骤控制
      currentStep: 1,
      
      // 新增：用途选择相关
      selectedPurpose: '',
      purposeOptions: [],
      purposeMessage: '',
      purposeMaxAmount: 0,
      purposeExceeded: false,
      purposeWarningMessage: '',
      
      // 新增：备注信息
      customerRemarks: '',
      
      // 新增：兑换类型（大额交易相关 - 监管要求第40行）
      showExchangeType: true,  // 修改：默认开启，根据金额自动显示
      exchangeType: 'normal',  // 默认为normal，可选: 'normal' | 'asset_backed'
      LARGE_AMOUNT_THRESHOLD: 2000000,  // 200万本币阈值
      
      // 新增：签名设置
      signatureSettings: {
        signature_style: 'double',
        show_date_line: true,
        single_label: '',
        left_label: '',
        right_label: ''
      },
      
      // 新增：完整的打印设置
      fullPrintSettings: {},
      
      // 新增：余额相关数据
      selectedForeignCurrencyInfo: null,
      currentBalanceInfo: null,
      
      // 新增：余额检查结果
      balanceCheckResult: {
        foreign_currency: {
          sufficient: true,
          current_balance: 0,
          message: ''
        },
        base_currency: {
          sufficient: true,
          current_balance: 0,
          message: ''
        },
        threshold_alerts: []
      },
      
      // 新增：语音相关数据
      canSpeak: false,
      currentLanguage: 'zh',
      speechSynthesis: null,
      currentPromptText: '',
      calculatedInputAmount: null,
      calculatedTargetAmount: null,

      // 新增：AMLO/BOT触发检查相关
      triggerCheckResult: null,
      showReservationModal: false,
      reservationTransactionData: null,
      customerHistoryData: null,
      showCustomerHistory: false
    };
  },
  computed: {
    baseFlagUrl() {
      return this.getFlagUrl(this.baseCurrency);
    },
    foreignFlagUrl() {
      return this.getFlagUrl(this.foreignCurrency);
    },
    foreignCurrencyName() {
      return this.getCurrencyName(this.foreignCurrency);
    },
    exchangeHint() {
      return this.exchangeMode === 'sell_foreign' 
        ? `客户卖出 ${this.foreignCurrencyName}(${this.foreignCurrency}) 对 ${this.baseCurrencyName}(${this.baseCurrency})`
        : `客户买入 ${this.foreignCurrencyName}(${this.foreignCurrency}) (对 ${this.baseCurrencyName}(${this.baseCurrency}))`;
    },
    inputUnitCode() {
      if (this.exchangeMode === 'sell_foreign') {
        // 客户卖出外币（银行买入外币）
        // 无论顾客支付还是顾客需，客户都是支付外币，获得本币
        return this.foreignCurrency;
      } else {
        // 客户买入外币（银行卖出外币）
        // 无论顾客支付还是顾客需，客户都是支付本币，获得外币
        return this.baseCurrency;
      }
    },
    targetUnitCode() {
      if (this.exchangeMode === 'sell_foreign') {
        // 客户卖出外币（银行买入外币）
        // 无论顾客支付还是顾客需，客户都是支付外币，获得本币
        return this.baseCurrency;
      } else {
        // 客户买入外币（银行卖出外币）
        // 无论顾客支付还是顾客需，客户都是支付本币，获得外币
        return this.foreignCurrency;
      }
    },
    inputUnitFlagUrl() {
      return this.getFlagUrl(this.inputUnitCode);
    },
    targetUnitFlagUrl() {
      return this.getFlagUrl(this.targetUnitCode);
    },
    inputUnit() {
      return `${this.availableCurrencies[this.inputUnitCode] || ''}(${this.inputUnitCode})`;
    },
    targetUnit() {
      return `${this.availableCurrencies[this.targetUnitCode] || ''}(${this.targetUnitCode})`;
    },
    // 交易类型描述
    transactionTypeDescription() {
      if (this.exchangeMode === 'buy_foreign') {
        return `(卖出 ${this.foreignCurrency} ${this.foreignCurrencyName})`;
      } else {
        return `(买入 ${this.foreignCurrency} ${this.foreignCurrencyName})`;
      }
    },
    canConfirm() {
      if (this.disableExchange) {
        return false;
      }
      // 检查是否有有效的输入金额和计算结果
      if (this.amountType === 'have') {
        return this.inputAmount > 0 && this.targetAmount > 0;
      } else {
        return this.targetAmount > 0 && this.inputAmount > 0;
      }
    },
    // 过滤汇率列表
    filteredRates() {
      if (!this.rateSearchKeyword.trim()) {
        return this.topRates;
      }

      const keyword = this.rateSearchKeyword.toLowerCase().trim();
      return this.topRates.filter(rate => {
        return rate.currency.toLowerCase().includes(keyword);
      });
    },

    // 计算本币金额（用于兑换类型判断）
    calculatedLocalAmount() {
      // 没有输入任何金额时返回0
      if (!this.inputAmount && !this.targetAmount) return 0;

      // 获取当前输入的金额
      const currentAmount = this.amountType === 'have' ?
        parseFloat(this.inputAmount || 0) :
        parseFloat(this.targetAmount || 0);

      if (currentAmount === 0) return 0;

      let localAmount = 0;

      // 判断逻辑：
      // 1. buy_foreign (界面显示"卖出外币") = 客户买入外币，网点卖出外币给客户
      //    - 本币是客户支付的金额
      // 2. sell_foreign (界面显示"买入外币") = 客户卖出外币，网点买入外币
      //    - 本币是网点支付的金额

      if (this.exchangeMode === 'sell_foreign') {
        // 客户卖出外币，网点买入外币
        if (this.amountType === 'have') {
          // 顾客有外币：输入的是外币金额(inputAmount)，需要计算本币
          // 需要汇率才能计算，暂时无法判断，返回一个估算值
          const rate = this.getExchangeRate();
          localAmount = currentAmount * rate;
        } else {
          // 顾客需要本币：输入的就是本币金额(targetAmount)
          localAmount = currentAmount;
        }
      } else if (this.exchangeMode === 'buy_foreign') {
        // 客户买入外币，网点卖出外币
        if (this.amountType === 'have') {
          // 顾客有本币：输入的就是本币金额(inputAmount)
          localAmount = currentAmount;
        } else {
          // 顾客需要外币：输入的是外币金额(targetAmount)，需要计算本币
          const rate = this.getExchangeRate();
          localAmount = currentAmount * rate;
        }
      }

      return localAmount;
    },

    // 检查是否需要显示大额兑换类型选择
    shouldShowExchangeType() {
      return this.showExchangeType && this.calculatedLocalAmount > this.LARGE_AMOUNT_THRESHOLD;
    },
  },
  methods: {
    async loadFundingSources() {
      try {
        this.loading.fundingSources = true
        const response = await complianceService.getFundingSources({ is_active: true })
        if (response.success && Array.isArray(response.data)) {
          this.fundingSourceOptions = response.data
        } else if (Array.isArray(response)) {
          // 兼容旧格式
          this.fundingSourceOptions = response
        } else {
          this.fundingSourceOptions = []
        }
      } catch (error) {
        console.error('加载资金来源失败:', error)
        this.fundingSourceOptions = []
      } finally {
        this.loading.fundingSources = false
      }
    },
    // 获取货币的多语言名称
    getCurrencyDisplayName(currencyCode) {
      return getCurrencyName(currencyCode, null, this.currencyNames);
    },
    // 初始化签名标签多语言
    initSignatureLabels() {
      this.signatureSettings.single_label = 'Customer';
      this.signatureSettings.left_label = 'Customer';
      this.signatureSettings.right_label = 'Teller';
    },
    // 获取币种的多语言名称 - 使用统一的货币翻译工具
    getCurrencyName(currencyCode) {
      // 在Vue组件中，直接使用this.$i18n.locale来获取当前语言
      const currentLang = this.getCurrentLang();
      
      // 检查是否是自定义币种（有custom_flag_filename）
      const currencyData = this.availableCurrencies[currencyCode];
      if (currencyData && currencyData.custom_flag_filename) {
        // console.log(`[自定义币种] ${currencyCode} 使用数据库名称: ${currencyData.currency_name}`);
        return currencyData.currency_name || currencyCode;
      }
      
      // 兼容旧格式（直接存储字符串的情况）
      if (typeof currencyData === 'string') {
        return currencyData;
      }
      
      return getCurrencyName(currencyCode, currentLang, this.currencyNames);
    },
    
    // 获取当前语言代码
    getCurrentLang() {
      const locale = this.$i18n?.locale || 'zh-CN';
      const langMap = {
        'zh-CN': 'zh',
        'en-US': 'en', 
        'th-TH': 'th'
      };
      return langMap[locale] || 'zh';
    },
    
    // 获取币种的自定义图标文件名
    getCurrencyCustomFlag(currencyCode) {
      const currencyData = this.availableCurrencies[currencyCode];
      if (currencyData && currencyData.custom_flag_filename) {
        return currencyData.custom_flag_filename;
      }
      return null;
    },
    
    async handleAmountInput(event, isInputAmount) {
      const value = event.target.value ? parseFloat(event.target.value) : null;
      if (this.amountType === 'have' && isInputAmount) {
        this.inputAmount = value;
        this.targetAmount = null;
        // 清空之前的检查结果
        this.resetBalanceCheckResult();
      } else if (this.amountType === 'want' && !isInputAmount) {
        this.targetAmount = value;
        this.inputAmount = null;
        
        // 顾客需要模式：实时检查余额
        if (value && value > 0 && this.foreignCurrency && this.exchangeMode) {
          await this.performRealTimeBalanceCheck(value);
        } else {
          this.resetBalanceCheckResult();
        }
      }
    },
    
    // 重置余额检查结果
    resetBalanceCheckResult() {
      this.balanceCheckResult = {
        foreign_currency: {
          sufficient: true,
          current_balance: 0,
          message: ''
        },
        base_currency: {
          sufficient: true,
          current_balance: 0,
          message: ''
        },
        threshold_alerts: []
      };
    },
    
    // 实时余额检查（顾客需要模式）
    async performRealTimeBalanceCheck(targetAmount) {
      if (!this.foreignCurrency || !this.exchangeMode || !targetAmount || targetAmount <= 0) {
        return;
      }
      
      try {
        // 计算需要支付的金额
        const exchangeRate = this.getExchangeRate();
        if (!exchangeRate || exchangeRate <= 0) {
          console.warn('无法获取汇率');
          return;
        }
        
                // 根据交易模式确定要检查的金额和币种
        let checkAmount;
        if (this.exchangeMode === 'buy_foreign') {
          // 界面显示"卖出外币"：客户买入外币，网点卖出外币给客户，网点需要支出外币
          // 在"顾客需要"模式下，输入的就是网点需要支出的外币金额
          checkAmount = targetAmount; // 网点需要支付的外币金额，检查外币库存
        } else if (this.exchangeMode === 'sell_foreign') {
          // 界面显示"买入外币"：客户卖出外币，网点买入外币，网点需要支出本币
          // 在"顾客需要"模式下，输入的就是网点需要支出的本币金额
          checkAmount = targetAmount; // 网点需要支付的本币金额，检查本币余额
        } else {
          console.warn('未知的交易模式:', this.exchangeMode);
          return;
        }
        
        // 检查余额和阈值
        const checkResult = await this.checkBalanceAndThreshold(checkAmount);
        
        if (checkResult) {
          // 重要修复：更新组件的balanceCheckResult属性
          this.balanceCheckResult = checkResult;
          
          // 显示检查结果
          const resultMessage = this.displayBalanceCheckResult(checkResult);
          if (resultMessage) {
            // 在resultDisplay中显示实时检查结果
            this.resultDisplay = `<div class="balance-check-realtime">
              <div class="mb-2"><i class="fas fa-info-circle me-1"></i><strong>${this.$t('exchange.realtime_balance_check')}：</strong></div>
              ${resultMessage}
            </div>`;
          } else if (checkResult.sufficient && checkResult.threshold_alerts.length === 0) {
            // 余额充足且无阈值警告
            this.resultDisplay = `<div class="text-success balance-check-realtime">
              <i class="fas fa-check-circle me-1"></i>${this.$t('exchange.balance_sufficient')}
            </div>`;
          }
        }
        
      } catch (error) {
        console.error('实时余额检查失败:', error);
      }
    },
    getFlagUrl(currencyCode) {
      if (!currencyCode) return '';
      const knownFlags = ['USD', 'EUR', 'CNY', 'JPY', 'THB', 'HKD', 'GBP'];
      if (knownFlags.includes(currencyCode.toUpperCase())) {
        return `/flags/${currencyCode.toUpperCase()}.svg`;
      }
      return '';
    },
    getCurrencyFlag(code) {
      const flagMap = {
        USD: '🇺🇸',
        EUR: '🇪🇺',
        GBP: '🇬🇧',
        JPY: '🇯🇵',
        HKD: '🇭🇰',
        THB: '🇹🇭',
        CNY: '🇨🇳',
        AUD: '🇦🇺',
        CAD: '🇨🇦',
        SGD: '🇸🇬',
        CHF: '🇨🇭',
      };
      return flagMap[code] || code;
    },
    formatRate(rate) {
      return parseFloat(rate).toFixed(4);
    },
    formatDateTime(date, time) {
      // 使用统一的交易时间格式化函数
      return formatTransactionTime(date, time);
    },
    formatAmount,
    formatReceiptTime,
    // updateForeignOptions方法已删除 - CurrencySelect组件现在直接从API加载数据
    fetchRateForPair(foreignC) {
      // 从当前汇率中查找
      const rate = this.topRates.find(r => r.currency === foreignC);
      if (rate) {
        return {
          buy_rate: rate.buyRate,
          sell_rate: rate.sellRate
        };
      }
      return null; // 汇率不可用
    },
    updateRateDisplay() {
      let rateText = this.$t('exchange.rate_unavailable');
      const rateObject = this.fetchRateForPair(this.foreignCurrency);
      
      if (rateObject) {
        if (this.exchangeMode === 'sell_foreign') { // 客户卖出外币，银行买入外币
          if (rateObject.buy_rate) {
            rateText = `1 ${this.foreignCurrency} = ${parseFloat(rateObject.buy_rate).toFixed(4)} ${this.baseCurrency} (${this.$t('exchange.bank_buy_rate')})`;
          }
        } else { // 客户买入外币，银行卖出外币
          if (rateObject.sell_rate) {
            rateText = `1 ${this.foreignCurrency} = ${parseFloat(rateObject.sell_rate).toFixed(4)} ${this.baseCurrency} (${this.$t('exchange.bank_sell_rate')})`;
          }
        }
      }
      
      this.rateDisplay = rateText;
    },
    refreshAll() {
      this.updateRateDisplay();
      this.resultDisplay = '';
    },
    // updateForeignOptionsAndRefresh方法已删除
    
    // 新增：检查余额和阈值的方法
    async checkBalanceAndThreshold(transactionAmount) {
      console.log('=== 开始余额检查 ===');
      console.log('exchangeMode:', this.exchangeMode);
      console.log('transactionAmount:', transactionAmount);
      console.log('foreignCurrency:', this.foreignCurrency);
      console.log('baseCurrency:', this.baseCurrency);
      
      if (!this.foreignCurrency || !transactionAmount || transactionAmount <= 0) {
        console.log('⚠️ 检查条件不满足，跳过余额检查');
        return null;
      }
      
      try {
        // 获取外币和本币的币种ID
        console.log('🔍 当前currencyIdMap:', this.currencyIdMap);
        console.log('🔍 外币:', this.foreignCurrency, '本币:', this.baseCurrency);
        
        const foreignCurrencyId = this.currencyIdMap[this.foreignCurrency];
        const baseCurrencyId = this.currencyIdMap[this.baseCurrency];
        
        console.log('🔍 获取到的ID - 外币ID:', foreignCurrencyId, '本币ID:', baseCurrencyId);
        
        if (!foreignCurrencyId || !baseCurrencyId) {
          console.error('❌ 无法获取币种ID:', { 
            foreignCurrency: this.foreignCurrency,
            baseCurrency: this.baseCurrency,
            foreignCurrencyId, 
            baseCurrencyId,
            currencyIdMap: this.currencyIdMap
          });
          return null;
        }
        
        // 根据交易类型确定需要检查的币种
        let checkCurrencyId;
        
        console.log('💰 确定检查币种...');
        console.log('💰 当前交易模式:', this.exchangeMode);
        console.log('💰 外币ID:', foreignCurrencyId, '本币ID:', baseCurrencyId);
        
        if (this.exchangeMode === 'buy_foreign') {
          // 客户买入外币（如选择"卖出美元USD"）：网点卖出外币给客户，需要检查外币库存
          checkCurrencyId = foreignCurrencyId;
          console.log('📤 客户买入外币模式 - 检查外币库存:', this.foreignCurrency, 'ID:', checkCurrencyId);
        } else if (this.exchangeMode === 'sell_foreign') {
          // 客户卖出外币（如选择"买入美元USD"）：网点买入外币，需要支付本币，检查本币余额
          checkCurrencyId = baseCurrencyId;
          console.log('📥 客户卖出外币模式 - 网点需要支付本币，检查本币余额:', this.baseCurrency, 'ID:', checkCurrencyId);
        } else {
          console.error('❌ 未知的交易模式:', this.exchangeMode);
          return null;
        }
        
        console.log('🔍 最终确定检查的币种ID:', checkCurrencyId);
        
        // 调用余额检查API
        console.log('🌐 调用余额API - 币种ID:', checkCurrencyId);
        const balanceResponse = await balanceService.getCurrentBalance(checkCurrencyId);
        console.log('🌐 余额API响应:', balanceResponse.data);
        
        const alertResponse = await balanceService.getAlertStatus(checkCurrencyId);
        console.log('🌐 阈值API响应:', alertResponse.data);
        
        if (!balanceResponse.data.success || !alertResponse.data.success) {
          console.error('❌ 获取余额或阈值信息失败');
          console.error('余额API成功:', balanceResponse.data.success);
          console.error('阈值API成功:', alertResponse.data.success);
          return null;
        }
        
        const currentBalance = balanceResponse.data.balance;
        const alertInfo = alertResponse.data.alert_info;
        
        console.log('💰 当前余额:', currentBalance);
        console.log('💰 需要金额:', transactionAmount);
        console.log('💰 阈值信息:', alertInfo);
        
        // 检查余额充足性
        const sufficient = currentBalance >= transactionAmount;
        console.log('💰 余额充足性检查结果:', sufficient);
        
        // 检查阈值
        const thresholdAlerts = [];
        console.log('🚨 开始阈值检查...');
        
        // 检查本币和外币的阈值
        if (this.exchangeMode === 'sell_foreign') {
          // 买入外币时，本币会减少，检查本币下限；外币会增加，检查外币上限
          // 1. 检查本币下限（银行支付本币）
          const baseCurrencyAlertResponse = await balanceService.getAlertStatus(baseCurrencyId);
          if (baseCurrencyAlertResponse.data.success) {
            const baseCurrencyAlertInfo = baseCurrencyAlertResponse.data.alert_info;
            const baseCurrencyBalanceResponse = await balanceService.getCurrentBalance(baseCurrencyId);
            if (baseCurrencyBalanceResponse.data.success && baseCurrencyAlertInfo.threshold_info) {
              const baseCurrencyBalance = baseCurrencyBalanceResponse.data.balance;
              const baseCurrencyThreshold = baseCurrencyAlertInfo.threshold_info;
              
              // 重要：在sell_foreign模式下，传入的transactionAmount已经是本币金额，不需要再乘汇率
              let baseCurrencyAmount;
              if (checkCurrencyId === baseCurrencyId) {
                // 如果检查的就是本币，transactionAmount就是本币金额
                baseCurrencyAmount = transactionAmount;
              } else {
                // 如果检查的是外币，需要转换为本币金额
                baseCurrencyAmount = transactionAmount * this.getExchangeRate();
              }
              
              const baseCurrencyAfterBalance = baseCurrencyBalance - baseCurrencyAmount;
              
              console.log('🚨 买入外币模式 - 本币检查:');
              console.log('🚨 - 本币余额:', baseCurrencyBalance);
              console.log('🚨 - 传入交易金额:', transactionAmount);
              console.log('🚨 - 检查币种ID:', checkCurrencyId, '本币ID:', baseCurrencyId);
              console.log('🚨 - 实际本币支出金额:', baseCurrencyAmount);
              console.log('🚨 - 交易后本币余额:', baseCurrencyAfterBalance);
              console.log('🚨 - 下限阈值:', baseCurrencyThreshold.min_threshold);
              
              // 检查本币下限
              if (baseCurrencyThreshold.min_threshold && baseCurrencyAfterBalance < baseCurrencyThreshold.min_threshold) {
                thresholdAlerts.push({
                  type: 'min',
                  level: 'critical',
                  currency: this.baseCurrency,
                                      message: `${this.$t('exchange.after_transaction')}${this.getCurrencyName(this.baseCurrency)}${this.$t('exchange.balance_will_below')}${this.$t('exchange.min_threshold')} ${baseCurrencyThreshold.min_threshold}`,
                  current_balance: baseCurrencyBalance,
                  after_balance: baseCurrencyAfterBalance,
                  threshold_value: baseCurrencyThreshold.min_threshold
                });
              }
            }
          }
          
          // 2. 检查外币上限（银行增加外币）
          const foreignCurrencyAlertResponse = await balanceService.getAlertStatus(foreignCurrencyId);
          if (foreignCurrencyAlertResponse.data.success) {
            const foreignCurrencyAlertInfo = foreignCurrencyAlertResponse.data.alert_info;
            const foreignCurrencyBalanceResponse = await balanceService.getCurrentBalance(foreignCurrencyId);
            if (foreignCurrencyBalanceResponse.data.success && foreignCurrencyAlertInfo.threshold_info) {
              const foreignCurrencyBalance = foreignCurrencyBalanceResponse.data.balance;
              const foreignCurrencyThreshold = foreignCurrencyAlertInfo.threshold_info;
              
              // 计算外币变化金额
              let foreignCurrencyAmount;
              if (checkCurrencyId === foreignCurrencyId) {
                // 如果检查的就是外币，transactionAmount就是外币金额
                foreignCurrencyAmount = transactionAmount;
              } else {
                // 如果检查的是本币，需要转换为外币金额
                foreignCurrencyAmount = transactionAmount / this.getExchangeRate();
              }
              
              const foreignCurrencyAfterBalance = foreignCurrencyBalance + foreignCurrencyAmount;
              
              // 检查外币上限
              if (foreignCurrencyThreshold.max_threshold && foreignCurrencyAfterBalance > foreignCurrencyThreshold.max_threshold) {
                thresholdAlerts.push({
                  type: 'max',
                  level: 'warning',
                  currency: this.foreignCurrency,
                                      message: `${this.$t('exchange.after_transaction')}${this.getCurrencyName(this.foreignCurrency)}${this.$t('exchange.balance_will_exceed')}${this.$t('exchange.max_threshold')} ${foreignCurrencyThreshold.max_threshold}`,
                  current_balance: foreignCurrencyBalance,
                  after_balance: foreignCurrencyAfterBalance,
                  threshold_value: foreignCurrencyThreshold.max_threshold
                });
              }
            }
          }
        } else {
          // 卖出外币时，外币会减少，检查外币下限；本币会增加，检查本币上限
          // 1. 检查外币下限（银行支出外币）
          const foreignCurrencyAlertResponse = await balanceService.getAlertStatus(foreignCurrencyId);
          if (foreignCurrencyAlertResponse.data.success) {
            const foreignCurrencyAlertInfo = foreignCurrencyAlertResponse.data.alert_info;
            const foreignCurrencyBalanceResponse = await balanceService.getCurrentBalance(foreignCurrencyId);
            if (foreignCurrencyBalanceResponse.data.success && foreignCurrencyAlertInfo.threshold_info) {
              const foreignCurrencyBalance = foreignCurrencyBalanceResponse.data.balance;
              const foreignCurrencyThreshold = foreignCurrencyAlertInfo.threshold_info;
              
              // 计算外币变化金额
              let foreignCurrencyAmount;
              if (checkCurrencyId === foreignCurrencyId) {
                // 如果检查的就是外币，transactionAmount就是外币金额
                foreignCurrencyAmount = transactionAmount;
              } else {
                // 如果检查的是本币，需要转换为外币金额
                foreignCurrencyAmount = transactionAmount / this.getExchangeRate();
              }
              
              const foreignCurrencyAfterBalance = foreignCurrencyBalance - foreignCurrencyAmount;
              
              // 检查外币下限
              if (foreignCurrencyThreshold.min_threshold && foreignCurrencyAfterBalance < foreignCurrencyThreshold.min_threshold) {
                thresholdAlerts.push({
                  type: 'min',
                  level: 'critical',
                  currency: this.foreignCurrency,
                                      message: `${this.$t('exchange.after_transaction')}${this.getCurrencyName(this.foreignCurrency)}${this.$t('exchange.balance_will_below')}${this.$t('exchange.min_threshold')} ${foreignCurrencyThreshold.min_threshold}`,
                  current_balance: foreignCurrencyBalance,
                  after_balance: foreignCurrencyAfterBalance,
                  threshold_value: foreignCurrencyThreshold.min_threshold
                });
              }
            }
          }
          
          // 2. 检查本币上限（银行增加本币）
          const baseCurrencyAlertResponse = await balanceService.getAlertStatus(baseCurrencyId);
          if (baseCurrencyAlertResponse.data.success) {
            const baseCurrencyAlertInfo = baseCurrencyAlertResponse.data.alert_info;
            const baseCurrencyBalanceResponse = await balanceService.getCurrentBalance(baseCurrencyId);
            if (baseCurrencyBalanceResponse.data.success && baseCurrencyAlertInfo.threshold_info) {
              const baseCurrencyBalance = baseCurrencyBalanceResponse.data.balance;
              const baseCurrencyThreshold = baseCurrencyAlertInfo.threshold_info;
              
              // 计算本币变化金额
              let baseCurrencyAmount;
              if (checkCurrencyId === baseCurrencyId) {
                // 如果检查的就是本币，transactionAmount就是本币金额
                baseCurrencyAmount = transactionAmount;
              } else {
                // 如果检查的是外币，需要转换为本币金额
                baseCurrencyAmount = transactionAmount * this.getExchangeRate();
              }
              
              const baseCurrencyAfterBalance = baseCurrencyBalance + baseCurrencyAmount;
              
              // 检查本币上限
              if (baseCurrencyThreshold.max_threshold && baseCurrencyAfterBalance > baseCurrencyThreshold.max_threshold) {
                thresholdAlerts.push({
                  type: 'max',
                  level: 'warning',
                  currency: this.baseCurrency,
                                      message: `${this.$t('exchange.after_transaction')}${this.getCurrencyName(this.baseCurrency)}${this.$t('exchange.balance_will_exceed')}${this.$t('exchange.max_threshold')} ${baseCurrencyThreshold.max_threshold}`,
                  current_balance: baseCurrencyBalance,
                  after_balance: baseCurrencyAfterBalance,
                  threshold_value: baseCurrencyThreshold.max_threshold
                });
              }
            }
          }
        }
        
        // 确定检查的币种信息
        let checkedCurrencyCode, checkedCurrencyName;
        if (this.exchangeMode === 'sell_foreign') {
          // 客户卖出外币：检查本币余额
          checkedCurrencyCode = this.baseCurrency;
          checkedCurrencyName = this.baseCurrencyName;
        } else {
          // 客户买入外币：检查外币库存
          checkedCurrencyCode = this.foreignCurrency;
          checkedCurrencyName = this.foreignCurrencyName;
        }
        
        console.log('=== 余额检查结果 ===');
        console.log('交易模式:', this.exchangeMode);
        console.log('检查币种:', checkedCurrencyCode, checkedCurrencyName);
        console.log('需要金额:', transactionAmount);
        console.log('当前余额:', currentBalance);
        console.log('余额充足:', sufficient);
        
        return {
          sufficient,
          current_balance: currentBalance,
          after_balance: currentBalance - transactionAmount,
          threshold_alerts: thresholdAlerts,
          currency_code: checkedCurrencyCode,
          currency_name: checkedCurrencyName
        };
        
      } catch (error) {
        console.error('余额检查失败:', error);
        return null;
      }
    },
    
    // 获取汇率用于计算
    getExchangeRate() {
      const rateObject = this.fetchRateForPair(this.foreignCurrency);
      if (rateObject) {
        return this.exchangeMode === 'sell_foreign' ? 
          parseFloat(rateObject.buy_rate) : 
          parseFloat(rateObject.sell_rate);
      }
      return 1;
    },
    

    
    // 显示余额检查结果
    displayBalanceCheckResult(checkResult) {
      if (!checkResult) return '';
      
      console.log('🎨 显示余额检查结果:');
      console.log('🎨 - checkResult:', checkResult);
      console.log('🎨 - exchangeMode:', this.exchangeMode);
      console.log('🎨 - sufficient:', checkResult.sufficient);
      
      let messages = [];
      
      // 余额不足的错误信息
      if (!checkResult.sufficient) {
        const requiredAmount = checkResult.current_balance - checkResult.after_balance; // 实际需要的金额
        const shortfallAmount = requiredAmount - checkResult.current_balance; // 缺少的金额
        
        console.log('🎨 计算金额:');
        console.log('🎨 - requiredAmount:', requiredAmount);
        console.log('🎨 - shortfallAmount:', shortfallAmount);
        console.log('🎨 - current_balance:', checkResult.current_balance);
        
        // 根据交易模式生成更准确的提示信息
        let errorMessage = '';
        console.log('🎨 判断交易模式:', this.exchangeMode);
        if (this.exchangeMode === 'sell_foreign') {
          console.log('🎨 执行sell_foreign分支 - 客户卖出外币，银行需要支付本币');
          // 买入外币场景：需要支付本币
          errorMessage = `<div class="text-danger">
            <i class="fas fa-exclamation-triangle me-1"></i><strong>${checkResult.currency_name}${this.$t('exchange.insufficient_balance')}：</strong><br/>
            ${this.$t('exchange.need_pay_amount')} <strong>${this.formatAmount(requiredAmount)} ${checkResult.currency_code}</strong>，<br/>
            ${this.$t('exchange.current_balance_amount')} <strong>${this.formatAmount(checkResult.current_balance)} ${checkResult.currency_code}</strong>，<br/>
            ${this.$t('exchange.shortage_amount')} <strong>${this.formatAmount(shortfallAmount)} ${checkResult.currency_code}</strong>
          </div>`;
        } else {
          console.log('🎨 执行buy_foreign分支 - 客户买入外币，银行需要出库外币');
          // 卖出外币场景：需要足够的外币库存
          errorMessage = `<div class="text-danger">
            <i class="fas fa-exclamation-triangle me-1"></i><strong>${checkResult.currency_name}${this.$t('exchange.insufficient_stock')}：</strong><br/>
            ${this.$t('exchange.need_amount')} <strong>${this.formatAmount(requiredAmount)} ${checkResult.currency_code}</strong>，<br/>
            ${this.$t('exchange.current_stock_amount')} <strong>${this.formatAmount(checkResult.current_balance)} ${checkResult.currency_code}</strong>，<br/>
            ${this.$t('exchange.missing_amount')} <strong>${this.formatAmount(shortfallAmount)} ${checkResult.currency_code}</strong>
          </div>`;
        }
        
        messages.push(errorMessage);
      }
      
      // 阈值警告信息
      checkResult.threshold_alerts.forEach(alert => {
        // 阈值警告使用灰绿色背景，与余额不足的红色背景区分
        const iconClass = alert.level === 'critical' ? 'fa-exclamation-triangle text-warning' : 'fa-exclamation-circle text-info';
        const alertClass = 'threshold-warning'; // 使用专门的CSS类
        const levelText = alert.level === 'critical' ? this.$t('exchange.threshold_exceeded') : this.$t('exchange.threshold_warning');
        messages.push(`<div class="${alertClass}"><i class="fas ${iconClass} me-1"></i><strong>${levelText}：</strong>${alert.message}</div>`);
      });
      
      return messages.join('');
    },
    setExchangeMode(mode) {
      this.exchangeMode = mode;
      
      // 清空输入的金额数据
      this.inputAmount = null;
      this.targetAmount = null;
      this.amountType = '';
      
      // 更新步骤状态
      this.updateCurrentStep();
      this.refreshAll();
    },
    toggleAmountInput(type) {
      this.amountType = type;
      
      if (type === 'have') {
        this.targetAmount = null;
        this.inputAmount = null; // 清空输入框
        // 自动聚焦到输入金额字段
        this.$nextTick(() => {
          const inputElement = document.getElementById('input_amount');
          if (inputElement) {
            inputElement.focus();
            inputElement.value = ''; // 清空显示值
          }
        });
      } else if (type === 'want') {
        this.inputAmount = null;
        this.targetAmount = null; // 清空输入框
        // 自动聚焦到目标金额字段
        this.$nextTick(() => {
          const targetElement = document.getElementById('input_amount');
          if (targetElement) {
            targetElement.focus();
            targetElement.value = ''; // 清空显示值
          }
        });
      }
      
      this.resultDisplay = '';
    },
    async calculateExchange() {
      this.resultDisplay = '';
      console.log('🚨🚨🚨 用户点击了计算按钮，开始计算兑换...');
      console.log('🚨 当前状态:');
      console.log('🚨 - amountType:', this.amountType);
      console.log('🚨 - exchangeMode:', this.exchangeMode);
      console.log('🚨 - inputAmount:', this.inputAmount);
      console.log('🚨 - targetAmount:', this.targetAmount);

      // 重置大额交易选择状态
      this.resetExchangeTypeSelection();
      this.pendingTriggers = [];
      this.currentTrigger = null;
      this.activeTriggerReportType = null;
      this.activeTriggerMessage = '';
      this.lastTriggerData = null;
      
      if (!this.amountType || 
          (this.amountType === 'have' && (this.inputAmount === null || this.inputAmount <= 0)) || 
          (this.amountType === 'want' && (this.targetAmount === null || this.targetAmount <= 0))) {
        this.resultDisplay = this.$t('exchange.enter_valid_amount');
        return;
      }
      
      const rateObject = this.fetchRateForPair(this.foreignCurrency);
      if (!rateObject) {
        this.resultDisplay = this.$t('exchange.rate_unavailable');
        return;
      }

      // 根据网点买卖外币的角度选择汇率
      const relevantRate = this.exchangeMode === 'sell_foreign' ? 
        rateObject.buy_rate : // 网点买入外币（客户卖出外币）时使用买入汇率
        rateObject.sell_rate; // 网点卖出外币（客户买入外币）时使用卖出汇率
      if (!relevantRate) {
        this.resultDisplay = this.$t('exchange.rate_unavailable');
        return;
      }

      // 确定源币种和目标币种
      const fromCurrCode = this.exchangeMode === 'sell_foreign' ? 
        this.foreignCurrency : this.baseCurrency;
      const toCurrCode = this.exchangeMode === 'sell_foreign' ? 
        this.baseCurrency : this.foreignCurrency;

      
      let fromAmount, toAmount;
      
      if (this.amountType === 'have') {
        fromAmount = parseFloat(this.inputAmount);
        if (this.exchangeMode === 'sell_foreign') {
          // 网点买入外币：外币金额 * 买入汇率 = 本币金额
          // 使用字符串计算保持精度
          const preciseAmount = (fromAmount * parseFloat(relevantRate)).toFixed(4);
          toAmount = Math.round(parseFloat(preciseAmount) * 100) / 100;
        } else {
          // 网点卖出外币：本币金额 / 卖出汇率 = 外币金额
          const preciseAmount = (fromAmount / parseFloat(relevantRate)).toFixed(4);
          toAmount = Math.round(parseFloat(preciseAmount) * 100) / 100;
        }
        this.targetAmount = toAmount;
      } else {
        toAmount = parseFloat(this.targetAmount);
        if (this.exchangeMode === 'sell_foreign') {
          // 网点买入外币：本币金额 / 买入汇率 = 外币金额
          const preciseAmount = (toAmount / parseFloat(relevantRate)).toFixed(4);
          fromAmount = Math.round(parseFloat(preciseAmount) * 100) / 100;
        } else {
          // 网点卖出外币：外币金额 * 卖出汇率 = 本币金额
          const preciseAmount = (toAmount * parseFloat(relevantRate)).toFixed(4);
          fromAmount = Math.round(parseFloat(preciseAmount) * 100) / 100;
        }
        this.inputAmount = fromAmount;
      }

      // 使用新的优化提示词格式
              this.resultDisplay = this.generateOptimizedPrompt(fromAmount, toAmount);
      
      // 保存计算出的金额用于语音播报
      this.calculatedInputAmount = fromAmount;
      this.calculatedTargetAmount = toAmount;
      
      // 调试信息：确保currentPromptText被正确设置
      console.log('🔊 计算完成后 - currentPromptText:', this.currentPromptText);
      console.log('🔊 计算完成后 - 保存的金额:', fromAmount, toAmount);

      // 保存验证数据
      const validateData = {
        fromCurrency: fromCurrCode,
        toCurrency: toCurrCode,
        fromAmount: parseFloat(fromAmount.toFixed(fromCurrCode === 'JPY' ? 0 : 2)),
        toAmount: parseFloat(toAmount.toFixed(toCurrCode === 'JPY' ? 0 : 2)),
        rate: parseFloat(relevantRate).toFixed(4),
        exchangeMode: this.exchangeMode,
        amountType: this.amountType
      };
      
      console.log('计算阶段 - 验证数据:', JSON.stringify(validateData, null, 2));
      
      try {
        await rateService.validateExchangeTransaction(validateData);
        console.log('余额验证通过');
        // 保存验证通过的数据
        this.lastValidatedData = validateData;
        
        // 新增：顾客支付模式下，计算完成后检查余额和阈值
        console.log('💳 检查是否需要进行余额检查...');
        console.log('amountType:', this.amountType);
        
        if (this.amountType === 'have') {
          console.log('✅✅✅ 顾客支付模式，需要检查余额');
          console.log('📊📊📊 计算数据 - fromAmount:', fromAmount, 'toAmount:', toAmount);
          console.log('📊📊📊 exchangeMode:', this.exchangeMode);
          
          // 根据交易模式确定要检查的金额
          let checkAmount;
          if (this.exchangeMode === 'buy_foreign') {
            // 客户买入外币（选择"卖出美元"）：网点出库外币，检查外币库存
            checkAmount = toAmount; // toAmount是客户获得的外币
            console.log('🏦 网点出库外币金额:', checkAmount, this.foreignCurrency);
          } else if (this.exchangeMode === 'sell_foreign') {
            // 客户卖出外币（选择"买入美元"）：网点需要支付本币给客户，检查本币余额
            // 在"顾客有外币"模式下，fromAmount是客户的外币，toAmount是网点需要支付的本币
            checkAmount = toAmount; // toAmount是网点需要支付给客户的本币金额
            console.log('🏦 网点需要支付本币金额:', checkAmount, this.baseCurrency);
            console.log('🏦 客户提供的外币金额:', fromAmount, this.foreignCurrency);
          } else {
            console.error('❌ 未知交易模式，跳过余额检查');
            checkAmount = null;
          }
          
                               if (checkAmount) {
            console.log('🔍 开始调用余额检查方法...');
            const balanceCheckResult = await this.checkBalanceAndThreshold(checkAmount);
            console.log('🔍 余额检查结果:', balanceCheckResult);
            if (balanceCheckResult) {
              // 重要修复：更新组件的balanceCheckResult属性
              this.balanceCheckResult = balanceCheckResult;
              
              const balanceMessage = this.displayBalanceCheckResult(balanceCheckResult);
              if (balanceMessage) {
                // 如果有余额或阈值问题，添加到现有的结果显示中
                this.resultDisplay += `<div class="mt-3 balance-check-after-calculation">
                  <div class="mb-2"><i class="fas fa-info-circle me-1"></i><strong>${this.$t('exchange.balance_check')}：</strong></div>
                  ${balanceMessage}
                </div>`;
              } else if (balanceCheckResult.sufficient && balanceCheckResult.threshold_alerts.length === 0) {
                // 余额充足且无阈值警告，添加确认信息
                this.resultDisplay += `<div class="mt-2 text-success balance-check-after-calculation">
                  <i class="fas fa-check-circle me-1"></i>${this.$t('exchange.balance_sufficient')}
                </div>`;
              }
            }
          }
         } else {
           console.log('⚠️ 非顾客支付模式，跳过余额检查');
         }
        
        // 新增：计算完成后检查用途限额
        this.checkPurposeLimit();

        // 新增：检查并处理大额交易（200万本币阈值）
        this.checkAndHandleLargeAmount();

        this.updateCurrentStep();
        
        // 新增：计算完成后自动触发语音播报（如果启用了语音功能）
        if (this.canSpeak) {
            console.log('🔊 计算完成，准备自动播放语音提示');
            // 延迟一点时间确保界面更新完成
            setTimeout(() => {
                this.speakPrompt();
            }, 500);
        }
      } catch (error) {
        console.error('余额验证失败:', error);
        const errorMessage = this.translateApiError(error.response?.data?.message) || this.$t('exchange.insufficient_balance_cannot_exchange');
        this.resultDisplay = `<div class="text-danger">${errorMessage}</div>`;
        // 清空计算结果
        this.targetAmount = null;
        this.inputAmount = null;
      }
    },
    submitExchange() {
      if (!this.resultDisplay || this.resultDisplay.startsWith(this.$t('exchange.calculation_error')) || this.resultDisplay.startsWith(this.$t('exchange.enter_valid_amount'))) {
        alert(this.$t('exchange.calculate_first'));
        return;
      }
      
      this.showConfirmation = true;
    },
    async handleConfirm() {
      console.log('确认交易 - 开始');

      if (this.shouldShowExchangeType && this.exchangeType === 'asset_backed' && !this.selectedFundingSource) {
        alert(this.$t('exchange.select_funding_source'))
        return
      }

      // 检查数据是否与上次验证时一致
      const currentData = {
        fromCurrency: this.exchangeMode === 'sell_foreign' ? this.foreignCurrency : this.baseCurrency,
        toCurrency: this.exchangeMode === 'sell_foreign' ? this.baseCurrency : this.foreignCurrency,
        fromAmount: this.inputAmount,
        toAmount: this.targetAmount,
        rate: this.lastValidatedData.rate, // 使用已经格式化好的汇率
        exchangeMode: this.exchangeMode,
        amountType: this.amountType,
        exchangeType: this.exchangeType || 'normal',
        fundingSource: this.selectedFundingSource || '',
        address: this.customerAddress
      };

      console.log('确认阶段 - 当前数据:', JSON.stringify(currentData, null, 2));
      console.log('确认阶段 - 上次验证数据:', JSON.stringify(this.lastValidatedData, null, 2));

      // 检查关键数据是否发生变化
      const keyFields = ['fromCurrency', 'toCurrency', 'fromAmount', 'toAmount', 'rate', 'exchangeMode'];
      const changes = keyFields.filter(field =>
        JSON.stringify(this.lastValidatedData[field]) !== JSON.stringify(currentData[field])
      );

      if (changes.length > 0) {
        console.warn('警告：以下字段与上次验证通过时不一致:', changes);
        // 重新验证
        try {
          await rateService.validateExchangeTransaction(currentData);
          console.log('重新验证通过');
          this.lastValidatedData = currentData;
        } catch (error) {
          console.error('重新验证失败:', error);
          alert(error.response?.data?.message || this.$t('exchange.validation_failed_please_recalculate'));
          return;
        }
      }

      const transactionData = {
        ...currentData,
        customerName: this.customerName,
        customerId: this.customerId,
        // 新增：用途和备注信息
        purpose: this.selectedPurpose ? this.purposeOptions.find(p => p.id == this.selectedPurpose)?.purpose_name : '',
        remarks: this.customerRemarks,
        address: this.customerAddress,
        // 新增：本币信息
        baseCurrency: this.baseCurrency,
        baseCurrencyName: this.baseCurrencyName
      };

      // ===== 新增：已审核预约的金额验证 =====
      if (this.reservationStatus && this.reservationStatus.status === 'approved') {
        const localAmount = this.exchangeMode === 'sell_foreign' ? this.targetAmount : this.inputAmount;
        const approvedAmount = this.reservationStatus.approved_amount;
        
        if (localAmount > approvedAmount) {
          alert(`交易金额超出批准额度！\n\n本次交易：${localAmount.toLocaleString()} THB\n批准金额：${approvedAmount.toLocaleString()} THB\n超出金额：${(localAmount - approvedAmount).toLocaleString()} THB\n\n请调整交易金额或联系管理员`);
          return;
        }
        
        // 金额符合，继续交易，记录预约ID
        transactionData.reservation_id = this.reservationStatus.reservation_id;
        transactionData.reservation_no = this.reservationStatus.reservation_no;
        console.log('已通过预约验证，预约ID:', this.reservationStatus.reservation_id);
      }
      
      // ===== AMLO/BOT触发检查（仅对无预约或首次交易） =====
      if (this.customerId && this.customerId.trim() && !this.reservationStatus) {
        try {
          console.log('开始AMLO/BOT触发检查...');

          const baseAmountRaw = this.exchangeMode === 'sell_foreign' ? this.targetAmount : this.inputAmount
          const baseAmount = parseFloat(baseAmountRaw || 0)
          const triggerData = {
            total_amount: baseAmount,
            currency_code: this.foreignCurrency,
            customer_id: this.customerId,
            exchange_type: this.exchangeType || 'normal',
            funding_source: this.selectedFundingSource || null,
            asset_value: this.exchangeType === 'asset_mortgage' ? baseAmount : null
          }

          const reportTypes = ['AMLO-1-01']
          if (triggerData.exchange_type === 'asset_mortgage') {
            reportTypes.push('AMLO-1-02')
          }
          if (triggerData.funding_source) {
            reportTypes.push('AMLO-1-03')
          }

          const triggerResults = []
          let customerStats = {}

          for (const reportType of reportTypes) {
            const response = await repformService.checkTrigger({
              report_type: reportType,
              data: triggerData,
              branch_id: this.userInfo.branch_id
            })
            console.log('触发检查响应', reportType, response.data)

            if (response.data.success) {
              if (response.data.customer_stats) {
                customerStats = response.data.customer_stats
              }
              const amloTrigger = response.data.triggers?.amlo
              if (amloTrigger) {
                triggerResults.push({
                  ...amloTrigger,
                  report_type: reportType
                })
              }
            }
          }

          this.triggerCheckResult = {
            triggers: triggerResults,
            customer_stats: customerStats,
            bot: this.triggerCheckResult?.bot || null
          }

          const blockingTriggers = triggerResults.filter(item => item.triggered && item.allow_continue === false)
          const nonBlockingTriggers = triggerResults.filter(item => item.triggered && item.allow_continue !== false)

          nonBlockingTriggers.forEach(item => {
            const locale = this.$i18n?.locale || 'zh-CN'
            let message = item.message_cn || item.message_en || item.message_th
            if (locale === 'en-US') {
              message = item.message_en || message
            } else if (locale === 'th-TH') {
              message = item.message_th || message
            }
            if (message) {
              alert(message)
            }
          })

          this.pendingTriggers = blockingTriggers

          if (blockingTriggers.length > 0) {
            this.prepareReservationModalForTrigger(blockingTriggers[0], triggerData)
            this.loading.transaction = false
            return
          }
        } catch (error) {
          console.error('触发检查失败:', error)
        }
      }
      
// ===== 触发检查结束 =====

      this.loading.transaction = true;
      this.error.transaction = null;

      try {
        const response = await rateService.executeExchangeTransaction(transactionData);
        console.log('确认交易 - 响应:', response.data);

        if (response.data.success) {
          this.transactionSuccess = true;
          this.transactionDetails = response.data.transaction;

          // 新增：如果有阈值警告，创建交易报警记录
          await this.createTransactionAlertsIfNeeded(response.data.transaction);

          // ===== 新增：BOT静默生成逻辑 =====
          if (this.triggerCheckResult && this.triggerCheckResult.triggers?.bot?.triggered) {
            try {
              console.log('BOT触发，开始静默生成报表...');

              const transaction = response.data.transaction;
              const reportDate = new Date().toISOString().split('T')[0];

              const botData = {
                transaction_id: transaction.id,
                report_date: reportDate,
                json_data: {
                  transaction_no: transaction.transaction_no,
                  customer_id: this.customerId,
                  customer_name: this.customerName,
                  currency_code: this.foreignCurrency,
                  direction: this.exchangeMode === 'sell_foreign' ? 'buy' : 'sell',
                  foreign_amount: transaction.foreign_amount,
                  local_amount: transaction.local_amount,
                  exchange_rate: transaction.exchange_rate,
                  transaction_time: transaction.transaction_time,
                  exchange_type: this.selectedPurpose || 'normal',
                  funding_source: 'other'
                }
              };

              // 根据交易方向调用不同的API
              let botReportType = ''
              if (this.exchangeMode === 'sell_foreign') {
                // 客户卖出外币 = 银行买入外币
                await botService.saveBuyFX(botData);
                botReportType = 'BOT_BuyFX'
                console.log('BOT买入外币报表已生成');
              } else {
                // 客户买入外币 = 银行卖出外币
                await botService.saveSellFX(botData);
                botReportType = 'BOT_SellFX'
                console.log('BOT卖出外币报表已生成');
              }
              
              // 显示BOT报表生成提示
              setTimeout(() => {
                alert(this.$t('compliance.botReportGenerated', { type: botReportType }))
              }, 500)
            } catch (error) {
              console.error('BOT报表生成失败:', error);
              // BOT生成失败不影响交易，只记录日志
            }
          }
          // ===== BOT静默生成逻辑结束 =====

          this.resetForm(true);  // 重置表单但保留交易成功信息
        } else {
          alert(this.translateApiError(response.data.message) || this.$t('exchange.transaction_failed'));
        }
      } catch (error) {
        console.error('确认交易失败:', error);
        this.error.transaction = error.response?.data?.message || this.$t('exchange.transaction_failed');
        alert(this.error.transaction);
      } finally {
        this.loading.transaction = false;
      }
    },
    handleCancel() {
      this.showConfirmation = false;
    },
    // 处理预约提交成功
    handleReservationSubmitted(result) {
      console.log('预约提交成功:', result);

      // 显示成功消息
      alert(this.$t('reservation.submission_success') + '\n' +
            this.$t('reservation.reservation_no') + ': ' + result.reservation_no + '\n' +
            this.$t('reservation.please_wait_approval'));

      // 关闭确认对话框
      this.showConfirmation = false;

      // 重置表单
      this.resetForm(false);

      // 隐藏预约模态框
      this.showReservationModal = false;
      this.reservationTransactionData = null;
      this.triggerCheckResult = null;
    },
    // 处理预约取消
    handleReservationCancelled() {
      console.log('预约已取消');

      // 隐藏预约模态框
      this.showReservationModal = false;
      this.reservationTransactionData = null;
      this.pendingTriggers.shift();

      if (this.pendingTriggers.length > 0) {
        this.prepareReservationModalForTrigger(this.pendingTriggers[0], this.lastTriggerData)
      } else {
        this.pendingTriggers = []
        this.currentTrigger = null
        this.activeTriggerReportType = null
        this.activeTriggerMessage = ''
        this.triggerCheckResult = null
        this.lastTriggerData = null
      }

      // 保持确认对话框打开，用户可以修改数据后重试
    },
    // 加载客户历史统计
    async fetchCustomerHistory(customerId, days = 30) {
      const trimmedId = (customerId || '').trim();
      if (!trimmedId) {
        this.customerStats = null;
        return;
      }

      this.customerHistoryLoading = true;

      try {
        const response = await repformService.getCustomerHistory(trimmedId, days);
        if (response?.data?.success) {
          this.customerStats = response.data.data || response.data;
        } else {
          this.customerStats = null;
        }
      } catch (error) {
        console.error('加载客户信息失败:', error);
        this.customerStats = null;
      } finally {
        this.customerHistoryLoading = false;
      }
    },

    async onReservationStatusUpdated(reservation, error) {
      const trimmedId = (this.customerId || '').trim();
      const statusKey = reservation
        ? `${reservation.status}:${reservation.reservation_id || reservation.id || reservation.reservation_no || 'unknown'}`
        : (error ? `error:${Date.now()}` : 'none');

            if (reservation && this.lastReservationStatusCode !== statusKey) {
        if (reservation.status === 'approved') {
          this.$message?.({
            message: `Reservation approved.<br/>Limit: ${Number(reservation.approved_amount || 0).toLocaleString()} THB.<br/>Please ensure the transaction stays within the approved amount.`,
            type: 'success',
            duration: 5000,
            dangerouslyUseHTMLString: true
          });
        } else if (reservation.status === 'pending') {
          this.$message?.({
            message: `Reservation review in progress.<br/>Report type: ${reservation.report_type}<br/>Submitted at: ${reservation.created_at}<br/><br/>The exchange is blocked until approval.`,
            type: 'warning',
            duration: 8000,
            dangerouslyUseHTMLString: true
          });
        } else if (reservation.status === 'rejected') {
          const reason = reservation.rejection_reason || 'No rejection reason provided.';
          this.$message?.({
            message: `Reservation rejected.<br/>Reason: ${reason}<br/>Reviewer: ${reservation.auditor_name || 'unknown'}`,
            type: 'error',
            duration: 8000,
            dangerouslyUseHTMLString: true
          });
        }
      }

      if (!reservation && !error && trimmedId && this.lastReservationStatusCode !== statusKey) {
        this.$message?.({
          message: 'No active reservation found for this customer. You may proceed with the standard process.',
          type: 'info',
          duration: 3000
        });
      }

      this.lastReservationStatusCode = reservation ? statusKey : (error ? null : 'none');

      if (error) {
        this.customerStats = null;
        return;
      }

      if (trimmedId) {
        await this.fetchCustomerHistory(trimmedId, 30);
      } else {
        this.customerStats = null;
      }
    },

    onReservationStatusCleared() {
      this.lastReservationStatusCode = null;
      this.customerStats = null;
    },
    // 显示客户历史交易查询弹窗
    showCustomerHistoryModal() {
      if (!this.customerId || !this.customerId.trim()) {
        alert(this.$t('exchange.please_enter_customer_id'));
        return;
      }

      this.showCustomerHistory = true;
      this.$nextTick(() => {
        if (this.$refs.customerHistoryModal) {
          this.$refs.customerHistoryModal.show();
        }
      });
    },
    resetForm(preserveTransaction = false) {
      this.pendingTriggers = []
      this.currentTrigger = null
      this.activeTriggerReportType = null
      this.activeTriggerMessage = ''
      this.lastTriggerData = null
      // 保存当前交易信息作为上一笔交易（在重置之前）
      if (preserveTransaction && this.lastValidatedData && this.transactionDetails) {
        this.lastTransaction = {
          transactionNo: this.transactionDetails.transaction_no,  // 新增：保存单据号
          type: this.exchangeMode === 'sell_foreign' ? 'buy' : 'sell', // 从银行角度
          currency: this.foreignCurrency,
          customerPaid: this.lastValidatedData.fromAmount,
          customerCurrency: this.lastValidatedData.fromCurrency,
          bankPaid: this.lastValidatedData.toAmount,
          bankCurrency: this.lastValidatedData.toCurrency,
          date: this.transactionDetails.transaction_date,
          time: this.transactionDetails.transaction_time
        };
        
        // 保存到本地存储，确保页面刷新后仍然显示
        localStorage.setItem('lastTransaction', JSON.stringify(this.lastTransaction));
      }
      
      // 重置所有表单字段
      this.foreignCurrency = ''; // 修改：重置外币选择为空
      this.exchangeMode = ''; // 修改：重置交易模式为空
      this.amountType = ''; // 修改：重置金额类型为空，不设默认值
      this.inputAmount = null;
      this.targetAmount = null;
      this.resultDisplay = '';
      this.customerName = '';
      this.customerId = '';
      this.customerAddress = '';
      this.customerRemarks = '';  // 新增：重置备注
      this.showConfirmation = false;
      this.selectedFundingSource = '';
      
      // 新增：重置用途选择相关字段
      this.resetPurposeSelection();
      this.currentStep = 1;
      
      
      // 只有在不保留交易信息时才重置交易相关状态
      if (!preserveTransaction) {
        this.transactionSuccess = false;
        this.transactionDetails = {};
        this.lastValidatedData = null;
        // 注意：不再清空lastTransaction，让它始终保持显示
      }
    },
    closeTransaction() {
      // 关闭交易成功对话框，但保持上一笔交易信息显示
      this.transactionSuccess = false;
      this.transactionDetails = {};
      this.lastValidatedData = null;
      this.showConfirmation = false;
      
      // 重置表单字段，但不影响上一笔交易显示
      this.foreignCurrency = '';
      this.exchangeMode = '';
      this.amountType = ''; // 修改：重置为空，不设默认值
      this.inputAmount = null;
      this.targetAmount = null;
      this.resultDisplay = '';
      this.customerName = '';
      this.customerId = '';
      this.customerAddress = '';
      this.customerRemarks = '';
      this.selectedFundingSource = '';
      this.resetPurposeSelection();
      this.currentStep = 1;
      
      // 清除外币余额信息和报警状态
      this.updateSelectedCurrencyInfo();
    },
    // 新增：创建交易报警记录（如果需要）
    prepareReservationModalForTrigger(trigger, triggerData) {
      this.currentTrigger = trigger || null
      this.activeTriggerReportType = trigger?.report_type || 'AMLO-1-01'
      this.activeTriggerMessage = trigger?.message_cn || trigger?.message_en || trigger?.message_th || ''
      this.lastTriggerData = triggerData

      const fromAmount = this.exchangeMode === 'sell_foreign' ? this.inputAmount : this.calculatedInputAmount || this.inputAmount
      const toAmount = this.exchangeMode === 'sell_foreign' ? this.targetAmount : this.calculatedTargetAmount || this.targetAmount

      this.reservationTransactionData = {
        customerId: this.customerId,
        customerName: this.customerName,
        customerCountryCode: this.userInfo?.branch?.country_code || 'TH',
        currencyId: this.currencyIdMap[this.foreignCurrency],
        currencyCode: this.foreignCurrency,
        exchangeMode: this.exchangeMode,
        fromCurrency: this.exchangeMode === 'sell_foreign' ? this.foreignCurrency : this.baseCurrency,
        toCurrency: this.exchangeMode === 'sell_foreign' ? this.baseCurrency : this.foreignCurrency,
        fromAmount: fromAmount,
        toAmount: toAmount,
        rate: this.lastValidatedData?.rate || this.rateDisplay,
        exchangeType: this.exchangeType || 'normal',
        fundingSource: this.selectedFundingSource || null,
        assetValue: triggerData?.asset_value || null,
        purpose: this.selectedPurpose ? (this.purposeOptions.find(p => p.id == this.selectedPurpose)?.purpose_name || '') : '',
        remarks: this.customerRemarks,
        address: this.customerAddress
      }

      this.showReservationModal = true
    },

    async createTransactionAlertsIfNeeded(transactionData) {
      try {
        // 检查是否有阈值警告需要记录
        if (!this.balanceCheckResult || !this.balanceCheckResult.threshold_alerts || 
            this.balanceCheckResult.threshold_alerts.length === 0) {
          console.log('🔍 无阈值警告，跳过创建交易报警记录');
          return;
        }

        console.log('🚨 检测到阈值警告，开始创建交易报警记录:', this.balanceCheckResult.threshold_alerts);

        // 为每个阈值警告创建报警记录
        for (const alert of this.balanceCheckResult.threshold_alerts) {
          const alertData = {
            // 从currencyIdMap获取currency_id
            currency_id: this.currencyIdMap[alert.currency] || null,
            alert_type: this.mapAlertType(alert.type),
            alert_level: this.mapAlertLevel(alert.type),
            current_balance: alert.current_balance || 0,
            threshold_value: alert.threshold || 0,
            transaction_amount: parseFloat(transactionData.amount) || 0,
            transaction_type: transactionData.type === 'buy' ? 'buy_foreign' : 'sell_foreign',
            after_balance: alert.after_balance || alert.current_balance || 0,
            message: alert.message || `${alert.currency}${alert.type === 'exceed' ? this.$t('exchange.threshold_exceeded') : this.$t('exchange.threshold_warning')}`
          };

          console.log('🚨 创建报警记录数据:', alertData);

          // 调用创建交易报警的API
          const alertResponse = await fetch('/api/transaction-alerts/create', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify(alertData)
          });

          if (alertResponse.ok) {
            const alertResult = await alertResponse.json();
            console.log('✅ 交易报警记录创建成功:', alertResult);
          } else {
            const errorData = await alertResponse.json();
            console.error('❌ 创建交易报警记录失败:', errorData);
          }
        }
      } catch (error) {
        console.error('❌ 创建交易报警记录异常:', error);
        // 不阻断主流程，只记录错误
      }
    },

    // 新增：映射报警类型
    mapAlertType(alertType) {
      const typeMap = {
        'exceed': 'threshold_exceed',
        'warning': 'threshold_warning',
        'low_balance': 'low_balance',
        'high_balance': 'high_balance'
      };
      return typeMap[alertType] || 'threshold_warning';
    },

    // 新增：映射报警级别
    mapAlertLevel(alertType) {
      const levelMap = {
        'exceed': 'high',
        'warning': 'medium',
        'low_balance': 'high',
        'high_balance': 'medium'
      };
      return levelMap[alertType] || 'medium';
    },

    async printReceipt() {
      try {
        // 获取当前语言
        const currentLanguage = this.getCurrentLang();
        
        // 使用统一打印服务 - 硬编码格式
        const config = PrintService.getExchangeConfig(
          this.transactionDetails, 
          this.$toast, 
          false,  // 使用硬编码格式，不需要HTML模式
          currentLanguage  // 传递当前语言
        );
        const success = await printService.printPDF(config);
        
        if (success) {
          console.log('外币兑换凭证打印完成 (硬编码格式)');
          // 显示成功消息（如果没有自动显示的话）
          if (this.$toast && typeof this.$toast.success === 'function') {
            this.$toast.success(this.$t('common.print_success'));
          }
        }
      } catch (error) {
        console.error('外币兑换打印失败:', error);
        if (this.$toast && typeof this.$toast.error === 'function') {
          this.$toast.error(this.$t('common.print_failed') + ': ' + (error.message || this.$t('common.error')));
        }
      }
    },
    
    getFundingSourceLabel(option) {
      if (!option) return ''
      const locale = this.$i18n?.locale || 'zh-CN'
      if (locale === 'en-US') return option.source_name_en || option.source_code || ''
      if (locale === 'th-TH') return option.source_name_th || option.source_code || ''
      return option.source_name_cn || option.source_code || ''
    },

    async fetchCurrencies() {
      try {
        this.loading.currencies = true;
        this.error.currencies = null;
        
        console.log('开始获取可兑换外币列表...');
        const response = await rateService.getAvailableCurrencies(true);
        console.log('获取到的响应:', response);
        
        if (response.data.success) {
          const currencies = response.data.currencies;
          console.log('可兑换的外币列表:', currencies);
          
          // 将currencies数组转换为{ USD: '美元', EUR: '欧元', ... }的对象形式
          this.availableCurrencies = {};
          this.currencyIdMap = {}; // 新增：清空并重新填充ID映射
          this.currencyNames = {}; // 新增：清空并重新填充多语言名称映射
          currencies.forEach(c => {
            // 存储完整的币种数据，包括custom_flag_filename
            this.availableCurrencies[c.currency_code] = {
              currency_name: c.currency_name,
              custom_flag_filename: c.custom_flag_filename,
              flag_code: c.flag_code
            };
            this.currencyIdMap[c.currency_code] = c.id; // 修复：使用id而不是currency_id
            // 新增：存储多语言名称
            if (c.currency_names) {
              this.currencyNames[c.currency_code] = c.currency_names;
            }
          });
          
          // 重要修复：确保本币也被包含在currencyIdMap中
          if (!this.currencyIdMap[this.baseCurrency]) {
            console.warn(`⚠️ 本币 ${this.baseCurrency} 不在可兑换币种列表中，需要单独获取ID`);
            await this.ensureBaseCurrencyInMap();
          }
          
          console.log('可兑换外币:', this.availableCurrencies);
          console.log('币种ID映射:', this.currencyIdMap); // 新增：调试日志
          
          // 更新本币名称
          if (this.availableCurrencies[this.baseCurrency]) {
            this.baseCurrencyName = this.getCurrencyName(this.baseCurrency);
            console.log('更新本币名称:', this.baseCurrencyName);
          }
          
                  // 外币选项现在由CurrencySelect组件直接从API加载
        } else {
          this.error.currencies = this.translateApiError(response.data.message) || this.$t('exchange.get_currencies_failed');
          console.error('获取币种失败:', this.error.currencies);
        }
      } catch (error) {
        console.error('获取币种出错:', error);
        this.error.currencies = this.translateApiError(error.response?.data?.message) || this.$t('exchange.get_currencies_error');
      } finally {
        this.loading.currencies = false;
      }
    },
    async fetchRates() {
      this.loading.rates = true;
      this.error.rates = null;
      
      try {
        // 只获取当日发布的汇率
        const response = await rateService.getCurrentRates(true);
        
        if (response.data.success) {
          // 过滤掉本币的汇率
          this.topRates = response.data.rates
            .filter(rate => rate.currency_code !== this.baseCurrency)
            .map(rate => ({
              currency: rate.currency_code,
              buyRate: rate.buy_rate,
              sellRate: rate.sell_rate
            }));
            
          this.updateRateDisplay();
        } else {
          this.error.rates = this.translateApiError(response.data.message) || this.$t('exchange.get_rates_failed');
          console.error('获取汇率失败:', this.error.rates);
        }
      } catch (error) {
        console.error('获取汇率出错:', error);
        this.error.rates = this.translateApiError(error.response?.data?.message) || this.$t('exchange.get_rates_error');
      } finally {
        this.loading.rates = false;
      }
    },
    async handleForeignCurrencyChange() {
      console.log('handleForeignCurrencyChange 被调用，当前外币:', this.foreignCurrency);
      
      // 新增：根据外币自动匹配语音语言
      this.autoSetVoiceLanguage();
      
      // 新增：更新选中币种信息，触发余额组件更新
      this.updateSelectedCurrencyInfo();
      
      this.updateCurrentStep();
      this.resetPurposeSelection();
      
      // 确保有外币选择时才加载用途选项
      if (this.foreignCurrency) {
        console.log('开始加载用途选项...');
        await this.loadPurposeOptions();
      } else {
        console.log('没有选择外币，清空用途选项');
        this.purposeOptions = [];
      }
      
      this.refreshAll();
    },
    async loadPurposeOptions() {
      if (!this.foreignCurrency) {
        console.log('No foreign currency selected, clearing purpose options');
        this.purposeOptions = [];
        return;
      }
      
      console.log(`=== Loading purpose options for currency: ${this.foreignCurrency} ===`);
      
      try {
        // 使用正确的API路径，不需api前缀因为baseURL已经包含
        console.log('Making API call...');
        const response = await this.$api.get(`/system/purpose-limits/by-currency/${this.foreignCurrency}`);
        
        console.log('=== API Response Details ===');
        console.log('Response status:', response.status);
        console.log('Response data:', response.data);
        
        if (response.data && response.data.success) {
          this.purposeOptions = response.data.purposes || [];
          console.log(`成功加载了${this.purposeOptions.length}个用途选项:`, this.purposeOptions);
          
          if (this.purposeOptions.length === 0) {
            console.warn(`⚠️ 没有找到${this.foreignCurrency}的用途选项`);
          }
        } else {
          console.error('API返回错误或无效的响应结构');
          console.error('Response data:', response.data);
          this.purposeOptions = [];
          // 只在明确有错误消息时显示
          if (response.data?.message) {
            this.$toast?.warning(this.translateApiError(response.data.message));
          }
        }
      } catch (error) {
        console.error('加载用途选项出错:', error);
        
        // 检查是否是权限问题
        if (error.response?.status === 401) {
          console.error('🔒 认证失败 - token可能已过期');
          this.$toast?.error(this.$t('exchange.login_expired_please_relogin'));
        } else if (error.response?.status === 403) {
          console.error('🚫 没有权限访问交易用途设置，请联系管理员');
          this.$toast?.error(this.$t('exchange.no_permission_access_purpose_settings'));
        } else if (error.response?.status === 404) {
          console.warn('🔍 交易用途设置API未找到或该币种没有配置用途限额');
          // 404可能是正常的，表示该币种没有配置用途限额
          console.log('No purpose limits configured for this currency, which is normal');
        } else {
          console.error('🌐 网络或其他错误:', error.message);
          // 只在404错误时显示错误提示
          this.$toast?.error(this.$t('exchange.load_purpose_options_failed'));
        }
        
        this.purposeOptions = [];
      }
      
      console.log('=== Final purpose options state ===');
      console.log('purposeOptions length:', this.purposeOptions.length);
      console.log('purposeOptions:', this.purposeOptions);
    },
    handlePurposeChange() {
      const selectedPurpose = this.purposeOptions.find(p => p.id == this.selectedPurpose);
      if (selectedPurpose) {
        this.purposeMessage = selectedPurpose.display_message;
        this.purposeMaxAmount = selectedPurpose.max_amount;
      } else {
        this.purposeMessage = '';
        this.purposeMaxAmount = 0;
      }
      
      this.updateCurrentStep();
      this.checkPurposeLimit();
    },
    checkPurposeLimit() {
      if (!this.selectedPurpose || !this.purposeMaxAmount || !this.targetAmount) {
        this.purposeExceeded = false;
        this.purposeWarningMessage = '';
        return;
      }
      
      // 获取顾客得到的外币金额进行限额比较
      let foreignAmount = 0;
      if (this.exchangeMode === 'sell_foreign') {
        // 客户卖出外币，得到本币 - 不需要检查外币限额
        this.purposeExceeded = false;
        this.purposeWarningMessage = '';
        return;
      } else {
        // 客户买入外币，得到外币 - 检查外币限额
        foreignAmount = this.targetAmount;
      }
      
      if (foreignAmount > this.purposeMaxAmount) {
        this.purposeExceeded = true;
        this.purposeWarningMessage = `超出${this.purposeOptions.find(p => p.id == this.selectedPurpose)?.purpose_name}用途限额：最多${this.formatAmount(this.purposeMaxAmount)} ${this.foreignCurrency}`;
      } else {
        this.purposeExceeded = false;
        this.purposeWarningMessage = '';
      }
    },
    resetPurposeSelection() {
      this.selectedPurpose = '';
      this.purposeMessage = '';
      this.purposeMaxAmount = 0;
      this.purposeExceeded = false;
      this.purposeWarningMessage = '';
    },

    // 新增：重置大额交易类型选择
    resetExchangeTypeSelection() {
      this.showExchangeType = false;
      this.exchangeType = null;
      this.selectedFundingSource = '';
    },

    // 新增：检查并处理大额交易
    checkAndHandleLargeAmount() {
      const localAmount = this.calculatedLocalAmount;

      console.log('💰 大额交易检查:', {
        localAmount,
        threshold: this.LARGE_AMOUNT_THRESHOLD,
        baseCurrency: this.baseCurrency
      });

      // 200万本币阈值检查
      if (localAmount > this.LARGE_AMOUNT_THRESHOLD) {
        console.log('⚠️ 检测到大额交易，本币金额:', localAmount);
        this.showExchangeType = true;

        // 如果用户之前没有选择过兑换类型，默认设置为大额兑换
        if (!this.exchangeType) {
          this.exchangeType = 'large_amount';
          console.log('📋 自动设置兑换类型为: large_amount');
        }

        // 在结果显示中添加大额交易提示
        const amountFormatted = this.formatAmount(localAmount);
        const thresholdFormatted = this.formatAmount(this.LARGE_AMOUNT_THRESHOLD);
        const largeAmountNotice = `<div class="mt-2 alert alert-warning py-2">
          <i class="fas fa-exclamation-triangle me-2"></i>
          <strong>${this.$t('exchange.large_amount_notice')}：</strong>
          ${this.$t('exchange.transaction_amount')} <strong>${amountFormatted} ${this.baseCurrency}</strong>
          ${this.$t('exchange.exceeds_threshold')} <strong>${thresholdFormatted} ${this.baseCurrency}</strong>，
          ${this.$t('exchange.please_select_exchange_type')}
        </div>`;

        this.resultDisplay += largeAmountNotice;
      } else {
        console.log('✅ 普通交易，本币金额:', localAmount);
        this.showExchangeType = false;
        this.exchangeType = null;
      }
    },
    updateCurrentStep() {
      let step = 1;
      
      if (this.foreignCurrency) {
        step = 2;
      }
      
      if (this.exchangeMode) {
        step = 3;
      }
      
      if (this.selectedPurpose) {
        step = 4;
      }
      
      if ((this.amountType === 'have' && this.inputAmount > 0) || 
          (this.amountType === 'want' && this.targetAmount > 0)) {
        step = 5;
      }
      
      this.currentStep = step;
    },
    async loadPrintSettings() {
      try {
        const response = await this.$api.get('print-settings/templates');
        if (response.data.success && response.data.settings) {
          // 加载签名设置
          if (response.data.settings.signature_settings) {
          this.signatureSettings = response.data.settings.signature_settings.value;
          }
          
          // 保存完整的打印设置，用于PDF生成
          this.fullPrintSettings = response.data.settings;
          
          console.log('打印设置加载成功:', {
            signature: this.signatureSettings,
            full: this.fullPrintSettings
          });
        } else {
          console.error('打印设置加载失败:', response.data.message);
          this.useDefaultSettings();
        }
      } catch (error) {
        console.error('打印设置加载出错:', error);
        this.useDefaultSettings();
      }
    },
    
    useDefaultSettings() {
        // 使用默认设置
        this.signatureSettings = {
          signature_style: 'double',
          show_date_line: true,
          single_label: '签名/Signature',
                  left_label: this.$t('exchange.customer_signature'),
        right_label: this.$t('exchange.teller_signature')
        };
      
      this.fullPrintSettings = {
        paper_size: { value: { width: 210, height: 297, name: 'A4' } },
        margins: { value: { top: 10, right: 10, bottom: 10, left: 10 } },
        font_settings: { value: { family: 'SimSun', size: 12, bold: false } },
        header_settings: { value: { show_logo: true, show_branch_info: true, title_size: 16, title_bold: true } },
        layout_settings: { value: { line_spacing: 1.2, table_border: true, auto_page_break: true } },
        signature_settings: { value: this.signatureSettings }
      };
      
      console.warn('使用默认打印设置:', this.fullPrintSettings);
    },
    
    // 新增：更新选中币种信息
    async updateSelectedCurrencyInfo() {
      if (this.foreignCurrency && this.availableCurrencies[this.foreignCurrency]) {
        const currencyId = await this.getCurrencyIdByCode(this.foreignCurrency);
        this.selectedForeignCurrencyInfo = {
          id: currencyId,
          currency_code: this.foreignCurrency,
          currency_name: this.availableCurrencies[this.foreignCurrency]
        };
        
        console.log('更新选中币种信息:', this.selectedForeignCurrencyInfo);
      } else {
        this.selectedForeignCurrencyInfo = null;
        console.log('清空选中币种信息');
      }
    },
    
    // 新增：确保本币被包含在currencyIdMap中
    async ensureBaseCurrencyInMap() {
      try {
        console.log(`🔍 获取本币 ${this.baseCurrency} 的ID...`);
        const baseCurrencyId = await this.getCurrencyIdByCode(this.baseCurrency);
        if (baseCurrencyId) {
          this.currencyIdMap[this.baseCurrency] = baseCurrencyId;
          console.log(`✅ 成功获取本币ID: ${this.baseCurrency} -> ${baseCurrencyId}`);
        } else {
          console.error(`❌ 无法获取本币 ${this.baseCurrency} 的ID`);
        }
      } catch (error) {
        console.error(`获取本币ID失败:`, error);
      }
    },
    
    // 新增：根据币种代码获取币种ID
    async getCurrencyIdByCode(currencyCode) {
      if (!currencyCode) return null;
      
      // 首先尝试从已加载的币种数据中查找
      if (this.currencyIdMap && this.currencyIdMap[currencyCode]) {
        console.log(`从缓存获取币种 ${currencyCode} 的ID: ${this.currencyIdMap[currencyCode]}`);
        return this.currencyIdMap[currencyCode];
      }
      
      // 如果缓存中没有，尝试调用API获取
      try {
        console.log(`缓存中没有 ${currencyCode}，尝试从API获取...`);
        const response = await this.$api.get(`/currencies/code/${currencyCode}`);
        
        if (response.data.success && response.data.currency) {
          const currencyId = response.data.currency.id;
          // 更新缓存
          this.currencyIdMap[currencyCode] = currencyId;
          console.log(`从API获取币种 ${currencyCode} 的ID: ${currencyId}`);
          return currencyId;
        } else {
          console.error(`API返回失败，未找到币种 ${currencyCode}`);
          return null;
        }
      } catch (error) {
        console.error(`API获取币种 ${currencyCode} ID失败:`, error);
        return null;
      }
    },
    
    // 新增：处理余额更新事件
    onBalanceUpdated(balanceInfo) {
      this.currentBalanceInfo = balanceInfo;
      console.log('余额信息更新:', balanceInfo);
      
      if (balanceInfo.alert_status && balanceInfo.alert_status.level !== 'normal') {
        console.log('余额报警:', balanceInfo.alert_status.message);
      }
    },
    
    // 新增：检查交易对余额的影响
    async checkTransactionImpact() {
      if (!this.selectedForeignCurrencyInfo || !this.inputAmount || !this.exchangeMode) {
        return;
      }
      
      try {
        const transactionType = this.exchangeMode === 'buy_foreign' ? 'sell' : 'buy';
        const response = await balanceService.checkTransactionImpact({
          currency_id: this.selectedForeignCurrencyInfo.id,
          transaction_amount: this.inputAmount,
          transaction_type: transactionType
        });
        
        if (response.data.success && response.data.impact_analysis.will_trigger_alert) {
          console.log('交易将触发余额报警:', response.data.impact_analysis);
        }
      } catch (error) {
        console.error('检查交易影响失败:', error);
      }
    },
    
    // 新增：初始化语音功能
    initSpeechSynthesis() {
      try {
        // 检查浏览器是否支持语音合成
        if ('speechSynthesis' in window) {
          this.speechSynthesis = window.speechSynthesis;
          
          // 检查语音合成对象是否可用
          if (this.speechSynthesis && typeof this.speechSynthesis.speak === 'function') {
            this.canSpeak = true;
            console.log('🔊 语音合成功能初始化成功');
            
            // 获取可用的语音列表
            const voices = this.speechSynthesis.getVoices();
            console.log('🔊 可用语音数量:', voices.length);
            
            // 显示支持的语音语言
            const supportedLanguages = [...new Set(voices.map(voice => voice.lang.split('-')[0]))];
            console.log('🔊 支持的语音语言:', supportedLanguages);
            
            // 详细记录语音信息
            if (voices.length > 0) {
              console.log('🔊 语音详细信息:');
              voices.forEach((voice, index) => {
                console.log(`🔊 语音 ${index + 1}:`, {
                  name: voice.name,
                  lang: voice.lang,
                  localService: voice.localService,
                  default: voice.default,
                  voiceURI: voice.voiceURI
                });
              });
            }
            
            // 检查是否有中文语音
            const chineseVoices = voices.filter(voice => voice.lang.startsWith('zh'));
            if (chineseVoices.length === 0) {
              console.warn('🔊 警告：没有找到中文语音，可能影响中文播报效果');
            } else {
              console.log('🔊 找到中文语音:', chineseVoices.map(v => v.name));
            }
            
          } else {
            console.warn('🔊 语音合成对象不可用');
            this.canSpeak = false;
          }
        } else {
          console.warn('🔊 浏览器不支持语音合成 API');
          this.canSpeak = false;
        }
        
        // 语音语言独立于系统语言，默认从中文开始
        this.currentLanguage = 'zh';
        console.log('🔊 初始化语音播报语言:', this.currentLanguage, '独立于系统语言');
        
        // 记录浏览器信息
        console.log('🔊 浏览器信息:', {
          userAgent: navigator.userAgent,
          language: navigator.language,
          languages: navigator.languages,
          platform: navigator.platform
        });
        
      } catch (error) {
        console.error('🔊 语音功能初始化失败:', error);
        console.error('🔊 错误堆栈:', error.stack);
        this.canSpeak = false;
      }
    },
    
    // 新增：翻译API错误消息
    translateApiError(errorMessage) {
      if (typeof errorMessage !== 'string') {
        return errorMessage;
      }
      
      // 检查是否包含翻译键模式（如：泰铢insufficient_balance,need_pay_amount...）
      const translationKeyPattern = /([A-Za-z]+)(insufficient_balance|insufficient_stock|need_pay_amount|current_balance_amount|shortage_amount|need_amount|current_stock_amount|missing_amount)/;
      const match = errorMessage.match(translationKeyPattern);
      
      if (match) {
        const currencyName = match[1];
        const translationKey = match[2];
        
        // 构建翻译后的消息
        let translatedMessage = '';
        
        // 根据翻译键构建消息
        if (translationKey === 'insufficient_balance') {
          translatedMessage = `${currencyName}${this.$t('exchange.insufficient_balance')}：`;
        } else if (translationKey === 'insufficient_stock') {
          translatedMessage = `${currencyName}${this.$t('exchange.insufficient_stock')}：`;
        }
        
        // 解析其他翻译键
        const parts = errorMessage.split(',');
        for (const part of parts) {
          if (part.includes('need_pay_amount')) {
            const amount = part.split(' ')[1];
            const currency = part.split(' ')[2];
            translatedMessage += `<br/>${this.$t('exchange.need_pay_amount')} <strong>${amount} ${currency}</strong>，`;
          } else if (part.includes('current_balance_amount')) {
            const amount = part.split(' ')[1];
            const currency = part.split(' ')[2];
            translatedMessage += `<br/>${this.$t('exchange.current_balance_amount')} <strong>${amount} ${currency}</strong>，`;
          } else if (part.includes('shortage_amount')) {
            const amount = part.split(' ')[1];
            const currency = part.split(' ')[2];
            translatedMessage += `<br/>${this.$t('exchange.shortage_amount')} <strong>${amount} ${currency}</strong>`;
          } else if (part.includes('need_amount')) {
            const amount = part.split(' ')[1];
            const currency = part.split(' ')[2];
            translatedMessage += `<br/>${this.$t('exchange.need_amount')} <strong>${amount} ${currency}</strong>，`;
          } else if (part.includes('current_stock_amount')) {
            const amount = part.split(' ')[1];
            const currency = part.split(' ')[2];
            translatedMessage += `<br/>${this.$t('exchange.current_stock_amount')} <strong>${amount} ${currency}</strong>，`;
          } else if (part.includes('missing_amount')) {
            const amount = part.split(' ')[1];
            const currency = part.split(' ')[2];
            translatedMessage += `<br/>${this.$t('exchange.missing_amount')} <strong>${amount} ${currency}</strong>`;
          }
        }
        
        return translatedMessage;
      }
      
      // 如果是简单的错误代码，使用翻译
      if (this.$t(`exchange.${errorMessage}`)) {
        return this.$t(`exchange.${errorMessage}`);
      }
      
      // 否则返回原始消息
      return errorMessage;
    },
    
    // 新增：获取中文货币名称（用于语音播放）
    getChineseCurrencyName(currencyCode) {
      // 硬编码中文货币名称映射
      const chineseCurrencyNames = {
        'CNY': '人民币',
        'USD': '美元',
        'EUR': '欧元',
        'JPY': '日元',
        'GBP': '英镑',
        'THB': '泰铢',
        'KRW': '韩元',
        'HKD': '港币',
        'SGD': '新加坡元',
        'AUD': '澳元',
        'CAD': '加元',
        'CHF': '瑞士法郎',
        'SEK': '瑞典克朗',
        'NOK': '挪威克朗',
        'DKK': '丹麦克朗',
        'RUB': '俄罗斯卢布',
        'INR': '印度卢比',
        'BRL': '巴西雷亚尔',
        'MXN': '墨西哥比索',
        'ZAR': '南非兰特',
        'TRY': '土耳其里拉',
        'PLN': '波兰兹罗提',
        'CZK': '捷克克朗',
        'HUF': '匈牙利福林',
        'RON': '罗马尼亚列伊',
        'BGN': '保加利亚列弗',
        'HRK': '克罗地亚库纳',
        'RSD': '塞尔维亚第纳尔',
        'UAH': '乌克兰格里夫纳',
        'BYN': '白俄罗斯卢布',
        'KZT': '哈萨克斯坦坚戈',
        'UZS': '乌兹别克斯坦索姆',
        'KGS': '吉尔吉斯斯坦索姆',
        'TJS': '塔吉克斯坦索莫尼',
        'TMT': '土库曼斯坦马纳特',
        'AZN': '阿塞拜疆马纳特',
        'GEL': '格鲁吉亚拉里',
        'AMD': '亚美尼亚德拉姆',
        'ALL': '阿尔巴尼亚列克',
        'MKD': '北马其顿第纳尔',
        'MNT': '蒙古图格里克',
        'LAK': '老挝基普',
        'KHR': '柬埔寨瑞尔',
        'MMK': '缅甸元',
        'VND': '越南盾',
        'IDR': '印尼盾',
        'MYR': '马来西亚林吉特',
        'PHP': '菲律宾比索',
        'BDT': '孟加拉塔卡',
        'LKR': '斯里兰卡卢比',
        'NPR': '尼泊尔卢比',
        'PKR': '巴基斯坦卢比',
        'AFN': '阿富汗尼',
        'IRR': '伊朗里亚尔',
        'IQD': '伊拉克第纳尔',
        'JOD': '约旦第纳尔',
        'LBP': '黎巴嫩镑',
        'SAR': '沙特里亚尔',
        'AED': '阿联酋迪拉姆',
        'QAR': '卡塔尔里亚尔',
        'KWD': '科威特第纳尔',
        'BHD': '巴林第纳尔',
        'OMR': '阿曼里亚尔',
        'YER': '也门里亚尔',
        'SCR': '塞舌尔卢比',
        'MVR': '马尔代夫拉菲亚',
        'BTN': '不丹努尔特鲁姆',
        'MOP': '澳门元'
      };
      
      return chineseCurrencyNames[currencyCode] || currencyCode;
    },
    
    // 新增：生成中文语音提示（独立于系统语言）
    generateChinesePrompt() {
      if (!this.foreignCurrency) {
        return '';
      }
      
      let promptText = '';
      
      // 获取有效的金额值 - 优先使用计算后的金额
      const inputAmount = this.calculatedInputAmount || this.inputAmount;
      const targetAmount = this.calculatedTargetAmount || this.targetAmount;
      
      console.log('🔊 generateChinesePrompt - 金额检查:');
      console.log('🔊 - calculatedInputAmount:', this.calculatedInputAmount);
      console.log('🔊 - calculatedTargetAmount:', this.calculatedTargetAmount);
      console.log('🔊 - inputAmount:', inputAmount, '类型:', typeof inputAmount);
      console.log('🔊 - targetAmount:', targetAmount, '类型:', typeof targetAmount);
      console.log('🔊 - currentPromptText:', this.currentPromptText);
      
      // 如果两个金额都为空或为0，尝试从currentPromptText中提取信息
      if ((!inputAmount || inputAmount === 0) && (!targetAmount || targetAmount === 0) && this.currentPromptText) {
        // 尝试从currentPromptText中解析出金额信息
        const text = this.currentPromptText;
        console.log('🔊 尝试从currentPromptText解析金额:', text);
        
        // 使用正则表达式提取数字和币种信息
        const amountPattern = /(\d+(?:\.\d+)?)/g;
        const amounts = text.match(amountPattern);
        
        if (amounts && amounts.length >= 2) {
          // 如果找到了两个数字，假设第一个是输入金额，第二个是目标金额
          const extractedInputAmount = parseFloat(amounts[0]);
          const extractedTargetAmount = parseFloat(amounts[1]);
          
          console.log('🔊 从文本中提取的金额:', extractedInputAmount, extractedTargetAmount);
          
          // 使用提取的金额生成完整的中文提示
          if (this.exchangeMode === 'buy_foreign') {
            if (this.amountType === 'have') {
              promptText = `您有${extractedInputAmount}的${this.getChineseCurrencyName(this.baseCurrency)}，可以兑换${extractedTargetAmount}的${this.getChineseCurrencyName(this.foreignCurrency)}`;
            } else {
              promptText = `您要${extractedTargetAmount}的${this.getChineseCurrencyName(this.foreignCurrency)}，需要支付${extractedInputAmount}的${this.getChineseCurrencyName(this.baseCurrency)}`;
            }
          } else {
            if (this.amountType === 'have') {
              promptText = `您有${extractedInputAmount}的${this.getChineseCurrencyName(this.foreignCurrency)}，可以兑换${extractedTargetAmount}的${this.getChineseCurrencyName(this.baseCurrency)}`;
            } else {
              promptText = `您要${extractedTargetAmount}的${this.getChineseCurrencyName(this.baseCurrency)}，需要支付${extractedInputAmount}的${this.getChineseCurrencyName(this.foreignCurrency)}`;
            }
          }
          return promptText;
        } else {
          // 如果无法提取金额，使用简化提示
          if (this.exchangeMode === 'buy_foreign') {
            if (this.amountType === 'have') {
              promptText = `您有本币，可以兑换${this.getChineseCurrencyName(this.foreignCurrency)}`;
            } else {
              promptText = `您要${this.getChineseCurrencyName(this.foreignCurrency)}`;
            }
          } else {
            if (this.amountType === 'have') {
              promptText = `您有${this.getChineseCurrencyName(this.foreignCurrency)}，可以兑换本币`;
            } else {
              promptText = `您要本币`;
            }
          }
          return promptText;
        }
      }
      
      // 如果只有一个金额，生成简化提示
      if (inputAmount && inputAmount > 0 && (!targetAmount || targetAmount === 0)) {
        if (this.exchangeMode === 'buy_foreign') {
          if (this.amountType === 'have') {
            promptText = `您有${inputAmount}的${this.getChineseCurrencyName(this.baseCurrency)}，可以兑换${this.getChineseCurrencyName(this.foreignCurrency)}`;
          } else {
            promptText = `您要${this.getChineseCurrencyName(this.foreignCurrency)}，需要支付${inputAmount}的${this.getChineseCurrencyName(this.baseCurrency)}`;
          }
        } else {
          if (this.amountType === 'have') {
            promptText = `您有${inputAmount}的${this.getChineseCurrencyName(this.foreignCurrency)}，可以兑换本币`;
          } else {
            promptText = `您要本币，需要支付${inputAmount}的${this.getChineseCurrencyName(this.foreignCurrency)}`;
          }
        }
        return promptText;
      }
      
      if ((!inputAmount || inputAmount === 0) && targetAmount && targetAmount > 0) {
        if (this.exchangeMode === 'buy_foreign') {
          if (this.amountType === 'have') {
            promptText = `您有本币，可以兑换${targetAmount}的${this.getChineseCurrencyName(this.foreignCurrency)}`;
          } else {
            promptText = `您要${targetAmount}的${this.getChineseCurrencyName(this.foreignCurrency)}`;
          }
        } else {
          if (this.amountType === 'have') {
            promptText = `您有${this.getChineseCurrencyName(this.foreignCurrency)}，可以兑换${targetAmount}的本币`;
          } else {
            promptText = `您要${targetAmount}的本币`;
          }
        }
        return promptText;
      }
      
      // 完整的兑换信息
      if (this.exchangeMode === 'buy_foreign') {
        // S方式：银行卖出外币（客户买入外币）
        if (this.amountType === 'have') {
          // S1状态：客户有本币，要外币
          promptText = `您有${inputAmount}的${this.getChineseCurrencyName(this.baseCurrency)}，可以兑换${targetAmount}的${this.getChineseCurrencyName(this.foreignCurrency)}`;
        } else {
          // S2状态：客户要外币，问需要多少本币
          promptText = `您要${targetAmount}的${this.getChineseCurrencyName(this.foreignCurrency)}，需要支付${inputAmount}的${this.getChineseCurrencyName(this.baseCurrency)}`;
        }
      } else {
        // B方式：银行买入外币（客户卖出外币）
        if (this.amountType === 'have') {
          // B1状态：客户有外币，要本币
          promptText = `您有${inputAmount}的${this.getChineseCurrencyName(this.foreignCurrency)}，可以兑换${targetAmount}的${this.getChineseCurrencyName(this.baseCurrency)}`;
        } else {
          // B2状态：客户要本币，问需要多少外币
          promptText = `您要${targetAmount}的${this.getChineseCurrencyName(this.baseCurrency)}，需要支付${inputAmount}的${this.getChineseCurrencyName(this.foreignCurrency)}`;
        }
      }
      
      return promptText;
    },
    
    // 新增：生成优化的提示词
    generateOptimizedPrompt(fromAmount, toAmount) {
      let promptText = '';
      
      if (this.exchangeMode === 'buy_foreign') {
        // S方式：银行卖出外币（客户买入外币）
        if (this.amountType === 'have') {
          // S1状态：客户有本币，要外币
          promptText = this.$t('exchange.you_have_can_exchange', {
            fromAmount,
            fromCurrency: this.getCurrencyDisplayName(this.baseCurrency),
            toAmount,
            toCurrency: this.getCurrencyDisplayName(this.foreignCurrency)
          });
        } else {
          // S2状态：客户要外币，问需要多少本币
          promptText = this.$t('exchange.you_want_need_pay', {
            toAmount,
            toCurrency: this.getCurrencyDisplayName(this.foreignCurrency),
            fromAmount,
            fromCurrency: this.getCurrencyDisplayName(this.baseCurrency)
          });
        }
      } else {
        // B方式：银行买入外币（客户卖出外币）
        if (this.amountType === 'have') {
          // B1状态：客户有外币，要本币
          promptText = this.$t('exchange.you_have_can_exchange', {
            fromAmount,
            fromCurrency: this.getCurrencyDisplayName(this.foreignCurrency),
            toAmount,
            toCurrency: this.getCurrencyDisplayName(this.baseCurrency)
          });
        } else {
          // B2状态：客户要本币，问需要多少外币
          promptText = this.$t('exchange.you_want_need_pay', {
            toAmount,
            toCurrency: this.getCurrencyDisplayName(this.baseCurrency),
            fromAmount,
            fromCurrency: this.getCurrencyDisplayName(this.foreignCurrency)
          });
        }
      }
      
      this.currentPromptText = promptText;
      return promptText;
    },
    
    // 新增：语音播报功能
    speakPrompt() {
      // 重新检查语音功能是否可用
      if (!this.speechSynthesis || !this.canSpeak) {
        console.log('🔊 语音功能未启用，尝试重新初始化...');
        this.initSpeechSynthesis();
        
        if (!this.canSpeak) {
          console.log('🔊 语音功能初始化失败，跳过播报');
          return;
        }
      }
      
      // 确保语音合成对象可用
      if (!this.speechSynthesis || typeof this.speechSynthesis.speak !== 'function') {
        console.error('🔊 语音合成对象不可用');
        return;
      }
      
      this.speechSynthesis.cancel();
      
      // 获取要播放的文本 - 只播放核心兑换信息，过滤内部信息
      let textToSpeak = '';
      
      // 调试信息
      console.log('🔊 语音播报调试信息:');
      console.log('🔊 - 当前语音语言:', this.currentLanguage);
      console.log('🔊 - 外币币种:', this.foreignCurrency);
      console.log('🔊 - 输入金额:', this.inputAmount);
      console.log('🔊 - 目标金额:', this.targetAmount);
      console.log('🔊 - 交易模式:', this.exchangeMode);
      console.log('🔊 - 金额类型:', this.amountType);
      console.log('🔊 - 当前提示文本:', this.currentPromptText);
      
      // 根据当前语音语言选择文本源
      if (this.currentLanguage === 'zh') {
        // 中文语音使用专门的中文提示文本
        textToSpeak = this.generateChinesePrompt();
        console.log('🔊 生成的中文语音文本:', textToSpeak);
      } else if (this.currentPromptText) {
        // 其他语言使用核心提示文本，这是给客户的主要信息
        textToSpeak = this.currentPromptText;
        console.log('🔊 使用当前提示文本:', textToSpeak);
      } else if (this.resultDisplay) {
        // 从resultDisplay中提取主要兑换信息，过滤掉内部检查信息
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = this.resultDisplay;
        const fullText = tempDiv.textContent || tempDiv.innerText;
        
        // 过滤掉内部信息（余额检查、阈值警告等）
        const lines = fullText.split('\n').map(line => line.trim()).filter(line => line.length > 0);
        const filteredLines = lines.filter(line => {
          // 过滤掉不需要播报的内容
          return !line.includes(this.$t('exchange.balance_check')) &&
                 !line.includes(this.$t('exchange.threshold_exceeded')) &&
                 !line.includes(this.$t('exchange.threshold_warning')) &&
                 !line.includes(this.$t('exchange.insufficient_balance')) &&
                 !line.includes(this.$t('exchange.insufficient_stock')) &&
                 !line.includes(this.$t('exchange.realtime_balance_check')) &&
                 !line.includes(this.$t('exchange.after_transaction')) &&
                 !line.includes(this.$t('exchange.min_threshold')) &&
                 !line.includes(this.$t('exchange.max_threshold')) &&
                 !line.includes(this.$t('exchange.balance_sufficient'));
        });
        
        // 取第一行作为主要信息（通常是兑换提示）
        textToSpeak = filteredLines.length > 0 ? filteredLines[0] : '';
        
        // 清理文本，移除多余空白字符
        textToSpeak = textToSpeak.replace(/\s+/g, ' ').trim();
        console.log('🔊 从resultDisplay提取的文本:', textToSpeak);
      }
      
      if (!textToSpeak) {
        console.log('🔊 没有可播放的文本内容');
        return;
      }
      
      console.log('🔊 最终将要播放的文本:', textToSpeak);
      
      const utterance = new SpeechSynthesisUtterance();
      
      // 根据语音语言设置播放参数 - 支持更多语言
      const languageSettings = {
        // 主要语言
        'zh': { lang: 'zh-CN', rate: 0.8, pitch: 1, text: this.generateChinesePrompt() },
        'en': { lang: 'en-US', rate: 0.9, pitch: 1, text: this.translateToEnglish(textToSpeak) },
        'th': { lang: 'th-TH', rate: 0.7, pitch: 1, text: this.translateToThai(textToSpeak) },
        'ja': { lang: 'ja-JP', rate: 0.8, pitch: 1, text: this.translateToJapanese(textToSpeak) },
        'ko': { lang: 'ko-KR', rate: 0.8, pitch: 1, text: this.translateToKorean(textToSpeak) },
        'fr': { lang: 'fr-FR', rate: 0.9, pitch: 1, text: this.translateToFrench(textToSpeak) },
        'de': { lang: 'de-DE', rate: 0.9, pitch: 1, text: this.translateToGerman(textToSpeak) },
        'es': { lang: 'es-ES', rate: 0.9, pitch: 1, text: this.translateToSpanish(textToSpeak) },
        'ru': { lang: 'ru-RU', rate: 0.8, pitch: 1, text: this.translateToRussian(textToSpeak) },
        'ar': { lang: 'ar-SA', rate: 0.7, pitch: 1, text: this.translateToArabic(textToSpeak) }
      };
      
      // 获取语言设置，如果不存在则使用英语
      let settings = languageSettings[this.currentLanguage];
      if (!settings) {
        console.log(`🔊 语言 ${this.currentLanguage} 未找到，回退到英语`);
        settings = languageSettings['en'];
      }
      
      // 对于其他语言，动态调用翻译函数
      if (!settings) {
        const translationFunctions = {
          'sv': this.translateToSwedish,
          'no': this.translateToNorwegian,
          'da': this.translateToDanish,
          'pt': this.translateToPortuguese,
          'tr': this.translateToTurkish,
          'pl': this.translateToPolish,
          'cs': this.translateToCzech,
          'hu': this.translateToHungarian,
          'ro': this.translateToRomanian,
          'bg': this.translateToBulgarian,
          'hr': this.translateToCroatian,
          'sr': this.translateToSerbian,
          'uk': this.translateToUkrainian,
          'be': this.translateToBelarusian,
          'hi': this.translateToHindi,
          'vi': this.translateToVietnamese,
          'id': this.translateToIndonesian,
          'ms': this.translateToMalay,
          'tl': this.translateToTagalog,
          'bn': this.translateToBengali,
          'si': this.translateToSinhala,
          'ne': this.translateToNepali,
          'ur': this.translateToUrdu,
          'ps': this.translateToPashto,
          'fa': this.translateToPersian,
          'he': this.translateToHebrew,
          'af': this.translateToEnglish,
          'kk': this.translateToEnglish,
          'uz': this.translateToEnglish,
          'ky': this.translateToEnglish,
          'tg': this.translateToEnglish,
          'tk': this.translateToEnglish,
          'az': this.translateToEnglish,
          'ka': this.translateToEnglish,
          'hy': this.translateToEnglish,
          'sq': this.translateToEnglish,
          'mk': this.translateToEnglish,
          'mn': this.translateToEnglish,
          'lo': this.translateToEnglish,
          'km': this.translateToEnglish,
          'my': this.translateToEnglish
        };
        
        const translationFunction = translationFunctions[this.currentLanguage];
        if (translationFunction) {
          const translatedText = translationFunction.call(this, textToSpeak);
          settings = {
            lang: `${this.currentLanguage}-${this.currentLanguage.toUpperCase()}`,
            rate: 0.8,
            pitch: 1,
            text: translatedText
          };
        } else {
          // 默认回退到英语
          settings = languageSettings['en'];
        }
      }
      
      // 调试信息
      console.log('🔊 当前语音语言:', this.currentLanguage);
      console.log('🔊 中文语音文本:', this.generateChinesePrompt());
      console.log('🔊 英文语音文本:', this.translateToEnglish(textToSpeak));
      
      // 检查浏览器是否支持该语言
      const voices = this.speechSynthesis.getVoices();
      const supportedVoices = voices.filter(voice => 
        voice.lang.startsWith(settings.lang.split('-')[0])
      );
      
      if (supportedVoices.length === 0) {
        console.log(`🔊 浏览器不支持语言 ${settings.lang}，回退到英语`);
        settings = languageSettings['en'];
      }
      
      utterance.text = settings.text;
      utterance.lang = settings.lang;
      utterance.rate = settings.rate;
      utterance.pitch = settings.pitch;
      
      console.log('🔊 语音设置:', {
        text: utterance.text,
        lang: utterance.lang,
        rate: utterance.rate,
        pitch: utterance.pitch
      });
      
      // 添加错误处理
      try {
        // 检查语音合成是否可用
        if (!this.speechSynthesis || !this.speechSynthesis.speak) {
          console.error('🔊 语音合成功能不可用');
          return;
        }
        
        // 检查文本是否为空
        if (!utterance.text || utterance.text.trim() === '') {
          console.warn('🔊 语音播报文本为空');
          return;
        }
        
        // 添加语音事件监听
        utterance.onstart = () => {
          console.log('🔊 语音播报开始');
        };
        
        utterance.onend = () => {
          console.log('🔊 语音播报结束');
        };
        
        utterance.onerror = (event) => {
          console.error('🔊 语音播报错误:', event.error);
          console.error('🔊 错误详情:', {
            error: event.error,
            message: event.message,
            elapsedTime: event.elapsedTime,
            charIndex: event.charIndex,
            name: event.name
          });
        };
        
        utterance.onpause = () => {
          console.log('🔊 语音播报暂停');
        };
        
        utterance.onresume = () => {
          console.log('🔊 语音播报恢复');
        };
        
        // 执行语音播报
        this.speechSynthesis.speak(utterance);
        
        // 设置超时检查，如果语音播报没有在合理时间内开始，提供用户反馈
        setTimeout(() => {
          if (!this.speechSynthesis.speaking && !this.speechSynthesis.pending) {
            console.warn('🔊 语音播报可能没有正常启动，提供用户反馈');
            this.showVoiceFeedback();
          }
        }, 2000);
        
      } catch (error) {
        console.error('🔊 语音播报执行失败:', error);
        console.error('🔊 错误堆栈:', error.stack);
        this.showVoiceFeedback();
      }
    },
    
    // 新增：显示语音功能反馈
    showVoiceFeedback() {
      // 创建一个临时的提示信息
      const feedbackMessage = this.$t('exchange.voice_playback_failed') || '语音播报失败，请检查浏览器设置或尝试手动点击播放按钮';
      
      // 在界面上显示提示
      if (this.resultDisplay && !this.resultDisplay.includes('text-danger')) {
        const originalDisplay = this.resultDisplay;
        this.resultDisplay = `<div class="text-warning">🔊 ${feedbackMessage}</div>`;
        
        // 3秒后恢复原始显示
        setTimeout(() => {
          this.resultDisplay = originalDisplay;
        }, 3000);
      }
      
      console.log('🔊 显示语音功能反馈:', feedbackMessage);
    },
    
    // 新增：根据外币自动匹配语音语言
    autoSetVoiceLanguage() {
      if (!this.foreignCurrency) {
        return;
      }
      
      // 币种到语音语言的映射 - 优化版本
      const currencyToLanguage = {
        // 主要货币 - 使用官方语言
        'USD': 'en',  // 美元 - 英语
        'EUR': 'de',  // 欧元 - 德语
        'JPY': 'ja',  // 日元 - 日语
        'GBP': 'en',  // 英镑 - 英语
        'THB': 'th',  // 泰铢 - 泰语
        'KRW': 'ko',  // 韩元 - 韩语
        'CNY': 'zh',  // 人民币 - 中文
        'HKD': 'zh',  // 港币 - 中文（香港使用粤语，但Web Speech API主要支持普通话）
        'SGD': 'en',  // 新加坡元 - 英语
        'AUD': 'en',  // 澳元 - 英语
        'CAD': 'en',  // 加元 - 英语
        'CHF': 'de',  // 瑞士法郎 - 德语
        'SEK': 'sv',  // 瑞典克朗 - 瑞典语
        'NOK': 'no',  // 挪威克朗 - 挪威语
        'DKK': 'da',  // 丹麦克朗 - 丹麦语
        'RUB': 'ru',  // 俄罗斯卢布 - 俄语
        'INR': 'hi',  // 印度卢比 - 印地语
        'BRL': 'pt',  // 巴西雷亚尔 - 葡萄牙语
        'MXN': 'es',  // 墨西哥比索 - 西班牙语
        'ZAR': 'af',  // 南非兰特 - 南非荷兰语
        'TRY': 'tr',  // 土耳其里拉 - 土耳其语
        'PLN': 'pl',  // 波兰兹罗提 - 波兰语
        'CZK': 'cs',  // 捷克克朗 - 捷克语
        'HUF': 'hu',  // 匈牙利福林 - 匈牙利语
        'RON': 'ro',  // 罗马尼亚列伊 - 罗马尼亚语
        'BGN': 'bg',  // 保加利亚列弗 - 保加利亚语
        'HRK': 'hr',  // 克罗地亚库纳 - 克罗地亚语
        'RSD': 'sr',  // 塞尔维亚第纳尔 - 塞尔维亚语
        'UAH': 'uk',  // 乌克兰格里夫纳 - 乌克兰语
        'BYN': 'be',  // 白俄罗斯卢布 - 白俄罗斯语
        'KZT': 'kk',  // 哈萨克斯坦坚戈 - 哈萨克语
        'UZS': 'uz',  // 乌兹别克斯坦索姆 - 乌兹别克语
        'KGS': 'ky',  // 吉尔吉斯斯坦索姆 - 吉尔吉斯语
        'TJS': 'tg',  // 塔吉克斯坦索莫尼 - 塔吉克语
        'TMT': 'tk',  // 土库曼斯坦马纳特 - 土库曼语
        'AZN': 'az',  // 阿塞拜疆马纳特 - 阿塞拜疆语
        'GEL': 'ka',  // 格鲁吉亚拉里 - 格鲁吉亚语
        'AMD': 'hy',  // 亚美尼亚德拉姆 - 亚美尼亚语
        'ALL': 'sq',  // 阿尔巴尼亚列克 - 阿尔巴尼亚语
        'MKD': 'mk',  // 北马其顿第纳尔 - 马其顿语
        'MNT': 'mn',  // 蒙古图格里克 - 蒙古语
        'LAK': 'lo',  // 老挝基普 - 老挝语
        'KHR': 'km',  // 柬埔寨瑞尔 - 高棉语
        'MMK': 'my',  // 缅甸元 - 缅甸语
        'VND': 'vi',  // 越南盾 - 越南语
        'IDR': 'id',  // 印尼盾 - 印尼语
        'MYR': 'ms',  // 马来西亚林吉特 - 马来语
        'PHP': 'tl',  // 菲律宾比索 - 他加禄语
        'BDT': 'bn',  // 孟加拉塔卡 - 孟加拉语
        'LKR': 'si',  // 斯里兰卡卢比 - 僧伽罗语
        'NPR': 'ne',  // 尼泊尔卢比 - 尼泊尔语
        'PKR': 'ur',  // 巴基斯坦卢比 - 乌尔都语
        'AFN': 'ps',  // 阿富汗尼 - 普什图语
        'IRR': 'fa',  // 伊朗里亚尔 - 波斯语
        'IQD': 'ar',  // 伊拉克第纳尔 - 阿拉伯语
        'JOD': 'ar',  // 约旦第纳尔 - 阿拉伯语
        'LBP': 'ar',  // 黎巴嫩镑 - 阿拉伯语
        'SAR': 'ar',  // 沙特里亚尔 - 阿拉伯语
        'AED': 'ar',  // 阿联酋迪拉姆 - 阿拉伯语
        'QAR': 'ar',  // 卡塔尔里亚尔 - 阿拉伯语
        'KWD': 'ar',  // 科威特第纳尔 - 阿拉伯语
        'BHD': 'ar',  // 巴林第纳尔 - 阿拉伯语
        'OMR': 'ar',  // 阿曼里亚尔 - 阿拉伯语
        'YER': 'ar',  // 也门里亚尔 - 阿拉伯语
        'EGP': 'ar',  // 埃及镑 - 阿拉伯语
        'MAD': 'ar',  // 摩洛哥迪拉姆 - 阿拉伯语
        'TND': 'ar',  // 突尼斯第纳尔 - 阿拉伯语
        'DZD': 'ar',  // 阿尔及利亚第纳尔 - 阿拉伯语
        'LYD': 'ar',  // 利比亚第纳尔 - 阿拉伯语
        'SDG': 'ar',  // 苏丹镑 - 阿拉伯语
        'SYP': 'ar',  // 叙利亚镑 - 阿拉伯语
        'ILS': 'he',  // 以色列谢克尔 - 希伯来语
        'PEN': 'es',  // 秘鲁索尔 - 西班牙语
        'CLP': 'es',  // 智利比索 - 西班牙语
        'COP': 'es',  // 哥伦比亚比索 - 西班牙语
        'ARS': 'es',  // 阿根廷比索 - 西班牙语
        'UYU': 'es',  // 乌拉圭比索 - 西班牙语
        'PYG': 'es',  // 巴拉圭瓜拉尼 - 西班牙语
        'BOB': 'es',  // 玻利维亚诺 - 西班牙语
        'VEF': 'es',  // 委内瑞拉玻利瓦尔 - 西班牙语
        'GTQ': 'es',  // 危地马拉格查尔 - 西班牙语
        'HNL': 'es',  // 洪都拉斯伦皮拉 - 西班牙语
        'NIO': 'es',  // 尼加拉瓜科多巴 - 西班牙语
        'CRC': 'es',  // 哥斯达黎加科朗 - 西班牙语
        'PAB': 'es',  // 巴拿马巴波亚 - 西班牙语
        'DOP': 'es',  // 多米尼加比索 - 西班牙语
        'JMD': 'es',  // 牙买加元 - 西班牙语
        'TTD': 'es',  // 特立尼达和多巴哥元 - 西班牙语
        'BBD': 'es',  // 巴巴多斯元 - 西班牙语
        'XCD': 'es',  // 东加勒比元 - 西班牙语
        'GYD': 'es',  // 圭亚那元 - 西班牙语
        'SRD': 'es',  // 苏里南元 - 西班牙语
        'BZD': 'es',  // 伯利兹元 - 西班牙语
        'HTG': 'es',  // 海地古德 - 西班牙语
        'CUP': 'es',  // 古巴比索 - 西班牙语
        'ANG': 'es',  // 荷属安的列斯盾 - 西班牙语
        'AWG': 'es',  // 阿鲁巴弗罗林 - 西班牙语
        'KYD': 'es',  // 开曼群岛元 - 西班牙语
        'BMD': 'es',  // 百慕大元 - 西班牙语
        'FJD': 'en',  // 斐济元 - 英语
        'PGK': 'en',  // 巴布亚新几内亚基那 - 英语
        'SBD': 'en',  // 所罗门群岛元 - 英语
        'VUV': 'en',  // 瓦努阿图瓦图 - 英语
        'WST': 'en',  // 萨摩亚塔拉 - 英语
        'TOP': 'en',  // 汤加潘加 - 英语
        'KID': 'en',  // 基里巴斯元 - 英语
        'TVD': 'en',  // 图瓦卢元 - 英语
        'NZD': 'en',  // 新西兰元 - 英语
        'XPF': 'en',  // 太平洋法郎 - 英语
        'XOF': 'en',  // 西非法郎 - 英语
        'XAF': 'en',  // 中非法郎 - 英语
        'CDF': 'en',  // 刚果法郎 - 英语
        'GHS': 'en',  // 加纳塞地 - 英语
        'NGN': 'en',  // 尼日利亚奈拉 - 英语
        'KES': 'en',  // 肯尼亚先令 - 英语
        'UGX': 'en',  // 乌干达先令 - 英语
        'TZS': 'en',  // 坦桑尼亚先令 - 英语
        'MWK': 'en',  // 马拉维克瓦查 - 英语
        'ZMW': 'en',  // 赞比亚克瓦查 - 英语
        'BWP': 'en',  // 博茨瓦纳普拉 - 英语
        'NAD': 'en',  // 纳米比亚元 - 英语
        'SZL': 'en',  // 斯威士兰里兰吉尼 - 英语
        'LSL': 'en',  // 莱索托洛蒂 - 英语
        'MUR': 'en',  // 毛里求斯卢比 - 英语
        'SCR': 'en',  // 塞舌尔卢比 - 英语
        'MVR': 'en',  // 马尔代夫拉菲亚 - 英语
        'BTN': 'en',  // 不丹努尔特鲁姆 - 英语
        'MOP': 'zh',  // 澳门元 - 中文
        'TWD': 'zh'   // 新台币 - 中文
      };
      
      const matchedLanguage = currencyToLanguage[this.foreignCurrency];
      if (matchedLanguage) {
        this.currentLanguage = matchedLanguage;
        console.log(`外币${this.foreignCurrency}自动匹配语音语言: ${matchedLanguage}`);
      } else {
        // 没有匹配的语言，默认使用英语
        this.currentLanguage = 'en';
        console.log(`外币${this.foreignCurrency}没有匹配的语音语言，默认使用英语`);
      }
    },
    
    // 新增：切换语言 - 支持更多常用语言
    toggleLanguage() {
      const languageCycle = ['zh', 'en', 'th', 'ja', 'ko', 'fr', 'de', 'es', 'ru', 'ar'];
      const currentIndex = languageCycle.indexOf(this.currentLanguage);
      const nextIndex = (currentIndex + 1) % languageCycle.length;
      this.currentLanguage = languageCycle[nextIndex];
      console.log('切换语音语言到:', this.currentLanguage);
    },
    
    // 新增：翻译为英文
    translateToEnglish(chineseText) {
      const translations = {
        '您有': 'You have',
        '您要': 'You want',
        '您需要': 'You need',
        '可以兑换': 'can exchange to',
        '需支付': 'need to pay',
        '需要支付': 'need to pay',
        [this.$t('exchange.after_transaction')]: 'After transaction',
        [this.$t('exchange.balance_will_below') + this.$t('exchange.min_threshold')]: 'balance will be below minimum threshold',
        [this.$t('exchange.balance_will_exceed') + this.$t('exchange.max_threshold')]: 'balance will exceed maximum threshold',
        [this.$t('exchange.threshold_exceeded')]: 'Threshold exceeded',
        [this.$t('exchange.threshold_warning')]: 'Threshold warning',
        [this.$t('exchange.insufficient_balance')]: 'Insufficient balance',
        [this.$t('exchange.insufficient_stock')]: 'Insufficient stock',
        '的': ' ',
        '人民币': 'Chinese Yuan',
        '美元': 'US Dollar',
        '欧元': 'Euro',
        '日元': 'Japanese Yen',
        '英镑': 'British Pound',
        '港币': 'Hong Kong Dollar',
        '泰铢': 'Thai Baht'
      };
      
      let englishText = chineseText;
      for (const [chinese, english] of Object.entries(translations)) {
        englishText = englishText.replace(new RegExp(chinese, 'g'), english);
      }
      
      return englishText;
    },
    // 新增：翻译为泰文
    translateToThai(chineseText) {
      const translations = {
        '您有': 'คุณมี',
        '您要': 'คุณต้องการ',
        '可以兑换': 'สามารถแลกเป็น',
        '需要支付': 'ต้องจ่าย',
        [this.$t('exchange.after_transaction')]: 'หลังจากทำธุรกรรม',
        [this.$t('exchange.balance_will_below') + this.$t('exchange.min_threshold')]: 'ยอดคงเหลือจะต่ำกว่าขีดจำกัดต่ำสุด',
        [this.$t('exchange.balance_will_exceed') + this.$t('exchange.max_threshold')]: 'ยอดคงเหลือจะเกินขีดจำกัดสูงสุด',
        [this.$t('exchange.threshold_exceeded')]: 'เกินขีดจำกัด',
        [this.$t('exchange.threshold_warning')]: 'คำเตือนขีดจำกัด',
        [this.$t('exchange.insufficient_balance')]: 'ยอดคงเหลือไม่เพียงพอ',
        [this.$t('exchange.insufficient_stock')]: 'สต็อกไม่เพียงพอ',
        '的': '',
        '人民币': 'หยวนจีน',
        '美元': 'ดอลลาร์สหรัฐ',
        '欧元': 'ยูโร',
        '日元': 'เยนญี่ปุ่น',
        '英镑': 'ปอนด์อังกฤษ',
        '港币': 'ดอลลาร์ฮ่องกง',
        '泰铢': 'บาทไทย'
      };
      
      let thaiText = chineseText;
      for (const [chinese, thai] of Object.entries(translations)) {
        thaiText = thaiText.replace(new RegExp(chinese, 'g'), thai);
      }
      
      return thaiText;
    },
    
    // 新增：翻译为日语
    translateToJapanese(chineseText) {
      const translations = {
        '您有': 'あなたは持っています',
        '您要': 'あなたは欲しい',
        '可以兑换': '両替できます',
        '需要支付': '支払う必要があります',
        '人民币': '人民元',
        '美元': '米ドル',
        '欧元': 'ユーロ',
        '日元': '日本円',
        '英镑': 'ポンド',
        '港币': '香港ドル',
        '泰铢': 'タイバーツ'
      };
      
      let japaneseText = chineseText;
      for (const [chinese, japanese] of Object.entries(translations)) {
        japaneseText = japaneseText.replace(new RegExp(chinese, 'g'), japanese);
      }
      
      return japaneseText;
    },
    
    // 新增：翻译为韩语
    translateToKorean(chineseText) {
      const translations = {
        '您有': '당신은 가지고 있습니다',
        '您要': '당신은 원합니다',
        '可以兑换': '환전할 수 있습니다',
        '需要支付': '지불해야 합니다',
        '人民币': '중국 위안',
        '美元': '미국 달러',
        '欧元': '유로',
        '日元': '일본 엔',
        '英镑': '영국 파운드',
        '港币': '홍콩 달러',
        '泰铢': '태국 바트'
      };
      
      let koreanText = chineseText;
      for (const [chinese, korean] of Object.entries(translations)) {
        koreanText = koreanText.replace(new RegExp(chinese, 'g'), korean);
      }
      
      return koreanText;
    },
    
    // 新增：翻译为法语
    translateToFrench(chineseText) {
      const translations = {
        '您有': 'Vous avez',
        '您要': 'Vous voulez',
        '可以兑换': 'peut échanger',
        '需要支付': 'doit payer',
        '人民币': 'Yuan chinois',
        '美元': 'Dollar américain',
        '欧元': 'Euro',
        '日元': 'Yen japonais',
        '英镑': 'Livre sterling',
        '港币': 'Dollar de Hong Kong',
        '泰铢': 'Baht thaïlandais'
      };
      
      let frenchText = chineseText;
      for (const [chinese, french] of Object.entries(translations)) {
        frenchText = frenchText.replace(new RegExp(chinese, 'g'), french);
      }
      
      return frenchText;
    },
    
    // 新增：翻译为德语
    translateToGerman(chineseText) {
      const translations = {
        '您有': 'Sie haben',
        '您要': 'Sie möchten',
        '可以兑换': 'kann umtauschen',
        '需要支付': 'muss zahlen',
        '人民币': 'Chinesischer Yuan',
        '美元': 'US-Dollar',
        '欧元': 'Euro',
        '日元': 'Japanischer Yen',
        '英镑': 'Britisches Pfund',
        '港币': 'Hongkong-Dollar',
        '泰铢': 'Thailändischer Baht'
      };
      
      let germanText = chineseText;
      for (const [chinese, german] of Object.entries(translations)) {
        germanText = germanText.replace(new RegExp(chinese, 'g'), german);
      }
      
      return germanText;
    },
    
    // 新增：翻译为西班牙语
    translateToSpanish(chineseText) {
      const translations = {
        '您有': 'Usted tiene',
        '您要': 'Usted quiere',
        '可以兑换': 'puede cambiar',
        '需要支付': 'necesita pagar',
        '人民币': 'Yuan chino',
        '美元': 'Dólar estadounidense',
        '欧元': 'Euro',
        '日元': 'Yen japonés',
        '英镑': 'Libra esterlina',
        '港币': 'Dólar de Hong Kong',
        '泰铢': 'Baht tailandés'
      };
      
      let spanishText = chineseText;
      for (const [chinese, spanish] of Object.entries(translations)) {
        spanishText = spanishText.replace(new RegExp(chinese, 'g'), spanish);
      }
      
      return spanishText;
    },
    
    // 新增：翻译为俄语
    translateToRussian(chineseText) {
      const translations = {
        '您有': 'У вас есть',
        '您要': 'Вы хотите',
        '可以兑换': 'можно обменять',
        '需要支付': 'нужно заплатить',
        '人民币': 'Китайский юань',
        '美元': 'Доллар США',
        '欧元': 'Евро',
        '日元': 'Японская иена',
        '英镑': 'Британский фунт',
        '港币': 'Гонконгский доллар',
        '泰铢': 'Тайский бат'
      };
      
      let russianText = chineseText;
      for (const [chinese, russian] of Object.entries(translations)) {
        russianText = russianText.replace(new RegExp(chinese, 'g'), russian);
      }
      
      return russianText;
    },
    
    // 新增：翻译为阿拉伯语
    translateToArabic(chineseText) {
      const translations = {
        '您有': 'لديك',
        '您要': 'تريد',
        '可以兑换': 'يمكن تبادل',
        '需要支付': 'تحتاج للدفع',
        '人民币': 'اليوان الصيني',
        '美元': 'الدولار الأمريكي',
        '欧元': 'اليورو',
        '日元': 'الين الياباني',
        '英镑': 'الجنيه الإسترليني',
        '港币': 'دولار هونغ كونغ',
        '泰铢': 'الباht التايلندي'
      };
      
      let arabicText = chineseText;
      for (const [chinese, arabic] of Object.entries(translations)) {
        arabicText = arabicText.replace(new RegExp(chinese, 'g'), arabic);
      }
      
      return arabicText;
    },
    getLanguageTitle() {
      const languageNames = {
        'zh': this.$t('exchange.language_chinese'),
        'en': this.$t('exchange.language_english'),
        'th': this.$t('exchange.language_thai'),
        'ja': '日本語',
        'ko': '한국어',
        'fr': 'Français',
        'de': 'Deutsch',
        'es': 'Español',
        'ru': 'Русский',
        'ar': 'العربية'
      };
      return languageNames[this.currentLanguage] || this.$t('exchange.language_english');
    },
    getLanguageDisplay() {
      const languageNames = {
        'zh': this.$t('exchange.language_chinese'),
        'en': this.$t('exchange.language_english'),
        'th': this.$t('exchange.language_thai'),
        'ja': '日本語',
        'ko': '한국어',
        'fr': 'Français',
        'de': 'Deutsch',
        'es': 'Español',
        'ru': 'Русский',
        'ar': 'العربية'
      };
      return languageNames[this.currentLanguage] || this.$t('exchange.language_english');
    }
  },
  async created() {
    console.log('组件创建，当前用户信息:', JSON.parse(localStorage.getItem('user') || '{}'));
    console.log('当前网点本币:', this.baseCurrency);
    
    // 检查本币信息是否存在
    if (!this.baseCurrency || !this.userBranchCurrency) {
      console.error('本币信息不存在，用户需要重新登录');
      this.$router.push('/login?message=本币信息缺失，请重新登录');
      return;
    }
    
    await this.loadFundingSources();

    // 从本地存储加载上一笔交易信息
    try {
      const savedLastTransaction = localStorage.getItem('lastTransaction');
      if (savedLastTransaction) {
        this.lastTransaction = JSON.parse(savedLastTransaction);
        console.log('加载上一笔交易信息:', this.lastTransaction);
      }
    } catch (error) {
      console.error('加载上一笔交易信息失败:', error);
      // 如果解析失败，清除无效数据
      localStorage.removeItem('lastTransaction');
    }
    
    // 加载签名设置
    await this.loadPrintSettings();
    
    await this.fetchCurrencies();
    if (this.availableCurrencies[this.baseCurrency]) {
      this.baseCurrencyName = this.getCurrencyName(this.baseCurrency);
    }
    await this.fetchRates();
  },
  mounted() {
    this.fetchCurrencies();
    this.fetchRates();
    // 初始化语音功能
    this.initSpeechSynthesis();
    
    // 确保本币名称使用统一翻译
    if (this.baseCurrency) {
      this.baseCurrencyName = this.getCurrencyName(this.baseCurrency);
      console.log('mounted - 设置本币名称:', this.baseCurrencyName);
    }
    
    // 初始化签名标签多语言
    this.initSignatureLabels();
  },
  watch: {
    // 监听语言切换
    '$i18n.locale': {
      handler() {
        // 当语言切换时，重新计算币种名称
        if (this.baseCurrency && this.availableCurrencies[this.baseCurrency]) {
          this.baseCurrencyName = this.getCurrencyName(this.baseCurrency);
        }
        // 更新签名标签
        this.initSignatureLabels();
        // 语音语言保持独立，不受系统语言影响
        console.log('系统语言切换，语音语言保持独立:', this.currentLanguage);
      },
      immediate: false
    },
    
    // 监听外币选择变化
    foreignCurrency: {
      handler(newValue, oldValue) {
        console.log('外币选择变化:', oldValue, '->', newValue);
        if (newValue && newValue !== oldValue) {
          console.log('触发用途选项加载...');
          this.updateCurrentStep();
          this.resetPurposeSelection();
          // 立即加载用途选项
          this.loadPurposeOptions();
          this.refreshAll();
        } else if (!newValue) {
          // 如果清空了外币选择，也要清空用途选项
          console.log('清空外币选择，重置用途选项');
          this.resetPurposeSelection();
          this.purposeOptions = [];
        }
      },
      immediate: false // 不在初始化时立即执行
    }
  },
  
  // 基本翻译函数 - 回退到英语
  translateToSwedish(text) { return this.translateToEnglish(text); },
  translateToNorwegian(text) { return this.translateToEnglish(text); },
  translateToDanish(text) { return this.translateToEnglish(text); },
  translateToPortuguese(text) { return this.translateToEnglish(text); },
  translateToTurkish(text) { return this.translateToEnglish(text); },
  translateToPolish(text) { return this.translateToEnglish(text); },
  translateToCzech(text) { return this.translateToEnglish(text); },
  translateToHungarian(text) { return this.translateToEnglish(text); },
  translateToRomanian(text) { return this.translateToEnglish(text); },
  translateToBulgarian(text) { return this.translateToEnglish(text); },
  translateToCroatian(text) { return this.translateToEnglish(text); },
  translateToSerbian(text) { return this.translateToEnglish(text); },
  translateToUkrainian(text) { return this.translateToEnglish(text); },
  translateToBelarusian(text) { return this.translateToEnglish(text); },
  translateToHindi(text) { return this.translateToEnglish(text); },
  translateToVietnamese(text) { return this.translateToEnglish(text); },
  translateToIndonesian(text) { return this.translateToEnglish(text); },
  translateToMalay(text) { return this.translateToEnglish(text); },
  translateToTagalog(text) { return this.translateToEnglish(text); },
  translateToBengali(text) { return this.translateToEnglish(text); },
  translateToSinhala(text) { return this.translateToEnglish(text); },
  translateToNepali(text) { return this.translateToEnglish(text); },
  translateToUrdu(text) { return this.translateToEnglish(text); },
  translateToPashto(text) { return this.translateToEnglish(text); },
  translateToPersian(text) { return this.translateToEnglish(text); },
  translateToHebrew(text) { return this.translateToEnglish(text); },
  
  // 其他翻译函数
  translateToFrench(text) {
    const translations = {
      '您有': 'Vous avez',
      '您要': 'Vous voulez',
      '可以兑换': 'peut échanger vers',
      '需要支付': 'doit payer',
      '人民币': 'Yuan chinois',
      '美元': 'Dollar américain',
      '欧元': 'Euro',
      '日元': 'Yen japonais',
      '英镑': 'Livre sterling',
      '港币': 'Dollar de Hong Kong',
      '泰铢': 'Baht thaïlandais'
    };
    
    let frenchText = text;
    for (const [chinese, french] of Object.entries(translations)) {
      frenchText = frenchText.replace(new RegExp(chinese, 'g'), french);
    }
    
    return frenchText;
  },
  
  translateToGerman(text) {
    const translations = {
      '您有': 'Sie haben',
      '您要': 'Sie möchten',
      '可以兑换': 'kann umtauschen zu',
      '需要支付': 'muss zahlen',
      '人民币': 'Chinesischer Yuan',
      '美元': 'US-Dollar',
      '欧元': 'Euro',
      '日元': 'Japanischer Yen',
      '英镑': 'Britisches Pfund',
      '港币': 'Hongkong-Dollar',
      '泰铢': 'Thailändischer Baht'
    };
    
    let germanText = text;
    for (const [chinese, german] of Object.entries(translations)) {
      germanText = germanText.replace(new RegExp(chinese, 'g'), german);
    }
    
    return germanText;
  },
  
  translateToSpanish(text) {
    const translations = {
      '您有': 'Usted tiene',
      '您要': 'Usted quiere',
      '可以兑换': 'puede cambiar a',
      '需要支付': 'necesita pagar',
      '人民币': 'Yuan chino',
      '美元': 'Dólar estadounidense',
      '欧元': 'Euro',
      '日元': 'Yen japonés',
      '英镑': 'Libra esterlina',
      '港币': 'Dólar de Hong Kong',
      '泰铢': 'Baht tailandés'
    };
    
    let spanishText = text;
    for (const [chinese, spanish] of Object.entries(translations)) {
      spanishText = spanishText.replace(new RegExp(chinese, 'g'), spanish);
    }
    
    return spanishText;
  },
  
  translateToRussian(text) {
    const translations = {
      '您有': 'У вас есть',
      '您要': 'Вы хотите',
      '可以兑换': 'можно обменять на',
      '需要支付': 'нужно заплатить',
      '人民币': 'Китайский юань',
      '美元': 'Доллар США',
      '欧元': 'Евро',
      '日元': 'Японская иена',
      '英镑': 'Британский фунт',
      '港币': 'Гонконгский доллар',
      '泰铢': 'Тайский бат'
    };
    
    let russianText = text;
    for (const [chinese, russian] of Object.entries(translations)) {
      russianText = russianText.replace(new RegExp(chinese, 'g'), russian);
    }
    
    return russianText;
  },
  
  translateToArabic(text) {
    const translations = {
      '您有': 'لديك',
      '您要': 'تريد',
      '可以兑换': 'يمكن تبادل إلى',
      '需要支付': 'تحتاج إلى الدفع',
      '人民币': 'يوان صيني',
      '美元': 'دولار أمريكي',
      '欧元': 'يورو',
      '日元': 'ين ياباني',
      '英镑': 'جنيه إسترليني',
      '港币': 'دولار هونغ كونغ',
      '泰铢': 'بات تايلاندي'
    };
    
    let arabicText = text;
    for (const [chinese, arabic] of Object.entries(translations)) {
      arabicText = arabicText.replace(new RegExp(chinese, 'g'), arabic);
    }
    
    return arabicText;
  },
  
  translateToKorean(text) {
    const translations = {
      '您有': '당신은 가지고 있습니다',
      '您要': '당신은 원합니다',
      '可以兑换': '교환할 수 있습니다',
      '需要支付': '지불해야 합니다',
      '人民币': '중국 위안',
      '美元': '미국 달러',
      '欧元': '유로',
      '日元': '일본 엔',
      '英镑': '영국 파운드',
      '港币': '홍콩 달러',
      '泰铢': '태국 바트'
    };
    
    let koreanText = text;
    for (const [chinese, korean] of Object.entries(translations)) {
      koreanText = koreanText.replace(new RegExp(chinese, 'g'), korean);
    }
    
    return koreanText;
  }
};

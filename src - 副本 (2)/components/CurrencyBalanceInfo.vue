<template>
  <div class="currency-balance-info" v-if="selectedCurrency">
    <div class="card">
      <div class="card-header d-flex justify-content-between align-items-center">
        <h6 class="mb-0">
          <font-awesome-icon :icon="['fas', 'wallet']" class="me-2" />
          {{ getCurrencyDisplayName(selectedCurrency.currency_code) }} {{ $t('exchange.balance_info') }}
        </h6>
        <BalanceAlertIcon 
          :alert-status="balanceAlert.status"
          :alert-message="balanceAlert.message"
          :show-text="false"
        />
      </div>
      <div class="card-body">
        <div class="row" v-if="!loading">
          <div class="col-6">
            <div class="balance-item">
              <label>{{ $t('exchange.current_balance') }}</label>
              <div class="balance-value">
                {{ formatAmount(currentBalance) }}
                <span class="currency-code">{{ selectedCurrency.currency_code }}</span>
              </div>
            </div>
          </div>
          <div class="col-6">
            <div class="balance-item">
              <label>{{ $t('exchange.balance_status') }}</label>
              <div class="balance-status" :class="statusClass">
                <BalanceAlertIcon 
                  :alert-status="balanceAlert.status"
                  :alert-message="balanceAlert.message"
                  :show-text="true"
                />
              </div>
            </div>
          </div>
        </div>
        
        <!-- 加载状态 -->
        <div v-if="loading" class="text-center py-3">
          <div class="spinner-border spinner-border-sm text-primary" role="status">
            <span class="visually-hidden">{{ $t('exchange.loading') }}</span>
          </div>
        </div>
        
        <!-- 阈值信息 -->
        <div class="threshold-info mt-3" v-if="thresholdInfo && !loading">
          <div class="row">
            <div class="col-6" v-if="thresholdInfo.min_threshold">
              <small class="text-muted">{{ $t('exchange.min_threshold') }}: {{ formatAmount(thresholdInfo.min_threshold) }}</small>
            </div>
            <div class="col-6" v-if="thresholdInfo.max_threshold">
              <small class="text-muted">{{ $t('exchange.max_threshold') }}: {{ formatAmount(thresholdInfo.max_threshold) }}</small>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import BalanceAlertIcon from './BalanceAlertIcon.vue';
import { balanceService } from '@/services/api/balanceService';
import { getCurrencyName } from '@/utils/currencyTranslator';

export default {
  name: 'CurrencyBalanceInfo',
  components: {
    BalanceAlertIcon
  },
  props: {
    selectedCurrency: {
      type: Object,
      default: null
    }
  },
  data() {
    return {
      currentBalance: 0,
      balanceAlert: {
        status: 'normal',
        message: '正常'
      },
      thresholdInfo: null,
      loading: false
    };
  },
  computed: {
    statusClass() {
      return {
        'status-critical': this.balanceAlert.status && this.balanceAlert.status.includes('critical'),
        'status-warning': this.balanceAlert.status && this.balanceAlert.status.includes('warning'),
        'status-normal': this.balanceAlert.status === 'normal'
      };
    }
  },
  watch: {
    selectedCurrency: {
      handler(newCurrency) {
        console.log('CurrencyBalanceInfo - selectedCurrency变化:', newCurrency);
        if (newCurrency && newCurrency.id) {
          console.log('CurrencyBalanceInfo - 开始加载余额信息，币种ID:', newCurrency.id);
          this.loadBalanceInfo();
        } else {
          console.log('CurrencyBalanceInfo - 重置数据');
          this.resetData();
        }
      },
      immediate: true
    }
  },
  methods: {
    // 获取货币的显示名称
    getCurrencyDisplayName(currencyCode) {
      // 在Vue组件中，直接使用this.$i18n.locale来获取当前语言
      const currentLang = this.getCurrentLang();
      return getCurrencyName(currencyCode, currentLang);
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
    
    async loadBalanceInfo() {
      if (!this.selectedCurrency || !this.selectedCurrency.id) return;
      
      console.log('CurrencyBalanceInfo - loadBalanceInfo开始，币种:', this.selectedCurrency);
      this.loading = true;
      try {
        // 获取当前余额
        console.log('CurrencyBalanceInfo - 获取当前余额...');
        const balanceResponse = await balanceService.getCurrentBalance(this.selectedCurrency.id);
        console.log('CurrencyBalanceInfo - 余额响应:', balanceResponse.data);
        if (balanceResponse.data.success) {
          this.currentBalance = balanceResponse.data.balance;
          console.log('CurrencyBalanceInfo - 当前余额:', this.currentBalance);
        }
        
        // 获取报警状态
        console.log('CurrencyBalanceInfo - 获取报警状态...');
        const alertResponse = await balanceService.getAlertStatus(this.selectedCurrency.id);
        console.log('CurrencyBalanceInfo - 报警响应:', alertResponse.data);
        if (alertResponse.data.success) {
          let alertStatus = alertResponse.data.alert_info.alert_status || {
            status: 'normal',
            message: this.$t('exchange.balance_normal')
          };
          
          // 处理需要翻译的消息
          if (alertStatus.message_params && alertStatus.message_params.currency_code) {
            const currencyName = this.getCurrencyDisplayName(alertStatus.message_params.currency_code);
            const threshold = alertStatus.message_params.threshold;
            
            // 根据消息键生成翻译后的消息
            switch (alertStatus.message) {
              case 'balance_insufficient_below_min_threshold':
                alertStatus.message = `${currencyName}${this.$t('exchange.balance_insufficient')}, ${this.$t('exchange.below_min_threshold')} ${threshold}`;
                break;
              case 'balance_low_near_min_threshold':
                alertStatus.message = `${currencyName}${this.$t('exchange.balance_low')}, ${this.$t('exchange.near_min_threshold')}`;
                break;
              case 'balance_excessive_above_max_threshold':
                alertStatus.message = `${currencyName}${this.$t('exchange.balance_excessive')}, ${this.$t('exchange.above_max_threshold')} ${threshold}`;
                break;
              case 'balance_high_near_max_threshold':
                alertStatus.message = `${currencyName}${this.$t('exchange.balance_high')}, ${this.$t('exchange.near_max_threshold')}`;
                break;
            }
          }
          
          this.balanceAlert = alertStatus;
          this.thresholdInfo = alertResponse.data.alert_info.threshold_info;
          console.log('CurrencyBalanceInfo - 报警状态:', this.balanceAlert);
          console.log('CurrencyBalanceInfo - 阈值信息:', this.thresholdInfo);
        }
        
        // 发出余额更新事件
        this.$emit('balance-updated', {
          currency_id: this.selectedCurrency.id,
          balance: this.currentBalance,
          alert_status: this.balanceAlert
        });
        
      } catch (error) {
        console.error('加载余额信息失败:', error);
        this.balanceAlert = {
          status: 'error',
          message: this.$t('exchange.loading_failed')
        };
      } finally {
        this.loading = false;
      }
    },
    
    resetData() {
      this.currentBalance = 0;
      this.balanceAlert = {
        status: 'normal',
        message: this.$t('exchange.balance_normal')
      };
      this.thresholdInfo = null;
      this.loading = false;
    },
    
    formatAmount(amount) {
      return new Intl.NumberFormat('zh-CN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(amount || 0);
    },
    
    // 公开方法，供父组件调用
    refresh() {
      this.loadBalanceInfo();
    }
  }
};
</script>

<style scoped>
.currency-balance-info {
  margin-bottom: 1rem;
}

.card {
  border: 1px solid #e9ecef;
  border-radius: 0.5rem;
  box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
}

.card-header {
  background-color: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
  padding: 0.75rem 1rem;
}

.card-body {
  padding: 1rem;
}

.balance-item {
  text-align: center;
}

.balance-item label {
  font-size: 0.875rem;
  color: #6c757d;
  display: block;
  margin-bottom: 0.25rem;
}

.balance-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: #2c3e50;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
}

.currency-code {
  font-size: 0.875rem;
  color: #6c757d;
  margin-left: 0.5rem;
}

.balance-status {
  font-size: 0.875rem;
  min-height: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.status-critical {
  color: #dc3545;
}

.status-warning {
  color: #ffc107;
}

.status-normal {
  color: #28a745;
}

.threshold-info {
  border-top: 1px solid #e9ecef;
  padding-top: 0.75rem;
}

.threshold-info small {
  font-size: 0.75rem;
}
</style> 
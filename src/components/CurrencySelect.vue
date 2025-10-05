<template>
  <div class="currency-select-container">
    <!-- 币种选择触发器 -->
    <div class="currency-trigger" @click="openModal" :class="{ 'selected': modelValue }">
      <div v-if="selectedCurrency" class="selected-currency">
        <currency-flag :code="modelValue" :custom-filename="getCurrencyCustomFlag(modelValue)" class="me-2" />
        <span class="currency-text">{{ getCurrencyName(selectedCurrency) }} ({{ modelValue }})</span>
      </div>
      <div v-else class="placeholder-text">
        <font-awesome-icon icon="fa-solid fa-coins" class="me-2 text-muted" />
        <span>{{ $t('exchange.select_foreign_currency_placeholder') }}</span>
      </div>
      <div class="trigger-actions">
        <button 
          v-if="modelValue" 
          class="clear-btn"
          @click.stop="clearSelection"
          title="清空选择"
        >
          <font-awesome-icon icon="fa-solid fa-times" />
        </button>
        <div class="trigger-arrow">
          <font-awesome-icon icon="fa-solid fa-chevron-down" />
        </div>
      </div>
    </div>
    
    <!-- 隐藏的原生select，用于表单兼容性 -->
    <select 
      :id="id"
      class="d-none"
      :value="modelValue"
      tabindex="-1"
    >
      <option value="" disabled>{{ $t('exchange.select_foreign_currency_placeholder') }}</option>
      <option 
        v-for="currency in currencies" 
        :key="currency.id" 
        :value="currency.currency_code"
      >
        {{ getCurrencyName(currency) }} ({{ currency.currency_code }})
      </option>
    </select>

    <!-- 币种选择模态框 -->
    <div 
      class="modal fade" 
      :class="{ 'show': modalVisible }"
      :id="modalId" 
      tabindex="-1" 
      v-show="modalVisible"
      @click.self="closeModal"
    >
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              <font-awesome-icon icon="fa-solid fa-coins" class="me-2" />
              {{ $t('exchange.select_foreign_currency') }}
            </h5>
            <button type="button" class="btn-close" @click="closeModal" :aria-label="$t('common.close')"></button>
          </div>
          <div class="modal-body">
            <!-- 搜索框 -->
            <div class="mb-3">
              <div class="input-group">
                <span class="input-group-text">
                  <font-awesome-icon icon="fa-solid fa-search" />
                </span>
                <input
                  v-model="searchText"
                  :placeholder="$t('exchange.select_foreign_currency_placeholder')"
                  type="text"
                  class="form-control"
                  autocomplete="off"
                />
              </div>
            </div>
            
            <!-- 加载状态 -->
            <div v-if="loading" class="text-center mt-3">
              <div class="spinner-border" role="status">
                <span class="visually-hidden">{{ $t('exchange.loading') }}</span>
              </div>
              <p class="mt-2">{{ $t('exchange.loading_currencies') }}</p>
            </div>
            
            <!-- 错误状态 -->
            <div v-else-if="error" class="alert alert-danger mt-3">
              {{ error }}
            </div>
            
            <!-- 币种网格 -->
            <div v-else class="currency-grid">
              <div
                v-for="currency in filteredCurrencies"
                :key="currency.id"
                class="currency-card"
                :class="{ 'selected': modelValue === currency.currency_code }"
                @click="selectCurrency(currency)"
              >
                <div class="card h-100">
                  <div class="card-body d-flex align-items-center p-2">
                    <currency-flag :code="currency.currency_code" :custom-filename="currency.custom_flag_filename" class="me-2 currency-flag-large" />
                    <div class="currency-info flex-grow-1">
                      <div class="currency-inline">
                        <span class="currency-code">{{ currency.currency_code }}</span>
                        <span class="currency-separator">-</span>
                        <span class="currency-name">{{ getCurrencyName(currency) }}</span>
                      </div>
                    </div>
                    <div v-if="modelValue === currency.currency_code" class="check-mark">
                      <font-awesome-icon icon="fa-solid fa-check-circle" class="text-success" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 无搜索结果提示 -->
            <div v-if="filteredCurrencies.length === 0 && !loading && !error" class="text-center py-4 text-muted">
              <font-awesome-icon icon="fa-solid fa-search" size="2x" class="mb-2 opacity-50" />
              <p>{{ $t('exchange.no_currency_found') }}</p>
            </div>
          </div>
          
          <div class="modal-footer">
            <button 
              v-if="modelValue" 
              type="button" 
              class="btn btn-outline-danger me-auto" 
              @click="clearSelection"
            >
              <font-awesome-icon icon="fa-solid fa-times" class="me-1" />
              {{ $t('exchange.clear_selection') }}
            </button>
            <button type="button" class="btn btn-secondary" @click="closeModal">
              {{ $t('common.cancel') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import CurrencyFlag from './CurrencyFlag.vue'
import api from '@/services/api'

export default {
  name: 'CurrencySelect',
  components: {
    CurrencyFlag
  },
  props: {
    id: {
      type: String,
      required: true
    },
    modelValue: {
      type: String,
      required: true
    },
    apiEndpoint: {
      type: String,
      default: '/rates/available_currencies'
    },
    currencies: {
      type: Array,
      default: () => []
    }
  },
  emits: ['update:modelValue', 'change'],
  data() {
    return {
      searchText: '',
      modalVisible: false,
      internalCurrencies: [],
      loading: false,
      error: null
    }
  },
  computed: {
    modalId() {
      return `currencySelectModal_${this.id}`
    },
    filteredCurrencies() {
      if (!this.searchText) {
        return this.internalCurrencies;
      }
      
      const term = this.searchText.toLowerCase();
      return this.internalCurrencies.filter(currency => {
        const currentName = this.getCurrencyName(currency).toLowerCase();
        return currency.currency_code.toLowerCase().includes(term) ||
               currentName.includes(term);
      });
    },
    selectedCurrency() {
      return this.internalCurrencies.find(c => c.currency_code === this.modelValue);
    }
  },
  watch: {
    currencies: {
      handler(newCurrencies) {
        if (newCurrencies && newCurrencies.length > 0) {
          this.internalCurrencies = [...newCurrencies];
        }
      },
      immediate: true
    }
  },
  methods: {
    openModal() {
      this.modalVisible = true;
      this.loadCurrencies();
      this.$nextTick(() => {
        const modalEl = document.getElementById(this.modalId);
        if (modalEl) {
          modalEl.classList.add('show');
          modalEl.style.display = 'block';
          document.body.classList.add('modal-open');
        }
      });
    },
    closeModal() {
      this.modalVisible = false;
      this.searchText = '';
      
      const modalEl = document.getElementById(this.modalId);
      if (modalEl) {
        modalEl.classList.remove('show');
        modalEl.style.display = 'none';
        document.body.classList.remove('modal-open');
        
        // 移除backdrop
        const backdrop = document.querySelector('.modal-backdrop');
        if (backdrop) {
          backdrop.remove();
        }
      }
    },
    selectCurrency(currency) {
      console.log('选择币种:', currency);
      this.$emit('update:modelValue', currency.currency_code);
      this.$emit('change', currency.currency_code, currency);
      this.closeModal();
    },
    clearSelection() {
      this.$emit('update:modelValue', '');
      this.$emit('change', '', null);
      this.closeModal();
    },
    
    // 获取币种的自定义图标文件名
    getCurrencyCustomFlag(currencyCode) {
      const currency = this.internalCurrencies.find(c => c.currency_code === currencyCode);
      if (currency && currency.custom_flag_filename) {
        return currency.custom_flag_filename;
      }
      

      
      return null;
    },
    getCurrencyName(currency) {
      // 检查是否是自定义币种（有custom_flag_filename）
      if (currency.custom_flag_filename) {
        // console.log(`[自定义币种] ${currency.currency_code} 使用数据库名称: ${currency.currency_name}`);

        return currency.currency_name || currency.currency_code;
      }
      
      // 使用翻译键获取币种名称
      const currencyCode = currency.currency_code;
      const translationKey = `currencies.${currencyCode}`;
      
      try {
        // 尝试使用翻译键获取多语言名称
        const translatedName = this.$t(translationKey);
        if (translatedName && translatedName !== translationKey) {
          return translatedName;
        }
      } catch (error) {
        console.log(`翻译键 ${translationKey} 不存在，使用默认名称`);
      }
      
      // 如果翻译键不存在，回退到默认名称
      return currency.currency_name || currency.currency_code;
    },
    async loadCurrencies() {
      // 如果已经传入了currencies数据，直接使用
      if (this.currencies && this.currencies.length > 0) {
        this.internalCurrencies = [...this.currencies];
        return;
      }
      
      // 如果已经有数据，不再重复加载
      if (this.internalCurrencies.length > 0) return;
      
      this.loading = true;
      this.error = null;
      
      try {
        console.log('开始加载币种列表...');
        console.log('使用API端点:', this.apiEndpoint);
        
        // 根据不同的API端点使用不同的参数
        const params = this.apiEndpoint.includes('currency-templates') 
          ? {} 
          : { published_only: true };
          
        const response = await api.get(this.apiEndpoint, { params });
        console.log('API响应:', response.data);
        
        if (response.data.success) {
          // 根据不同的API端点处理不同的响应格式
          if (this.apiEndpoint.includes('currency-templates')) {
            this.internalCurrencies = response.data.templates;
          } else {
            this.internalCurrencies = response.data.currencies;
          }
          console.log('成功加载币种:', this.internalCurrencies.length, '个');
          
          // 详细检查第一个币种的数据结构
          if (this.internalCurrencies.length > 0) {
            console.log('=== 第一个币种数据结构检查 ===');
            console.log('第一个币种:', this.internalCurrencies[0]);
            console.log('currency_names字段:', this.internalCurrencies[0].currency_names);
            if (this.internalCurrencies[0].currency_names) {
              console.log('支持的语言:', Object.keys(this.internalCurrencies[0].currency_names));
              console.log('各语言名称:', this.internalCurrencies[0].currency_names);
            }
            console.log('=============================');
          }
        } else {
          this.error = response.data.message || '加载货币列表失败';
          console.error('API返回错误:', this.error);
        }
      } catch (error) {
        console.error('加载货币列表失败:', error);
        this.error = '加载货币列表失败: ' + error.message;
      } finally {
        this.loading = false;
      }
    }
  }
}
</script>

<style scoped>
.currency-select-container {
  position: relative;
  display: inline-block;
  min-width: 200px;
}

/* 触发器样式 */
.currency-trigger {
  min-height: 38px;
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 8px 12px;
  background: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.currency-trigger:hover {
  border-color: #007bff;
}

.currency-trigger.selected {
  border-color: #007bff;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

.selected-currency {
  display: flex;
  align-items: center;
  flex-grow: 1;
}

.currency-text {
  font-weight: 500;
}

.placeholder-text {
  display: flex;
  align-items: center;
  color: #6c757d;
  flex-grow: 1;
}

.trigger-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.clear-btn {
  background: none;
  border: none;
  color: #dc3545;
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 2px;
  transition: background-color 0.2s;
}

.clear-btn:hover {
  background-color: rgba(220, 53, 69, 0.1);
}

.trigger-arrow {
  color: #6c757d;
  transition: transform 0.2s;
}

.currency-trigger:hover .trigger-arrow {
  color: #007bff;
}

/* 模态框样式 */
.modal {
  z-index: 1060;
}

.modal.show {
  display: block !important;
}

.currency-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 8px;
  max-height: 400px;
  overflow-y: auto;
  padding: 4px;
}

.currency-card {
  cursor: pointer;
  transition: transform 0.1s, box-shadow 0.2s;
}

.currency-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.currency-card.selected .card {
  border-color: #007bff;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

.currency-card .card-body {
  min-height: 50px;
  padding: 8px !important;
}

.currency-info {
  min-width: 0;
}

.currency-inline {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}

.currency-code {
  font-weight: bold;
  font-size: 0.9rem;
  color: #007bff;
}

.currency-separator {
  color: #6c757d;
  font-weight: normal;
}

.currency-name {
  font-size: 0.8rem;
  color: #495057;
  font-weight: 500;
}

.currency-flag-large {
  width: 28px;
  height: 21px;
  border-radius: 3px;
  flex-shrink: 0;
}

.check-mark {
  color: #28a745;
  font-size: 1.2rem;
}

/* 搜索框样式 */
.input-group-text {
  background-color: #f8f9fa;
  border-color: #ced4da;
}

/* 加载和错误状态样式 */
.spinner-border {
  width: 2rem;
  height: 2rem;
}

.alert {
  font-size: 0.9rem;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .currency-grid {
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  }
}

@media (max-width: 768px) {
  .currency-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    max-height: 300px;
  }
  
  .modal-dialog {
    margin: 10px;
  }
  
  .currency-inline {
    flex-direction: column;
    align-items: flex-start;
    gap: 2px;
  }
}

@media (max-width: 576px) {
  .currency-grid {
    grid-template-columns: 1fr;
  }
}

/* 无障碍支持 */
.currency-card:focus {
  outline: 2px solid #007bff;
  outline-offset: 2px;
}

.clear-btn:focus {
  outline: 2px solid #dc3545;
  outline-offset: 2px;
}
</style> 
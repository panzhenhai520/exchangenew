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
    <teleport to="body">
      <div 
        v-if="modalVisible"
        class="currency-modal-overlay"
        @click.self="closeModal"
      >
      <div class="modal-dialog modal-lg" @click.stop>
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <h5 class="modal-title">
              <font-awesome-icon icon="fa-solid fa-coins" class="me-2" />
              {{ $t('exchange.select_foreign_currency') }}
            </h5>
            <button type="button" class="btn-close" @click="closeModal" :aria-label="$t('common.close')"></button>
          </div>
          <div class="modal-body">
            <!-- 搜索框 -->
            <div class="search-container">
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
                  ref="searchInput"
                  @click.stop
                  @keydown.stop
                  @input.stop
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
    </teleport>
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
      // 添加保护性检查
      if (!this.internalCurrencies || !Array.isArray(this.internalCurrencies)) {
        return [];
      }
      
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
      // 添加保护性检查，确保internalCurrencies是数组
      if (!this.internalCurrencies || !Array.isArray(this.internalCurrencies)) {
        return null;
      }
      return this.internalCurrencies.find(c => c.currency_code === this.modelValue);
    }
  },
  mounted() {
    // 绑定键盘事件
    document.addEventListener('keydown', this.handleKeydown);
  },
  beforeUnmount() {
    // 移除键盘事件
    document.removeEventListener('keydown', this.handleKeydown);
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
      
      // 简化聚焦逻辑，移除延迟
      this.$nextTick(() => {
        if (this.$refs.searchInput) {
          this.$refs.searchInput.focus();
        }
      });
    },
    closeModal() {
      this.searchText = '';
      this.modalVisible = false;
    },
    selectCurrency(currency) {
      console.log('选择币种:', currency);
      this.$emit('update:modelValue', currency.currency_code);
      this.$emit('change', currency.currency_code, currency);
      this.closeModal();
    },
    
    // 键盘事件处理
    handleKeydown(event) {
      if (!this.modalVisible) return;
      
      switch(event.key) {
        case 'Escape':
          event.preventDefault();
          this.closeModal();
          break;
        case 'Enter': {
          event.preventDefault();
          const firstCurrency = this.filteredCurrencies[0];
          if (firstCurrency) {
            this.selectCurrency(firstCurrency);
          }
          break;
        }
      }
    },
    clearSelection() {
      this.$emit('update:modelValue', '');
      this.$emit('change', '', null);
      this.closeModal();
    },
    
    // 获取币种的自定义图标文件名
    getCurrencyCustomFlag(currencyCode) {
      // 添加保护性检查
      if (!this.internalCurrencies || !Array.isArray(this.internalCurrencies)) {
        return null;
      }
      
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
            this.internalCurrencies = response.data.templates || [];
          } else {
            this.internalCurrencies = response.data.currencies || [];
          }
          
          // 确保 internalCurrencies 是数组
          if (!Array.isArray(this.internalCurrencies)) {
            console.error('币种数据不是数组格式:', this.internalCurrencies);
            this.internalCurrencies = [];
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

/* 币种选择模态框覆盖层 */
.currency-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1070;
  background-color: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(2px);
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 模态框对话框样式 */
.modal-dialog {
  position: relative;
  margin: 0.5rem;
  max-width: 90vw;
  max-height: 90vh;
  width: 800px;
  display: flex;
  flex-direction: column;
}

/* 模态框内容区域 */
.modal-content {
  border-radius: 12px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
  border: none;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  position: relative;
  background-color: #fff;
  background-clip: padding-box;
  outline: 0;
}

/* 模态框头部 */
.modal-header {
  border-bottom: 1px solid #e9ecef;
  padding: 1rem 1.5rem;
  border-radius: 12px 12px 0 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.modal-header .modal-title {
  font-weight: 600;
  margin: 0;
}

.modal-header .btn-close {
  filter: invert(1);
  opacity: 0.8;
}

.modal-header .btn-close:hover {
  opacity: 1;
}

/* 模态框主体 */
.modal-body {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 1.5rem;
}

/* 模态框底部 */
.modal-footer {
  border-top: 1px solid #e9ecef;
  padding: 1rem 1.5rem;
  border-radius: 0 0 12px 12px;
  background-color: #f8f9fa;
}

.currency-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
  max-height: 450px;
  overflow-y: auto;
  padding: 8px 4px;
  flex: 1;
  /* 自定义滚动条样式 */
  scrollbar-width: thin;
  scrollbar-color: #cbd5e0 #f7fafc;
}

/* WebKit浏览器滚动条样式 */
.currency-grid::-webkit-scrollbar {
  width: 8px;
}

.currency-grid::-webkit-scrollbar-track {
  background: #f7fafc;
  border-radius: 4px;
}

.currency-grid::-webkit-scrollbar-thumb {
  background: #cbd5e0;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.currency-grid::-webkit-scrollbar-thumb:hover {
  background: #a0aec0;
}

.currency-card {
  cursor: pointer;
  transition: all 0.2s ease;
  border-radius: 8px;
  overflow: hidden;
}

.currency-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.12);
}

.currency-card.selected .card {
  border: 2px solid #007bff;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
  background: linear-gradient(135deg, #f8f9ff 0%, #e6f3ff 100%);
}

.currency-card .card {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  transition: all 0.2s ease;
  background: white;
  height: 100%;
}

.currency-card .card:hover {
  border-color: #cbd5e0;
}

.currency-card .card-body {
  min-height: 60px;
  padding: 12px !important;
  display: flex;
  align-items: center;
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
.search-container {
  position: sticky;
  top: 0;
  background: white;
  z-index: 10;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e2e8f0;
}

.input-group {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  border-radius: 8px;
  overflow: hidden;
}

.input-group-text {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
  font-weight: 500;
}

.form-control {
  border: 1px solid #e2e8f0;
  border-left: none;
  padding: 0.75rem 1rem;
  font-size: 0.95rem;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-control:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
  outline: none;
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
  
  .modal-dialog {
    width: 90vw;
    max-width: 700px;
  }
}

@media (max-width: 768px) {
  .currency-grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    max-height: 350px;
    gap: 8px;
  }
  
  .modal-dialog {
    width: 95vw;
    max-width: 600px;
    margin: 10px;
  }
  
  .modal-content {
    max-height: 85vh;
  }
  
  .currency-inline {
    flex-direction: column;
    align-items: flex-start;
    gap: 2px;
  }
  
  .modal-header {
    padding: 0.75rem 1rem;
  }
  
  .modal-body {
    padding: 1rem;
  }
  
  .modal-footer {
    padding: 0.75rem 1rem;
  }
}

@media (max-width: 576px) {
  .currency-grid {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    max-height: 300px;
  }
  
  .modal-dialog {
    width: 98vw;
    margin: 5px;
  }
  
  .modal-header .modal-title {
    font-size: 1.1rem;
  }
  
  .currency-card .card-body {
    padding: 8px !important;
    min-height: 50px;
  }
  
  .currency-flag-large {
    width: 24px;
    height: 18px;
  }
  
  .currency-code {
    font-size: 0.85rem;
  }
  
  .currency-name {
    font-size: 0.75rem;
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
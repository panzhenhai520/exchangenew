<template>
  <div class="exchange-form">
    <div class="currency-selection mb-4">
      <label class="form-label">选择外币:</label>
      <select v-model="selectedCurrency" class="form-select">
        <option value="USD">美元 (USD)</option>
        <!-- 其他货币选项 -->
      </select>
    </div>

    <div class="exchange-cards">
      <div class="row g-4">
        <!-- 买入卡片 -->
        <div class="col-md-6">
          <div class="card h-100">
            <div class="card-header bg-primary text-white">
              <h5 class="card-title mb-0">买入 {{ selectedCurrency }} ({{ getCurrencySymbol(selectedCurrency) }})</h5>
            </div>
            <div class="card-body">
              <div class="form-check">
                <input
                  class="form-check-input"
                  type="radio"
                  name="exchangeDirection"
                  id="buyOption"
                  value="buy"
                  v-model="direction"
                >
                <label class="form-check-label" for="buyOption">
                  <span class="currency-flag">{{ getCurrencyFlag(selectedCurrency) }}</span>
                  {{ selectedCurrency }} →
                  <span class="currency-flag">🇪🇺</span>
                  EUR
                  (买入 {{ selectedCurrency }})
                </label>
              </div>
            </div>
          </div>
        </div>

        <!-- 卖出卡片 -->
        <div class="col-md-6">
          <div class="card h-100">
            <div class="card-header bg-secondary text-white">
              <h5 class="card-title mb-0">卖出 {{ selectedCurrency }} ({{ getCurrencySymbol(selectedCurrency) }})</h5>
            </div>
            <div class="card-body">
              <div class="form-check">
                <input
                  class="form-check-input"
                  type="radio"
                  name="exchangeDirection"
                  id="sellOption"
                  value="sell"
                  v-model="direction"
                >
                <label class="form-check-label" for="sellOption">
                  <span class="currency-flag">🇪🇺</span>
                  EUR ←
                  <span class="currency-flag">{{ getCurrencyFlag(selectedCurrency) }}</span>
                  {{ selectedCurrency }}
                  (卖出 {{ selectedCurrency }})
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 汇率显示 -->
    <div class="rate-display mt-4" v-if="currentRate">
      <div class="alert alert-info">
        1 {{ selectedCurrency }} = {{ currentRate }} EUR (银行{{ direction === 'buy' ? '买入' : '卖出' }}价)
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ExchangeForm',
  data() {
    return {
      selectedCurrency: 'USD',
      direction: 'buy',
      currentRate: 7.1929
    }
  },
  methods: {
    getCurrencySymbol(currency) {
      const symbols = {
        USD: '$',
        EUR: '€',
        // 添加其他货币符号
      }
      return symbols[currency] || currency
    },
    getCurrencyFlag(currency) {
      const flags = {
        USD: '🇺🇸',
        EUR: '🇪🇺',
        // 添加其他货币国旗
      }
      return flags[currency] || ''
    }
  }
}
</script>

<style scoped>
.exchange-form {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.card {
  border: none;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s;
}

.card:hover {
  transform: translateY(-2px);
}

.card-header {
  border-bottom: none;
}

.form-check {
  padding: 1rem;
}

.currency-flag {
  font-size: 1.2em;
  margin: 0 0.3em;
}

.rate-display {
  text-align: center;
}
</style> 
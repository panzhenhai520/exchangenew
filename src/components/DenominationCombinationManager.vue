<template>
  <div class="denomination-combination-manager">
    <!-- 面值组合列表 -->
    <div class="combination-list" v-if="combinations.length > 0">
      <h6 class="mb-3">
        <font-awesome-icon :icon="['fas', 'list']" class="me-2" />
        {{ $t('exchange.denomination_combinations') }}
      </h6>

      <div class="table-responsive">
        <table class="table table-sm table-bordered">
          <thead class="table-light">
            <tr>
              <th width="12%">{{ $t('exchange.currency') }}</th>
              <th width="18%">{{ $t('exchange.denomination') }}</th>
              <th width="12%">{{ $t('exchange.direction') }}</th>
              <th width="8%">{{ $t('exchange.quantity') }}</th>
              <th width="12%">{{ $t('exchange.exchange_rate') }}</th>
              <th width="13%">{{ $t('exchange.subtotal') }}</th>
              <th width="13%">{{ $t('exchange.local_amount') }}</th>
              <th width="12%">{{ $t('exchange.actions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in combinations" :key="item.id" class="combination-item">
              <td class="currency-cell">
                <div class="d-flex align-items-center">
                  <CurrencyFlag
                    :code="item.currency_code"
                    :custom-filename="item.custom_flag_filename"
                    class="me-2 currency-flag-medium"
                  />
                  <div>
                    <div class="currency-code">{{ item.currency_code }}</div>
                    <small class="text-muted currency-name">{{ item.currency_name }}</small>
                  </div>
                </div>
              </td>
              <td class="denomination-cell">
                <div>
                  <strong>{{ formatAmount(item.denomination_value) }}</strong>
                  <span class="badge ms-1" :class="item.denomination_type === 'bill' ? 'bg-success' : 'bg-warning'">
                    {{ $t(`exchange.${item.denomination_type}`) }}
                  </span>
                </div>
              </td>
              <td class="direction-cell">
                <select
                  v-model="item.direction"
                  @change="updateItemCalculation(index)"
                  class="form-select form-select-sm"
                  :class="getDirectionClass(item.direction)"
                >
                  <option value="sell">{{ $t('exchange.sell') }}</option>
                  <option value="buy">{{ $t('exchange.buy') }}</option>
                </select>
              </td>
              <td class="quantity-cell">
                <input
                  type="number"
                  v-model.number="item.quantity"
                  @input="updateItemCalculation(index)"
                  class="form-control form-control-sm text-center"
                  min="1"
                  max="999"
                />
              </td>
              <td class="rate-cell">
                <div class="exchange-rate-display">
                  <div class="rate-value">{{ formatRate(item.rate) }}</div>
                  <div class="rate-label">{{ getRateLabel(item.direction) }}</div>
                </div>
              </td>
              <td class="subtotal-cell">
                <span class="text-primary fw-bold">
                  {{ formatAmount(item.subtotal) }} {{ item.currency_code }}
                </span>
              </td>
              <td class="local-amount-cell">
                <span class="text-success fw-bold">
                  {{ formatAmount(Math.abs(item.local_amount)) }} {{ baseCurrency }}
                </span>
              </td>
              <td class="actions-cell">
                <button
                  @click="removeCombination(index)"
                  class="btn btn-sm btn-outline-danger"
                  :title="$t('exchange.remove')"
                >
                  <font-awesome-icon :icon="['fas', 'trash']" />
                </button>
              </td>
            </tr>
          </tbody>
          <tfoot class="table-secondary">
            <tr>
              <th colspan="5" class="text-end">{{ $t('exchange.total') }}：</th>
              <th colspan="2" class="text-center">
                <div class="total-summary">
                  <div v-for="(total, currency) in currencyTotals" :key="currency" class="currency-total">
                    <span class="currency-amount" :class="{'text-success': total.foreign_amount > 0, 'text-danger': total.foreign_amount < 0}">
                      {{ formatAmountWithSign(total.foreign_amount) }} {{ currency }}
                    </span>
                    <span class="mx-2">→</span>
                    <span class="local-amount" :class="{'text-success': total.local_amount > 0, 'text-danger': total.local_amount < 0}">
                      {{ formatAmountWithSign(total.local_amount) }} {{ baseCurrency }}
                    </span>
                  </div>
                </div>
              </th>
              <th></th>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-state text-center py-4">
      <font-awesome-icon :icon="['fas', 'coins']" class="fa-2x text-muted mb-2" />
      <p class="text-muted">{{ $t('exchange.no_combinations_yet') }}</p>
      <small class="text-muted">{{ $t('exchange.add_combinations_hint') }}</small>
    </div>

    <!-- 计算结果摘要 -->
    <div v-if="combinations.length > 0" class="calculation-summary mt-3">
      <div class="alert alert-info">
        <h6 class="mb-2">
          <font-awesome-icon :icon="['fas', 'calculator']" class="me-2" />
          {{ $t('exchange.calculation_summary') }}
        </h6>
        <div class="summary-content">
          <div v-for="(summary, currency) in currencyTotals" :key="currency" class="currency-summary mb-2">
            <strong>{{ currency }}:</strong>
            <span v-if="summary.buy_amount > 0" class="ms-2">
              {{ $t('exchange.buy') }} {{ formatAmount(summary.buy_amount) }} {{ currency }}
              ({{ formatAmount(summary.buy_local) }} {{ baseCurrency }})
            </span>
            <span v-if="summary.sell_amount > 0" class="ms-2">
              {{ $t('exchange.sell') }} {{ formatAmount(summary.sell_amount) }} {{ currency }}
              ({{ formatAmount(summary.sell_local) }} {{ baseCurrency }})
            </span>
            <span v-if="summary.net_amount != 0" class="ms-2 net-amount">
              {{ $t('exchange.net') }}: {{ formatAmount(summary.net_amount) }} {{ currency }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import CurrencyFlag from '@/components/CurrencyFlag.vue'

export default {
  name: 'DenominationCombinationManager',
  components: {
    CurrencyFlag
  },
  props: {
    baseCurrency: {
      type: String,
      default: 'THB'
    }
  },
  emits: ['change'],
  data() {
    return {
      combinations: []
    }
  },
  computed: {
    // 按币种统计总计
    currencyTotals() {
      const totals = {}

      this.combinations.forEach(item => {
        const currency = item.currency_code
        if (!totals[currency]) {
          totals[currency] = {
            buy_amount: 0,
            sell_amount: 0,
            buy_local: 0,
            sell_local: 0,
            foreign_amount: 0,
            local_amount: 0,
            net_amount: 0
          }
        }

        const total = totals[currency]

        if (item.direction === 'buy') {
          // 前端选择"买入" = 客户买入外币：网点支付外币给客户，收取本币
          total.buy_amount += item.subtotal
          total.buy_local += Math.abs(item.local_amount)
          total.foreign_amount += item.subtotal   // 外币：网点增加（显示为正）
          total.local_amount -= item.local_amount  // 本币：网点减少（item.local_amount为正，减去后显示为负）
        } else {
          // 前端选择"卖出" = 客户卖出外币：网点收取外币，支付本币给客户
          total.sell_amount += item.subtotal
          total.sell_local += Math.abs(item.local_amount)
          total.foreign_amount -= item.subtotal   // 外币：网点减少（显示为负）
          total.local_amount -= item.local_amount  // 本币：网点增加（item.local_amount为负，减去负数=加，显示为正）
        }

        total.net_amount = total.foreign_amount
      })

      return totals
    }
  },
  watch: {
    combinations: {
      handler() {
        this.emitChange()
      },
      deep: true
    }
  },
  methods: {
    // 添加新的面值组合
    addCombination(combinationData) {
      console.log('DenominationCombinationManager 接收数据:', combinationData)
      console.log('当前组合列表:', this.combinations)

      // 直接使用传入的数据，不要重新计算覆盖
      const newCombination = {
        id: Date.now() + Math.random(),
        currency_id: combinationData.currency_id,
        currency_code: combinationData.currency_code,
        currency_name: combinationData.currency_name,
        custom_flag_filename: combinationData.custom_flag_filename,
        denomination_id: combinationData.denomination_id,
        denomination_value: combinationData.denomination_value,
        denomination_type: combinationData.denomination_type,
        direction: combinationData.direction, // 保持原始方向
        quantity: combinationData.quantity,
        rate: combinationData.rate,
        subtotal: combinationData.subtotal, // 使用传入的subtotal
        local_amount: combinationData.local_amount // 使用传入的local_amount
      }

      console.log('创建的新组合:', newCombination)

      // 使用深拷贝创建新数组避免响应式问题
      this.combinations = [...this.combinations, newCombination]

      console.log('添加后的组合列表:', this.combinations)
    },

    // 移除组合
    removeCombination(index) {
      this.combinations.splice(index, 1)
    },

    // 更新单项计算
    updateItemCalculation(index) {
      const item = this.combinations[index]
      item.subtotal = item.denomination_value * item.quantity
      item.local_amount = this.calculateLocalAmount(
        item.subtotal,
        item.direction,
        item.rate
      )
    },

    // 计算本币金额（与后端TransactionSplitService逻辑保持一致）
    calculateLocalAmount(foreignAmount, direction, rate) {
      if (direction === 'buy') {
        // 客户买入外币：网点卖出外币，收取本币（正数）
        return foreignAmount * rate
      } else {
        // 客户卖出外币：网点买入外币，支付本币（负数）
        return -(foreignAmount * rate)
      }
    },

    // 清空所有组合
    clearAllCombinations() {
      this.combinations = []
    },

    // 获取方向样式类
    getDirectionClass(direction) {
      return direction === 'buy' ? 'border-success' : 'border-primary'
    },

    // 格式化金额
    formatAmount(amount) {
      if (!amount && amount !== 0) return '0.00'
      return new Intl.NumberFormat('zh-CN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(Math.abs(amount))
    },

    // 格式化带符号的金额
    formatAmountWithSign(amount) {
      if (!amount && amount !== 0) return '+0.00'
      const formatted = new Intl.NumberFormat('zh-CN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(Math.abs(amount))
      return amount >= 0 ? `+${formatted}` : `-${formatted}`
    },

    // 格式化汇率
    formatRate(rate) {
      if (!rate && rate !== 0) return '0.0000'
      return new Intl.NumberFormat('zh-CN', {
        minimumFractionDigits: 4,
        maximumFractionDigits: 4
      }).format(rate)
    },

    // 获取汇率标签
    getRateLabel(direction) {
      return direction === 'buy' ? this.$t('exchange.sell_rate') : this.$t('exchange.buy_rate')
    },

    // 发送变更事件
    emitChange() {
      this.$emit('change', {
        combinations: this.combinations,
        totals: this.currencyTotals,
        total_combinations: this.combinations.length,
        total_currencies: Object.keys(this.currencyTotals).length
      })
    }
  }
}
</script>

<style scoped>
.denomination-combination-manager {
  border: 1px solid #e9ecef;
  border-radius: 0.375rem;
  padding: 1rem;
  background: #f8f9fa;
}

.combination-item:hover {
  background-color: #f5f5f5;
}

.currency-flag-small {
  width: 16px;
  height: 12px;
}

.currency-flag-medium {
  width: 32px;
  height: 24px;
  object-fit: cover;
  border-radius: 3px;
  border: 1px solid #dee2e6;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.currency-code {
  font-weight: 600;
  font-size: 0.875rem;
  color: #495057;
  line-height: 1.2;
}

.currency-name {
  font-size: 0.75rem;
  color: #6c757d;
  line-height: 1.1;
  display: block;
  margin-top: 1px;
}

.rate-cell {
  text-align: center;
}

.exchange-rate-display {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.rate-value {
  font-weight: 600;
  font-size: 0.875rem;
  color: #495057;
  line-height: 1.2;
}

.rate-label {
  font-size: 0.7rem;
  color: #6c757d;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  margin-top: 1px;
}

.direction-cell select {
  min-width: 80px;
}

.quantity-cell input {
  max-width: 70px;
}

.actions-cell {
  text-align: center;
}

.total-summary {
  font-size: 0.875rem;
}

.currency-total {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 0.25rem;
}

.currency-amount {
  color: #0d6efd;
  font-weight: 600;
}

.local-amount {
  color: #198754;
  font-weight: 600;
}

.empty-state {
  min-height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.calculation-summary .currency-summary {
  padding: 0.5rem;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 0.25rem;
  font-size: 0.875rem;
}

.net-amount {
  padding: 0.25rem 0.5rem;
  background: #e7f3ff;
  border-radius: 0.25rem;
  font-weight: bold;
}

.border-success {
  border-color: #198754 !important;
}

.border-primary {
  border-color: #0d6efd !important;
}
</style>
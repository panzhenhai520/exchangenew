<template>
  <div class="denomination-selector">
    <!-- 面值选择区域 -->
    <div class="denomination-selection mb-3">
      <label class="form-label">
        <i class="fas fa-coins me-2"></i>
        {{ $t('exchange.select_denomination') }}
      </label>

      <!-- 面值按钮组 -->
      <div class="denomination-buttons" v-if="denominations.length > 0">
        <button
          v-for="denom in denominations"
          :key="denom.id"
          type="button"
          class="btn btn-outline-primary denomination-btn"
          @click="showQuantityModal(denom)"
        >
          <div class="denomination-value">{{ formatDenominationValue(denom.denomination_value) }}</div>
          <div class="denomination-type">
            <i :class="denom.denomination_type === 'bill' ? 'fas fa-money-bill' : 'fas fa-coins'"></i>
            {{ $t(`exchange.${denom.denomination_type}`) }}
          </div>
        </button>
      </div>

      <!-- 无面值提示 -->
      <div v-else class="alert alert-warning">
        <i class="fas fa-exclamation-triangle me-2"></i>
        {{ $t('exchange.no_denominations_available') }}
      </div>
    </div>
    
    <!-- 多面值组合列表 -->
    <div class="combination-list mb-4" v-if="combinationList.length > 0">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <label class="form-label mb-0">
          <i class="fas fa-layer-group me-2 text-primary"></i>
          {{ $t('exchange.denomination_combination_list') }}
        </label>
        <button
          type="button"
          class="btn btn-sm btn-outline-danger"
          @click="clearAllCombinations"
        >
          <i class="fas fa-trash me-1"></i>
          {{ $t('common.clear_all') }}
        </button>
      </div>

      <div class="table-responsive">
        <table class="table table-sm table-bordered combination-table">
          <thead class="table-light">
            <tr>
              <th width="20%">{{ $t('exchange.denomination') }}</th>
              <th width="15%">{{ $t('exchange.direction') }}</th>
              <th width="12%">{{ $t('exchange.quantity') }}</th>
              <th width="18%">{{ $t('exchange.subtotal') }}</th>
              <th width="20%">{{ $t('exchange.exchange_rate') }}</th>
              <th width="15%">{{ $t('common.actions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in combinationList" :key="index" class="combination-row">
              <td>
                <div class="d-flex align-items-center">
                  <i :class="item.denomination_type === 'bill' ? 'fas fa-money-bill text-success me-2' : 'fas fa-coins text-warning me-2'"></i>
                  <span class="fw-bold">{{ formatDenominationValue(item.denomination_value) }}</span>
                  <span class="badge ms-1" :class="item.denomination_type === 'bill' ? 'bg-success' : 'bg-warning'">
                    {{ $t(`exchange.${item.denomination_type}`) }}
                  </span>
                </div>
              </td>
              <td class="text-center">
                <select
                  v-model="item.direction"
                  @change="updateItemDirection(index)"
                  class="form-select form-select-sm direction-select"
                >
                  <option value="sell">{{ $t('exchange.sell') }}</option>
                  <option value="buy">{{ $t('exchange.buy') }}</option>
                </select>
              </td>
              <td class="text-center">
                <span class="badge bg-primary">{{ item.quantity }}</span>
              </td>
              <td>
                <span class="fw-bold text-primary">{{ formatAmount(item.subtotal) }} {{ currencyCode }}</span>
              </td>
              <td>
                <div class="rate-display" v-if="getCurrentRate(item)">
                  <div class="small">
                    <span class="badge me-1" :class="getCurrentRateBadgeClass()">
                      {{ getCurrentRateLabel() }}
                    </span>
                    <span>{{ formatRate(getCurrentRate(item)) }}</span>
                  </div>
                </div>
                <div v-else class="text-muted small">
                  {{ $t('exchange.rate_not_available') }}
                </div>
              </td>
              <td class="text-center">
                <button
                  type="button"
                  class="btn btn-outline-danger btn-lg delete-btn"
                  @click="removeCombination(index)"
                  :title="$t('common.delete')"
                >
                  <i class="fas fa-times"></i>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 组合总计 -->
      <div class="combination-total mt-3">
        <div class="card border-primary">
          <div class="card-body py-2">
            <div class="d-flex justify-content-between align-items-center">
              <span class="fw-bold text-primary">
                <i class="fas fa-calculator me-2"></i>
                {{ $t('exchange.combination_total') }}:
              </span>
              <span class="h4 mb-0 text-primary fw-bold">
                {{ formatAmount(combinationTotal) }} {{ currencyCode }}
              </span>
            </div>
            <div class="text-muted small">
              {{ $t('exchange.total_items') }}: {{ combinationList.length }}
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 数量输入模态框 -->
    <div class="modal fade" id="quantityModal" tabindex="-1" aria-labelledby="quantityModalLabel" aria-hidden="true">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="quantityModalLabel">
              <i class="fas fa-calculator me-2"></i>
              {{ $t('exchange.enter_quantity') }}
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body" v-if="modalDenomination">
            <!-- 面值信息显示 -->
            <div class="denomination-info mb-4">
              <div class="card bg-light">
                <div class="card-body py-3">
                  <div class="d-flex align-items-center justify-content-center">
                    <i :class="modalDenomination.denomination_type === 'bill' ? 'fas fa-money-bill text-success me-3' : 'fas fa-coins text-warning me-3'" style="font-size: 2rem;"></i>
                    <div class="text-center">
                      <div class="h4 mb-1">{{ formatDenominationValue(modalDenomination.denomination_value) }} {{ currencyCode }}</div>
                      <div class="badge" :class="modalDenomination.denomination_type === 'bill' ? 'bg-success' : 'bg-warning'">
                        {{ $t(`exchange.${modalDenomination.denomination_type}`) }}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 数量输入 -->
            <div class="mb-3">
              <label for="modalQuantity" class="form-label fw-bold">{{ $t('exchange.quantity') }}</label>
              <div class="input-group input-group-lg">
                <span class="input-group-text">
                  <i :class="modalDenomination.denomination_type === 'bill' ? 'fas fa-money-bill' : 'fas fa-coins'"></i>
                </span>
                <input
                  type="number"
                  class="form-control"
                  id="modalQuantity"
                  v-model="modalQuantity"
                  @input="calculateModalTotal"
                  @keyup.enter="confirmQuantity"
                  min="1"
                  step="1"
                  ref="quantityInput"
                />
                <span class="input-group-text">
                  {{ $t(`exchange.${modalDenomination.denomination_type}_unit`) }}
                </span>
              </div>
            </div>

            <!-- 小计显示 -->
            <div class="subtotal-display" v-if="modalSubtotal > 0">
              <div class="card border-primary">
                <div class="card-body py-2">
                  <div class="d-flex justify-content-between align-items-center">
                    <span class="text-muted">{{ $t('exchange.subtotal') }}:</span>
                    <span class="h5 mb-0 text-primary fw-bold">
                      {{ formatAmount(modalSubtotal) }} {{ currencyCode }}
                    </span>
                  </div>
                  <div class="text-muted small text-center mt-1">
                    {{ modalQuantity }} {{ $t(`exchange.${modalDenomination.denomination_type}_unit`) }} ×
                    {{ formatDenominationValue(modalDenomination.denomination_value) }} =
                    {{ formatAmount(modalSubtotal) }}
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
              <i class="fas fa-times me-1"></i>
              {{ $t('common.cancel') }}
            </button>
            <button type="button" class="btn btn-primary" @click="confirmQuantity" :disabled="!modalQuantity || modalQuantity <= 0">
              <i class="fas fa-check me-1"></i>
              {{ $t('common.confirm') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DenominationSelector',
  props: {
    currencyId: {
      type: Number,
      required: true
    },
    currencyCode: {
      type: String,
      required: true
    },
    allowMultiple: {
      type: Boolean,
      default: false
    },
    value: {
      type: Object,
      default: null
    },
    exchangeMode: {
      type: String,
      default: ''
    }
  },
  data() {
    return {
      denominations: [],
      combinationList: [], // 多面值组合列表
      loading: false,

      // 模态框相关数据
      modalDenomination: null,
      modalQuantity: 1,
      modalSubtotal: 0,

      // 汇率数据
      denominationRates: {}
    }
  },
  computed: {
    combinationTotal() {
      return this.combinationList.reduce((sum, item) => sum + item.subtotal, 0)
    }
  },
  watch: {
    currencyId: {
      immediate: true,
      handler(newVal) {
        if (newVal) {
          this.loadDenominations()
          this.loadDenominationRates()
        }
      }
    },
    value: {
      immediate: true,
      handler(newVal) {
        if (newVal) {
          this.loadFromValue(newVal)
        }
      }
    }
  },
  methods: {
    async loadDenominations() {
      if (!this.currencyId) return
      
      this.loading = true
      try {
        const response = await this.$api.get(`/denominations/${this.currencyId}`)
        if (response.data.success) {
          this.denominations = response.data.data
        } else {
          this.$toast.error(response.data.message || '加载面值失败')
        }
      } catch (error) {
        console.error('加载面值失败:', error)
        this.$toast.error('加载面值失败')
      } finally {
        this.loading = false
      }
    },
    
    showQuantityModal(denomination) {
      this.modalDenomination = denomination
      this.modalQuantity = 1
      this.calculateModalTotal()

      // 显示模态框
      const modal = new window.bootstrap.Modal(document.getElementById('quantityModal'))
      modal.show()

      // 模态框显示后自动聚焦到输入框
      modal._element.addEventListener('shown.bs.modal', () => {
        this.$nextTick(() => {
          if (this.$refs.quantityInput) {
            this.$refs.quantityInput.focus()
            this.$refs.quantityInput.select()
          }
        })
      })
    },

    calculateModalTotal() {
      if (this.modalDenomination && this.modalQuantity > 0) {
        this.modalSubtotal = this.modalDenomination.denomination_value * this.modalQuantity
      } else {
        this.modalSubtotal = 0
      }
    },

    confirmQuantity() {
      if (!this.modalDenomination || !this.modalQuantity || this.modalQuantity <= 0) {
        return
      }

      // 获取面值汇率
      const rates = this.denominationRates[this.modalDenomination.id] || {}

      // 添加到组合列表
      const combinationItem = {
        denomination_id: this.modalDenomination.id,
        denomination_value: this.modalDenomination.denomination_value,
        denomination_type: this.modalDenomination.denomination_type,
        quantity: this.modalQuantity,
        subtotal: this.modalSubtotal,
        buy_rate: rates.buy_rate || null,
        sell_rate: rates.sell_rate || null,
        direction: this.exchangeMode || 'sell', // 默认交易方向
        currency_id: this.currencyId
      }

      this.combinationList.push(combinationItem)

      // 关闭模态框
      const modal = window.bootstrap.Modal.getInstance(document.getElementById('quantityModal'))
      if (modal) {
        modal.hide()
      }

      // 重置模态框数据
      this.modalDenomination = null
      this.modalQuantity = 1
      this.modalSubtotal = 0

      // 触发变更事件
      this.emitChange()

      // 显示成功提示
      this.$toast.success(this.$t('exchange.denomination_added_successfully'))
    },
    
    removeCombination(index) {
      this.combinationList.splice(index, 1)
      this.emitChange()
      this.$toast.success(this.$t('exchange.denomination_removed_successfully'))
    },

    clearAllCombinations() {
      if (confirm(this.$t('exchange.confirm_clear_all_combinations'))) {
        this.combinationList = []
        this.emitChange()
        this.$toast.success(this.$t('exchange.all_combinations_cleared'))
      }
    },

    async loadDenominationRates() {
      if (!this.currencyId) return

      try {
        const response = await this.$api.get('/denominations/rates', {
          params: { currency_id: this.currencyId }
        })

        if (response.data.success) {
          // 将汇率数据转换为以denomination_id为key的对象
          this.denominationRates = {}
          response.data.data.forEach(rate => {
            this.denominationRates[rate.denomination_id] = {
              buy_rate: rate.buy_rate,
              sell_rate: rate.sell_rate
            }
          })
          console.log('加载面值汇率成功:', this.denominationRates)
        }
      } catch (error) {
        console.error('加载面值汇率失败:', error)
      }
    },
    
    loadFromValue(value) {
      if (value && value.combinations) {
        // 加载组合列表数据
        this.combinationList = value.combinations || []
      }
    },
    
    emitChange() {
      const value = this.getValue()
      this.$emit('input', value)
      this.$emit('change', value)
    },

    getValue() {
      if (this.combinationList.length === 0) {
        return null
      }

      return {
        combinations: this.combinationList,
        total_amount: this.combinationTotal,
        currency_id: this.currencyId,
        currency_code: this.currencyCode
      }
    },
    
    formatDenominationValue(value) {
      return new Intl.NumberFormat('zh-CN', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
      }).format(value)
    },
    
    formatAmount(amount) {
      return new Intl.NumberFormat('zh-CN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(amount)
    },

    formatRate(rate) {
      if (!rate) return '---'
      return new Intl.NumberFormat('zh-CN', {
        minimumFractionDigits: 4,
        maximumFractionDigits: 4
      }).format(rate)
    },

    getCurrentRate(item) {
      // 根据每个项目的交易方向返回对应的汇率
      if (item.direction === 'sell') {
        // 网点买入外币，使用买入汇率
        return item.buy_rate
      } else if (item.direction === 'buy') {
        // 网点卖出外币，使用卖出汇率
        return item.sell_rate
      }
      return null
    },

    getCurrentRateLabel() {
      // 统一显示汇率标签
      return this.$t('exchange.rate')
    },

    getCurrentRateBadgeClass() {
      // 统一徽章样式
      return 'bg-primary'
    },

    updateItemDirection(index) {
      // 更新指定项目的交易方向
      const item = this.combinationList[index]
      if (item) {
        // 触发变更事件，通知父组件重新计算
        this.emitChange()
      }
    }
  }
}
</script>

<style scoped>
.denomination-selector {
  width: 100%;
}

.denomination-buttons {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.denomination-btn {
  padding: 0.75rem 0.5rem;
  text-align: center;
  border-radius: 0.5rem;
  transition: all 0.2s ease;
}

.denomination-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.denomination-btn.active {
  background-color: var(--bs-primary);
  border-color: var(--bs-primary);
  color: white;
}

.denomination-value {
  font-size: 1.1rem;
  font-weight: bold;
  margin-bottom: 0.25rem;
}

.denomination-type {
  font-size: 0.8rem;
  opacity: 0.8;
}

.total-amount-display .card {
  border-left: 4px solid var(--bs-primary);
}

.denomination-entry {
  padding: 0.5rem;
  border: 1px solid #e9ecef;
  border-radius: 0.375rem;
  background-color: #f8f9fa;
}

.combination-table {
  font-size: 0.9rem;
}

.combination-row:hover {
  background-color: #f8f9fa;
}

.delete-btn {
  padding: 0.5rem 0.75rem !important;
  font-size: 1.1rem !important;
  border-width: 2px !important;
}

.delete-btn:hover {
  transform: scale(1.1);
  transition: transform 0.2s ease;
}

.rate-display {
  font-size: 0.8rem;
}

.direction-select {
  min-width: 80px;
  font-size: 0.875rem;
}

.combination-total .card {
  border-left: 4px solid var(--bs-primary);
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.subtotal-display .card {
  border-left: 4px solid var(--bs-primary);
}

.denomination-info .card {
  border: 2px solid #e9ecef;
}

.modal-body {
  padding: 1.5rem;
}

.input-group-lg .form-control {
  font-size: 1.2rem;
  padding: 0.75rem 1rem;
}

.breakdown {
  font-size: 0.75rem;
  margin-top: 0.25rem;
}
</style>
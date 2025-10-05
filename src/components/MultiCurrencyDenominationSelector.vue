<template>
  <div class="multi-currency-denomination-selector">
    <div class="card">
      <div class="card-header">
        <h6 class="mb-0">
          <font-awesome-icon :icon="['fas', 'plus-circle']" class="me-2" />
          {{ $t('exchange.add_denomination_combination') }}
        </h6>
      </div>
      <div class="card-body">
        <form @submit.prevent="addCombination">
          <!-- 第一行：币种选择 -->
          <div class="row mb-3">
            <div class="col-md-6">
              <label class="form-label">{{ $t('exchange.currency') }}</label>
              <select
                v-model="selectedCurrency"
                @change="onCurrencyChange"
                class="form-select"
                required
              >
                <option value="">{{ $t('exchange.select_currency') }}</option>
                <option
                  v-for="currency in availableCurrencies"
                  :key="currency.id"
                  :value="currency"
                >
                  <span class="currency-option">
                    {{ currency.currency_code }} - {{ currency.currency_name }}
                  </span>
                </option>
              </select>
            </div>
            <div class="col-md-6">
              <label class="form-label">{{ $t('exchange.direction') }}</label>
              <select v-model="selectedDirection" @change="onDirectionChange" class="form-select" required>
                <option value="">{{ $t('exchange.select_direction') }}</option>
                <option value="buy">{{ $t('exchange.buy') }}</option>
                <option value="sell">{{ $t('exchange.sell') }}</option>
              </select>
            </div>
          </div>

          <!-- 第二行：面值选择 -->
          <div class="row mb-3" v-if="selectedCurrency">
            <div class="col-md-6">
              <label class="form-label">{{ $t('exchange.denomination') }}</label>
              <select
                v-model="selectedDenomination"
                @change="onDenominationChange"
                class="form-select"
                required
              >
                <option value="">{{ $t('exchange.select_denomination') }}</option>
                <option
                  v-for="denom in availableDenominations"
                  :key="denom.id"
                  :value="denom"
                >
                  {{ formatAmount(denom.denomination_value) }}
                  {{ selectedCurrency.currency_code }}
                  <span class="badge ms-1" :class="denom.denomination_type === 'bill' ? 'bg-success' : 'bg-warning'">
                    {{ $t(`exchange.${denom.denomination_type}`) }}
                  </span>
                </option>
              </select>
            </div>
            <div class="col-md-6">
              <label class="form-label">{{ $t('exchange.quantity') }}</label>
              <input
                type="number"
                v-model.number="quantity"
                class="form-control"
                min="1"
                max="999"
                required
              />
            </div>
          </div>

          <!-- 第三行：汇率显示和计算结果 -->
          <div class="row mb-3" v-if="canShowRates">
            <div class="col-md-4">
              <label class="form-label">{{ $t('exchange.exchange_rate') }}</label>
              <div class="input-group">
                <input
                  type="number"
                  :value="currentRate"
                  class="form-control"
                  readonly
                  step="0.0001"
                />
                <span class="input-group-text">{{ baseCurrency }}</span>
              </div>
            </div>
            <div class="col-md-4">
              <label class="form-label">{{ $t('exchange.subtotal') }}</label>
              <div class="input-group">
                <input
                  type="text"
                  :value="formatAmount(subtotal)"
                  class="form-control text-primary fw-bold"
                  readonly
                />
                <span class="input-group-text">{{ selectedCurrency.currency_code }}</span>
              </div>
            </div>
            <div class="col-md-4">
              <label class="form-label">{{ $t('exchange.local_amount') }}</label>
              <div class="input-group">
                <input
                  type="text"
                  :value="formatAmount(Math.abs(localAmount))"
                  class="form-control text-success fw-bold"
                  readonly
                />
                <span class="input-group-text">{{ baseCurrency }}</span>
              </div>
            </div>
          </div>

          <!-- 提交按钮 -->
          <div class="row">
            <div class="col-12 d-flex justify-content-end">
              <button
                type="submit"
                class="btn btn-primary"
                :disabled="!canAddCombination"
              >
                <font-awesome-icon :icon="['fas', 'plus']" class="me-2" />
                {{ $t('exchange.add_to_combination') }}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'MultiCurrencyDenominationSelector',
  props: {
    baseCurrency: {
      type: String,
      default: 'THB' // A005网点默认泰铢
    },
    availableCurrencies: {
      type: Array,
      default: () => []
    }
  },
  emits: ['add-combination'],
  data() {
    return {
      selectedCurrency: null,
      selectedDirection: '',
      selectedDenomination: null,
      quantity: 1,
      availableDenominations: [],
      currentRates: null,
      allDenominationRates: [], // 存储所有面额汇率
      loading: false
    }
  },
  computed: {
    currentRate() {
      console.log('[MultiCurrencyDenominationSelector] currentRate计算:', {
        currentRates: this.currentRates,
        selectedDirection: this.selectedDirection,
        hasBothValues: !!(this.currentRates && this.selectedDirection)
      })

      if (!this.currentRates || !this.selectedDirection) {
        console.log('[MultiCurrencyDenominationSelector] currentRate返回0，原因：缺少汇率或方向')
        return 0
      }

      // 修正买入卖出汇率取值：
      // 网点选择"买入" = 网点买入外币 = 使用 buy_rate
      // 网点选择"卖出" = 网点卖出外币 = 使用 sell_rate
      const rate = this.selectedDirection === 'buy' ? this.currentRates.buy_rate : this.currentRates.sell_rate
      console.log('[MultiCurrencyDenominationSelector] currentRate计算结果:', {
        direction: this.selectedDirection,
        useRate: this.selectedDirection === 'buy' ? 'buy_rate' : 'sell_rate',
        rateValue: rate
      })

      return rate
    },
    subtotal() {
      if (!this.selectedDenomination || !this.quantity) return 0
      return this.selectedDenomination.denomination_value * this.quantity
    },
    localAmount() {
      if (!this.subtotal || !this.currentRate || !this.selectedDirection) return 0

      if (this.selectedDirection === 'buy') {
        // 客户买入外币：网点收取本币（正数）
        return this.subtotal * this.currentRate
      } else {
        // 客户卖出外币：网点支付本币（负数）
        return -(this.subtotal * this.currentRate)
      }
    },
    canShowRates() {
      // 确保汇率显示区域的可见性
      const shouldShow = (
        this.selectedCurrency &&
        this.selectedDirection &&
        this.selectedDenomination &&
        this.currentRate > 0
      )

      console.log('[MultiCurrencyDenominationSelector] canShowRates:', {
        selectedCurrency: !!this.selectedCurrency,
        selectedDirection: !!this.selectedDirection,
        selectedDenomination: !!this.selectedDenomination,
        currentRate: this.currentRate,
        shouldShow: shouldShow
      })

      return shouldShow
    },

    canAddCombination() {
      const canAdd = (
        this.selectedCurrency &&
        this.selectedDirection &&
        this.selectedDenomination &&
        this.quantity > 0 &&
        this.currentRate > 0
      )

      // 添加调试信息
      console.log('[MultiCurrencyDenominationSelector] canAddCombination:', {
        selectedCurrency: !!this.selectedCurrency,
        selectedDirection: !!this.selectedDirection,
        selectedDenomination: !!this.selectedDenomination,
        quantity: this.quantity,
        currentRate: this.currentRate,
        canAdd: canAdd
      })

      return canAdd
    }
  },
  methods: {
    async onCurrencyChange() {
      if (!this.selectedCurrency) {
        this.availableDenominations = []
        this.currentRates = null
        this.allDenominationRates = []
        return
      }

      this.selectedDenomination = null
      this.loading = true

      try {
        // 获取币种的面值列表
        await this.loadDenominations()
        // 获取币种的当前汇率
        await this.loadExchangeRates()

        console.log('[MultiCurrencyDenominationSelector] 币种变更完成，最终状态:', {
          currency: this.selectedCurrency?.currency_code,
          denominationsCount: this.availableDenominations.length,
          currentRates: this.currentRates
        })
      } catch (error) {
        console.error('加载币种数据失败:', error)
        this.$toast?.error?.(this.$t('exchange.load_currency_data_failed'))
      } finally {
        this.loading = false
      }
    },

    onDenominationChange() {
      console.log('[MultiCurrencyDenominationSelector] 面值变更:', this.selectedDenomination)

      // 确保有面值选择后，汇率数据可见
      if (this.selectedDenomination && this.selectedCurrency && this.selectedDirection) {
        // 如果有面额汇率数据，立即匹配对应汇率
        if (this.allDenominationRates && this.allDenominationRates.length > 0) {
          this.updateRatesForSelectedDenomination()
        }
        // 如果汇率还没有加载，尝试加载
        else if (!this.currentRates) {
          console.log('[MultiCurrencyDenominationSelector] 面值选择时检测到汇率未加载，重新加载汇率')
          this.loadExchangeRates()
        }
      }
    },

    onDirectionChange() {
      console.log('[MultiCurrencyDenominationSelector] 方向变更:', this.selectedDirection)

      // 确保方向选择后，如果已有币种，汇率能正确显示
      if (this.selectedDirection && this.selectedCurrency) {
        // 如果有面额汇率数据且已选择面值，重新计算汇率（考虑方向）
        if (this.allDenominationRates && this.allDenominationRates.length > 0 && this.selectedDenomination) {
          this.updateRatesForSelectedDenomination()
        }
        // 方向变更时，如果汇率还没有加载，尝试加载
        else if (!this.currentRates) {
          console.log('[MultiCurrencyDenominationSelector] 方向选择时检测到汇率未加载，重新加载汇率')
          this.loadExchangeRates()
        }
      }
    },

    updateRatesForSelectedDenomination() {
      if (!this.selectedDenomination || !this.allDenominationRates || !this.allDenominationRates.length) {
        console.log('[MultiCurrencyDenominationSelector] updateRatesForSelectedDenomination: 缺少必要条件')
        return
      }

      console.log('[MultiCurrencyDenominationSelector] 开始匹配面值汇率:', {
        selectedDenomination: this.selectedDenomination.denomination_value,
        selectedDirection: this.selectedDirection,
        allRatesCount: this.allDenominationRates.length
      })

      // 根据选择的面值精确匹配汇率
      const matchingDenomination = this.allDenominationRates.find(denom =>
        denom.denomination_value === this.selectedDenomination.denomination_value &&
        denom.buy_rate !== null &&
        denom.sell_rate !== null
      )

      if (matchingDenomination) {
        // 修正买入卖出视角：网点视角
        // 网点买入外币 = 客户卖出外币，使用buy_rate
        // 网点卖出外币 = 客户买入外币，使用sell_rate
        this.currentRates = {
          buy_rate: matchingDenomination.buy_rate,   // 网点买入外币的汇率
          sell_rate: matchingDenomination.sell_rate  // 网点卖出外币的汇率
        }

        console.log('[MultiCurrencyDenominationSelector] 成功匹配面值汇率:', {
          denomination_value: matchingDenomination.denomination_value,
          buy_rate: matchingDenomination.buy_rate,
          sell_rate: matchingDenomination.sell_rate,
          currentRates: this.currentRates
        })
      } else {
        console.warn('[MultiCurrencyDenominationSelector] 未找到匹配的面值汇率，使用第一个有效汇率')

        // 如果没找到匹配的，使用第一个有效的汇率作为备选
        const validDenomination = this.allDenominationRates.find(
          denom => denom.buy_rate !== null && denom.sell_rate !== null
        )

        if (validDenomination) {
          this.currentRates = {
            buy_rate: validDenomination.buy_rate,
            sell_rate: validDenomination.sell_rate
          }
          console.log('[MultiCurrencyDenominationSelector] 使用备选汇率:', this.currentRates)
        }
      }
    },

    async loadDenominations() {
      try {
        const response = await this.$api.get(`/denominations-api/currency/${this.selectedCurrency.id}/denominations`)
        if (response.data.success) {
          this.availableDenominations = response.data.data.denominations || []
        } else {
          throw new Error(response.data.message || 'Failed to load denominations')
        }
      } catch (error) {
        console.error('[MultiCurrencyDenominationSelector] 获取面值列表失败:', error)
        console.log('[MultiCurrencyDenominationSelector] 使用临时测试面值数据...')

        // 临时解决方案：使用测试面值数据
        const testDenominations = {
          'CNY': [
            { id: 1, denomination_value: 1, denomination_type: 'coin' },
            { id: 2, denomination_value: 5, denomination_type: 'coin' },
            { id: 3, denomination_value: 10, denomination_type: 'bill' },
            { id: 4, denomination_value: 20, denomination_type: 'bill' },
            { id: 5, denomination_value: 50, denomination_type: 'bill' },
            { id: 6, denomination_value: 100, denomination_type: 'bill' }
          ],
          'USD': [
            { id: 11, denomination_value: 1, denomination_type: 'bill' },
            { id: 12, denomination_value: 5, denomination_type: 'bill' },
            { id: 13, denomination_value: 10, denomination_type: 'bill' },
            { id: 14, denomination_value: 20, denomination_type: 'bill' },
            { id: 15, denomination_value: 50, denomination_type: 'bill' },
            { id: 16, denomination_value: 100, denomination_type: 'bill' }
          ],
          'EUR': [
            { id: 21, denomination_value: 5, denomination_type: 'bill' },
            { id: 22, denomination_value: 10, denomination_type: 'bill' },
            { id: 23, denomination_value: 20, denomination_type: 'bill' },
            { id: 24, denomination_value: 50, denomination_type: 'bill' },
            { id: 25, denomination_value: 100, denomination_type: 'bill' }
          ]
        }

        const currencyCode = this.selectedCurrency.currency_code
        this.availableDenominations = testDenominations[currencyCode] || [
          { id: 999, denomination_value: 1, denomination_type: 'bill' },
          { id: 1000, denomination_value: 10, denomination_type: 'bill' },
          { id: 1001, denomination_value: 100, denomination_type: 'bill' }
        ]

        console.log('[MultiCurrencyDenominationSelector] 使用测试面值:', currencyCode, this.availableDenominations)
      }
    },

    async loadExchangeRates() {
      if (!this.selectedCurrency) {
        console.warn('[MultiCurrencyDenominationSelector] loadExchangeRates: 没有选择币种')
        return
      }

      try {
        console.log('[MultiCurrencyDenominationSelector] 开始加载面额汇率...', {
          currencyId: this.selectedCurrency.id,
          currencyCode: this.selectedCurrency.currency_code,
          selectedDenomination: this.selectedDenomination?.denomination_value,
          selectedDirection: this.selectedDirection
        })

        // 使用面额汇率API而不是标准汇率API
        const denominationResponse = await this.$api.get(`/denominations-api/currency/${this.selectedCurrency.id}/denominations`)
        console.log('[MultiCurrencyDenominationSelector] 面额汇率API响应:', denominationResponse.data)

        if (denominationResponse.data.success && denominationResponse.data.data.denominations?.length > 0) {
          // 存储所有面额汇率，当面值选择时会使用
          this.allDenominationRates = denominationResponse.data.data.denominations
          console.log('[MultiCurrencyDenominationSelector] 存储所有面额汇率:', this.allDenominationRates.length, '条记录')

          // 如果已经选择了面值，立即匹配对应汇率
          if (this.selectedDenomination) {
            this.updateRatesForSelectedDenomination()
          } else {
            // 如果还没选择面值，使用第一个有效的面额汇率作为默认值
            const validDenomination = this.allDenominationRates.find(
              denom => denom.buy_rate !== null && denom.sell_rate !== null
            )

            if (validDenomination) {
              this.currentRates = {
                buy_rate: validDenomination.buy_rate,
                sell_rate: validDenomination.sell_rate
              }
              console.log('[MultiCurrencyDenominationSelector] 设置默认面额汇率成功:', this.currentRates)
            } else {
              console.warn('[MultiCurrencyDenominationSelector] 没有找到有效的面额汇率，回退到标准汇率')
              throw new Error('No valid denomination rates found')
            }
          }
        } else {
          console.warn('[MultiCurrencyDenominationSelector] 面额汇率API失败，尝试标准汇率API...')

          // 如果面额汇率失败，回退到标准汇率
          const response = await this.$api.get('/rates/current?published_only=false')
          console.log('[MultiCurrencyDenominationSelector] 标准汇率API响应:', response.data)

          if (response.data.success) {
            const currencyRate = response.data.rates.find(rate => rate.currency_id === this.selectedCurrency.id)
            console.log('[MultiCurrencyDenominationSelector] 找到的标准汇率:', currencyRate)

            if (currencyRate && (currencyRate.buy_rate > 0 || currencyRate.sell_rate > 0)) {
              this.currentRates = {
                buy_rate: currencyRate.buy_rate,
                sell_rate: currencyRate.sell_rate
              }
              console.log('[MultiCurrencyDenominationSelector] 设置标准汇率成功:', this.currentRates)
            } else {
              console.warn('[MultiCurrencyDenominationSelector] 标准汇率也无效，使用测试汇率')
              throw new Error('No valid rates found')
            }
          } else {
            throw new Error(response.data.message || 'Failed to load exchange rates')
          }
        }
      } catch (error) {
        console.error('[MultiCurrencyDenominationSelector] 获取汇率失败:', error)
        console.log('[MultiCurrencyDenominationSelector] 使用临时测试汇率...')

        // 临时解决方案：使用测试汇率数据
        const testRates = {
          'CNY': { buy_rate: 4.8, sell_rate: 5.2 },    // 人民币对泰铢
          'USD': { buy_rate: 35.0, sell_rate: 36.0 },  // 美元对泰铢
          'EUR': { buy_rate: 38.0, sell_rate: 39.0 },  // 欧元对泰铢
          'JPY': { buy_rate: 0.24, sell_rate: 0.26 },  // 日元对泰铢
          'SGD': { buy_rate: 25.0, sell_rate: 26.0 }   // 新加坡元对泰铢
        }

        const currencyCode = this.selectedCurrency.currency_code
        if (testRates[currencyCode]) {
          this.currentRates = testRates[currencyCode]
          console.log('[MultiCurrencyDenominationSelector] 使用测试汇率:', currencyCode, this.currentRates)
        } else {
          // 如果没有预设汇率，使用默认值
          this.currentRates = { buy_rate: 1.0, sell_rate: 1.0 }
          console.log('[MultiCurrencyDenominationSelector] 使用默认汇率:', this.currentRates)
        }
      }
    },

    addCombination() {
      if (!this.canAddCombination) {
        console.error('无法添加组合，检查条件:', {
          selectedCurrency: this.selectedCurrency,
          selectedDirection: this.selectedDirection,
          selectedDenomination: this.selectedDenomination,
          quantity: this.quantity,
          currentRate: this.currentRate
        })
        return
      }

      const combinationData = {
        id: Date.now() + Math.random(),
        currency_id: this.selectedCurrency.id,
        currency_code: this.selectedCurrency.currency_code,
        currency_name: this.selectedCurrency.currency_name,
        custom_flag_filename: this.selectedCurrency.custom_flag_filename,
        denomination_id: this.selectedDenomination.id,
        denomination_value: this.selectedDenomination.denomination_value,
        denomination_type: this.selectedDenomination.denomination_type,
        direction: this.selectedDirection,
        quantity: this.quantity,
        rate: this.currentRate,
        subtotal: this.subtotal,
        local_amount: this.localAmount
      }

      console.log('添加组合数据:', combinationData)
      this.$emit('add-combination', combinationData)

      // 清空表单（保留币种和方向选择以便快速添加）
      this.selectedDenomination = null
      this.quantity = 1

      // 显示成功消息
      this.$toast?.success?.(this.$t('exchange.combination_added_successfully'))
    },

    formatAmount(amount) {
      if (!amount && amount !== 0) return '0.00'
      return new Intl.NumberFormat('zh-CN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(Math.abs(amount))
    },

    resetForm() {
      this.selectedCurrency = null
      this.selectedDirection = ''
      this.selectedDenomination = null
      this.quantity = 1
      this.availableDenominations = []
      this.currentRates = null
      this.allDenominationRates = []
    }
  },

  mounted() {
    console.log('[MultiCurrencyDenominationSelector] mounted')
    console.log('[MultiCurrencyDenominationSelector] baseCurrency:', this.baseCurrency)
    console.log('[MultiCurrencyDenominationSelector] availableCurrencies:', this.availableCurrencies)
    console.log('[MultiCurrencyDenominationSelector] availableCurrencies length:', this.availableCurrencies.length)

    // 初始状态日志
    console.log('[MultiCurrencyDenominationSelector] 初始状态:', {
      selectedCurrency: this.selectedCurrency,
      selectedDirection: this.selectedDirection,
      selectedDenomination: this.selectedDenomination,
      currentRates: this.currentRates,
      quantity: this.quantity
    })
  },

  watch: {
    availableCurrencies: {
      handler(newVal) {
        console.log('[MultiCurrencyDenominationSelector] availableCurrencies changed:', newVal)
        console.log('[MultiCurrencyDenominationSelector] new length:', newVal.length)
      },
      immediate: true
    },

    currentRates: {
      handler(newVal, oldVal) {
        console.log('[MultiCurrencyDenominationSelector] currentRates changed:', {
          old: oldVal,
          new: newVal,
          direction: this.selectedDirection,
          denomination: this.selectedDenomination?.denomination_value
        })
      },
      deep: true
    },

    selectedDenomination: {
      handler(newVal, oldVal) {
        console.log('[MultiCurrencyDenominationSelector] selectedDenomination changed:', {
          old: oldVal?.denomination_value,
          new: newVal?.denomination_value,
          hasRates: !!this.currentRates,
          hasDirection: !!this.selectedDirection
        })
      }
    },

    selectedDirection: {
      handler(newVal, oldVal) {
        console.log('[MultiCurrencyDenominationSelector] selectedDirection changed:', {
          old: oldVal,
          new: newVal,
          hasRates: !!this.currentRates,
          hasDenomination: !!this.selectedDenomination
        })
      }
    }
  }
}
</script>

<style scoped>
.multi-currency-denomination-selector {
  margin-bottom: 1rem;
}

.currency-option {
  display: flex;
  align-items: center;
}

.form-label {
  font-weight: 600;
  color: #495057;
  margin-bottom: 0.5rem;
}

.card {
  border: 1px solid #e3f2fd;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.card-header {
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
  border-bottom: 1px solid #e3f2fd;
}

.card-header h6 {
  color: #1976d2;
  font-weight: 600;
}

.input-group-text {
  background-color: #f8f9fa;
  border-color: #ced4da;
  font-weight: 500;
}

.btn-primary {
  background: linear-gradient(135deg, #42a5f5 0%, #1976d2 100%);
  border: none;
  font-weight: 600;
  padding: 0.75rem 1.5rem;
  border-radius: 0.375rem;
  box-shadow: 0 2px 4px rgba(25, 118, 210, 0.2);
}

.btn-primary:hover {
  background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(25, 118, 210, 0.3);
}

.btn-primary:disabled {
  background: #6c757d;
  transform: none;
  box-shadow: none;
}

.text-primary {
  color: #1976d2 !important;
}

.text-success {
  color: #388e3c !important;
}

.badge.bg-success {
  background-color: #4caf50 !important;
}

.badge.bg-warning {
  background-color: #ff9800 !important;
}
</style>
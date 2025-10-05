<template>
  <div class="container-fluid py-4">
    <div class="row">
      <div class="col-12">
        <!-- 页面标题 -->
        <div class="d-flex justify-content-between align-items-center mb-4">
          <h2 class="page-title-bold">
            <font-awesome-icon :icon="['fas', 'exchange-alt']" class="me-2" />
            {{ $t('exchange.dual_direction_title') }}
          </h2>
          <div class="d-flex gap-2">
            <button
              type="button"
              class="btn btn-outline-secondary"
              @click="goToSingleTransaction"
            >
              <font-awesome-icon :icon="['fas', 'arrow-left']" class="me-2" />
              {{ $t('exchange.single_transaction') }}
            </button>
          </div>
        </div>

        <!-- 主界面区域 -->
        <div class="row">
          <!-- 左侧：币种和面值选择器 + 操作指导 -->
          <div class="col-md-4">
            <!-- 操作指导卡片 -->
            <div class="card mb-3 guidance-card">
              <div class="card-header">
                <h6 class="mb-0">
                  <font-awesome-icon :icon="['fas', 'info-circle']" class="me-2" />
                  {{ $t('exchange.operation_guidance') }}
                </h6>
              </div>
              <div class="card-body">
                <div class="operation-steps">
                  <div class="step">
                    <span class="step-number">1</span>
                    <span class="step-text">{{ $t('exchange.select_currency_and_denomination') }}</span>
                  </div>
                  <div class="step">
                    <span class="step-number">2</span>
                    <span class="step-text">{{ $t('exchange.add_to_combination') }}</span>
                  </div>
                  <div class="step">
                    <span class="step-number">3</span>
                    <span class="step-text">{{ $t('exchange.fill_customer_info') }}</span>
                  </div>
                  <div class="step">
                    <span class="step-number">4</span>
                    <span class="step-text">{{ $t('exchange.validate_and_execute') }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 多币种面值选择器 -->
            <MultiCurrencyDenominationSelector
              :base-currency="baseCurrency"
              :available-currencies="availableCurrencies"
              @add-combination="onAddCombination"
              ref="denominationSelector"
            />

            <!-- 币种余额信息 -->
            <div class="card mt-3 balance-info-card" v-if="denominationCombinations.length > 0">
              <div class="card-header">
                <h6 class="mb-0">
                  <font-awesome-icon :icon="['fas', 'coins']" class="me-2" />
                  {{ $t('exchange.currency_balance') }}
                </h6>
              </div>
              <div class="card-body">
                <div v-for="currencyInfo in involvedCurrencies" :key="currencyInfo.currency_id" class="balance-item mb-2">
                  <div class="d-flex justify-content-between align-items-center">
                    <div class="currency-info">
                      <img
                        v-if="currencyInfo.custom_flag_filename"
                        :src="`/flags/${currencyInfo.custom_flag_filename}`"
                        :alt="currencyInfo.currency_code"
                        class="currency-flag me-2"
                        @error="$event.target.style.display='none'"
                      >
                      <span class="currency-name">{{ currencyInfo.currency_name }}</span>
                      <span class="currency-code text-muted small ms-1">({{ currencyInfo.currency_code }})</span>
                      <span class="expense-type-badge badge ms-2"
                            :class="{
                              'bg-primary': currencyInfo.expense_type === 'base_currency',
                              'bg-success': currencyInfo.expense_type === 'foreign_currency'
                            }">
                        {{ currencyInfo.expense_type === 'base_currency' ? $t('exchange.paying_currency') : $t('exchange.stock_currency') }}
                      </span>
                    </div>
                    <div class="balance-info text-end">
                      <div class="current-balance"
                           :class="{ 'text-danger': currencyInfo.balance < currencyInfo.required }">{{ formatAmount(currencyInfo.balance) }}</div>
                      <div class="balance-label">{{ $t('exchange.current_balance') }}</div>
                    </div>
                  </div>
                  <div v-if="currencyInfo.required > 0" class="required-amount mt-1">
                    <small class="text-muted">{{ $t('exchange.required') }}: {{ formatAmount(currencyInfo.required) }}</small>
                    <small v-if="currencyInfo.balance < currencyInfo.required" class="text-danger ms-2">
                      ({{ $t('exchange.shortage_amount') }}: {{ formatAmount(currencyInfo.required - currencyInfo.balance) }})
                    </small>
                  </div>
                </div>
              </div>
            </div>

            <!-- 验证错误提示 -->
            <div v-if="validationError" class="card mt-3 error-card">
              <div class="card-header bg-danger text-white">
                <h6 class="mb-0">
                  <font-awesome-icon :icon="['fas', 'exclamation-triangle']" class="me-2" />
                  {{ $t('exchange.validation_error') }}
                </h6>
              </div>
              <div class="card-body">
                <div class="alert alert-danger mb-0">
                  {{ validationError }}
                </div>
              </div>
            </div>

            <!-- 阈值警告提示 -->
            <div v-if="thresholdWarnings && thresholdWarnings.length > 0" class="card mt-3 warning-card">
              <div class="card-header"
                   :class="{
                     'bg-warning text-dark': !hasCriticalWarnings,
                     'bg-danger text-white': hasCriticalWarnings
                   }">
                <h6 class="mb-0">
                  <font-awesome-icon :icon="['fas', 'exclamation-triangle']" class="me-2" />
                  {{ hasCriticalWarnings ? $t('exchange.critical_threshold_warnings') : $t('exchange.threshold_warnings') }}
                </h6>
              </div>
              <div class="card-body">
                <div v-for="warning in thresholdWarnings" :key="warning.currency_id"
                     :class="{
                       'alert alert-warning': warning.warning_level === 'warning',
                       'alert alert-danger': warning.warning_level === 'critical'
                     }"
                     class="mb-2">
                  <div class="d-flex align-items-center">
                    <img
                      v-if="getCurrencyFlag(warning.currency_code)"
                      :src="getCurrencyFlag(warning.currency_code)"
                      :alt="warning.currency_code"
                      class="currency-flag me-2"
                      style="width: 20px; height: 15px;"
                      @error="$event.target.style.display='none'"
                    >
                    <div class="flex-grow-1">
                      <strong>{{ warning.currency_name }} ({{ warning.currency_code }})</strong>
                      <div class="mt-1">{{ warning.warning_message }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

          </div>

          <!-- 右侧：面值组合管理器 -->
          <div class="col-md-8">
            <!-- 面值组合管理器 -->
            <DenominationCombinationManager
              :base-currency="baseCurrency"
              @change="onCombinationsChange"
              ref="combinationManager"
            />

            <!-- 客户信息输入 -->
            <div class="card mt-3" v-if="denominationCombinations.length > 0">
              <div class="card-header">
                <h6 class="mb-0">
                  <font-awesome-icon :icon="['fas', 'user']" class="me-2" />
                  {{ $t('exchange.customer_information') }}
                </h6>
              </div>
              <div class="card-body">
                <div class="row">
                  <div class="col-md-6">
                    <label class="form-label">{{ $t('exchange.customer_name') }} *</label>
                    <input
                      type="text"
                      v-model="customerInfo.name"
                      class="form-control"
                      :placeholder="$t('exchange.enter_customer_name')"
                      required
                    />
                  </div>
                  <div class="col-md-6">
                    <label class="form-label">{{ $t('exchange.customer_id') }}</label>
                    <input
                      type="text"
                      v-model="customerInfo.id_number"
                      class="form-control"
                      :placeholder="$t('exchange.enter_customer_id')"
                    />
                  </div>
                </div>
                <div class="row mt-3">
                  <div class="col-md-6">
                    <label class="form-label">{{ $t('exchange.customer_country') }}</label>
                    <select v-model="customerInfo.country_code" class="form-select">
                      <option value="">{{ $t('exchange.select_country') }}</option>
                      <option
                        v-for="country in countries"
                        :key="country.country_code"
                        :value="country.country_code"
                      >
                        {{ country.country_name }}
                      </option>
                    </select>
                  </div>
                  <div class="col-md-6">
                    <label class="form-label">{{ $t('exchange.customer_address') }}</label>
                    <input
                      type="text"
                      v-model="customerInfo.address"
                      class="form-control"
                      :placeholder="$t('exchange.enter_customer_address')"
                    />
                  </div>
                </div>
                <div class="row mt-3">
                  <div class="col-12">
                    <label class="form-label">{{ $t('exchange.remarks') }}</label>
                    <textarea
                      v-model="customerInfo.remarks"
                      class="form-control"
                      rows="2"
                      :placeholder="$t('exchange.enter_remarks')"
                    ></textarea>
                  </div>
                </div>

                <!-- 付款方式选择 -->
                <div class="row mt-3">
                  <div class="col-12">
                    <label class="form-label">{{ $t('exchange.payment_method') }}</label>
                    <div class="d-flex gap-3 flex-wrap">
                      <div class="form-check">
                        <input
                          class="form-check-input"
                          type="radio"
                          name="paymentMethod"
                          id="paymentCash"
                          value="cash"
                          v-model="customerInfo.payment_method"
                        >
                        <label class="form-check-label" for="paymentCash">
                          {{ $t('exchange.payment_cash') }}
                        </label>
                      </div>
                      <div class="form-check">
                        <input
                          class="form-check-input"
                          type="radio"
                          name="paymentMethod"
                          id="paymentBankTransfer"
                          value="bank_transfer"
                          v-model="customerInfo.payment_method"
                        >
                        <label class="form-check-label" for="paymentBankTransfer">
                          {{ $t('exchange.payment_bank_transfer') }}
                        </label>
                      </div>
                      <div class="form-check">
                        <input
                          class="form-check-input"
                          type="radio"
                          name="paymentMethod"
                          id="paymentFcdAccount"
                          value="fcd_account"
                          v-model="customerInfo.payment_method"
                        >
                        <label class="form-check-label" for="paymentFcdAccount">
                          {{ $t('exchange.payment_fcd_account') }}
                        </label>
                      </div>
                      <div class="form-check">
                        <input
                          class="form-check-input"
                          type="radio"
                          name="paymentMethod"
                          id="paymentOther"
                          value="other"
                          v-model="customerInfo.payment_method"
                        >
                        <label class="form-check-label" for="paymentOther">
                          {{ $t('exchange.payment_other') }}
                        </label>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- 其他付款方式备注 (仅当选择"其他"时显示) -->
                <div class="row mt-2" v-if="customerInfo.payment_method === 'other'">
                  <div class="col-12">
                    <input
                      type="text"
                      v-model="customerInfo.payment_method_note"
                      class="form-control"
                      :placeholder="$t('exchange.payment_other_note')"
                      maxlength="200"
                    />
                  </div>
                </div>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="card mt-3" v-if="denominationCombinations.length > 0">
              <div class="card-body">
                <div class="d-flex justify-content-between">
                  <button
                    type="button"
                    class="btn btn-outline-danger"
                    @click="clearAllCombinations"
                  >
                    <font-awesome-icon :icon="['fas', 'trash']" class="me-2" />
                    {{ $t('exchange.clear_all') }}
                  </button>
                  <div class="d-flex gap-2">
                    <button
                      type="button"
                      class="btn btn-outline-primary"
                      @click="validateTransaction"
                      :disabled="loading"
                    >
                      <font-awesome-icon :icon="['fas', 'check-circle']" class="me-2" />
                      {{ $t('exchange.validate_transaction') }}
                    </button>
                    <button
                      type="button"
                      class="btn btn-primary"
                      @click="executeTransaction"
                      :disabled="!canExecuteTransaction || loading"
                    >
                      <font-awesome-icon
                        :icon="loading ? ['fas', 'spinner'] : ['fas', 'handshake']"
                        :class="{ 'fa-spin': loading }"
                        class="me-2"
                      />
                      {{ loading ? $t('exchange.processing') : $t('exchange.execute_transaction') }}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 空状态提示 -->
        <div v-if="denominationCombinations.length === 0" class="row mt-4">
          <div class="col-12">
            <div class="text-center py-5">
              <font-awesome-icon :icon="['fas', 'coins']" class="fa-3x text-muted mb-3" />
              <h5 class="text-muted">{{ $t('exchange.no_combinations_selected') }}</h5>
              <p class="text-muted">{{ $t('exchange.dual_direction_hint') }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 交易确认模态框 -->
    <div class="modal fade" id="confirmModal" tabindex="-1" aria-labelledby="confirmModalLabel" aria-hidden="true">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="confirmModalLabel">
              <font-awesome-icon :icon="['fas', 'handshake']" class="me-2" />
              {{ $t('exchange.confirm_dual_direction_transaction') }}
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <div v-if="transactionSummary">
              <!-- 客户信息 -->
              <div class="mb-4">
                <h6 class="text-primary">{{ $t('exchange.customer_information') }}</h6>
                <div class="table-responsive">
                  <table class="table table-sm">
                    <tr>
                      <td width="30%">{{ $t('exchange.customer_name') }}:</td>
                      <td>{{ customerInfo.name }}</td>
                    </tr>
                    <tr v-if="customerInfo.id_number">
                      <td>{{ $t('exchange.customer_id') }}:</td>
                      <td>{{ customerInfo.id_number }}</td>
                    </tr>
                  </table>
                </div>
              </div>

              <!-- 交易总结 -->
              <div v-for="(total, currency) in transactionSummary.totals" :key="currency" class="mb-3">
                <h6 class="text-primary">{{ currency }} {{ $t('exchange.transaction_summary') }}</h6>
                <div class="table-responsive">
                  <table class="table table-sm table-bordered">
                    <tr v-if="total.buy_amount > 0">
                      <td>{{ $t('exchange.customer_buy') }}:</td>
                      <td class="text-success fw-bold">{{ formatAmount(total.buy_amount) }} {{ currency }}</td>
                      <td class="text-primary">{{ formatAmount(total.buy_local) }} {{ baseCurrency }}</td>
                    </tr>
                    <tr v-if="total.sell_amount > 0">
                      <td>{{ $t('exchange.customer_sell') }}:</td>
                      <td class="text-warning fw-bold">{{ formatAmount(total.sell_amount) }} {{ currency }}</td>
                      <td class="text-primary">{{ formatAmount(total.sell_local) }} {{ baseCurrency }}</td>
                    </tr>
                    <tr class="table-info">
                      <td>{{ $t('exchange.net_result') }}:</td>
                      <td class="fw-bold">{{ formatAmount(Math.abs(total.net_amount)) }} {{ currency }}</td>
                      <td class="fw-bold">{{ formatAmount(Math.abs(total.local_amount)) }} {{ baseCurrency }}</td>
                    </tr>
                  </table>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
              <font-awesome-icon :icon="['fas', 'times']" class="me-2" />
              {{ $t('common.cancel') }}
            </button>
            <button type="button" class="btn btn-primary" @click="confirmTransaction" :disabled="loading">
              <font-awesome-icon
                :icon="loading ? ['fas', 'spinner'] : ['fas', 'check']"
                :class="{ 'fa-spin': loading }"
                class="me-2"
              />
              {{ loading ? $t('exchange.processing') : $t('common.confirm') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import MultiCurrencyDenominationSelector from '@/components/MultiCurrencyDenominationSelector.vue'
import DenominationCombinationManager from '@/components/DenominationCombinationManager.vue'

export default {
  name: 'DualDirectionExchangeView',
  components: {
    MultiCurrencyDenominationSelector,
    DenominationCombinationManager
  },
  data() {
    return {
      // 基础数据
      baseCurrency: 'THB', // A005网点默认泰铢
      availableCurrencies: [],
      denominationCombinations: [],
      countries: [], // 国家列表

      // 客户信息
      customerInfo: {
        name: '',
        id_number: '',
        country_code: '',
        address: '',
        remarks: '',
        payment_method: 'cash', // 默认现金支付
        payment_method_note: '' // 其他付款方式备注
      },

      // 状态管理
      loading: false,
      validationResult: null,
      transactionSummary: null,
      validationError: null,
      currencyBalances: {}, // 存储各币种余额信息
      baseCurrencyBalance: 0, // 存储本币余额
      thresholdWarnings: [] // 存储阈值警告信息
    }
  },
  computed: {
    canExecuteTransaction() {
      return (
        this.denominationCombinations.length > 0 &&
        this.customerInfo.name.trim() !== '' &&
        this.validationResult?.success
      )
    },

    involvedCurrencies() {
      if (!this.denominationCombinations.length) return []

      console.log('[involvedCurrencies] 开始计算涉及的币种余额')
      console.log('[involvedCurrencies] denominationCombinations:', this.denominationCombinations)
      console.log('[involvedCurrencies] baseCurrencyBalance:', this.baseCurrencyBalance)
      console.log('[involvedCurrencies] currencyBalances:', this.currencyBalances)

      const currencyMap = {}
      const baseCurrencyInfo = {
        currency_code: this.baseCurrency,
        currency_name: this.getBaseCurrencyName(),
        custom_flag_filename: this.getBaseCurrencyFlag(),
        required: 0,
        balance: 0
      }

      // 统计每个币种的支出需求量（显示需要支出的币种余额）
      this.denominationCombinations.forEach(combination => {
        const currencyId = combination.currency_id
        const currencyCode = combination.currency_code
        const amount = Math.abs(combination.subtotal || 0)
        const rate = combination.rate

        console.log(`[involvedCurrencies] 处理组合: ${currencyCode} ${combination.direction} ${amount}, 汇率: ${rate}`)

        if (combination.direction === 'buy') {
          // 客户买入外币：网点需要支出本币给客户，检查本币余额
          console.log(`[involvedCurrencies] 买入 ${currencyCode}: 金额=${amount}, 汇率=${rate}`)
          const localAmount = amount * rate
          console.log(`[involvedCurrencies] 买入 ${currencyCode}: 需要本币 ${localAmount}`)

          if (!isNaN(localAmount) && localAmount > 0) {
            baseCurrencyInfo.required += localAmount
            baseCurrencyInfo.expense_type = 'base_currency' // 支出本币
          } else {
            console.warn(`[involvedCurrencies] 计算本币金额失败: amount=${amount}, rate=${rate}, localAmount=${localAmount}`)
          }
        } else if (combination.direction === 'sell') {
          // 客户卖出外币：网点需要支出外币给客户，检查外币库存
          console.log(`[involvedCurrencies] 卖出 ${currencyCode}: 需要外币 ${amount}`)
          if (!currencyMap[currencyId]) {
            currencyMap[currencyId] = {
              currency_id: currencyId,
              currency_code: currencyCode,
              currency_name: combination.currency_name || currencyCode,
              custom_flag_filename: combination.custom_flag_filename,
              required: 0,
              balance: this.currencyBalances[currencyId]?.balance || 0,
              direction: combination.direction,
              expense_type: 'foreign_currency' // 支出外币
            }
          }
          currencyMap[currencyId].required += amount
        }
      })

      const result = Object.values(currencyMap).filter(currency => currency.required > 0)

      // 如果需要检查本币余额，添加到结果中
      if (baseCurrencyInfo.required > 0) {
        baseCurrencyInfo.balance = this.baseCurrencyBalance
        result.unshift(baseCurrencyInfo) // 本币放在最前面
        console.log(`[involvedCurrencies] 添加本币余额: ${this.baseCurrency} 需要 ${baseCurrencyInfo.required} 余额 ${baseCurrencyInfo.balance}`)
      }

      console.log('[involvedCurrencies] 最终结果:', result)
      return result
    },

    hasCriticalWarnings() {
      return this.thresholdWarnings.some(warning => warning.warning_level === 'critical')
    }
  },
  async mounted() {
    await this.loadAvailableCurrencies()
    await this.loadUserBaseCurrency()
    await this.loadCountries()
  },
  methods: {
    async loadCountries() {
      try {
        console.log('[DualDirectionExchangeView] 开始加载国家列表...')
        const language = this.$i18n.locale || 'zh' // 获取当前语言
        const response = await this.$api.get(`/system/countries?language=${language}&active_only=true`)
        console.log('[DualDirectionExchangeView] 国家API响应:', response.data)
        if (response.data.success) {
          this.countries = response.data.countries || []
          console.log('[DualDirectionExchangeView] 加载到的国家数量:', this.countries.length)
        }
      } catch (error) {
        console.error('[DualDirectionExchangeView] 获取国家列表失败:', error)
        // 失败时不显示错误提示，使用空列表
        this.countries = []
      }
    },

    async loadAvailableCurrencies() {
      try {
        console.log('[DualDirectionExchangeView] 开始加载币种列表...')
        const response = await this.$api.get('/rates/available_currencies?published_only=false')
        console.log('[DualDirectionExchangeView] API响应:', response.data)
        if (response.data.success) {
          this.availableCurrencies = response.data.currencies || []
          console.log('[DualDirectionExchangeView] 加载到的币种数量:', this.availableCurrencies.length)
          console.log('[DualDirectionExchangeView] 币种列表:', this.availableCurrencies)
        }
      } catch (error) {
        console.error('[DualDirectionExchangeView] 获取币种列表失败:', error)
        this.$toast?.error?.(this.$t('exchange.load_currencies_failed'))
      }
    },

    async loadUserBaseCurrency() {
      try {
        console.log('[loadUserBaseCurrency] 开始加载用户基础币种')

        // 从localStorage获取用户信息中的本币信息
        const userInfo = localStorage.getItem('user')
        console.log('[loadUserBaseCurrency] 本地存储的用户信息:', userInfo)

        if (userInfo) {
          const user = JSON.parse(userInfo)
          console.log('[loadUserBaseCurrency] 解析的用户信息:', user)

          // 从用户信息中获取本币信息
          if (user.branch_currency && user.branch_currency.code) {
            this.baseCurrency = user.branch_currency.code
            console.log(`[loadUserBaseCurrency] 从用户信息获取本币代码: ${this.baseCurrency}`)
            console.log(`[loadUserBaseCurrency] 本币详细信息:`, user.branch_currency)
            return
          }
        }

        // 如果用户信息中没有，尝试从branch_info获取（备用方案）
        const branchInfo = localStorage.getItem('branch_info')
        console.log('[loadUserBaseCurrency] 尝试从branch_info获取:', branchInfo)

        if (branchInfo) {
          const branch = JSON.parse(branchInfo)
          console.log('[loadUserBaseCurrency] 解析的网点信息:', branch)

          if (branch.base_currency_code) {
            this.baseCurrency = branch.base_currency_code
            console.log(`[loadUserBaseCurrency] 从网点信息获取本币代码: ${this.baseCurrency}`)
            return
          }
        }

        // 如果都没有，使用默认值
        console.warn('[loadUserBaseCurrency] 本地存储中无本币信息，使用默认值')
        this.baseCurrency = 'THB'
        console.log(`[loadUserBaseCurrency] 使用默认本币代码: ${this.baseCurrency}`)
      } catch (error) {
        console.error('[loadUserBaseCurrency] 获取用户基础币种失败:', error)
        // 使用默认值
        this.baseCurrency = 'THB'
        console.log(`[loadUserBaseCurrency] 异常情况使用默认本币代码: ${this.baseCurrency}`)
      }
    },

    onAddCombination(combinationData) {
      if (this.$refs.combinationManager) {
        this.$refs.combinationManager.addCombination(combinationData)
      }
    },

    async onCombinationsChange(changeData) {
      this.denominationCombinations = changeData.combinations || []
      this.transactionSummary = {
        combinations: this.denominationCombinations,
        totals: changeData.totals,
        total_combinations: changeData.total_combinations,
        total_currencies: changeData.total_currencies
      }

      // 加载相关币种的余额信息
      await this.loadCurrencyBalances()

      // 清除之前的验证结果和错误信息
      this.validationResult = null
      this.validationError = null
    },

    clearAllCombinations(skipConfirmation = false) {
      if (skipConfirmation || confirm(this.$t('exchange.confirm_clear_all_combinations'))) {
        if (this.$refs.combinationManager) {
          this.$refs.combinationManager.clearAllCombinations()
        }
        this.validationResult = null
        this.validationError = null
        this.thresholdWarnings = []
      }
    },

    async validateTransaction() {
      if (this.denominationCombinations.length === 0) {
        this.$toast?.warning?.(this.$t('exchange.no_combinations_to_validate'))
        return
      }

      this.loading = true
      this.validationError = null

      try {
        // 构建验证数据
        const validationData = {
          denomination_data: {
            combinations: this.denominationCombinations
          },
          customer_info: this.customerInfo
        }

        console.log('[DualDirectionExchangeView] 发送验证数据:', validationData)

        // 调用后端验证API
        const response = await this.$api.post('/exchange/validate-dual-direction', validationData)

        if (response.data.success) {
          this.validationResult = {
            success: true,
            message: response.data.message || this.$t('exchange.validation_passed')
          }

          // 处理阈值警告
          if (response.data.threshold_warnings && response.data.threshold_warnings.length > 0) {
            this.thresholdWarnings = response.data.threshold_warnings
            // 如果有严重警告，使用警告类型的toast
            if (this.hasCriticalWarnings) {
              this.$toast?.warning?.(this.validationResult.message)
            } else {
              this.$toast?.info?.(this.validationResult.message)
            }
          } else {
            this.thresholdWarnings = []
            this.$toast?.success?.(this.validationResult.message)
          }
        } else {
          this.validationResult = {
            success: false,
            message: response.data.message || this.$t('exchange.validation_failed')
          }
          this.validationError = response.data.message
          this.thresholdWarnings = [] // 清除阈值警告
          this.$toast?.error?.(this.validationResult.message)
        }
      } catch (error) {
        console.error('交易验证失败:', error)
        const errorMessage = error.response?.data?.message || error.message || this.$t('exchange.validation_failed')
        this.validationResult = {
          success: false,
          message: errorMessage
        }
        this.validationError = errorMessage
        this.thresholdWarnings = [] // 清除阈值警告
        this.$toast?.error?.(errorMessage)
      } finally {
        this.loading = false
      }
    },

    executeTransaction() {
      if (!this.canExecuteTransaction) return

      // 显示确认模态框
      const modal = new window.bootstrap.Modal(document.getElementById('confirmModal'))
      modal.show()
    },

    async confirmTransaction() {
      this.loading = true
      try {
        const transactionData = {
          denomination_data: {
            combinations: this.denominationCombinations
          },
          customer_info: this.customerInfo
        }

        console.log('[DualDirectionExchangeView] 发送交易数据:', {
          transactionData,
          denominationCombinations: this.denominationCombinations,
          denominationData: transactionData.denomination_data
        })

        const response = await this.$api.post('/exchange/perform-dual-direction', transactionData)

        if (response.data.success) {
          const businessGroupId = response.data.data?.business_group_id
          console.log('双向交易执行成功，业务组ID:', businessGroupId)

          // 自动生成并打印收据（在关闭模态框之前执行，避免被中断）
          if (businessGroupId) {
            try {
              console.log('🎯 [收据生成] 开始调用打印API...')
              console.log('🎯 [收据生成] businessGroupId:', businessGroupId)
              console.log('🎯 [收据生成] API URL:', `/exchange/business-group/${businessGroupId}/print-receipt`)

              const printResponse = await this.$api.post(`/exchange/business-group/${businessGroupId}/print-receipt`, {})

              console.log('🎯 [收据生成] API响应状态:', printResponse.status)
              console.log('🎯 [收据生成] API响应数据:', printResponse.data)

              if (printResponse.data.success) {
                console.log('✅ [收据生成] 收据生成成功')
                this.$toast?.success?.(this.$t('exchange.transaction_and_receipt_success'))

                // 如果返回了PDF内容，自动打开打印对话框
                if (printResponse.data.pdf_base64) {
                  console.log('📄 [收据生成] PDF base64长度:', printResponse.data.pdf_base64.length)

                  try {
                    // 将base64转换为blob
                    const byteCharacters = atob(printResponse.data.pdf_base64)
                    const byteNumbers = new Array(byteCharacters.length)
                    for (let i = 0; i < byteCharacters.length; i++) {
                      byteNumbers[i] = byteCharacters.charCodeAt(i)
                    }
                    const byteArray = new Uint8Array(byteNumbers)
                    const blob = new Blob([byteArray], { type: 'application/pdf' })

                    // 创建临时URL
                    const url = window.URL.createObjectURL(blob)

                    // 在新窗口中打开PDF（会触发浏览器的PDF查看器）
                    const printWindow = window.open(url, '_blank')

                    // 等待PDF加载后自动打印
                    if (printWindow) {
                      printWindow.onload = function() {
                        printWindow.print()
                      }
                      console.log('🖨️ [收据生成] 已打开打印窗口')
                    } else {
                      console.warn('⚠️ [收据生成] 无法打开新窗口，可能被浏览器拦截')
                      this.$toast?.warning?.('请允许弹出窗口以打印收据')
                    }

                    // 5秒后释放URL（给足够时间打印）
                    setTimeout(() => {
                      window.URL.revokeObjectURL(url)
                    }, 5000)
                  } catch (printError) {
                    console.error('❌ [收据生成] 打印PDF失败:', printError)
                  }
                }
              } else {
                console.warn('⚠️ [收据生成] 收据生成失败:', printResponse.data.message)
                this.$toast?.warning?.(this.$t('exchange.transaction_success_but_receipt_failed'))
              }
            } catch (printError) {
              console.error('❌ [收据生成] 调用打印API异常:', printError)
              console.error('❌ [收据生成] 错误详情:', {
                message: printError.message,
                response: printError.response?.data,
                status: printError.response?.status
              })
              this.$toast?.warning?.(this.$t('exchange.transaction_success_but_receipt_failed'))
            }
          } else {
            console.error('❌ [收据生成] businessGroupId为空，无法打印收据')
          }

          // 关闭模态框
          const modal = window.bootstrap.Modal.getInstance(document.getElementById('confirmModal'))
          if (modal) modal.hide()

          // 清空表单（跳过确认提示）
          this.clearAllCombinations(true)
          this.customerInfo = {
            name: '',
            id_number: '',
            country_code: '',
            address: '',
            remarks: ''
          }
          this.validationResult = null
        } else {
          throw new Error(response.data.message || this.$t('exchange.transaction_failed'))
        }
      } catch (error) {
        console.error('交易执行失败:', error)
        this.$toast?.error?.(error.message || this.$t('exchange.transaction_failed'))
      } finally {
        this.loading = false
      }
    },

    goToSingleTransaction() {
      this.$router.push({ name: 'exchange-with-denominations' })
    },

    async loadCurrencyBalances() {
      // 清除之前的余额记录，避免累积
      this.currencyBalances = {}
      this.baseCurrencyBalance = 0

      // 分析需要检查余额的币种
      const needBaseCurrency = this.denominationCombinations.some(c => c.direction === 'buy')
      const needForeignCurrencies = this.denominationCombinations.filter(c => c.direction === 'sell').map(c => c.currency_id)

      console.log('[loadCurrencyBalances] 需要本币余额:', needBaseCurrency)
      console.log('[loadCurrencyBalances] 需要外币余额:', needForeignCurrencies)

      // 加载需要的外币余额（卖出方向的币种）
      for (const currencyId of needForeignCurrencies) {
        try {
          const response = await this.$api.get(`/dashboard/currency-balance/${currencyId}`)
          if (response.data.success) {
            this.currencyBalances[currencyId] = {
              balance: response.data.balance || 0
            }
          }
        } catch (error) {
          console.error(`获取币种${currencyId}余额失败:`, error)
          this.currencyBalances[currencyId] = {
            balance: 0
          }
        }
      }

      // 加载本币余额（买入方向时需要）
      if (needBaseCurrency) {
        console.log('[loadCurrencyBalances] 开始加载本币余额...')
        await this.loadBaseCurrencyBalance()
        console.log('[loadCurrencyBalances] 本币余额加载完成，余额:', this.baseCurrencyBalance)
      }
    },

    async loadBaseCurrencyBalance() {
      try {
        console.log(`[loadBaseCurrencyBalance] 开始加载本币余额，本币代码: ${this.baseCurrency}`)

        // 从localStorage获取用户信息中的本币ID
        const userInfo = localStorage.getItem('user')
        if (userInfo) {
          const user = JSON.parse(userInfo)
          console.log('[loadBaseCurrencyBalance] 用户信息:', user)

          if (user.branch_currency && user.branch_currency.id) {
            const baseCurrencyId = user.branch_currency.id
            console.log(`[loadBaseCurrencyBalance] 从用户信息获取本币ID: ${baseCurrencyId}`)

            try {
              const balanceResponse = await this.$api.get(`/dashboard/currency-balance/${baseCurrencyId}`)
              console.log('[loadBaseCurrencyBalance] 本币余额响应:', balanceResponse.data)

              if (balanceResponse.data.success) {
                this.baseCurrencyBalance = balanceResponse.data.balance || 0
                console.log(`[loadBaseCurrencyBalance] 本币余额设置为: ${this.baseCurrencyBalance} (类型: ${typeof this.baseCurrencyBalance})`)
                return
              } else {
                console.warn('[loadBaseCurrencyBalance] 获取本币余额失败:', balanceResponse.data.message)
                this.baseCurrencyBalance = 0
              }
            } catch (apiError) {
              console.error('[loadBaseCurrencyBalance] API调用失败:', apiError)
              this.baseCurrencyBalance = 0
            }
          }
        }

        // 备用方案：通过本币代码查找ID
        console.log('[loadBaseCurrencyBalance] 备用方案：通过币种代码查找ID')
        const response = await this.$api.get('/dashboard/currencies')
        console.log('[loadBaseCurrencyBalance] 获取币种列表响应:', response.data)

        if (response.data.success) {
          const baseCurrencyObj = response.data.currencies.find(c => c.currency_code === this.baseCurrency)
          console.log(`[loadBaseCurrencyBalance] 查找本币对象 (${this.baseCurrency}):`, baseCurrencyObj)

          if (baseCurrencyObj) {
            console.log(`[loadBaseCurrencyBalance] 准备获取本币余额，币种ID: ${baseCurrencyObj.id}`)
            const balanceResponse = await this.$api.get(`/dashboard/currency-balance/${baseCurrencyObj.id}`)
            console.log('[loadBaseCurrencyBalance] 本币余额响应:', balanceResponse.data)

            if (balanceResponse.data.success) {
              this.baseCurrencyBalance = balanceResponse.data.balance || 0
              console.log(`[loadBaseCurrencyBalance] 本币余额设置为: ${this.baseCurrencyBalance}`)
            } else {
              console.warn('[loadBaseCurrencyBalance] 获取本币余额失败:', balanceResponse.data.message)
              this.baseCurrencyBalance = 0
            }
          } else {
            console.error(`[loadBaseCurrencyBalance] 未找到本币对象，本币代码: ${this.baseCurrency}`)
            this.baseCurrencyBalance = 0
          }
        } else {
          console.error('[loadBaseCurrencyBalance] 获取币种列表失败:', response.data.message)
          this.baseCurrencyBalance = 0
        }
      } catch (error) {
        console.error(`[loadBaseCurrencyBalance] 获取本币余额失败:`, error)
        this.baseCurrencyBalance = 0
      }
    },

    getBaseCurrencyName() {
      // 多语言的本币名称映射
      const currencyNames = {
        'THB': {
          'zh-CN': '泰铢',
          'en-US': 'Thai Baht',
          'th-TH': 'บาท'
        },
        'CNY': {
          'zh-CN': '人民币',
          'en-US': 'Chinese Yuan',
          'th-TH': 'หยวนจีน'
        },
        'USD': {
          'zh-CN': '美元',
          'en-US': 'US Dollar',
          'th-TH': 'ดอลลาร์สหรัฐ'
        },
        'EUR': {
          'zh-CN': '欧元',
          'en-US': 'Euro',
          'th-TH': 'ยูโร'
        },
        'JPY': {
          'zh-CN': '日元',
          'en-US': 'Japanese Yen',
          'th-TH': 'เยนญี่ปุ่น'
        }
      }
      const currentLocale = this.$i18n.locale
      return currencyNames[this.baseCurrency]?.[currentLocale] || this.baseCurrency
    },

    getBaseCurrencyFlag() {
      // 简化的本币国旗文件名映射
      const flagMapping = {
        'THB': 'th.png',
        'CNY': 'cn.png',
        'USD': 'us.png',
        'EUR': 'eu.png',
        'JPY': 'jp.png'
      }
      return flagMapping[this.baseCurrency] || null
    },

    getCurrencyFlag(currencyCode) {
      // 通用的币种国旗映射
      const flagMapping = {
        'THB': '/flags/th.png',
        'CNY': '/flags/cn.png',
        'USD': '/flags/us.png',
        'EUR': '/flags/eu.png',
        'JPY': '/flags/jp.png',
        'GBP': '/flags/gb.png',
        'AUD': '/flags/au.png',
        'CAD': '/flags/ca.png',
        'SGD': '/flags/sg.png',
        'HKD': '/flags/hk.png',
        'KRW': '/flags/kr.png',
        'MYR': '/flags/my.png'
      }
      return flagMapping[currencyCode] || null
    },

    formatAmount(amount) {
      if (!amount && amount !== 0) return '0.00'
      return new Intl.NumberFormat('zh-CN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(Math.abs(amount))
    }
  }
}
</script>

<style scoped>
.page-title-bold {
  font-weight: 700;
  color: #1976d2;
}

.card {
  border: 1px solid #e9ecef;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 1rem;
}

.card-header {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-bottom: 1px solid #e9ecef;
  font-weight: 600;
}

.btn-primary {
  background: linear-gradient(135deg, #42a5f5 0%, #1976d2 100%);
  border: none;
  font-weight: 600;
}

.btn-primary:hover {
  background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(25, 118, 210, 0.3);
}

.btn-outline-primary:hover {
  background: linear-gradient(135deg, #42a5f5 0%, #1976d2 100%);
  border-color: #1976d2;
}

.text-primary {
  color: #1976d2 !important;
}

.text-success {
  color: #388e3c !important;
}

.text-warning {
  color: #f57c00 !important;
}

.fa-3x {
  font-size: 3rem;
}

.table-info {
  background-color: #e3f2fd !important;
}

.modal-content {
  border: none;
  border-radius: 0.5rem;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.modal-header {
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
  border-bottom: 1px solid #e3f2fd;
}

.modal-title {
  color: #1976d2;
  font-weight: 600;
}

/* 新增的指导卡片样式 */
.guidance-card .card-body {
  padding: 1rem;
}

.operation-steps .step {
  display: flex;
  align-items: center;
  margin-bottom: 0.75rem;
  font-size: 0.875rem;
}

.operation-steps .step:last-child {
  margin-bottom: 0;
}

.step-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  background: linear-gradient(135deg, #42a5f5 0%, #1976d2 100%);
  color: white;
  border-radius: 50%;
  font-size: 0.75rem;
  font-weight: 600;
  margin-right: 0.75rem;
  flex-shrink: 0;
}

.step-text {
  color: #495057;
  line-height: 1.4;
}

/* 余额信息卡片样式 */
.balance-info-card .card-body {
  padding: 1rem;
}

.balance-item {
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 0.375rem;
  border-left: 4px solid #1976d2;
}

.balance-item:last-child {
  margin-bottom: 0 !important;
}

.currency-flag {
  width: 20px;
  height: 15px;
  object-fit: cover;
  border-radius: 2px;
}

.currency-code {
  font-weight: 600;
  color: #1976d2;
  font-size: 0.9rem;
}

.current-balance {
  font-weight: 700;
  font-size: 1rem;
  color: #28a745;
}

.current-balance.text-danger {
  color: #dc3545 !important;
}

.balance-label {
  font-size: 0.75rem;
  color: #6c757d;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.required-amount {
  color: #6c757d;
}

/* 错误提示卡片样式 */
.error-card {
  border: 1px solid #dc3545;
}

.error-card .card-header {
  background: #dc3545 !important;
  border-bottom: 1px solid #dc3545;
}

.error-card .alert {
  font-size: 0.875rem;
  line-height: 1.4;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .operation-steps .step {
    font-size: 0.8rem;
  }

  .step-number {
    width: 18px;
    height: 18px;
    font-size: 0.7rem;
  }

  .balance-item {
    padding: 0.5rem;
  }

  .current-balance {
    font-size: 0.9rem;
  }
}
</style>
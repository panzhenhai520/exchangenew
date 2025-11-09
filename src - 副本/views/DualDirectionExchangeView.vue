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
        </div>

        <!-- 主界面区域 -->
        <div class="row">
          <!-- 左侧：币种和面值选择器 + 历史预约列表 -->
          <div class="col-md-4">
            <!-- 历史预约列表卡片 -->
            <div class="card mb-3 reservation-list-card">
              <div class="card-header">
                <div class="d-flex justify-content-between align-items-center">
                  <h6 class="mb-0">
                    <font-awesome-icon :icon="['fas', 'history']" class="me-2" />
                    {{ $t('exchange.reservation_history') || '历史预约' }}
                  </h6>
                  <button class="btn btn-sm btn-outline-primary" @click="loadReservations">
                    <font-awesome-icon :icon="['fas', 'sync']" :spin="loadingReservations" />
                  </button>
                </div>
              </div>
              <div class="card-body p-2">
                <!-- 快速搜索 -->
                <div class="mb-2">
                  <input
                    type="text"
                    class="form-control form-control-sm"
                    v-model="reservationSearch"
                    :placeholder="$t('exchange.search_customer_id') || '搜索客户证件号'"
                    @input="onSearchReservation"
                  />
                </div>

                <!-- 预约列表 -->
                <div class="reservation-list" style="max-height: 300px; overflow-y: auto;">
                  <div v-if="loadingReservations" class="text-center py-3">
                    <div class="spinner-border spinner-border-sm" role="status">
                      <span class="visually-hidden">Loading...</span>
                    </div>
                  </div>

                  <div v-else-if="filteredReservations.length === 0" class="text-center text-muted py-3">
                    <small>{{ $t('exchange.no_reservations') || '暂无预约记录' }}</small>
                  </div>

                  <div
                    v-else
                    v-for="reservation in filteredReservations"
                    :key="reservation.id"
                    class="reservation-item p-2 mb-1 border rounded"
                    :class="{ 'bg-light': selectedReservation?.id === reservation.id }"
                    @click="selectReservation(reservation)"
                    style="cursor: pointer;"
                  >
                    <div class="d-flex justify-content-between align-items-start">
                      <div class="flex-grow-1">
                        <div class="fw-bold small">{{ reservation.customer_name }}</div>
                        <div class="text-muted" style="font-size: 0.75rem;">{{ reservation.customer_id }}</div>
                      </div>
                      <span class="badge" :class="{
                        'bg-warning': reservation.status === 'pending',
                        'bg-success': reservation.status === 'approved',
                        'bg-danger': reservation.status === 'rejected'
                      }">
                        {{ getReservationStatusText(reservation.status) }}
                      </span>
                    </div>
                    <div class="d-flex justify-content-between align-items-center mt-1">
                      <small class="text-muted">{{ formatAmount(reservation.local_amount) }} THB</small>
                      <small class="text-muted">{{ reservation.report_type }}</small>
                    </div>
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
                  <div class="col-md-4">
                    <label class="form-label">{{ $t('exchange.customer_name') }} *</label>
                    <input
                      type="text"
                      v-model="customerInfo.name"
                      class="form-control"
                      :placeholder="$t('exchange.enter_customer_name')"
                      required
                    />
                  </div>
                  <div class="col-md-4">
                    <label class="form-label">{{ $t('exchange.id_type') }}</label>
                    <select v-model="customerInfo.id_type" class="form-select">
                      <option value="national_id">{{ $t('exchange.national_id') }}</option>
                      <option value="passport">{{ $t('exchange.passport') }}</option>
                      <option value="tax_id">{{ $t('exchange.tax_id') }}</option>
                    </select>
                  </div>
                  <div class="col-md-4">
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
                          id="paymentInstrumentCheque"
                          value="instrument_cheque"
                          v-model="customerInfo.payment_method"
                        >
                        <label class="form-check-label" for="paymentInstrumentCheque">
                          {{ $t('exchange.payment_instrument_cheque') }}
                        </label>
                      </div>
                      <div class="form-check">
                        <input
                          class="form-check-input"
                          type="radio"
                          name="paymentMethod"
                          id="paymentInstrumentDraft"
                          value="instrument_draft"
                          v-model="customerInfo.payment_method"
                        >
                        <label class="form-check-label" for="paymentInstrumentDraft">
                          {{ $t('exchange.payment_instrument_draft') }}
                        </label>
                      </div>
                      <div class="form-check">
                        <input
                          class="form-check-input"
                          type="radio"
                          name="paymentMethod"
                          id="paymentInstrumentOther"
                          value="instrument_other"
                          v-model="customerInfo.payment_method"
                        >
                        <label class="form-check-label" for="paymentInstrumentOther">
                          {{ $t('exchange.payment_instrument_other') }}
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
                          {{ $t('exchange.payment_other_method') }}
                        </label>
                      </div>
                    </div>
                    <div class="form-check mt-2" v-if="isInstrumentPayment(customerInfo.payment_method)">
                      <input
                        class="form-check-input"
                        type="checkbox"
                        id="paymentInstrumentForeignAccount"
                        v-model="customerInfo.payment_is_foreign_account"
                      >
                      <label class="form-check-label" for="paymentInstrumentForeignAccount">
                        {{ $t('exchange.payment_is_foreign_account') }}
                      </label>
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

            <!-- 交易类型选择 (大额交易时显示) -->
            <div v-if="shouldShowExchangeType" class="card mt-3">
              <div class="card-header bg-info text-white">
                <h6 class="mb-0">
                  <font-awesome-icon :icon="['fas', 'file-invoice-dollar']" class="me-2" />
                  {{ $t('exchange.exchange_type_selection') }}
                </h6>
              </div>
              <div class="card-body">
                <div class="alert alert-info mb-3">
                  <font-awesome-icon :icon="['fas', 'info-circle']" class="me-2" />
                  {{ $t('exchange.exchange_type_notice', { amount: formatAmount(totalTransactionAmountThb) }) }}
                </div>

                <div class="mb-3">
                  <div class="form-check mb-2">
                    <input
                      class="form-check-input"
                      type="radio"
                      id="exchange_type_normal"
                      value="normal"
                      v-model="exchangeType"
                    />
                    <label class="form-check-label" for="exchange_type_normal">
                      <strong>{{ $t('exchange.exchange_type_normal') }}</strong> - {{ $t('exchange.exchange_type_normal_desc') }}
                    </label>
                  </div>
                  <div class="form-check">
                    <input
                      class="form-check-input"
                      type="radio"
                      id="exchange_type_asset"
                      value="asset_backed"
                      v-model="exchangeType"
                    />
                    <label class="form-check-label" for="exchange_type_asset">
                      <strong>{{ $t('exchange.exchange_type_asset_mortgage') }}</strong> - {{ $t('exchange.exchange_type_asset_mortgage_desc') }}
                    </label>
                  </div>
                </div>

                <!-- 资金来源选择 (仅当选择资产抵押交易时显示) -->
                <div v-if="exchangeType === 'asset_backed'" class="mt-3">
                  <label class="form-label">
                    <font-awesome-icon :icon="['fas', 'wallet']" class="me-2" />
                    {{ $t('exchange.funding_source') }} <span class="text-danger">*</span>
                  </label>
                  <select class="form-select" v-model="selectedFundingSource" required>
                    <option value="">{{ $t('exchange.select_funding_source') }}</option>
                    <option
                      v-for="source in fundingSourceOptions"
                      :key="source.id"
                      :value="source.source_code"
                    >
                      {{ getFundingSourceLabel(source) }}
                    </option>
                  </select>
                  <small class="text-muted">
                    <font-awesome-icon :icon="['fas', 'exclamation-triangle']" class="me-1" />
                    {{ $t('exchange.exchange_type_hint') }}
                  </small>
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

    <!-- AMLO预约模态框 -->
    <ReservationModal
      v-if="showReservationModal"
      ref="reservationModal"
      :visible="showReservationModal"
      :report-type="triggerCheckResult?.triggers?.amlo?.report_type || 'AMLO-1-01'"
      :trigger-message="triggerCheckResult?.triggers?.amlo?.message_cn || '交易金额达到AMLO报告触发条件'"
      :transaction-data="reservationTransactionData"
      :allow-continue="triggerCheckResult?.triggers?.amlo?.allow_continue || false"
      @update:visible="handleReservationModalClosed"
      @submit="handleReservationCreated"
      @cancel="handleReservationModalClosed"
    />
  </div>
</template>

<script>
import MultiCurrencyDenominationSelector from '@/components/MultiCurrencyDenominationSelector.vue'
import DenominationCombinationManager from '@/components/DenominationCombinationManager.vue'
import ReservationModal from '@/components/exchange/ReservationModal.vue'

export default {
  name: 'DualDirectionExchangeView',
  components: {
    MultiCurrencyDenominationSelector,
    DenominationCombinationManager,
    ReservationModal
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
        id_type: 'national_id', // ID类型：national_id, passport, tax_id
        country_code: '',
        address: '',
        remarks: '',
        payment_method: 'cash', // 默认现金支付
        payment_is_foreign_account: false, // 是否使用外币账户
        use_fcd: false, // 与是否外币账户保持同步
        payment_method_note: '' // 其他付款方式备注
      },

      // 状态管理
      loading: false,
      validationResult: null,
      transactionSummary: null,
      validationError: null,
      currencyBalances: {}, // 存储各币种余额信息
      baseCurrencyBalance: 0, // 存储本币余额
      thresholdWarnings: [], // 存储阈值警告信息

      // AMLO预约相关
      showReservationModal: false,
      reservationTransactionData: null,
      reservationStatus: null, // 客户预约状态
      triggerCheckResult: null, // 触发检查结果

      // 交易类型和资金来源 (大额交易监管要求)
      exchangeType: 'normal', // 'normal' | 'asset_backed'
      selectedFundingSource: '', // 资金来源代码
      fundingSourceOptions: [], // 资金来源选项列表
      LARGE_AMOUNT_THRESHOLD: 2000000, // 200万本币阈值

      // 历史预约列表相关
      reservations: [], // 所有预约记录
      loadingReservations: false, // 加载状态
      reservationSearch: '', // 搜索关键词
      selectedReservation: null // 当前选中的预约
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

    // 过滤后的预约列表
    filteredReservations() {
      if (!this.reservationSearch.trim()) {
        return this.reservations.slice(0, 10) // 只显示最近10条
      }

      const searchLower = this.reservationSearch.toLowerCase()
      return this.reservations.filter(r =>
        r.customer_id?.toLowerCase().includes(searchLower) ||
        r.customer_name?.toLowerCase().includes(searchLower)
      ).slice(0, 10)
    },

    involvedCurrencies() {
      if (!this.denominationCombinations.length) return []

      console.log('[involvedCurrencies] 开始计算涉及的币种余额')
      console.log('[involvedCurrencies] denominationCombinations:', this.denominationCombinations)
      console.log('[involvedCurrencies] baseCurrency:', this.baseCurrency)
      console.log('[involvedCurrencies] baseCurrencyBalance:', this.baseCurrencyBalance)
      console.log('[involvedCurrencies] currencyBalances:', this.currencyBalances)

      // 获取本币ID
      const baseCurrencyId = this.getBaseCurrencyId()
      console.log('[involvedCurrencies] 本币ID:', baseCurrencyId)

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

        // 检查是否为本币交易
        const isBaseCurrency = currencyId === baseCurrencyId
        console.log(`[involvedCurrencies] 处理组合: ${currencyCode} (ID:${currencyId}) ${combination.direction} ${amount}, 汇率: ${rate}, 是否本币: ${isBaseCurrency}`)

        // 如果交易的就是本币自身，这是不合理的交易，跳过
        if (isBaseCurrency) {
          console.warn(`[involvedCurrencies] 警告: 检测到本币自身交易 ${currencyCode}，跳过`)
          return
        }

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
    },

    // 计算交易总金额(THB)
    totalTransactionAmountThb() {
      if (!this.denominationCombinations.length) return 0

      let total = 0
      this.denominationCombinations.forEach(combination => {
        // 使用 local_amount (本币金额)
        total += Math.abs(combination.local_amount || 0)
      })

      return total
    },

    // 是否显示交易类型选择
    shouldShowExchangeType() {
      return this.totalTransactionAmountThb >= this.LARGE_AMOUNT_THRESHOLD
    }
  },
  async mounted() {
    await this.loadAvailableCurrencies()
    await this.loadUserBaseCurrency()
    await this.loadCountries()
    await this.loadFundingSources() // 加载资金来源选项
    await this.loadReservations() // 加载历史预约列表

    // 监听语言变化，重新加载国家列表
    this.$watch('$i18n.locale', async (newLocale) => {
      console.log('[DualDirectionExchangeView] 语言变化，重新加载国家列表:', newLocale)
      await this.loadCountries()
    })

    // 监听客户ID变化，当用户填写客户ID时自动检查AMLO触发
    this.$watch('customerInfo.id_number', async (newValue, oldValue) => {
      // 只有当客户ID从无到有，或者发生实质性变化时才触发
      if (newValue && newValue.trim() && newValue !== oldValue) {
        console.log('[客户ID变化] 检测到客户ID填写:', newValue)

        // 检查是否有面值组合
        if (this.denominationCombinations.length > 0) {
          console.log('[客户ID变化] 存在面值组合，自动检查AMLO触发')
          await this.checkAMLOTriggersAfterChange()
        } else {
          console.log('[客户ID变化] 暂无面值组合，跳过AMLO检查')
        }
      }
    })

    this.$watch('customerInfo.payment_method', (newValue) => {
      if (!this.isInstrumentPayment(newValue)) {
        this.customerInfo.payment_is_foreign_account = false
        this.customerInfo.use_fcd = false
      }
      if (newValue !== 'other') {
        this.customerInfo.payment_method_note = ''
      }
    })

    this.$watch('customerInfo.payment_is_foreign_account', (newValue) => {
      this.customerInfo.use_fcd = !!newValue
    })
  },
  methods: {
    isInstrumentPayment(method) {
      return ['instrument_cheque', 'instrument_draft', 'instrument_other'].includes(method)
    },

    async loadCountries() {
      try {
        console.log('[DualDirectionExchangeView] 开始加载国家列表...')
        const language = this.$i18n.locale || 'zh' // 获取当前语言
        console.log('[DualDirectionExchangeView] 当前语言:', language)
        const response = await this.$api.get(`/system/countries?language=${language}&active_only=true`)
        console.log('[DualDirectionExchangeView] 国家API响应:', response.data)
        if (response.data.success) {
          this.countries = response.data.countries || []
          console.log('[DualDirectionExchangeView] 加载到的国家数量:', this.countries.length)
          // 打印前几个国家的名称，验证语言是否正确
          if (this.countries.length > 0) {
            console.log('[DualDirectionExchangeView] 前3个国家名称:',
              this.countries.slice(0, 3).map(c => `${c.country_code}: ${c.country_name}`))
          }
        }
      } catch (error) {
        console.error('[DualDirectionExchangeView] 获取国家列表失败:', error)
        // 失败时不显示错误提示，使用空列表
        this.countries = []
      }
    },

    async loadFundingSources() {
      try {
        console.log('[DualDirectionExchangeView] 开始加载资金来源选项...')
        const response = await this.$api.get('/compliance/funding-sources', {
          params: { is_active: true }
        })
        console.log('[DualDirectionExchangeView] 资金来源API响应:', response.data)
        if (response.data.success && Array.isArray(response.data.data)) {
          this.fundingSourceOptions = response.data.data
        } else if (Array.isArray(response.data)) {
          // 兼容旧格式
          this.fundingSourceOptions = response.data
        } else {
          this.fundingSourceOptions = []
        }
        console.log('[DualDirectionExchangeView] 加载到的资金来源数量:', this.fundingSourceOptions.length)
      } catch (error) {
        console.error('[DualDirectionExchangeView] 加载资金来源失败:', error)
        this.fundingSourceOptions = []
      }
    },

    // 获取资金来源的多语言标签
    getFundingSourceLabel(option) {
      if (!option) return ''
      const locale = this.$i18n?.locale || 'zh-CN'
      if (locale === 'en-US') return option.source_name_en || option.source_code || ''
      if (locale === 'th-TH') return option.source_name_th || option.source_code || ''
      return option.source_name_cn || option.source_code || ''
    },

    async loadAvailableCurrencies() {
      try {
        console.log('[DualDirectionExchangeView] 开始加载币种列表...')
        const response = await this.$api.get('/rates/available_currencies?published_only=true')
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

    getBaseCurrencyId() {
      /**
       * 获取本币的currency_id
       * 用于与denomination组合中的currency_id进行比较，判断是否为本币交易
       */
      try {
        // 从localStorage获取用户信息中的本币ID
        const userInfo = localStorage.getItem('user')
        if (userInfo) {
          const user = JSON.parse(userInfo)

          // 从用户的branch_currency信息中获取本币ID
          if (user.branch_currency && user.branch_currency.id) {
            console.log(`[getBaseCurrencyId] 从用户信息获取本币ID: ${user.branch_currency.id}`)
            return user.branch_currency.id
          }
        }

        // 备用方案：从availableCurrencies中查找本币ID
        if (this.availableCurrencies && this.availableCurrencies.length > 0) {
          const baseCurrencyObj = this.availableCurrencies.find(c => c.currency_code === this.baseCurrency)
          if (baseCurrencyObj && baseCurrencyObj.id) {
            console.log(`[getBaseCurrencyId] 从币种列表获取本币ID: ${baseCurrencyObj.id}`)
            return baseCurrencyObj.id
          }
        }

        console.warn('[getBaseCurrencyId] 无法获取本币ID，返回null')
        return null
      } catch (error) {
        console.error('[getBaseCurrencyId] 获取本币ID失败:', error)
        return null
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

      // ===== 新增: 自动检查AMLO触发条件 =====
      // 如果已填写客户证件号，自动检查是否触发AMLO报告
      if (this.customerInfo.id_number && this.customerInfo.id_number.trim()) {
        console.log('[组合变化] 检测到客户ID，自动检查AMLO触发')
        await this.checkAMLOTriggersAfterChange()
      }
    },

    /**
     * 组合变化后的AMLO触发检查
     * 当用户修改面值数量时，自动检查是否触发AMLO报告要求
     * 这是防止用户绕过AMLO检查的关键安全措施
     */
    async checkAMLOTriggersAfterChange() {
      try {
        // 计算交易总金额（转换为THB）
        let totalAmountThb = 0
        for (const combination of this.denominationCombinations) {
          totalAmountThb += Math.abs(combination.local_amount || 0)
        }

        // 如果金额为0，跳过检查
        if (totalAmountThb === 0) {
          console.log('[组合变化] 交易金额为0，跳过触发检查')
          return
        }

        console.log('[组合变化] 交易总金额(THB):', totalAmountThb)

        // 构建触发检查数据
        const triggerCheckData = {
          report_type: 'AMLO-1-01',
          data: {
            customer_id: this.customerInfo.id_number,
            customer_name: this.customerInfo.name || '',
            customer_country: this.customerInfo.country_code || 'TH',
            transaction_type: 'exchange',
            transaction_amount_thb: totalAmountThb,
            total_amount: totalAmountThb,
            transaction_details: this.denominationCombinations,
            payment_method: this.customerInfo.payment_method || 'cash',
            payment_is_foreign_account: this.customerInfo.payment_is_foreign_account || false,
            customer_age: this.customerInfo.age || null,
            exchange_type: this.customerInfo.exchange_type || 'normal'
          },
          branch_id: this.getBranchId()
        }

        console.log('[组合变化] 触发检查数据:', triggerCheckData)

        // 调用后端AMLO触发检查API
        const triggerResponse = await this.$api.post('/repform/check-trigger', triggerCheckData)
        console.log('[组合变化] AMLO触发检查响应:', triggerResponse.data)

        // 如果触发了AMLO报告，显示警告提示（不立即弹出模态框，避免干扰用户操作）
        if (triggerResponse.data.success && triggerResponse.data.triggers?.amlo?.triggered) {
          const amloTrigger = triggerResponse.data.triggers.amlo
          console.log('[组合变化] 触发了AMLO报告:', amloTrigger.report_type)

          // 显示警告提示
          const warningMessage = `当前交易金额 ${this.formatAmount(totalAmountThb)} THB 已触发 ${amloTrigger.report_type} 报告要求`

          this.$toast?.warning?.(warningMessage, {
            duration: 6000,
            position: 'top-right'
          })

          // 保存触发结果，供后续验证和执行时使用
          this.triggerCheckResult = triggerResponse.data

          console.log('[组合变化] 已保存AMLO触发结果，用户继续操作时将强制要求填写AMLO表单')
        } else {
          // 如果未触发，清除之前的触发结果
          this.triggerCheckResult = null
          console.log('[组合变化] 未触发AMLO报告')
        }
      } catch (error) {
        console.error('[组合变化] AMLO触发检查失败:', error)
        console.error('[组合变化] 错误详情:', error.response?.data)
        // 失败时不影响用户继续操作，但记录错误日志
        // 实际执行交易时会再次检查，确保不会遗漏
      }
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
        // ===== 步骤0: 检查是否是已审核预约 (快速兑换模式) =====
        if (this.selectedReservation && this.selectedReservation.status === 'approved') {
          console.log('[验证] 已审核预约快速兑换模式，跳过AMLO触发检查')
          console.log('[验证] 预约编号:', this.selectedReservation.reservation_no)
          console.log('[验证] 预约状态:', this.selectedReservation.status)

          // 跳过AMLO检查，直接进入余额验证
          // 注意：如果用户修改了金额，需要在执行交易前检测并生成新预约
          this.triggerCheckResult = null // 清除触发结果，表示不需要AMLO审核
        } else {
          // ===== 步骤1: 检查AMLO/BOT触发条件 =====
          console.log('[验证] 步骤1: 检查客户证件号:', this.customerInfo.id_number)
          if (this.customerInfo.id_number && this.customerInfo.id_number.trim()) {
            console.log('[验证] 步骤1: 检查AMLO/BOT触发条件...')

            // 计算交易总金额（转换为THB）
            let totalAmountThb = 0
            for (const combination of this.denominationCombinations) {
              totalAmountThb += Math.abs(combination.local_amount || 0)
            }

            console.log('[验证] 交易总金额(THB):', totalAmountThb)

            // 调用AMLO触发检查API
            try {
              const triggerCheckData = {
                report_type: 'AMLO-1-01',
                data: {
                  customer_id: this.customerInfo.id_number,
                  customer_name: this.customerInfo.name,
                  customer_country: this.customerInfo.country_code || 'TH',
                  transaction_type: 'exchange',
                  transaction_amount_thb: totalAmountThb,
                  total_amount: totalAmountThb,
                  transaction_details: this.denominationCombinations,
                  payment_method: this.customerInfo.payment_method || 'cash',
                  payment_is_foreign_account: this.customerInfo.payment_is_foreign_account || false
                },
                branch_id: this.getBranchId()
              }

              const triggerResponse = await this.$api.post('/repform/check-trigger', triggerCheckData)
              console.log('[验证] AMLO触发检查响应:', triggerResponse.data)

              // 如果触发了AMLO报告，弹出预约表单
              if (triggerResponse.data.success && triggerResponse.data.triggers?.amlo?.triggered) {
                console.log('[验证] 触发了AMLO报告，弹出预约表单')

                // 🔧 判断交易类型：根据组合中的direction判断
                console.log('[验证] 所有denomination组合:', JSON.stringify(this.denominationCombinations, null, 2))

                // 过滤掉空的或undefined的direction
                const validDirections = this.denominationCombinations
                  .map(c => c.direction)
                  .filter(d => d && d !== '')

                console.log('[验证] 有效的direction值:', validDirections)

                const uniqueDirections = [...new Set(validDirections)]
                console.log('[验证] 去重后的direction:', uniqueDirections)

                let transaction_type
                if (uniqueDirections.length === 0) {
                  // 没有有效的direction信息
                  console.warn('[验证] ⚠️ 警告：没有找到有效的direction字段！')
                  transaction_type = 'exchange'  // 默认为普通兑换
                } else if (uniqueDirections.length === 1) {
                  // 只有一个方向
                  transaction_type = uniqueDirections[0] // 直接使用direction值（'buy'或'sell'）
                  console.log('[验证] ✓ 单一方向交易:', transaction_type)
                } else {
                  // 多个方向 = 真正的双向交易
                  transaction_type = 'dual_direction'
                  console.log('[验证] ✓ 检测到双向交易')
                }

                console.log('[验证] 最终交易类型:', transaction_type)

                // 准备预约交易数据
                const rawTransactionData = {
                  customer_id: this.customerInfo.id_number,
                  customer_name: this.customerInfo.name,
                  customer_country_code: this.customerInfo.country_code || 'TH',
                  transaction_type: transaction_type,  // 使用动态判断的交易类型
                  payment_method: this.customerInfo.payment_method,
                  payment_method_note: this.customerInfo.payment_method_note,
                  payment_is_foreign_account: !!this.customerInfo.payment_is_foreign_account,
                  remarks: this.customerInfo.remarks
                }
                this.reservationTransactionData = this.convertTransactionDataForModal(rawTransactionData, totalAmountThb)

                // 显示预约模态框
                this.showReservationModal = true

                this.loading = false
                return
              }
            } catch (triggerError) {
              console.error('[验证] AMLO触发检查失败:', triggerError)
              console.error('[验证] 触发检查错误详情:', triggerError.response?.data)

              // 如果是认证错误，提示用户重新登录
              if (triggerError.response?.status === 401) {
                console.error('[验证] 认证失败，可能需要重新登录')
                this.$toast?.error?.('认证失败，请重新登录后再试')
                this.loading = false
                return
              }

              // 其他错误不阻止验证，继续检查库存
            }
          } else {
            console.log('[验证] 跳过AMLO触发检查 - 客户证件号为空')
          }
        }

        // ===== 步骤2: 检查库存充足性 =====
        console.log('[验证] 步骤2: 检查库存充足性...')
        
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
        console.log('[验证] 库存验证API响应:', response.data)

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
          // 🔧 库存验证失败 - 直接显示错误，不弹出预约表单
          // AMLO预约表单只应在触发AMLO规则时弹出，与库存无关
          console.log('[验证] 库存验证失败')

          this.validationResult = {
            success: false,
            message: response.data.message || this.$t('exchange.validation_failed')
          }
          this.validationError = response.data.message
          this.thresholdWarnings = []
          this.$toast?.error?.(this.validationResult.message)
        }
      } catch (error) {
        console.error('交易验证失败:', error)
        const errorMessage = error.response?.data?.message || error.message || this.$t('exchange.validation_failed')

        // 🔧 所有验证错误（包括库存不足）都直接显示错误信息
        // AMLO预约表单只应在触发AMLO规则时弹出，与库存无关
        this.validationResult = {
          success: false,
          message: errorMessage
        }
        this.validationError = errorMessage
        this.thresholdWarnings = []
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
        // ===== 验证资产抵押交易时必须填写资金来源 =====
        if (this.shouldShowExchangeType && this.exchangeType === 'asset_backed' && !this.selectedFundingSource) {
          this.$toast?.error?.(this.$t('exchange.funding_source_required'))
          this.loading = false
          return
        }

        // ===== AMLO/BOT触发检查 =====
        if (this.customerInfo.id_number && this.customerInfo.id_number.trim()) {
          console.log('[AMLO触发检查] 开始检查客户:', this.customerInfo.id_number)

          // 1. 先检查客户是否已有预约记录
          await this.checkCustomerReservationStatus()

          // 2. 如果有pending或rejected状态的预约，阻止交易
          if (this.reservationStatus && ['pending', 'rejected'].includes(this.reservationStatus.status)) {
            const statusText = this.reservationStatus.status === 'pending' ? '审核中' : '已拒绝'
            this.$toast?.warning?.(`客户已有${statusText}的预约记录，无法继续交易`)
            this.loading = false
            return
          }

          // 3. 计算交易总金额（转换为THB）
          let totalAmountThb = 0
          for (const combination of this.denominationCombinations) {
            // 买入方向：客户支付本币购买外币，使用local_amount
            // 卖出方向：客户卖出外币获得本币，使用local_amount
            totalAmountThb += Math.abs(combination.local_amount || 0)
          }

          console.log('[AMLO触发检查] 交易总金额(THB):', totalAmountThb)
          console.log('[AMLO触发检查] 交易类型:', this.exchangeType)
          console.log('[AMLO触发检查] 资金来源:', this.selectedFundingSource)

          // 4. 调用AMLO触发检查API - 检查所有可能的报告类型
          try {
            const reportTypes = ['AMLO-1-01'] // 默认检查CTR
            if (this.exchangeType === 'asset_backed') {
              reportTypes.push('AMLO-1-02') // 资产抵押交易还要检查ATR
            }
            if (this.selectedFundingSource) {
              reportTypes.push('AMLO-1-03') // 有资金来源时检查STR
            }

            console.log('[AMLO触发检查] 需要检查的报告类型:', reportTypes)

            const triggerResults = []
            let customerStats = {}

            for (const reportType of reportTypes) {
              const triggerCheckData = {
                report_type: reportType,
                data: {
                  customer_id: this.customerInfo.id_number,
                  customer_name: this.customerInfo.name,
                  customer_country: this.customerInfo.country_code || 'TH',
                  transaction_type: 'exchange',
                  transaction_amount_thb: totalAmountThb,
                  total_amount: totalAmountThb, // 兼容不同的字段名
                  exchange_type: this.exchangeType || 'normal', // 交易类型
                  funding_source: this.selectedFundingSource || null, // 资金来源
                  asset_value: this.exchangeType === 'asset_backed' ? totalAmountThb : null, // 资产价值
                  transaction_details: this.denominationCombinations,
                  payment_method: this.customerInfo.payment_method || 'cash',
                  payment_is_foreign_account: this.customerInfo.payment_is_foreign_account || false
                },
                branch_id: this.getBranchId()
              }

              console.log(`[AMLO触发检查] 检查报告类型 ${reportType}:`, triggerCheckData)

              const triggerResponse = await this.$api.post('/repform/check-trigger', triggerCheckData)
              console.log(`[AMLO触发检查] 报告类型 ${reportType} 响应:`, triggerResponse.data)

              if (triggerResponse.data.success) {
                if (triggerResponse.data.customer_stats) {
                  customerStats = triggerResponse.data.customer_stats
                }
                const amloTrigger = triggerResponse.data.triggers?.amlo
                if (amloTrigger && amloTrigger.triggered) {
                  triggerResults.push({
                    ...amloTrigger,
                    report_type: reportType
                  })
                }
              }
            }

            console.log('[AMLO触发检查] 所有触发结果:', triggerResults)

            // 保存完整的触发结果
            this.triggerCheckResult = {
              triggers: triggerResults,
              customer_stats: customerStats,
              bot: null
            }

            // 检查是否有阻断性触发（需要预约审核）
            const blockingTriggers = triggerResults.filter(item => item.allow_continue === false)
            const nonBlockingTriggers = triggerResults.filter(item => item.allow_continue !== false)

            // 显示非阻断性触发的提示
            nonBlockingTriggers.forEach(item => {
              const message = item.message_cn || item.message_en || item.message_th
              if (message) {
                this.$toast?.info?.(message)
              }
            })

            // 如果有阻断性触发，显示预约模态框
            if (blockingTriggers.length > 0) {
              console.log('[AMLO触发检查] 检测到阻断性触发，需要预约审核:', blockingTriggers)

              // 🔧 判断交易类型：根据组合中的direction判断
              console.log('[确认交易] 所有denomination组合:', JSON.stringify(this.denominationCombinations, null, 2))

              // 过滤掉空的或undefined的direction
              const validDirections = this.denominationCombinations
                .map(c => c.direction)
                .filter(d => d && d !== '')

              console.log('[确认交易] 有效的direction值:', validDirections)

              const uniqueDirections = [...new Set(validDirections)]
              console.log('[确认交易] 去重后的direction:', uniqueDirections)

              let transaction_type
              if (uniqueDirections.length === 0) {
                // 没有有效的direction信息
                console.warn('[确认交易] ⚠️ 警告：没有找到有效的direction字段！')
                transaction_type = 'exchange'  // 默认为普通兑换
              } else if (uniqueDirections.length === 1) {
                // 只有一个方向
                transaction_type = uniqueDirections[0] // 直接使用direction值（'buy'或'sell'）
                console.log('[确认交易] ✓ 单一方向交易:', transaction_type)
              } else {
                // 多个方向 = 真正的双向交易
                transaction_type = 'dual_direction'
                console.log('[确认交易] ✓ 检测到双向交易')
              }

              console.log('[确认交易] 最终交易类型:', transaction_type)

              // 准备预约交易数据
              const rawTransactionData = {
                customer_id: this.customerInfo.id_number,
                customer_name: this.customerInfo.name,
                customer_country_code: this.customerInfo.country_code || 'TH',
                transaction_type: transaction_type,  // 使用动态判断的交易类型
                payment_method: this.customerInfo.payment_method,
                payment_method_note: this.customerInfo.payment_method_note,
                payment_is_foreign_account: !!this.customerInfo.payment_is_foreign_account,
                remarks: this.customerInfo.remarks,
                exchange_type: this.exchangeType || 'normal', // 新增：交易类型
                funding_source: this.selectedFundingSource || null // 新增：资金来源
              }
              this.reservationTransactionData = this.convertTransactionDataForModal(rawTransactionData, totalAmountThb)

              // 显示预约模态框
              this.showReservationModal = true

              // 停止交易流程，等待用户完成预约
              this.loading = false
              return
            } else {
              console.log('[AMLO触发检查] 未检测到阻断性触发，继续交易')
            }
          } catch (triggerError) {
            console.error('[AMLO触发检查] 触发检查失败:', triggerError)
            // 触发检查失败不阻止交易，只是记录日志
          }
        }
        // ===== 触发检查结束 =====

        // 继续执行交易
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
            id_type: 'national_id',
            country_code: '',
            address: '',
            remarks: '',
            payment_method: 'cash',
            payment_is_foreign_account: false,
            use_fcd: false,
            payment_method_note: ''
          }
          this.validationResult = null

          // 清空预约相关状态
          this.selectedReservation = null
          this.reservationStatus = null
          this.reservations = []

          console.log('[交易完成] 已清空客户信息、组合和预约列表')
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
    },

    // ===== AMLO预约相关方法 =====
    
    /**
     * 检查客户预约状态
     */
    async checkCustomerReservationStatus() {
      if (!this.customerInfo.id_number) {
        this.reservationStatus = null
        return
      }

      try {
        console.log('[预约状态检查] 检查客户ID:', this.customerInfo.id_number)
        const response = await this.$api.get(`/api/amlo/check-customer-reservation?customer_id=${this.customerInfo.id_number}`)
        
        if (response.data.success && response.data.has_reservation) {
          this.reservationStatus = response.data
          console.log('[预约状态检查] 找到预约记录:', this.reservationStatus)
          
          // 显示预约状态提示
          if (response.data.status === 'pending') {
            this.$toast?.info?.('该客户有待审核的预约记录')
          } else if (response.data.status === 'rejected') {
            this.$toast?.warning?.('该客户的预约已被拒绝')
          } else if (response.data.status === 'approved') {
            this.$toast?.success?.('该客户的预约已审核通过')
          }
        } else {
          this.reservationStatus = null
          console.log('[预约状态检查] 没有找到预约记录')
        }
      } catch (error) {
        console.error('[预约状态检查] 检查失败:', error)
        this.reservationStatus = null
      }
    },

    /**
     * 处理预约创建成功
     */
    handleReservationCreated(reservation) {
      console.log('[预约创建] 预约已创建:', reservation)
      this.$toast?.success?.('AMLO预约已提交，等待审核')
      
      // 关闭确认模态框
      const confirmModal = window.bootstrap.Modal.getInstance(document.getElementById('confirmModal'))
      if (confirmModal) confirmModal.hide()
      
      // 清空表单
      this.clearAllCombinations(true)
      this.customerInfo = {
        name: '',
        id_number: '',
        id_type: 'national_id',
        country_code: '',
        address: '',
        remarks: '',
        payment_method: 'cash',
        payment_is_foreign_account: false,
        use_fcd: false,
        payment_method_note: ''
      }
      this.validationResult = null
    },

    /**
     * 转换交易数据为ReservationModal期望的格式
     *
     * 针对双向交易，需要特殊处理：
     * - 汇总所有买入外币的交易（客户支付本币，获得外币）
     * - 汇总所有卖出外币的交易（客户支付外币，获得本币）
     * - 计算净买入/净卖出金额
     */
    convertTransactionDataForModal(transactionData, totalAmountThb) {
      console.log('[convertTransactionDataForModal] 开始转换交易数据')
      console.log('[convertTransactionDataForModal] transactionData:', transactionData)
      console.log('[convertTransactionDataForModal] totalAmountThb:', totalAmountThb)
      console.log('[convertTransactionDataForModal] combinations:', this.denominationCombinations)

      // 分析所有组合，按币种和方向分类
      const currencySummary = {}
      let totalBuyLocalAmount = 0  // 买入外币时支付的本币总额
      let totalSellLocalAmount = 0  // 卖出外币时获得的本币总额

      this.denominationCombinations.forEach(combination => {
        const currencyCode = combination.currency_code
        const currencyId = combination.currency_id
        const direction = combination.direction
        const foreignAmount = Math.abs(combination.subtotal || 0)
        const localAmount = Math.abs(combination.local_amount || 0)
        const rate = combination.rate || 0

        if (!currencySummary[currencyCode]) {
          currencySummary[currencyCode] = {
            currency_id: currencyId,
            currency_code: currencyCode,
            buy_foreign_amount: 0,  // 买入的外币金额
            buy_local_amount: 0,    // 买入时支付的本币金额
            sell_foreign_amount: 0, // 卖出的外币金额
            sell_local_amount: 0,   // 卖出时获得的本币金额
            rate: rate
          }
        }

        if (direction === 'buy') {
          // 客户买入外币：支付本币，获得外币
          currencySummary[currencyCode].buy_foreign_amount += foreignAmount
          currencySummary[currencyCode].buy_local_amount += localAmount
          totalBuyLocalAmount += localAmount
        } else if (direction === 'sell') {
          // 客户卖出外币：支付外币，获得本币
          currencySummary[currencyCode].sell_foreign_amount += foreignAmount
          currencySummary[currencyCode].sell_local_amount += localAmount
          totalSellLocalAmount += localAmount
        }
      })

      console.log('[convertTransactionDataForModal] currencySummary:', currencySummary)
      console.log('[convertTransactionDataForModal] totalBuyLocalAmount:', totalBuyLocalAmount)
      console.log('[convertTransactionDataForModal] totalSellLocalAmount:', totalSellLocalAmount)

      // 确定主要币种（按交易金额最大的币种）
      let mainCurrency = null
      let maxAmount = 0
      for (const [currencyCode, summary] of Object.entries(currencySummary)) {
        const totalAmount = summary.buy_foreign_amount + summary.sell_foreign_amount
        if (totalAmount > maxAmount) {
          maxAmount = totalAmount
          mainCurrency = {
            code: currencyCode,
            id: summary.currency_id,
            rate: summary.rate
          }
        }
      }

      // 如果没有找到主要币种，使用第一个组合
      if (!mainCurrency && this.denominationCombinations.length > 0) {
        const firstCombination = this.denominationCombinations[0]
        mainCurrency = {
          code: firstCombination.currency_code,
          id: firstCombination.currency_id,
          rate: firstCombination.rate || 1
        }
      }

      console.log('[convertTransactionDataForModal] mainCurrency:', mainCurrency)

      // 判断主要交易方向（净买入或净卖出）
      const netLocalAmount = totalSellLocalAmount - totalBuyLocalAmount
      const isDominantSell = netLocalAmount > 0

      console.log('[convertTransactionDataForModal] netLocalAmount:', netLocalAmount)
      console.log('[convertTransactionDataForModal] isDominantSell:', isDominantSell)

      // 构建返回数据
      return {
        // 客户信息
        customerId: transactionData.customer_id || this.customerInfo.id_number || '',
        customerName: transactionData.customer_name || this.customerInfo.name || '',
        customerCountryCode: transactionData.customer_country_code || this.customerInfo.country_code || 'TH',
        address: transactionData.address || this.customerInfo.address || '',  // 新增：地址信息

        // 交易模式和方向 - 🔧 使用传入的transaction_type，不要硬编码！
        exchangeMode: transactionData.transaction_type || 'dual_direction',

        // 币种信息
        fromCurrency: mainCurrency?.code || 'USD',
        toCurrency: this.baseCurrency || 'THB',
        currencyId: mainCurrency?.id || null,

        // 主要币种的金额和汇率
        fromAmount: isDominantSell ?
          (currencySummary[mainCurrency?.code]?.sell_foreign_amount || 0) :
          (currencySummary[mainCurrency?.code]?.buy_foreign_amount || 0),
        toAmount: totalAmountThb,
        rate: mainCurrency?.rate || 1,

        // 总金额
        totalAmountThb: Math.abs(totalAmountThb),

        // 完整的组合数据（供AMLO表单详细分析）
        combinations: this.denominationCombinations,
        currencySummary: currencySummary,

        // 汇总金额（用于AMLO表单自动填充）
        totalBuyLocalAmount: totalBuyLocalAmount,      // 买入外币支付的本币总额
        totalSellLocalAmount: totalSellLocalAmount,    // 卖出外币获得的本币总额
        totalBuyForeignAmount: Object.values(currencySummary).reduce((sum, c) => sum + c.buy_foreign_amount, 0),
        totalSellForeignAmount: Object.values(currencySummary).reduce((sum, c) => sum + c.sell_foreign_amount, 0),

        // 交易详情
        paymentMethod: transactionData.payment_method || this.customerInfo.payment_method || 'cash',
        paymentIsForeignAccount: typeof transactionData.payment_is_foreign_account === 'boolean'
          ? transactionData.payment_is_foreign_account
          : !!this.customerInfo.payment_is_foreign_account,
        paymentMethodNote: transactionData.payment_method_note || this.customerInfo.payment_method_note || '',
        idType: transactionData.id_type || this.customerInfo.id_type || 'national_id',
        remarks: transactionData.remarks || this.customerInfo.remarks || '',

        // 标记为库存不足导致的预约（如果适用）
        inventoryInsufficient: transactionData.inventory_insufficient || false
      }
    },

    /**
     * 获取branch_id的辅助方法
     * 从localStorage中的user对象提取branch.id
     */
    getBranchId() {
      try {
        const userInfo = localStorage.getItem('user')
        if (userInfo) {
          const user = JSON.parse(userInfo)
          if (user.branch && user.branch.id) {
            return parseInt(user.branch.id)
          }
        }
        // 如果获取失败，返回默认值1
        console.warn('[getBranchId] 无法获取branch_id，使用默认值1')
        return 1
      } catch (error) {
        console.error('[getBranchId] 获取branch_id失败:', error)
        return 1
      }
    },

    /**
     * 处理预约模态框关闭
     */
    handleReservationModalClosed() {
      console.log('[预约模态框] 模态框已关闭')
      this.showReservationModal = false
    },

    // ===== 历史预约列表相关方法 =====

    /**
     * 加载历史预约列表
     */
    async loadReservations() {
      this.loadingReservations = true
      try {
        const response = await this.$api.get('/amlo/reservations', {
          params: {
            page: 1,
            page_size: 50, // 加载最近50条
            status: 'approved' // 只显示已审批的预约
          }
        })

        if (response.data.success) {
          this.reservations = response.data.data?.items || []
          console.log('[loadReservations] 成功加载预约列表:', this.reservations.length, '条')
        } else {
          console.error('[loadReservations] 加载失败:', response.data.message)
          this.reservations = []
        }
      } catch (error) {
        console.error('[loadReservations] 加载预约列表异常:', error)
        this.reservations = []
      } finally {
        this.loadingReservations = false
      }
    },

    /**
     * 搜索预约（防抖处理）
     */
    onSearchReservation() {
      // 实时过滤由computed属性处理，这里不需要额外操作
    },

    /**
     * 选择预约
     */
    async selectReservation(reservation) {
      console.log('[selectReservation] 选中预约:', reservation)
      this.selectedReservation = reservation

      // 根据预约状态执行不同操作
      if (reservation.status === 'pending') {
        // 待审核：提示用户先审核
        this.$toast?.warning?.('该预约尚未审核，请先前往AMLO审计页面进行审核')
      } else if (reservation.status === 'approved') {
        // 已审批：自动填充交易表单，完成交易
        await this.fillTransactionFromReservation(reservation)
      } else if (reservation.status === 'rejected') {
        // 已拒绝：提示用户
        this.$toast?.error?.('该预约已被拒绝，无法继续处理')
      } else if (reservation.status === 'completed') {
        // 已完成：可以查看或修改报告
        this.$toast?.info?.('该预约已完成交易，可以查看或修改AMLO报告')
        // TODO: 打开报告查看/编辑界面
      }
    },

    /**
     * 从预约填充交易表单
     */
    async fillTransactionFromReservation(reservation) {
      try {
        console.log('[fillTransactionFromReservation] 开始填充表单，预约数据:', reservation)

        // 1. 填充客户信息
        this.customerInfo = {
          name: reservation.customer_name || '',
          id_number: reservation.customer_id || '',
          id_type: 'national_id',
          country_code: reservation.customer_country_code || 'TH',
          address: reservation.customer_address || '',
          remarks: '',
          payment_method: 'cash',
          payment_is_foreign_account: false,
          use_fcd: false,
          payment_method_note: ''
        }

        // 2. 清空现有组合（REPLACE模式，不是APPEND）
        if (this.$refs.combinationManager) {
          this.$refs.combinationManager.clearAllCombinations()
        }
        this.denominationCombinations = []

        // 3. 解析denomination_data，填充面值组合
        if (reservation.denomination_data) {
          console.log('[fillTransactionFromReservation] 原始denomination_data:', reservation.denomination_data)

          try {
            // 解析JSON字符串（如果是字符串）
            const denominationData = typeof reservation.denomination_data === 'string'
              ? JSON.parse(reservation.denomination_data)
              : reservation.denomination_data

            console.log('[fillTransactionFromReservation] 解析后的denomination_data:', denominationData)

            // 如果是数组，遍历每个组合
            if (Array.isArray(denominationData) && denominationData.length > 0) {
              for (const combination of denominationData) {
                console.log('[fillTransactionFromReservation] 添加组合:', combination)

                // 使用onAddCombination方法添加组合
                this.onAddCombination(combination)
              }

              // 等待Vue更新DOM和状态
              await this.$nextTick()

              // 如果combinationManager有更新方法，等待它完成
              if (this.$refs.combinationManager) {
                await this.$nextTick()
              }

              console.log('[fillTransactionFromReservation] 所有组合已添加，当前组合数:', this.denominationCombinations.length)
            } else {
              console.warn('[fillTransactionFromReservation] denomination_data为空或不是数组')
            }
          } catch (error) {
            console.error('[fillTransactionFromReservation] 解析denomination_data失败:', error)
            this.$toast?.error?.('解析面值数据失败: ' + error.message)
          }
        } else {
          console.warn('[fillTransactionFromReservation] 预约没有denomination_data，使用简化逻辑')

          // 降级方案: 如果没有denomination_data，从基本字段构建简化组合
          const { direction, currency_id, amount, local_amount, rate } = reservation

          if (currency_id && amount) {
            this.onAddCombination({
              currency_id,
              currency_code: reservation.currency_code || 'USD',
              direction: direction || 'buy',
              subtotal: parseFloat(amount),
              local_amount: parseFloat(local_amount || 0),
              rate: parseFloat(rate || 0),
              denominations: []
            })

            // 等待状态更新
            await this.$nextTick()
          }
        }

        // 4. 等待所有状态更新完成
        await this.$nextTick()

        console.log('[fillTransactionFromReservation] 最终组合数:', this.denominationCombinations.length)

        // 5. 提示用户
        this.$toast?.success?.(`已加载预约 ${reservation.reservation_no}，请检查并完成交易`)

        // 6. 延迟自动验证，确保组合已加载
        setTimeout(async () => {
          if (this.denominationCombinations.length > 0) {
            await this.validateTransaction()
          }
        }, 300)

      } catch (error) {
        console.error('[fillTransactionFromReservation] 填充表单失败:', error)
        this.$toast?.error?.('加载预约数据失败: ' + error.message)
      }
    },

    /**
     * 获取预约状态文本
     */
    getReservationStatusText(status) {
      const statusMap = {
        'pending': this.$t('amlo.reservation.pending') || '待审核',
        'approved': this.$t('amlo.reservation.approved') || '已批准',
        'rejected': this.$t('amlo.reservation.rejected') || '已拒绝',
        'completed': this.$t('amlo.reservation.completed') || '已完成'
      }
      return statusMap[status] || status
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

/* 历史预约列表卡片样式 */
.reservation-list-card .card-body {
  padding: 0.5rem;
}

.reservation-item {
  transition: all 0.2s;
}

.reservation-item:hover {
  background-color: #f8f9fa !important;
  border-color: #1976d2 !important;
  box-shadow: 0 2px 4px rgba(25, 118, 210, 0.2);
}

.reservation-list {
  max-height: 300px;
  overflow-y: auto;
}

.reservation-list::-webkit-scrollbar {
  width: 6px;
}

.reservation-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.reservation-list::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 3px;
}

.reservation-list::-webkit-scrollbar-thumb:hover {
  background: #555;
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
  .reservation-item {
    font-size: 0.85rem;
  }

  .balance-item {
    padding: 0.5rem;
  }

  .current-balance {
    font-size: 0.9rem;
  }
}
</style>

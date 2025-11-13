<template>
  <div class="container-fluid py-4">
    <div class="row">
      <div class="col-12">
        <div class="d-flex justify-content-between align-items-center mb-4">
          <h2 class="page-title-bold">
            <font-awesome-icon :icon="['fas', 'exchange-alt']" class="me-2" />
            {{ $t('exchange.title') }}
          </h2>
          <div class="d-flex gap-2">
            <button
              type="button"
              class="btn btn-outline-primary"
              @click="goToDualDirectionExchange"
            >
              <font-awesome-icon :icon="['fas', 'arrows-alt-h']" class="me-2" />
              双向交易
            </button>
          </div>
        </div>
        
        <div class="row">
          <!-- 左侧：操作指引 -->
          <div class="col-md-2">
            <div class="card mb-4 exchange-guide-card">
              <div class="card-header py-2 bg-primary text-white">
                <h6 class="mb-0">
                  <font-awesome-icon :icon="['fas', 'list-ol']" class="me-2" />
                  {{ $t('exchange.exchange_steps') }}
                </h6>
              </div>
              <div class="card-body p-2">
                <div class="exchange-steps">
                  <div class="step-item" :class="{ 'active': currentStep >= 1, 'completed': currentStep > 1 }">
                    <div class="step-number">1</div>
                    <div class="step-text">{{ $t('exchange.select_foreign_currency') }}</div>
                  </div>
                  <div class="step-item" :class="{ 'active': currentStep >= 2, 'completed': currentStep > 2 }">
                    <div class="step-number">2</div>
                    <div class="step-text">{{ $t('exchange.select_buy_sell') }}</div>
                  </div>
                  <div class="step-item" :class="{ 'active': currentStep >= 3, 'completed': currentStep > 3 }">
                    <div class="step-number">3</div>
                    <div class="step-text">{{ $t('exchange.select_purpose') }}</div>
                  </div>
                  <div class="step-item" :class="{ 'active': currentStep >= 4, 'completed': currentStep > 4 }">
                    <div class="step-number">4</div>
                    <div class="step-text">{{ $t('exchange.select_denomination') }}</div>
                  </div>
                  <div class="step-item" :class="{ 'active': currentStep >= 5, 'completed': currentStep > 5 }">
                    <div class="step-number">5</div>
                    <div class="step-text">{{ $t('exchange.calculate_confirm') }}</div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 当前余额信息 -->
            <CurrencyBalanceInfo 
              :selected-currency="selectedForeignCurrencyInfo"
              @balance-updated="onBalanceUpdated"
              ref="currencyBalanceInfo"
            />
          </div>
          
          <!-- 中间：交易区域 -->
          <div class="col-md-6">
            <div class="card mb-4">
              <div class="card-body p-4">
                <div v-if="!showConfirmation">
                  <!-- 步骤1: 设置本币和外币 -->
                  <div class="mb-2 step-section">
                    <div class="d-flex align-items-center mb-1">
                      <span class="step-badge" :class="{ 'completed': currentStep > 1 }">1</span>
                      <label for="foreign_currency" class="me-2 step-label">{{ $t('exchange.select_foreign_currency') }}：</label>
                      <div class="flex-grow-1">
                        <currency-select
                          id="foreign_currency"
                          v-model="foreignCurrency"
                          @change="handleForeignCurrencyChange"
                        />
                      </div>
                    </div>
                  </div>
                  
                  <!-- 步骤2: 兑换模式选择 -->
                  <div class="mb-3 step-section">
                    <div class="d-flex align-items-center mb-1">
                      <span class="step-badge" :class="{ 'completed': currentStep > 2 }">2</span>
                      <span class="step-label">{{ $t('exchange.select_transaction_direction') }}：</span>
                    </div>
                    <div class="step-content">
                      <div class="row g-2">
                        <!-- 买入外币卡片 -->
                        <div class="col-md-6">
                          <label class="w-100 mb-0" style="cursor: pointer">
                            <div class="card h-100 exchange-mode-card" :class="{ 'active-card': exchangeMode === 'buy_foreign' }">
                              <div class="card-header py-1" :class="{ 'bg-primary text-white': exchangeMode === 'buy_foreign', 'bg-light': exchangeMode !== 'buy_foreign' }">
                                <h6 class="card-title mb-0 fs-6">{{ $t('exchange.sell_out') }} {{ foreignCurrency ? getCurrencyName(foreignCurrency) : '' }}</h6>
                              </div>
                              <div class="card-body p-2">
                                <div class="form-check">
                                  <input
                                    type="radio"
                                    id="buy_foreign"
                                    name="exchangeMode"
                                    :checked="exchangeMode === 'buy_foreign'"
                                    @change="setExchangeMode('buy_foreign')"
                                    class="form-check-input"
                                  />
                                  <div class="form-check-label">
                                    <div class="d-flex align-items-center">
                                      <CurrencyFlag 
                                        :code="baseCurrency || 'CNY'"
                                        class="me-1 currency-flag-medium"
                                      />
                                      <span class="small">{{ $t(`currencies.${baseCurrency}`) }}{{ baseCurrency }}</span>
                                      <span class="mx-1">←</span>
                                      <CurrencyFlag 
                                        v-if="foreignCurrency"
                                        :code="foreignCurrency"
                                        :custom-filename="getCurrencyCustomFlag(foreignCurrency)"
                                        class="me-1 currency-flag-large"
                                      />
                                      <span v-else class="me-1 currency-flag-large text-muted">
                                        <i class="fas fa-question-circle text-muted" style="font-size: 1.2rem;"></i>
                                      </span>
                                      <span class="small">{{ foreignCurrency ? getCurrencyName(foreignCurrency) : '' }}{{ foreignCurrency || '' }}</span>
                                    </div>
                                    <small class="text-muted d-block mt-1" style="font-size: 0.75rem;">
                                      ({{ $t('exchange.customer_buy_foreign') }} {{ foreignCurrency || '' }} {{ foreignCurrency ? getCurrencyName(foreignCurrency) : '' }})
                                    </small>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </label>
                        </div>

                        <!-- 卖出外币卡片 -->
                        <div class="col-md-6">
                          <label class="w-100 mb-0" style="cursor: pointer">
                            <div class="card h-100 exchange-mode-card" :class="{ 'active-card': exchangeMode === 'sell_foreign' }">
                              <div class="card-header py-1" :class="{ 'bg-primary text-white': exchangeMode === 'sell_foreign', 'bg-light': exchangeMode !== 'sell_foreign' }">
                                <h6 class="card-title mb-0 fs-6">{{ $t('exchange.buy_in') }} {{ foreignCurrency ? getCurrencyName(foreignCurrency) : '' }}</h6>
                              </div>
                              <div class="card-body p-2">
                                <div class="form-check">
                                  <input
                                    type="radio"
                                    id="sell_foreign"
                                    name="exchangeMode"
                                    :checked="exchangeMode === 'sell_foreign'"
                                    @change="setExchangeMode('sell_foreign')"
                                    class="form-check-input"
                                  />
                                  <div class="form-check-label">
                                    <div class="d-flex align-items-center">
                                      <CurrencyFlag 
                                        v-if="foreignCurrency"
                                        :code="foreignCurrency"
                                        :custom-filename="getCurrencyCustomFlag(foreignCurrency)"
                                        class="me-1 currency-flag-large"
                                      />
                                      <span v-else class="me-1 currency-flag-large text-muted">
                                        <i class="fas fa-question-circle text-muted" style="font-size: 1.2rem;"></i>
                                      </span>
                                      <span class="small">{{ foreignCurrency ? getCurrencyName(foreignCurrency) : '' }}{{ foreignCurrency || '' }}</span>
                                      <span class="mx-1">→</span>
                                      <CurrencyFlag 
                                        :code="baseCurrency || 'CNY'"
                                        class="me-1 currency-flag-medium"
                                      />
                                      <span class="small">{{ $t(`currencies.${baseCurrency}`) }}{{ baseCurrency }}</span>
                                    </div>
                                    <small class="text-muted d-block mt-1" style="font-size: 0.75rem;">
                                      ({{ $t('exchange.customer_sell_foreign') }} {{ foreignCurrency || '' }} {{ foreignCurrency ? getCurrencyName(foreignCurrency) : '' }})
                                    </small>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </label>
                        </div>
                      </div>
                    </div>
                    
                    <!-- 汇率显示 -->
                    <div class="alert alert-info py-1 mb-2" style="font-size: 0.875rem;">
                      {{ rateDisplay }}
                    </div>
                  </div>
                  
                  <!-- 步骤3: 用途选择 -->
                  <div class="mb-3 step-section">
                    <div class="d-flex align-items-start mb-1">
                      <span class="step-badge" :class="{ 'completed': currentStep > 3 }">3</span>
                      <span class="step-label me-2">{{ $t('exchange.select_purpose_label') }}：</span>
                      <div style="width: 200px; min-width: 200px;">
                        <select 
                          v-model="selectedPurpose" 
                          @change="handlePurposeChange"
                          class="form-select form-select-sm purpose-select"
                          :disabled="!foreignCurrency"
                          style="max-width: 200px;"
                        >
                          <option value="">{{ $t('exchange.select_purpose_placeholder') }}</option>
                          <option 
                            v-for="purpose in purposeOptions" 
                            :key="purpose.id" 
                            :value="purpose.id"
                          >
                            {{ purpose.purpose_name }}
                          </option>
                        </select>
                      </div>
                      <!-- 用途提示信息 -->
                      <div class="flex-grow-1 ms-3 purpose-info-container" v-if="purposeMessage || purposeExceeded">
                        <div v-if="purposeMessage" class="purpose-hint-inline">
                          <i class="fas fa-info-circle text-info"></i>
                          <strong>{{ $t('exchange.purpose_hint') }}：</strong>{{ purposeMessage }}
                        </div>
                        <div v-if="purposeExceeded" class="purpose-warning-inline">
                          <i class="fas fa-exclamation-triangle text-warning"></i>
                          {{ purposeWarningMessage }}
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <!-- 步骤4: 面值选择 -->
                  <div class="mb-3 step-section">
                    <div class="d-flex align-items-center mb-1">
                      <span class="step-badge" :class="{ 'completed': currentStep > 4 }">4</span>
                      <span class="step-label">{{ $t('exchange.select_denomination') }}：</span>
                    </div>
                    <div class="step-content">
                      <!-- 面值选择器 -->
                      <DenominationSelector
                        :currency-id="selectedForeignCurrencyId"
                        :currency-code="foreignCurrency"
                        :allow-multiple="true"
                        :exchange-mode="exchangeMode"
                        v-model="denominationData"
                        @change="handleDenominationChange"
                      />
                    </div>
                  </div>
                  
                  <!-- 计算结果显示 -->
                  <div v-if="resultDisplay" class="alert py-1 mb-2 exchange-prompt" :class="{'alert-info': !resultDisplay.includes('text-danger'), 'alert-danger': resultDisplay.includes('text-danger')}" style="font-size: 0.875rem;">
                    <div class="d-flex align-items-center">
                      <font-awesome-icon 
                        :icon="['fas', 'volume-up']" 
                        class="me-2 text-primary prompt-speaker"
                        @click="speakPrompt"
                        :title="$t('exchange.click_to_play_voice')"
                        style="cursor: pointer;"
                      />
                      <div v-html="resultDisplay" class="flex-grow-1"></div>
                      <button 
                        v-if="canSpeak" 
                        @click="toggleLanguage" 
                        class="btn btn-sm btn-outline-primary ms-1"
                        :title="getLanguageTitle()"
                        style="min-width: 40px;"
                      >
                        {{ getLanguageDisplay() }}
                      </button>
                      <button 
                        v-if="canSpeak" 
                        @click="speakPrompt" 
                        class="btn btn-sm btn-success ms-1"
                        :title="$t('exchange.play_voice_hint')"
                      >
                        <font-awesome-icon :icon="['fas', 'play']" />
                      </button>
                    </div>
                  </div>
                  
                  <!-- 步骤5: 操作按钮 -->
                  <div class="step-section">
                    <div class="d-flex align-items-center mb-1">
                      <span class="step-badge" :class="{ 'completed': currentStep > 5 }">5</span>
                      <span class="step-label">{{ $t('exchange.calculate_confirm_label') }}：</span>
                    </div>
                    <div class="step-content">
                      <div class="d-flex gap-2">
                        <button 
                          class="btn btn-secondary btn-sm" 
                          @click="calculateExchange"
                          :disabled="!denominationData || !denominationData.total_amount || !denominationData.combinations?.length"
                        >
                          <i class="fas fa-calculator me-1"></i>
                          {{ $t('exchange.calculate') }}
                        </button>
                        <button 
                          class="btn btn-primary btn-sm" 
                          @click="showConfirmation = true"
                          :disabled="!canConfirm || purposeExceeded"
                        >
                          <i class="fas fa-check me-1"></i>
                          {{ $t('exchange.confirm_exchange') }}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- 确认界面 -->
                <div v-else>
                  <h4 class="mb-4 text-center">{{ $t('exchange.confirm_transaction') }}</h4>
                  
                  <div class="alert alert-info mb-4">
                    <div v-html="resultDisplay"></div>
                  </div>
                  
                  <!-- 面值详情显示 -->
                  <div v-if="denominationData && denominationData.combinations" class="mb-4">
                    <h6 class="mb-3">{{ $t('exchange.denomination_details') }}</h6>
                    <div class="table-responsive">
                      <table class="table table-sm table-bordered">
                        <thead class="table-light">
                          <tr>
                            <th>{{ $t('exchange.denomination') }}</th>
                            <th>{{ $t('exchange.type') }}</th>
                            <th>{{ $t('exchange.quantity') }}</th>
                            <th>{{ $t('exchange.subtotal') }}</th>
                            <th>{{ $t('exchange.exchange_rate') }}</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="item in denominationData.combinations" :key="item.denomination_id">
                            <td>{{ formatDenominationValue(item.denomination_value) }}</td>
                            <td>
                              <span class="badge" :class="item.denomination_type === 'bill' ? 'bg-success' : 'bg-warning'">
                                {{ $t(`exchange.${item.denomination_type}`) }}
                              </span>
                            </td>
                            <td>{{ item.quantity }}</td>
                            <td>{{ formatAmount(item.subtotal) }}</td>
                            <td>
                              <div v-if="item.buy_rate && item.sell_rate" class="small">
                                <div>{{ $t('exchange.buy') }}: {{ formatRate(item.buy_rate) }}</div>
                                <div>{{ $t('exchange.sell') }}: {{ formatRate(item.sell_rate) }}</div>
                              </div>
                              <div v-else class="text-muted small">
                                {{ $t('exchange.rate_not_available') }}
                              </div>
                            </td>
                          </tr>
                        </tbody>
                        <tfoot class="table-light">
                          <tr>
                            <th colspan="4">{{ $t('exchange.combination_total') }}</th>
                            <th>{{ formatAmount(denominationData.total_amount) }}</th>
                          </tr>
                        </tfoot>
                      </table>
                    </div>
                  </div>
                  
                  <div class="mb-4">
                    <!-- 基本信息 -->
                    <div class="card mb-3 customer-info-card">
                      <div class="card-header py-2 bg-light">
                        <h6 class="mb-0">
                          <i class="fas fa-user me-2"></i>
                          {{ $t('exchange.basic_information') }}
                        </h6>
                      </div>
                      <div class="card-body">
                        <div class="mb-3">
                          <label for="customer_name" class="form-label required">{{ $t('exchange.customer_name') }}</label>
                          <input
                            type="text"
                            id="customer_name"
                            class="form-control"
                            v-model="customerName"
                            :placeholder="$t('exchange.customer_name_placeholder')"
                            required
                          />
                        </div>

                        <div class="row">
                          <div class="col-md-8">
                            <div class="mb-3">
                              <label for="customer_id" class="form-label required">{{ $t('exchange.customer_id') }}</label>
                              <input
                                type="text"
                                id="customer_id"
                                class="form-control"
                                v-model="customerId"
                                :placeholder="$t('exchange.customer_id_placeholder')"
                                required
                              />
                            </div>
                          </div>
                          <div class="col-md-4">
                            <div class="mb-3">
                              <label for="customer_country_code" class="form-label">{{ $t('exchange.country_code') }}</label>
                              <select
                                id="customer_country_code"
                                class="form-select"
                                v-model="customerCountryCode"
                              >
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
                          </div>
                        </div>
                      </div>
                    </div>

                    <!-- 联系信息 -->
                    <div class="card mb-3 customer-info-card">
                      <div class="card-header py-2 bg-light">
                        <h6 class="mb-0">
                          <i class="fas fa-address-card me-2"></i>
                          {{ $t('exchange.contact_information') }}
                        </h6>
                      </div>
                      <div class="card-body">
                        <div class="mb-3">
                          <label for="customer_address" class="form-label">{{ $t('exchange.customer_address') }}</label>
                          <textarea
                            id="customer_address"
                            class="form-control"
                            v-model="customerAddress"
                            rows="2"
                            :placeholder="$t('exchange.customer_address_placeholder')"
                          ></textarea>
                        </div>

                        <div class="mb-3">
                          <label for="customer_remarks" class="form-label">{{ $t('exchange.remarks') }}</label>
                          <textarea
                            id="customer_remarks"
                            class="form-control"
                            v-model="customerRemarks"
                            rows="2"
                            :placeholder="$t('exchange.remarks_placeholder')"
                          ></textarea>
                        </div>

                        <!-- 付款方式选择 -->
                        <div class="mb-3">
                          <label class="form-label">{{ $t('exchange.payment_method') }}</label>
                          <div class="d-flex gap-3 flex-wrap">
                            <div class="form-check">
                              <input
                                class="form-check-input"
                                type="radio"
                                name="paymentMethod"
                                id="paymentCash"
                                value="cash"
                                v-model="paymentMethod"
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
                                v-model="paymentMethod"
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
                                v-model="paymentMethod"
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
                                v-model="paymentMethod"
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
                                v-model="paymentMethod"
                              >
                              <label class="form-check-label" for="paymentOther">
                                {{ $t('exchange.payment_other_method') }}
                              </label>
                            </div>
                          </div>
                          <div class="form-check mt-2" v-if="isInstrumentPayment(paymentMethod)">
                            <input
                              class="form-check-input"
                              type="checkbox"
                              id="paymentInstrumentForeignAccount"
                              v-model="paymentIsForeignAccount"
                            >
                            <label class="form-check-label" for="paymentInstrumentForeignAccount">
                              {{ $t('exchange.payment_is_foreign_account') }}
                            </label>
                          </div>
                        </div>

                        <!-- 其他付款方式备注 (仅当选择"其他"时显示) -->
                        <div class="mb-3" v-if="paymentMethod === 'other'">
                          <input
                            type="text"
                            v-model="paymentMethodNote"
                            class="form-control"
                            :placeholder="$t('exchange.payment_other_note')"
                            maxlength="200"
                          />
                        </div>
                      </div>
                    </div>
                  </div>

                  <div class="d-flex justify-content-center">
                    <button class="btn btn-secondary me-2" @click="showConfirmation = false">
                      <i class="fas fa-arrow-left me-1"></i>
                      {{ $t('exchange.back') }}
                    </button>
                    <button
                      class="btn btn-success"
                      @click="executeTransaction"
                      :disabled="executing || disableExchange || !canConfirm"
                    >
                      <i class="fas fa-check me-1" :class="{ 'fa-spin': executing }"></i>
                      {{ executing ? $t('exchange.executing') : $t('exchange.execute') }}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 右侧：面值汇率信息 -->
          <div class="col-md-4">
            <div class="card mb-4">
              <div class="card-header py-2 bg-info text-white">
                <h6 class="mb-0">
                  <font-awesome-icon :icon="['fas', 'coins']" class="me-2" />
                  {{ $t('exchange.denomination_rates') }}
                </h6>
              </div>
              <div class="card-body p-0">
                <div v-if="selectedForeignCurrencyId && denominationRates.length > 0" class="denomination-rates-list">
                  <div 
                    v-for="rate in denominationRates" 
                    :key="rate.denomination_id" 
                    class="denomination-rate-item"
                  >
                    <div class="denomination-info">
                      <div class="denomination-value">{{ formatDenominationValue(rate.denomination_value) }}</div>
                      <div class="denomination-type">
                        <span class="badge" :class="rate.denomination_type === 'bill' ? 'bg-success' : 'bg-warning'">
                          {{ $t(`exchange.${rate.denomination_type}`) }}
                        </span>
                      </div>
                    </div>
                    <div class="rate-values">
                      <div class="rate-buy">
                        <small class="text-muted">{{ $t('exchange.buy_rate') }}</small>
                        <div class="rate-number">{{ rate.buy_rate || '-' }}</div>
                      </div>
                      <div class="rate-sell">
                        <small class="text-muted">{{ $t('exchange.sell_rate') }}</small>
                        <div class="rate-number">{{ rate.sell_rate || '-' }}</div>
                      </div>
                    </div>
                  </div>
                </div>
                <div v-else class="text-center p-4 text-muted">
                  <i class="fas fa-coins fa-2x mb-2"></i>
                  <div>{{ $t('exchange.no_denomination_rates') }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import CurrencyFlag from '@/components/CurrencyFlag.vue'
import CurrencySelect from '@/components/CurrencySelect.vue'
import CurrencyBalanceInfo from '@/components/CurrencyBalanceInfo.vue'
import DenominationSelector from '@/components/DenominationSelector.vue'
import { getCurrencyName } from '@/utils/currencyTranslator'
import rateService from '@/services/api/rateService'
import customerReservationMixin from './exchange/mixins/customerReservationMixin'

export default {
  mixins: [customerReservationMixin],
  name: 'ExchangeViewWithDenominations',
  components: {
    CurrencyFlag,
    CurrencySelect,
    CurrencyBalanceInfo,
    DenominationSelector
  },
  data() {
    const userInfo = JSON.parse(localStorage.getItem('user') || '{}');
    const branchCurrency = userInfo.branch_currency || null;
    
    return {
      userInfo: userInfo,
      userBranchCurrency: branchCurrency,
      baseCurrency: branchCurrency?.code || '',
      baseCurrencyName: branchCurrency?.name || '',
      
      // 币种数据
      availableCurrencies: {},
      currencyIdMap: {},
      currencyNames: {},
      foreignCurrency: '',
      selectedForeignCurrencyId: null,
      
      // 汇率数据
      topRates: [],
      rateSearchKeyword: '',
      denominationRates: [],
      
      // 状态变量
      exchangeMode: '',
      denominationData: null,
      rateDisplay: '',
      resultDisplay: '',
      showConfirmation: false,
      customerName: '',
      customerId: '',
      customerCountryCode: '',
      customerAddress: '',
      customerRemarks: '',
      paymentMethod: 'cash', // 付款方式，默认现金
      paymentIsForeignAccount: false, // 是否使用外币账户
      paymentMethodNote: '', // 其他付款方式备注

      calculatedLocalAmount: 0,
      approvedReservationAmount: null,
      lastReservationStatusCode: null,
      reservationData: null,  // 🆕 存储预约数据用于关联交易

      // 交易成功
      transactionSuccess: false,
      transactionDetails: {},
      
      // 加载状态
      loading: {
        currencies: false,
        rates: false,
        transaction: false
      },
      
      // 错误状态
      error: {
        currencies: null,
        rates: null,
        transaction: null
      },
      
      // 步骤控制
      currentStep: 1,
      
      // 用途相关
      purposeOptions: [],
      selectedPurpose: '',
      purposeMessage: '',
      purposeExceeded: false,
      purposeWarningMessage: '',

      // 国家列表
      countries: [],
      currentCountryLanguage: 'zh',
      
      // 语音相关
      canSpeak: false,
      currentPromptText: '',
      currentLanguage: 'zh',
      
      // 执行状态
      executing: false
    };
  },
  computed: {
    selectedForeignCurrencyInfo() {
      if (!this.foreignCurrency) return null;
      return this.availableCurrencies[this.foreignCurrency] || null;
    },
    
    foreignCurrencyName() {
      return this.foreignCurrency ? getCurrencyName(this.foreignCurrency) : '';
    },
    
    canConfirm() {
      if (this.disableExchange) {
        return false;
      }

      return this.denominationData &&
             this.denominationData.total_amount > 0 &&
             this.calculatedLocalAmount > 0 &&
             this.selectedPurpose &&
             this.customerName.trim() &&
             this.customerId.trim();
    },
  },
  mounted() {
    this.initializeData();
    this.checkSpeechSupport();

    this.$watch('paymentMethod', (newValue) => {
      if (!this.isInstrumentPayment(newValue)) {
        this.paymentIsForeignAccount = false;
      }
      if (newValue !== 'other') {
        this.paymentMethodNote = '';
      }
    });

    this.$watch('paymentIsForeignAccount', (newValue) => {
      if (!this.isInstrumentPayment(this.paymentMethod) && newValue) {
        this.paymentIsForeignAccount = false;
      }
    });

    this.$watch(
      () => this.$i18n?.locale,
      (newLocale, oldLocale) => {
        if (!newLocale || newLocale === oldLocale) {
          return;
        }
        this.loadCountries(newLocale);
      }
    );
  },
  methods: {
    isInstrumentPayment(method) {
      return ['instrument_cheque', 'instrument_draft', 'instrument_other'].includes(method);
    },

    async initializeData() {
      await Promise.all([
        this.loadCurrencies(),
        this.loadRates(),
        this.loadPurposeOptions(),
        this.loadCountries()
      ]);
    },
    
    async loadCurrencies() {
      this.loading.currencies = true;
      try {
        const response = await this.$api.get('/rates/available_currencies');
        if (response.data.success) {
          this.availableCurrencies = {};
          response.data.currencies.forEach(currency => {
            this.availableCurrencies[currency.currency_code] = currency;
            this.currencyIdMap[currency.currency_code] = currency.id;
            this.currencyNames[currency.currency_code] = currency.currency_name;
          });
        }
      } catch (error) {
        console.error('加载币种失败:', error);
        this.error.currencies = error.message;
      } finally {
        this.loading.currencies = false;
      }
    },
    
    async loadRates() {
      this.loading.rates = true;
      try {
        const response = await rateService.getCurrentRates(true);
        if (response.data.success) {
          this.topRates = response.data.data || [];
        }
      } catch (error) {
        console.error('加载汇率失败:', error);
        this.error.rates = error.message;
      } finally {
        this.loading.rates = false;
      }
    },
    
    async loadPurposeOptions() {
      try {
        if (!this.foreignCurrency) {
          this.purposeOptions = [];
          return;
        }

        const response = await this.$api.get(`/purpose-limits/by-currency/${this.foreignCurrency}`);
        if (response.data.success) {
          this.purposeOptions = response.data.purposes || [];
        }
      } catch (error) {
        console.error('加载用途选项失败:', error);
        this.purposeOptions = [];
      }
    },

    async loadCountries(localeOverride) {
      try {
        console.log('[ExchangeViewWithDenominations] 开始加载国家列表...')
        const locale = localeOverride || this.$i18n?.locale || 'zh-CN'
        const language = this.resolveCountryLanguage(locale)

        if (this.currentCountryLanguage === language && this.countries.length) {
          console.log('[ExchangeViewWithDenominations] 国家列表已是最新语言:', language)
          return
        }

        const response = await this.$api.get(`/system/countries?language=${language}&active_only=true`)
        console.log('[ExchangeViewWithDenominations] 国家API响应:', response.data)
        if (response.data.success) {
          const countries = response.data.countries || []
          this.countries = countries.map(country => ({
            ...country,
            country_name: country.country_name || this.getCountryNameByLanguage(country, language)
          }))
          this.currentCountryLanguage = language
          console.log('[ExchangeViewWithDenominations] 加载到的国家数量:', this.countries.length)
        }
      } catch (error) {
        console.error('[ExchangeViewWithDenominations] 获取国家列表失败:', error)
        // 失败时不显示错误提示，使用空列表
        this.countries = []
      }
    },

    resolveCountryLanguage(locale) {
      const normalized = (locale || 'zh').toLowerCase()
      if (normalized.startsWith('en')) {
        return 'en'
      }
      if (normalized.startsWith('th')) {
        return 'th'
      }
      return 'zh'
    },

    getCountryNameByLanguage(country, language) {
      if (!country) {
        return ''
      }
      if (language === 'en') {
        return country.country_name_en || country.country_name_th || country.country_name_zh || country.country_name
      }
      if (language === 'th') {
        return country.country_name_th || country.country_name_en || country.country_name_zh || country.country_name
      }
      return country.country_name_zh || country.country_name_en || country.country_name_th || country.country_name
    },
    
    handleForeignCurrencyChange(currencyCode) {
      this.foreignCurrency = currencyCode;
      this.selectedForeignCurrencyId = this.currencyIdMap[currencyCode];
      this.denominationData = null;
      this.updateCurrentStep();
      this.updateRateDisplay();
      this.loadDenominationRates();
      this.loadPurposeOptions();
    },
    
    setExchangeMode(mode) {
      this.exchangeMode = mode;
      this.updateCurrentStep();
      this.updateRateDisplay();
      // 重新计算兑换结果，因为汇率方向已改变
      if (this.denominationData && this.denominationData.total_amount > 0) {
        this.calculateExchange();
      }
    },
    
    handlePurposeChange() {
      this.updateCurrentStep();
      // 处理用途相关的逻辑
    },
    
    async loadDenominationRates() {
      if (!this.selectedForeignCurrencyId) {
        this.denominationRates = [];
        return;
      }
      
      try {
        const response = await this.$api.get(`/denominations/rates`, {
          params: { currency_id: this.selectedForeignCurrencyId }
        });
        
        if (response.data.success) {
          this.denominationRates = response.data.data || [];
        } else {
          console.warn('加载面值汇率失败:', response.data.message);
          this.denominationRates = [];
        }
      } catch (error) {
        console.error('加载面值汇率失败:', error);
        this.denominationRates = [];
      }
    },
    
    handleDenominationChange(data) {
      this.denominationData = data;
      this.updateCurrentStep();
      this.calculateExchange();
    },
    
    updateCurrentStep() {
      let step = 1;
      if (this.foreignCurrency) step = 2;
      if (this.exchangeMode) step = 3;
      if (this.selectedPurpose) step = 4;
      if (this.denominationData && this.denominationData.total_amount > 0) step = 5;
      this.currentStep = step;
    },
    
    updateRateDisplay() {
      if (!this.foreignCurrency || !this.exchangeMode) {
        this.rateDisplay = '';
        return;
      }
      
      // 在面值兑换模式下，显示面值汇率信息
      if (this.denominationRates && this.denominationRates.length > 0) {
        const hasRates = this.denominationRates.some(rate => rate.buy_rate && rate.sell_rate);
        if (hasRates) {
          this.rateDisplay = this.$t('exchange.denomination_rates_available');
        } else {
          this.rateDisplay = this.$t('exchange.denomination_rates_unavailable');
        }
      } else {
        // 回退到标准汇率显示
        const rate = this.topRates.find(r => r.currency_code === this.foreignCurrency);
        if (rate) {
          const buyRate = rate.buy_rate;
          const sellRate = rate.sell_rate;
          
          if (this.exchangeMode === 'buy_foreign') {
            this.rateDisplay = `${this.$t('exchange.sell_rate')}: ${sellRate}`;
          } else {
            this.rateDisplay = `${this.$t('exchange.buy_rate')}: ${buyRate}`;
          }
        } else {
          this.rateDisplay = this.$t('exchange.rate_unavailable');
        }
      }
    },
    
    async calculateExchange() {
      if (!this.denominationData || !this.denominationData.total_amount) {
        this.resultDisplay = '';
        this.calculatedLocalAmount = 0;
        return;
      }
      
      // 在面值兑换模式下，使用面值汇率进行计算
      if (this.denominationRates && this.denominationRates.length > 0) {
        // 计算加权平均汇率
        let totalWeight = 0;
        let weightedBuyRate = 0;
        let weightedSellRate = 0;
        
        for (const item of this.denominationData.combinations) {
          // 使用新结构中的汇率数据
          if (item.buy_rate && item.sell_rate) {
            const weight = item.subtotal;
            totalWeight += weight;
            weightedBuyRate += item.buy_rate * weight;
            weightedSellRate += item.sell_rate * weight;
          }
        }
        
        if (totalWeight > 0) {
          const avgBuyRate = weightedBuyRate / totalWeight;
          const avgSellRate = weightedSellRate / totalWeight;
          const relevantRate = this.exchangeMode === 'sell_foreign' ? avgBuyRate : avgSellRate;
          const totalAmount = this.denominationData.total_amount;

          // 添加调试信息
          console.log('=== 计算调试信息 ===');
          console.log('网点本币:', this.baseCurrency, this.baseCurrencyName);
          console.log('选择外币:', this.foreignCurrency, this.foreignCurrencyName);
          console.log('交易模式:', this.exchangeMode);
          console.log('总权重:', totalWeight);
          console.log('加权买入汇率总和:', weightedBuyRate);
          console.log('加权卖出汇率总和:', weightedSellRate);
          console.log('平均买入汇率:', avgBuyRate);
          console.log('平均卖出汇率:', avgSellRate);
          console.log('使用的汇率:', relevantRate);
          console.log('外币总金额:', totalAmount, this.foreignCurrency);
          console.log('面值组合明细:', this.denominationData.combinations);

          let resultAmount;
          if (this.exchangeMode === 'sell_foreign') {
            // 网点买入外币：外币金额 * 买入汇率 = 本币金额
            resultAmount = (totalAmount * relevantRate).toFixed(2);
            console.log('网点买入外币模式: 外币金额 * 买入汇率 = 本币金额');
            console.log(`${totalAmount} ${this.foreignCurrency} * ${relevantRate} = ${resultAmount} ${this.baseCurrency}`);
          } else {
            // 网点卖出外币：外币金额 * 卖出汇率 = 本币金额
            resultAmount = (totalAmount * relevantRate).toFixed(2);
            console.log('网点卖出外币模式: 外币金额 * 卖出汇率 = 本币金额');
            console.log(`${totalAmount} ${this.foreignCurrency} * ${relevantRate} = ${resultAmount} ${this.baseCurrency}`);
          }

          this.resultDisplay = this.generateExchangePrompt(totalAmount, resultAmount, relevantRate);
          this.calculatedLocalAmount = Number(resultAmount);
          console.log('生成提示:', this.resultDisplay);
          console.log('==================');
          return;
        }
      }
      
      // 回退到标准汇率
      const rate = this.topRates.find(r => r.currency_code === this.foreignCurrency);
      if (!rate) {
        this.resultDisplay = this.$t('exchange.rate_unavailable');
        this.calculatedLocalAmount = 0;
        return;
      }
      
      const relevantRate = this.exchangeMode === 'sell_foreign' ? rate.buy_rate : rate.sell_rate;
      const totalAmount = this.denominationData.total_amount;
      
      let resultAmount;
      if (this.exchangeMode === 'sell_foreign') {
        // 网点买入外币：外币金额 * 买入汇率 = 本币金额
        resultAmount = (totalAmount * relevantRate).toFixed(2);
      } else {
        // 网点卖出外币：外币金额 * 卖出汇率 = 本币金额
        resultAmount = (totalAmount * relevantRate).toFixed(2);
      }
      
      this.resultDisplay = this.generateExchangePrompt(totalAmount, resultAmount, relevantRate);
      this.calculatedLocalAmount = Number(resultAmount);
    },
    
    generateExchangePrompt(foreignAmount, localAmount, rate) {
      const foreignCurrencyName = this.foreignCurrencyName;
      const localCurrencyName = this.baseCurrencyName;

      if (this.exchangeMode === 'buy_foreign') {
        return `${this.$t('exchange.customer_pays')} ${this.formatAmount(localAmount)} ${localCurrencyName}，获得 ${this.formatAmount(foreignAmount)} ${foreignCurrencyName}（${this.$t('exchange.rate')}: ${rate}）`;
      } else {
        return `${this.$t('exchange.customer_pays')} ${this.formatAmount(foreignAmount)} ${foreignCurrencyName}，获得 ${this.formatAmount(localAmount)} ${localCurrencyName}（${this.$t('exchange.rate')}: ${rate}）`;
      }
    },
    
    async executeTransaction() {
      if (!this.canConfirm) return;
      if (this.disableExchange) {
        this.$toast?.warning?.('Reservation is pending review. Please complete the approval before executing the exchange.');
        return;
      }

      const localAmount = Math.abs(this.calculatedLocalAmount || 0);
      if (!localAmount) {
        this.$toast?.warning?.('Unable to determine the local amount. Please complete the denomination calculation first.');
        return;
      }

      this.executing = true;
      try {
        const transactionData = {
          currency_id: this.selectedForeignCurrencyId,
          exchange_mode: this.exchangeMode,
          denomination_data: {
            combinations: this.denominationData.combinations,
            total_amount: this.denominationData.total_amount,
            currency_id: this.denominationData.currency_id,
            currency_code: this.denominationData.currency_code
          },
          customer_info: {
            name: this.customerName,
            id_number: this.customerId,
            country_code: this.customerCountryCode || '',
            address: this.customerAddress || '',
            remarks: this.customerRemarks,
            payment_method: this.paymentMethod,
            payment_is_foreign_account: this.paymentIsForeignAccount,
            use_fcd: this.paymentIsForeignAccount,
            payment_method_note: this.paymentMethodNote,
            local_amount: localAmount
          },
          purpose_id: this.selectedPurpose
        };

        if (this.reservationStatus && this.reservationStatus.status === 'approved') {
          const approvedAmount = Number(this.approvedReservationAmount ?? this.reservationStatus.approved_amount ?? 0);
          if (localAmount > approvedAmount) {
            this.$toast?.error?.(`Local amount (${localAmount.toLocaleString()} THB) exceeds the approved limit (${approvedAmount.toLocaleString()} THB).`);
            this.executing = false;
            return;
          }

          transactionData.customer_info.reservation_id = this.reservationStatus.reservation_id || this.reservationStatus.id;
          transactionData.customer_info.reservation_no = this.reservationStatus.reservation_no;
          transactionData.customer_info.approved_amount = approvedAmount;
        }

        const response = await this.$api.post('/exchange/perform-dual-direction', transactionData);
        if (response.data.success) {
          this.transactionSuccess = true;
          this.transactionDetails = response.data.data;
          this.$toast?.success?.('Denomination exchange completed successfully.');

          // 🆕 如果有关联的预约，标记为已完成
          if (this.reservationData && this.reservationData.reservation_id) {
            await this.markReservationCompleted(
              this.reservationData.reservation_id,
              response.data.data.transaction_id
            );
          }

          this.resetForm();
        } else {
          this.$toast?.error?.(response.data.message || 'Denomination exchange failed.');
        }
      } catch (error) {
        console.error('executeTransaction failed:', error);
        this.$toast?.error?.('Failed to execute denomination exchange.');
      } finally {
        this.executing = false;
      }
    },

    resetForm() {
      this.foreignCurrency = '';
      this.selectedForeignCurrencyId = null;
      this.exchangeMode = '';
      this.denominationData = null;
      this.selectedPurpose = '';
      this.customerName = '';
      this.customerId = '';
      this.customerCountryCode = '';
      this.customerAddress = '';
      this.customerRemarks = '';
      this.paymentMethod = 'cash';
      this.paymentIsForeignAccount = false;
      this.paymentMethodNote = '';
      this.resultDisplay = '';
      this.showConfirmation = false;
      this.currentStep = 1;
      this.calculatedLocalAmount = 0;
      this.approvedReservationAmount = null;
      this.lastReservationStatusCode = null;
      this.reservationData = null;  // 🆕 清除预约数据
    },

    async onReservationStatusUpdated(reservation, error) {
      const trimmedId = (this.customerId || '').trim();
      let statusKey = 'empty';

      if (reservation) {
        const idPart = reservation.reservation_id || reservation.id || reservation.reservation_no || 'unknown';
        statusKey = `${reservation.status}:${idPart}`;
      } else if (error) {
        statusKey = `error:${error.name || 'unknown'}`;
      } else if (trimmedId) {
        statusKey = 'none';
      }

      if (reservation && this.lastReservationStatusCode !== statusKey) {
        if (reservation.status === 'approved') {
          this.$toast?.success?.(`Reservation approved. Limit: ${Number(reservation.approved_amount || 0).toLocaleString()} THB.`);

          // 🆕 预填充已批准的预约数据
          this.prefillApprovedReservation(reservation);
        } else if (reservation.status === 'pending') {
          this.$toast?.warning?.('Reservation is pending review. Denomination exchange is temporarily blocked.');
        } else if (reservation.status === 'rejected') {
          const reason = reservation.rejection_reason || 'No rejection reason provided.';
          this.$toast?.error?.(`Reservation was rejected. Reason: ${reason}`);
        }
      }

      if (!reservation && !error && trimmedId && this.lastReservationStatusCode !== statusKey) {
        this.$toast?.info?.('No active reservation found for this customer. Proceed with the standard flow.');
      }

      this.approvedReservationAmount = reservation && reservation.status === 'approved'
        ? Number(reservation.approved_amount || 0)
        : null;

      this.lastReservationStatusCode = statusKey;
    },

    prefillApprovedReservation(reservation) {
      /**
       * 🆕 预填充已批准的AMLO预约数据到兑换表单
       *
       * 功能：
       * 1. 自动填充币种、方向、金额
       * 2. 填充客户信息（姓名、国家、地址）
       * 3. 存储预约ID用于后续关联
       */
      console.log('[ExchangeViewWithDenominations] 预填充预约数据:', reservation);

      try {
        // 1. 填充币种信息
        if (reservation.currency_code) {
          this.foreignCurrency = reservation.currency_code;
          this.selectedForeignCurrencyId = reservation.currency_id;
          this.handleForeignCurrencyChange(reservation.currency_code);
        }

        // 2. 填充交易方向
        if (reservation.direction) {
          // direction字段值: 'buy', 'sell', 'dual_direction'
          // exchangeMode需要映射为: 'buy_foreign', 'sell_foreign', 'dual_direction'
          if (reservation.direction === 'buy') {
            this.setExchangeMode('sell_foreign');  // 网点买入 = 客户卖出外币
          } else if (reservation.direction === 'sell') {
            this.setExchangeMode('buy_foreign');   // 网点卖出 = 客户买入外币
          } else if (reservation.direction === 'dual_direction') {
            this.setExchangeMode('dual_direction');
          }
        }

        // 3. 填充客户信息（如果表单还没填写）
        if (!this.customerName && reservation.customer_name) {
          this.customerName = reservation.customer_name;
        }
        if (!this.customerCountryCode && reservation.customer_country_code) {
          this.customerCountryCode = reservation.customer_country_code;
        }

        // 4. 从form_data提取地址信息（如果有）
        if (reservation.form_data && reservation.form_data.maker_address_full) {
          if (!this.customerAddress) {
            this.customerAddress = reservation.form_data.maker_address_full;
          }
        }

        // 5. 存储预约ID和相关数据，用于交易提交时关联
        this.reservationData = {
          reservation_id: reservation.reservation_id || reservation.id,
          reservation_no: reservation.reservation_no,
          report_type: reservation.report_type,
          approved_amount: reservation.approved_amount
        };

        console.log('[ExchangeViewWithDenominations] 预填充完成', {
          foreignCurrency: this.foreignCurrency,
          exchangeMode: this.exchangeMode,
          customerName: this.customerName,
          reservationData: this.reservationData
        });

        // 6. 显示提示信息
        this.$toast?.info?.(`已自动填充预约信息: ${reservation.currency_code} ${reservation.direction === 'buy' ? '买入' : '卖出'}`);

      } catch (error) {
        console.error('[ExchangeViewWithDenominations] 预填充失败:', error);
        this.$toast?.error?.('预约数据填充失败，请手动输入');
      }
    },

    onReservationStatusCleared() {
      this.lastReservationStatusCode = null;
      this.approvedReservationAmount = null;
      this.reservationData = null;  // 🆕 清除预约数据
    },

    async markReservationCompleted(reservationId, transactionId) {
      /**
       * 🆕 标记预约为已完成
       *
       * @param {number} reservationId - 预约ID
       * @param {number} transactionId - 实际执行的交易ID
       */
      try {
        console.log('[ExchangeViewWithDenominations] 标记预约完成:', {
          reservationId,
          transactionId
        });

        const response = await this.$api.post(
          `/amlo/reservations/${reservationId}/complete`,
          {
            transaction_id: transactionId
          }
        );

        if (response.data.success) {
          console.log('[ExchangeViewWithDenominations] 预约已标记为完成:', response.data);
          this.$toast?.success?.(`预约 ${response.data.data.reservation_no} 已关联到交易`);
        } else {
          console.warn('[ExchangeViewWithDenominations] 标记预约完成失败:', response.data.message);
        }
      } catch (error) {
        console.error('[ExchangeViewWithDenominations] 标记预约完成异常:', error);
        // 不影响主流程，只记录错误
      }
    },
    
    selectRate(rate) {
      this.foreignCurrency = rate.currency_code;
      this.selectedForeignCurrencyId = rate.currency_id;
      this.handleForeignCurrencyChange(rate.currency_code);
    },
    
    formatDenominationValue(value) {
      if (!value && value !== 0) return '0'
      return new Intl.NumberFormat('zh-CN', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
      }).format(value);
    },
    
    formatAmount(amount) {
      if (!amount && amount !== 0) return '0.00'
      return new Intl.NumberFormat('zh-CN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(amount);
    },
    
    getCurrencyName(code) {
      return getCurrencyName(code);
    },
    
    getCurrencyCustomFlag(code) {
      const currency = this.availableCurrencies[code];
      return currency ? currency.custom_flag_filename : null;
    },
    
    checkSpeechSupport() {
      this.canSpeak = 'speechSynthesis' in window;
    },
    
    speakPrompt() {
      if (!this.canSpeak || !this.resultDisplay) return;
      
      const utterance = new SpeechSynthesisUtterance(this.currentPromptText || this.resultDisplay);
      utterance.lang = this.currentLanguage === 'zh' ? 'zh-CN' : 'en-US';
      speechSynthesis.speak(utterance);
    },
    
    toggleLanguage() {
      this.currentLanguage = this.currentLanguage === 'zh' ? 'en' : 'zh';
    },
    
    getLanguageTitle() {
      const isChinese = this.currentLanguage === 'zh';
      return isChinese ? '切换到英文' : 'Switch to Chinese';
    },
    
    getLanguageDisplay() {
      return this.currentLanguage === 'zh' ? 'EN' : '中文';
    },
    
    onBalanceUpdated() {
      // 处理余额更新
    },

    formatRate(rate) {
      if (!rate) return '---'
      return new Intl.NumberFormat('zh-CN', {
        minimumFractionDigits: 4,
        maximumFractionDigits: 4
      }).format(rate)
    },

    // 跳转到双向交易页面
    goToDualDirectionExchange() {
      this.$router.push({ name: 'dual-direction-exchange' })
    }
  }
}
</script>

<style scoped>
/* 样式保持与原ExchangeView.vue一致 */
.exchange-guide-card {
  border-left: 4px solid var(--bs-primary);
}

.exchange-steps {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.step-item {
  display: flex;
  align-items: center;
  padding: 0.5rem;
  border-radius: 0.375rem;
  transition: all 0.2s ease;
}

.step-item.active {
  background-color: var(--bs-primary);
  color: white;
}

.step-item.completed {
  background-color: var(--bs-success);
  color: white;
}

.step-number {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: bold;
  margin-right: 0.5rem;
}

.step-text {
  font-size: 0.875rem;
}

.exchange-mode-card {
  cursor: pointer;
  transition: all 0.2s ease;
}

.exchange-mode-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.exchange-mode-card.active-card {
  border-color: var(--bs-primary);
  box-shadow: 0 0 0 0.2rem rgba(13, 110, 253, 0.25);
}

.rate-list {
  max-height: 400px;
  overflow-y: auto;
}

.rate-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  border-bottom: 1px solid #e9ecef;
  cursor: pointer;
  transition: all 0.2s ease;
}

.rate-item:hover {
  background-color: #f8f9fa;
}

.rate-item.selected {
  background-color: var(--bs-primary);
  color: white;
}

.rate-currency {
  display: flex;
  align-items: center;
  font-weight: 500;
}

.rate-values {
  display: flex;
  gap: 1rem;
  font-size: 0.875rem;
}

.rate-buy, .rate-sell {
  min-width: 60px;
  text-align: right;
}

.currency-flag-medium {
  width: 20px;
  height: 15px;
}

.currency-flag-large {
  width: 24px;
  height: 18px;
}

.step-badge {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background-color: #e9ecef;
  color: #6c757d;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: bold;
  margin-right: 0.5rem;
}

/* 面值汇率列表样式 */
.denomination-rates-list {
  max-height: 600px;
  overflow-y: auto;
}

.denomination-rate-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #e9ecef;
  transition: background-color 0.2s;
}

.denomination-rate-item:hover {
  background-color: #f8f9fa;
}

.denomination-rate-item:last-child {
  border-bottom: none;
}

.denomination-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.denomination-value {
  font-weight: 600;
  font-size: 1rem;
  color: #495057;
}

.denomination-type {
  font-size: 0.75rem;
}

.rate-values {
  display: flex;
  gap: 1.5rem;
  text-align: center;
}

.rate-buy, .rate-sell {
  min-width: 60px;
}

.rate-number {
  font-weight: 600;
  font-size: 0.9rem;
  color: #495057;
}

.step-badge.completed {
  background-color: var(--bs-success);
  color: white;
}

.step-label {
  font-weight: 500;
  font-size: 0.875rem;
}

.exchange-prompt {
  border-left: 4px solid var(--bs-info);
}

.prompt-speaker {
  cursor: pointer;
  transition: color 0.2s ease;
}

.prompt-speaker:hover {
  color: var(--bs-primary) !important;
}

/* 客户信息表单样式 */
.card-header {
  border-bottom: 2px solid #e9ecef;
}

.form-label.required::after {
  content: ' *';
  color: #dc3545;
  font-weight: bold;
}

.customer-info-card {
  border-left: 4px solid var(--bs-info);
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.customer-info-card .card-header {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
}

.form-control:focus, .form-select:focus {
  border-color: var(--bs-primary);
  box-shadow: 0 0 0 0.2rem rgba(13, 110, 253, 0.25);
}
</style>

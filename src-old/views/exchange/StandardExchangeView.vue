<template>
  <div class="container-fluid py-4">
    <div class="row">
      <div class="col-12">
        <div class="d-flex justify-content-between align-items-center mb-4">
          <h2 class="page-title-bold">
            <font-awesome-icon :icon="['fas', 'exchange-alt']" class="me-2" />
            {{ $t('exchange.title') }}
          </h2>
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
                    <div class="step-text">{{ $t('exchange.input_amount') }}</div>
                  </div>
                  <div class="step-item" :class="{ 'active': currentStep >= 5, 'completed': currentStep > 5 }">
                    <div class="step-number">5</div>
                    <div class="step-text">{{ $t('exchange.calculate_confirm') }}</div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 新增：上一笔交易信息 -->
            <div class="card mb-4 last-transaction-card" v-if="lastTransaction">
              <div class="card-header py-2 bg-info text-white">
                <h6 class="mb-0">
                  <font-awesome-icon :icon="['fas', 'history']" class="me-2" />
                  {{ $t('exchange.last_transaction') }}
                </h6>
              </div>
              <div class="card-body p-2">
                <div class="last-transaction-info">
                  <div class="transaction-item" v-if="lastTransaction.transactionNo">
                    <span class="label">{{ $t('exchange.transaction_number') }}：</span>
                    <span class="value transaction-no">{{ lastTransaction.transactionNo }}</span>
                  </div>
                  <div class="transaction-item">
                    <span class="label">{{ $t('exchange.transaction_type') }}：</span>
                    <span class="value">{{ lastTransaction.type === 'buy' ? $t('exchange.buy') : $t('exchange.sell') }} {{ lastTransaction.currency }}</span>
                  </div>
                  <div class="transaction-item">
                    <span class="label">{{ $t('exchange.customer_paid') }}：</span>
                    <span class="value">{{ formatAmount(lastTransaction.customerPaid) }} {{ lastTransaction.customerCurrency }}</span>
                  </div>
                  <div class="transaction-item">
                    <span class="label">{{ $t('exchange.bank_paid') }}：</span>
                    <span class="value">{{ formatAmount(lastTransaction.bankPaid) }} {{ lastTransaction.bankCurrency }}</span>
                  </div>
                  <div class="transaction-item">
                    <span class="label">{{ $t('exchange.transaction_time') }}：</span>
                    <span class="value">{{ formatDateTime(lastTransaction.date, lastTransaction.time) }}</span>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 新增：当前余额信息 -->
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
                      <!-- 用途提示信息 - 调整为可换行布局 -->
                      <div class="flex-grow-1 ms-3 purpose-info-container" v-if="purposeMessage || purposeExceeded">
                        <div v-if="purposeMessage" class="purpose-hint-inline">
                          <i class="fas fa-info-circle text-info"></i>
                          <strong>{{ $t('exchange.purpose_hint') }}：</strong>{{ purposeMessage }}
                    </div>
                    <!-- 限额提醒 -->
                        <div v-if="purposeExceeded" class="purpose-warning-inline">
                          <i class="fas fa-exclamation-triangle text-warning"></i>
                      {{ purposeWarningMessage }}
                        </div>
                      </div>
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

                  <!-- 交易类型选择 (大额交易时显示) -->
                  <div v-if="shouldShowExchangeType" class="alert alert-info border-info bg-light-subtle mb-2">
                    <h6 class="fw-bold mb-2 d-flex align-items-center">
                      <font-awesome-icon :icon="['fas', 'file-invoice-dollar']" class="me-2" />
                      {{ $t('exchange.exchange_type_selection') }}
                    </h6>
                    <div class="d-flex flex-column gap-2">
                      <div class="form-check">
                        <input class="form-check-input" type="radio" id="exchange_type_normal" value="normal" v-model="exchangeType" />
                        <label class="form-check-label" for="exchange_type_normal">
                          <strong>{{ $t('exchange.exchange_type_normal') }}</strong> - {{ $t('exchange.exchange_type_normal_desc') }}
                        </label>
                      </div>
                      <div class="form-check">
                        <input class="form-check-input" type="radio" id="exchange_type_asset" value="asset_backed" v-model="exchangeType" />
                        <label class="form-check-label" for="exchange_type_asset">
                          <strong>{{ $t('exchange.exchange_type_asset_mortgage') }}</strong> - {{ $t('exchange.exchange_type_asset_mortgage_desc') }}
                        </label>
                      </div>
                    </div>
                    <div class="mt-3">
                      <label class="form-label">{{ $t('exchange.funding_source') }}</label>
                      <select class="form-select" v-model="selectedFundingSource" :disabled="loading.fundingSources">
                        <option value="">{{ $t('exchange.select_funding_source') }}</option>
                        <option v-for="source in fundingSourceOptions" :key="source.id" :value="source.source_code">
                          {{ getFundingSourceLabel(source) }}
                        </option>
                      </select>
                      <small v-if="loading.fundingSources" class="text-muted">{{ $t('common.loading') }}</small>
                    </div>
                  </div>
                  
                  <!-- 步骤4: 金额输入 -->
                  <div class="mb-3 step-section">
                    <div class="d-flex align-items-center mb-1">
                      <span class="step-badge" :class="{ 'completed': currentStep > 4 }">4</span>
                      <span class="step-label">{{ $t('exchange.input_amount_label') }}：</span>
                    </div>
                    <div class="step-content">
                      <div class="amount-type-selector mb-2">
                        <div class="row g-2">
                          <div class="col-6">
                            <label class="amount-type-card" :class="{ 'active': amountType === 'have' }">
                              <input 
                                class="form-check-input visually-hidden" 
                                type="radio" 
                                id="have_amount" 
                                name="amountType"
                                :checked="amountType === 'have'"
                                @change="toggleAmountInput('have')"
                              />
                              <div class="amount-type-content">
                                <div class="amount-type-icon">
                                  <font-awesome-icon :icon="['fas', 'wallet']" />
                                </div>
                                <div class="amount-type-label">
                                  <strong style="font-size: 0.875rem;">{{ $t('exchange.customer_payment') }}</strong>
                                  <small class="d-block text-muted" style="font-size: 0.7rem;">{{ $t('exchange.customer_payment_desc') }}</small>
                                </div>
                              </div>
                            </label>
                          </div>
                          <div class="col-6">
                            <label class="amount-type-card" :class="{ 'active': amountType === 'want' }">
                              <input 
                                class="form-check-input visually-hidden" 
                                type="radio" 
                                id="want_amount" 
                                name="amountType"
                                :checked="amountType === 'want'"
                                @change="toggleAmountInput('want')"
                              />
                              <div class="amount-type-content">
                                <div class="amount-type-icon">
                                  <font-awesome-icon :icon="['fas', 'hand-holding-dollar']" />
                                </div>
                                <div class="amount-type-label">
                                  <strong style="font-size: 0.875rem;">{{ $t('exchange.customer_needs') }}</strong>
                                  <small class="d-block text-muted" style="font-size: 0.7rem;">{{ $t('exchange.customer_needs_desc') }}</small>
                                </div>
                              </div>
                            </label>
                          </div>
                        </div>
                      </div>
                      
                      <!-- 输入金额部分 -->
                      <div class="amount-input-section" :class="{'active-section': amountType === 'have'}">
                        <div class="mb-1">
                          <label :for="amountType === 'have' ? 'input_amount' : 'target_amount'" class="form-label h6 mb-1" style="font-size: 0.875rem;">
                            <span v-if="amountType === 'have'" class="text-primary d-flex align-items-center">
                              <font-awesome-icon :icon="['fas', 'arrow-right']" class="me-2" />
                              <template v-if="exchangeMode === 'buy_foreign'">
                                {{ $t('exchange.customer_payment') }} {{ baseCurrencyName }}
                              </template>
                              <template v-else>
                                {{ $t('exchange.customer_payment') }} {{ foreignCurrencyName || '?' }}
                              </template>
                              <span class="badge bg-light text-primary ms-2" style="font-size: 0.65rem;">{{ $t('exchange.paid_amount') }}</span>
                            </span>
                            <span v-else class="text-muted d-flex align-items-center">
                              <template v-if="exchangeMode === 'buy_foreign'">
                                {{ $t('exchange.customer_payment') }} {{ baseCurrencyName }}
                              </template>
                              <template v-else>
                                {{ $t('exchange.customer_payment') }} {{ foreignCurrencyName || '?' }}
                              </template>
                              <span class="badge bg-light text-muted ms-2" style="font-size: 0.65rem;">{{ $t('exchange.calculation_result') }}</span>
                            </span>
                          </label>
                          <div class="input-group input-group-sm">
                            <span class="input-group-text flag-container" :class="{'active-currency': amountType === 'have'}">
                              <CurrencyFlag 
                                :code="inputUnitCode || 'CNY'"
                                :custom-filename="getCurrencyCustomFlag(inputUnitCode || 'CNY')"
                                :margin-end="false"
                                :class="{'currency-flag-large': amountType === 'have', 'currency-flag-medium': amountType !== 'have'}"
                              />
                            </span>
                            <input 
                              :id="amountType === 'have' ? 'input_amount' : 'target_amount'"
                              type="number" 
                              class="form-control form-control-sm" 
                              :class="{'active-input': amountType === 'have'}"
                              :placeholder="amountType === 'have' ? $t('exchange.customer_pay_placeholder') : $t('exchange.calculated_payment_placeholder')"
                              :value="inputAmount"
                              @input="handleAmountInput($event, true)"
                              step="0.01"
                              min="0"
                              :readonly="amountType === 'want'"
                            />
                          </div>
                        </div>
                      </div>

                      <!-- 目标金额部分 -->
                      <div class="amount-input-section" :class="{'active-section': amountType === 'want'}">
                        <div class="mb-1">
                          <label :for="amountType === 'have' ? 'target_amount' : 'input_amount'" class="form-label h6 mb-1" style="font-size: 0.875rem;">
                            <span v-if="amountType === 'want'" class="text-primary d-flex align-items-center">
                              <i class="fas fa-arrow-right me-2"></i>
                              <template v-if="exchangeMode === 'buy_foreign'">
                                {{ $t('exchange.customer_needs') }} {{ foreignCurrencyName || '?' }}
                              </template>
                              <template v-else>
                                {{ $t('exchange.customer_needs') }} {{ baseCurrencyName }}
                              </template>
                              <span class="badge bg-light text-primary ms-2" style="font-size: 0.65rem;">{{ $t('exchange.target_amount') }}</span>
                            </span>
                            <span v-else class="text-muted d-flex align-items-center">
                              <template v-if="exchangeMode === 'buy_foreign'">
                                {{ amountType === 'have' ? $t('exchange.customer_gets') : $t('exchange.customer_needs') }} {{ foreignCurrencyName || '?' }}
                              </template>
                              <template v-else>
                                {{ amountType === 'have' ? $t('exchange.customer_gets') : $t('exchange.customer_needs') }} {{ baseCurrencyName }}
                              </template>
                              <span class="badge bg-light text-muted ms-2" style="font-size: 0.65rem;">{{ $t('exchange.calculation_result') }}</span>
                            </span>
                          </label>
                          <div class="input-group input-group-sm">
                            <span class="input-group-text flag-container" :class="{'active-currency': amountType === 'want'}">
                              <CurrencyFlag 
                                v-if="targetUnitCode"
                                :code="targetUnitCode"
                                :custom-filename="getCurrencyCustomFlag(targetUnitCode)"
                                :margin-end="false"
                                :class="{'currency-flag-large': amountType === 'want', 'currency-flag-medium': amountType !== 'want'}"
                              />
                              <span v-else class="text-muted">?</span>
                            </span>
                            <input 
                              :id="amountType === 'have' ? 'target_amount' : 'input_amount'"
                              type="number" 
                              class="form-control form-control-sm"
                              :class="{'active-input': amountType === 'want'}"
                              :placeholder="amountType === 'want' ? $t('exchange.customer_receive_placeholder') : $t('exchange.calculated_exchange_placeholder')"
                              :value="targetAmount"
                              @input="handleAmountInput($event, false)"
                              step="0.01"
                              min="0"
                              :readonly="amountType === 'have'"
                            />
                          </div>
                        </div>
                      </div>
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
                        <button class="btn btn-secondary btn-sm" @click="calculateExchange">
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
                  
                  <div class="mb-4">
                    <div class="mb-3">
                      <label for="customer_name" class="form-label">{{ $t('exchange.customer_name') }}</label>
                      <input type="text" id="customer_name" class="form-control" v-model="customerName" />
                    </div>
                    
                    <div class="mb-3">
                      <label for="customer_id" class="form-label">{{ $t('exchange.customer_id') }}</label>
                      <input type="text" id="customer_id" class="form-control" v-model="customerId" />
                    <div class="mb-3">
                      <label for="customer_address" class="form-label">{{ ('exchange.customer_address') }}</label>
                      <textarea id="customer_address" class="form-control" rows="2"
                        :placeholder="('exchange.enter_customer_address')" v-model="customerAddress"></textarea>
                    </div>
                    </div>
                    
                    <!-- 新增备注输入 -->
                    <div class="mb-3">
                      <label for="customer_remarks" class="form-label">{{ $t('exchange.remarks') }}</label>
                      <textarea 
                        id="customer_remarks" 
                        class="form-control" 
                        v-model="customerRemarks" 
                        rows="3"
                        :placeholder="$t('exchange.remarks_placeholder')"
                      ></textarea>
                    </div>
                  </div>
                  
                  <div class="d-flex justify-content-center">
                    <button class="btn btn-secondary me-2" @click="handleCancel">
                      <font-awesome-icon :icon="['fas', 'times']" class="me-1" /> {{ $t('exchange.cancel') }}
                    </button>
                    <button
                      class="btn btn-success"
                      @click="handleConfirm"
                      :disabled="disableExchange || !canConfirm"
                    >
                      <font-awesome-icon :icon="['fas', 'check']" class="me-1" /> {{ $t('exchange.confirm') }}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 右侧：信息显示 -->
          <div class="col-md-4">
            <!-- 本币信息 -->
            <div class="card mb-4">
              <div class="card-body">
                <div class="d-flex align-items-center">
                  <label class="me-2 h5 mb-0">{{ $t('exchange.base_currency') }}：</label>
                  <div class="base-currency-display d-flex align-items-center">
                    <CurrencyFlag :code="baseCurrency || 'CNY'" :custom-filename="getCurrencyCustomFlag(baseCurrency || 'CNY')" class="me-2 base-currency-flag" />
                    <span class="base-currency-text" v-if="baseCurrencyName">{{ baseCurrencyName }}({{ baseCurrency }})</span>
                    <span class="base-currency-text" v-else>({{ baseCurrency }})</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 今日汇率 -->
            <div class="card">
              <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="mb-0">{{ $t('exchange.today_rates') }}</h5>
                <div class="rate-search-box">
                  <input 
                    type="text" 
                    class="form-control form-control-sm" 
                    v-model="rateSearchKeyword"
                    :placeholder="$t('exchange.search_currency')"
                    style="width: 120px; font-size: 0.8rem;"
                  />
                </div>
              </div>
              <div class="card-body">
                <div class="table-responsive">
                  <table class="table table-sm table-striped">
                    <thead>
                      <tr>
                        <th>{{ $t('exchange.currency') }}</th>
                        <th>{{ $t('exchange.buy_rate') }}</th>
                        <th>{{ $t('exchange.sell_rate') }}</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="rate in filteredRates" :key="rate.currency">
                        <td>
                          <div class="d-flex align-items-center">
                            <CurrencyFlag 
                              :code="rate.currency"
                              :custom-filename="getCurrencyCustomFlag(rate.currency)"
                              class="me-2"
                            />
                            <span>{{ rate.currency }}</span>
                          </div>
                        </td>
                        <td>{{ formatRate(rate.buyRate) }}</td>
                        <td>{{ formatRate(rate.sellRate) }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 交易成功提示 - 使用模态框 -->
        <div class="modal fade show" 
             v-if="transactionSuccess" 
             tabindex="-1" 
             style="display: block; background: rgba(0,0,0,0.5)"
             @click.self="closeTransaction">
          <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
              <div class="modal-header bg-success text-white">
                <h5 class="modal-title">{{ $t('exchange.transaction_success') }}</h5>
                <button type="button" class="btn-close btn-close-white" @click="closeTransaction"></button>
              </div>
              <div class="modal-body">
                <div id="printArea">
                  <div class="receipt-container">
                    <div class="text-center mb-2">
                      <h5 class="mb-1">{{ $t('exchange.exchange_receipt') }}</h5>
                      <div class="small mt-1" style="color: #666;">
                        {{ userInfo.branch_name }}({{ userInfo.branch_code }}) 
                        {{ exchangeMode === 'sell_foreign' ? $t('exchange.buy') : $t('exchange.sell') }}{{ lastValidatedData ? (exchangeMode === 'sell_foreign' ? getCurrencyDisplayName(lastValidatedData.fromCurrency) : getCurrencyDisplayName(lastValidatedData.toCurrency)) : getCurrencyDisplayName(foreignCurrency) }}
                      </div>
                    </div>
                    
                    <table class="receipt-table">
                      <tbody>
                        <tr>
                          <td width="35%">{{ $t('exchange.transaction_no') }}:</td>
                          <td>{{ transactionDetails.transaction_no }}</td>
                        </tr>
                        <tr>
                          <td>{{ $t('exchange.transaction_date') }}:</td>
                          <td>{{ formatReceiptTime(transactionDetails.transaction_date, transactionDetails.transaction_time) }}</td>
                        </tr>
                        <tr>
                          <td>{{ $t('exchange.transaction_amount') }}:</td>
                          <td>{{ lastValidatedData ? formatAmount(lastValidatedData.fromAmount) : '' }} {{ lastValidatedData ? getCurrencyDisplayName(lastValidatedData.fromCurrency) : '' }}</td>
                        </tr>
                        <tr>
                          <td>{{ $t('exchange.exchange_amount') }}:</td>
                          <td>{{ lastValidatedData ? formatAmount(lastValidatedData.toAmount) : '' }} {{ lastValidatedData ? getCurrencyDisplayName(lastValidatedData.toCurrency) : '' }}</td>
                        </tr>
                        <tr>
                          <td>{{ $t('exchange.exchange_rate') }}:</td>
                          <td>1 {{ getCurrencyDisplayName(lastValidatedData ? (exchangeMode === 'sell_foreign' ? lastValidatedData.fromCurrency : lastValidatedData.toCurrency) : foreignCurrency) }} = {{ lastValidatedData ? lastValidatedData.rate : '' }} {{ getCurrencyDisplayName(lastValidatedData ? (exchangeMode === 'sell_foreign' ? lastValidatedData.toCurrency : lastValidatedData.fromCurrency) : baseCurrency) }}</td>
                        </tr>
                        <tr>
                          <td>{{ $t('exchange.customer_name') }}:</td>
                          <td>{{ transactionDetails.customer_name }}</td>
                        </tr>
                        <tr v-if="transactionDetails.customer_id">
                          <td>{{ $t('exchange.customer_id') }}:</td>
                          <td>{{ transactionDetails.customer_id }}</td>
                        </tr>
                        <tr v-if="transactionDetails.purpose">
                          <td>{{ $t('exchange.transaction_purpose') }}:</td>
                          <td>{{ transactionDetails.purpose }}</td>
                        </tr>
                        <tr v-if="transactionDetails.remarks">
                          <td>{{ $t('exchange.remarks') }}:</td>
                          <td>{{ transactionDetails.remarks }}</td>
                        </tr>
                      </tbody>
                    </table>

                    <!-- 动态签名区域 -->
                    <div v-if="signatureSettings.signature_style !== 'none'" class="row g-2">
                      <!-- 单签名框 -->
                      <div v-if="signatureSettings.signature_style === 'single'" class="col-12">
                        <div class="signature-box text-center">
                          <div>{{ signatureSettings.single_label }}</div>
                          <div class="signature-line"></div>
                          <small v-if="signatureSettings.show_date_line">{{ $t('exchange.signature_date') }}:_____________</small>
                        </div>
                      </div>
                      
                      <!-- 双签名框 -->
                      <template v-else-if="signatureSettings.signature_style === 'double'">
                        <div class="col-6">
                          <div class="signature-box text-center">
                            <div>{{ signatureSettings.left_label }}</div>
                            <div class="signature-line"></div>
                            <small v-if="signatureSettings.show_date_line">{{ $t('exchange.signature_date') }}:_____________</small>
                          </div>
                        </div>
                        <div class="col-6">
                          <div class="signature-box text-center">
                            <div>{{ signatureSettings.right_label }}</div>
                            <div class="signature-line"></div>
                            <small v-if="signatureSettings.show_date_line">{{ $t('exchange.signature_date') }}:_____________</small>
                          </div>
                        </div>
                      </template>
                    </div>

                    <div class="notice-section">
                      <div class="small">{{ $t('exchange.receipt_note') }}</div>
                    </div>
                  </div>
                </div>
              </div>
              <div class="modal-footer">
                <button class="btn btn-secondary" @click="closeTransaction">{{ $t('common.close') }}</button>
                <button class="btn btn-primary" @click="printReceipt">
                  <i class="fas fa-print me-1"></i> {{ $t('common.print') }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <ReservationModal
      v-if="showReservationModal && reservationTransactionData"
      ref="reservationModal"
      :visible="showReservationModal"
      :report-type="activeTriggerReportType || 'AMLO-1-01'"
      :trigger-message="activeTriggerMessage"
      :transaction-data="reservationTransactionData"
      :allow-continue="currentTrigger?.allow_continue ?? false"
      @update:visible="value => showReservationModal = value"
      @submit="handleReservationSubmitted"
      @cancel="handleReservationCancelled"
    />

    <CustomerHistoryModal
      v-if="showCustomerHistory"
      ref="customerHistoryModal"
      :visible="showCustomerHistory"
      :customer-id="customerId"
      @update:visible="value => showCustomerHistory = value"
    />
  </div>
</template>

<script>
import CurrencyFlag from '@/components/CurrencyFlag.vue'
import CurrencySelect from '@/components/CurrencySelect.vue'
import CurrencyBalanceInfo from '@/components/CurrencyBalanceInfo.vue'
import ReservationModal from '@/components/exchange/ReservationModal.vue'
import CustomerHistoryModal from '@/components/exchange/CustomerHistoryModal.vue'
import standardExchangeLogic from './mixins/standardExchangeLogic'

export default {
  name: 'StandardExchangeView',
  components: {
    CurrencyFlag,
    CurrencySelect,
    CurrencyBalanceInfo,
    ReservationModal,
    CustomerHistoryModal
  },
  mixins: [standardExchangeLogic]
}
</script>

<style scoped>
.card {
  margin-bottom: 1rem;
}

.card-header {
  padding: 0.75rem 1rem;
}

.card-body {
  padding: 1rem;
}

.mb-4 {
  margin-bottom: 1rem !important;
}

.mb-3 {
  margin-bottom: 0.75rem !important;
}

.py-2 {
  padding-top: 0.375rem !important;
  padding-bottom: 0.375rem !important;
}

.py-3 {
  padding-top: 0.75rem !important;
  padding-bottom: 0.75rem !important;
}

.p-4 {
  padding: 1rem !important;
}

.alert {
  padding: 0.75rem 1rem;
  margin-bottom: 0.75rem;
}

.form-label {
  margin-bottom: 0.25rem;
}

.input-group {
  margin-bottom: 0.5rem;
}

.amount-input-section {
  margin-bottom: 0.75rem;
}

.gap-3 {
  gap: 0.75rem !important;
}

.mt-4 {
  margin-top: 1rem !important;
}

.active-card {
  border-color: var(--bs-primary);
  box-shadow: 0 0 0 1px var(--bs-primary);
}

.active-section {
  background-color: rgba(var(--bs-success-rgb), 0.15) !important; /* 修改：使用绿色背景，类似步骤数字圈 */
  padding: 1.25rem !important; /* 增加内边距，让区域更大 */
  border-radius: 0.75rem !important; /* 增加圆角 */
  border: 2px solid rgba(var(--bs-success-rgb), 0.3) !important; /* 添加绿色边框 */
  box-shadow: 0 4px 12px rgba(var(--bs-success-rgb), 0.2) !important; /* 添加绿色阴影 */
  transition: all 0.3s ease !important; /* 添加过渡效果 */
  transform: scale(1.02) !important; /* 轻微放大效果 */
}

.active-input {
  border-color: #dee2e6 !important; /* 移除高亮边框，使用默认颜色 */
  box-shadow: none !important; /* 移除阴影 */
  background-color: white !important; /* 使用白色背景 */
}

.active-currency {
  background-color: #f8f9fa !important; /* 使用默认背景色 */
  border-color: #dee2e6 !important; /* 使用默认边框色 */
  color: inherit !important; /* 使用默认文字色 */
}

.active-currency .currency-flag {
  filter: none !important; /* 移除阴影效果 */
}

/* 新增：余额检查相关样式 */
.balance-check-realtime {
  border: 1px solid #dee2e6;
  border-radius: 0.375rem;
  padding: 0.75rem;
  background-color: #f8f9fa;
  margin-top: 0.5rem;
}

.balance-check-after-calculation {
  border: 1px solid #dee2e6;
  border-radius: 0.375rem;
  padding: 0.75rem;
  background-color: #fff3cd;
}

.balance-check-realtime.text-success {
  background-color: #d1edff;
  border-color: #b6d7ff;
}

.balance-check-after-calculation.text-success {
  background-color: #d1f2eb;
  border-color: #a7e4c8;
}

.currency-flag {
  width: 1.25rem;
  height: 0.9375rem;
  border-radius: 0.125rem;
  transition: all 0.3s ease;
}

.currency-flag-large {
  width: 2rem !important;
  height: 1.5rem !important;
  border-radius: 0.25rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.currency-flag-medium {
  width: 1.5rem !important;
  height: 1.125rem !important;
  border-radius: 0.2rem;
}

.input-group-text {
  background-color: #f8f9fa;
  transition: all 0.3s ease;
  padding: 0.5rem 0.75rem;
}

.active-currency {
  background-color: rgba(var(--bs-primary-rgb), 0.1);
  border-color: var(--bs-primary);
}

.active-currency .currency-flag {
  filter: drop-shadow(0 0 2px rgba(var(--bs-primary-rgb), 0.3));
}

.input-group {
  margin-bottom: 0;
}

.input-group-text {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 3rem;
}

.base-currency-flag {
  width: 1.5rem;
  height: 1.125rem;
}

.table-responsive {
  margin: -0.5rem -1rem;
  padding: 0.5rem 1rem;
}

.table {
  margin-bottom: 0.5rem;
}

.table th,
.table td {
  padding: 0.375rem;
  vertical-align: middle;
}

.btn {
  padding: 0.375rem 0.75rem;
}

.btn-sm {
  padding: 0.25rem 0.5rem;
}

.receipt-container {
  padding: 1rem;
}

.receipt-table {
  width: 100%;
  margin-top: 0.75rem;
}

.receipt-table td {
  padding: 0.375rem 0;
}

.signature-box {
  border: 1px solid #dee2e6;
  border-radius: 4px;
  margin-top: 10px;
  padding: 8px;
  min-height: 50px;
}

.signature-line {
  height: 1px;
  background: #000;
  margin: 8px 0 4px;
}

@media (min-width: 768px) {
  .container {
    max-width: 1140px;
  }
  
  .card-body {
    min-height: auto;
  }
}

.amount-type-selector {
  margin-bottom: 1rem !important;
}

.amount-type-card {
  display: block;
  padding: 0.75rem !important;
  border: 1px solid #dee2e6;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: all 0.2s ease;
  min-height: 70px;
}

.amount-type-card:hover {
  border-color: var(--bs-primary);
  background-color: rgba(var(--bs-primary-rgb), 0.02);
}

.amount-type-card.active {
  border-color: var(--bs-primary);
  background-color: rgba(var(--bs-primary-rgb), 0.05);
  box-shadow: 0 0 0 1px var(--bs-primary);
}

.amount-type-content {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.amount-type-icon {
  width: 2rem !important;
  height: 2rem !important;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(var(--bs-primary-rgb), 0.1);
  border-radius: 50%;
  color: var(--bs-primary);
  font-size: 1rem;
  transition: all 0.3s ease;
}

.amount-input-section {
  margin-bottom: 0.5rem !important;
}

.gap-2 {
  gap: 0.5rem !important;
}

/* 响应式调整 */
@media (max-width: 767px) {
  .step-content {
    margin-left: 0;
    margin-top: 0.5rem;
  }
  
  .step-badge {
    width: 1.25rem;
    height: 1.25rem;
    font-size: 0.7rem;
    margin-right: 0.5rem;
  }
  
  .step-badge.completed {
    background-color: var(--bs-success);
    color: white;
  }
  
  .step-label {
    font-size: 0.8rem;
  }
  
  .amount-type-card {
    padding: 0.5rem !important;
    min-height: 60px;
  }
  
  .amount-type-icon {
    width: 1.5rem !important;
    height: 1.5rem !important;
    font-size: 0.875rem;
  }
  
  .currency-flag-large {
    width: 1.75rem !important;
    height: 1.3125rem !important;
  }
}

/* 新增：金额类型图标过渡效果 */
.amount-type-icon {
  transition: all 0.3s ease;
}

.amount-type-card.active .amount-type-icon {
  background-color: var(--bs-primary);
  color: white;
}

/* 新增：左侧操作指引样式 */
.exchange-guide-card {
  box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
  border: none;
}

.exchange-steps {
  padding: 0;
}

.step-item {
  display: flex;
  align-items: center;
  padding: 0.75rem 0.5rem;
  margin-bottom: 0.5rem;
  border-radius: 0.375rem;
  transition: all 0.3s ease;
  border-left: 3px solid transparent;
}

.step-item.active {
  background-color: rgba(var(--bs-primary-rgb), 0.1);
  border-left-color: var(--bs-primary);
}

.step-item.completed {
  background-color: rgba(var(--bs-success-rgb), 0.1);
  border-left-color: var(--bs-success);
}

.step-number {
  width: 1.5rem;
  height: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #e9ecef;
  color: #6c757d;
  border-radius: 50%;
  font-size: 0.75rem;
  font-weight: 600;
  margin-right: 0.75rem;
  transition: all 0.3s ease;
}

.step-item.active .step-number {
  background-color: var(--bs-primary);
  color: white;
}

.step-item.completed .step-number {
  background-color: var(--bs-success);
  color: white;
}

.step-text {
  font-size: 0.875rem;
  font-weight: 500;
  color: #495057;
}

.step-item.active .step-text {
  color: var(--bs-primary);
  font-weight: 600;
}

.step-item.completed .step-text {
  color: var(--bs-success);
}

/* 新增：中间区域步骤样式 */
.step-section {
  margin-bottom: 1rem !important;
  padding-bottom: 0.75rem !important;
  border-bottom: 1px solid #e9ecef;
}

.step-section:last-child {
  border-bottom: none;
}

.step-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.75rem;
  height: 1.75rem;
  background-color: var(--bs-primary);
  color: white;
  border-radius: 50%;
  font-size: 0.875rem;
  font-weight: 600;
  margin-right: 0.75rem;
  transition: all 0.3s ease;
}

.step-badge.completed {
  background-color: var(--bs-success);
  color: white;
}

.step-label {
  font-size: 1rem;
  font-weight: 600;
  color: #495057;
  margin: 0;
}

.step-content {
  margin-left: 2.5rem;
  margin-top: 0.75rem;
}

/* 新增：用途选择样式 */
.purpose-hint {
  padding: 0.5rem;
  background-color: #f8f9fa;
  border-radius: 0.375rem;
  border-left: 3px solid #17a2b8;
}

/* 新增：用途选择优化样式 */
.purpose-select {
  min-width: 180px;
  max-width: 200px;
  font-size: 0.875rem;
}

.purpose-info-container {
  min-width: 0; /* 允许flex item收缩 */
  flex: 1;
  align-self: flex-start;
}

.purpose-hint-inline {
  display: block;
  margin-bottom: 0.25rem;
}

.purpose-warning-inline {
  display: block;
  margin-top: 0.25rem;
}

/* 确保提示信息能够正常换行显示 */
.purpose-hint-inline small,
.purpose-warning-inline small {
  white-space: normal;
  word-wrap: break-word;
  word-break: break-word;
  line-height: 1.3;
  display: block;
  margin-bottom: 0.25rem;
}

/* 新增：响应式调整 */
@media (max-width: 767px) {
  .exchange-guide-card {
    margin-bottom: 1rem;
  }
  
  .step-content {
    margin-left: 0;
    margin-top: 0.5rem;
  }
  
  .step-badge {
    width: 1.5rem;
    height: 1.5rem;
    font-size: 0.75rem;
    margin-right: 0.5rem;
  }
  
  .step-label {
    font-size: 0.875rem;
  }
  
  /* 用途选择响应式调整 */
  .purpose-select {
    min-width: 150px;
    max-width: 170px;
  }
  
  .purpose-info-container {
    margin-top: 0.5rem;
    margin-left: 0;
  }
  
  .step-section .d-flex {
    flex-direction: column;
    align-items: flex-start !important;
  }
  
  .step-section .d-flex .step-badge {
    align-self: flex-start;
  }
}

/* 修复可能的编码问题样式 */
.currency-flag img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 新增：让国旗图标填满输入框前缀区域，控制高度，无白色边距 */
.input-group-text.flag-container {
  padding: 0 !important;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 3rem;
  height: 2.25rem; /* 固定高度，防止被撑开 */
  overflow: hidden;
  border-radius: 0.375rem 0 0 0.375rem;
}

.input-group-text.flag-container .currency-flag {
  margin: 0 !important;
  width: 2.5rem !important;
  height: 1.875rem !important; /* 按比例缩小 */
  border-radius: 0 !important;
  border: none !important;
  box-shadow: none !important;
}

.input-group-text.flag-container .currency-flag img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 0 !important;
}

/* 确保输入框组合保持正常高度 */
.input-group-sm .form-control {
  height: 2.25rem;
}

.input-group-sm .input-group-text {
  height: 2.25rem;
}

/* 新增：语音提示样式 */
.exchange-prompt {
  position: relative;
}

.prompt-speaker {
  animation: pulse-speaker 2s infinite;
  transition: all 0.3s ease;
}

.prompt-speaker:hover {
  transform: scale(1.1);
  color: var(--bs-success) !important;
}

@keyframes pulse-speaker {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
  100% {
    opacity: 1;
  }
}

/* 新增：上一笔交易信息样式 */
.last-transaction-card {
  border: 1px solid #17a2b8;
  box-shadow: 0 2px 4px rgba(23, 162, 184, 0.1);
}

.last-transaction-info {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.transaction-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.2rem 0;
  border-bottom: 1px solid #f0f0f0;
}

.transaction-item:last-child {
  border-bottom: none;
}

.transaction-item .label {
  font-size: 0.75rem;
  color: #6c757d;
  font-weight: 500;
  flex: 0 0 auto;
  margin-right: 0.5rem;
}

.transaction-item .value {
  font-size: 0.75rem;
  color: #333;
  font-weight: 600;
  text-align: right;
  flex: 1;
}

/* 单据号特殊样式 */
.transaction-item .value.transaction-no {
  color: #007bff;
  font-family: 'Courier New', monospace;
  font-weight: 700;
  font-size: 0.8rem;
  background-color: #f8f9fa;
  padding: 0.1rem 0.3rem;
  border-radius: 0.2rem;
  border: 1px solid #dee2e6;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .last-transaction-card {
    margin-bottom: 1rem;
  }
  
  .transaction-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.2rem;
  }
  
  .transaction-item .value {
    text-align: left;
  }
}

/* 新增：阈值警告专用样式 */
.threshold-warning {
  background-color: #d1edff !important; /* 灰绿色背景 */
  border: 1px solid #b6d7ff !important;
  border-radius: 0.375rem !important;
  padding: 0.5rem 0.75rem !important;
  margin-bottom: 0.5rem !important;
  color: #0c5460 !important;
  font-size: 0.875rem !important;
}

.threshold-warning i {
  color: #856404 !important;
}

/* 保留原有的选择卡片样式，不做特殊修改 */

</style>

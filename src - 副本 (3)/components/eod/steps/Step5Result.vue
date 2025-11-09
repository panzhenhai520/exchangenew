<template>
  <div class="step-content">
    <!-- 紧凑的标题行 -->
    <div class="compact-header mb-3">
      <h5 class="title">{{ $t('eod.step5.title') }}</h5>
      <small class="text-muted ms-2">{{ $t('eod.step5.description') }}</small>
    </div>

    <!-- 核对结果概览和收入统计并排显示 -->
    <div class="row mb-3">
      <!-- 左侧：核对结果概览 -->
      <div class="col-md-6">
        <div class="card h-100">
          <div class="card-header py-2">
            <h6 class="mb-0">
              <font-awesome-icon :icon="['fas', 'check-circle']" class="me-2 text-success" />
              {{ t('eod.step5.verification_overview') }}
            </h6>
          </div>
          <div class="card-body py-2">
            <div class="row text-center">
              <div class="col-3">
                <div class="stat-number text-primary">{{ matchedCount + mismatchedCount }}</div>
                <div class="stat-label">{{ t('eod.step4.total_currencies') }}</div>
              </div>
              <div class="col-3">
                <div class="stat-number text-success">{{ matchedCount }}</div>
                <div class="stat-label">{{ t('eod.step4.matched_currencies') }}</div>
              </div>
              <div class="col-3">
                <div class="stat-number text-danger">{{ mismatchedCount }}</div>
                <div class="stat-label">{{ t('eod.step4.mismatched_currencies') }}</div>
              </div>
              <div class="col-3">
                <div class="stat-number text-info">{{ calculateMatchRate() }}%</div>
                <div class="stat-label">{{ t('eod.step5.match_rate') }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：收入统计 -->
      <div class="col-md-6">
        <div class="card h-100">
          <div class="card-header py-2">
            <h6 class="mb-0">
              <font-awesome-icon :icon="['fas', 'chart-bar']" class="me-2 text-primary" />
              {{ t('eod.income_statistics_title') }}
            </h6>
          </div>
          <div class="card-body py-2">
            <div class="row text-center">
              <div class="col-4">
                <div class="stat-number text-success">{{ formatAmount(totalIncome) }}</div>
                <div class="stat-label">{{ t('eod.income') }}</div>
              </div>
              <div class="col-4">
                <div class="stat-number text-info">{{ formatAmount(totalSpreadIncome) }}</div>
                <div class="stat-label">{{ t('eod.spread_income') }}</div>
              </div>
              <div class="col-4">
                <div class="stat-number text-primary">{{ incomeReports.length }}</div>
                <div class="stat-label">{{ t('eod.currency_count') }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 强制继续后的提示 -->
    <div v-if="isForceContinued" class="alert alert-warning py-2 mb-3">
      <div class="d-flex align-items-center">
        <div>
          <font-awesome-icon :icon="['fas', 'exclamation-triangle']" class="me-2" />
          <strong>{{ t("eod.step5.force_continued_title") }}</strong>
          <span class="ms-2 text-muted">{{ t("eod.step5.force_continued_message") }}</span>
        </div>
      </div>
    </div>

    <!-- 余额核对一致的情况 -->
    <div v-if="allMatched && !shouldShowIncomeStats" class="alert alert-success py-2">
      <div class="d-flex align-items-center justify-content-between">
        <div>
          <font-awesome-icon :icon="['fas', 'check-circle']" class="me-2" />
          <strong>{{ t("eod.step5.balance_verification_passed") }}</strong>
          <span class="ms-2 text-muted">{{ t("eod.step5.continue_eod_process") }}</span>
        </div>
        <button 
          class="btn btn-success btn-sm"
          @click="continueEOD"
          :disabled="loading || isProcessing"
        >
          <span v-if="isProcessing">
            <span class="spinner-border spinner-border-sm me-2" role="status"></span>
            {{ t("eod.step5.processing") }}
          </span>
          <span v-else>
            <font-awesome-icon :icon="['fas', 'arrow-right']" class="me-2" />
            {{ t('eod.step5.generate_income_stats') }}
          </span>
        </button>
      </div>
    </div>
    
    <!-- {{ $t("eod.step5.income_stats_confirmed") }}的情况 -->
    <div v-else-if="allMatched && incomeStatsConfirmed" class="alert alert-info py-2">
      <div class="d-flex align-items-center">
        <div>
          <font-awesome-icon :icon="['fas', 'check-circle']" class="me-2" />
          <strong>{{ t("eod.step5.income_stats_confirmed") }}</strong>
          <span class="ms-2 text-muted">{{ t("eod.step5.continue_eod_process") }}</span>
        </div>
      </div>
    </div>
    
    <!-- {{ $t("eod.step5.balance_verification_passed") }}且显示收入统计 -->
    <div v-else-if="allMatched && shouldShowIncomeStats" class="alert alert-success py-2">
      <div class="d-flex align-items-center">
        <div>
          <font-awesome-icon :icon="['fas', 'check-circle']" class="me-2" />
          <strong>{{ t("eod.step5.balance_verification_passed") }}</strong>
          <span class="ms-2 text-muted">{{ t("eod.step5.complete_income_stats_first") }}。</span>
        </div>
      </div>
    </div>

    <!-- 收入统计区域 -->
    <div v-if="shouldShowIncomeStats || isForceContinued" class="income-stats-section">
      <!-- 收入统计生成区域 -->
      <div v-if="!incomeStatsGenerated" class="text-center py-3">
        <div v-if="isGeneratingStats">
          <div class="spinner-border text-primary mb-3" role="status">
            <span class="visually-hidden">{{ t('eod.step5.generating') }}</span>
          </div>
          <p class="text-muted mb-0">{{ t("eod.step5.generating_income_stats_message") }}</p>
        </div>
        <div v-else-if="!props.autoGenerateIncomeStats">
          <font-awesome-icon :icon="['fas', 'chart-bar']" size="3x" class="text-muted mb-3" />
          <p class="text-muted mb-3">{{ t("eod.step5.click_to_generate_income_stats") }}</p>
          <button 
            class="btn btn-primary"
            @click="generateIncomeStats"
            :disabled="loading"
          >
            <font-awesome-icon :icon="['fas', 'calculator']" class="me-2" />
            {{ t('eod.step5.generate_income_stats') }}
          </button>
        </div>
        <div v-else>
          <div class="spinner-border text-primary mb-3" role="status">
            <span class="visually-hidden">{{ t('eod.step5.auto_generating') }}</span>
          </div>
          <p class="text-muted mb-0">{{ t("eod.step5.auto_generating_income_stats_message") }}</p>
        </div>
      </div>

      <!-- 收入报表 - 采用展开/收起样式 -->
      <div v-if="incomeStatsGenerated" class="reports-section">
        <div class="card">
          <div class="card-header py-2 cursor-pointer" 
               @click="toggleIncomeReports">
            <div class="d-flex align-items-center justify-content-between">
              <h6 class="mb-0">
                <font-awesome-icon :icon="['fas', 'coins']" class="me-2 text-warning" />
                {{ t("eod.step5.income_report") }}
                <span class="badge bg-primary ms-2">{{ incomeReports.length }}{{ t("eod.step5.currency_types") }}</span>
              </h6>
              <div class="d-flex align-items-center">
                <span class="text-success me-3">
                  {{ t("eod.step5.total_income") }}: <strong>{{ formatAmount(totalIncome) }}</strong>
                </span>
                <font-awesome-icon 
                  :icon="['fas', 'chevron-down']" 
                  class="transition-transform"
                  :class="{ 'rotate-180': showIncomeReports }"
                />
              </div>
            </div>
          </div>
          <div v-if="showIncomeReports" class="card-body p-0">
            <div class="table-responsive">
              <table class="table table-sm table-hover mb-0">
                <thead class="table-light">
                  <tr>
                    <th>{{ t("eod.step5.currency") }}</th>
                    <th>{{ t("eod.step5.buy_volume") }}</th>
                    <th>{{ t("eod.step5.sell_volume") }}</th>
                    <th>{{ t("eod.step5.reversal_volume") }}</th>
                    <th>{{ t("eod.step5.net_income") }}</th>
                    <th>{{ t("eod.step5.spread_income") }}</th>
                  </tr>
                </thead>
                <tbody>
                  <template v-for="report in foreignIncomeReports" :key="report.currency_code">
                    <tr class="currency-row" 
                        @click="toggleCurrencyDetails(report.currency_code)"
                        :class="{ 'expanded': expandedCurrency === report.currency_code }">
                      <td>
                        <div class="currency-info-cell">
                          <CurrencyFlag 
                            :code="report.currency_code || 'USD'" 
                            :custom-filename="report.custom_flag_filename"
                            :width="20" 
                            :height="14" 
                            class="currency-flag"
                          />
                          <div class="currency-details">
                            <!-- 【修复】币种名称放到币种代码的后面，节约行高 -->
                            <span class="currency-code">{{ report.currency_code }}</span>
                            <span class="currency-name text-muted ms-1">{{ getCurrencyNameTranslated(report.currency_code) }}</span>
                          </div>
                          <i class="fas fa-chevron-down detail-arrow" 
                             :class="{ 'rotated': expandedCurrency === report.currency_code }"></i>
                        </div>
                      </td>
                      <td>{{ formatAmount(report.buy_amount || 0) }}</td>
                      <td>{{ formatAmount(report.sell_amount || 0) }}</td>
                      <td :class="getReversalAmountClass(report.reversal_amount || 0)">{{ formatDifference(report.reversal_amount || 0) }}</td>
                      <td class="text-success">{{ formatAmount(report.income || 0) }}</td>
                      <td class="text-info">{{ formatAmount(report.spread_income || 0) }}</td>
                    </tr>
                    <!-- 明细展开区域 -->
                    <tr v-if="expandedCurrency === report.currency_code" class="details-row">
                      <td colspan="6" class="details-cell">
                        <div class="transaction-details-compact">
                          <div class="details-header-compact">
                            <div class="details-title">
                              <CurrencyFlag 
                                :code="report.currency_code || 'USD'"
                                :custom-filename="report.custom_flag_filename"
                                :width="18"
                                :height="12"
                                class="detail-flag"
                              />
                              <span class="currency-title">{{ report.currency_code }} {{ t('eod.transaction_details') }}</span>
                              <button class="btn-collapse" @click="expandedCurrency = null">
                                <i class="fas fa-times"></i>
                              </button>
                            </div>
                            <div class="details-summary-compact">
                              <span class="summary-compact">{{ t('eod.transaction_count') }}: {{ getPaginationData(report.currency_code)?.totalCount || 0 }}</span>
                              <span class="summary-compact">{{ t('eod.foreign_total') }}: <span :class="getForeignTotalClass(report.currency_code)">{{ formatForeignTotal(report.currency_code) }}</span></span>
                              <span class="summary-compact">{{ t('eod.local_total') }}: {{ formatLocalTotal(report.currency_code) }}</span>
                              <span class="summary-compact" v-if="currencyDetails[report.currency_code]?.time_range">
                                {{ t('eod.statistics_time_range') }}: {{ formatTimeRange(currencyDetails[report.currency_code].time_range.start_time, currencyDetails[report.currency_code].time_range.end_time) }}
                              </span>
                              
                              <!-- 动态勾选计算区域 -->
                              <div v-if="hasSelectedTransactions" class="selected-summary-compact">
                                <div class="selected-divider"></div>
                                <span class="selected-label">{{ t("eod.step5.selected_transactions") }}:</span>
                                <span class="selected-count">{{ selectedCount }}{{ t('dashboard.transactions_unit') }}</span>
                                <span class="selected-foreign">{{ t('eod.step5.foreign_currency_short') }} <span :class="selectedForeignTotal >= 0 ? 'text-success' : 'text-danger'">{{ formatSignedAmount(selectedForeignTotal) }}</span></span>
                                <span class="selected-local">{{ t('eod.step5.local_currency_short') }} {{ formatAmount(selectedLocalTotal) }}</span>
                                <button class="btn-clear-selections" @click="clearAllSelections" :title="t('common.clear_selection')">
                                  <i class="fas fa-times"></i>
                                </button>
                              </div>
                            </div>
                          </div>
                          
                          <div class="transactions-container-compact" v-if="currencyDetails[report.currency_code]">
                            <!-- 全选控制 -->
                            <div class="transaction-control-row">
                              <label class="checkbox-container">
                                <input type="checkbox" 
                                       :checked="isCurrentPageAllSelected(report.currency_code)"
                                       @change="toggleAllCurrentPage(report.currency_code)">
                                <span class="checkmark"></span>
                                <span class="checkbox-label text-nowrap">
                                  {{ isCurrentPageAllSelected(report.currency_code) ? t("eod.step5.deselect_all") : t("eod.step5.select_all_current_page") }}
                                </span>
                              </label>
                            </div>
                            
                            <div class="transaction-row-compact" 
                                 v-for="transaction in getCurrentPageTransactions(report.currency_code)" 
                                 :key="transaction.transaction_no"
                                 :class="{ 'transaction-selected': isTransactionSelected(report.currency_code, transaction) }">
                              <div class="transaction-line">
                                <label class="checkbox-container">
                                  <input type="checkbox" 
                                         :checked="isTransactionSelected(report.currency_code, transaction)"
                                         @change="toggleTransactionSelection(report.currency_code, transaction)">
                                  <span class="checkmark"></span>
                                </label>
                                <span class="tx-no">{{ getShortTransactionNo(transaction.transaction_no) }}</span>
                                <span class="tx-time">{{ getCompactDateTime(transaction.created_at) }}</span>
                                <span class="tx-separator">|</span>
                                <span class="tx-type" :class="getTransactionTypeClass(transaction?.type)">
                                  {{ getTransactionTypeText(transaction?.type) }}:
                                </span>
                                <span class="tx-foreign" :class="getTransactionAmountClass(transaction.amount)">
                                  {{ formatSignedForeignAmount(transaction.amount) }} {{ transaction.currency_code || t('common.unknown') }}
                                </span>
                                <span class="tx-rate">× {{ formatRate(transaction.rate) }}</span>
                                <span class="tx-equals">=</span>
                                <span class="tx-local">{{ formatAmount(transaction.local_amount) }}</span>
                                <span class="tx-separator">|</span>
                                <span class="tx-customer">{{ transaction.customer_name || t('common.customer') }}</span>
                              </div>
                            </div>
                            
                            <!-- 分页控制 -->
                            <div class="pagination-controls" v-if="needsPagination(report.currency_code)">
                              <div class="pagination-info">
                                {{ t('eod.page_info', { 
                                  current: getCurrentPage(report.currency_code),
                                  total: getTotalPages(report.currency_code),
                                  count: getTotalTransactions(report.currency_code)
                                }) }}
                              </div>
                              <div class="pagination-buttons">
                                <button class="btn-page" 
                                        @click="prevPage(report.currency_code)"
                                        :disabled="getCurrentPage(report.currency_code) === 1">
                                  <i class="fas fa-chevron-left"></i>
                                </button>
                                <button class="btn-page" 
                                        @click="nextPage(report.currency_code)"
                                        :disabled="getCurrentPage(report.currency_code) === getTotalPages(report.currency_code)">
                                  <i class="fas fa-chevron-right"></i>
                                </button>
                              </div>
                            </div>
                            
                            <!-- 页面小计/总计 -->
                            <div class="subtotal-row">
                              <div class="subtotal-content">
                                <span v-if="needsPagination(report.currency_code) && getCurrentPage(report.currency_code) < getTotalPages(report.currency_code)">
                                  {{ t('eod.page_subtotal') }}: {{ t('eod.foreign_currency') }} <span :class="getForeignPageTotalClass(report.currency_code)">{{ formatForeignPageTotal(report.currency_code) }}</span>，
                                  {{ t('eod.local_currency') }} {{ formatLocalPageTotal(report.currency_code) }}
                                </span>
                                <span v-else>
                                  <strong>{{ t('eod.total') }}: {{ t('eod.foreign_currency') }}  <span :class="getForeignTotalClass(report.currency_code)">{{ formatForeignTotal(report.currency_code) }}</span>，
                                  {{ t('eod.local_currency') }}  {{ formatLocalTotal(report.currency_code) }}</strong>
                                </span>
                              </div>
                            </div>
                          </div>
                          
                          <div class="loading-details" v-else-if="loadingDetails">
                            <i class="fas fa-spinner fa-spin"></i>
                            {{ t('eod.loading_details') }} 
                          </div>
                        </div>
                      </td>
                    </tr>
                  </template>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- 外币库存报表 - 采用展开/收起样式 -->
        <div class="card mt-3">
          <div class="card-header py-2 cursor-pointer" 
               @click="toggleStockReports">
            <div class="d-flex align-items-center justify-content-between">
              <h6 class="mb-0">
                <font-awesome-icon :icon="['fas', 'warehouse']" class="me-2 text-primary" />
                {{ t("eod.step5.foreign_stock_report") }}
                <span class="badge bg-secondary ms-2">{{ stockReports.length }}{{ t("eod.step5.currency_types") }}</span>
              </h6>
              <font-awesome-icon 
                :icon="['fas', 'chevron-down']" 
                class="transition-transform"
                :class="{ 'rotate-180': showStockReports }"
              />
            </div>
          </div>
          <div v-if="showStockReports" class="card-body p-0">
            <div class="table-responsive">
              <table class="table table-sm table-hover mb-0">
                <thead class="table-light">
                  <tr>
                    <th>{{ t("eod.step5.currency") }}</th>
                    <th>{{ t("eod.step5.opening_balance") }}</th>
                    <th>{{ t("eod.step5.change_amount") }}</th>
                    <th>{{ t("eod.step5.current_balance") }}</th>
                    <th>{{ t("eod.step5.status") }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="report in foreignStockReports" :key="report.currency_code">
                    <td>
                      <div class="d-flex align-items-center">
                        <CurrencyFlag 
                          :code="report.currency_code || 'USD'" 
                          :custom-filename="report.custom_flag_filename"
                          :width="20" 
                          :height="14" 
                          class="me-2"
                        />
                        <div>
                          <!-- 【修复】币种名称放到币种代码的后面，节约行高 -->
                          <span class="currency-code">{{ report.currency_code }}</span>
                          <span class="currency-name small text-muted ms-1">{{ getCurrencyNameTranslated(report.currency_code) }}</span>
                        </div>
                      </div>
                    </td>
                    <td>{{ formatAmount(report.opening_balance || 0) }}</td>
                    <td :class="getBalanceChangeClass(report.change_amount || 0)">
                      {{ formatDifference(report.change_amount || 0) }}
                    </td>
                    <td>{{ formatAmount(report.current_balance || 0) }}</td>
                    <td>
                      <span :class="getStockStatusClass(report.current_balance || 0)">
                        {{ t('eod.step5.balance_normal') }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- 本币库存报表 -->
        <div class="card mt-3">
          <div class="card-header py-2 cursor-pointer" 
               @click="toggleBaseCurrencyReports">
            <div class="d-flex justify-content-between align-items-center">
              <span class="fw-semibold text-success" 
                    @click="toggleBaseCurrencyReports">
                <font-awesome-icon :icon="['fas', 'coins']" class="me-2" />
                {{ t("eod.step5.base_currency_report") }}
                <span class="badge bg-success ms-2">{{ t("eod.step5.base_currency") }}</span>
                <!-- 【调试】显示实际本币代码 -->
                <small class="text-muted ms-2">({{ getBaseCurrencyCode() || $t('common.unknown') }})</small>
              </span>
              <font-awesome-icon 
                :icon="['fas', 'chevron-down']" 
                :class="{ 'rotate-180': showBaseCurrencyReports }"
                class="transition-transform cursor-pointer"
                @click="toggleBaseCurrencyReports"
              />
            </div>
          </div>
          <div v-if="showBaseCurrencyReports" class="card-body p-0">
            <div class="table-responsive">
              <table class="table table-sm table-hover mb-0">
                <thead class="table-light">
                  <tr>
                    <th>{{ t("eod.step5.currency") }}</th>
                    <th>{{ t("eod.step5.opening_balance") }}</th>
                    <th>{{ t("eod.step5.income_amount") }}</th>
                    <th>{{ t("eod.step5.expense_amount") }}</th>
                    <th>{{ t("eod.step5.reversal_amount") }}</th>
                    <th>{{ t("eod.step5.adjust_balance_amount") }}</th>
                    <th>{{ t("eod.step5.cash_out_amount") }}</th>
                    <th>{{ t("eod.step5.current_balance") }}</th>
                    <th>{{ t("eod.step5.status") }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="baseCurrencyData" 
                      class="currency-row cursor-pointer"
                      @click="toggleBaseCurrencyDetails(baseCurrencyData.currency_code)"
                      :class="{ 'expanded': isBaseCurrencyExpanded }">
                    <td>
                      <div class="d-flex align-items-center">
                        <CurrencyFlag 
                          :code="baseCurrencyData.currency_code || getBaseCurrencyCode() || 'THB'" 
                          :custom-filename="baseCurrencyData.custom_flag_filename"
                          :width="20" 
                          :height="14" 
                          class="me-2"
                        />
                        <div>
                          <!-- 【修复】显示正确的本币代码和名称 -->
                          <span class="currency-code">{{ getBaseCurrencyCode() || baseCurrencyData.currency_code || 'THB' }}</span>
                          <span class="currency-name small text-muted ms-1">{{ getCurrencyNameTranslated(getBaseCurrencyCode() || baseCurrencyData.currency_code || 'THB') }} ({{ t('eod.step5.base_currency') }})</span>
                        </div>
                      </div>
                    </td>
                    <td>{{ formatAmount(baseCurrencyData.opening_balance || 0) }}</td>
                    <td class="text-success">{{ formatAmount(baseCurrencyData.income_amount || 0) }}</td>
                    <td class="text-danger">{{ formatAmount(baseCurrencyData.expense_amount || 0) }}</td>
                    <td class="text-warning">{{ formatAmount(baseCurrencyData.reversal_amount || 0) }}</td>
                    <td class="text-info">{{ formatAmount(baseCurrencyData.adjust_balance_amount || 0) }}</td>
                    <td class="text-secondary">{{ formatAmount(baseCurrencyData.cash_out_amount || 0) }}</td>
                    <td class="fw-bold">{{ formatAmount(baseCurrencyData.theoretical_balance || 0) }}</td>
                    <td>
                      <span class="badge bg-success">{{ t('eod.step5.balance_normal') }}</span>
                    </td>
                  </tr>
                  
                  <!-- 本币交易明细 -->
                  <!-- 调试信息 -->
                  <tr v-if="baseCurrencyData" class="d-none">
                    <td colspan="8" class="small text-info">
                      🐛 调试: baseCurrencyData={{ !!baseCurrencyData }}, 
                      expandedBaseCurrency='{{ expandedBaseCurrency }}', 
                      正确本币='{{ getBaseCurrencyCode() }}',
                      显示本币='{{ baseCurrencyData?.currency_code }}',
                      展开状态={{ isBaseCurrencyExpanded }}
                    </td>
                  </tr>
                  <tr v-if="baseCurrencyData && isBaseCurrencyExpanded">
                    <td colspan="8" class="p-0">
                      <div class="transaction-details bg-light">
                        <div v-if="loadingBaseCurrencyDetails" class="text-center py-3">
                          <div class="spinner-border spinner-border-sm me-2" role="status"></div>
                          {{ t('eod.loading_base_currency_details') }}
                        </div>
                        <div v-else-if="baseCurrencyDetails" class="p-3">
                          <!-- 合计计算区 - 压缩成一行显示 -->
                          <div class="calculation-summary-compact mb-3">
                            <div class="d-flex justify-content-between align-items-center">
                              <div>
                                <h6 class="mb-0 d-inline-block me-3">{{ t('eod.step5.local_currency_details') }}</h6>
                                <small class="text-muted">
                                  {{ t("eod.step5.transaction_count_template", { count: baseCurrencyDetails.transaction_count || 0 }) }}
                                  <span v-if="baseCurrencyDetails.time_range"> - 
                                    {{ formatTimeRange(baseCurrencyDetails.time_range.start_time, baseCurrencyDetails.time_range.end_time) }}
                                  </span>
                                </small>
                              </div>
                              <div v-if="hasBaseCurrencySelectedTransactions" class="selected-summary-inline">
                                                                  <span class="me-2">{{ t("eod.step5.selected_count_template", { count: selectedBaseCurrencyCount }) }} </span>
                                <span class="me-2">{{ t('eod.step5.subtotal') }}: <span :class="getBaseCurrencyAmountClass(selectedBaseCurrencySum)">{{ formatSignedAmount(selectedBaseCurrencySum) }}</span></span>
                                <span class="me-2">{{ t('eod.step5.current_balance') }}: <span class="text-primary fw-bold">{{ formatAmount((baseCurrencyData?.opening_balance || 0) + selectedBaseCurrencySum) }}</span></span>
                                <button class="btn btn-sm btn-outline-secondary" @click="clearBaseCurrencySelections()" :title="t('common.clear_selection')">
                                  <i class="fas fa-times"></i>
                                </button>
                              </div>
                              <div v-else class="text-muted small">
                                {{ t('eod.step5.current_balance') }}: <span class="text-primary fw-bold">{{ formatAmount((baseCurrencyData?.opening_balance || 0) + selectedBaseCurrencySum) }}</span>
                              </div>
                            </div>
                          </div>
                          <div v-if="baseCurrencyDetails.transactions && baseCurrencyDetails.transactions.length > 0" 
                               class="table-responsive">
                            <table class="table table-sm table-hover mb-0">
                              <thead class="table-light">
                                <tr>
                                  <th width="40px">
                                    <div class="form-check">
                                      <input class="form-check-input" type="checkbox" 
                                             :checked="isCurrentPageAllSelected('BASE_CURRENCY')" 
                                             @change="toggleAllCurrentPage('BASE_CURRENCY')"
                                             id="selectAll">
                                      <label class="form-check-label text-nowrap" for="selectAll">
                                        {{ t('eod.select_all') }}
                                      </label>
                                    </div>
                                  </th>
                                  <th>{{ t('eod.time') }}</th>
                                  <th>{{ t('eod.transaction_no') }}</th>
                                  <th>{{ t('eod.type') }}</th>
                                  <th>{{ t('eod.amount') }}</th>
                                  <th>{{ t('eod.transaction_content') }}</th>
                                </tr>
                              </thead>
                              <tbody>
                                <tr v-for="tx in baseCurrencyDetails.transactions" :key="tx.transaction_no || tx.id"
                                    :class="{ 'selected-row': isTransactionSelected('BASE_CURRENCY', tx) }">
                                  <td>
                                    <div class="form-check">
                                      <input class="form-check-input" type="checkbox" 
                                             :checked="isTransactionSelected('BASE_CURRENCY', tx)"
                                             @change="toggleTransactionSelection('BASE_CURRENCY', tx)"
                                             :id="'tx-' + (tx.transaction_no || tx.id)">
                                    </div>
                                  </td>
                                  <td class="text-muted small">{{ getCompactDateTime(tx.created_at) }}</td>
                                  <td class="text-muted small">{{ getShortTransactionNo(tx.transaction_no) }}</td>
                                  <td>
                                                                    <span class="badge" :class="getBaseCurrencyTransactionTypeClass(tx?.type)">
                                  {{ getBaseCurrencyTransactionTypeText(tx?.type) }}
                                </span>
                                  </td>
                                  <td :class="getBaseCurrencyAmountClass(tx.amount)">
                                    {{ formatSignedAmount(tx.amount) }}
                                  </td>
                                  <td class="text-muted small">{{ parseTransactionDescription(tx.description) || tx.customer_name || '-' }}</td>
                                </tr>
                              </tbody>
                            </table>
                          </div>
                          <div v-else class="text-center text-muted py-3">
                            {{ t('eod.no_base_currency_details') }}
                          </div>
                        </div>
                      </div>
                    </td>
                  </tr>

                  <!-- 只有当baseCurrencyData为空时才显示加载状态 -->
                  <tr v-if="!baseCurrencyData">
                    <td colspan="6" class="text-center text-muted">
                      <div class="py-3">
                        <div class="spinner-border spinner-border-sm me-2" role="status"></div>
                        {{ t('eod.loading_base_currency_data') }}
                      </div>
                    </td>
                  </tr>
                  <!-- 显示本币详细变动（如果有调节、冲正、交款等） -->
                  <tr v-if="hasDetailedMovements && baseCurrencyData" class="table-secondary">
                    <td colspan="6" class="small text-muted px-4">
                      <div class="d-flex flex-wrap gap-3">
                        <span v-if="baseCurrencyData.adjustment_amount && baseCurrencyData.adjustment_amount !== 0">
                          <strong>{{ t('eod.adjustment') }}:</strong> {{ formatSignedAmount(baseCurrencyData.adjustment_amount) }}
                        </span>
                        <span v-if="baseCurrencyData.reversal_amount && baseCurrencyData.reversal_amount !== 0">
                          <strong>{{ t('common.reversal') }}:</strong> {{ formatSignedAmount(baseCurrencyData.reversal_amount) }}
                        </span>
                        <span v-if="baseCurrencyData.cashout_amount && baseCurrencyData.cashout_amount !== 0">
                          <strong>{{ t('eod.cash_out') }}:</strong> -{{ formatAmount(baseCurrencyData.cashout_amount) }}
                        </span>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- 操作按钮区域 -->
        <div class="mt-3">
          <!-- 第一行：生成和打印相关按钮 -->
          <div class="d-flex gap-2 justify-content-end mb-2">
          <button 
            class="btn btn-outline-secondary btn-sm"
            @click="regenerateIncomeStats"
            :disabled="isGeneratingStats"
          >
            <font-awesome-icon :icon="['fas', 'sync-alt']" class="me-2" />
            {{ t('eod.step5.regenerate') }}
          </button>
            
            <!-- 重新打印按钮 -->
            <button v-if="incomeStatsConfirmed" 
            class="btn btn-outline-primary btn-sm"
            @click="printIncomeReports"
                    :disabled="isPrintingReports">
            <span v-if="isPrintingReports">
              <span class="spinner-border spinner-border-sm me-2" role="status"></span>
              {{ t('eod.step5.printing') }}
            </span>
            <span v-else>
              <font-awesome-icon :icon="['fas', 'print']" class="me-2" />
                {{ t('eod.step5.reprint') }}
              </span>
            </button>
            
            <button v-if="!incomeStatsConfirmed && incomeStatsGenerated" 
                    class="btn btn-success btn-sm"
                    @click="confirmIncomeAndPrintReports"
                    :disabled="isConfirmingStats || isPrintingReports">
              <span v-if="isConfirmingStats || isPrintingReports">
                <span class="spinner-border spinner-border-sm me-2" role="status"></span>
                {{ t("eod.step5.processing") }}
              </span>
              <span v-else>
                <font-awesome-icon :icon="['fas', 'check-double']" class="me-2" />
                {{ t('eod.step5.confirm_income_and_print') }}
            </span>
          </button>
          </div>
          
          <!-- 第二行：{{ $t("eod.step5.continue_eod_process") }}按钮 -->
          <div v-if="incomeStatsConfirmed" class="d-flex justify-content-end">
            <button 
              class="btn btn-primary btn-sm"
              @click="continueEOD"
              :disabled="loading || isProcessing">
              <span v-if="isProcessing">
                <span class="spinner-border spinner-border-sm me-2" role="status"></span>
                {{ t("eod.step5.processing") }}
              </span>
              <span v-else>
                <font-awesome-icon :icon="['fas', 'arrow-right']" class="me-2" />
                {{ t("eod.step5.continue_eod_process") }}
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 余额不一致的情况 -->
    <div v-if="!allMatched && !isForceContinued" class="mt-3">
      <div class="alert alert-danger py-2">
        <h6 class="alert-heading">
          <font-awesome-icon :icon="['fas', 'exclamation-triangle']" class="me-2" />
          {{ t("eod.step5.balance_differences_found") }}
        </h6>
        <p class="mb-3">{{ t('eod.step5.detected_differences_message', { count: mismatchedCount }) }}</p>
        
        <!-- 处理选项 -->
        <div class="d-flex justify-content-between align-items-center">
          <div>
            <span class="badge bg-danger me-2">{{ t('eod.step5.critical_differences') }}</span>
            <span class="text-muted">{{ t('eod.step5.critical_differences_desc') }}</span>
          </div>
          <div class="btn-group">
            <button 
              v-if="hasCriticalDifferences"
              class="btn btn-outline-danger btn-sm"
              @click="cancelEOD"
              :disabled="isProcessing"
            >
              <font-awesome-icon :icon="['fas', 'times']" class="me-2" />
              {{ t("eod.step5.cancel_eod") }}
            </button>
            <button 
              class="btn btn-warning btn-sm"
              @click="forceContinue"
              :disabled="isProcessing"
            >
              <font-awesome-icon :icon="['fas', 'exclamation-triangle']" class="me-2" />
              {{ t("eod.step5.force_continue") }}
            </button>
          </div>
        </div>
      </div>

      <!-- 不一致币种详情表格 -->
      <div class="card mt-3">
        <div class="card-header py-2">
          <h6 class="mb-0">{{ t('eod.step5.balance_differences_details') }}</h6>
        </div>
        <div class="card-body p-0">
          <div class="table-responsive">
            <table class="table table-sm mb-0">
              <thead class="table-light">
                <tr>
                                        <th>{{ t("eod.step5.currency") }}</th>
                                      <th>{{ t("eod.step5.step5_theoretical_balance") }}</th>
                <th>{{ t("eod.step5.step5_actual_balance") }}</th>
                      <th>{{ t("eod.step5.difference_amount") }}</th>
                      <th>{{ t("eod.step5.difference_ratio") }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="result in mismatchedResults.filter(r => r && r.currency_code)" :key="result.currency_id" class="table-danger">
                  <td>
                    <CurrencyFlag 
                      :code="result.currency_code || 'USD'" 
                      :width="20" 
                      :height="14" 
                      class="me-2"
                    />
                    {{ result.currency_code }}
                  </td>
                  <td>{{ formatAmount(result.theoretical_balance || 0) }}</td>
                  <td>{{ formatAmount(result.actual_balance || 0) }}</td>
                  <td class="text-danger fw-bold">
                    {{ formatDifference(result.difference || 0) }}
                  </td>
                  <td class="text-danger">
                    {{ formatPercentage(result.difference || 0, result.theoretical_balance || 0) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { eodAPI } from '../../../api/eod'
import CurrencyFlag from '../../CurrencyFlag.vue'
import { formatAmount } from '@/utils/formatters'
import { useI18n } from 'vue-i18n'
import { getCurrencyName } from '@/utils/currencyTranslator'

export default {
  name: 'Step5Result',
  components: {
    CurrencyFlag
  },
  emits: ['next', 'cancel', 'error'],
  props: {
    eodId: {
      type: [Number, String],
      required: true
    },
    verificationResults: {
      type: Array,
      default: () => []
    },
    loading: {
      type: Boolean,
      default: false
    },
    autoGenerateIncomeStats: {
      type: Boolean,
      default: false
    },
    eodStatus: {
      type: Object,
      default: () => {}
    },
    forced_continue: {
      type: Boolean,
      default: false
    }
  },
  setup(props, { emit }) {
    const { t, locale } = useI18n()

    // 响应式数据
    const isProcessing = ref(false)
    const cancelReason = ref('')
    const forceReason = ref('')
    const forceConfirm = ref(false)
    
    // 收入统计相关
    const shouldShowIncomeStats = ref(false)
    const isForceContinued = ref(false)  // 新增：标记是否已强制继续
    const incomeStatsGenerated = ref(false)
    const incomeStatsConfirmed = ref(false)
    const isGeneratingStats = ref(false)
    const isPrintingReports = ref(false)
    const isConfirmingStats = ref(false)
    const incomeReports = ref([])
    const stockReports = ref([])
    const totalIncome = ref(0)
    const totalSpreadIncome = ref(0)
    
    // 展开/收起状态
    const showIncomeReports = ref(true)
    const showStockReports = ref(true)
    const showBaseCurrencyReports = ref(true)
    
    // 币种明细展开/收起状态
    const expandedCurrency = ref(null)
    const currencyDetails = ref({})
    const loadingDetails = ref(false)
    const paginatedTransactions = ref({})
    const pageSize = ref(20)
    
    // 本币库存数据
    const baseCurrencyData = ref(null)
    
    // 本币库存明细展开/收起状态
    const expandedBaseCurrency = ref(null)
    const baseCurrencyDetails = ref(null)
    const loadingBaseCurrencyDetails = ref(false)
    
    // 明细交易勾选相关数据
    const selectedTransactions = ref({}) // 存储勾选的交易：{ currencyCode: { transactionNo: transaction } }
    const selectedSum = ref(0)
    
    // 【修复】使用统一的本币获取函数
    const getBaseCurrencyCode = () => {
      try {
        const userInfo = JSON.parse(localStorage.getItem('user') || '{}')
        const branchCurrency = userInfo.branch_currency || null
        const baseCurrencyCode = branchCurrency?.code || branchCurrency?.currency_code || null
        
        if (!baseCurrencyCode) {
          console.warn('⚠️ 无法获取本币信息，用户可能需要重新登录')
          return null // 返回null而不是默认值，让调用方处理
        }
        
        console.log('✅ 成功获取本币信息:', {
          code: baseCurrencyCode,
          name: branchCurrency.name || branchCurrency.currency_name,
          id: branchCurrency.id
        })
        
        return baseCurrencyCode
      } catch (error) {
        console.error('❌ 获取本币信息失败:', error)
        return null
      }
    }
    
    // 移除未使用的getBaseCurrencyId函数
    
    // 【修复】过滤外币的计算属性 - 正确处理本币信息为null的情况
    const foreignIncomeReports = computed(() => {
      const baseCurrencyCode = getBaseCurrencyCode()
      if (!baseCurrencyCode) {
        console.warn('⚠️ 无法获取本币信息，无法过滤外币报表')
        return incomeReports.value // 如果无法获取本币信息，返回所有报表
      }
      return incomeReports.value.filter(r => r && r.currency_code && r.currency_code !== baseCurrencyCode)
    })
    
    const foreignStockReports = computed(() => {
      const baseCurrencyCode = getBaseCurrencyCode()
      if (!baseCurrencyCode) {
        console.warn('⚠️ 无法获取本币信息，无法过滤外币报表')
        return stockReports.value // 如果无法获取本币信息，返回所有报表
      }
      return stockReports.value.filter(r => r && r.currency_code && r.currency_code !== baseCurrencyCode)
    })
    
    // 【新增】判断本币明细是否应该展开的计算属性
    const isBaseCurrencyExpanded = computed(() => {
      const baseCurrencyCode = getBaseCurrencyCode()
      return baseCurrencyCode && expandedBaseCurrency.value === baseCurrencyCode
    })
    
    // 计算属性
    const allMatched = computed(() => {
      return props.verificationResults.every(result => result.is_match)
    })
    
    const matchedCount = computed(() => {
      return props.verificationResults.filter(result => result.is_match).length
    })
    
    const mismatchedCount = computed(() => {
      return props.verificationResults.filter(result => !result.is_match).length
    })
    
    // 计算一致率，避免除零错误
    const calculateMatchRate = () => {
      const total = matchedCount.value + mismatchedCount.value
      if (total === 0) return 0
      return Math.round((matchedCount.value / total) * 100)
    }
    
    const mismatchedResults = computed(() => {
      return props.verificationResults.filter(result => !result.is_match)
    })
    
    // 判断是否有严重差异，需要显示取消按钮
    const hasCriticalDifferences = computed(() => {
      return mismatchedResults.value.some(result => {
        const difference = Math.abs(result.difference || 0)
        const theoreticalBalance = Math.abs(result.theoretical_balance || 0)
        // 差异超过理论余额的10%或差异金额超过1000认为是严重差异
        return difference > 1000 || (theoreticalBalance > 0 && difference / theoreticalBalance > 0.1)
      })
    })
    
    // 勾选项目的动态计算
    const selectedCount = computed(() => {
      let count = 0
      Object.values(selectedTransactions.value).forEach(currencyTxs => {
        count += Object.keys(currencyTxs).length
      })
      return count
    })
    
    const selectedForeignTotal = computed(() => {
      let total = 0
      Object.values(selectedTransactions.value).forEach(currencyTxs => {
        Object.values(currencyTxs).forEach(tx => {
          total += parseFloat(tx.amount || 0)
        })
      })
      // 保留两位小数精度
      return Math.round(total * 100) / 100
    })
    
    const selectedLocalTotal = computed(() => {
      let total = 0
      Object.values(selectedTransactions.value).forEach(currencyTxs => {
        Object.values(currencyTxs).forEach(tx => {
          total += parseFloat(tx.local_amount || 0)
        })
      })
      // 保留两位小数精度
      return Math.round(total * 100) / 100
    })
    
    // 是否显示勾选汇总
    const hasSelectedTransactions = computed(() => {
      return selectedCount.value > 0
    })
    
    // 展开/收起方法
    const toggleIncomeReports = () => {
      showIncomeReports.value = !showIncomeReports.value
    }
    
    const toggleStockReports = () => {
      showStockReports.value = !showStockReports.value
    }
    
    const toggleBaseCurrencyReports = () => {
      showBaseCurrencyReports.value = !showBaseCurrencyReports.value
    }
    
    // 方法
    const continueEOD = async () => {
      try {
        isProcessing.value = true
        
        // 如果{{ $t("eod.step5.balance_verification_passed") }}，显示收入统计
        if (allMatched.value && !shouldShowIncomeStats.value) {
          shouldShowIncomeStats.value = true
          isProcessing.value = false
          return
        }
        
        const result = await eodAPI.handleVerification(props.eodId, 'continue')
        
        if (result.success) {
          emit('next', {
            action: 'continue',
            step: 6,  // 第5步完成后，应该进入第6步
            from_api_call: true
          })
        } else {
          emit('error', result.message || t('eod.step5.continue_eod_failed'))
        }
      } catch (error) {
        console.error('Continue EOD failed:', error)
        
        // 【方案1优化】当遇到权限错误时，自动尝试恢复会话
        const errorMessage = error.response?.data?.message || error.message || ''
        if (errorMessage.includes('无权限进行日结操作')) {
          console.log('检测到权限错误，尝试自动恢复会话...')
          
          try {
            // 调用父组件的继续现有日结方法
            if (emit) {
              // 发送事件通知父组件进行会话恢复
              emit('session-recovery-needed')
              
              // 等待一小段时间让父组件处理
              await new Promise(resolve => setTimeout(resolve, 1000))
              
              // 重新尝试继续日结
              console.log('会话恢复后，重新尝试继续日结...')
              const retryResult = await eodAPI.handleVerification(props.eodId, 'continue')
              
              if (retryResult.success) {
                emit('next', {
                  action: 'continue',
                  step: 6,
                  from_api_call: true,
                  auto_recovered: true
                })
                return
              }
            }
          } catch (recoveryError) {
            console.error('自动恢复会话失败:', recoveryError)
          }
        }
        
        emit('error', errorMessage || t('eod.step5.continue_eod_failed'))
      } finally {
        isProcessing.value = false
      }
    }
    
    const cancelEOD = async () => {
      try {
        const result = await eodAPI.cancelComplete(props.eodId, '用户取消日结')
        
        if (result.success) {
          emit('cancel', result)
        } else {
          emit('error', result.message || t('eod.step5.cancel_eod_failed'))
        }
      } catch (error) {
        console.error('取消日结失败:', error)
        emit('error', error.response?.data?.message || error.message || t('eod.step5.cancel_eod_failed'))
      }
    }
    
    const forceContinue = async () => {
      if (!confirm(t('eod.confirm_force_continue_eod'))) return
      
      try {
        isProcessing.value = true
        
        const result = await eodAPI.handleVerification(props.eodId, 'force', forceReason.value)
        
        if (result.success) {
          // 强制继续后，显示收入统计页面，而不是直接跳转到步骤6
          shouldShowIncomeStats.value = true
          isForceContinued.value = true  // 设置强制继续标记
          
          // 自动生成收入统计
          await generateIncomeStats()
          
          // 显示成功消息
          emit('next', {
            action: 'force',
            reason: forceReason.value,
            step: 5,  // 保持在步骤5，显示收入统计
            from_api_call: true,
            show_income_stats: true
          })
        } else {
          emit('error', result.message || t('eod.step5.force_continue_failed'))
        }
      } catch (error) {
        console.error('强制继续失败:', error)
        emit('error', error.response?.data?.message || error.message || t('eod.step5.force_continue_failed'))
      } finally {
        isProcessing.value = false
      }
    }
    
    const formatDifference = (difference) => {
      if (difference === 0) return '0.00'
      const formatted = formatAmount(Math.abs(difference))
      return difference > 0 ? `+${formatted}` : `-${formatted}`
    }
    
    const formatPercentage = (difference, expected) => {
      if (expected === 0) return '0.00%'
      const percentage = Math.abs(difference / expected) * 100
      return `${percentage.toFixed(2)}%`
    }
    
    // 收入统计相关方法
    const generateIncomeStats = async () => {
      try {
        isGeneratingStats.value = true
        
        const result = await eodAPI.generateIncomeStatistics(props.eodId, {
          language: locale.value || 'zh'
        })
        
        if (result.success) {
          incomeReports.value = result.income_data ? result.income_data.currencies || [] : []
          stockReports.value = result.stock_data ? result.stock_data.currencies || [] : []
          baseCurrencyData.value = result.base_currency_data || null
          totalIncome.value = result.income_data ? result.income_data.total_income || 0 : 0
          totalSpreadIncome.value = result.income_data ? result.income_data.total_spread_income || 0 : 0
          incomeStatsGenerated.value = true
        } else {
          emit('error', result.message || t('eod.income_stats_generation_failed'))
        }
      } catch (error) {
        console.error('生成收入统计失败:', error)
        emit('error', error.response?.data?.message || error.message || t('eod.income_stats_generation_failed'))
      } finally {
        isGeneratingStats.value = false
      }
    }
    
    const confirmIncomeAndPrintReports = async () => {
      try {
        isConfirmingStats.value = true
        console.log('开始确认收入统计并打印报表...')
        
        // 第一步：确认收入统计
        const result = await eodAPI.finalizeReports(props.eodId)
        
        if (result.success) {
          incomeStatsConfirmed.value = true
          console.log('收入统计确认成功，开始打印报表...')
          
          // 第二步：打印收入报表到manager目录并自动打印
          isPrintingReports.value = true
          try {
            // 调用收入报表打印API（传递当前语言）
            const printResult = await eodAPI.printIncomeReports(props.eodId, {
              language: locale.value || 'zh'
            })
            
            if (printResult && printResult.success) {
              // 根据PDF来源显示提示信息
              const source = printResult.source || 'unknown'
              if (source === 'synchronized') {
                console.log('✅ 使用同步生成PDF文件，数据与界面显示完全一致，开始自动打印...')
              } else {
                console.log('📄 收入报表生成成功，数据与界面完全一致，开始自动打印...')
              }
              
              // 自动下载PDF并触发浏览器打印
              await autoDownloadAndPrint()
              
            } else {
              console.error('收入报表打印失败')
              // 检查是否是PDF文件丢失的错误
              if (printResult.error_code === 'PDF_NOT_FOUND') {
                emit('error', printResult.message || 'PDF文件丢失，请重新执行第5步生成收入统计')
              } else {
                emit('error', printResult.message || '打印收入报表失败')
              }
            }
          } catch (printError) {
            console.error('打印收入报表异常:', printError)
            emit('error', printError.message || '打印收入报表失败')
          } finally {
            isPrintingReports.value = false
          }
        } else {
          emit('error', result.message || t('eod.income_stats_confirmation_failed'))
        }
      } catch (error) {
        console.error('确认收入统计失败:', error)
        emit('error', error.response?.data?.message || error.message || t('eod.income_stats_confirmation_failed'))
      } finally {
        isConfirmingStats.value = false
      }
    }
    
    const printIncomeReports = async () => {
      try {
        isPrintingReports.value = true
        
        // 使用新的下载API获取收入报表PDF
        const token = localStorage.getItem('token')
        const downloadUrl = `/api/end_of_day/${props.eodId}/download-income-report?language=${locale.value || 'zh'}`
        
        console.log('开始获取PDF数据用于重新打印...')
        
        // 使用fetch获取PDF文件
        const pdfFetchResponse = await fetch(downloadUrl, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        
        if (!pdfFetchResponse.ok) {
          // 检查响应类型，避免解析非JSON数据
          const contentType = pdfFetchResponse.headers.get('Content-Type') || ''
          let errorMessage = '获取PDF文件失败'
          
          if (contentType.includes('application/json')) {
            try {
              const errorData = await pdfFetchResponse.json()
              errorMessage = errorData.message || errorMessage
            } catch (e) {
              // JSON解析失败，使用默认错误信息
            }
          } else {
            // 非JSON响应，可能是代理错误HTML页面
            const errorText = await pdfFetchResponse.text()
            if (errorText.includes('Proxy Error')) {
              errorMessage = '代理服务器错误，请检查后端服务是否正常运行'
            } else {
              errorMessage = `服务器响应错误: ${pdfFetchResponse.status}`
            }
          }
          
          throw new Error(errorMessage)
        }
        
        // 获取PDF blob数据
        const pdfBlob = await pdfFetchResponse.blob()
        const blobUrl = window.URL.createObjectURL(pdfBlob)
        
        console.log('PDF blob URL创建成功，使用iframe方式重新打印...')
        
        // 使用隐藏的iframe方式直接触发重新打印对话框
        const iframe = document.createElement('iframe')
        iframe.style.display = 'none'  // 隐藏iframe，只显示打印对话框
        iframe.style.width = '1200px'  // 更大的尺寸以获得更好的打印预览
        iframe.style.height = '800px'
        iframe.src = blobUrl
        
        // 添加到body
        document.body.appendChild(iframe)
        
        // 监听iframe加载完成事件
        iframe.onload = function() {
          try {
            console.log('PDF已加载到隐藏iframe，触发重新打印对话框...')
            
            // 短延迟后触发打印，确保PDF完全加载
            setTimeout(() => {
              iframe.contentWindow.focus()
              iframe.contentWindow.print()
              console.log('浏览器重新打印对话框已触发')
              
              // 打印对话框关闭后清理资源
              setTimeout(() => {
                if (iframe && iframe.parentNode) {
                  document.body.removeChild(iframe)
                }
                window.URL.revokeObjectURL(blobUrl)
                console.log('重新打印PDF资源已清理')
              }, 20000) // 20秒后清理，给用户足够时间完成打印
            }, 800) // 800ms延迟确保PDF完全加载
          } catch (printError) {
            console.error('触发重新打印失败:', printError)
            // 清理资源
            if (iframe && iframe.parentNode) {
              document.body.removeChild(iframe)
            }
            window.URL.revokeObjectURL(blobUrl)
          }
        }
        
        iframe.onerror = function() {
          console.error('iframe重新打印PDF加载失败')
          if (iframe && iframe.parentNode) {
            document.body.removeChild(iframe)
          }
          window.URL.revokeObjectURL(blobUrl)
        }
        
      } catch (error) {
        console.error('重新打印失败:', error)
        emit('error', error.message || t('eod.reprint_failed'))
      } finally {
        isPrintingReports.value = false
      }
    }
    
    const regenerateIncomeStats = async () => {
      incomeStatsGenerated.value = false
      incomeStatsConfirmed.value = false
      incomeReports.value = []
      stockReports.value = []
      totalIncome.value = 0
      totalSpreadIncome.value = 0
      await generateIncomeStats()
    }
    
    const showIncomeDetail = (currencyCode) => {
      // 显示收入详情（可以实现模态框或跳转）
      console.log('显示收入详情:', currencyCode)
    }
    
    const getBalanceChangeClass = (changeAmount) => {
      if (changeAmount > 0) return 'text-success'
      if (changeAmount < 0) return 'text-danger'
      return 'text-muted'
    }
    
    const getReversalAmountClass = (reversalAmount) => {
      if (reversalAmount > 0) return 'text-success'
      if (reversalAmount < 0) return 'text-danger'
      return 'text-muted'
    }
    
    const getStockStatusClass = (balance) => {
      if (balance <= 0) return 'badge bg-danger'
      if (balance < 1000) return 'badge bg-warning'
      return 'badge bg-success'
    }
    
    const getStockStatusText = (balance) => {
      if (balance <= 0) return t('eod.out_of_stock')
      if (balance < 1000) return t('eod.low_stock')
      return t('eod.normal')
    }
    
    // 币种明细展开/收起功能
    const toggleCurrencyDetails = async (currencyCode) => {
      if (expandedCurrency.value === currencyCode) {
        expandedCurrency.value = null
      } else {
        // 切换到新币种时，清除之前的所有勾选项目
        clearAllSelections()
        
        expandedCurrency.value = currencyCode
        if (!currencyDetails.value[currencyCode]) {
          await loadCurrencyDetails(currencyCode)
        }
      }
    }
    
    const loadCurrencyDetails = async (currencyCode) => {
      loadingDetails.value = true
      try {
        // 获取日结日期 - 需要从props或其他地方获取
        const eodDate = getEodDate() // 获取日结日期的函数
        
        // 获取当前用户信息
        const currentUser = JSON.parse(localStorage.getItem('user') || '{}')
        const branchId = currentUser.branch_id
        
        // 添加调试日志
        console.log(`🔍 [loadCurrencyDetails] 开始加载币种明细:`)
        console.log(`  币种: ${currencyCode}`)
        console.log(`  日期: ${eodDate}`)
        console.log(`  分支ID: ${branchId}`)
        console.log(`  EOD状态:`, props.eodStatus)
        
        // 调用API获取币种交易明细，传递正确的日期和分支ID
        const response = await eodAPI.getCurrencyTransactionDetails(currencyCode, {
          date: eodDate,
          branch_id: branchId
        })
        
        console.log(`📡 [API响应] 完整响应:`, response)
        console.log(`📡 [API响应] response.data:`, response.data)
        console.log(`📡 [API响应] success:`, response.data?.success)
        console.log(`📡 [API响应] data:`, response.data?.data)
        
        // 保存到window对象供调试
        if (typeof window !== 'undefined') {
          window.lastResponse = response
        }
        
        // 尝试多种响应结构的兼容处理
        let apiData = null
        let isSuccess = false
        
        // 情况1: 标准结构 response.data.success
        if (response.data && typeof response.data.success !== 'undefined') {
          console.log(`🔧 [响应模式] 标准axios结构: response.data.success`)
          isSuccess = response.data.success
          apiData = response.data.data
        }
        // 情况2: 直接成功数据 response.data (没有success字段)
        else if (response.data && response.data.transactions) {
          console.log(`🔧 [响应模式] 直接数据结构: response.data包含transactions`)
          isSuccess = true
          apiData = response.data
        }
        // 情况3: response直接是数据 (没有嵌套的data)
        else if (response.success !== 'undefined') {
          console.log(`🔧 [响应模式] 扁平结构: response.success`)
          isSuccess = response.success
          apiData = response.data
        }
        // 情况4: response直接包含数据
        else if (response.transactions) {
          console.log(`🔧 [响应模式] 直接transactions: response.transactions`)
          isSuccess = true
          apiData = response
        }
        // 情况5: 错误响应
        else {
          console.log(`🔧 [响应模式] 未知结构，尝试解析错误信息`)
          console.log(`  response类型:`, typeof response)
          console.log(`  response.status:`, response.status)
          console.log(`  response.statusText:`, response.statusText)
          console.log(`  response的所有属性:`, Object.keys(response))
          if (response.data) {
            console.log(`  response.data类型:`, typeof response.data)
            console.log(`  response.data的所有属性:`, Object.keys(response.data))
          }
        }
        
        console.log(`📊 [处理结果] isSuccess:`, isSuccess)
        console.log(`📊 [处理结果] apiData:`, apiData)
        
        if (isSuccess && apiData) {
          console.log(`✅ [API成功] 设置currencyDetails[${currencyCode}]:`, apiData)
          console.log(`✅ [API成功] 交易数量:`, apiData?.transactions?.length || 0)
          
          currencyDetails.value[currencyCode] = apiData
          initializePagination(currencyCode)
          
          console.log(`✅ [设置完成] currencyDetails.value[${currencyCode}]:`, currencyDetails.value[currencyCode])
          console.log(`✅ [设置完成] paginatedTransactions.value[${currencyCode}]:`, paginatedTransactions.value[currencyCode])
        } else {
          const errorMsg = response.data?.message || response.message || response.statusText || t('common.unknown_error')
          console.error('❌ [API失败] 加载币种明细失败:', errorMsg)
          console.error('❌ [API失败] 完整响应结构:', response)
        }
      } catch (error) {
        console.error('❌ [异常] 加载币种明细失败:', error)
        console.error('❌ [异常] 错误详情:', error.response?.data || error.message)
      } finally {
        loadingDetails.value = false
        console.log(`🏁 [完成] loadCurrencyDetails 结束`)
      }
    }
    
    // 获取日结日期的辅助函数
    const getEodDate = () => {
      // 从EOD状态获取正确的日结日期
      if (props.eodStatus && props.eodStatus.date) {
        // 如果是ISO格式，提取日期部分
        const dateStr = props.eodStatus.date.split('T')[0]
        return dateStr
      }
      
      // 如果没有日结状态，尝试从其他地方获取
      // 注意：这里需要根据实际情况调整，暂时使用默认日期
      // const currentEodStatus = userStore.currentEodStatus
      // if (currentEodStatus && currentEodStatus.date) {
      //   const dateStr = currentEodStatus.date.split('T')[0]
      //   return dateStr
      // }
      
      // 最后才使用今天的日期作为默认值
      return new Date().toISOString().split('T')[0]
    }
    
    const initializePagination = (currencyCode) => {
      if (!currencyDetails.value[currencyCode]) return
      
      const transactions = currencyDetails.value[currencyCode].transactions || []
      paginatedTransactions.value[currencyCode] = {
        currentPage: 1,
        totalCount: transactions.length,
        transactions: transactions
      }
    }
    
    const getCurrentPageTransactions = (currencyCode) => {
      // 特殊处理本币交易
      if (currencyCode === 'BASE_CURRENCY') {
        return baseCurrencyDetails.value?.transactions || []
      }
      
      const pagination = paginatedTransactions.value[currencyCode]
      if (!pagination) return []
      
      const start = (pagination.currentPage - 1) * pageSize.value
      const end = start + pageSize.value
      return pagination.transactions.slice(start, end)
    }
    
    const needsPagination = (currencyCode) => {
      const pagination = paginatedTransactions.value[currencyCode]
      return pagination && pagination.totalCount > pageSize.value
    }
    
    const getCurrentPage = (currencyCode) => {
      return paginatedTransactions.value[currencyCode]?.currentPage || 1
    }
    
    const getTotalPages = (currencyCode) => {
      const pagination = paginatedTransactions.value[currencyCode]
      if (!pagination) return 1
      return Math.ceil(pagination.totalCount / pageSize.value)
    }
    
    const getTotalTransactions = (currencyCode) => {
      return paginatedTransactions.value[currencyCode]?.totalCount || 0
    }
    
    const getPaginationData = (currencyCode) => {
      return paginatedTransactions.value[currencyCode]
    }
    
    const prevPage = (currencyCode) => {
      const pagination = paginatedTransactions.value[currencyCode]
      if (pagination && pagination.currentPage > 1) {
        pagination.currentPage--
      }
    }
    
    const nextPage = (currencyCode) => {
      const pagination = paginatedTransactions.value[currencyCode]
      if (pagination && pagination.currentPage < getTotalPages(currencyCode)) {
        pagination.currentPage++
      }
    }
    
    // 格式化方法
    const getShortTransactionNo = (transactionNo) => {
      return transactionNo.slice(-8) // 显示后8位
    }
    
    const getCompactDateTime = (dateTime) => {
      const date = new Date(dateTime)
      return date.toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    }
    
    const formatTimeRange = (startTime, endTime) => {
      if (!startTime || !endTime) return ''
      const start = new Date(startTime)
      const end = new Date(endTime)
      return `${start.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })} - ${end.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })}`
    }
    
    const formatRate = (value) => {
      if (value === null || value === undefined || value === 0) return '-'
      return new Intl.NumberFormat('zh-CN', {
        minimumFractionDigits: 4,
        maximumFractionDigits: 4
      }).format(value)
    }
    
    const formatSignedForeignAmount = (amount) => {
      // 直接使用原始金额，保持正负符号
      const numAmount = parseFloat(amount)
      const sign = numAmount >= 0 ? '+' : ''  // 负数会自动显示-号
      return `${sign}${formatAmount(numAmount)}`
    }
    
    const getTransactionAmountClass = (amount) => {
      // 根据金额的正负决定颜色
      return parseFloat(amount) >= 0 ? 'amount-positive' : 'amount-negative'
    }
    
    const getTransactionTypeClass = (type) => {
      if (!type) return 'type-unknown'
      return type === 'buy' ? 'type-buy' : 'type-sell'
    }
    
    const getTransactionTypeText = (type) => {
      if (!type) return '未知'
      switch (type) {
        case 'buy':
          return t('exchange.buy')
        case 'sell':
          return t('exchange.sell')
        case 'reversal':
          return t('common.reversal')
        default:
          return type
      }
    }
    
    // 合计计算方法
    const formatForeignTotal = (currencyCode) => {
      const transactions = currencyDetails.value[currencyCode]?.transactions || []
      let total = 0
      
      transactions.forEach(tx => {
        // 直接使用amount的值，因为数据库中已经存储了正确的正负符号
        // buy: 正数（银行买入外币，外币增加）
        // sell: 负数（银行卖出外币，外币减少）  
        // reversal: 根据被冲正的交易类型，amount已经有正确的正负符号
        const amount = parseFloat(tx.amount)
        total += amount
      })
      
      const sign = total >= 0 ? '+' : ''
      return `${sign}${formatAmount(Math.abs(total))} ${currencyCode}`
    }
    
    const formatLocalTotal = (currencyCode) => {
      const transactions = currencyDetails.value[currencyCode]?.transactions || []
      const total = transactions.reduce((sum, tx) => sum + parseFloat(tx.local_amount), 0)
      return formatAmount(total)
    }
    
    const formatForeignPageTotal = (currencyCode) => {
      const pageTransactions = getCurrentPageTransactions(currencyCode)
      let total = 0
      
      pageTransactions.forEach(tx => {
        // 直接使用amount的值，因为数据库中已经存储了正确的正负符号
        const amount = parseFloat(tx.amount)
        total += amount
      })
      
      const sign = total >= 0 ? '+' : ''
      return `${sign}${formatAmount(Math.abs(total))} ${currencyCode}`
    }
    
    const formatLocalPageTotal = (currencyCode) => {
      const pageTransactions = getCurrentPageTransactions(currencyCode)
      const total = pageTransactions.reduce((sum, tx) => sum + parseFloat(tx.local_amount), 0)
      return formatAmount(total)
    }
    
    const getForeignTotalClass = (currencyCode) => {
      const transactions = currencyDetails.value[currencyCode]?.transactions || []
      let total = 0
      
      transactions.forEach(tx => {
        // 直接使用amount的值，因为数据库中已经存储了正确的正负符号
        const amount = parseFloat(tx.amount)
        total += amount
      })
      
      return total >= 0 ? 'amount-positive' : 'amount-negative'
    }
    
    const getForeignPageTotalClass = (currencyCode) => {
      const pageTransactions = getCurrentPageTransactions(currencyCode)
      let total = 0
      
      pageTransactions.forEach(tx => {
        // 直接使用amount的值，因为数据库中已经存储了正确的正负符号
        const amount = parseFloat(tx.amount)
        total += amount
      })
      
      return total >= 0 ? 'amount-positive' : 'amount-negative'
    }
    
    // 使用统一的多语言币种名称翻译，支持自定义币种
    const getCurrencyNameTranslated = (currencyCode) => {
      // 检查是否是自定义币种（在incomeReports或stockReports中查找）
      const incomeReport = incomeReports.value.find(r => r.currency_code === currencyCode)
      const stockReport = stockReports.value.find(r => r.currency_code === currencyCode)
      
      if (incomeReport && incomeReport.custom_flag_filename) {
        // console.log(`[自定义币种] ${currencyCode} 使用数据库名称: ${incomeReport.currency_name}`)
        return incomeReport.currency_name || currencyCode
      }
      
      if (stockReport && stockReport.custom_flag_filename) {
        // console.log(`[自定义币种] ${currencyCode} 使用数据库名称: ${stockReport.currency_name}`)
        return stockReport.currency_name || currencyCode
      }
      
      return getCurrencyName(currencyCode)
    }
    
    // 格式化带符号的金额 - 移除重复声明，使用后面的版本
    
    // 判断是否有详细变动需要显示
    const hasDetailedMovements = computed(() => {
      if (!baseCurrencyData.value) return false
      
      return baseCurrencyData.value.adjustment_amount !== 0 ||
             baseCurrencyData.value.reversal_amount !== 0 ||
             baseCurrencyData.value.cashout_amount !== 0
    })
    
    // 调试函数 - 用于实时查看数据状态
    const debugCurrencyDetails = (currencyCode) => {
      console.log(`🐛 [调试] ${currencyCode} 当前状态:`)
      console.log(`  currencyDetails.value[${currencyCode}]:`, currencyDetails.value[currencyCode])
      console.log(`  paginatedTransactions.value[${currencyCode}]:`, paginatedTransactions.value[currencyCode])
      console.log(`  expandedCurrency.value:`, expandedCurrency.value)
      console.log(`  loadingDetails.value:`, loadingDetails.value)
      
      const details = currencyDetails.value[currencyCode]
      if (details) {
        console.log(`  transactions数组:`, details.transactions)
        console.log(`  transactions长度:`, details.transactions?.length || 0)
        console.log(`  total_count:`, details.total_count)
      } else {
        console.log(`  ❌ currencyDetails[${currencyCode}] 为空`)
      }
      
      const pagination = paginatedTransactions.value[currencyCode]
      if (pagination) {
        console.log(`  分页信息:`)
        console.log(`    totalCount: ${pagination.totalCount}`)
        console.log(`    currentPage: ${pagination.currentPage}`)
        console.log(`    transactions: ${pagination.transactions?.length || 0} 笔`)
      } else {
        console.log(`  ❌ paginatedTransactions[${currencyCode}] 为空`)
      }
          }
      
      // 本币库存明细相关方法
      const toggleBaseCurrencyDetails = async (paramCurrencyCode) => {
        // 【修复】不依赖传入的参数，直接从localStorage获取正确的本币代码
        const baseCurrencyCode = getBaseCurrencyCode()
        
        if (!baseCurrencyCode) {
          console.error('❌ 无法获取本币信息，请重新登录')
          emit('error', '无法获取本币信息，请重新登录')
          return
        }
        
        console.log('🔍 本币明细操作:', {
          传入参数: paramCurrencyCode,
          实际本币: baseCurrencyCode,
          当前展开状态: expandedBaseCurrency.value
        })
        
        if (expandedBaseCurrency.value === baseCurrencyCode) {
          // 收起明细
          expandedBaseCurrency.value = null
          baseCurrencyDetails.value = null
        } else {
          // 展开明细 - 使用正确的本币代码
          expandedBaseCurrency.value = baseCurrencyCode
          await loadBaseCurrencyDetails(baseCurrencyCode)
        }
      }
      
      const loadBaseCurrencyDetails = async (currencyCode) => {
        try {
          loadingBaseCurrencyDetails.value = true
          
          // 清空之前的选中状态
          selectedTransactions.value = []
          selectedSum.value = 0
          
          // 调用API获取本币交易明细
          const result = await eodAPI.getBaseCurrencyTransactionDetails(props.eodId, currencyCode, {
            page: 1,
            per_page: 20
          })
          
          if (result.success) {
            baseCurrencyDetails.value = result.data
          } else {
                    console.error('❌ 获取本币交易明细失败:', result.message)
        emit('error', result.message || t('eod.error_load_base_currency_details'))
          }
        } catch (error) {
                  console.error('💥 获取本币交易明细异常:', error)
        emit('error', error.response?.data?.message || error.message || t('eod.error_load_base_currency_details'))
        } finally {
          loadingBaseCurrencyDetails.value = false
        }
      }
      
      // 本币交易样式处理方法
      const getBaseCurrencyTransactionTypeClass = (type) => {
        if (!type) return 'bg-light text-dark'
        switch (type) {
          case 'initial_balance':
            return 'bg-info text-white'
          case 'adjust':
            return 'bg-warning text-dark'
          case 'reversal':
            return 'bg-danger text-white'
          case 'cash_out':
            return 'bg-secondary text-white'
          default:
            return 'bg-light text-dark'
        }
      }
      
      const getBaseCurrencyTransactionTypeText = (type) => {
        switch (type) {
          case 'initial_balance':
            return t('eod.opening_balance')
          case 'adjust':
          case 'adjust_balance':
            return t('common.adjustment')
          case 'reversal':
            return t('common.reversal')
          case 'cash_out':
            return t('common.cash_out')
          case 'buy':
            return t('exchange.buy')
          case 'sell':
            return t('exchange.sell')
          default:
            return type
        }
      }
      
      // 解析交易描述，处理翻译键格式
      const parseTransactionDescription = (description) => {
        if (!description) return ''
        
        // 调试当前语言
        console.log(`当前语言: ${locale.value}`)
        
        // 检查是否是翻译键格式（以eod.开头的键）
        if (description.startsWith('eod.')) {
          const parts = description.split(' ')
          const translationKey = parts[0]
          const remainingParts = parts.slice(1)
          
          // 获取翻译文本 - 尝试不同的路径
          let translatedText = t(translationKey)
          console.log(`直接翻译: ${translationKey} → ${translatedText}`)
          
          // 如果直接路径失败，尝试在step5下查找
          if (translatedText === translationKey) {
            const step5Key = translationKey.replace('eod.', 'eod.step5.')
            translatedText = t(step5Key)
            console.log(`尝试step5路径: ${step5Key} → ${translatedText}`)
            
            // 如果step5路径也失败，尝试其他可能的路径
            if (translatedText === step5Key) {
              const directKey = translationKey.replace('eod.step5.', '')
              translatedText = t(directKey)
              console.log(`尝试直接路径: ${directKey} → ${translatedText}`)
            }
          }
          
          // 调试信息
          console.log(`翻译调试: ${translationKey} → ${translatedText}`)
          
          // 如果翻译成功且不是键本身，返回翻译后的文本加上剩余部分
          if (translatedText && translatedText !== translationKey) {
            const result = translatedText + (remainingParts.length > 0 ? ' ' + remainingParts.join(' ') : '')
            console.log(`翻译结果: ${description} → ${result}`)
            return result
          } else {
            console.log(`翻译失败: ${translationKey} 返回原值`)
          }
        }
        
        // 如果不是翻译键格式或翻译失败，返回原始描述
        return description
      }
      
      const getBaseCurrencyAmountClass = (amount) => {
        const numAmount = parseFloat(amount)
        return numAmount >= 0 ? 'text-success fw-bold' : 'text-danger fw-bold'
      }
      
      // 本币交易明细勾选相关方法 - 移除旧的逻辑，使用新的统一逻辑
    
    // 勾选处理方法
    const toggleTransactionSelection = (currencyCode, transaction) => {
      if (!selectedTransactions.value[currencyCode]) {
        selectedTransactions.value[currencyCode] = {}
      }
      
      const txKey = transaction.transaction_no
      if (selectedTransactions.value[currencyCode][txKey]) {
        delete selectedTransactions.value[currencyCode][txKey]
        // 如果币种下没有选中项了，删除整个币种
        if (Object.keys(selectedTransactions.value[currencyCode]).length === 0) {
          delete selectedTransactions.value[currencyCode]
        }
      } else {
        selectedTransactions.value[currencyCode][txKey] = transaction
      }
    }
    
    // 检查交易是否被选中
    const isTransactionSelected = (currencyCode, transaction) => {
      return !!(selectedTransactions.value[currencyCode] && 
                selectedTransactions.value[currencyCode][transaction.transaction_no])
    }
    
    // 清空所有选中项
    const clearAllSelections = () => {
      selectedTransactions.value = {}
    }
    
    // 本币交易的特定计算属性
    const hasBaseCurrencySelectedTransactions = computed(() => {
      return selectedTransactions.value['BASE_CURRENCY'] && 
             Object.keys(selectedTransactions.value['BASE_CURRENCY']).length > 0
    })
    
    const selectedBaseCurrencyCount = computed(() => {
      if (!selectedTransactions.value['BASE_CURRENCY']) return 0
      return Object.keys(selectedTransactions.value['BASE_CURRENCY']).length
    })
    
    const selectedBaseCurrencySum = computed(() => {
      if (!selectedTransactions.value['BASE_CURRENCY']) return 0
      let sum = 0
      console.log('计算选中交易的总和:')
      Object.values(selectedTransactions.value['BASE_CURRENCY']).forEach(tx => {
        // 使用更精确的数值处理，避免浮点数精度问题
        const amount = parseFloat(tx.amount || 0)
        console.log(`交易 ${tx.transaction_no}: ${tx.amount} (原始) → ${amount} (解析后)`)
        // 使用整数运算避免浮点数精度问题
        sum = Math.round((sum + amount) * 100) / 100
        console.log(`当前总和: ${sum}`)
      })
      // 保留两位小数精度
      const finalSum = Math.round(sum * 100) / 100
      console.log(`最终总和: ${finalSum}`)
      return finalSum
    })
    
    // 清空本币交易选择
    const clearBaseCurrencySelections = () => {
      if (selectedTransactions.value['BASE_CURRENCY']) {
        delete selectedTransactions.value['BASE_CURRENCY']
      }
    }
    
    // 【新增】全选/取消全选当前页面的交易
    const toggleAllCurrentPage = (currencyCode) => {
      const currentPageTxs = getCurrentPageTransactions(currencyCode)
      const isAllSelected = isCurrentPageAllSelected(currencyCode)
      
      if (!selectedTransactions.value[currencyCode]) {
        selectedTransactions.value[currencyCode] = {}
      }
      
      if (isAllSelected) {
        // 取消选择当前页面的所有交易
        currentPageTxs.forEach(tx => {
          delete selectedTransactions.value[currencyCode][tx.transaction_no]
        })
        // 如果币种下没有选中项了，删除整个币种
        if (Object.keys(selectedTransactions.value[currencyCode]).length === 0) {
          delete selectedTransactions.value[currencyCode]
        }
      } else {
        // 选择当前页面的所有交易
        currentPageTxs.forEach(tx => {
          selectedTransactions.value[currencyCode][tx.transaction_no] = tx
        })
      }
    }
    
    // 【新增】检查当前页面是否全部选中
    const isCurrentPageAllSelected = (currencyCode) => {
      const currentPageTxs = getCurrentPageTransactions(currencyCode)
      if (currentPageTxs.length === 0) return false
      
      if (!selectedTransactions.value[currencyCode]) return false
      
      return currentPageTxs.every(tx => 
        selectedTransactions.value[currencyCode][tx.transaction_no]
      )
    }
    
    // 格式化有符号金额
    const formatSignedAmount = (amount) => {
      const num = parseFloat(amount) || 0
      const formatted = formatAmount(Math.abs(num))
      return num >= 0 ? `+${formatted}` : `-${formatted}`
    }

    // 暴露调试函数到window对象，方便在浏览器控制台中调用
    if (typeof window !== 'undefined') {
      window.debugCurrencyDetails = debugCurrencyDetails
      console.log('🐛 调试函数已添加到window.debugCurrencyDetails，可在控制台调用')
    }
    
    // 生命周期钩子
    onMounted(() => {
      // 如果余额一致且需要自动生成收入统计，或者强制继续的情况
      if ((allMatched.value && props.autoGenerateIncomeStats) || props.forced_continue) {
        shouldShowIncomeStats.value = true
        // 自动生成收入统计
        generateIncomeStats()
      }
    })
    
    // 组件卸载时清理数据
    onUnmounted(() => {
      // 清理所有响应式数据，避免内存泄漏和null访问错误
      currencyDetails.value = {}
      selectedTransactions.value = {}
      expandedCurrency.value = []
      loadingDetails.value = null
      loadingBaseCurrencyDetails.value = null
    })
    
    // 【新增缺失的函数】
    const formatLocalAmount = (amount) => {
      return formatAmount(amount)
    }
    
    const formatForeignAmount = (amount) => {
      return formatAmount(amount)
    }
    
    const getLocalPageTotalClass = (currencyCode) => {
      const total = formatLocalPageTotal(currencyCode)
      return parseFloat(total) >= 0 ? 'text-success' : 'text-danger'
    }
    
    const getLocalTotalClass = (currencyCode) => {
      const total = formatLocalTotal(currencyCode)
      return parseFloat(total) >= 0 ? 'text-success' : 'text-danger'
    }
    
    const clearCurrencySelections = (currencyCode) => {
      if (selectedTransactions.value[currencyCode]) {
        delete selectedTransactions.value[currencyCode]
      }
    }
    
    const autoDownloadAndPrint = async () => {
      try {
        console.log('开始自动下载PDF并触发打印...')
        
        // 从manager目录下载PDF文件（传递当前语言）
        const downloadResponse = await eodAPI.downloadIncomeReport(props.eodId, {
          language: locale.value || 'zh'
        })
        
        if (downloadResponse && downloadResponse.data) {
          // 创建blob URL
          const pdfBlob = new Blob([downloadResponse.data], { type: 'application/pdf' })
          const blobUrl = window.URL.createObjectURL(pdfBlob)
          
          console.log('PDF blob URL创建成功，使用iframe方式打印...')
          
          // 使用隐藏的iframe方式直接触发打印对话框
          const iframe = document.createElement('iframe')
          iframe.style.display = 'none'  // 隐藏iframe，只显示打印对话框
          iframe.style.width = '1200px'  // 更大的尺寸以获得更好的打印预览
          iframe.style.height = '800px'
          iframe.src = blobUrl
          
          // 添加到body
          document.body.appendChild(iframe)
          
          // 监听iframe加载完成事件
          iframe.onload = function() {
            try {
              console.log('PDF已加载到隐藏iframe，触发打印对话框...')
              
              // 短延迟后触发打印，确保PDF完全加载
              setTimeout(() => {
                iframe.contentWindow.focus()
                iframe.contentWindow.print()
                console.log('浏览器打印对话框已触发')
                
                // 打印对话框关闭后清理资源
                setTimeout(() => {
                  if (iframe && iframe.parentNode) {
                    document.body.removeChild(iframe)
                  }
                  window.URL.revokeObjectURL(blobUrl)
                  console.log('PDF资源已清理')
                }, 20000) // 20秒后清理，给用户足够时间完成打印
              }, 800) // 800ms延迟确保PDF完全加载
            } catch (printError) {
              console.error('触发打印失败:', printError)
              // 清理资源
              if (iframe && iframe.parentNode) {
                document.body.removeChild(iframe)
              }
              window.URL.revokeObjectURL(blobUrl)
            }
          }
          
          iframe.onerror = function() {
            console.error('iframe PDF加载失败')
            if (iframe && iframe.parentNode) {
              document.body.removeChild(iframe)
            }
            window.URL.revokeObjectURL(blobUrl)
          }
          
        } else {
          throw new Error('下载PDF失败：响应数据为空')
        }
        
      } catch (error) {
        console.error('自动下载并打印失败:', error)
        emit('error', `自动打印失败: ${error.message}`)
      }
    }
    
    return {
      t,
      isProcessing,
      cancelReason,
      forceReason,
      forceConfirm,
      allMatched,
      matchedCount,
      mismatchedCount,
      calculateMatchRate,
      mismatchedResults,
      continueEOD,
      cancelEOD,
      forceContinue,
      formatAmount,
      formatDifference,
      formatPercentage,
      // 收入统计相关
      shouldShowIncomeStats,
      isForceContinued,
      incomeStatsGenerated,
      incomeStatsConfirmed,
      isGeneratingStats,
      isPrintingReports,
      isConfirmingStats,
      incomeReports,
      stockReports,
      // 【新增】过滤后的外币报表
      foreignIncomeReports,
      foreignStockReports,
      getBaseCurrencyCode,
      totalIncome,
      totalSpreadIncome,
      generateIncomeStats,
      confirmIncomeAndPrintReports,
      printIncomeReports,
      regenerateIncomeStats,
      showIncomeDetail,
      getBalanceChangeClass,
      getReversalAmountClass,
      getStockStatusClass,
      getStockStatusText,
      // 展开/收起相关
      showIncomeReports,
      showStockReports,
      showBaseCurrencyReports,
      toggleIncomeReports,
      toggleStockReports,
      toggleBaseCurrencyReports,
      baseCurrencyData,
      // 本币库存明细相关
      expandedBaseCurrency,
      baseCurrencyDetails,
      loadingBaseCurrencyDetails,
      toggleBaseCurrencyDetails,
      getBaseCurrencyTransactionTypeClass,
      getBaseCurrencyTransactionTypeText,
      parseTransactionDescription,
      getBaseCurrencyAmountClass,
      // 明细交易勾选相关（统一逻辑）
      selectedTransactions,
      selectedSum,
      // 币种明细展开/收起相关
      expandedCurrency,
      currencyDetails,
      loadingDetails,
      paginatedTransactions,
      pageSize,
      toggleCurrencyDetails,
      loadCurrencyDetails,
      getEodDate,
      initializePagination,
      getCurrentPageTransactions,
      needsPagination,
      getCurrentPage,
      getTotalPages,
      getTotalTransactions,
      getPaginationData,
      prevPage,
      nextPage,
      getShortTransactionNo,
      getCompactDateTime,
      formatTimeRange,
      formatRate,
      formatSignedForeignAmount,
      formatSignedAmount,
      formatLocalAmount,
      formatForeignAmount,
      formatLocalPageTotal,
      formatForeignPageTotal,
      formatLocalTotal,
      formatForeignTotal,
      getForeignPageTotalClass,
      getForeignTotalClass,
      getLocalPageTotalClass,
      getLocalTotalClass,
      getTransactionTypeClass,
      getTransactionAmountClass,
      getTransactionTypeText,
      // 新增的勾选相关功能
      isTransactionSelected,
      toggleTransactionSelection,
      toggleAllCurrentPage,
      isCurrentPageAllSelected,
      clearCurrencySelections,
      clearAllSelections,
      selectedCount,
      selectedForeignTotal,
      selectedLocalTotal,
      hasSelectedTransactions,
      hasDetailedMovements,
      getCurrencyName,
      getCurrencyNameTranslated,
      isBaseCurrencyExpanded,
      // 本币交易相关
      hasBaseCurrencySelectedTransactions,
      selectedBaseCurrencyCount,
      selectedBaseCurrencySum,
      clearBaseCurrencySelections,
      hasCriticalDifferences
    }
  }
}
</script>

<style scoped>
.step-content {
  padding: 1rem 0;
}

.compact-header {
  display: flex;
  align-items: center;
  border-bottom: 1px solid #dee2e6;
  padding-bottom: 0.5rem;
}

.compact-header .title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: #495057;
}

.stat-number {
  font-size: 1.5rem;
  font-weight: bold;
  line-height: 1;
}

.stat-label {
  font-size: 0.75rem;
  color: #6c757d;
  margin-top: 0.25rem;
}

.cursor-pointer {
  cursor: pointer;
  user-select: none;
}

.cursor-pointer:hover {
  background-color: #f8f9fa;
}

.transition-transform {
  transition: transform 0.2s ease-in-out;
}

.rotate-180 {
  transform: rotate(180deg);
}

.income-stats-section {
  margin-top: 1rem;
}

.reports-section .card {
  border: 1px solid #dee2e6;
  margin-bottom: 0;
}

.reports-section .card-header {
  background-color: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
}

.currency-flag {
  display: inline-block;
  border-radius: 2px;
}

.table th {
  border-top: none;
  font-weight: 600;
  font-size: 0.875rem;
}

.table td {
  font-size: 0.875rem;
  vertical-align: middle;
}

.card.border-danger {
  border-color: #dc3545 !important;
}

.card.border-warning {
  border-color: #ffc107 !important;
}

.alert {
  border-radius: 0.375rem;
}

.btn-sm {
  font-size: 0.875rem;
  padding: 0.25rem 0.5rem;
}

.gap-2 {
  gap: 0.5rem;
}

/* 币种明细展开/收起样式 */
.currency-row {
  cursor: pointer;
  transition: background-color 0.2s;
}

.currency-row:hover {
  background-color: #f0f8ff !important;
}

.currency-row.expanded {
  background-color: #e3f2fd !important;
}

.currency-info-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.currency-flag {
  width: 20px;
  height: 14px;
  border-radius: 2px;
  border: 1px solid #ddd;
  flex-shrink: 0;
}

.currency-details {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.currency-code {
  font-weight: 600;
  color: #333;
  font-size: 0.95em;
}

.currency-name {
  font-size: 0.85em;
  color: #6c757d;
}

.detail-arrow {
  margin-left: 8px;
  color: #666;
  transition: transform 0.3s;
  font-size: 0.8em;
}

.detail-arrow.rotated {
  transform: rotate(180deg);
}

.details-row {
  background-color: #f8f9fa !important;
}

.details-cell {
  padding: 0 !important;
}

.transaction-details-compact {
  background: #f8f9fa;
  border-radius: 6px;
  overflow: hidden;
  margin: 8px;
}

.details-header-compact {
  background: #e9ecef;
  padding: 10px 15px;
  border-bottom: 1px solid #dee2e6;
}

.details-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.detail-flag {
  width: 18px;
  height: 12px;
  border-radius: 2px;
  border: 1px solid #ddd;
  flex-shrink: 0;
}

.currency-title {
  font-weight: 600;
  color: #333;
  flex: 1;
}

.btn-collapse {
  background: none;
  border: none;
  color: #6c757d;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 3px;
  transition: all 0.2s;
}

.btn-collapse:hover {
  background: #dee2e6;
  color: #333;
}

.details-summary-compact {
  display: flex;
  gap: 15px;
  font-size: 0.9em;
}

.summary-compact {
  color: #495057;
}

.transactions-container-compact {
  max-height: 400px;
  overflow-y: auto;
  background: white;
}

.transaction-row-compact {
  border-bottom: 1px solid #f1f3f4;
  transition: background-color 0.2s;
}

.transaction-row-compact:hover {
  background-color: #f8f9fa;
}

.transaction-line {
  display: flex;
  align-items: center;
  padding: 6px 15px;
  font-size: 0.85em;
  gap: 8px;
  line-height: 1.2;
}

.tx-no {
  font-family: monospace;
  color: #6c757d;
  min-width: 70px;
}

.tx-time {
  color: #6c757d;
  min-width: 80px;
}

.tx-separator {
  color: #dee2e6;
}

.tx-type {
  min-width: 40px;
  font-weight: 500;
}

.tx-foreign {
  font-weight: 600;
  min-width: 100px;
}

.tx-rate {
  color: #6c757d;
  min-width: 60px;
}

.tx-equals {
  color: #6c757d;
}

.tx-local {
  font-weight: 500;
  min-width: 80px;
}

.tx-customer {
  color: #495057;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.amount-positive {
  color: #28a745;
}

.amount-negative {
  color: #dc3545;
}

.type-buy {
  color: #28a745;
}

.type-sell {
  color: #dc3545;
}

.pagination-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 15px;
  background: #f8f9fa;
  border-top: 1px solid #e9ecef;
  font-size: 0.85em;
}

.pagination-info {
  color: #6c757d;
}

.pagination-buttons {
  display: flex;
  gap: 5px;
}

.btn-page {
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 3px;
  padding: 4px 8px;
  cursor: pointer;
  color: #495057;
  transition: all 0.2s;
}

.btn-page:hover:not(:disabled) {
  background: #e9ecef;
  border-color: #adb5bd;
}

.btn-page:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.subtotal-row {
  background: #f8f9fa;
  border-top: 1px solid #e9ecef;
  padding: 8px 15px;
}

.subtotal-content {
  font-size: 0.9em;
  color: #495057;
}

.subtotal-content strong {
  color: #333;
}

.loading-details {
  text-align: center;
  padding: 20px;
  color: #6c757d;
}

.loading-details i {
  margin-right: 8px;
}

/* 本币交易明细勾选相关样式 */
/* 本币库存明细表格紧凑样式 */
.transaction-details .table-sm th,
.transaction-details .table-sm td {
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
  line-height: 1.3;
  vertical-align: middle;
}

/* 确保全选控件不折行 */
.form-check-label.text-nowrap {
  white-space: nowrap;
}

/* 本币库存明细表格行高与收入明细保持一致 */
.transaction-details .table-sm tbody tr {
  height: 2.5rem;
}

/* 确保本币库存明细表格与收入明细表格完全一致的样式 */
.transaction-details .table-hover tbody tr:hover {
  background-color: #f0f8ff !important;
}

/* 选中行的样式 */
.transaction-details .selected-row {
  background-color: #e3f2fd !important;
}

/* 本币交易明细勾选相关样式 */
.calculation-summary {
  border: 1px solid #e9ecef;
  border-radius: 0.375rem;
  background: #f8f9fa;
  padding: 1rem;
  margin-bottom: 1rem;
}

.summary-box {
  border: 1px solid #dee2e6;
  border-radius: 0.375rem;
  background: white;
  padding: 0.75rem;
}

.summary-header {
  display: flex;
  align-items: center;
  margin-bottom: 0.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #e9ecef;
}

.summary-title {
  font-weight: 600;
  color: #495057;
}

.summary-content {
  font-size: 0.875rem;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.25rem;
}

.summary-row:last-child {
  margin-bottom: 0;
}

.summary-label {
  color: #6c757d;
  font-weight: 500;
}

.summary-amount {
  font-weight: 600;
  font-family: monospace;
}

.summary-count {
  color: #6c757d;
  font-size: 0.8rem;
}

.selected-row {
  background-color: rgba(13, 110, 253, 0.1) !important;
  border-left: 3px solid #0d6efd;
}

.selected-row:hover {
  background-color: rgba(13, 110, 253, 0.15) !important;
}

.form-check {
  margin-bottom: 0;
}

.form-check-input {
  margin-top: 0.1rem;
}

.form-check-label {
  font-size: 0.875rem;
  color: #6c757d;
  margin-left: 0.25rem;
}

/* 勾选框样式 */
.checkbox-container {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  position: relative;
}

.checkbox-container input[type="checkbox"] {
  appearance: none;
  width: 16px;
  height: 16px;
  border: 2px solid #dee2e6;
  border-radius: 3px;
  background: white;
  cursor: pointer;
  position: relative;
  transition: all 0.2s;
}

.checkbox-container input[type="checkbox"]:checked {
  background: #007bff;
  border-color: #007bff;
}

.checkbox-container input[type="checkbox"]:checked::before {
  content: "✓";
  position: absolute;
  top: -1px;
  left: 1px;
  color: white;
  font-size: 12px;
  font-weight: bold;
}

.checkbox-container:hover input[type="checkbox"] {
  border-color: #007bff;
}

.checkbox-label {
  font-size: 0.85em;
  color: #495057;
  user-select: none;
}

.transaction-control-row {
  padding: 8px 15px;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
}

.transaction-selected {
  background-color: #e3f2fd !important;
}

.transaction-selected:hover {
  background-color: #bbdefb !important;
}

/* 动态勾选汇总区域样式 */
.selected-summary-compact {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 10px;
  padding: 8px 12px;
  background: #e3f2fd;
  border-radius: 4px;
  font-size: 0.85em;
  border-left: 4px solid #2196f3;
}

.selected-divider {
  width: 1px;
  height: 16px;
  background: #dee2e6;
  margin: 0 5px;
}

.selected-label {
  font-weight: 600;
  color: #1976d2;
}

.selected-count {
  color: #1976d2;
  font-weight: 500;
}

.selected-foreign {
  color: #495057;
}

.selected-local {
  color: #495057;
}

.btn-clear-selections {
  background: none;
  border: none;
  color: #dc3545;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 3px;
  transition: all 0.2s;
  font-size: 0.8em;
}

.btn-clear-selections:hover {
  background: #f8d7da;
  color: #721c24;
}

/* 压缩的合计计算区样式 */
.calculation-summary-compact {
  border: 1px solid #e9ecef;
  border-radius: 0.375rem;
  background: #f8f9fa;
  padding: 0.75rem 1rem;
}

.selected-summary-inline {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  color: #495057;
}

.selected-summary-inline .btn {
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  line-height: 1;
}
</style> 

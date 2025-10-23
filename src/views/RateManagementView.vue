<template>
  <!-- App角色专用手机端界面 -->
  <div v-if="isAppRole" class="app-rates-view">
    <div class="container-fluid py-3">
      <!-- 页面头部 -->
      <div class="row mb-3">
        <div class="col-12">
          <div class="d-flex justify-content-between align-items-center">
            <h4 class="mb-0 text-primary">
              <i class="fas fa-chart-line me-2"></i>
              汇率发布
            </h4>
            <div class="text-muted small">
              {{ formatDate(new Date()) }}
            </div>
          </div>
        </div>
      </div>

      <!-- 汇率发布状态 -->
      <div class="row mb-3">
        <div class="col-12">
          <div class="card border-0 shadow-sm">
            <div class="card-body p-3">
              <div class="d-flex align-items-center justify-content-between">
                <div class="d-flex align-items-center">
                  <div class="status-icon bg-success me-3">
                    <i class="fas fa-check text-white"></i>
                  </div>
                  <div>
                    <div class="status-title">发布状态</div>
                    <div class="status-subtitle">
                      {{ dailyRatesPublished ? '已发布' : '未发布' }}
                    </div>
                  </div>
                </div>
                <div class="badge bg-primary">
                  {{ rates.length }} 个币种
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 快速操作按钮 -->
      <div class="row mb-3">
        <div class="col-6">
          <button 
            class="btn btn-success w-100" 
            @click="publishDailyRates"
            :disabled="publishing"
          >
            <i class="fas fa-paper-plane me-2" :class="{ 'fa-spin': publishing }"></i>
            发布汇率
          </button>
        </div>
        <div class="col-6">
          <button 
            class="btn btn-outline-primary w-100" 
            @click="showSetTopBoxModal"
            :disabled="!dailyRatesPublished"
          >
            <i class="fas fa-tv me-2"></i>
            机顶盒
          </button>
        </div>
      </div>

      <!-- 汇率列表 -->
      <div class="row mb-3" v-if="rates.length > 0">
        <div class="col-12">
          <div class="card border-0 shadow-sm">
            <div class="card-header bg-light py-2">
              <h6 class="mb-0">
                <i class="fas fa-coins text-warning me-2"></i>
                当前汇率
              </h6>
            </div>
            <div class="card-body p-0">
              <div class="rate-list">
                <div 
                  v-for="rate in rates.slice(0, 6)" 
                  :key="rate.id" 
                  class="rate-item"
                >
                  <div class="rate-currency">
                    <CurrencyFlag 
                      :code="rate.flag_code || rate.currency_code" 
                      :custom-filename="rate.custom_flag_filename"
                      class="me-2" 
                    />
                    {{ rate.currency_code }}
                  </div>
                  <div class="rate-values">
                    <div class="rate-buy">{{ rate.buy_rate }}</div>
                    <div class="rate-sell">{{ rate.sell_rate }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 发布记录 -->
      <div class="row mb-3">
        <div class="col-12">
          <div class="card border-0 shadow-sm">
            <div class="card-header bg-light py-2">
              <h6 class="mb-0">
                <i class="fas fa-history text-info me-2"></i>
                发布记录
              </h6>
            </div>
            <div class="card-body p-0">
              <div class="publish-list">
                <div 
                  v-for="record in publishRecords.slice(0, 3)" 
                  :key="record.id" 
                  class="publish-item"
                >
                  <div class="publish-time">
                    {{ formatDateTime(record.publish_time) }}
                  </div>
                  <div class="publish-info">
                    {{ record.currency_count }} 个币种
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 机顶盒模态框 -->
    <div class="modal fade" id="setTopBoxModal" tabindex="-1">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              <i class="fas fa-tv me-2"></i>
              机顶盒访问
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body text-center">
            <div class="qr-code-container mb-3">
              <div id="qrCode"></div>
            </div>
            <div class="access-link mb-3">
              <label class="form-label">访问链接：</label>
              <div class="input-group">
                <input 
                  type="text" 
                  class="form-control" 
                  :value="setTopBoxUrl" 
                  readonly
                >
                <button 
                  class="btn btn-outline-primary" 
                  @click="copySetTopBoxUrl"
                >
                  <i class="fas fa-copy"></i>
                </button>
              </div>
            </div>
            <div class="access-info">
              <p class="text-muted small">
                <i class="fas fa-info-circle me-1"></i>
                扫描二维码或点击链接访问机顶盒显示页面
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- App角色底部Tab导航 -->

  </div>

  <!-- 原有桌面端界面 -->
  <div v-else class="container-fluid py-4">
    <div class="row">
      <div class="col-12">
        <div class="d-flex justify-content-between align-items-center mb-4">
          <h2 class="page-title-bold">
            <font-awesome-icon :icon="['fas', 'chart-line']" class="me-2" />
            {{ $t('rates.today_rates_management') }}
          </h2>
          <div class="text-muted">
            <small>{{ formatDate(new Date()) }}</small>
          </div>
        </div>

        <!-- Tab导航 -->
        <ul class="nav nav-tabs mb-4" id="rateManagementTabs" role="tablist">
          <li class="nav-item" role="presentation">
            <button 
              class="nav-link active" 
              id="rate-management-tab" 
              data-bs-toggle="tab" 
              data-bs-target="#rate-management-pane" 
              type="button" 
              role="tab"
            >
              <font-awesome-icon icon="fa-solid fa-coins" class="me-2" />
              {{ $t('rates.rate_management') }}
            </button>
          </li>
          <li class="nav-item" role="presentation">
            <button 
              class="nav-link" 
              id="publish-records-tab" 
              data-bs-toggle="tab" 
              data-bs-target="#publish-records-pane" 
              type="button" 
              role="tab"
              @click="loadPublishRecords"
            >
              <font-awesome-icon icon="fa-solid fa-history" class="me-2" />
              {{ $t('rates.publish_records') }}
              <span v-if="pagination.total > 0" class="badge bg-primary ms-2">{{ pagination.total }}</span>
            </button>
          </li>
          <li class="nav-item" role="presentation">
            <button 
              class="nav-link" 
              id="denomination-rates-tab" 
              data-bs-toggle="tab" 
              data-bs-target="#denomination-rates-pane" 
              type="button" 
              role="tab"
            >
              <font-awesome-icon icon="fa-solid fa-layer-group" class="me-2" />
              {{ $t('rates.denomination_rates') }}
            </button>
          </li>
        </ul>

        <!-- Tab内容 -->
        <div class="tab-content" id="rateManagementTabsContent">
          
          <!-- 汇率管理Tab -->
          <div class="tab-pane fade show active" id="rate-management-pane" role="tabpanel">
            <!-- 操作按钮 -->
            <div class="row mb-4">
              <div class="col-md-12">
                <div class="d-flex flex-wrap gap-2 align-items-center">
                  <button 
                    class="btn btn-success" 
                    @click="publishDailyRates"
                    :disabled="publishing"
                  >
                    <font-awesome-icon icon="fa-solid fa-calendar-plus" :spin="publishing" class="me-1" />
                    {{ $t('rates.select_exchangeable_currencies') }}
                  </button>
                  <button 
                    class="btn btn-outline-primary" 
                    @click="showAddCurrencyModal"
                    :disabled="!dailyRatesPublished"
                  >
                    <font-awesome-icon icon="fa-solid fa-plus" class="me-1" />
                    {{ $t('rates.add_currency') }}
                  </button>

                  <div class="ms-auto d-flex gap-2">
                    <button 
                      class="btn btn-info" 
                      @click="showThemeModal"
                      :disabled="!dailyRatesPublished || rates.length === 0"
                    >
                      <font-awesome-icon icon="fa-solid fa-palette" class="me-1" />
                      {{ $t('rates.apply_publish') }}
                    </button>
                    <button 
                      class="btn btn-outline-warning btn-sm"
                      @click="clearPublishCache"
                      :disabled="clearingCache"
                      title="清除发布缓存（调试用）"
                    >
                      <font-awesome-icon icon="fa-solid fa-trash-alt" :spin="clearingCache" class="me-1" />
                      {{ $t('rates.clear_cache') }}
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- 状态提示 -->
            <div v-if="!dailyRatesPublished" class="alert alert-warning">
              <font-awesome-icon icon="fa-solid fa-info-circle" class="me-2" />
              {{ $t('rates.rates_not_initialized') }}
            </div>

            <!-- 汇率列表 -->
            <div class="row" v-if="dailyRatesPublished">
              <div class="col-md-8">
                <div class="card">
                  <div class="card-header d-flex justify-content-between align-items-center">
                    <h5 class="mb-0">
                      {{ $t('rates.today_rates_list') }} 
                      <small class="text-muted">({{ $t('rates.draggable_sort') }})</small>
                    </h5>
                    <div class="text-muted small">
                      {{ $t('rates.last_updated') }}: {{ updateTime }}
                    </div>
                  </div>
                  <div class="card-body">
                    <div v-if="rates.length === 0" class="text-center text-muted py-4">
                      <font-awesome-icon icon="fa-solid fa-coins" size="2x" class="mb-2 opacity-50" />
                      <p>{{ $t('rates.no_rate_data') }}</p>
                    </div>
                    <div v-else>
                      <!-- 批量操作工具栏 -->
                      <div class="mb-3 p-3 border rounded bg-light">
                        <div class="row align-items-center">
                          <div class="col-auto">
                            <input 
                              type="checkbox" 
                              id="selectAll"
                              v-model="selectAll"
                              @change="toggleSelectAll"
                              style="width: 16px; height: 16px; border: 1px solid #ccc; background: white; margin-right: 8px;"
                            />
                            <label for="selectAll">
                              {{ $t('rates.select_all') }}
                            </label>
                          </div>
                          <div class="col-auto">
                            <button 
                              class="btn btn-success btn-sm me-2"
                              @click="batchSave"
                              :disabled="selectedCurrencies.length === 0 || batchSaving"
                            >
                              <font-awesome-icon 
                                icon="fa-solid fa-save" 
                                :spin="batchSaving"
                                class="me-1"
                              />
                              {{ batchSaving ? $t('rates.saving') : $t('rates.save') }}
                            </button>
                            <button 
                              class="btn btn-info btn-sm"
                              @click="copyAllLastRates"
                              :disabled="copyingAll"
                              :title="$t('rates.copy_all_last_rates')"
                            >
                              <font-awesome-icon 
                                icon="fa-solid fa-copy" 
                                :spin="copyingAll"
                                class="me-1"
                              />
                              {{ copyingAll ? $t('rates.copying_all') : $t('rates.copy_last_rates') }}
                            </button>
                          </div>
                          <div class="col-auto text-muted small" v-if="selectedCurrencies.length > 0">
                            {{ $t('rates.selected_count', {count: selectedCurrencies.length}) }}
                          </div>
                        </div>
                      </div>
                      
                      <div class="table-responsive">
                        <table class="table table-striped table-bordered table-hover table-sm">
                          <thead>
                            <tr>
                              <th style="width: 3%">{{ $t('rates.select') }}</th>
                              <th style="width: 0.5%">{{ $t('rates.sequence_number') }}</th>
                              <th style="width: 3%">{{ $t('rates.sort_order') }}</th>
                              <th style="width: 22%; text-align: center;">{{ $t('rates.currency') }}</th>
                              <th style="width: 12%">{{ $t('rates.buy_rate') }}</th>
                              <th style="width: 12%">{{ $t('rates.sell_rate') }}</th>
                              <th style="width: 47.5%">{{ $t('rates.operations') }}</th>
                            </tr>
                          </thead>
                          <draggable
                            v-model="rates"
                            tag="tbody"
                            handle=".drag-handle"
                            :animation="150"
                            @end="onSortEnd"
                            item-key="currency_code"
                          >
                            <template #item="{element: rate, index}">
                              <tr 
                                v-if="rate && rate.currency_code"
                                :key="rate.currency_code"
                                :data-index="index"
                                class="rate-row compact-row"
                              >
                                <td class="text-center align-middle">
                                  <input 
                                    type="checkbox" 
                                    :id="`currency-${rate.currency_code}`"
                                    v-model="selectedCurrencies"
                                    :value="rate.currency_code"
                                    @change="updateSelectAll"
                                    style="width: 16px; height: 16px; border: 1px solid #ccc; background: white;"
                                  />
                                </td>
                                <td class="text-center align-middle">
                                  <span class="text-muted small">{{ index + 1 }}</span>
                                </td>
                                <td class="text-center align-middle">
                                  <div class="drag-handle" style="cursor: move;">
                                    <font-awesome-icon icon="fa-solid fa-grip-vertical" class="text-muted" />
                                  </div>
                                </td>
                                <td class="align-middle">
                                  <div class="d-flex align-items-center">
                                    <CurrencyFlag 
                                      :code="rate.flag_code || rate.currency_code || 'USD'"
                                      :custom-filename="rate.custom_flag_filename"
                                      class="me-2"
                                    />
                                    {{ rate.currency_code }} - {{ getCurrencyNameTranslated(rate.currency_code, rate.currency_name, rate.custom_flag_filename) }}
                                  </div>
                                </td>
                                <td class="align-middle">
                                  <input
                                    v-if="rate.editMode || selectedCurrencies.includes(rate.currency_code)"
                                    type="number"
                                    class="form-control form-control-sm"
                                    step="0.0001"
                                    :value="editValues[rate.currency_code]?.buyRate || (rate?.buy_rate || 0)"
                                    @input="(e) => handleRateChange(rate.currency_code, 'buyRate', e.target.value)"
                                  />
                                  <template v-else>
                                    {{ formatRateValue(rate?.buy_rate || 0) }}
                                  </template>
                                </td>
                                <td class="align-middle">
                                  <input
                                    v-if="rate.editMode || selectedCurrencies.includes(rate.currency_code)"
                                    type="number"
                                    class="form-control form-control-sm"
                                    step="0.0001"
                                    :value="editValues[rate.currency_code]?.sellRate || (rate?.sell_rate || 0)"
                                    @input="(e) => handleRateChange(rate.currency_code, 'sellRate', e.target.value)"
                                  />
                                  <template v-else>
                                    {{ formatRateValue(rate?.sell_rate || 0) }}
                                  </template>
                                </td>
                                <td class="align-middle">
                                  <div class="d-flex align-items-center gap-4 flex-wrap">
                                    <button 
                                      v-if="rate.editMode"
                                      class="btn btn-success btn-sm"
                                      @click="saveRateChanges(rate.currency_code)"
                                      :disabled="saving === rate.currency_code"
                                      :title="$t('rates.save_title')"
                                    >
                                      <font-awesome-icon icon="fa-solid fa-check" :spin="saving === rate.currency_code" />
                                    </button>
                                    <button 
                                      v-if="!rate.editMode"
                                      class="btn btn-primary btn-sm"
                                      @click="toggleEditMode(rate.currency_code)"
                                      :title="$t('rates.edit_title')"
                                    >
                                      <font-awesome-icon icon="fa-solid fa-edit" />
                                    </button>
                                    <!-- 复制最近一次汇率按钮 -->
                                    <button 
                                      v-if="!rate.editMode"
                                      class="btn btn-outline-info btn-sm"
                                      @click="copyLastRate(rate.currency_code)"
                                      :title="$t('rates.copy_last_rate')"
                                      :disabled="copying === rate.currency_code"
                                    >
                                      <font-awesome-icon icon="fa-solid fa-copy" :spin="copying === rate.currency_code" />
                                    </button>
                                    <button 
                                      v-if="rate.editMode"
                                      class="btn btn-outline-secondary btn-sm"
                                      @click="toggleEditMode(rate.currency_code)"
                                      :title="$t('rates.cancel_title')"
                                    >
                                      <font-awesome-icon icon="fa-solid fa-times" />
                                    </button>
                                    <button 
                                      v-if="!rate.editMode"
                                      class="btn btn-outline-secondary btn-sm text-muted"
                                      @click="removeCurrency(rate.currency_code)"
                                      :title="$t('rates.delete_title')"
                                      style="border-color: #dee2e6; color: #6c757d;"
                                    >
                                      <font-awesome-icon icon="fa-solid fa-trash" />
                                    </button>
                                    
                                    <!-- 发布状态指示器 -->
                                    <div 
                                      v-if="!rate.editMode" 
                                      class="d-flex align-items-center ms-2"
                                    >
                                      <!-- 批量保存状态：显示绿色勾号 -->
                                      <div v-if="rate.batchSaved" class="d-flex align-items-center">
                                        <font-awesome-icon 
                                          icon="fa-solid fa-check-circle"
                                          class="text-success me-2"
                                          :title="$t('rates.batch_saved')"
                                        />
                                        <div class="small text-muted rate-update-info-compact">
                                          <span class="text-success">
                                            {{ $t('rates.saved_by') }} {{ formatDateTime(rate.batchSavedTime) }} {{ rate.batchSavedBy }}
                                          </span>
                                        </div>
                                      </div>
                                      
                                      <!-- 已发布状态：显示绿色勾号 -->
                                      <div v-else-if="rate.isPublished" class="d-flex align-items-center">
                                        <font-awesome-icon 
                                          icon="fa-solid fa-check-circle"
                                          class="text-success me-2"
                                          title="今日已发布"
                                        />
                                        <div class="small text-muted rate-update-info-compact">
                                          <span class="text-success">
                                            {{ $t('rates.modified_by') }} {{ formatDateTime(rate.last_publish_time) }} {{ rate.publisher_name }}
                                          </span>
                                        </div>
                                      </div>
                                      
                                      <!-- 未发布状态：显示黄色时钟图标 -->
                                      <div v-else class="d-flex align-items-center">
                                        <font-awesome-icon 
                                          icon="fa-solid fa-clock"
                                          class="text-warning spinning-clock me-2"
                                          :title="$t('rates.waiting_publish')"
                                        />
                                        <div class="small text-muted">
                                          <span class="text-warning">
                                            {{ $t('rates.waiting_publish') }}
                                          </span>
                                        </div>
                                      </div>
                                    </div>
                                  </div>
                                </td>
                              </tr>
                            </template>
                          </draggable>
                        </table>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- 右侧发布信息和趋势图 -->
              <div class="col-md-4">
                <!-- 当日发布状态 -->
                <div class="card mb-4">
                  <div class="card-header">
                    <h6 class="mb-0">
                      <font-awesome-icon icon="fa-solid fa-calendar-day" class="me-2" />
                      {{ $t('rates.today_publish_status') }}
                    </h6>
                  </div>
                  <div class="card-body">
                    <div class="row">
                      <div class="col-6">
                        <div class="text-center">
                          <div class="fs-4 fw-bold text-primary">{{ validRates.length }}</div>
                          <small class="text-muted">{{ $t('reports.currency_count') }}</small>
                        </div>
                      </div>
                      <div class="col-6">
                        <div class="text-center">
                          <div class="fs-4 fw-bold" :class="publishedCount > 0 ? 'text-success' : 'text-warning'">
                            {{ publishedCount }}
                          </div>
                          <small class="text-muted">{{ $t('rates.saved_count') }}</small>
                        </div>
                      </div>
                    </div>
                    
                    <!-- 发布状态指示 -->
                    <div class="mt-3">
                      <div v-if="!lastPublishInfo && publishedCount > 0" class="alert alert-danger alert-sm">
                        <font-awesome-icon icon="fa-solid fa-exclamation-triangle" class="me-2" />
                        <strong>{{ $t('common.warning') }}:</strong> {{ $t('rates.rates_edited_not_published') }}
                      </div>
                      <div v-else-if="publishedCount === 0" class="alert alert-info alert-sm">
                        <font-awesome-icon icon="fa-solid fa-info-circle" class="me-2" />
                        {{ $t('rates.please_edit_and_publish') }}
                      </div>
                      <div v-else class="alert alert-success alert-sm">
                        <font-awesome-icon icon="fa-solid fa-check-circle" class="me-2" />
                        {{ $t('rates.published_success') }}
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- 汇率趋势图 -->
                <div class="card mb-3">
                  <div class="card-header">
                    <h5 class="mb-0">{{ $t('rates.rate_trends') }}</h5>
                  </div>
                  <div class="card-body">
                    <div class="mb-3">
                      <label for="trend-currency" class="form-label">{{ $t('rates.select_currency') }}</label>
                      <CurrencySelect
                        id="trend-currency"
                        v-model="selectedCurrencyCode"
                        :currencies="validRates"
                        :api-endpoint="'/system/currencies'"
                        @change="handleTrendCurrencyChange"
                        class="w-100"
                      />
                    </div>
                    <AsyncChart
                      ref="rateChart"
                      :chart-data="chartData"
                      :chart-options="chartOptions"
                      :loading-delay="600"
                      height="300px"
                      :show-toolbar="true"
                      :auto-refresh="false"
                      @chart-ready="onChartReady"
                      @chart-error="onChartError"
                      @chart-refresh="onChartRefresh"
                    />
                  </div>
                </div>

                <!-- 最新发布信息 -->
                <div class="card" v-if="lastPublishInfo">
                  <div class="card-header">
                    <h6 class="mb-0">
                      <font-awesome-icon icon="fa-solid fa-broadcast-tower" class="me-2" />
                      {{ $t('rates.latest_publish') }}
                    </h6>
                  </div>
                  <div class="card-body">
                    <div class="small">
                      <div class="mb-2">
                        <strong>{{ $t('rates.theme_label') }}:</strong> 
                        <span :class="lastPublishInfo.theme === 'light' ? 'text-warning' : 'text-dark'">
                          <font-awesome-icon :icon="lastPublishInfo.theme === 'light' ? 'fa-solid fa-sun' : 'fa-solid fa-moon'" class="me-1" />
                          {{ lastPublishInfo.theme === 'light' ? $t('rates.theme_light') : $t('rates.theme_dark') }}
                        </span>
                      </div>
                      <div class="mb-2">
                        <strong>{{ $t('rates.publish_time_label') }}:</strong> {{ formatDateTime(lastPublishInfo.publishedAt) }}
                      </div>
                      <div class="mb-2">
                        <strong>{{ $t('rates.publish_records_count') }}:</strong> 
                        <span class="badge bg-primary">{{ pagination.total }}</span>{{ $t('rates.count_suffix') }}
                      </div>

                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 发布记录Tab -->
          <div class="tab-pane fade" id="publish-records-pane" role="tabpanel">
            <div class="card">
              <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="mb-0">
                  <font-awesome-icon icon="fa-solid fa-history" class="me-2" />
                  {{ $t('rates.rate_publish_records') }}
                </h5>
                                  <button class="btn btn-primary btn-sm" @click="loadPublishRecords">
                    <font-awesome-icon icon="fa-solid fa-refresh" class="me-1" />
                    {{ $t('rates.refresh') }}
                  </button>
              </div>
              <div class="card-body">
                <div v-if="publishRecordsLoading" class="text-center py-4">
                  <font-awesome-icon icon="fa-solid fa-spinner" spin size="2x" class="mb-2" />
                  <p>{{ $t('rates.loading_publish_records') }}</p>
                </div>
                <div v-else-if="pagination.total === 0" class="text-center text-muted py-4">
                  <font-awesome-icon icon="fa-solid fa-archive" size="2x" class="mb-2 opacity-50" />
                  <p>{{ $t('rates.no_publish_records') }}</p>
                </div>
                <div v-else>
                  <div class="table-responsive">
                    <table class="table table-hover">
                      <thead>
                        <tr>
                          <th style="width: 40px;"></th> <!-- 展开/折叠图标列 -->
                          <th>{{ $t('rates.publish_time') }}</th>
                          <th>{{ $t('rates.publisher') }}</th>
                          <th>{{ $t('rates.currency_count') }}</th>
                          <th>{{ $t('rates.theme') }}</th>
                          <th>{{ $t('rates.notes') }}</th>
                          <th>{{ $t('rates.actions') }}</th>
                        </tr>
                      </thead>
                      <tbody>
                        <!-- 按日期分组的树形结构 -->
                        <template v-for="dateGroup in groupedPublishRecords" :key="dateGroup.date">
                          <!-- 日期分组节点（父节点） -->
                          <tr class="table-secondary date-group-row" @click="toggleDateExpansion(dateGroup.date)" style="cursor: pointer;">
                            <td class="text-center">
                              <font-awesome-icon 
                                :icon="isDateExpanded(dateGroup.date) ? 'fa-solid fa-chevron-down' : 'fa-solid fa-chevron-right'" 
                                class="text-muted"
                              />
                            </td>
                            <td colspan="6" class="fw-bold">
                              <font-awesome-icon icon="fa-solid fa-calendar-day" class="me-2 text-primary" />
                              {{ formatDate(dateGroup.records[0].publish_time) }}
                              <span class="badge bg-info ms-2">{{ dateGroup.records.length }} {{ $t('rates.records_count') }}</span>
                            </td>
                          </tr>
                          
                          <!-- 该日期下的发布记录（子节点） -->
                          <template v-if="isDateExpanded(dateGroup.date)">
                            <tr v-for="record in dateGroup.records" :key="record.id" class="table-light child-record-row">
                              <td class="text-center">
                                <font-awesome-icon icon="fa-solid fa-clock" class="text-muted small" />
                              </td>
                              <td class="ps-4">
                                <small class="text-muted">{{ formatTime(record.publish_time) }}</small>
                              </td>
                              <td>{{ record.publisher_name }}</td>
                              <td>
                                <span class="badge bg-primary">{{ record.total_currencies }}</span>
                              </td>
                              <td>
                                <span :class="record.publish_theme === 'light' ? 'text-warning' : 'text-dark'">
                                  <font-awesome-icon :icon="record.publish_theme === 'light' ? 'fa-solid fa-sun' : 'fa-solid fa-moon'" class="me-1" />
                                  {{ record.publish_theme === 'light' ? $t('rates.theme_light') : $t('rates.theme_dark') }}
                                </span>
                              </td>
                              <td>{{ record.notes || '-' }}</td>
                              <td>
                                <button 
                                  class="btn btn-outline-primary btn-sm"
                                  @click="viewPublishRecord(record.id)"
                                >
                                  <font-awesome-icon icon="fa-solid fa-eye" class="me-1" />
                                  {{ $t('rates.view_details') }}
                                </button>
                              </td>
                            </tr>
                          </template>
                        </template>
                      </tbody>
                    </table>
                  </div>
                  
                  <!-- 分页控件 -->
                  <div v-if="pagination.total_pages > 1" class="d-flex justify-content-between align-items-center mt-3">
                    <div class="text-muted small">
                      {{ $t('rates.pagination_info', { total: pagination.total, current: pagination.current_page, totalPages: pagination.total_pages }) }}
                    </div>
                    <nav aria-label="发布记录分页">
                      <ul class="pagination pagination-sm mb-0">
                        <li class="page-item" :class="{ disabled: pagination.current_page === 1 }">
                          <button class="page-link" @click="previousPage" :disabled="pagination.current_page === 1">
                            <font-awesome-icon icon="fa-solid fa-chevron-left" />
                          </button>
                        </li>
                        
                        <!-- 显示页码 -->
                        <li v-for="page in getVisiblePages()" :key="page" class="page-item" :class="{ active: page === pagination.current_page, disabled: page === '...' }">
                          <button v-if="page === '...'" class="page-link" disabled>
                            {{ page }}
                          </button>
                          <button v-else class="page-link" @click="goToPage(page)">
                            {{ page }}
                          </button>
                        </li>
                        
                        <li class="page-item" :class="{ disabled: pagination.current_page === pagination.total_pages }">
                          <button class="page-link" @click="nextPage" :disabled="pagination.current_page === pagination.total_pages">
                            <font-awesome-icon icon="fa-solid fa-chevron-right" />
                          </button>
                        </li>
                      </ul>
                    </nav>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 面值汇率Tab -->
          <div class="tab-pane fade" id="denomination-rates-pane" role="tabpanel">
            <div class="card">
              <div class="card-header">
                <h5 class="mb-0">
                  <font-awesome-icon icon="fa-solid fa-layer-group" class="me-2" />
                  {{ $t('rates.denomination_rates') }}
                </h5>
              </div>
              <div class="card-body">
                <DenominationRateManager />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 发布记录详情弹窗 -->
    <div class="modal fade" id="recordDetailModal" tabindex="-1">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              <font-awesome-icon icon="fa-solid fa-file-lines" class="me-2" />
              {{ $t('rates.publish_record_details') }}
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body" v-if="selectedRecord">
            <div class="row mb-3">
              <div class="col-md-6">
                <strong>{{ $t('rates.publish_time') }}:</strong> {{ formatDateTime(selectedRecord.publish_time) }}
              </div>
              <div class="col-md-6">
                <strong>{{ $t('rates.publisher') }}:</strong> {{ selectedRecord.publisher_name }}
              </div>
            </div>
            <div class="row mb-3">
              <div class="col-md-6">
                <strong>{{ $t('rates.currency_count') }}:</strong> {{ selectedRecord.total_currencies }}
              </div>
              <div class="col-md-6">
                <strong>{{ $t('rates.theme') }}:</strong> {{ selectedRecord.publish_theme === 'light' ? $t('rates.theme_light') : $t('rates.theme_dark') }}
              </div>
            </div>
            <div v-if="selectedRecord.notes" class="mb-3">
              <strong>{{ $t('rates.notes') }}:</strong> {{ selectedRecord.notes }}
            </div>
            
            <h6 class="mb-3">
              <font-awesome-icon icon="fa-solid fa-list" class="me-2" />
              {{ $t('rates.exchange_rates_details') }}
            </h6>
            <div class="table-responsive">
              <table class="table table-sm table-bordered">
                <thead class="table-light">
                  <tr>
                    <th>{{ $t('rates.currency') }}</th>
                    <th>{{ $t('rates.buy_rate_label') }}</th>
                    <th>{{ $t('rates.sell_rate_label') }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="detail in selectedRecord.details" :key="detail.currency_id">
                    <td>
                      <div class="d-flex align-items-center">
                        <CurrencyFlag 
                          :code="detail.flag_code || detail.currency_code || 'USD'"
                          :custom-filename="detail.custom_flag_filename"
                          class="me-2" 
                        />
                        {{ detail.currency_code }} - {{ getCurrencyNameTranslated(detail.currency_code, detail.currency_name, detail.custom_flag_filename) }}
                      </div>
                    </td>
                    <td>{{ formatRateValue(detail?.buy_rate) }}</td>
                    <td>{{ formatRateValue(detail?.sell_rate) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">{{ $t('common.close') }}</button>
            <button type="button" class="btn btn-primary" @click="copyRecordRates">
              <font-awesome-icon icon="fa-solid fa-copy" class="me-1" />
              {{ $t('rates.apply_this_rate') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 主题选择弹窗 -->
    <div class="modal fade" id="themeModal" tabindex="-1">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              <font-awesome-icon icon="fa-solid fa-palette" class="me-2" />
              {{ $t('rates.publish_modal_title') }}
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label">{{ $t('rates.select_display_theme') }}</label>
              <div class="d-flex gap-3 mt-2">
                <div class="form-check">
                  <input 
                    class="form-check-input" 
                    type="radio" 
                    id="theme-light" 
                    value="light"
                    v-model="selectedTheme"
                  >
                  <label class="form-check-label" for="theme-light">
                    <font-awesome-icon icon="fa-solid fa-sun" class="me-1" />
                    {{ $t('rates.theme_light') }}
                  </label>
                </div>
                <div class="form-check">
                  <input 
                    class="form-check-input" 
                    type="radio" 
                    id="theme-dark" 
                    value="dark"
                    v-model="selectedTheme"
                  >
                  <label class="form-check-label" for="theme-dark">
                    <font-awesome-icon icon="fa-solid fa-moon" class="me-1" />
                    {{ $t('rates.theme_dark') }}
                  </label>
                </div>
              </div>
            </div>
            <div class="mb-3">
              <label class="form-label">{{ $t('rates.select_display_language') }}</label>
              <div class="d-flex gap-3 mt-2">
                <div class="form-check">
                  <input 
                    class="form-check-input" 
                    type="radio" 
                    id="lang-zh" 
                    value="zh"
                    v-model="selectedLanguage"
                  >
                  <label class="form-check-label" for="lang-zh">
                    中文
                  </label>
                </div>
                <div class="form-check">
                  <input 
                    class="form-check-input" 
                    type="radio" 
                    id="lang-en" 
                    value="en"
                    v-model="selectedLanguage"
                  >
                  <label class="form-check-label" for="lang-en">
                    English
                  </label>
                </div>
                <div class="form-check">
                  <input 
                    class="form-check-input" 
                    type="radio" 
                    id="lang-th" 
                    value="th"
                    v-model="selectedLanguage"
                  >
                  <label class="form-check-label" for="lang-th">
                    ไทย
                  </label>
                </div>
              </div>
            </div>
            <div class="mb-3">
              <label class="form-label">{{ $t('rates.display_config_optional') }}</label>
              <div class="row">
                <div class="col-lg-6 col-md-12">
                  <label for="items-per-page" class="form-label">{{ $t('rates.items_per_page') }}</label>
                  <input 
                    type="number" 
                    id="items-per-page"
                    class="form-control" 
                    v-model.number="displayConfig.itemsPerPage" 
                    min="6" 
                    max="20"
                    placeholder="12"
                  >
                  <div class="form-text">{{ $t('rates.rows_recommendation') }}</div>
                </div>
                <div class="col-lg-6 col-md-12">
                  <label for="refresh-interval" class="form-label">{{ $t('rates.refresh_interval_seconds') }}</label>
                  <input 
                    type="number" 
                    id="refresh-interval"
                    class="form-control" 
                    v-model.number="displayConfig.refreshInterval" 
                    min="60" 
                    max="86400"
                    placeholder="3600"
                  >
                  <div class="form-text">{{ $t('rates.refresh_recommendation') }}</div>
                </div>
              </div>
            </div>
            <div class="mb-3">
              <label for="publish-notes" class="form-label">{{ $t('rates.publish_notes_optional') }}</label>
              <textarea 
                id="publish-notes" 
                class="form-control" 
                v-model="publishNotes" 
                rows="3"
                :placeholder="$t('rates.publish_notes_placeholder')"
              ></textarea>
            </div>
            <div class="alert alert-info">
              <font-awesome-icon icon="fa-solid fa-info-circle" class="me-2" />
              {{ $t('rates.publish_info_alert') }}
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">{{ $t('common.cancel') }}</button>
            <button type="button" class="btn btn-primary" @click="applyAndPublish" :disabled="applying">
              <font-awesome-icon icon="fa-solid fa-check" class="me-1" :spin="applying" />
              {{ applying ? $t('rates.publishing') : $t('rates.apply_and_publish') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 新增币种弹窗 -->
    <div class="modal fade" id="addCurrencyModal" tabindex="-1">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ $t('rates.add_currency') }}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body">
            <!-- 币种选择 -->
            <div class="mb-4">
              <h6 class="mb-3">{{ $t('rates.select_currency_title') }}</h6>
              <div class="table-responsive">
                <table class="table table-hover">
                  <thead>
                    <tr>
                      <th>{{ $t('rates.table_header_select') }}</th>
                      <th>{{ $t('rates.table_header_flag') }}</th>
                      <th>{{ $t('rates.table_header_currency_code') }}</th>
                      <th>{{ $t('rates.table_header_currency_name') }}</th>
                      <th>{{ $t('rates.table_header_country') }}</th>
                      <th>{{ $t('rates.table_header_symbol') }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="template in paginatedCurrencyTemplates" :key="template.id" 
                        @click="selectCurrencyTemplate(template)"
                        :class="{'table-active': selectedTemplate?.id === template?.id}">
                      <td>
                        <input type="radio" class="form-check-input" 
                               :checked="selectedTemplate?.id === template?.id"
                               @click="selectCurrencyTemplate(template)">
                      </td>
                      <td>
                        <CurrencyFlag 
                          :code="template?.flag_code || template?.currency_code || 'USD'"
                          :custom-filename="template?.custom_flag_filename"
                          class="me-2"
                        />
                      </td>
                      <td>{{ template?.currency_code || '' }}</td>
                      <td>{{ getCurrencyNameTranslated(template?.currency_code, template?.currency_name, template?.custom_flag_filename) }}</td>
                      <td>{{ getCountryNameTranslated(template?.country) }}</td>
                      <td>{{ template?.symbol || '' }}</td>
                    </tr>
                  </tbody>
                </table>
                
                <!-- 分页控件 -->
                <div class="d-flex justify-content-between align-items-center mt-3" v-if="currencyTemplates.length > 5">
                  <div class="text-muted small">
                    {{ $t('rates.currency_pagination_info', { 
                      start: (currencyTemplatePagination.current_page - 1) * currencyTemplatePagination.per_page + 1,
                      end: Math.min(currencyTemplatePagination.current_page * currencyTemplatePagination.per_page, currencyTemplates.length),
                      total: currencyTemplates.length 
                    }) }}
                  </div>
                  <nav>
                    <ul class="pagination mb-0">
                      <li class="page-item" :class="{ disabled: currencyTemplatePagination.current_page === 1 }">
                        <button class="page-link" @click="changeCurrencyTemplatePage(currencyTemplatePagination.current_page - 1)" :disabled="currencyTemplatePagination.current_page === 1" style="height: 38px; line-height: 1;">
                          <i class="fas fa-chevron-left"></i>
                        </button>
                      </li>
                      <li class="page-item" v-for="page in visibleCurrencyTemplatePages" :key="page"
                          :class="{ active: page === currencyTemplatePagination.current_page }">
                        <button class="page-link" @click="changeCurrencyTemplatePage(page)" style="height: 38px; line-height: 1;">{{ page }}</button>
                      </li>
                      <li class="page-item" :class="{ disabled: currencyTemplatePagination.current_page === currencyTemplatePagination.total_pages }">
                        <button class="page-link" @click="changeCurrencyTemplatePage(currencyTemplatePagination.current_page + 1)" :disabled="currencyTemplatePagination.current_page === currencyTemplatePagination.total_pages" style="height: 38px; line-height: 1;">
                          <i class="fas fa-chevron-right"></i>
                        </button>
                      </li>
                    </ul>
                  </nav>
                </div>
              </div>
            </div>

            <!-- 汇率设置 -->
            <div class="mb-4" v-if="selectedTemplate">
              <h6 class="mb-3">{{ $t('rates.set_exchange_rate') }}</h6>
              <div class="row">
                <div class="col-md-6">
                  <div class="form-group">
                    <label class="form-label">{{ $t('rates.buy_rate_label') }} <span class="text-danger">*</span></label>
                    <input type="number" class="form-control" v-model="safeNewCurrency.buy_rate" step="0.0001" min="0">
                  </div>
                </div>
                <div class="col-md-6">
                  <div class="form-group">
                    <label class="form-label">{{ $t('rates.sell_rate_label') }} <span class="text-danger">*</span></label>
                    <input type="number" class="form-control" v-model="safeNewCurrency.sell_rate" step="0.0001" min="0">
                  </div>
                </div>
              </div>
            </div>

            <!-- 币种详情 -->
            <div class="alert alert-info" v-if="selectedTemplate">
              <h6>{{ $t('rates.currency_info') }}</h6>
              <p class="mb-1">
                <strong>{{ selectedTemplate?.currency_code }}</strong> - 
                {{ getCurrencyNameTranslated(selectedTemplate?.currency_code, selectedTemplate?.currency_name, selectedTemplate?.custom_flag_filename) }}
              </p>
              <p class="mb-1">
                <strong>{{ $t('rates.country') }}:</strong> 
                {{ getCountryNameTranslated(selectedTemplate?.country) }}
              </p>
              <small class="text-muted">{{ $t('rates.currency_symbol') }}: {{ selectedTemplate?.symbol || '' }}</small>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">{{ $t('common.cancel') }}</button>
            <button type="button" class="btn btn-primary" 
                    @click="addCurrency" 
                    :disabled="!canAddCurrency">
              {{ $t('rates.confirm_add') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 保存确认模态窗口 -->
    <div class="modal fade" id="saveConfirmModal" tabindex="-1">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              <font-awesome-icon icon="fa-solid fa-exclamation-triangle" class="text-warning me-2" />
              {{ $t('rates.attention') }}
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <strong>{{ $t('rates.current_branch_currency') }}</strong> {{ currentBranchCurrency }}
            </div>
            <div class="mb-3">
                              <strong>{{ $t('rates.please_verify') }}</strong>
                              <div class="d-flex align-items-center mt-2">
                  <CurrencyFlag 
                    :code="editingRate?.flag_code || editingRate?.currency_code || 'USD'" 
                    :custom-filename="editingRate?.custom_flag_filename"
                    class="me-2" 
                  />
                  {{ editingRate?.currency_code }} - {{ getCurrencyNameTranslated(editingRate?.currency_code, editingRate?.currency_name, editingRate?.custom_flag_filename) }}
                </div>
            </div>
            <div class="row mb-3">
              <div class="col-6">
                <strong>{{ $t('rates.buy_rate_confirm') }}</strong> {{ editValues[editingRate?.currency_code]?.buyRate }}
              </div>
              <div class="col-6">
                <strong>{{ $t('rates.sell_rate_confirm') }}</strong> {{ editValues[editingRate?.currency_code]?.sellRate }}
              </div>
            </div>
            <div class="alert alert-warning">
                              {{ $t('rates.confirm_rate_setting', { date: formatDate(new Date()) }) }}
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">{{ $t('common.cancel') }}</button>
            <button 
              type="button" 
              class="btn btn-primary" 
              @click="confirmSaveRate"
              :disabled="saving"
            >
              <font-awesome-icon 
                v-if="saving"
                icon="fa-solid fa-spinner" 
                spin 
                class="me-1"
              />
              {{ saving ? $t('rates.saving') : $t('common.confirm') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 提示消息 -->
    <div 
      class="toast position-fixed bottom-0 end-0 m-3"
      :class="{ show: toast.show }"
      role="alert"
    >
      <div class="toast-header" :class="getToastHeaderClass">
        <strong class="me-auto">{{ getToastTitle }}</strong>
        <button type="button" class="btn-close" @click="hideToast"></button>
      </div>
      <div class="toast-body">
        {{ toast.message }}
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed, watch, onBeforeUnmount, nextTick, getCurrentInstance } from 'vue';
import rateService from '@/services/api/rateService';
import { Modal } from 'bootstrap';
import CurrencyFlag from '@/components/CurrencyFlag.vue'
import CurrencySelect from '@/components/CurrencySelect.vue'
import AsyncChart from '@/components/AsyncChart.vue'
import draggable from 'vuedraggable'
import DenominationRateManager from '@/components/DenominationRateManager.vue'

import { useUserStore } from '@/stores/user'
import {
  Chart,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  LineController
} from 'chart.js'
import { formatDateTime } from '@/utils/formatters'
import { getCurrencyName } from '@/utils/currencyTranslator'
import { getCountryName } from '@/utils/countryTranslator'
import { useI18n } from 'vue-i18n'

// 注册必要的组件
Chart.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  LineController
)



export default {
  name: 'RateManagementView',
  components: {
    CurrencyFlag,
    CurrencySelect,
    AsyncChart,
    draggable,
    DenominationRateManager
  },
  setup() {
    const { t, locale } = useI18n();
    const { proxy } = getCurrentInstance();
    const userStore = useUserStore();
    
    // App角色检测
    const isAppRole = computed(() => {
      if (!userStore || !userStore.user) {
        console.warn('User store not available');
        return false;
      }
      return userStore.user.role_name === 'App' || userStore.user.role_name === 'APP';
    });
    
    // 机顶盒相关
    const setTopBoxUrl = computed(() => {
      return `${window.location.origin}/static/Show.html`;
    });
    
    const rates = ref([]);
    const loading = ref(true);
    const error = ref(null);

    const publishing = ref(false);
    const applying = ref(false);
    const saving = ref(null);
    const copying = ref(null);
    const copyingAll = ref(false);
    const updateTime = ref('');
    const lastPublishTime = ref('');
    const dailyRatesPublished = ref(false);
    const editValues = reactive({});
    const selectedCurrency = ref('');
    const selectedCurrencyCode = ref('');
    const selectedTheme = ref('light');
    const selectedLanguage = ref('zh');
    const publishNotes = ref('');
    const lastPublishInfo = ref(null);
    const clearingCache = ref(false);
    
    // 显示配置参数
    const displayConfig = reactive({
      itemsPerPage: 12,        // 每页显示行数，默认12行
      refreshInterval: 3600    // 刷新间隔，默认3600秒
    });
    const addingCurrency = ref(false);
    const currencyTemplates = ref([]);
    const selectedTemplate = ref(null);
    
    // 币种模板分页
    const currencyTemplatePagination = reactive({
      current_page: 1,
      per_page: 5,  // 每页显示5个币种，减少页面长度
      total: 0,
      total_pages: 0
    });
    
    // 发布记录相关
    const publishRecords = ref([]);
    const publishRecordsLoading = ref(false);
    const selectedRecord = ref(null);
    
    // 树形结构：展开/折叠状态管理
    const expandedDates = ref(new Set());
    
    // 按日期分组的发布记录
    const groupedPublishRecords = computed(() => {
      if (!publishRecords.value || publishRecords.value.length === 0) {
        return [];
      }
      
      // 按日期分组
      const grouped = {};
      publishRecords.value.forEach(record => {
        const dateStr = new Date(record.publish_time).toDateString();
        if (!grouped[dateStr]) {
          grouped[dateStr] = {
            date: dateStr,
            dateDisplay: formatDate(record.publish_time),
            records: []
          };
        }
        grouped[dateStr].records.push(record);
      });
      
      // 转换为数组并按日期降序排序
      const groupedArray = Object.values(grouped);
      groupedArray.sort((a, b) => new Date(b.date) - new Date(a.date));
      
      // 为每个日期组内的记录按时间降序排序
      groupedArray.forEach(group => {
        group.records.sort((a, b) => new Date(b.publish_time) - new Date(a.publish_time));
      });
      
      return groupedArray;
    });
    
    // 切换日期节点的展开/折叠状态
    const toggleDateExpansion = (dateStr) => {
      if (expandedDates.value.has(dateStr)) {
        expandedDates.value.delete(dateStr);
      } else {
        expandedDates.value.add(dateStr);
      }
    };
    
    // 检查日期节点是否展开
    const isDateExpanded = (dateStr) => {
      return expandedDates.value.has(dateStr);
    };
    
    // 格式化日期（只显示日期部分）
    const formatDate = (dateTimeStr) => {
      const date = new Date(dateTimeStr);
      const today = new Date();
      const yesterday = new Date(today);
      yesterday.setDate(yesterday.getDate() - 1);
      
      if (date.toDateString() === today.toDateString()) {
        return t('common.today') + ' (' + date.toLocaleDateString() + ')';
      } else if (date.toDateString() === yesterday.toDateString()) {
        return t('common.yesterday') + ' (' + date.toLocaleDateString() + ')';
      } else {
        return date.toLocaleDateString();
      }
    };
    
    // 格式化时间（只显示时间部分）
    const formatTime = (dateTimeStr) => {
      return new Date(dateTimeStr).toLocaleTimeString();
    };
    
    // 分页相关
    const pagination = reactive({
      current_page: 1,
      per_page: 20,
      total: 0,
      total_pages: 0
    });
    
    const newCurrency = reactive({
      buy_rate: null,
      sell_rate: null
    });

    // 确保newCurrency对象始终存在
    const safeNewCurrency = computed({
      get: () => newCurrency || { buy_rate: null, sell_rate: null },
      set: (value) => {
        if (newCurrency) {
          Object.assign(newCurrency, value);
        }
      }
    });
    
    // 批量选择相关
    const selectedCurrencies = ref([]);
    const selectAll = ref(false);
    const batchSaving = ref(false);
    
    const toast = reactive({
      show: false,
      message: '',
      type: 'success',
      timeout: null
    });

    const getToastHeaderClass = computed(() => ({
      'bg-success text-white': toast.type === 'success',
      'bg-danger text-white': toast.type === 'error'
    }));

    const getToastTitle = computed(() => {
      switch (toast.type) {
        case 'success':
          return t('common.success_title');
        case 'error':
          return t('common.error_title');
        case 'warning':
          return t('common.warning_title');
        case 'info':
          return t('common.info_title');
        default:
          return t('common.info_title');
      }
    });

    // 过滤有效的汇率数据
    const validRates = computed(() => {
      return rates.value.filter(rate => rate && rate.currency_code);
    });
    
    // 计算今日已批量保存的币种数量
    const publishedCount = computed(() => {
      return validRates.value.filter(rate => rate.batchSaved).length;
    });
    
    const showToast = (message, type = 'success') => {
      if (toast.timeout) {
        clearTimeout(toast.timeout);
      }
      
      toast.message = message;
      toast.type = type;
      toast.show = true;
      
      toast.timeout = setTimeout(() => {
        toast.show = false;
      }, 3000);
    };
    
    const hideToast = () => {
      toast.show = false;
    };
    
    // 加载发布记录
    const loadPublishRecords = async (page = 1) => {
      publishRecordsLoading.value = true;
      
      try {
        // 构建请求参数
        const params = new URLSearchParams({
          page: page.toString(),
          per_page: pagination.per_page.toString()
        });
        
        const response = await proxy.$api.get(`/dashboard/publish-records?${params}`);
        
        const result = response.data;
        
        if (result.success) {
          publishRecords.value = result.records;
          // 更新分页信息
          pagination.current_page = result.pagination.page;
          pagination.total = result.pagination.total;
          pagination.total_pages = result.pagination.pages;
        } else {
          showToast(t('rates.load_records_failed') + ': ' + result.message, 'error');
        }
      } catch (err) {
        console.error('加载发布记录失败:', err);
        showToast(t('rates.load_records_failed') + ': ' + t('rates.network_error'), 'error');
      } finally {
        publishRecordsLoading.value = false;
      }
    };
    
    // 分页导航
    const goToPage = (page) => {
      if (page >= 1 && page <= pagination.total_pages) {
        loadPublishRecords(page);
      }
    };
    
    const previousPage = () => {
      if (pagination.current_page > 1) {
        goToPage(pagination.current_page - 1);
      }
    };
    
    const nextPage = () => {
      if (pagination.current_page < pagination.total_pages) {
        goToPage(pagination.current_page + 1);
      }
    };
    
    // 获取可见的页码列表
    const getVisiblePages = () => {
      const pages = [];
      const current = pagination.current_page;
      const total = pagination.total_pages;
      
      if (total <= 7) {
        // 如果总页数不超过7页，显示所有页码
        for (let i = 1; i <= total; i++) {
          pages.push(i);
        }
      } else {
        // 总页数超过7页，使用省略号
        if (current <= 4) {
          // 当前页在前面，显示 1,2,3,4,5...最后一页
          for (let i = 1; i <= 5; i++) {
            pages.push(i);
          }
          pages.push('...');
          pages.push(total);
        } else if (current >= total - 3) {
          // 当前页在后面，显示 1...倒数5页
          pages.push(1);
          pages.push('...');
          for (let i = total - 4; i <= total; i++) {
            pages.push(i);
          }
        } else {
          // 当前页在中间，显示 1...当前页前后各1页...最后一页
          pages.push(1);
          pages.push('...');
          for (let i = current - 1; i <= current + 1; i++) {
            pages.push(i);
          }
          pages.push('...');
          pages.push(total);
        }
      }
      
      return pages;
    };
    
    // 查看发布记录详情
    const viewPublishRecord = async (recordId) => {
      try {
        const response = await proxy.$api.get(`/dashboard/publish-records/${recordId}`);
        
        const result = response.data;
        
        if (result.success) {
          selectedRecord.value = result.record;
          const modal = new Modal(document.getElementById('recordDetailModal'));
          modal.show();
        } else {
          showToast(t('rates.get_record_details_failed') + ': ' + result.message, 'error');
        }
      } catch (err) {
        console.error('获取发布记录详情失败:', err);
        showToast(t('rates.get_record_details_failed') + ': ' + t('rates.network_error'), 'error');
      }
    };
    
    // 应用发布记录的汇率到当前列表
    const copyRecordRates = async () => {
      if (!selectedRecord.value || !selectedRecord.value.details) {
        showToast(t('rates.cannot_apply_rate_data'), 'error');
        return;
      }
      
      try {
        // 更新当前汇率列表
        const recordDetails = selectedRecord.value.details;
        
        // 更新现有汇率
        rates.value = rates.value.map(rate => {
          const recordDetail = recordDetails.find(d => d.currency_code === rate.currency_code);
          if (recordDetail) {
            return {
              ...rate,
              buy_rate: recordDetail.buy_rate,
              sell_rate: recordDetail.sell_rate,
              editMode: false
            };
          }
          return rate;
        });
        
        // 添加不存在的币种
        for (const detail of recordDetails) {
          const exists = rates.value.some(r => r.currency_code === detail.currency_code);
          if (!exists) {
            rates.value.push({
              currency_id: detail.currency_id,
              currency_code: detail.currency_code,
              currency_name: detail.currency_name,
              flag_code: detail.flag_code,
              buy_rate: detail.buy_rate,
              sell_rate: detail.sell_rate,
              editMode: false
            });
          }
        }
        
        // 关闭弹窗
        const modal = Modal.getInstance(document.getElementById('recordDetailModal'));
        modal.hide();
        
        showToast(t('rates.rate_data_applied'));
        updateTime.value = formatDateTime(new Date());
        
      } catch (err) {
        console.error('应用汇率数据失败:', err);
        showToast(t('rates.apply_rate_data_failed'), 'error');
      }
    };
    
    // 检查今日汇率是否已发布 - v2.0 强制显示修复版本
    const checkDailyRatesStatus = async () => {
      console.log('🔍 开始检查汇率状态 - 修复版本 v2.0');
      try {
        // 获取所有货币数据（包括未发布的），以便显示时钟图标
        const response = await rateService.getCurrentRates(false); // false表示获取所有货币
        
        if (response.data.success) {
          const today = new Date().toISOString().split('T')[0]; // 使用YYYY-MM-DD格式
          const hasToday = response.data.rates.some(rate => {
            if (rate.rate_date) {
              // 确保日期格式一致，都转换为YYYY-MM-DD格式
              const rateDate = rate.rate_date.split('T')[0];
              return rateDate === today;
            }
            return false;
          });
          
          console.log('今日汇率状态检查:', {
            today,
            totalRates: response.data.rates.length,
            hasToday,
            sampleDates: response.data.rates.slice(0, 3).map(r => r.rate_date)
          });
          
          // 强制设置为已初始化，只要有汇率数据就显示
          const hasAnyRates = response.data.rates && response.data.rates.length > 0;
          dailyRatesPublished.value = hasAnyRates;
          
          console.log('强制设置状态:', {
            hasAnyRates,
            dailyRatesPublished: dailyRatesPublished.value
          });
          
          // 如果有汇率数据就显示
          if (hasAnyRates) {
            rates.value = response.data.rates.map(rate => {
              return {
                ...rate,
                editMode: false,
                isPublished: rate.is_published || false,  // 是否当日发布
                last_publish_time: rate.last_publish_time || rate.rate_date,
                last_publisher: rate.publisher_name || '未知用户',  // 信任后端返回的数据
                // 添加批量保存相关字段
                batchSaved: rate.batch_saved || false,
                batchSavedTime: rate.batch_saved_time || null,
                batchSavedBy: rate.batch_saved_by || null
              };
            });
            
            // 检查今日是否有应用发布记录
            await checkTodayPublishStatus();
            
            // 自动选择第一个币种显示趋势图
            if (!selectedCurrency.value && rates.value.length > 0) {
              const firstRateWithData = rates.value.find(rate => rate.buy_rate !== null && rate.sell_rate !== null);
              if (firstRateWithData) {
                selectedCurrency.value = firstRateWithData.currency_id;
                // 立即更新图表数据
                nextTick(() => {
                  fetchRateHistory();
                });
              }
            }
          } else {
            rates.value = [];
          }
          
          updateTime.value = formatDateTime(new Date());
        }
      } catch (err) {
        console.error('检查每日汇率状态失败:', err);
        dailyRatesPublished.value = false;
        rates.value = [];
      }
    };

    // 检查今日发布状态
    const checkTodayPublishStatus = async () => {
      try {
        const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD格式
        const response = await proxy.$api.get(`/dashboard/publish-records?date_from=${today}&date_to=${today}&per_page=1`);
        
        const result = response.data;
        
        if (result.success && result.records && result.records.length > 0) {
          // 获取最新的发布记录
          const latestRecord = result.records[0];
          lastPublishInfo.value = {
            url: `/api/dashboard/display-rates?theme=${latestRecord.publish_theme || 'light'}`,
            theme: latestRecord.publish_theme || 'light',
            publishedAt: latestRecord.publish_time
          };
        } else {
          lastPublishInfo.value = null;
        }
      } catch (err) {
        console.error('检查今日发布状态失败:', err);
        lastPublishInfo.value = null;
      }
    };
    
    const fetchRates = async () => {
      loading.value = true;
      error.value = null;
      
      try {
        // 获取所有货币数据（包括未发布的），以便显示时钟图标
        const response = await rateService.getCurrentRates(false); // false表示获取所有货币
        
        if (response.data.success) {
          rates.value = response.data.rates.map(rate => {
            return {
              ...rate,
              editMode: false,
              isPublished: rate.is_published || false,  // 是否当日发布
              last_publish_time: rate.last_publish_time || rate.rate_date,
              last_publisher: rate.publisher_name || '未知用户',  // 信任后端返回的数据
              // 添加批量保存相关字段
              batchSaved: rate.batch_saved || false,
              batchSavedTime: rate.batch_saved_time || null,
              batchSavedBy: rate.batch_saved_by || null
            };
          });
          
          updateTime.value = formatDateTime(new Date());
          
          // 如果没有选择币种且有可用币种，选择第一个有汇率的币种
          if (!selectedCurrency.value && rates.value.length > 0) {
            const firstRateWithData = rates.value.find(rate => rate.buy_rate !== null && rate.sell_rate !== null);
            if (firstRateWithData) {
              selectedCurrency.value = firstRateWithData.currency_id;
              // 立即更新图表数据
              nextTick(() => {
                fetchRateHistory();
              });
            }
          }
        } else {
          error.value = response.data.message || '获取汇率失败';
        }
      } catch (err) {
        console.error('Failed to fetch rates:', err);
        error.value = err.response?.data?.message || '网络错误，请稍后重试';
      } finally {
        loading.value = false;
      }
    };
    

    
    // 拖拽排序处理
    const onSortEnd = async (evt) => {
      const { oldIndex, newIndex } = evt;
      if (oldIndex === newIndex) return;
      
      try {
        // vuedraggable已经自动更新了rates数组，现在保存排序到后端
        const sortData = {
          rates: rates.value.map(rate => ({
            currency_id: rate.currency_id,
            currency_code: rate.currency_code
          }))
        };
        
        const response = await proxy.$api.post('/dashboard/save-rate-sort-order', sortData);
        
        const result = response.data;
        
        if (result.success) {
          console.log(`拖拽完成: ${oldIndex} -> ${newIndex}，排序已保存`);
          showToast(t('rates.sort_saved'));
        } else {
          showToast(t('rates.save_sort_failed') + ': ' + result.message, 'error');
        }
      } catch (err) {
        console.error('保存排序失败:', err);
        showToast(t('rates.save_sort_failed') + ': ' + t('rates.network_error'), 'error');
      }
    };
    
    // 删除币种（从今日汇率列表中移除）
    const removeCurrency = async (currencyCode) => {
      if (confirm(t('rates.confirm_delete_currency_msg', { currencyCode }))) {
        try {
          // 从数据库中删除币种
          const response = await rateService.deleteCurrency(currencyCode);
          if (response.data.success) {
            // 立即从本地列表中移除该币种
            rates.value = rates.value.filter(rate => rate.currency_code !== currencyCode);
            
            // 不再重新获取数据，避免自动初始化重新创建汇率记录
            // await fetchRates();
            showToast(t('rates.currency_deleted', { currencyCode }));
          } else {
            showToast(t('rates.delete_currency_failed'), 'error');
          }
        } catch (error) {
          console.error('删除币种失败:', error);
          showToast(t('rates.delete_currency_failed'), 'error');
        }
      }
    };
    
    // 显示主题选择弹窗
    const showThemeModal = () => {
      const modal = new Modal(document.getElementById('themeModal'));
      modal.show();
    };
    
    // 应用并发布汇率
    const applyAndPublish = async () => {
      applying.value = true;
      
      try {
        // 发布所有显示绿色小勾的货币（batchSaved为true的货币）
        const publishedRates = rates.value.filter(rate => rate.batchSaved);
        const ratesData = publishedRates.map(rate => ({
          currency_id: rate.currency_id,
          currency_code: rate.currency_code,
          currency_name: rate.currency_name,
          flag_code: rate.flag_code,
          buy_rate: rate.buy_rate || 0,
          sell_rate: rate.sell_rate || 0
        }));
        
        console.log(`准备发布 ${ratesData.length} 种已批量保存的货币汇率数据`);
        console.log('已批量保存的货币:', ratesData.map(r => r.currency_code).join(', '));
        
        if (ratesData.length === 0) {
          showToast(t('rates.no_rate_data_to_publish'), 'error');
          return;
        }
        
                 // 发布到机顶盒显示
         const publishResponse = await proxy.$api.post('/dashboard/publish-rates', {
             rates: ratesData,
             theme: selectedTheme.value,
             language: selectedLanguage.value,
             notes: publishNotes.value,
             display_config: {
               items_per_page: parseInt(displayConfig.itemsPerPage) || 12,
               refresh_interval: parseInt(displayConfig.refreshInterval) || 3600
             }
         });
        
        const publishResult = publishResponse.data;
        
                 if (publishResult.success) {
           lastPublishInfo.value = {
             url: publishResult.redirect_url,
             theme: selectedTheme.value,
             publishedAt: new Date().toISOString()
           };
           
           // 关闭弹窗
           const modal = Modal.getInstance(document.getElementById('themeModal'));
           modal.hide();
           
           // 安全地清除遮罩层 - 使用Bootstrap的标准方法
           setTimeout(() => {
             // 检查并移除残留的modal-backdrop
             const backdrops = document.querySelectorAll('.modal-backdrop');
             if (backdrops.length > 0) {
               backdrops.forEach(backdrop => {
                 if (backdrop && backdrop.parentNode) {
                   backdrop.parentNode.removeChild(backdrop);
                 }
               });
               console.log('[遮罩层] 已清除残留的modal-backdrop');
             }
             
             // 恢复body样式
             if (document.body.classList.contains('modal-open')) {
               document.body.classList.remove('modal-open');
               document.body.style.overflow = '';
               document.body.style.paddingRight = '';
               console.log('[遮罩层] 已恢复body样式');
             }
           }, 200);
           
           // 清空备注
           publishNotes.value = '';
           
           // 重新加载发布记录
           await loadPublishRecords();
           
           // 重新加载汇率数据，确保显示最新状态
           await fetchRates();
           
           showToast(t('rates.rate_published_success'));
        } else {
          showToast(t('rates.publish_failed') + ': ' + publishResult.message, 'error');
        }
      } catch (err) {
        console.error('发布失败:', err);
        showToast(t('rates.publish_failed') + ': ' + (err.message || t('rates.network_error')), 'error');
      } finally {
        applying.value = false;
        
        // 确保在失败时也清除遮罩层
        setTimeout(() => {
          const backdrops = document.querySelectorAll('.modal-backdrop');
          if (backdrops.length > 0) {
            backdrops.forEach(backdrop => {
              if (backdrop && backdrop.parentNode) {
                backdrop.parentNode.removeChild(backdrop);
              }
            });
            console.log('[遮罩层] 失败时已清除残留的modal-backdrop');
          }
          
          if (document.body.classList.contains('modal-open')) {
            document.body.classList.remove('modal-open');
            document.body.style.overflow = '';
            document.body.style.paddingRight = '';
            console.log('[遮罩层] 失败时已恢复body样式');
          }
        }, 200);
      }
    };
    
    // 清除发布缓存
    const clearPublishCache = async () => {
      clearingCache.value = true;
      
      try {
        const response = await proxy.$api.post('/dashboard/clear-publish-cache');
        
        const result = response.data;
        
        if (result.success) {
          showToast(t('rates.clear_cache_success') + ': ' + result.message);
        } else {
          showToast(t('rates.clear_cache_failed') + ': ' + result.message, 'error');
        }
      } catch (err) {
        console.error('清除缓存失败:', err);
        showToast(t('rates.clear_cache_failed') + ': ' + (err.message || t('rates.network_error')), 'error');
      } finally {
        clearingCache.value = false;
      }
    };
    
    const toggleEditMode = (currency) => {
      const updatedRates = rates.value.map(rate => {
        if (rate.currency_code === currency) {
          if (!rate.editMode) {
            editValues[currency] = { 
              buyRate: rate.buy_rate, 
              sellRate: rate.sell_rate 
            };
          }
          return { ...rate, editMode: !rate.editMode };
        }
        return rate;
      });
      rates.value = updatedRates;
    };

    // 复制最近一次汇率
    const copyLastRate = async (currencyCode) => {
      copying.value = currencyCode;
      try {
        const response = await fetch(`/api/rates/last_rate/${currencyCode}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          if (data.success && data.last_rate) {
            const lastRate = data.last_rate;
            
            // 更新编辑值
            editValues[currencyCode] = {
              buyRate: lastRate.buy_rate,
              sellRate: lastRate.sell_rate
            };
            
            // 自动进入编辑模式，让用户看到复制的汇率
            const updatedRates = rates.value.map(rate => {
              if (rate.currency_code === currencyCode) {
                return { ...rate, editMode: true };
              }
              return rate;
            });
            rates.value = updatedRates;
            
            // 显示成功消息
            showToast(`${currencyCode} 已复制最近一次汇率：买入价 ${lastRate.buy_rate}，卖出价 ${lastRate.sell_rate}`, 'success');
          } else {
            showToast(data.message || '复制汇率失败', 'error');
          }
        } else {
          showToast('获取最近汇率失败', 'error');
        }
      } catch (error) {
        console.error('复制汇率失败:', error);
        showToast('复制汇率失败', 'error');
      } finally {
        copying.value = null;
      }
    };

    // 复制所有币种的最近一次汇率
    const copyAllLastRates = async () => {
      copyingAll.value = true;
      try {
        const response = await fetch('/api/rates/last_rates_all', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          if (data.success && data.last_rates) {
            let copiedCount = 0;
            let failedCount = 0;
            
            // 遍历所有币种，复制汇率
            for (const [currencyCode, lastRate] of Object.entries(data.last_rates)) {
              try {
                // 更新编辑值
                editValues[currencyCode] = {
                  buyRate: lastRate.buy_rate,
                  sellRate: lastRate.sell_rate
                };
                
                // 自动进入编辑模式
                const updatedRates = rates.value.map(rate => {
                  if (rate.currency_code === currencyCode) {
                    return { ...rate, editMode: true };
                  }
                  return rate;
                });
                rates.value = updatedRates;
                
                copiedCount++;
              } catch (error) {
                console.error(`复制币种 ${currencyCode} 汇率失败:`, error);
                failedCount++;
              }
            }
            
            // 显示结果消息
            if (copiedCount > 0) {
              showToast(`成功复制 ${copiedCount} 个币种的汇率${failedCount > 0 ? `，${failedCount} 个失败` : ''}，正在自动保存...`, 'success');
              
              // 自动保存所有复制的汇率
              await autoSaveAllCopiedRates();
            } else {
              showToast('没有找到可复制的汇率', 'warning');
            }
          } else {
            showToast(data.message || '批量复制汇率失败', 'error');
          }
        } else {
          showToast('获取汇率数据失败', 'error');
        }
      } catch (error) {
        console.error('批量复制汇率失败:', error);
        showToast('批量复制汇率失败', 'error');
      } finally {
        copyingAll.value = false;
      }
    };

    // 自动保存所有复制的汇率
    const autoSaveAllCopiedRates = async () => {
      try {
        const currenciesToSave = Object.keys(editValues);
        if (currenciesToSave.length === 0) {
          showToast('没有需要保存的汇率', 'warning');
          return;
        }

        let savedCount = 0;
        let failedCount = 0;

        // 批量保存所有复制的汇率
        for (const currencyCode of currenciesToSave) {
          try {
            const rate = rates.value.find(r => r.currency_code === currencyCode);
            if (rate && editValues[currencyCode]) {
              const saveData = {
                currency_id: rate.currency_id,
                buy_rate: editValues[currencyCode].buyRate,
                sell_rate: editValues[currencyCode].sellRate,
                batch_saved: true,
                is_published: true
              };

              const saveResponse = await fetch('/api/rates/set_rate', {
                method: 'POST',
                headers: {
                  'Authorization': `Bearer ${localStorage.getItem('token')}`,
                  'Content-Type': 'application/json'
                },
                body: JSON.stringify(saveData)
              });

              if (saveResponse.ok) {
                const saveResult = await saveResponse.json();
                if (saveResult.success) {
                  // 更新本地数据
                  const updatedRates = rates.value.map(r => {
                    if (r.currency_code === currencyCode) {
                      return {
                        ...r,
                        buy_rate: editValues[currencyCode].buyRate,
                        sell_rate: editValues[currencyCode].sellRate,
                        editMode: false,
                        is_today_rate: true,
                        is_published: true
                      };
                    }
                    return r;
                  });
                  rates.value = updatedRates;
                  
                  // 清除编辑值
                  delete editValues[currencyCode];
                  
                  savedCount++;
                } else {
                  failedCount++;
                  console.error(`保存币种 ${currencyCode} 失败:`, saveResult.message);
                }
              } else {
                failedCount++;
                console.error(`保存币种 ${currencyCode} 失败:`, saveResponse.status);
              }
            }
          } catch (error) {
            failedCount++;
            console.error(`保存币种 ${currencyCode} 时发生错误:`, error);
          }
        }

        // 显示保存结果
        if (savedCount > 0) {
          showToast(`成功保存 ${savedCount} 个币种的汇率${failedCount > 0 ? `，${failedCount} 个保存失败` : ''}`, 'success');
          
          // 刷新汇率数据
          await fetchRates();
        } else {
          showToast('所有汇率保存失败', 'error');
        }
      } catch (error) {
        console.error('自动保存汇率失败:', error);
        showToast('自动保存汇率失败', 'error');
      }
    };
    
    const handleRateChange = (currency, field, value) => {
      const numValue = parseFloat(value);
      if (isNaN(numValue)) return;
      
      editValues[currency] = {
        ...editValues[currency],
        [field]: numValue
      };
    };
    
    const editingRate = ref(null);
    const currentBranchCurrency = ref('');
    let saveConfirmModal = null;
    const isComponentMounted = ref(false);

    // 获取当前网点本币信息
    const fetchBranchCurrency = () => {
      try {
        // 从localStorage获取用户信息
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        if (user.branch_currency) {
          currentBranchCurrency.value = `${user.branch_currency.code} - ${user.branch_currency.name}`;
        } else {
          throw new Error('No branch currency info found');
        }
      } catch (err) {
        console.error('Failed to fetch branch currency:', err);
        currentBranchCurrency.value = '获取本币信息失败';
      }
    };

    // 获取当前网点本币信息
    const getCurrentBranchCurrency = () => {
      try {
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        if (user.branch_currency) {
          return `${user.branch_currency.code} - ${user.branch_currency.name}`;
        }
        return '获取本币信息失败';
      } catch (err) {
        console.error('Failed to get current branch currency:', err);
        return '获取本币信息失败';
      }
    };

    onMounted(async () => {
      isComponentMounted.value = true;
      await fetchBranchCurrency();
      await checkDailyRatesStatus(); // 先检查每日汇率状态
      
      // 加载发布记录
      await loadPublishRecords();
      
      // 确保汇率趋势图表自动加载
      if (selectedCurrency.value && rates.value.length > 0) {
        await nextTick();
        await fetchRateHistory();
      }
      
      // 确保DOM元素完全加载后再初始化Modal
      await nextTick();
      const saveConfirmModalElement = document.getElementById('saveConfirmModal');
      if (saveConfirmModalElement) {
        saveConfirmModal = new Modal(saveConfirmModalElement, {
          backdrop: true,
          keyboard: true,
          focus: true
        });
      }
      
      // 🔧 新增：检查URL参数，自动激活指定标签页
      await nextTick();
      const route = proxy.$route;
      if (route.query.tab) {
        const tabName = route.query.tab;
        console.log('[标签页] 从URL参数获取标签页:', tabName);
        
        // 根据参数激活对应标签页
        if (tabName === 'denomination-rates') {
          const tabElement = document.getElementById('denomination-rates-tab');
          if (tabElement) {
            console.log('[标签页] 激活面值汇率标签页');
            tabElement.click();
          }
        } else if (tabName === 'publish-records') {
          const tabElement = document.getElementById('publish-records-tab');
          if (tabElement) {
            console.log('[标签页] 激活发布记录标签页');
            tabElement.click();
          }
        }
      }
    });

    
    
    const saveRateChanges = async (currency) => {
      const rate = rates.value.find(r => r.currency_code === currency);
      
      // 系统允许一天多次修改和发布汇率，移除重复发布限制
      editingRate.value = rate;
      currentBranchCurrency.value = getCurrentBranchCurrency();
      if (saveConfirmModal) {
        saveConfirmModal.show();
      }
    };

    const confirmSaveRate = async () => {
      const currency = editingRate.value.currency_code;
      saving.value = currency;
      
      try {
        const data = {
          currency_id: editingRate.value.currency_id,
          buy_rate: editValues[currency].buyRate,
          sell_rate: editValues[currency].sellRate,
          batch_saved: true,  // 单个保存也设置批量保存标记
          is_published: true  // 设置发布标记
        };
        
        const response = await rateService.updateRate(data);
        
        if (response.data.success) {
          const now = new Date();
          const username = JSON.parse(localStorage.getItem('user') || '{}').username || '系统';
          
          rates.value = rates.value.map(rate => {
            if (rate.currency_code === currency) {
              return {
                ...rate,
                buy_rate: data.buy_rate,
                sell_rate: data.sell_rate,
                editMode: false,
                isPublished: true,  // 保存后状态为已发布
                is_published: true,  // 同时更新后端字段名
                is_edited_today: true,  // 标记为今日已编辑
                batchSaved: true,  // 单个保存也设置批量保存状态
                batchSavedTime: now.toISOString(),
                batchSavedBy: username,
                rate_date: now.toISOString(),
                last_publish_time: now.toISOString(),
                last_publisher: username,
                publisher_name: username,
                last_updated: now.toISOString()
              };
            }
            return rate;
          });
          
          updateTime.value = formatDateTime(now);
          lastPublishTime.value = updateTime.value;
          
          showToast(`${currency} ${t('rates.rate_updated_success')}`);
          if (saveConfirmModal) {
            saveConfirmModal.hide();
          }
        } else {
          showToast(response.data.message || t('rates.update_rate_failed'), 'error');
        }
      } catch (err) {
        console.error('Failed to update rate:', err);
                  showToast(t('rates.update_rate_failed') + ': ' + (err.response?.data?.message || t('rates.network_error')), 'error');
      } finally {
        saving.value = null;
        editingRate.value = null;
      }
    };

    const showAddCurrencyModal = async () => {
      try {
        // 获取当前网点已有的币种代码列表
        const currentCurrencyCodes = rates.value.map(rate => rate.currency_code).join(',');
        console.log(`[新增币种] 当前网点已有币种: ${currentCurrencyCodes}`);
        
        const response = await rateService.getCurrencyTemplates(currentCurrencyCodes);
        // 确保返回的数据是数组并且过滤掉无效的模板
        if (Array.isArray(response.data)) {
          currencyTemplates.value = response.data.filter(template => 
            template && 
            template.currency_code && 
            template.currency_name
          );
          // 更新分页信息
          updateCurrencyTemplatePagination();
          
          console.log(`[新增币种] 获取到 ${currencyTemplates.value.length} 个可添加的币种模板`);
          if (currencyTemplates.value.length === 0) {
            showToast(t('rates.no_available_currencies_to_add'), 'info');
          }
        } else {
          currencyTemplates.value = [];
          console.warn('API返回的币种模板数据不是数组:', response.data);
        }
        selectedTemplate.value = null;
        if (newCurrency) {
          newCurrency.buy_rate = null;
          newCurrency.sell_rate = null;
        }
        
        // 确保DOM元素完全加载后再初始化和显示Modal
        await nextTick();
        const addCurrencyModalElement = document.getElementById('addCurrencyModal');
        if (addCurrencyModalElement) {
          const modal = new Modal(addCurrencyModalElement, {
            backdrop: true,
            keyboard: true,
            focus: true
          });
          modal.show();
        }
      } catch (err) {
        console.error('Failed to fetch currency templates:', err);
        showToast(t('rates.get_currency_template_failed') + ': ' + (err.response?.data?.message || t('rates.network_error')), 'error');
      }
    };

    const selectCurrencyTemplate = (template) => {
      if (template && template.currency_code && template.currency_name) {
        selectedTemplate.value = template;
      } else {
        console.warn('尝试选择无效的币种模板:', template);
      }
    };

    const getFlagUrl = (flagCode) => {
      if (!flagCode) return '/flags/unknown.svg';
      return `/flags/${flagCode.toLowerCase()}.svg`;
    };

    const canAddCurrency = computed(() => {
      return selectedTemplate.value &&
             (safeNewCurrency.value.buy_rate && safeNewCurrency.value.buy_rate > 0) &&
             (safeNewCurrency.value.sell_rate && safeNewCurrency.value.sell_rate > 0);
    });

    const addCurrency = async () => {
      if (!selectedTemplate.value) {
        showToast(t('common.please_select_currency'), 'error');
        return;
      }

      if (!safeNewCurrency.value.buy_rate || !safeNewCurrency.value.sell_rate) {
        showToast(t('rates.please_enter_exchange_rate'), 'error');
        return;
      }

      addingCurrency.value = true;
      try {
        const response = await rateService.addCurrency({
          currency_code: selectedTemplate.value?.currency_code,
          currency_name: selectedTemplate.value?.currency_name,
          country: selectedTemplate.value?.country,
          flag_code: selectedTemplate.value?.flag_code,
          custom_flag_filename: selectedTemplate.value?.custom_flag_filename,  // 添加自定义图标文件名
          buy_rate: safeNewCurrency.value.buy_rate,
          sell_rate: safeNewCurrency.value.sell_rate
        });

        if (response.data.success) {
          showToast(t('rates.new_currency_added'));
          await fetchRates();
          const addCurrencyModalElement = document.getElementById('addCurrencyModal');
          if (addCurrencyModalElement) {
            const modal = Modal.getInstance(addCurrencyModalElement);
            if (modal) {
              modal.hide();
            }
          }

          selectedTemplate.value = null;
          if (newCurrency) {
            newCurrency.buy_rate = null;
            newCurrency.sell_rate = null;
          }
        } else {
          showToast(response.data.message || t('rates.add_currency_failed'), 'error');
        }
      } catch (err) {
        console.error('Failed to add currency:', err);
        showToast(t('rates.add_currency_failed') + ': ' + (err.response?.data?.message || t('rates.network_error')), 'error');
      } finally {
        addingCurrency.value = false;
      }
    };
    
    const handleImageError = (e) => {
      // 使用内联SVG替代外部占位图服务
      const svg = `
        <svg width="400" height="200" viewBox="0 0 400 200" xmlns="http://www.w3.org/2000/svg">
          <rect width="400" height="200" fill="#f8f9fa"/>
          <text x="200" y="100" font-family="Arial" font-size="16" fill="#6c757d" text-anchor="middle">
            汇率趋势图
          </text>
          <text x="200" y="120" font-family="Arial" font-size="12" fill="#6c757d" text-anchor="middle">
            即将上线
          </text>
        </svg>
      `;
      const blob = new Blob([svg], { type: 'image/svg+xml' });
      e.target.src = URL.createObjectURL(blob);
    };
    
    const rateHistory = ref([]);
    const rateChart = ref(null);
      
    // 图表数据和配置
    const chartData = computed(() => {
          if (!rateHistory.value || rateHistory.value.length === 0) {
        return {
          labels: [],
          datasets: []
        };
      }

      return {
        labels: rateHistory.value.map(item => {
          const date = new Date(item.date);
          // 根据当前语言设置格式化日期
          const localeMap = {
            'zh-CN': 'zh-CN',
            'en-US': 'en-US', 
            'th-TH': 'th-TH'
          };
          const currentLocale = localeMap[locale.value] || 'zh-CN';
          return date.toLocaleDateString(currentLocale, {
            month: 'short',
            day: 'numeric'
          });
        }),
            datasets: [
              {
                label: t('rates.buy_rate_label'),
            data: rateHistory.value.map(item => item.buy_rate),
            borderColor: '#28a745',
                backgroundColor: 'rgba(40, 167, 69, 0.1)',
                borderWidth: 2,
            fill: true,
            tension: 0.4,
                pointRadius: 3,
            pointHoverRadius: 6,
            pointBackgroundColor: '#28a745',
            pointBorderColor: '#fff',
            pointBorderWidth: 2
              },
              {
                label: t('rates.sell_rate_label'),
            data: rateHistory.value.map(item => item.sell_rate),
            borderColor: '#007bff',
                backgroundColor: 'rgba(0, 123, 255, 0.1)',
                borderWidth: 2,
            fill: true,
            tension: 0.4,
                pointRadius: 3,
            pointHoverRadius: 6,
            pointBackgroundColor: '#007bff',
            pointBorderColor: '#fff',
            pointBorderWidth: 2
              }
            ]
      };
    });

    const chartOptions = computed(() => ({
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
          display: true,
                position: 'top',
                labels: {
                  usePointStyle: true,
            padding: 15,
            font: {
              size: 12
            }
                }
              },
              tooltip: {
                mode: 'index',
                intersect: false,
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          titleColor: '#333',
          bodyColor: '#666',
                borderColor: '#ddd',
          borderWidth: 1,
          cornerRadius: 6,
          padding: 12,
          displayColors: true,
          callbacks: {
            title: function(tooltipItems) {
              return t('rates.chart_tooltip_date') + tooltipItems[0].label;
            },
            label: function(context) {
              return context.dataset.label + ': ' + Number(context.parsed.y).toFixed(4);
            }
          }
        }
      },
      hover: {
        mode: 'nearest',
        intersect: false,
        animationDuration: 150
            },
            scales: {
              x: {
                display: true,
                title: {
                  display: true,
                  text: t('rates.chart_date_label'),
                  color: '#666',
                  font: {
              size: 11
                  }
                },
                grid: {
                  display: false
          },
          ticks: {
            maxRotation: 45,
            font: {
              size: 10
            }
                }
              },
              y: {
                display: true,
                title: {
                  display: true,
                  text: t('rates.chart_rate_label'),
                  color: '#666',
                  font: {
              size: 11
                  }
                },
                beginAtZero: false,
                ticks: {
                  callback: function(value) {
              return Number(value).toFixed(4);
            },
            font: {
              size: 10
                  }
                },
                grid: {
            color: 'rgba(0, 0, 0, 0.05)',
            lineWidth: 1
              }
            }
      },
      elements: {
        line: {
          borderJoinStyle: 'round'
        },
        point: {
          hoverBorderWidth: 3
        }
      }
    }));

    // 获取汇率历史数据
    const fetchRateHistory = async () => {
      if (!selectedCurrency.value) {
        rateHistory.value = [];
        return;
      }
      
      try {
        const response = await rateService.getRateHistory(selectedCurrency.value, 7);
        if (response.data.success) {
          rateHistory.value = response.data.history || [];
          console.log('Rate history loaded:', rateHistory.value.length, 'records');
        } else {
          throw new Error(response.data.message || t('rates.get_rate_history_failed'));
        }
      } catch (err) {
        console.error('Error fetching rate history:', err);
        rateHistory.value = [];
      }
    };

    // 图表事件处理
    const onChartReady = (chartInstance) => {
      console.log('Rate management chart is ready:', chartInstance);
    };

    const onChartError = (error) => {
      console.error('Rate management chart error:', error);
    };

    // 处理趋势图币种选择变更
    const handleTrendCurrencyChange = (currencyCode, currency) => {
      console.log('趋势图币种变更:', currencyCode, currency);
      selectedCurrencyCode.value = currencyCode;
      
      // 找到对应的币种ID
      const rate = validRates.value.find(r => r.currency_code === currencyCode);
      if (rate) {
        selectedCurrency.value = rate.currency_id;
        console.log('设置selectedCurrency为:', rate.currency_id);
      } else {
        selectedCurrency.value = '';
        console.warn('未找到对应的币种ID:', currencyCode);
      }
    };

    const onChartRefresh = () => {
      console.log('Rate management chart is refreshing...');
      if (selectedCurrency.value) {
        fetchRateHistory();
      }
    };

    const formatRateValue = (value) => {
      if (value === null || value === undefined || value === '') {
        return t('rates.chart_no_data');
      }
      const numValue = Number(value);
      if (isNaN(numValue)) {
        return t('rates.chart_no_data');
      }
      return numValue.toFixed(4);
    };

    const isFormValid = computed(() => {
      return (safeNewCurrency.value.buy_rate && safeNewCurrency.value.buy_rate > 0) && 
             (safeNewCurrency.value.sell_rate && safeNewCurrency.value.sell_rate > 0);
    });

    const handleFlagError = (event) => {
      // 如果国家代码的图片加载失败，尝试使用货币代码
      const img = event.target;
      const currentSrc = img.src;
      if (currentSrc.includes('/flags/')) {
        const isCountryCode = currentSrc.includes(img.alt.toLowerCase());
        if (isCountryCode) {
          // 尝试使用货币代码
          const template = currencyTemplates.value.find(t => t.flag_code.toLowerCase() === img.alt.toLowerCase());
          if (template) {
            img.src = `/flags/${template.currency_code}.svg`;
            return;
          }
        }
      }
      img.src = '/flags/unknown.svg';
    };
    
    onBeforeUnmount(() => {
      console.log('RateManagement component is being unmounted');
      isComponentMounted.value = false;
      
      // 安全销毁图表
      if (rateChart.value) {
        try {
          console.log('Cleaning up chart...');
          // 停止所有动画
          rateChart.value.stop();
          // 销毁图表实例
          rateChart.value.destroy();
        } catch (error) {
          console.warn('Chart cleanup error (non-critical):', error);
        } finally {
          rateChart.value = null;
        }
      }
      
      // 清理DOM容器
      if (rateHistory.value) {
        rateHistory.value = [];
      }
      
      // 清理toast定时器
      if (toast.timeout) {
        clearTimeout(toast.timeout);
        toast.timeout = null;
      }
    });

    // 监听selectedCurrency变化
    watch(selectedCurrency, async (newValue) => {
      if (newValue && isComponentMounted.value) {
        console.log('Selected currency changed, fetching rate history...');
        await fetchRateHistory();
      }
    });
    
    // 监听rates变化，确保图表正确初始化
    watch(rates, (newRates) => {
      if (newRates.length > 0 && !selectedCurrency.value && isComponentMounted.value) {
        const firstRateWithData = newRates.find(rate => rate.buy_rate !== null && rate.sell_rate !== null);
        if (firstRateWithData) {
          selectedCurrency.value = firstRateWithData.currency_id;
        }
      }
    }, { immediate: true });
    
    // 选择可兑换外币
    const publishDailyRates = async () => {
      publishing.value = true;
      
      try {
        const response = await rateService.publishDailyRates();
        
        if (response.data.success) {
          showToast(t('rates.daily_rates_published'));
          dailyRatesPublished.value = true;
          
          // 获取发布后的汇率数据
          await fetchRates();
          
          // 根据当前语言设置格式化日期
          const localeMap = {
            'zh-CN': 'zh-CN',
            'en-US': 'en-US', 
            'th-TH': 'th-TH'
          };
          const currentLocale = localeMap[locale.value] || 'zh-CN';
          lastPublishTime.value = new Date().toLocaleString(currentLocale, {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
          }).replace(/\//g, '-');
        } else {
          showToast(response.data.message || t('rates.select_exchangeable_currencies_failed'), 'error');
        }
      } catch (err) {
        console.error('Failed to publish daily rates:', err);
        showToast(t('rates.select_exchangeable_currencies_failed') + ': ' + (err.response?.data?.message || t('rates.network_error')), 'error');
      } finally {
        publishing.value = false;
      }
    };
    
    // 分页后的币种模板列表
    const paginatedCurrencyTemplates = computed(() => {
      const start = (currencyTemplatePagination.current_page - 1) * currencyTemplatePagination.per_page;
      const end = start + currencyTemplatePagination.per_page;
      return currencyTemplates.value.slice(start, end);
    });
    
    // 可见的页码
    const visibleCurrencyTemplatePages = computed(() => {
      const pages = [];
      const current = currencyTemplatePagination.current_page;
      const total = currencyTemplatePagination.total_pages;
      
      // 显示当前页附近的页码
      for (let i = Math.max(1, current - 2); i <= Math.min(total, current + 2); i++) {
        pages.push(i);
      }
      
      return pages;
    });
    
    // 切换币种模板页码
    const changeCurrencyTemplatePage = (page) => {
      if (page >= 1 && page <= currencyTemplatePagination.total_pages) {
        currencyTemplatePagination.current_page = page;
      }
    };
    
    // 更新币种模板分页信息
    const updateCurrencyTemplatePagination = () => {
      currencyTemplatePagination.total = currencyTemplates.value.length;
      currencyTemplatePagination.total_pages = Math.ceil(currencyTemplatePagination.total / currencyTemplatePagination.per_page);
      if (currencyTemplatePagination.current_page > currencyTemplatePagination.total_pages) {
        currencyTemplatePagination.current_page = 1;
      }
    };
    
    // 获取货币名称的多语言翻译
    const getCurrencyNameTranslated = (currencyCode, fallbackName, customFlagFilename) => {
      // 🌟 自定义币种逻辑：如果有自定义图标，直接使用数据库中的名称
      if (customFlagFilename) {
        // console.log(`[自定义币种] ${currencyCode} 使用数据库名称: ${fallbackName}, 自定义图标: ${customFlagFilename}`);
        return fallbackName || currencyCode;
      }
      
      // 调试信息：检查币种信息
      // console.log(`[币种翻译] ${currencyCode}: fallbackName=${fallbackName}, customFlagFilename=${customFlagFilename}`);
      
      // 优先使用翻译，而不是数据库中的值
      const currentLang = locale.value === 'zh-CN' ? 'zh' : locale.value === 'en-US' ? 'en' : 'th';
      const translatedName = getCurrencyName(currencyCode, currentLang, null);
      if (translatedName && translatedName !== currencyCode) {
        return translatedName;
      }
      // 如果没有翻译，使用数据库中的自定义名称
      if (fallbackName) {
        return fallbackName;
      }
      return currencyCode;
    };
    
    // 获取国家名称的多语言翻译
    const getCountryNameTranslated = (countryName) => {
      // 优先使用翻译，而不是数据库中的值
      const currentLang = locale.value === 'zh-CN' ? 'zh' : locale.value === 'en-US' ? 'en' : 'th';
      const translatedName = getCountryName(countryName, currentLang);
      if (translatedName && translatedName !== countryName) {
        return translatedName;
      }
      // 如果没有翻译，使用数据库中的自定义名称
      if (countryName && countryName !== '') {
        return countryName;
      }
      return countryName;
    };
    
    // 批量选择相关方法
    const toggleSelectAll = () => {
      if (selectAll.value) {
        selectedCurrencies.value = rates.value.map(rate => rate.currency_code);
        // 当全选时，为所有币种初始化editValues
        rates.value.forEach(rate => {
          if (!editValues[rate.currency_code]) {
            editValues[rate.currency_code] = {
              buyRate: rate.buy_rate,
              sellRate: rate.sell_rate
            };
          }
        });
      } else {
        selectedCurrencies.value = [];
      }
    };
    
    const updateSelectAll = () => {
      if (selectedCurrencies.value.length === rates.value.length) {
        selectAll.value = true;
      } else {
        selectAll.value = false;
      }
      
      // 当币种被选中时，自动初始化editValues，确保有数据可保存
      selectedCurrencies.value.forEach(currencyCode => {
        if (!editValues[currencyCode]) {
          const rate = rates.value.find(r => r.currency_code === currencyCode);
          if (rate) {
            editValues[currencyCode] = {
              buyRate: rate.buy_rate,
              sellRate: rate.sell_rate
            };
          }
        }
      });
    };
    
    const batchSave = async () => {
      if (selectedCurrencies.value.length === 0) {
        showToast(t('rates.select_currencies_to_edit'), 'error');
        return;
      }
      
      console.log('开始批量保存，选中币种:', selectedCurrencies.value);
      console.log('当前editValues:', editValues);
      
      batchSaving.value = true;
      let savedCount = 0;
      
      try {
        // 获取当前登录用户
        const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
        const userName = currentUser.name || currentUser.username || t('rates.system_admin');
        console.log('当前用户:', userName);
        
        // 批量保存选中的币种
        for (const currencyCode of selectedCurrencies.value) {
          console.log(`处理币种: ${currencyCode}`);
          const rate = rates.value.find(r => r.currency_code === currencyCode);
          if (rate) {
            // 确保editValues存在
            if (!editValues[currencyCode]) {
              console.log(`初始化editValues for ${currencyCode}`);
              editValues[currencyCode] = {
                buyRate: rate.buy_rate,
                sellRate: rate.sell_rate
              };
            }
            
            // 获取编辑值，如果没有编辑过就使用当前汇率值
            const editValue = editValues[currencyCode];
            const buyRate = editValue?.buyRate !== undefined ? editValue.buyRate : rate.buy_rate;
            const sellRate = editValue?.sellRate !== undefined ? editValue.sellRate : rate.sell_rate;
            
            console.log(`${currencyCode} - 买入价: ${buyRate}, 卖出价: ${sellRate}`);
            
            // 准备保存数据
            const saveData = {
              currency_id: rate.currency_id,
              buy_rate: parseFloat(buyRate),
              sell_rate: parseFloat(sellRate),
              // 添加批量保存标识
              batch_saved: true,
              is_published: true
            };
            
            console.log(`${currencyCode} 保存数据:`, saveData);
            console.log(`[前端调试] 即将发送API请求到 /api/rates/set_rate`);
            console.log(`[前端调试] 请求数据:`, JSON.stringify(saveData, null, 2));
            
            try {
              // 使用rateService而不是原生fetch，保持一致性
              const response = await rateService.updateRate(saveData);
              console.log(`[前端调试] ${currencyCode} API响应:`, response);
              console.log(`[前端调试] 响应状态:`, response.status);
              console.log(`[前端调试] 响应数据:`, JSON.stringify(response.data, null, 2));
              
              if (response.data && response.data.success) {
                console.log(`${currencyCode} 保存成功`);
                // 更新本地数据
                rate.buy_rate = saveData.buy_rate;
                rate.sell_rate = saveData.sell_rate;
                rate.batchSaved = true;
                rate.batchSavedTime = new Date().toISOString();
                rate.batchSavedBy = userName;
                rate.is_edited_today = true;
                rate.editMode = false;
                
                // 设置发布状态，确保可以被应用发布
                rate.isPublished = true;
                rate.is_published = true;
                rate.last_publish_time = new Date().toISOString();
                rate.publisher_name = userName;
                
                // 清除编辑值
                delete editValues[currencyCode];
                
                savedCount++;
              } else {
                console.error(`保存币种 ${currencyCode} 失败:`, response.data?.message || '未知错误');
              }
            } catch (apiError) {
              console.error(`保存币种 ${currencyCode} API调用失败:`, apiError);
            }
          } else {
            console.error(`找不到币种: ${currencyCode}`);
          }
        }
        
        console.log(`批量保存完成，成功保存: ${savedCount} 种币种`);
        
        // 清除选择
        selectedCurrencies.value = [];
        selectAll.value = false;
        
        // 显示成功消息
        showToast(t('rates.batch_save_success', {count: savedCount}), 'success');
        
      } catch (error) {
        console.error('批量保存失败:', error);
        showToast(t('rates.batch_save_failed'), 'error');
      } finally {
        batchSaving.value = false;
      }
    };
    
    // App角色专用方法
    const showSetTopBoxModal = () => {
      // 生成QR码
      nextTick(() => {
        const qrContainer = document.getElementById('qrCode');
        if (qrContainer) {
          // 清空容器
          qrContainer.innerHTML = '';
          
          // 创建QR码（这里使用简单的文本显示，实际项目中可以使用QR码库）
          const qrText = document.createElement('div');
          qrText.className = 'text-center p-3';
          qrText.innerHTML = `
            <div class="qr-placeholder bg-light border rounded p-4">
              <i class="fas fa-qrcode fa-3x text-muted mb-2"></i>
              <div class="small text-muted">QR码生成中...</div>
            </div>
          `;
          qrContainer.appendChild(qrText);
        }
      });
      
      // 显示模态框
      const modal = new Modal(document.getElementById('setTopBoxModal'));
      modal.show();
    };
    
    const copySetTopBoxUrl = async () => {
      try {
        await navigator.clipboard.writeText(setTopBoxUrl.value);
        showToast('访问链接已复制到剪贴板', 'success');
      } catch (err) {
        console.error('复制失败:', err);
        showToast('复制失败，请手动复制链接', 'error');
      }
    };
    
    return {
      // App角色相关
      isAppRole,
      setTopBoxUrl,
      showSetTopBoxModal,
      copySetTopBoxUrl,
      
      rates,
      loading,
      error,
      publishing,
      applying,
      saving,
      updateTime,
      lastPublishTime,
      dailyRatesPublished,
      editValues,
      selectedCurrency,
      selectedTheme,
      selectedLanguage,
      publishNotes,
      lastPublishInfo,
      displayConfig,
      addingCurrency,
      toast,
      getToastHeaderClass,
      getToastTitle,
      publishedCount,
      // 批量选择相关
      selectedCurrencies,
      selectAll,
      batchSaving,
      fetchRates,
      publishDailyRates,
      onSortEnd,
      removeCurrency,
      showThemeModal,
      applyAndPublish,
      toggleEditMode,
      copyLastRate,
      copyAllLastRates,
      autoSaveAllCopiedRates,
      handleRateChange,
      saveRateChanges,
      showAddCurrencyModal,
      addCurrency,
      handleImageError,
      hideToast,
      currencyTemplates,
      selectedTemplate,
      selectCurrencyTemplate,
      getFlagUrl,
      canAddCurrency,
      safeNewCurrency,
              formatRateValue,
        validRates,
      clearingCache,
      clearPublishCache,
      rateHistory,
      rateChart,
      chartData,
      chartOptions,
      onChartReady,
      onChartError,
      onChartRefresh,
      editingRate,
      currentBranchCurrency,
      confirmSaveRate,
      isFormValid,
      handleFlagError,
      publishRecords,
      publishRecordsLoading,
      selectedRecord,
      pagination,
      loadPublishRecords,
      goToPage,
      previousPage,
      nextPage,
      getVisiblePages,
      viewPublishRecord,
      copyRecordRates,
      getCurrencyNameTranslated,
      getCountryNameTranslated,
      toggleSelectAll,
      updateSelectAll,
      batchSave,
      expandedDates,
      groupedPublishRecords,
      toggleDateExpansion,
      isDateExpanded,
      formatDate,
      formatTime,
      formatDateTime,
      // 币种模板分页相关
      paginatedCurrencyTemplates,
      currencyTemplatePagination,
      visibleCurrencyTemplatePages,
      changeCurrencyTemplatePage,
      copyingAll,
      copying,
      // 趋势图币种选择
      selectedCurrencyCode,
      handleTrendCurrencyChange
    };
  }
};
</script>

<style scoped>
/* 拖拽相关样式 */
.drag-handle {
  padding: 5px;
  cursor: grab;
  user-select: none;
  transition: all 0.2s;
}

.drag-handle:hover {
  background-color: #f8f9fa;
  border-radius: 4px;
}

.drag-handle:active {
  cursor: grabbing;
}

/* 拖拽时的行样式 */
tr[draggable="true"]:hover {
  background-color: #f8f9fa;
}

tr.drag-placeholder {
  background-color: #e3f2fd !important;
  border: 2px dashed #2196f3;
}

/* 拖拽过程中的样式 */
tr:has(.drag-handle):active {
  cursor: grabbing;
}

/* 表格行过渡效果 */
tbody tr {
  transition: all 0.2s ease;
}

.toast {
  opacity: 0;
  transition: opacity 0.3s;
}

.toast.show {
  opacity: 1;
}

.currency-flag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-right: 8px;
}

.modal-lg {
  max-width: 800px;
}

.bg-light {
  background-color: #f8f9fa;
}

.table-hover tbody tr:hover {
  cursor: pointer;
  background-color: rgba(0, 0, 0, 0.075);
}

.table-active {
  background-color: rgba(0, 123, 255, 0.1) !important;
}

.table td {
  vertical-align: middle;
}

.d-flex.align-items-center {
  gap: 8px;
}

.chart-container {
  height: 400px;
  margin-top: 20px;
}

.status-btn {
  padding: 0.25rem;
  margin: 0;
  border: none;
  background: transparent;
  cursor: default;
}

.status-btn i {
  font-size: 1.1rem;
}

/* 转动的黄色时钟动画 */
.spinning-clock {
  animation: clockSpin 2s linear infinite;
  color: #ffc107 !important; /* 确保是黄色 */
}

@keyframes clockSpin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.text-success {
  color: #198754 !important;
}

/* 灰绿色样式 - 用于已修改状态，低饱和度 */
.text-muted-green {
  color: #8c9c8c !important;
  font-weight: normal !important;
}

.text-warning {
  color: #ffc107 !important;
}

.rate-update-info {
  color: #adb5bd !important;
}

/* 删除按钮样式优化 */
.btn-outline-secondary.text-muted {
  border-color: #dee2e6 !important;
  color: #6c757d !important;
  transition: all 0.2s ease;
}

.btn-outline-secondary.text-muted:hover {
  background-color: #f8f9fa !important;
  border-color: #dc3545 !important;
  color: #dc3545 !important;
  transform: scale(1.05);
}

.btn-outline-secondary.text-muted:active {
  background-color: #e9ecef !important;
  transform: scale(0.98);
}

/* 发布状态警告样式 */
.alert-sm {
  padding: 8px 12px;
  font-size: 0.875rem;
  border-radius: 6px;
  margin-bottom: 0;
}

.alert-warning {
  background-color: rgba(255, 193, 7, 0.1);
  border-color: rgba(255, 193, 7, 0.2);
  color: #856404;
}

.alert-info {
  background-color: rgba(13, 202, 240, 0.1);
  border-color: rgba(13, 202, 240, 0.2);
  color: #055160;
}

.alert-success {
  background-color: rgba(25, 135, 84, 0.1);
  border-color: rgba(25, 135, 84, 0.2);
  color: #0a3622;
}

/* 紧凑表格样式 */
.compact-row td {
  padding: 0.5rem 0.75rem !important;
  vertical-align: middle;
  line-height: 1.2;
}

.compact-row .btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
  line-height: 1.2;
}

.rate-update-info-compact {
  font-size: 0.7rem !important;
  line-height: 1.2;
  white-space: nowrap;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.rate-update-info-compact .fw-bold {
  font-weight: 600 !important;
}

/* 表格行紧凑样式 */
.table-sm th,
.table-sm td {
  padding: 0.4rem 0.75rem;
}

/* 操作按钮组紧凑样式 */
.compact-row .d-flex.gap-4 {
  gap: 0.5rem !important;
}

/* 操作列样式优化 */
.rates-table td:last-child,
.table-responsive .table td:last-child {
  white-space: nowrap;
  min-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.rates-table .d-flex.align-items-center.gap-4 {
  gap: 0.5rem !important;
  flex-wrap: nowrap !important;
}

.rates-table .btn-sm {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  min-width: auto;
}

.compact-row .btn {
  font-size: 0.8rem;
  padding: 0.2rem 0.4rem;
  line-height: 1.2;
}

/* 紧凑行高样式 */
.compact-row td {
  padding: 0.5rem 0.25rem !important;
  vertical-align: middle;
  line-height: 1.2;
}

.compact-row th {
  padding: 0.5rem 0.25rem !important;
  vertical-align: middle;
  line-height: 1.2;
}

/* 币种列样式优化 */
.compact-row .currency-flag {
  width: 20px;
  height: 14px;
}

/* 汇率输入框样式 */
.compact-row input[type="number"] {
  font-size: 0.875rem;
  padding: 0.25rem 0.5rem;
  height: auto;
}

/* 树形结构样式 */
.date-group-row {
  background-color: #f8f9fa !important;
  border-left: 4px solid #007bff;
  font-weight: 600;
}

.date-group-row:hover {
  background-color: #e9ecef !important;
}

.child-record-row {
  background-color: #ffffff !important;
  border-left: 4px solid #dee2e6;
}

.child-record-row:hover {
  background-color: #f8f9fa !important;
}

.child-record-row td:first-child {
  border-left: 2px solid #6c757d;
  padding-left: 1rem;
}

.date-group-row td {
  padding: 0.75rem;
  vertical-align: middle;
}

.child-record-row td {
  padding: 0.5rem 0.75rem;
  vertical-align: middle;
}

/* 展开/折叠图标过渡动画 */
.fa-chevron-right, .fa-chevron-down {
  transition: transform 0.2s ease;
}

.date-group-row:hover .fa-chevron-right {
  transform: rotate(90deg);
}

.date-group-row:hover .fa-chevron-down {
  transform: rotate(180deg);
}

/* 日期节点样式 */
.date-group-row .badge {
  font-size: 0.75rem;
  font-weight: 500;
}

.child-record-row .badge {
  font-size: 0.7rem;
}

/* 操作按钮样式 */
.child-record-row .btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.8rem;
}

/* 币种列表样式 */
.compact-row .currency-flag {
  width: 20px;
  height: 14px;
}

/* 汇率输入框样式 */
.compact-row input[type="number"] {
  font-size: 0.875rem;
  padding: 0.25rem 0.5rem;
  height: auto;
}

/* App角色手机端专用样式 */
.app-rates-view {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  padding-bottom: 80px;
  overflow-x: hidden;
}



/* 隐藏性能监控浮动按钮 */
.app-rates-view .performance-monitor {
  display: none !important;
}

.app-rates-view .card {
  border-radius: 15px;
  border: none;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.app-rates-view .card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

.app-rates-view .card-header {
  border-radius: 15px 15px 0 0 !important;
  border-bottom: none;
}

.app-rates-view .card-body {
  border-radius: 0 0 15px 15px;
}

/* 状态图标 */
.status-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}

.status-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: #495057;
  margin-bottom: 0.2rem;
}

.status-subtitle {
  font-size: 0.8rem;
  color: #6c757d;
}

/* 汇率列表样式 */
.rate-list {
  max-height: 300px;
  overflow-y: auto;
}

.rate-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  transition: background-color 0.2s ease;
}

.rate-item:last-child {
  border-bottom: none;
}

.rate-item:hover {
  background-color: #f8f9fa;
}

.rate-currency {
  display: flex;
  align-items: center;
  font-weight: 600;
  color: #495057;
}

.rate-values {
  display: flex;
  gap: 1rem;
  font-size: 0.9rem;
}

.rate-buy {
  color: #28a745;
  font-weight: 600;
}

.rate-sell {
  color: #dc3545;
  font-weight: 600;
}

/* 发布记录列表样式 */
.publish-list {
  max-height: 200px;
  overflow-y: auto;
}

.publish-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  transition: background-color 0.2s ease;
}

.publish-item:last-child {
  border-bottom: none;
}

.publish-item:hover {
  background-color: #f8f9fa;
}

.publish-time {
  font-size: 0.8rem;
  color: #6c757d;
}

.publish-info {
  font-size: 0.8rem;
  color: #495057;
  font-weight: 500;
}

/* 机顶盒模态框样式 */
.qr-code-container {
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.qr-placeholder {
  text-align: center;
  padding: 2rem;
}

/* 手机端响应式调整 */
@media (max-width: 768px) {
  .app-rates-view .container-fluid {
    padding-left: 10px;
    padding-right: 10px;
  }
  
  .app-rates-view .card-body {
    padding: 1rem;
  }
  
  .status-icon {
    width: 35px;
    height: 35px;
    font-size: 14px;
  }
  
  .rate-values {
    gap: 0.5rem;
    font-size: 0.8rem;
  }
}

/* 发布机顶盒模态框宽度限制 */
#themeModal .modal-dialog {
  max-width: 500px !important;
  width: 90% !important;
}

@media (min-width: 576px) {
  #themeModal .modal-dialog {
    max-width: 450px !important;
    width: auto !important;
  }
}

@media (min-width: 768px) {
  #themeModal .modal-dialog {
    max-width: 500px !important;
    width: auto !important;
  }
}

@media (min-width: 992px) {
  #themeModal .modal-dialog {
    max-width: 550px !important;
    width: auto !important;
  }
}

/* 强制覆盖所有可能的模态框宽度设置 */
#themeModal .modal-dialog,
#themeModal .modal-content {
  max-width: 500px !important;
  width: 90% !important;
}

@media (min-width: 576px) {
  #themeModal .modal-dialog,
  #themeModal .modal-content {
    max-width: 450px !important;
    width: auto !important;
  }
}

@media (min-width: 768px) {
  #themeModal .modal-dialog,
  #themeModal .modal-content {
    max-width: 500px !important;
    width: auto !important;
  }
}

@media (min-width: 992px) {
  #themeModal .modal-dialog,
  #themeModal .modal-content {
    max-width: 550px !important;
    width: auto !important;
  }
}

/* 保存确认模态框宽度限制 */
#saveConfirmModal .modal-dialog {
  max-width: 500px !important;
  width: 90% !important;
}

@media (min-width: 576px) {
  #saveConfirmModal .modal-dialog {
    max-width: 450px !important;
    width: auto !important;
  }
}

@media (min-width: 768px) {
  #saveConfirmModal .modal-dialog {
    max-width: 500px !important;
    width: auto !important;
  }
}

@media (min-width: 992px) {
  #saveConfirmModal .modal-dialog {
    max-width: 550px !important;
    width: auto !important;
  }
}

/* 强制覆盖所有可能的确认模态框宽度设置 */
#saveConfirmModal .modal-dialog,
#saveConfirmModal .modal-content {
  max-width: 500px !important;
  width: 90% !important;
}

@media (min-width: 576px) {
  #saveConfirmModal .modal-dialog,
  #saveConfirmModal .modal-content {
    max-width: 450px !important;
    width: auto !important;
  }
}

@media (min-width: 768px) {
  #saveConfirmModal .modal-dialog,
  #saveConfirmModal .modal-content {
    max-width: 500px !important;
    width: auto !important;
  }
}

@media (min-width: 992px) {
  #saveConfirmModal .modal-dialog,
  #saveConfirmModal .modal-content {
    max-width: 550px !important;
    width: auto !important;
  }
}

</style>

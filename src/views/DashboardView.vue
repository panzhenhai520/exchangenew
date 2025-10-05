<template>
  <div class="dashboard-view">
    <div class="container-fluid py-4">
      <div class="row">
        <div class="col-12">
          <div class="d-flex justify-content-between align-items-center mb-4">
            <h2 class="page-title-bold">
              <font-awesome-icon :icon="['fas', 'home']" class="me-2" />
              {{ $t('dashboard.title') }}
            </h2>
          </div>
          
          <div v-if="loading" class="text-center my-5">
            <div class="spinner-border text-primary" role="status">
                          <span class="visually-hidden">{{ $t('dashboard.loading') }}</span>
          </div>
          <p class="mt-2">{{ $t('dashboard.loading_data') }}</p>
          </div>
          
          <div v-else-if="error" class="alert alert-danger my-4">
            <font-awesome-icon :icon="['fas', 'exclamation-circle']" class="me-2" />
            {{ $t('dashboard.load_data_failed') }}: {{ error }}
            <button class="btn btn-outline-danger btn-sm ms-3" @click="fetchAllData">
              <font-awesome-icon :icon="['fas', 'sync']" class="me-1" />
              {{ $t('dashboard.retry') }}
            </button>
          </div>
          
          <div v-else>
            <!-- 主要内容区域 -->
            <div class="row g-3">
              <!-- 左侧：汇率卡片 - 调整为9列，让汇率卡片更宽 -->
              <div class="col-md-9">
                <div class="row g-3">
                  <div v-for="rate in rates" :key="rate.id" class="col-md-4">
                    <div class="card rate-card h-100">
                      <div class="card-header py-2 custom-header text-dark">
                                                  <div class="d-flex align-items-center">
                            <CurrencyFlag :code="rate.currency_code || 'USD'" :custom-filename="rate.custom_flag_filename" :width="40" :height="30" class="me-2" />
                            <h5 class="mb-0 fs-6">{{ rate.currency_code }} - {{ getCurrencyDisplayName(rate.currency_code) }}</h5>
                          </div>
                      </div>
                      <div class="card-body py-2">
                        <div class="row g-2">
                          <div class="col-6 text-center border-end">
                            <div class="text-muted small mb-1">{{ $t('dashboard.buy_rate') }}</div>
                            <div class="rate-value">
                              {{ formatRateValue(rate.buy_rate) }}
                            </div>
                          </div>
                          <div class="col-6 text-center">
                            <div class="text-muted small mb-1">{{ $t('dashboard.sell_rate') }}</div>
                            <div class="rate-value">
                              {{ formatRateValue(rate.sell_rate) }}
                            </div>
                          </div>
                        </div>
                        <div class="text-center mt-2">
                          <small class="text-muted">{{ $t('dashboard.last_updated') }}: {{ formatDateTime(rate.rate_date) }}</small>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- 右侧：汇率图表和业务统计 - 调整为3列 -->
              <div class="col-md-3">
                <!-- 汇率走势图 - 适中高度 -->
                <div class="card trend-card-enhanced mb-3">
                  <div class="card-header py-2 bg-light">
                    <div class="d-flex justify-content-between align-items-center">
                      <h6 class="mb-0 fs-6">{{ $t('dashboard.rate_trends') }}</h6>
                      <div class="currency-selector">
                        <select 
                          class="form-select form-select-sm" 
                          v-model="selectedCurrency" 
                          :disabled="!currencies?.length"
                          style="z-index: 1000;"
                        >
                          <option value="">{{ $t('common.please_select_currency') }}</option>
                          <option v-for="currency in currencies" :key="currency.id" :value="currency.id">
                            {{ currency.currency_code }} - {{ getCurrencyDisplayName(currency.currency_code) }}
                          </option>
                        </select>
                      </div>
                    </div>
                  </div>
                  <div class="card-body p-0 chart-container-enhanced">
                    <!-- 异步图表 - 适中版 -->
                    <div class="p-2">
                      <AsyncChart
                        ref="dashboardChart"
                        :chart-data="chartData"
                        :chart-options="chartOptions"
                        :loading-delay="300"
                        height="320px"
                        :show-toolbar="false"
                        :auto-refresh="false"
                        @chart-ready="onChartReady"
                        @chart-error="onChartError"
                      />
                    </div>
                  </div>
                </div>

                <!-- 业务统计卡片区域 -->
                <div class="business-stats-container">
                  <!-- 加载状态 -->
                  <div v-if="businessStatsLoading" class="text-center text-muted py-4">
                    <i class="fas fa-spinner fa-spin fa-2x mb-2"></i>
                                          <p>{{ $t('dashboard.loading_business_stats') }}</p>
                  </div>
                  
                  <!-- 统计数据 -->
                  <div v-else-if="businessStats" class="row g-2">
                    <!-- 交易统计 -->
                    <div class="col-6">
                      <div class="card stats-card h-100">
                        <div class="card-body p-2">
                          <div class="d-flex align-items-center">
                            <div class="stats-icon bg-primary">
                              <i class="fas fa-exchange-alt"></i>
                            </div>
                            <div class="ms-2">
                              <div class="stats-title">{{ $t('dashboard.seven_day_transactions') }}</div>
                              <div class="stats-value">
                                {{ businessStats.transaction_trend.reduce((sum, item) => sum + item.count, 0) }}{{ $t('dashboard.transactions_unit') }}
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    <!-- 冲正统计 -->
                    <div class="col-6">
                      <div class="card stats-card h-100">
                        <div class="card-body p-2">
                          <div class="d-flex align-items-center">
                            <div class="stats-icon bg-warning">
                              <i class="fas fa-undo"></i>
                            </div>
                            <div class="ms-2">
                              <div class="stats-title">{{ $t('dashboard.seven_day_reversals') }}</div>
                              <div class="stats-value">
                                {{ businessStats.reversal_trend.reduce((sum, item) => sum + item.count, 0) }}{{ $t('dashboard.transactions_unit') }}
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    <!-- 汇率发布状态 -->
                    <div class="col-12">
                      <div class="card stats-card">
                        <div class="card-body p-2">
                          <div class="d-flex align-items-center justify-content-between">
                            <div class="d-flex align-items-center">
                              <div class="stats-icon bg-success">
                                <i class="fas fa-clock"></i>
                              </div>
                              <div class="ms-2">
                                <div class="stats-title">{{ $t('dashboard.rate_publishing') }}</div>
                                <div class="stats-subtitle">
                                  {{ businessStats.rate_publish_status.last_publish_time ? 
                                    formatDateTime(businessStats.rate_publish_status.last_publish_time) : $t('dashboard.no_publish_data') }}
                                </div>
                              </div>
                            </div>
                            <div class="badge bg-light text-dark">
                              {{ businessStats.rate_publish_status.total_currencies }}{{ $t('dashboard.currencies_unit') }}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    <!-- 外币排行 -->
                    <div class="col-12">
                      <div class="card stats-card">
                        <div class="card-body p-2">
                          <div class="stats-title mb-2">
                            <i class="fas fa-trophy text-warning me-1"></i>
                            {{ $t('dashboard.popular_currencies') }}
                          </div>
                          <div class="row g-2">
                            <div class="col-6 ranking-col-left">
                              <div class="ranking-section">
                                <div class="ranking-title">{{ $t('dashboard.buy_top3') }}</div>
                                <div v-if="businessStats.buy_ranking.length > 0">
                                  <div v-for="(item, index) in businessStats.buy_ranking" 
                                       :key="'buy-' + index" 
                                       class="ranking-item">
                                    <span class="ranking-num">{{ index + 1 }}</span>
                                    <span class="ranking-currency">{{ getCurrencyDisplayName(item.currency_code) }}</span>
                                    <span class="ranking-count">{{ item.count }}{{ $t('dashboard.transactions_unit') }}</span>
                                  </div>
                                </div>
                                <div v-else class="text-muted small">{{ $t('dashboard.no_data') }}</div>
                              </div>
                            </div>
                            <div class="col-6 ranking-col-right">
                              <div class="ranking-section">
                                <div class="ranking-title">{{ $t('dashboard.sell_top3') }}</div>
                                <div v-if="businessStats.sell_ranking.length > 0">
                                  <div v-for="(item, index) in businessStats.sell_ranking" 
                                       :key="'sell-' + index" 
                                       class="ranking-item">
                                    <span class="ranking-num">{{ index + 1 }}</span>
                                    <span class="ranking-currency">{{ getCurrencyDisplayName(item.currency_code) }}</span>
                                    <span class="ranking-count">{{ item.count }}{{ $t('dashboard.transactions_unit') }}</span>
                                  </div>
                                </div>
                                <div v-else class="text-muted small">{{ $t('dashboard.no_data') }}</div>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    <!-- 余额预警 -->
                    <div class="col-12">
                      <div class="card stats-card">
                        <div class="card-body p-2">
                          <div class="d-flex align-items-center justify-content-between mb-2">
                            <div class="d-flex align-items-center">
                              <div class="stats-icon bg-danger">
                                <i class="fas fa-exclamation-triangle"></i>
                              </div>
                              <div class="ms-2">
                                <div class="stats-title">{{ $t('dashboard.balance_alerts') }}</div>
                                <div class="stats-value">
                                  {{ businessStats.balance_alerts.low_alerts + businessStats.balance_alerts.high_alerts }}{{ $t('dashboard.items_unit') }}
                                </div>
                              </div>
                            </div>
                          </div>
                          <!-- 预警详情 -->
                          <div v-if="businessStats.balance_alerts.alert_details && businessStats.balance_alerts.alert_details.length > 0" 
                               class="alert-details">
                            <div v-for="(alert, index) in businessStats.balance_alerts.alert_details" 
                                 :key="index" 
                                 class="alert-item">
                              <span class="alert-currency">{{ getCurrencyDisplayName(alert.currency_code) }}</span>
                              <span :class="['alert-type', 'text-danger']">
                                {{ alert.type === 'low' ? $t('dashboard.balance_low') : $t('dashboard.balance_high') }}
                              </span>
                            </div>
                          </div>
                          <div v-else-if="(businessStats.balance_alerts.low_alerts + businessStats.balance_alerts.high_alerts) === 0" 
                               class="text-muted small">
                            暂无预警
                          </div>
                        </div>
                      </div>
                    </div>

                    <!-- 交易报警事件 -->
                    <div class="col-12" v-if="transactionAlerts">
                      <div class="card stats-card">
                        <div class="card-body p-2">
                          <div class="d-flex align-items-center justify-content-between mb-2">
                            <div class="d-flex align-items-center">
                              <div class="stats-icon bg-warning">
                                <i class="fas fa-bell"></i>
                              </div>
                              <div class="ms-2">
                                <div class="stats-title">{{ $t('dashboard.transaction_alerts') }}</div>
                                <div class="stats-value">
                                  {{ transactionAlerts.statistics.unresolved_alerts }}{{ $t('dashboard.alerts_unit') }}
                                </div>
                              </div>
                            </div>
                            <div class="badge bg-light text-dark">
                              7{{ $t('dashboard.days_unit') }} {{ transactionAlerts.statistics.total_alerts }}{{ $t('dashboard.items_unit') }}
                            </div>
                          </div>
                          <!-- 最近报警事件 -->
                          <div v-if="transactionAlerts.statistics.recent_alerts && transactionAlerts.statistics.recent_alerts.length > 0" 
                               class="alert-details">
                            <div v-for="(alert, index) in transactionAlerts.statistics.recent_alerts.slice(0, 3)" 
                                 :key="index" 
                                 class="alert-item">
                              <span class="alert-currency">{{ getCurrencyDisplayName(alert.currency_code) }}</span>
                              <span :class="['alert-type', alert.alert_level === 'critical' ? 'text-danger' : 'text-warning']">
                                {{ alert.alert_level === 'critical' ? $t('dashboard.critical') : $t('dashboard.warning') }}
                              </span>
                              <span class="alert-time text-muted small">
                                {{ formatDateTime(alert.created_at).split(' ')[1] }}
                              </span>
                            </div>
                          </div>
                          <div v-else class="text-muted small">
                            {{ $t('dashboard.no_unresolved_alerts') }}
                          </div>
                        </div>
                      </div>
                    </div>

                    <!-- 日结状态 -->
                    <div class="col-12">
                      <div class="card stats-card">
                        <div class="card-body p-2">
                          <div class="d-flex align-items-center justify-content-between">
                            <div class="d-flex align-items-center">
                              <div class="stats-icon bg-info">
                                <i class="fas fa-calendar-check"></i>
                              </div>
                              <div class="ms-2">
                                <div class="stats-title">{{ $t('dashboard.recent_eod') }}</div>
                                <div class="stats-subtitle">
                                  <div v-if="businessStats.eod_status.last_eod_time">
                                    {{ formatDateTime(businessStats.eod_status.last_eod_time).split(' ')[0] }}
                                    <span class="text-primary ms-1">
                                      {{ formatDateTime(businessStats.eod_status.last_eod_time).split(' ')[1] }}
                                    </span>
                                  </div>
                                  <div v-else class="text-muted">{{ $t('dashboard.no_eod_data') }}</div>
                                </div>
                              </div>
                            </div>
                            <div v-if="businessStats.eod_status.eod_operator_name" class="text-end">
                              <div class="badge bg-light text-dark">
                                {{ businessStats.eod_status.eod_operator_name }}
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <!-- 无数据状态 -->
                  <div v-else class="text-center text-muted py-4">
                    <i class="fas fa-chart-bar fa-2x mb-2"></i>
                    <p>{{ $t('dashboard.no_business_stats') }}</p>
                    <button class="btn btn-sm btn-outline-primary" @click="fetchBusinessStats">
                      <i class="fas fa-refresh me-1"></i>{{ $t('dashboard.reload') }}
                    </button>
                  </div>
                </div>
                
                <!-- 嵌入式性能监控面板 -->
                <div class="card performance-stats-card mt-3" v-if="performanceMonitorEnabled">
                  <div class="card-header py-2 bg-light">
                    <div class="d-flex justify-content-between align-items-center">
                      <h6 class="mb-0 fs-6">
                        <i class="fas fa-tachometer-alt me-1"></i>
                        {{ $t('dashboard.performance_monitor.title') }} ({{ performanceMonitorEnabled ? $t('dashboard.performance_monitor.debug_enabled') : $t('dashboard.performance_monitor.debug_disabled') }})
                      </h6>
                      <div class="performance-controls">
                        <button 
                          class="btn btn-sm btn-outline-secondary me-1"
                          @click="refreshPerformanceData"
                          :disabled="performanceRefreshing"
                          :title="$t('dashboard.performance_monitor.refresh_data')"
                        >
                          <i class="fas fa-sync" :class="{ 'fa-spin': performanceRefreshing }"></i>
                        </button>
                        <button 
                          class="btn btn-sm btn-outline-danger me-1"
                          @click="clearPerformanceData"
                          :title="$t('dashboard.performance_monitor.clear_data')"
                        >
                          <i class="fas fa-trash"></i>
                        </button>
                        <button 
                          class="btn btn-sm btn-outline-warning"
                          @click="togglePerformanceMonitor"
                          :title="$t('dashboard.performance_monitor.close_monitoring')"
                        >
                          <i class="fas fa-times"></i>
                        </button>
                      </div>
                    </div>
                  </div>
                  <div class="card-body p-2 performance-content">
                    <!-- 基本指标 -->
                    <div class="performance-section mb-3">
                      <h6 class="section-title mb-2">{{ $t('dashboard.performance_monitor.basic_metrics') }}</h6>
                      <div class="metrics-grid-compact">
                        <div class="metric-item-compact">
                          <div class="metric-label-compact">{{ $t('dashboard.performance_monitor.page_load') }}</div>
                          <div class="metric-value-compact" :class="getPerformanceClass(performanceTiming.loadComplete)">
                            {{ formatDuration(performanceTiming.loadComplete) }}
                            <small class="text-muted">({{ performanceTiming.loadComplete }})</small>
                          </div>
                        </div>
                        <div class="metric-item-compact">
                          <div class="metric-label-compact">{{ $t('dashboard.performance_monitor.dom_ready') }}</div>
                          <div class="metric-value-compact" :class="getPerformanceClass(performanceTiming.domReady)">
                            {{ formatDuration(performanceTiming.domReady) }}
                          </div>
                        </div>
                        <div class="metric-item-compact">
                          <div class="metric-label-compact">{{ $t('dashboard.performance_monitor.memory_usage') }}</div>
                          <div class="metric-value-compact" :class="getMemoryClass(performanceMemory.usedJSHeapSize)">
                            {{ formatMemory(performanceMemory.usedJSHeapSize) }}
                          </div>
                        </div>
                        <div class="metric-item-compact">
                          <div class="metric-label-compact">{{ $t('dashboard.performance_monitor.cache_hit_rate') }}</div>
                          <div class="metric-value-compact" :class="getCacheHitRateClass(performanceCache.hitRate)">
                            {{ (performanceCache.hitRate * 100).toFixed(1) }}%
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <!-- API性能 -->
                    <div class="performance-section mb-3" v-if="performanceApiMetrics.length > 0">
                      <h6 class="section-title mb-2">{{ $t('dashboard.performance_monitor.api_performance') }}</h6>
                      <div class="api-metrics-compact">
                        <div 
                          v-for="metric in performanceApiMetrics.slice(0, 3)" 
                          :key="metric.name"
                          class="api-metric-item-compact"
                        >
                          <div class="api-name-compact">{{ metric.name }}</div>
                          <div class="api-duration-compact" :class="getPerformanceClass(metric.duration)">
                            {{ formatDuration(metric.duration) }}
                          </div>
                          <div class="api-status-compact" :class="metric.status === 'success' ? 'text-success' : 'text-danger'">
                            <i class="fas" :class="metric.status === 'success' ? 'fa-check' : 'fa-times'"></i>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <!-- 缓存统计 -->
                    <div class="performance-section">
                      <h6 class="section-title mb-2">{{ $t('dashboard.performance_monitor.cache_statistics') }}</h6>
                      <div class="cache-stats-compact">
                        <div class="cache-stat-compact">
                          <span class="stat-label-compact">{{ $t('dashboard.performance_monitor.size') }}:</span>
                          <span class="stat-value-compact">{{ performanceCache.size }}/{{ performanceCache.maxSize }}</span>
                        </div>
                        <div class="cache-stat-compact">
                          <span class="stat-label-compact">{{ $t('dashboard.performance_monitor.hits') }}:</span>
                          <span class="stat-value-compact text-success">{{ performanceCache.hits }}</span>
                        </div>
                        <div class="cache-stat-compact">
                          <span class="stat-label-compact">{{ $t('dashboard.performance_monitor.misses') }}:</span>
                          <span class="stat-value-compact text-warning">{{ performanceCache.misses }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- 调试信息 -->
                <div class="card mt-3 border-info">
                  <div class="card-body p-2">
                    <h6 class="text-info">{{ $t('dashboard.performance_monitor.debug_info') }}</h6>
                    <small class="text-muted">
                      {{ $t('dashboard.performance_monitor.performance_monitor_enabled') }}: {{ performanceMonitorEnabled }}<br>
                      {{ $t('dashboard.performance_monitor.browser_environment') }}: {{ typeof window !== 'undefined' }}<br>
                      {{ $t('dashboard.performance_monitor.current_time') }}: {{ new Date().toLocaleTimeString() }}
                    </small>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 性能监控控制 -->
    <div class="performance-control">
      <button 
        @click="togglePerformanceMonitor" 
        class="btn btn-sm btn-outline-secondary"
        :title="performanceMonitorEnabled ? $t('dashboard.performance_monitor.close_monitor') : $t('dashboard.performance_monitor.enable_monitor')"
      >
        <i class="fas fa-tachometer-alt"></i>
        {{ performanceMonitorEnabled ? $t('dashboard.performance_monitor.close_monitor') : $t('dashboard.performance_monitor.enable_monitor') }}
      </button>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount, watch, computed } from 'vue';
import CurrencyFlag from '@/components/CurrencyFlag.vue'
import AsyncChart from '@/components/AsyncChart.vue'
import { hasPermission, hasAnyPermission } from '@/utils/permissions'
import { formatDateTime } from '@/utils/formatters'
import { useDebouncedSearch } from '@/services/api/enhancedApiService'
import api from '@/services/api'
import dashboardService from '@/services/api/dashboardService'
import { usePerformance } from '@/utils/performance'
import { getCurrencyName } from '@/utils/currencyTranslator'
import { useI18n } from 'vue-i18n'

export default {
  name: 'DashboardView',
  components: {
    CurrencyFlag,
    AsyncChart
  },
  setup() {
    const { t, locale } = useI18n();
    const rates = ref([]);
    const currencies = ref([]);
    const selectedCurrency = ref(null);
    const loading = ref(true);
    const error = ref(null);
    const rateHistory = ref([]);
    const isComponentMounted = ref(false);
    const refreshTimer = ref(null);
    const dashboardChart = ref(null);

    // 业务统计数据
    const businessStats = ref(null);
    const businessStatsLoading = ref(false);
    const businessStatsCache = ref({
      data: null,
      timestamp: null,
      CACHE_DURATION: 5 * 60 * 1000 // 5分钟缓存
    });

    // 交易报警事件数据
    const transactionAlerts = ref(null);
    const transactionAlertsLoading = ref(false);
    
    // 性能监控控制
    const isDevelopmentMode = ref(process.env.NODE_ENV === 'development');
    const performanceMonitorEnabled = ref(true); // 强制开启，方便调试
    console.log('性能监控状态：', performanceMonitorEnabled.value);
    
    // 性能监控数据
    const performanceRefreshing = ref(false);
    const performanceTiming = ref({
      loadComplete: 0,
      domReady: 0,
      domContentLoaded: 0
    });
    const performanceMemory = ref({
      usedJSHeapSize: 0,
      totalJSHeapSize: 0,
      jsHeapSizeLimit: 0
    });
    const performanceCache = ref({
      size: 0,
      maxSize: 0,
      hits: 0,
      misses: 0,
      hitRate: 0
    });
    const performanceApiMetrics = ref([]);

    // 性能优化工具
    const { performanceMonitor, throttle, cache: performanceCacheAPI } = usePerformance();
    // const dashboardApi = useEnhancedApi('dashboard'); // 暂时注释掉，使用标准API
    
    // 防抖搜索
    const { search: debouncedFetchRateHistory } = useDebouncedSearch(fetchRateHistory, 300);

    // 图表数据和配置
    const chartData = computed(() => {
      console.log('Dashboard chartData computed:', {
        rateHistoryLength: rateHistory.value?.length || 0,
        rateHistory: rateHistory.value
      });
      
      // 确保 rateHistory.value 存在且是数组
      if (!rateHistory.value || !Array.isArray(rateHistory.value) || rateHistory.value.length === 0) {
        console.log('Dashboard: No rate history data available');
        return {
          labels: [],
          datasets: []
        };
      }

      try {
        const result = {
          labels: rateHistory.value.map(item => {
            if (!item || !item.date) {
              console.warn('Invalid history item:', item);
              return '';
            }
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
          }).filter(label => label !== ''), // 过滤掉无效的标签
          datasets: [
            {
              label: t('rates.buy_rate_label'),
              data: rateHistory.value.map(item => item?.buy_rate || 0).filter(rate => rate !== null),
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
              data: rateHistory.value.map(item => item?.sell_rate || 0).filter(rate => rate !== null),
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
        
        console.log('Dashboard: Generated chart data:', result);
        return result;
      } catch (error) {
        console.error('Error generating chart data:', error);
        return {
          labels: [],
          datasets: []
        };
      }
    });

    const chartOptions = computed(() => ({
      responsive: true,
      maintainAspectRatio: false,
      layout: {
        padding: {
          top: 10,
          right: 10,
          bottom: 30,
          left: 10
        }
      },
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
            },
            padding: {
              top: 10
            }
          },
          grid: {
            display: false
          },
          ticks: {
            maxRotation: 45,
            minRotation: 0,
            font: {
              size: 10
            },
            padding: 5,
            maxTicksLimit: 8
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
            },
            padding: 5
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

    // 性能监控的获取汇率函数
    const fetchRates = async () => {
      performanceMonitor.mark('dashboard_fetch_rates_start');
      loading.value = true;
      error.value = null;
      
      try {
        // 获取当前网点所有汇率数据，不限制只获取已发布的汇率
        const response = await api.get('/rates/all', {
          params: { 
            published_only: false,
            include_publish_info: true 
          }
        });
        
        if (response.data && response.data.success) {
          rates.value = response.data.rates;
          performanceMonitor.mark('dashboard_fetch_rates_success');
        } else {
          throw new Error(response.data?.message || t('dashboard.get_rates_failed'));
        }
      } catch (err) {
        console.error('Failed to fetch rates:', err);
        error.value = err.message || t('dashboard.network_error');
        performanceMonitor.mark('dashboard_fetch_rates_error');
      } finally {
        loading.value = false;
        performanceMonitor.measure('dashboard_fetch_rates_duration', 'dashboard_fetch_rates_start');
      }
    };

    const fetchCurrencies = async () => {
      performanceMonitor.mark('dashboard_fetch_currencies_start');
      
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          throw new Error('No token available');
        }
        
        console.log('Fetching currencies...');
        // 获取当前网点所有币种，不限制只获取已发布的币种
        const response = await api.get('/rates/available_currencies', {
          params: { published_only: false }
        });
        
        console.log('Currencies response:', response);
        
        if (response.data && response.data.success) {
          currencies.value = response.data.currencies || [];
          console.log('Loaded currencies:', currencies.value);
          
          if (currencies.value.length === 0) {
            console.warn('No currencies available');
            return;
          }
          
          if (!selectedCurrency.value && currencies.value.length > 0) {
            console.log('Setting default currency:', currencies.value[0]);
            selectedCurrency.value = currencies.value[0].id;
          }
          
          performanceMonitor.mark('dashboard_fetch_currencies_success');
        } else {
          throw new Error(response.data?.message || t('dashboard.get_currencies_failed'));
        }
      } catch (err) {
        console.error('Error fetching currencies:', err);
        error.value = err.message || t('dashboard.network_error');
        performanceMonitor.mark('dashboard_fetch_currencies_error');
      } finally {
        performanceMonitor.measure('dashboard_fetch_currencies_duration', 'dashboard_fetch_currencies_start');
      }
    };

    // 防抖的汇率历史获取函数
    async function fetchRateHistory() {
      if (!selectedCurrency.value) {
        console.log('Dashboard: No currency selected for rate history');
        rateHistory.value = [];
        return;
      }
      
      performanceMonitor.mark('dashboard_fetch_history_start');
      console.log('Dashboard: Fetching rate history for currency:', selectedCurrency.value);
      
      try {
        // 使用标准API服务
        const response = await api.get(`/rates/currency/${selectedCurrency.value}/history`, {
          params: { days: 7 }
        });
        
        console.log('Dashboard: Rate history response:', response);
        
        if (response.data && response.data.success) {
          rateHistory.value = response.data.history || [];
          console.log('Rate history loaded:', rateHistory.value.length, 'records');
          console.log('Rate history data:', rateHistory.value);
          performanceMonitor.mark('dashboard_fetch_history_success');
        } else {
          console.error('Dashboard: Failed to fetch rate history:', response.data?.message);
          throw new Error(response.data?.message || t('dashboard.get_rate_history_failed'));
        }
      } catch (err) {
        console.error('Error fetching rate history:', err);
        rateHistory.value = [];
        performanceMonitor.mark('dashboard_fetch_history_error');
      } finally {
        performanceMonitor.measure('dashboard_fetch_history_duration', 'dashboard_fetch_history_start');
      }
    }

    // 获取业务统计数据（带缓存）
    const fetchBusinessStats = async () => {
      // 检查缓存
      const now = Date.now();
      if (businessStatsCache.value.data && 
          businessStatsCache.value.timestamp && 
          (now - businessStatsCache.value.timestamp) < businessStatsCache.value.CACHE_DURATION) {
        console.log('Dashboard: Using cached business stats');
        businessStats.value = businessStatsCache.value.data;
        return;
      }

      if (businessStatsLoading.value) {
        console.log('Dashboard: Business stats already loading');
        return;
      }

      businessStatsLoading.value = true;
      
      try {
        console.log('Dashboard: Fetching business stats');
        const response = await dashboardService.getBusinessStats();
        
        if (response.data.success) {
          businessStats.value = response.data.data;
          // 更新缓存
          businessStatsCache.value = {
            data: response.data.data,
            timestamp: now,
            CACHE_DURATION: 5 * 60 * 1000
          };
          console.log('Dashboard: Business stats loaded successfully');
        } else {
          throw new Error(response.data.message || '获取业务统计失败');
        }
      } catch (err) {
        console.error('Error fetching business stats:', err);
        businessStats.value = null;
      } finally {
        businessStatsLoading.value = false;
      }
    };

    // 获取交易报警事件统计
    const fetchTransactionAlerts = async () => {
      if (transactionAlertsLoading.value) {
        console.log('Dashboard: Transaction alerts already loading');
        return;
      }

      transactionAlertsLoading.value = true;
      
      try {
        console.log('Dashboard: Fetching transaction alerts statistics');
        
        // 使用统一的API服务，自动处理401错误
        try {
          const response = await this.$api.get('/transaction-alerts/statistics?days=7');
          
          if (response.data.success) {
            transactionAlerts.value = response.data;
            console.log('Dashboard: Transaction alerts loaded successfully', response.data);
          } else {
            console.warn('Dashboard: Transaction alerts API returned error:', response.data.message);
            // 如果是权限问题或API不存在，不显示错误，只是不显示卡片
            transactionAlerts.value = null;
          }
        } catch (error) {
          // 如果是401错误，API拦截器会自动跳转到登录页面
          if (error.message && error.message.includes('登录状态已过期')) {
            console.warn('Dashboard: Token expired, redirecting to login');
            return; // 直接返回，不继续处理
          }
          throw error; // 重新抛出其他错误
        }
      } catch (err) {
        console.warn('Dashboard: Error fetching transaction alerts (may not have permission):', err);
        // 静默处理错误，因为可能是权限问题
        transactionAlerts.value = null;
      } finally {
        transactionAlertsLoading.value = false;
      }
    };

    const formatRateValue = (value) => {
      if (value === null || value === undefined) {
        return t('dashboard.no_data');
      }
      
      if (value >= 1000) {
        return new Intl.NumberFormat('zh-CN', {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2
        }).format(value);
      }
      return value < 1 ? value.toFixed(4) : value.toFixed(2);
    };

    // 节流的数据刷新函数
    const throttledFetchAllData = throttle(async () => {
      performanceMonitor.mark('dashboard_refresh_start');
      loading.value = true;
      error.value = null;
      
      try {
        // 并行获取数据，提高性能
        await Promise.all([
          fetchCurrencies(),
          fetchRates()
        ]);
        
        if (selectedCurrency.value) {
          await debouncedFetchRateHistory();
        }
        
        performanceMonitor.mark('dashboard_refresh_success');
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        error.value = err.message || '加载数据失败';
        performanceMonitor.mark('dashboard_refresh_error');
      } finally {
        loading.value = false;
        performanceMonitor.measure('dashboard_refresh_duration', 'dashboard_refresh_start');
      }
    }, 2000); // 2秒内最多执行一次

    const fetchAllData = throttledFetchAllData;

    // 图表事件处理
    const onChartReady = (chartInstance) => {
      console.log('Dashboard chart is ready:', chartInstance);
      performanceMonitor.mark('dashboard_chart_ready');
    };

    const onChartError = (error) => {
      console.error('Dashboard chart error:', error);
      performanceMonitor.mark('dashboard_chart_error');
    };

    const onChartRefresh = () => {
      console.log('Dashboard chart is refreshing...');
      if (selectedCurrency.value) {
        debouncedFetchRateHistory();
      }
    };

    // 监听货币选择变化 - 区分初始化和用户手动选择
    watch(selectedCurrency, async (newValue, oldValue) => {
      if (newValue && isComponentMounted.value) {
        console.log('Selected currency changed to:', newValue);
        
        // 如果是初始化时设置（oldValue为null），立即获取数据
        if (oldValue === null || oldValue === undefined) {
          console.log('Dashboard: Initial currency selection, fetching history immediately');
          await fetchRateHistory();
        } else {
          // 如果是用户手动选择，使用防抖
          console.log('Dashboard: User currency selection, using debounced fetch');
          await debouncedFetchRateHistory();
        }
      }
    });

    const getSystemManagementRoute = () => {
      // 根据用户权限优先级返回合适的系统管理页面
      if (hasPermission('user_manage')) {
        return '/user-management';
      } else if (hasPermission('role_manage')) {
        return '/role-management';
      } else if (hasPermission('branch_manage')) {
        return '/branch-management';
      } else if (hasPermission('system_manage')) {
        return '/user-activity';
      }
      // 默认返回用户管理（虽然理论上不会到达这里，因为已经有权限检查）
      return '/user-management';
    };

    // 获取货币的多语言名称
    const getCurrencyDisplayName = (currencyCode, apiCurrencyNames = null) => {
      // 检查是否是自定义币种（在rates数据中查找）
      const rateData = rates.value.find(rate => rate.currency_code === currencyCode);
      if (rateData && rateData.custom_flag_filename) {
        // console.log(`[自定义币种] ${currencyCode} 使用数据库名称: ${rateData.currency_name}`);
        return rateData.currency_name || currencyCode;
      }
      
      return getCurrencyName(currencyCode, null, apiCurrencyNames);
    };

    // 获取当前语言，用于组件内安全访问
    const getCurrentLang = () => {
      try {
        // 从localStorage获取语言设置
        const storedLang = localStorage.getItem('language') || 'zh-CN';
        return storedLang;
      } catch (e) {
        return 'zh-CN';
      }
    };
    
    // 切换性能监控状态
    const togglePerformanceMonitor = () => {
      const newState = !performanceMonitorEnabled.value;
      performanceMonitorEnabled.value = newState;
      localStorage.setItem('enablePerformanceMonitor', newState.toString());
      
      if (newState) {
        // 启用时刷新性能数据
        refreshPerformanceData();
      }
    };
    
    // 刷新性能数据
    const refreshPerformanceData = async () => {
      if (!performanceMonitorEnabled.value) return;
      
      performanceRefreshing.value = true;
      
      try {
        // 获取性能报告
        const report = performanceMonitor.getReport();
        
        // 更新时序信息
        if (report.timing) {
          performanceTiming.value = { ...report.timing };
        }
        
        // 更新内存信息
        if (report.memory) {
          performanceMemory.value = { ...report.memory };
        }
        
        // 更新缓存统计
        const stats = performanceCacheAPI.getStats();
        const totalRequests = performanceCache.value.hits + performanceCache.value.misses;
        performanceCache.value = {
          ...stats,
          hits: performanceCache.value.hits,
          misses: performanceCache.value.misses,
          hitRate: totalRequests > 0 ? performanceCache.value.hits / totalRequests : 0
        };
        
        // 更新API指标
        if (report.measures) {
          const newMetrics = Object.entries(report.measures)
            .filter(([name]) => name.includes('api_duration'))
            .map(([name, duration]) => ({
              name: name.replace('api_duration_', '').replace(/_/g, ' '),
              duration,
              status: 'success',
              timestamp: Date.now()
            }))
            .sort((a, b) => b.timestamp - a.timestamp);
          
          performanceApiMetrics.value = newMetrics;
        }
        
      } catch (error) {
        console.error('Failed to refresh performance data:', error);
      } finally {
        performanceRefreshing.value = false;
      }
    };
    
    // 清除性能数据
    const clearPerformanceData = () => {
      performanceMonitor.clear();
      performanceCacheAPI.clear();
      performanceApiMetrics.value = [];
      performanceCache.value.hits = 0;
      performanceCache.value.misses = 0;
      performanceCache.value.hitRate = 0;
    };
    
    // 格式化持续时间
    const formatDuration = (duration) => {
      if (!duration || duration === 0) return '0ms';
      if (duration < 1000) return Math.round(duration) + 'ms';
      if (duration < 60000) return (duration / 1000).toFixed(1) + 's';
      return (duration / 60000).toFixed(1) + 'm';
    };
    
    // 格式化内存
    const formatMemory = (bytes) => {
      if (!bytes || bytes === 0) return '0B';
      const units = ['B', 'KB', 'MB', 'GB'];
      let size = bytes;
      let unitIndex = 0;
      
      while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
      }
      
      return size.toFixed(1) + units[unitIndex];
    };
    
    // 获取性能等级样式
    const getPerformanceClass = (duration) => {
      if (!duration || duration === 0) return 'text-muted';
      if (duration < 100) return 'text-success';
      if (duration < 500) return 'text-warning';
      return 'text-danger';
    };
    
    // 获取内存等级样式
    const getMemoryClass = (bytes) => {
      if (!bytes || bytes === 0) return 'text-muted';
      const mb = bytes / (1024 * 1024);
      if (mb < 50) return 'text-success';
      if (mb < 100) return 'text-warning';
      return 'text-danger';
    };
    
    // 获取缓存命中率样式
    const getCacheHitRateClass = (rate) => {
      if (!rate || rate === 0) return 'text-muted';
      if (rate > 0.8) return 'text-success';
      if (rate > 0.5) return 'text-warning';
      return 'text-danger';
    };

    onMounted(async () => {
      performanceMonitor.mark('dashboard_mount_start');
      isComponentMounted.value = true;
      
      try {
        loading.value = true;
        
        // 预加载关键数据 - 暂时注释掉，使用标准API
        // await dashboardApi.preload([
        //   'dashboard/overview',
        //   'rates/currencies'
        // ], { priority: 'high' });
        
        // 先获取币种列表
        await fetchCurrencies();
        
        // 再获取汇率数据
        await fetchRates();
        
        // 确保选择了默认币种（如果currencies已经设置了默认值）
        if (!selectedCurrency.value && currencies.value.length > 0) {
          selectedCurrency.value = currencies.value[0].id;
          console.log('Dashboard: Set default currency to:', selectedCurrency.value);
        }
        
        // 汇率历史数据会通过watch自动获取，不需要在这里手动调用
        console.log('Dashboard: Currency selection completed, history will be fetched by watch');
        
        // 获取业务统计数据
        await fetchBusinessStats();
        
        // 获取交易报警事件统计
        await fetchTransactionAlerts();
        
        // 初始化性能监控数据
        if (performanceMonitorEnabled.value) {
          // 设置一些测试数据
          performanceTiming.value = {
            loadComplete: 1200,
            domReady: 800,
            domContentLoaded: 600
          };
          performanceMemory.value = {
            usedJSHeapSize: 45 * 1024 * 1024, // 45MB
            totalJSHeapSize: 80 * 1024 * 1024, // 80MB
            jsHeapSizeLimit: 2048 * 1024 * 1024 // 2GB
          };
          performanceCache.value = {
            size: 15,
            maxSize: 100,
            hits: 120,
            misses: 8,
            hitRate: 0.94
          };
          
          await refreshPerformanceData();
        }
        
        // 每5分钟刷新一次汇率数据
        refreshTimer.value = setInterval(() => {
          if (isComponentMounted.value) {
            fetchRates();
            // 每5分钟也刷新业务统计
            fetchBusinessStats();
            // 如果性能监控启用，也刷新性能数据
            if (performanceMonitorEnabled.value) {
              refreshPerformanceData();
            }
          }
        }, 300000);

        performanceMonitor.mark('dashboard_mount_success');
      } catch (err) {
        console.error('Failed to initialize dashboard:', err);
        error.value = err.message || '初始化失败';
        performanceMonitor.mark('dashboard_mount_error');
      } finally {
        loading.value = false;
        performanceMonitor.measure('dashboard_mount_duration', 'dashboard_mount_start');
        
        // 输出性能报告（开发环境）
        if (process.env.NODE_ENV === 'development') {
          setTimeout(() => {
            const report = performanceMonitor.getReport();
            console.log('Dashboard Performance Report:', report);
          }, 1000);
        }
      }
    });

    onBeforeUnmount(() => {
      console.log('Dashboard component is being unmounted');
      isComponentMounted.value = false;
      
      // 清理定时器
      if (refreshTimer.value) {
        clearInterval(refreshTimer.value);
        refreshTimer.value = null;
      }
      
      performanceMonitor.mark('dashboard_unmount');
    });

    return {
      rates,
      currencies,
      selectedCurrency,
      loading,
      error,
      rateHistory,
      chartData,
      chartOptions,
      dashboardChart,
      formatDateTime,
      formatRateValue,
      fetchAllData,
      onChartReady,
      onChartError,
      onChartRefresh,
      hasPermission,
      hasAnyPermission,
      getSystemManagementRoute,
      // 业务统计相关
      businessStats,
      businessStatsLoading,
      fetchBusinessStats,
      // 交易报警事件相关
      transactionAlerts,
      transactionAlertsLoading,
      fetchTransactionAlerts,
      getCurrencyDisplayName,
      getCurrentLang,
      // 性能监控控制
      isDevelopmentMode,
      performanceMonitorEnabled,
      togglePerformanceMonitor,
      // 性能监控数据和方法
      performanceRefreshing,
      performanceTiming,
      performanceMemory,
      performanceCache,
      performanceApiMetrics,
      refreshPerformanceData,
      clearPerformanceData,
      formatDuration,
      formatMemory,
      getPerformanceClass,
      getMemoryClass,
      getCacheHitRateClass
    };
  }
}
</script>

<style scoped>
.rate-card {
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  border: none;
  background: #fff;
  overflow: hidden;
}

.rate-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 25px rgba(0,0,0,0.15);
}

.custom-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-bottom: none;
  color: white !important;
}

.custom-header h5 {
  color: white !important;
  font-weight: 600;
}

/* 移除重复的性能监控控制按钮样式 */

/* 嵌入式性能监控面板样式 */
.performance-stats-card {
  border: 1px solid #e0e0e0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.performance-content {
  max-height: 400px;
  overflow-y: auto;
}

.performance-section {
  margin-bottom: 0.75rem;
}

.section-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: #495057;
  margin-bottom: 0.5rem;
}

/* 紧凑指标网格 */
.metrics-grid-compact {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
}

.metric-item-compact {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 0.25rem;
  padding: 0.5rem;
  text-align: center;
}

.metric-label-compact {
  font-size: 0.7rem;
  color: #6c757d;
  margin-bottom: 0.25rem;
}

.metric-value-compact {
  font-size: 0.8rem;
  font-weight: 600;
  line-height: 1;
}

/* API指标紧凑布局 */
.api-metrics-compact {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.api-metric-item-compact {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.25rem 0.5rem;
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 0.25rem;
  font-size: 0.75rem;
}

.api-name-compact {
  flex: 1;
  color: #495057;
  font-weight: 500;
  text-overflow: ellipsis;
  overflow: hidden;
  white-space: nowrap;
  max-width: 120px;
}

.api-duration-compact {
  font-weight: 600;
  margin-left: 0.5rem;
  min-width: 50px;
  text-align: right;
}

.api-status-compact {
  margin-left: 0.25rem;
  min-width: 20px;
  text-align: center;
}

/* 缓存统计紧凑布局 */
.cache-stats-compact {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
}

.cache-stat-compact {
  flex: 1;
  text-align: center;
  padding: 0.25rem;
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 0.25rem;
  font-size: 0.7rem;
}

.stat-label-compact {
  display: block;
  color: #6c757d;
  margin-bottom: 0.25rem;
}

.stat-value-compact {
  display: block;
  font-weight: 600;
  font-size: 0.75rem;
}

/* 性能控制按钮组 */
.performance-controls {
  display: flex;
  gap: 0.25rem;
}

.performance-controls .btn {
  padding: 0.125rem 0.25rem;
  font-size: 0.7rem;
  line-height: 1;
}

.rate-value {
  font-size: 1.2rem;
  font-weight: 700;
  font-family: 'Roboto Mono', 'Courier New', monospace;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding: 0.25rem;
  color: #2c3e50;
  background: rgba(52, 152, 219, 0.05);
  border-radius: 0.25rem;
  margin: 0.25rem 0;
}

.currency-flag {
  width: 20px;
  height: 15px;
  object-fit: cover;
  border-radius: 2px;
  margin-right: 8px;
}

.chart-wrapper {
  min-height: 300px;
  background-color: #fff;
}

.trend-card {
  height: 100%;
  min-height: 400px;
}

.trend-card-compact {
  height: 100%;
  min-height: 160px;
}

.trend-card-enhanced {
  height: auto;
  min-height: auto;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  border: none;
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
}

.chart-container {
  height: 160px;
  overflow: hidden;
}

.chart-container-enhanced {
  height: 360px;
  overflow: visible;
  border-radius: 0 0 0.375rem 0.375rem;
  padding-bottom: 10px;
}

.feature-card {
  min-height: 200px;
  transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
}

.feature-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15) !important;
}

.currency-selector {
  position: relative;
  min-width: 160px;
  z-index: 1000;
}

.currency-selector select {
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(10px);
  font-size: 0.8rem;
}

.currency-selector select:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
}

.card-header {
  position: relative;
  z-index: 1;
}

.chart-wrapper {
  position: relative;
  z-index: 0;
}

/* 使用 g-3 替代 mb-4 来减小间距 */
.row.g-3 {
  margin-right: -0.5rem;
  margin-left: -0.5rem;
}

.row.g-3 > [class*="col-"] {
  padding-right: 0.5rem;
  padding-left: 0.5rem;
}

.feature-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
  font-size: 1.5rem;
  color: white;
}

.card {
  transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
}

.card:hover {
  transform: translateY(-5px);
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15) !important;
}

.feature-card-compact {
  min-height: 110px;
  transition: all 0.3s ease;
  border: none;
  background: #fff;
}

.feature-card-compact:hover {
  transform: translateY(-3px) scale(1.02);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.12) !important;
}

.feature-icon-small {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
  font-size: 1.1rem;
  color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

/* 响应式优化 */
@media (max-width: 1199.98px) {
  .col-md-8 {
    order: 2;
  }
  
  .col-md-4 {
    order: 1;
    margin-bottom: 1rem;
  }
  
  .trend-card-enhanced {
    height: auto;
    min-height: auto;
  }
  
  .chart-container-enhanced {
    height: 340px;
    padding-bottom: 15px;
  }
}

@media (max-width: 991.98px) {
  .col-md-8 .col-md-4 {
    flex: 0 0 50%;
    max-width: 50%;
  }
  
  .chart-container-enhanced {
    height: 320px;
    padding-bottom: 15px;
  }
}

@media (max-width: 767.98px) {
  .col-md-8 .col-md-4 {
    flex: 0 0 100%;
    max-width: 100%;
  }
  
  .feature-card-compact {
    min-height: 90px;
  }
  
  .trend-card-enhanced {
    height: auto;
    min-height: auto;
  }
  
  .chart-container-enhanced {
    height: 300px;
    padding-bottom: 20px;
  }
}

@media (max-width: 575.98px) {
  .chart-container-enhanced {
    height: 280px;
    padding-bottom: 25px;
  }
}

/* 增强间距和布局 */
.row.g-3 {
  --bs-gutter-x: 1rem;
  --bs-gutter-y: 1rem;
}

.dashboard-view {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: 100vh;
}

.dashboard-view .container-fluid {
  background: transparent;
}

/* 业务统计卡片样式 */
.business-stats-container {
  margin-top: 1rem;
}

.stats-card {
  border: none;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  background: linear-gradient(135deg, #fff 0%, #f8f9fa 100%);
}

.stats-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
}

.stats-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: white;
  flex-shrink: 0;
}

.stats-title {
  font-size: 0.75rem;
  color: #6c757d;
  font-weight: 500;
  line-height: 1.2;
}

.stats-value {
  font-size: 1rem;
  font-weight: bold;
  color: #212529;
  line-height: 1.2;
  margin-top: 2px;
}

.stats-subtitle {
  font-size: 0.7rem;
  color: #6c757d;
  line-height: 1.2;
  margin-top: 2px;
}

.ranking-section {
  padding: 0.25rem 0;
}

.ranking-title {
  font-size: 0.7rem;
  font-weight: 600;
  color: #495057;
  margin-bottom: 0.5rem;
  padding-bottom: 0.25rem;
  border-bottom: 1px solid #e9ecef;
}

.ranking-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.7rem;
  padding: 0.25rem 0.1rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  gap: 0.3rem;
}

.ranking-item:last-child {
  border-bottom: none;
}

.ranking-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  background: #007bff;
  color: white;
  border-radius: 50%;
  font-size: 0.6rem;
  font-weight: bold;
  flex-shrink: 0;
}

.ranking-currency {
  font-weight: 600;
  color: #495057;
  flex: 1;
  text-align: center;
  margin: 0 0.2rem;
}

.ranking-count {
  color: #6c757d;
  font-size: 0.65rem;
  white-space: nowrap;
  font-weight: 500;
}

/* 热门外币列分隔样式 */
.ranking-col-left {
  border-right: 1px solid #e9ecef;
  padding-right: 0.75rem;
}

.ranking-col-right {
  padding-left: 0.75rem;
}

/* 余额预警详情样式 */
.alert-details {
  border-top: 1px solid #e9ecef;
  padding-top: 0.5rem;
  margin-top: 0.25rem;
}

.alert-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.2rem 0;
  font-size: 0.7rem;
}

.alert-currency {
  font-weight: 600;
  color: #495057;
}

.alert-type {
  font-size: 0.65rem;
  font-weight: 500;
}

/* 性能监控控制按钮样式 */
.performance-control {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 1000;
  opacity: 0.9;
  transition: all 0.3s ease;
}

.performance-control:hover {
  opacity: 1;
  transform: scale(1.05);
}

.performance-control .btn {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  border-radius: 25px;
  padding: 10px 18px;
  font-size: 0.85rem;
  font-weight: 500;
  background: linear-gradient(135deg, #007bff, #0056b3);
  border: none;
  color: white;
  min-width: 120px;
}

.performance-control .btn:hover {
  background: linear-gradient(135deg, #0056b3, #004085);
  transform: translateY(-1px);
}

/* 性能监控面板样式 */
.performance-stats-card {
  border: 1px solid #dee2e6;
  border-radius: 8px;
  background: #ffffff;
}

.performance-content {
  max-height: 400px;
  overflow-y: auto;
}

.performance-section {
  border-bottom: 1px solid #f1f3f4;
  padding-bottom: 0.75rem;
}

.performance-section:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.section-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: #495057;
  margin-bottom: 0.5rem;
}

/* 紧凑型指标网格 */
.metrics-grid-compact {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
}

.metric-item-compact {
  background: #f8f9fa;
  padding: 0.4rem;
  border-radius: 4px;
  text-align: center;
}

.metric-label-compact {
  font-size: 0.65rem;
  color: #6c757d;
  margin-bottom: 0.2rem;
}

.metric-value-compact {
  font-size: 0.7rem;
  font-weight: bold;
}

/* API指标样式 */
.api-metrics-compact .api-metric-item-compact {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.3rem 0;
  border-bottom: 1px solid #f1f3f4;
  font-size: 0.7rem;
}

.api-metrics-compact .api-metric-item-compact:last-child {
  border-bottom: none;
}

.api-name-compact {
  flex: 1;
  font-weight: 500;
  color: #495057;
}

.api-duration-compact {
  margin: 0 0.5rem;
  font-weight: 600;
}

.api-status-compact {
  font-size: 0.8rem;
}

/* 缓存统计样式 */
.cache-stats-compact {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
}

.cache-stat-compact {
  font-size: 0.7rem;
  text-align: center;
}

.stat-label-compact {
  color: #6c757d;
  font-weight: 500;
}

.stat-value-compact {
  margin-left: 0.2rem;
  font-weight: 600;
}

/* 性能等级颜色 */
.text-excellent { color: #28a745; }
.text-good { color: #17a2b8; }
.text-average { color: #ffc107; }
.text-poor { color: #dc3545; }
</style>

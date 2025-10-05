<template>
  <div class="denomination-rate-manager">
    <!-- 币种选择 -->
    <div class="row mb-4">
      <!-- 币种选择 - 缩小到1/4宽度 -->
      <div class="col-3">
      <label class="form-label">
        <i class="fas fa-flag me-2"></i>
        {{ $t('rates.select_currency') }}
      </label>
      <select
        class="form-select"
        v-model="selectedCurrencyId"
        @change="loadCurrencyData"
      >
        <option value="">{{ $t('rates.select_currency_placeholder') }}</option>
        <option
          v-for="currency in currencies"
          :key="currency.id"
          :value="currency.id"
        >
          <CurrencyFlag :code="currency.currency_code" class="me-2" />
          {{ currency.currency_code }} - {{ getCurrencyName(currency.currency_code) }}
        </option>
      </select>
      
      <!-- 币种图标显示区域 -->
      <div v-if="selectedCurrency" class="currency-display-area mt-3">
        <div class="text-center">
          <img 
            :src="getFlagUrl(selectedCurrency.currency_code)" 
            :alt="selectedCurrency.currency_code"
            class="large-currency-flag"
            @error="handleFlagError"
          />
          <div class="currency-info mt-2">
            <h4 class="mb-1">{{ selectedCurrency.currency_code }}</h4>
            <p class="text-muted mb-0">{{ getCurrencyName(selectedCurrency.currency_code) }}</p>
          </div>
        </div>
      </div>
      </div>
      
      <!-- 已设置币种显示区域 - 统一框架 -->
      <div class="col-6">
        <div class="border rounded p-3">
          <!-- 标题行：标题 + 操作按钮 -->
          <div class="d-flex justify-content-between align-items-center mb-3">
            <h6 class="mb-0 d-flex align-items-center">
              <i class="fas fa-list-check me-2 text-primary"></i>
              {{ $t('rates.today_set_denomination_currencies') }}
            </h6>
            <div class="d-flex gap-2">
              <button 
                class="btn btn-sm btn-outline-primary"
                @click="loadTodayDenominationCurrencies"
                :disabled="loading"
                :title="$t('rates.refresh_set')"
              >
                <i class="fas fa-sync-alt me-1" :class="{ 'fa-spin': loading }"></i>
                {{ $t('rates.refresh') }}
              </button>
              <button 
                class="btn btn-sm btn-outline-secondary"
                @click="selectAllCurrencies"
                :disabled="todayDenominationCurrencies.length === 0"
              >
                <i class="fas fa-check-square me-1"></i>{{ $t('rates.select_all') }}
              </button>
              <button 
                class="btn btn-sm btn-outline-secondary"
                @click="clearAllCurrencies"
                :disabled="selectedCurrenciesForBatch.length === 0"
              >
                <i class="fas fa-square me-1"></i>{{ $t('rates.clear_all') }}
              </button>
              <button 
                class="btn btn-sm btn-primary"
                @click="showBatchPublishModal"
                :disabled="selectedCurrenciesForBatch.length === 0"
              >
                <i class="fas fa-rocket me-1"></i>
                {{ $t('rates.batch_publish_selected_currencies') }}
                <span v-if="selectedCurrenciesForBatch.length > 0" class="badge bg-light text-dark ms-1">
                  {{ selectedCurrenciesForBatch.length }}
                </span>
              </button>
            </div>
          </div>
          
          <!-- 币种列表区域 -->
          <div style="min-height: 60px; max-height: 120px; overflow-y: auto;">
            <div v-if="todayDenominationCurrencies.length === 0" class="text-muted small text-center py-3">
              {{ $t('rates.no_set_currencies') }}
            </div>
            <div v-else class="d-flex flex-wrap gap-2">
              <div 
                v-for="currency in todayDenominationCurrencies" 
                :key="currency.currency_id"
                class="form-check form-check-inline"
              >
                <input 
                  class="form-check-input" 
                  type="checkbox" 
                  :id="`currency-${currency.currency_id}`"
                  :value="currency.currency_id"
                  v-model="selectedCurrenciesForBatch"
                >
                <label 
                  class="form-check-label small" 
                  :for="`currency-${currency.currency_id}`"
                >
                  <span class="badge bg-info me-1">{{ currency.currency_code }}</span>
                  {{ currency.currency_name }}
                  <span class="text-muted">({{ currency.denomination_count }}{{ $t('rates.denomination_count_suffix') }})</span>
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 已发布币种显示区域 - 统一框架 -->
      <div class="col-3">
        <div class="border rounded p-3">
          <!-- 标题行：标题 + 刷新按钮 -->
          <div class="d-flex justify-content-between align-items-center mb-3">
            <h6 class="mb-0 d-flex align-items-center">
              <i class="fas fa-tv me-2 text-success"></i>
              {{ $t('rates.today_published_denomination_currencies') }}
            </h6>
            <button 
              class="btn btn-sm btn-outline-success"
              @click="loadTodayPublishedCurrencies"
              :disabled="loading"
              :title="$t('rates.refresh_published')"
            >
              <i class="fas fa-sync-alt me-1" :class="{ 'fa-spin': loading }"></i>
              {{ $t('rates.refresh') }}
            </button>
          </div>
          
          <!-- 币种列表区域 -->
          <div style="min-height: 60px; max-height: 120px; overflow-y: auto;">
            <div v-if="todayPublishedCurrencies.length === 0" class="text-muted small text-center py-3">
              {{ $t('rates.no_published_currencies') }}
            </div>
            <div v-else class="d-flex flex-wrap gap-2">
              <div 
                v-for="currency in todayPublishedCurrencies" 
                :key="currency.currency_id"
                class="form-check form-check-inline"
              >
                <span class="badge bg-success me-1">{{ currency.currency_code }}</span>
                <span class="small">
                  {{ currency.currency_name }}
                  <span class="text-muted">({{ currency.denomination_count }}{{ $t('rates.denomination_count_suffix') }})</span>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 面值汇率设置 -->
    <div v-if="selectedCurrencyId && denominations.length > 0" class="denomination-rates">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h5 class="mb-0 d-flex align-items-center">
          <img 
            v-if="selectedCurrency" 
            :src="getFlagUrl(selectedCurrency.currency_code)" 
            :alt="selectedCurrency.currency_code"
            class="currency-flag me-2"
            @error="handleFlagError"
          />
          <i class="fas fa-coins me-2"></i>
          {{ $t('rates.denomination_rates') }}
        </h5>
        <div class="btn-group">
          <button
            class="btn btn-sm btn-outline-primary"
            @click="copyFromYesterday"
            :disabled="loading"
          >
            <i class="fas fa-copy me-1"></i>
            {{ $t('rates.copy_yesterday_rates') }}
          </button>
          <button
            class="btn btn-sm btn-success"
            @click="saveAllRates"
            :disabled="loading || !hasChanges"
          >
            <i class="fas fa-save me-1"></i>
            {{ $t('rates.save_all') }}
          </button>
          <button
            class="btn btn-sm btn-primary"
            @click="publishToDisplay"
            :disabled="loading || !hasValidRates"
          >
            <i class="fas fa-tv me-1"></i>
            {{ $t('rates.publish_to_display') }}
          </button>
          <button
            class="btn btn-sm btn-info"
            @click="showPublishHistory"
            :disabled="loading"
          >
            <i class="fas fa-history me-1"></i>
            {{ $t('rates.publish_history') }}
          </button>
          <button
            class="btn btn-sm btn-outline-secondary"
            @click="goToDenominationManagement"
            title="管理面值"
          >
            <i class="fas fa-cog me-1"></i>
            {{ $t('rates.manage_denominations') }}
          </button>
        </div>
      </div>
      
      <!-- 面值汇率表格 -->
      <div class="table-responsive">
        <table class="table table-bordered table-hover">
          <thead class="table-light">
            <tr>
              <th width="15%">{{ $t('rates.denomination') }}</th>
              <th width="10%">{{ $t('rates.type') }}</th>
              <th width="20%">{{ $t('rates.buy_rate') }}</th>
              <th width="20%">{{ $t('rates.sell_rate') }}</th>
              <th width="15%">{{ $t('rates.spread') }}</th>
              <th width="10%">{{ $t('rates.status') }}</th>
              <th width="10%">{{ $t('rates.actions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="denom in denominations"
              :key="denom.id"
              class="denomination-row"
            >
              <td class="denomination-cell">
                <div class="d-flex align-items-center">
                  <i :class="denom.denomination_type === 'bill' ? 'fas fa-money-bill text-success' : 'fas fa-coins text-warning'"></i>
                  <span class="ms-2 fw-bold">{{ formatDenominationValue(denom.denomination_value) }}</span>
                </div>
              </td>
              <td>
                <span class="badge" :class="denom.denomination_type === 'bill' ? 'bg-success' : 'bg-warning'">
                  {{ $t(`exchange.${denom.denomination_type}`) }}
                </span>
              </td>
              <td>
                <input
                  type="number"
                  class="form-control form-control-sm"
                  v-model="denom.buy_rate"
                  @input="calculateSpread(denom)"
                  step="0.0001"
                  min="0"
                  :placeholder="$t('rates.enter_buy_rate')"
                />
              </td>
              <td>
                <input
                  type="number"
                  class="form-control form-control-sm"
                  v-model="denom.sell_rate"
                  @input="calculateSpread(denom)"
                  step="0.0001"
                  min="0"
                  :placeholder="$t('rates.enter_sell_rate')"
                />
              </td>
              <td class="spread-cell">
                <span class="badge" :class="getSpreadClass(denom.spread)">
                  {{ formatSpread(denom.spread) }}
                </span>
              </td>
              <td>
                <span class="badge" :class="denom.has_rate ? 'bg-success' : 'bg-secondary'">
                  {{ denom.has_rate ? $t('rates.set') : $t('rates.not_set') }}
                </span>
              </td>
              <td>
                <div class="btn-group btn-group-sm">
                  <button
                    class="btn btn-outline-primary"
                    @click="saveDenominationRate(denom)"
                    :disabled="loading || !denom.buy_rate || !denom.sell_rate"
                    :title="$t('rates.save')"
                  >
                    <i class="fas fa-save"></i>
                  </button>
                  <button
                    class="btn btn-outline-danger"
                    @click="clearDenominationRate(denom)"
                    :disabled="loading || !denom.has_rate"
                    :title="$t('rates.clear')"
                  >
                    <i class="fas fa-trash"></i>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <!-- 批量操作 -->
      <div class="batch-operations mt-3">
        <div class="row g-2">
          <div class="col-md-3">
            <button
              class="btn btn-outline-primary w-100"
              @click="applyToAll('buy_rate', getAverageBuyRate())"
              :disabled="loading"
            >
              <i class="fas fa-calculator me-1"></i>
              {{ $t('rates.apply_avg_buy_rate') }}
            </button>
          </div>
          <div class="col-md-3">
            <button
              class="btn btn-outline-primary w-100"
              @click="applyToAll('sell_rate', getAverageSellRate())"
              :disabled="loading"
            >
              <i class="fas fa-calculator me-1"></i>
              {{ $t('rates.apply_avg_sell_rate') }}
            </button>
          </div>
          <div class="col-md-3">
            <button
              class="btn btn-outline-secondary w-100"
              @click="clearAllRates"
              :disabled="loading"
            >
              <i class="fas fa-eraser me-1"></i>
              {{ $t('rates.clear_all') }}
            </button>
          </div>
          <div class="col-md-3">
            <button
              class="btn btn-outline-info w-100"
              @click="exportRates"
              :disabled="loading"
            >
              <i class="fas fa-download me-1"></i>
              {{ $t('rates.export') }}
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 无面值提示 -->
    <div v-else-if="selectedCurrencyId && denominations.length === 0" class="alert alert-warning">
      <i class="fas fa-exclamation-triangle me-2"></i>
      {{ $t('rates.no_denominations_for_currency') }}
      <button class="btn btn-sm btn-outline-primary ms-2" @click="goToDenominationManagement">
        <i class="fas fa-cog me-1"></i>
        {{ $t('rates.manage_denominations') }}
      </button>
    </div>
    
    <!-- 加载状态 -->
    <div v-if="loading" class="text-center py-4">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">{{ $t('common.loading') }}</span>
      </div>
      <div class="mt-2">{{ $t('common.loading') }}</div>
    </div>
    
    <!-- 批量发布模态框 -->
    <div class="modal fade" id="batchPublishModal" tabindex="-1" aria-labelledby="batchPublishModalLabel" aria-hidden="true">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="batchPublishModalLabel">
              <i class="fas fa-palette me-2"></i>
              选择显示主题并发布
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <!-- 选择机顶盒显示主题 -->
            <div class="mb-4">
              <h6 class="mb-3">
                <i class="fas fa-tv me-2"></i>
                选择机顶盒显示主题
              </h6>
              <div class="row">
                <div class="col-md-6">
                  <div class="form-check">
                    <input class="form-check-input" type="radio" name="batchTheme" id="batchThemeLight" value="light" v-model="batchPublishConfig.theme">
                    <label class="form-check-label" for="batchThemeLight">
                      <i class="fas fa-sun me-2"></i>
                      浅色
                    </label>
                  </div>
                </div>
                <div class="col-md-6">
                  <div class="form-check">
                    <input class="form-check-input" type="radio" name="batchTheme" id="batchThemeDark" value="dark" v-model="batchPublishConfig.theme">
                    <label class="form-check-label" for="batchThemeDark">
                      <i class="fas fa-moon me-2"></i>
                      深色
                    </label>
                  </div>
                </div>
              </div>
            </div>

            <!-- 选择显示语言 -->
            <div class="mb-4">
              <h6 class="mb-3">
                <i class="fas fa-language me-2"></i>
                选择显示语言
              </h6>
              <div class="row">
                <div class="col-md-4">
                  <div class="form-check">
                    <input class="form-check-input" type="radio" name="batchLanguage" id="batchLangZh" value="zh" v-model="batchPublishConfig.language">
                    <label class="form-check-label" for="batchLangZh">
                      <i class="fas fa-flag me-2"></i>
                      中文
                    </label>
                  </div>
                </div>
                <div class="col-md-4">
                  <div class="form-check">
                    <input class="form-check-input" type="radio" name="batchLanguage" id="batchLangEn" value="en" v-model="batchPublishConfig.language">
                    <label class="form-check-label" for="batchLangEn">
                      <i class="fas fa-flag me-2"></i>
                      English
                    </label>
                  </div>
                </div>
                <div class="col-md-4">
                  <div class="form-check">
                    <input class="form-check-input" type="radio" name="batchLanguage" id="batchLangTh" value="th" v-model="batchPublishConfig.language">
                    <label class="form-check-label" for="batchLangTh">
                      <i class="fas fa-flag me-2"></i>
                      ไทย
                    </label>
                  </div>
                </div>
              </div>
            </div>

            <!-- 显示配置 -->
            <div class="mb-4">
              <h6 class="mb-3">
                <i class="fas fa-cog me-2"></i>
                显示配置 (可选)
              </h6>
              <div class="row">
                <div class="col-md-6">
                  <label for="batchItemsPerPage" class="form-label">每页显示行数</label>
                  <input 
                    type="number" 
                    class="form-control" 
                    id="batchItemsPerPage" 
                    v-model.number="batchPublishConfig.displayConfig.itemsPerPage"
                    min="6" 
                    max="20"
                  >
                  <div class="form-text">建议6-20行,默认12行</div>
                </div>
                <div class="col-md-6">
                  <label for="batchRefreshInterval" class="form-label">刷新间隔(秒)</label>
                  <input 
                    type="number" 
                    class="form-control" 
                    id="batchRefreshInterval" 
                    v-model.number="batchPublishConfig.displayConfig.refreshInterval"
                    min="10" 
                    max="86400"
                  >
                  <div class="form-text">60秒-24小时,默认3600秒(1小时)</div>
                </div>
              </div>
            </div>

            <!-- 发布备注 -->
            <div class="mb-4">
              <h6 class="mb-3">
                <i class="fas fa-sticky-note me-2"></i>
                发布备注 (可选)
              </h6>
              <textarea 
                class="form-control" 
                rows="3" 
                v-model="batchPublishConfig.notes"
                placeholder="输入发布备注..."
              ></textarea>
            </div>

            <!-- 信息提示 -->
            <div class="alert alert-info">
              <i class="fas fa-info-circle me-2"></i>
              应用后将生成加密的访问链接,供机顶盒设备访问显示汇率信息,并保存发布记录。
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
            <button type="button" class="btn btn-primary" @click="batchPublishDenominationRates">
              <i class="fas fa-check me-2"></i>
              应用并发布
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import CurrencyFlag from '@/components/CurrencyFlag.vue'
import { getCurrencyName } from '@/utils/currencyTranslator'

export default {
  name: 'DenominationRateManager',
  components: {
    CurrencyFlag
  },
  data() {
    return {
      currencies: [],
      selectedCurrencyId: null,
      selectedCurrency: null,
      denominations: [],
      rates: [],
      loading: false,
      // 新增：今日已设置面值汇率的币种
      todayDenominationCurrencies: [],
      // 新增：今日已发布面值汇率的币种
      todayPublishedCurrencies: [],
      // 新增：批量发布选中的币种
      selectedCurrenciesForBatch: [],
      // 新增：批量发布配置
      batchPublishConfig: {
        theme: 'light',
        language: 'zh',
        displayConfig: {
          itemsPerPage: 12,
          refreshInterval: 3600
        },
        notes: ''
      }
    }
  },
  computed: {
    hasValidRates() {
      return this.denominations.some(denom => 
        denom.buy_rate && denom.sell_rate && denom.buy_rate > 0 && denom.sell_rate > 0
      );
    },
    hasChanges() {
      return this.denominations.some(denom => 
        (denom.buy_rate && denom.buy_rate !== '') || 
        (denom.sell_rate && denom.sell_rate !== '')
      );
    }
  },
  mounted() {
    this.loadCurrencies()
    this.loadTodayDenominationCurrencies()
    this.loadTodayPublishedCurrencies()
  },
  watch: {
    selectedCurrencyId(newId) {
      if (newId) {
        this.selectedCurrency = this.currencies.find(c => c.id === newId) || null
        console.log('选择币种:', this.selectedCurrency)
        this.loadCurrencyData()
      } else {
        this.selectedCurrency = null
      }
    }
  },
  methods: {
    async loadCurrencies() {
      this.loading = true
      try {
        const response = await this.$api.get('/system/currencies')
        if (response.data.success && response.data.currencies) {
          this.currencies = response.data.currencies.filter(c => !c.is_base)
        } else {
          console.warn('币种数据格式不正确:', response.data)
          this.currencies = []
        }
      } catch (error) {
        console.error('加载币种失败:', error)
        this.$toast.error('加载币种失败')
        this.currencies = []
      } finally {
        this.loading = false
      }
    },
    
    async loadCurrencyData() {
      if (!this.selectedCurrencyId) return
      
      this.loading = true
      try {
        // 加载面值列表
        const denomResponse = await this.$api.get(`/denominations/${this.selectedCurrencyId}`)
        if (denomResponse.data.success) {
          this.denominations = denomResponse.data.data.map(denom => ({
            ...denom,
            buy_rate: '',
            sell_rate: '',
            spread: 0,
            has_rate: false
          }))
        }
        
        // 加载面值汇率
        const rateResponse = await this.$api.get('/denominations/rates', {
          params: { currency_id: this.selectedCurrencyId }
        })
        if (rateResponse.data.success) {
          this.rates = rateResponse.data.data
          this.updateDenominationRates()
        }
      } catch (error) {
        console.error('加载面值数据失败:', error)
        this.$toast.error('加载面值数据失败')
      } finally {
        this.loading = false
      }
    },
    
    updateDenominationRates() {
      this.denominations.forEach(denom => {
        const rate = this.rates.find(r => r.denomination_id === denom.id)
        if (rate) {
          denom.buy_rate = rate.buy_rate
          denom.sell_rate = rate.sell_rate
          denom.has_rate = true
          this.calculateSpread(denom)
        } else {
          denom.buy_rate = ''
          denom.sell_rate = ''
          denom.spread = 0
          denom.has_rate = false
        }
      })
    },
    
    calculateSpread(denom) {
      if (denom.buy_rate && denom.sell_rate) {
        denom.spread = denom.sell_rate - denom.buy_rate
        denom.has_rate = true
      } else {
        denom.spread = 0
        denom.has_rate = false
      }
    },
    
    async saveDenominationRate(denom) {
      if (!denom.buy_rate || !denom.sell_rate) return
      
      this.loading = true
      try {
        const response = await this.$api.post('/denominations/rates', {
          currency_id: this.selectedCurrencyId,
          denomination_id: denom.id,
          buy_rate: denom.buy_rate,
          sell_rate: denom.sell_rate
        })
        
        if (response.data.success) {
          denom.has_rate = true
          this.$toast.success('面值汇率保存成功')
          
          // 刷新今日已设置币种列表
          this.loadTodayDenominationCurrencies()
        } else {
          this.$toast.error(response.data.message || '保存失败')
        }
      } catch (error) {
        console.error('保存面值汇率失败:', error)
        this.$toast.error('保存面值汇率失败')
      } finally {
        this.loading = false
      }
    },
    
    async clearDenominationRate(denom) {
      this.loading = true
      try {
        // 调用API删除面值汇率
        await this.$api.delete(`/denominations/rates/${denom.id}`)
        
        // 清除本地数据
        denom.buy_rate = ''
        denom.sell_rate = ''
        denom.spread = 0
        denom.has_rate = false
        
        this.$toast.success('面值汇率已删除')
        
        // 刷新今日已设置币种列表
        this.loadTodayDenominationCurrencies()
      } catch (error) {
        console.error('删除面值汇率失败:', error)
        this.$toast.error('删除面值汇率失败')
      } finally {
        this.loading = false
      }
    },
    
    async saveAllRates() {
      this.loading = true
      try {
        const promises = this.denominations
          .filter(denom => denom.buy_rate && denom.sell_rate)
          .map(denom => this.saveDenominationRate(denom))
        
        await Promise.all(promises)
        this.$toast.success('所有面值汇率保存成功')
        
        // 刷新今日已设置币种列表
        this.loadTodayDenominationCurrencies()
      } catch (error) {
        console.error('批量保存失败:', error)
        this.$toast.error('批量保存失败')
      } finally {
        this.loading = false
      }
    },
    
    async copyFromYesterday() {
      // 实现复制上次汇率的逻辑
      if (!this.selectedCurrency) {
        this.$toast.warning(this.$t('rates.please_select_currency'))
        return
      }
      
      this.loading = true
      try {
        const response = await this.$api.get(`/denominations/${this.selectedCurrency.id}/last-rates`)
        
        if (response.data.success) {
          const lastRates = response.data.data
          
          if (lastRates.length === 0) {
            this.$toast.info('该币种暂无历史汇率记录')
            return
          }
          
          // 将历史汇率应用到当前面值
          let appliedCount = 0
          this.denominations.forEach(denom => {
            const lastRate = lastRates.find(rate => 
              rate.denomination_value === denom.denomination_value && 
              rate.denomination_type === denom.denomination_type
            )
            
            if (lastRate) {
              denom.buy_rate = lastRate.buy_rate
              denom.sell_rate = lastRate.sell_rate
              this.calculateSpread(denom)
              appliedCount++
            }
          })
          
          if (appliedCount > 0) {
            this.$toast.success(`成功复制 ${appliedCount} 个面值的上次汇率`)
          } else {
            this.$toast.warning('当前面值与历史记录不匹配，无法复制汇率')
          }
        } else {
          this.$toast.error(response.data.message || '获取历史汇率失败')
        }
      } catch (error) {
        console.error('复制上次汇率失败:', error)
        this.$toast.error('复制上次汇率失败')
      } finally {
        this.loading = false
      }
    },
    
    applyToAll(field, value) {
      this.denominations.forEach(denom => {
        denom[field] = value
        this.calculateSpread(denom)
      })
    },
    
    getAverageBuyRate() {
      const validRates = this.denominations
        .filter(denom => denom.buy_rate && denom.buy_rate > 0)
        .map(denom => parseFloat(denom.buy_rate))
      
      return validRates.length > 0 
        ? (validRates.reduce((sum, rate) => sum + rate, 0) / validRates.length).toFixed(4)
        : 0
    },
    
    getAverageSellRate() {
      const validRates = this.denominations
        .filter(denom => denom.sell_rate && denom.sell_rate > 0)
        .map(denom => parseFloat(denom.sell_rate))
      
      return validRates.length > 0 
        ? (validRates.reduce((sum, rate) => sum + rate, 0) / validRates.length).toFixed(4)
        : 0
    },
    
    clearAllRates() {
      this.denominations.forEach(denom => {
        denom.buy_rate = ''
        denom.sell_rate = ''
        denom.spread = 0
        denom.has_rate = false
      })
    },
    
    getFlagUrl(currencyCode) {
      // 将币种代码映射到对应的国旗文件
      const flagMap = {
        'USD': 'us',
        'CNY': 'cn', 
        'EUR': 'eu',
        'JPY': 'jp',
        'GBP': 'gb',
        'HKD': 'hk',
        'KRW': 'kr',
        'SGD': 'sg',
        'THB': 'th',
        'VND': 'vn',
        'MYR': 'my',
        'IDR': 'id',
        'PHP': 'ph',
        'INR': 'in',
        'AUD': 'au',
        'NZD': 'nz',
        'CAD': 'ca',
        'CHF': 'ch',
        'SEK': 'se',
        'NOK': 'no',
        'DKK': 'dk',
        'PLN': 'pl',
        'CZK': 'cz',
        'HUF': 'hu',
        'RUB': 'ru',
        'BRL': 'br',
        'MXN': 'mx',
        'ZAR': 'za',
        'AED': 'ae',
        'SAR': 'sa',
        'TRY': 'tr'
      }
      
      const flagCode = flagMap[currencyCode] || 'unknown'
      return `/flags/${flagCode}.svg`
    },
    
    handleFlagError(event) {
      // 如果国旗加载失败，隐藏图片
      event.target.style.display = 'none'
    },
    
    exportRates() {
      // 实现导出功能
      this.$toast.info('导出功能待实现')
    },
    
    goToDenominationManagement() {
      // 跳转到面值管理页面，传递当前选择的币种
      if (this.selectedCurrencyId) {
        this.$router.push({
          path: '/system/denomination-management',
          query: { currency_id: this.selectedCurrencyId }
        })
      } else {
        this.$router.push('/system/denomination-management')
      }
    },
    
    async publishToDisplay() {
      if (!this.hasValidRates) {
        this.$toast.warning('请先设置有效的面值汇率');
        return;
      }
      
      if (!confirm('确定要发布面值汇率到机顶盒显示吗？\n\n注意：如果今日已发布，将自动覆盖原有发布。')) {
        return;
      }
      
      this.loading = true;
      try {
        // 准备面值汇率数据
        const denominationRates = this.denominations
          .filter(denom => denom.buy_rate && denom.sell_rate && denom.buy_rate > 0 && denom.sell_rate > 0)
          .map(denom => ({
            denomination_id: denom.id,
            denomination_value: denom.denomination_value,
            denomination_type: denom.denomination_type,
            buy_rate: parseFloat(denom.buy_rate),
            sell_rate: parseFloat(denom.sell_rate)
          }));
        
        const response = await this.$api.post('/dashboard/publish-denomination-rates', {
          currency_id: this.selectedCurrencyId,
          currency_code: this.selectedCurrency.currency_code,
          denomination_rates: denominationRates
        });
        
        if (response.data.success) {
          this.$toast.success('面值汇率发布成功');
        } else {
          this.$toast.error(response.data.message || '发布失败');
        }
      } catch (error) {
        console.error('发布面值汇率失败:', error);
        this.$toast.error('发布面值汇率失败');
      } finally {
        this.loading = false;
      }
    },
    
    
    async showPublishHistory() {
      try {
        const response = await this.$api.get('/dashboard/denomination-publish-history', {
          params: {
            currency_id: this.selectedCurrencyId,
            page: 1,
            per_page: 20
          }
        });
        
        if (response.data.success) {
          // 显示发布历史模态框
          this.$emit('show-publish-history', response.data.data);
        } else {
          this.$toast.error('获取发布历史失败');
        }
      } catch (error) {
        console.error('获取发布历史失败:', error);
        this.$toast.error('获取发布历史失败');
      }
    },
    
    formatDenominationValue(value) {
      return new Intl.NumberFormat('zh-CN', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
      }).format(value)
    },
    
    formatSpread(spread) {
      return spread > 0 ? `+${spread.toFixed(4)}` : spread.toFixed(4)
    },
    
    getSpreadClass(spread) {
      if (spread > 0) return 'bg-success'
      if (spread < 0) return 'bg-danger'
      return 'bg-secondary'
    },
    
    getCurrencyName(code) {
      return getCurrencyName(code)
    },
    
    // 新增：加载今日已设置面值汇率的币种
    async loadTodayDenominationCurrencies() {
      try {
        console.log('[面值汇率] 开始加载今日已设置币种...')
        const response = await this.$api.get('/dashboard/today-denomination-currencies')
        console.log('[面值汇率] API响应:', response.data)

        if (response.data.success) {
          this.todayDenominationCurrencies = response.data.data || []
          console.log('[面值汇率] 加载成功，币种数量:', this.todayDenominationCurrencies.length)
          this.todayDenominationCurrencies.forEach(currency => {
            console.log(`  - ${currency.currency_code}: ${currency.denomination_count}个面值`)
          })
        } else {
          console.error('[面值汇率] API返回失败:', response.data.message)
          this.todayDenominationCurrencies = []
        }
      } catch (error) {
        console.error('[面值汇率] 加载今日已设置币种失败:', error)
        console.error('[面值汇率] 错误详情:', error.response?.data || error.message)
        this.todayDenominationCurrencies = []

        // 如果是认证错误，提示用户重新登录
        if (error.response?.status === 401) {
          this.$toast.error('会话已过期，请重新登录')
        }
      }
    },
    
    // 新增：加载今日已发布面值汇率的币种
    async loadTodayPublishedCurrencies() {
      try {
        // 直接使用已有的API，从中筛选出今日已发布的币种
        const response = await this.$api.get('/denominations-api/currencies-with-denominations')
        if (response.data.success) {
          // 从API数据中提取今日已发布的币种
          const publishedCurrencies = response.data.data
            .filter(currency => currency.published_today)
            .map(currency => ({
              currency_id: currency.id,
              currency_code: currency.currency_code,
              currency_name: currency.currency_name,
              denomination_count: currency.denominations.length,
              publish_time: currency.last_updated
            }))

          this.todayPublishedCurrencies = publishedCurrencies
          console.log('今日已发布币种:', publishedCurrencies)
        }
      } catch (error) {
        console.error('加载今日已发布币种失败:', error)
        this.todayPublishedCurrencies = []
      }
    },
    
    // 新增：全选币种
    selectAllCurrencies() {
      this.selectedCurrenciesForBatch = this.todayDenominationCurrencies.map(c => c.currency_id)
    },
    
    // 新增：清空选择
    clearAllCurrencies() {
      this.selectedCurrenciesForBatch = []
    },
    
    // 新增：显示批量发布模态框
    showBatchPublishModal() {
      if (this.selectedCurrenciesForBatch.length === 0) {
        this.$toast.warning('请先选择要发布的币种')
        return
      }
      
      // 保持用户已设置的配置，只重置notes
      this.batchPublishConfig.notes = ''
      
      // 显示模态框
      const modal = new window.bootstrap.Modal(document.getElementById('batchPublishModal'))
      modal.show()
    },
    
    // 新增：批量发布面值汇率
    async batchPublishDenominationRates() {
      if (this.selectedCurrenciesForBatch.length === 0) {
        this.$toast.warning('请先选择要发布的币种')
        return
      }
      
      try {
        this.loading = true
        
        // 准备发布数据
        const currencies = []
        for (const currencyId of this.selectedCurrenciesForBatch) {
          const currency = this.todayDenominationCurrencies.find(c => c.currency_id === currencyId)
          if (currency) {
            // 获取该币种的面值汇率数据
            const response = await this.$api.get(`/dashboard/currency-denomination-rates/${currencyId}`)
            if (response.data.success && response.data.data.length > 0) {
              currencies.push({
                currency_id: currencyId,
                denomination_rates: response.data.data
              })
            }
          }
        }
        
        if (currencies.length === 0) {
          this.$toast.warning('没有找到有效的面值汇率数据')
          return
        }
        
        // 调试：打印发送的配置
        console.log('批量发布配置:', {
          theme: this.batchPublishConfig.theme,
          language: this.batchPublishConfig.language,
          notes: this.batchPublishConfig.notes,
          display_config: {
            items_per_page: this.batchPublishConfig.displayConfig.itemsPerPage,
            refresh_interval: this.batchPublishConfig.displayConfig.refreshInterval
          }
        })
        
        // 调用新的批次发布API
        const publishResponse = await this.$api.post('/dashboard/publish-batch-denomination-rates', {
          currencies: currencies,
          theme: this.batchPublishConfig.theme,
          language: this.batchPublishConfig.language,
          notes: this.batchPublishConfig.notes,
          items_per_page: this.batchPublishConfig.displayConfig.itemsPerPage,
          refresh_interval: this.batchPublishConfig.displayConfig.refreshInterval
        })
        
        if (publishResponse.data.success) {
          this.$toast.success('批量发布成功！')
          
          // 关闭模态框
          const modal = window.bootstrap.Modal.getInstance(document.getElementById('batchPublishModal'))
          modal.hide()
          
          // 清空选择
          this.selectedCurrenciesForBatch = []
          
          // 刷新今日已设置币种列表
          this.loadTodayDenominationCurrencies()
        } else {
          this.$toast.error(publishResponse.data.message || '批量发布失败')
        }
      } catch (error) {
        console.error('批量发布失败:', error)
        this.$toast.error('批量发布失败')
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.denomination-rate-manager {
  width: 100%;
}

.currency-flag {
  width: 32px;
  height: 24px;
  object-fit: cover;
  border-radius: 4px;
  border: 1px solid #dee2e6;
}

/* 币种图标显示区域样式 */
.currency-display-area {
  background: #f8f9fa;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  padding: 20px;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.large-currency-flag {
  width: 80px;  /* 放大2倍：原来40px -> 80px */
  height: 60px; /* 放大2倍：原来30px -> 60px */
  object-fit: cover;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease;
}

.large-currency-flag:hover {
  transform: scale(1.05);
}

.currency-info h4 {
  color: #495057;
  font-weight: 600;
}

.currency-info p {
  font-size: 0.9rem;
}

.denomination-row:hover {
  background-color: #f8f9fa;
}

.denomination-cell {
  vertical-align: middle;
}

.spread-cell {
  text-align: center;
  vertical-align: middle;
}

.batch-operations {
  border-top: 1px solid #dee2e6;
  padding-top: 1rem;
}

.table th {
  font-weight: 600;
  font-size: 0.875rem;
}

.table td {
  vertical-align: middle;
}

.form-control-sm {
  font-size: 0.875rem;
}

.btn-group-sm .btn {
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
}
</style>
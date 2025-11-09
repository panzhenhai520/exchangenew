<template>
  <div class="step-content">
    <div class="mb-4">
      <p class="text-muted">{{ $t('eod.step7.description') }}</p>
    </div>

    <div class="row">
      <!-- 左侧：报表设置 -->
      <div class="col-md-4">
        <div class="card">
          <div class="card-header">
            <h6 class="mb-0">{{ $t('eod.step7.report_settings') }}</h6>
          </div>
          <div class="card-body">
            <!-- 报表模式 -->
            <div class="mb-3">
              <label class="form-label">{{ $t('eod.step7.report_mode') }}</label>
              <div class="form-check">
                <input
                  class="form-check-input"
                  type="radio"
                  id="mode-simple"
                  value="simple"
                  v-model="reportMode"
                />
                <label class="form-check-label" for="mode-simple">
                  <strong>{{ getReportModeLabel('simple') }}</strong>
                  <br>
                  <small class="text-muted">{{ $t('eod.step7.simple_mode_desc') }}</small>
                </label>
              </div>
              <!-- 根据差额情况动态显示第二个选项 -->
              <div v-if="shouldShowSecondReport" class="form-check">
                <input
                  class="form-check-input"
                  type="radio"
                  id="mode-detailed"
                  value="detailed"
                  v-model="reportMode"
                />
                <label class="form-check-label" for="mode-detailed">
                  <strong>{{ getSecondReportLabel() }}</strong>
                  <br>
                  <small class="text-muted">{{ getSecondReportDescription() }}</small>
                </label>
              </div>
            </div>

            <!-- 打印设置 -->
            <div class="mb-3">
              <label for="print-copies" class="form-label">{{ $t('eod.step7.print_copies') }}</label>
              <input
                type="number"
                id="print-copies"
                class="form-control"
                v-model="printCopies"
                min="1"
                max="10"
              />
            </div>

            <div class="mb-3">
              <label for="paper-size" class="form-label">{{ $t('eod.step7.paper_size') }}</label>
              <select id="paper-size" class="form-select" v-model="paperSize">
                <option value="A4">{{ $t('eod.step7.paper_a4') }}</option>
                <option value="A5">{{ $t('eod.step7.paper_a5') }}</option>
                <option value="Letter">{{ $t('eod.step7.paper_letter') }}</option>
                <option value="Legal">{{ $t('eod.step7.paper_legal') }}</option>
                <option value="Custom">{{ $t('eod.step7.paper_custom') }}</option>
              </select>
            </div>

            <!-- 自定义纸张大小 -->
            <div v-if="paperSize === 'Custom'" class="mb-3">
              <label class="form-label">{{ $t('eod.step7.custom_size') }} (mm)</label>
              <div class="row">
                <div class="col-6">
                  <input
                    type="number"
                    class="form-control"
                    :placeholder="$t('eod.step7.custom_width')"
                    v-model="customWidth"
                    min="50"
                    max="500"
                  />
                </div>
                <div class="col-6">
                  <input
                    type="number"
                    class="form-control"
                    :placeholder="$t('eod.step7.custom_height')"
                    v-model="customHeight"
                    min="50"
                    max="500"
                  />
                </div>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="d-grid gap-2">
              
              <button 
                class="btn btn-success"
                @click="printReport"
                :disabled="!reportData || loading || isPrinting"
              >
                <span v-if="isPrinting">
                  <span class="spinner-border spinner-border-sm me-2" role="status"></span>
                  {{ $t('eod.step7.printing') }}
                </span>
                <span v-else>
                  <font-awesome-icon :icon="['fas', 'print']" class="me-2" />
                  {{ getPrintButtonText() }}
                </span>
              </button>
            </div>
          </div>
        </div>

        <!-- 打印历史 -->
        <div v-if="printHistory.length > 0" class="card mt-3">
          <div class="card-header">
            <h6 class="mb-0">{{ $t('eod.step7.print_history') }}</h6>
          </div>
          <div class="card-body">
            <div v-for="record in printHistory" :key="record.id" class="d-flex justify-content-between align-items-center mb-2">
              <div>
                <small class="text-muted">{{ formatDateTime(record.printed_at) }}</small>
                <br>
                <span class="badge bg-info">{{ record.mode === 'simple' ? $t('eod.step7.simple') : $t('eod.step7.detailed') }}</span>
              </div>
              <span class="badge bg-secondary">{{ record.copies || 1 }} {{ $t('eod.step7.copies') }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：报表预览 -->
      <div class="col-md-8">
        <div class="card">
          <div class="card-header d-flex justify-content-between align-items-center">
            <h6 class="mb-0">{{ $t('eod.step7.report_preview') }}</h6>
            <div v-if="reportData">
              <span class="badge bg-success me-2">{{ $t('eod.step7.generated') }}</span>
              <span class="badge bg-info">{{ reportMode === 'simple' ? $t('eod.step7.simple_mode_label') : $t('eod.step7.detailed_mode_label') }}</span>
            </div>
          </div>
          <div class="card-body">
            <div v-if="!reportData" class="text-center py-5">
              <font-awesome-icon :icon="['fas', 'file-alt']" size="3x" class="text-muted mb-3" />
              <p class="text-muted">{{ $t('eod.step7.please_generate') }}</p>
            </div>

            <div v-else class="report-preview" :style="getPreviewStyle()">
              <!-- 报表头部 -->
              <div class="report-header text-center mb-3">
                <h3 class="mb-1">{{ reportMode === 'detailed' ? $t('eod.step7.detailed_report_title') : $t('eod.step7.summary_report_title') }}</h3>
                <h5 class="text-muted mb-2">{{ reportData.branch_name }}</h5>
                <div class="row">
                  <div class="col-6">
                    <strong>{{ $t('eod.step7.eod_date') }}:</strong> {{ reportData.eod_date }}
                  </div>
                  <div class="col-6">
                    <strong>{{ $t('eod.step7.generated_at') }}:</strong> {{ formatDateTime(reportData.generated_at) }}
                  </div>
                </div>
              </div>

              <!-- 交易统计 -->
              <div class="report-section">
                <h6 class="section-title">{{ $t('eod.step7.transaction_stats') }}</h6>
                <table class="table table-sm table-bordered">
                  <tbody>
                    <tr>
                      <td><strong>{{ $t('eod.step7.total_transactions') }}</strong></td>
                      <td class="text-end">{{ reportData.total_transactions }} {{ $t('eod.transactions_unit') }}</td>
                    </tr>
                    <tr>
                      <td><strong>{{ $t('eod.step7.buy_transactions') }}</strong></td>
                      <td class="text-end">{{ reportData.buy_transactions }} {{ $t('eod.transactions_unit') }}</td>
                    </tr>
                    <tr>
                      <td><strong>{{ $t('eod.step7.sell_transactions') }}</strong></td>
                      <td class="text-end">{{ reportData.sell_transactions }} {{ $t('eod.transactions_unit') }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <!-- 余额汇总（简单模式） -->
              <div v-if="reportMode === 'simple'" class="report-section">
                <h6 class="section-title">{{ $t('eod.step7.balance_summary') }}</h6>
                <table class="table table-sm table-bordered">
                  <thead>
                    <tr>
                      <th>{{ $t('eod.currency') }}</th>
                      <th>{{ $t('eod.step7.currency_name') }}</th>
                      <th class="text-end">{{ $t('eod.step7.opening_balance') }}</th>
                      <th class="text-end">{{ $t('eod.step7.actual_balance') }}</th>
                      <th class="text-end">{{ $t('eod.step7.theoretical_balance') }}</th>
                      <th class="text-end">{{ $t('eod.step7.difference') }}</th>
                      <th class="text-center">{{ $t('eod.step7.status') }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="balance in reportData.balance_summary" :key="balance.currency_id">
                      <td>{{ balance.currency_code }}</td>
                      <td>{{ getTranslatedCurrencyName(balance) }}</td>
                      <td class="text-end">{{ formatAmount(balance.opening_balance) }}</td>
                      <td class="text-end">{{ formatAmount(balance.actual_balance) }}</td>
                      <td class="text-end">{{ formatAmount(balance.theoretical_balance) }}</td>
                      <td class="text-end" :class="getBalanceClass(balance.difference)">
                        {{ formatAmount(balance.difference) }}
                      </td>
                      <td class="text-center">
                        <span v-if="balance.status" :class="getStatusClass(balance)">
                          {{ getTranslatedStatus(balance.status) }}
                        </span>
                        <span v-else :class="balance.is_match ? 'text-success' : 'text-danger'">
                          {{ balance.is_match ? '✓' : '✗' }}
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <!-- 差额调节表（如果有差额调节） -->
              <div v-if="reportData.difference_adjustment_summary && reportData.difference_adjustment_summary.length > 0" class="report-section">
                <h6 class="section-title">{{ $t('eod.step7.difference_adjustment_table') }}</h6>
                <table class="table table-sm table-bordered">
                  <thead>
                    <tr>
                      <th>{{ $t('eod.step7.currency_name') }}</th>
                      <th class="text-end">{{ $t('eod.step7.theoretical_balance') }}</th>
                      <th class="text-end">{{ $t('eod.step7.actual_balance') }}</th>
                      <th class="text-end">{{ $t('eod.step7.adjust_amount') }}</th>
                      <th>{{ $t('eod.step7.adjust_reason') }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="adjustment in reportData.difference_adjustment_summary" :key="adjustment.currency_code">
                      <td>{{ getTranslatedCurrencyName(adjustment) }}</td>
                      <td class="text-end">{{ formatAmount(adjustment.theoretical_balance) }}</td>
                      <td class="text-end">{{ formatAmount(adjustment.original_actual_balance || adjustment.actual_balance) }}</td>
                      <td class="text-end" :class="getBalanceClass(adjustment.adjust_amount)">
                        {{ formatAmount(adjustment.adjust_amount) }}
                      </td>
                      <td>{{ adjustment.reason }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <!-- 差额报告表（如果有差额但未调节） -->
              <div v-if="reportData.difference_report_summary && reportData.difference_report_summary.length > 0" class="report-section">
                <h6 class="section-title">{{ $t('eod.step7.difference_table') }}</h6>
                <table class="table table-sm table-bordered">
                  <thead>
                    <tr>
                      <th>{{ $t('eod.step7.currency_name') }}</th>
                      <th class="text-end">{{ $t('eod.step7.theoretical_balance') }}</th>
                      <th class="text-end">{{ $t('eod.step7.actual_balance') }}</th>
                      <th class="text-end">{{ $t('eod.step7.difference') }}</th>
                      <th>{{ $t('eod.step7.difference_reason') }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="difference in reportData.difference_report_summary" :key="difference.currency_code">
                      <td>{{ getTranslatedCurrencyName(difference) }}</td>
                      <td class="text-end">{{ formatAmount(difference.theoretical_balance) }}</td>
                      <td class="text-end">{{ formatAmount(difference.actual_balance) }}</td>
                      <td class="text-end" :class="getBalanceClass(difference.difference)">
                        {{ formatAmount(difference.difference) }}
                      </td>
                      <td></td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <!-- 交款汇总（如果有交款记录） -->
              <div v-if="reportData.cash_out_summary && reportData.cash_out_summary.length > 0" class="report-section">
                <h6 class="section-title">{{ $t('eod.step7.cash_out_summary') }}</h6>
                <table class="table table-sm table-bordered">
                  <thead>
                    <tr>
                      <th>{{ $t('eod.currency') }}</th>
                      <th>{{ $t('eod.step7.currency_name') }}</th>
                      <th class="text-end">{{ $t('eod.step7.cash_out_amount') }}</th>
                      <th class="text-end">{{ $t('eod.step7.remaining_balance') }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="cashOut in reportData.cash_out_summary" :key="cashOut.currency_id">
                      <td>{{ cashOut.currency_code }}</td>
                      <td>{{ getTranslatedCurrencyName(cashOut) }}</td>
                      <td class="text-end">{{ formatAmount(cashOut.cash_out_amount) }}</td>
                      <td class="text-end">{{ formatAmount(cashOut.remaining_balance) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <!-- 详细模式：收入汇总 -->
              <div v-if="reportMode === 'detailed' && reportData.income_summary && reportData.income_summary.length > 0" class="report-section">
                <h6 class="section-title">{{ $t('eod.step7.income_summary') }}</h6>
                <table class="table table-sm table-bordered">
                  <thead>
                    <tr>
                      <th>{{ $t('eod.currency') }}</th>
                      <th>{{ $t('eod.step7.currency_name') }}</th>
                      <th class="text-end">{{ $t('eod.step7.buy_amount') }}</th>
                      <th class="text-end">{{ $t('eod.step7.sell_amount') }}</th>
                      <th class="text-end">{{ $t('eod.step7.buy_rate') }}</th>
                      <th class="text-end">{{ $t('eod.step7.sell_rate') }}</th>
                      <th class="text-end">{{ $t('eod.step7.net_income') }}</th>
                      <th class="text-end">{{ $t('eod.step7.spread_income') }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="income in reportData.income_summary" :key="income.currency_code">
                      <td>{{ income.currency_code }}</td>
                      <td>{{ getTranslatedCurrencyName(income) }}</td>
                      <td class="text-end">{{ formatAmount(income.total_buy) }}</td>
                      <td class="text-end">{{ formatAmount(income.total_sell) }}</td>
                      <td class="text-end">{{ formatRate(income.buy_rate) }}</td>
                      <td class="text-end">{{ formatRate(income.sell_rate) }}</td>
                      <td class="text-end">{{ formatAmount(income.income) }}</td>
                      <td class="text-end">{{ formatAmount(income.spread_income) }}</td>
                    </tr>
                    <tr class="table-secondary">
                      <td><strong>{{ $t('eod.step7.total') }}</strong></td>
                      <td></td>
                      <td></td>
                      <td></td>
                      <td></td>
                      <td></td>
                      <td class="text-end"><strong>{{ formatAmount(getTotalIncome()) }}</strong></td>
                      <td class="text-end"><strong>{{ formatAmount(getTotalSpreadIncome()) }}</strong></td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <!-- 详细模式：余额明细 -->
              <div v-if="reportMode === 'detailed'" class="report-section">
                <h6 class="section-title">{{ $t('eod.step7.balance_details') }}</h6>
                <table class="table table-sm table-bordered">
                  <thead>
                    <tr>
                      <th>{{ $t('eod.currency') }}</th>
                      <th class="text-end">{{ $t('eod.step7.opening_balance') }}</th>
                      <th class="text-end">{{ $t('eod.step7.closing_balance') }}</th>
                      <th class="text-end">{{ $t('eod.step7.actual_balance') }}</th>
                      <th class="text-end">{{ $t('eod.step7.difference') }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="balance in reportData.balance_summary" :key="balance.currency_id">
                      <td>{{ balance.currency_code }}</td>
                      <td class="text-end">{{ formatAmount(balance.opening_balance) }}</td>
                      <td class="text-end">{{ formatAmount(balance.theoretical_balance) }}</td>
                      <td class="text-end">{{ formatAmount(balance.actual_balance) }}</td>
                      <td class="text-end" :class="getBalanceClass(balance.difference)">
                        {{ formatAmount(balance.difference) }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <!-- 签字区域 -->
              <div class="report-footer">
                <div class="row">
                  <div class="col-6">
                    <div class="signature-area">
                      <p class="mb-1"><strong>{{ $t('eod.step7.cashier_signature') }}:</strong></p>
                      <div class="signature-line"></div>
                      <small class="text-muted">{{ reportData.operator_name }}</small>
                    </div>
                  </div>
                  <div class="col-6">
                    <div class="signature-area">
                      <p class="mb-1"><strong>{{ $t('eod.step7.receiver_signature') }}:</strong></p>
                      <div class="signature-line"></div>
                      <small class="text-muted">{{ $t('eod.step7.date') }}: {{ reportData.eod_date }}</small>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 完成按钮 -->
    <div v-if="reportData && printHistory.length > 0" class="d-flex justify-content-end mt-4">
      <button 
        class="btn btn-success"
        @click="proceedToNext"
        :disabled="loading"
      >
        <font-awesome-icon :icon="['fas', 'check']" class="me-1" />
        {{ $t('eod.step7.complete_report') }}
      </button>
    </div>

    <!-- 提示信息 -->
    <div v-else-if="reportData" class="alert alert-warning mt-4">
      <font-awesome-icon :icon="['fas', 'exclamation-triangle']" class="me-2" />
      {{ $t('eod.step7.please_print') }}
    </div>

    <!-- 隐藏的iframe用于打印 -->
    <iframe 
      ref="printFrame"
      style="display: none;"
      @load="onPrintFrameLoad"
    ></iframe>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { eodAPI } from '../../../api/eod'
import { formatDateTime, formatAmount } from '@/utils/formatters'
import { getCurrencyDisplayName } from '@/utils/currencyTranslator'

export default {
  name: 'Step7Report',
  emits: ['next', 'error'],
  props: {
    eodId: {
      type: [Number, String],
      required: true
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  setup(props, { emit }) {
    const { t } = useI18n()
    
    // 响应式数据
    const reportData = ref(null)
    const reportMode = ref('simple')
    const printCopies = ref(1)
    const paperSize = ref('A4')
    const customWidth = ref(210)
    const customHeight = ref(297)
    const isGenerating = ref(false)
    const isPrinting = ref(false)
    const printHistory = ref([])
    const printFrame = ref(null)
    const currentPrintBlob = ref(null)
    
    // 计算属性
    const currentUser = computed(() => {
      try {
        return JSON.parse(localStorage.getItem('user') || '{}')
      } catch {
        return {}
      }
    })
    
    // 【新增】币种名称翻译方法
    const getTranslatedCurrencyName = (currencyCodeOrObject) => {
      // 如果传入的是对象，直接使用
      if (currencyCodeOrObject && typeof currencyCodeOrObject === 'object') {
        return getCurrencyDisplayName(currencyCodeOrObject.currency_code, currencyCodeOrObject)
      }
      // 如果传入的是字符串，使用币种代码
      if (typeof currencyCodeOrObject === 'string') {
        return getCurrencyDisplayName(currencyCodeOrObject, null)
      }
      return currencyCodeOrObject || ''
    }
    
    // 【新增】状态文本翻译方法
    const getTranslatedStatus = (status) => {
      if (!status) return ''
      
      // 检查是否包含"差额调节"文本
      if (status.includes('差额调节')) {
        // 提取调节金额
        const amountMatch = status.match(/差额调节\s*([+-]?\d+\.?\d*)/)
        if (amountMatch) {
          const amount = amountMatch[1]
          // 根据当前语言返回翻译
          const currentLang = localStorage.getItem('language') || 'zh-CN'
          let translatedText = ''
          if (currentLang === 'th-TH' || currentLang === 'th') {
            translatedText = 'ปรับความแตกต่าง ' + amount
          } else if (currentLang === 'en-US' || currentLang === 'en') {
            translatedText = 'Adjust Difference ' + amount
          } else {
            translatedText = '差额调节 ' + amount
          }
          return translatedText
        }
        // 根据当前语言返回翻译
        const currentLang = localStorage.getItem('language') || 'zh-CN'
        if (currentLang === 'th-TH' || currentLang === 'th') {
          return 'ปรับความแตกต่าง'
        } else if (currentLang === 'en-US' || currentLang === 'en') {
          return 'Adjust Difference'
        } else {
          return '差额调节'
        }
      }
      
      // 检查是否包含翻译键格式的文本
      if (status.includes('eod.adjust_difference')) {
        // 提取调节金额
        const amountMatch = status.match(/eod\.adjust_difference\s*([+-]?\d+\.?\d*)/)
        if (amountMatch) {
          const amount = amountMatch[1]
          // 根据当前语言返回翻译
          const currentLang = localStorage.getItem('language') || 'zh-CN'
          let translatedText = ''
          if (currentLang === 'th-TH' || currentLang === 'th') {
            translatedText = 'ปรับความแตกต่าง ' + amount
          } else if (currentLang === 'en-US' || currentLang === 'en') {
            translatedText = 'Adjust Difference ' + amount
          } else {
            translatedText = '差额调节 ' + amount
          }
          return translatedText
        }
        // 根据当前语言返回翻译
        const currentLang = localStorage.getItem('language') || 'zh-CN'
        if (currentLang === 'th-TH' || currentLang === 'th') {
          return 'ปรับความแตกต่าง'
        } else if (currentLang === 'en-US' || currentLang === 'en') {
          return 'Adjust Difference'
        } else {
          return '差额调节'
        }
      }
      
      // 检查是否是纯翻译键
      if (status === 'eod.adjust_difference') {
        // 根据当前语言返回翻译
        const currentLang = localStorage.getItem('language') || 'zh-CN'
        if (currentLang === 'th-TH' || currentLang === 'th') {
          return 'ปรับความแตกต่าง'
        } else if (currentLang === 'en-US' || currentLang === 'en') {
          return 'Adjust Difference'
        } else {
          return '差额调节'
        }
      }
      
      return status
    }
    
    // 方法
    const generateReport = async () => {
      try {
        isGenerating.value = true
        
        const result = await eodAPI.previewReport(props.eodId, reportMode.value)
        
        if (result.success) {
          reportData.value = result.report_data
        } else {
          emit('error', result.message || '生成报表失败')
        }
      } catch (error) {
        console.error('生成报表失败:', error)
        emit('error', error.response?.data?.message || error.message || '生成报表失败')
      } finally {
        isGenerating.value = false
      }
    }
    
    const printReport = async () => {
      if (!reportData.value) {
        emit('error', '请先生成报表')
        return
      }
      
      try {
        isPrinting.value = true
        console.log('正在生成日结报表PDF...')
        
        // 获取当前语言设置
        const currentLocale = localStorage.getItem('language') || 'zh-CN'
        let language = 'zh'
        if (currentLocale === 'en-US') {
          language = 'en'
        } else if (currentLocale === 'th-TH') {
          language = 'th'
        }
        
        console.log(`当前语言: ${currentLocale}, PDF语言: ${language}`)
        
        // 检查是否有差额调节
        const hasAdjustment = reportData.value.balance_summary?.some(b => b.has_adjustment)
        const hasDifference = reportData.value.balance_summary?.some(b => b.difference !== 0 && !b.has_adjustment)
        
        let result
        if (reportMode.value === 'detailed') {
          // 详细模式：根据差额情况生成对应的报告
          if (hasAdjustment) {
            // 调用差额调节报告API
            result = await eodAPI.printDifferenceAdjustmentReport(props.eodId, language)
          } else if (hasDifference) {
            // 调用差额报告API
            result = await eodAPI.printDifferenceReport(props.eodId, language)
          } else {
            // 调用普通交款表API（详细模式）
            result = await eodAPI.printReport(props.eodId, 'detailed', language)
          }
        } else {
          // 简单模式：始终生成交款表
          result = await eodAPI.printReport(props.eodId, 'simple', language)
        }
        
        if (result.success) {
          console.log('日结报表PDF生成成功:', result)
          console.log('🌍 完整result对象:', JSON.stringify(result, null, 2))
          console.log('🌍 result.eod_no:', result.eod_no)
          console.log('🌍 props.eodId:', props.eodId)
          console.log('🌍 result.eod_id:', result.eod_id)
          
          // 检查eod_no是否存在且格式正确
          if (!result.eod_no || typeof result.eod_no !== 'string') {
            throw new Error(`EOD编号无效: ${result.eod_no}`)
          }
          
          if (!result.eod_no.startsWith('EOD')) {
            throw new Error(`EOD编号格式错误: ${result.eod_no}`)
          }
          
          // 添加到打印历史
          printHistory.value.push({
            id: Date.now(),
            mode: reportMode.value,
            copies: printCopies.value,
            printed_at: result.printed_at || new Date().toISOString(),
            operator: currentUser.value.name,
            print_count: result.print_count
          })
          
          // 显示成功消息
          console.log(`日结报表生成成功，第${result.print_count}次打印`)
          
          // 根据语言选择对应的PDF文件
          let pdfUrl
          if (language === 'en') {
            pdfUrl = `/api/end_of_day/${result.eod_no}/download-receipt?lang=en`
          } else if (language === 'th') {
            pdfUrl = `/api/end_of_day/${result.eod_no}/download-receipt?lang=th`
          } else {
            pdfUrl = `/api/end_of_day/${result.eod_no}/download-receipt`
          }
          
          console.log('🌍 PDF下载URL:', pdfUrl)
          
          // 获取认证token
          const token = localStorage.getItem('token')
          if (!token) {
            throw new Error('未找到认证信息，请重新登录')
          }
          
          console.log(`开始获取${language}语言PDF数据用于打印...`)
          
          // 使用fetch获取PDF文件（带认证头）
          const pdfFetchResponse = await fetch(pdfUrl, {
            method: 'GET',
            headers: {
              'Authorization': `Bearer ${token}`
            }
          })
          
          if (!pdfFetchResponse.ok) {
            const errorData = await pdfFetchResponse.json()
            throw new Error(errorData.message || '获取PDF文件失败')
          }
          
          // 获取PDF blob数据
          const pdfBlob = await pdfFetchResponse.blob()
          
          // 创建blob URL
          const blobUrl = window.URL.createObjectURL(pdfBlob)
          
          console.log('PDF blob URL创建成功，准备使用iframe打印...')
          
          // 存储当前blob用于后续清理
          currentPrintBlob.value = blobUrl
          
          // 使用iframe方式加载PDF并打印
          if (printFrame.value) {
            printFrame.value.src = blobUrl
          } else {
            // 如果iframe不存在，清理blob URL
            window.URL.revokeObjectURL(blobUrl)
            throw new Error('打印组件初始化失败')
          }
          
        } else {
          throw new Error(result.message || '日结报表生成失败')
        }
        
      } catch (error) {
        console.error('日结报表打印失败:', error)
        
        const errorMsg = error.response?.data?.message || error.message || '打印失败'
        emit('error', errorMsg)
      } finally {
        isPrinting.value = false
      }
    }
    
    // iframe加载完成后的处理
    const onPrintFrameLoad = () => {
      try {
        // 只有在有打印内容时才执行打印
        if (!currentPrintBlob.value || !printFrame.value.src) {
          console.log('iframe加载完成，但没有打印内容，跳过打印')
          return
        }
        
        console.log('PDF iframe加载完成，准备打印...')
        
        // 等待一小段时间确保PDF完全渲染
        setTimeout(() => {
          try {
            // 调用iframe的打印功能
            if (printFrame.value && printFrame.value.contentWindow) {
              printFrame.value.contentWindow.print()
              console.log('已触发iframe打印')
              
              // 打印后清理资源 - 给用户更多时间进行打印操作
              setTimeout(() => {
                if (currentPrintBlob.value) {
                  window.URL.revokeObjectURL(currentPrintBlob.value)
                  currentPrintBlob.value = null
                  console.log('PDF blob URL已清理')
                }
                // 清空iframe src
                if (printFrame.value) {
                  printFrame.value.src = ''
                }
              }, 20000) // 延长到20秒，给用户更多时间进行打印操作
            } else {
              console.warn('无法访问iframe内容窗口')
            }
          } catch (e) {
            console.warn('iframe打印失败:', e)
            // 清理资源
            if (currentPrintBlob.value) {
              window.URL.revokeObjectURL(currentPrintBlob.value)
              currentPrintBlob.value = null
            }
          }
        }, 1000)
        
      } catch (error) {
        console.error('iframe打印处理失败:', error)
        // 清理资源
        if (currentPrintBlob.value) {
          window.URL.revokeObjectURL(currentPrintBlob.value)
          currentPrintBlob.value = null
        }
      }
    }
    
    const getPreviewStyle = () => {
      let width = '100%'
      
      switch (paperSize.value) {
        case 'A4':
          width = '210mm'
          break
        case 'A5':
          width = '148mm'
          break
        case 'Custom':
          width = `${customWidth.value}mm`
          break
      }
      
      return {
        width,
        border: '1px solid #ddd',
        padding: '12px',
        backgroundColor: 'white',
        fontSize: '13px'
      }
    }
    
    const proceedToNext = async () => {
      try {
        isGenerating.value = true
        
        // 调用生成报表API推进到第8步
        const result = await eodAPI.generateReport(props.eodId, reportMode.value)
        
        if (result.success) {
          emit('next', {
            report_data: result.report_data || reportData.value,
            print_history: printHistory.value,
            step: result.step || 8,
            step_status: result.step_status || 'processing',
            from_api_call: true
          })
        } else {
          emit('error', result.message || '生成报表失败')
        }
      } catch (error) {
        console.error('生成报表失败:', error)
        emit('error', error.response?.data?.message || error.message || '生成报表失败')
      } finally {
        isGenerating.value = false
      }
    }
    
    const getBalanceClass = (amount) => {
      if (amount > 0) return 'text-success'
      if (amount < 0) return 'text-danger'
      return 'text-muted'
    }
    
    const getStatusClass = (balance) => {
      if (balance.has_adjustment) {
        return 'text-primary fw-bold'
      } else if (balance.status === 'X') {
        return 'text-danger fw-bold'
      } else {
        return 'text-success'
      }
    }
    
    const getReportModeLabel = (mode) => {
      // 检查是否有差额调节
      const hasAdjustment = reportData.value?.balance_summary?.some(b => b.has_adjustment)
      const hasDifference = reportData.value?.balance_summary?.some(b => b.difference !== 0 && !b.has_adjustment)
      
      if (mode === 'simple') {
        if (hasAdjustment) {
          return t('eod.step7.difference_adjustment_table')
        } else if (hasDifference) {
          return t('eod.step7.difference_table')
        } else {
          return t('eod.step7.payment_slip')
        }
      } else {
        if (hasAdjustment) {
          return t('eod.step7.difference_adjustment_table')
        } else if (hasDifference) {
          return t('eod.step7.difference_table')
        } else {
          return t('eod.step7.payment_slip')
        }
      }
    }
    
    const formatRate = (rate) => {
      if (!rate || rate === 0) return '0.0000'
      return Number(rate).toFixed(4)
    }
    
    const getTotalIncome = () => {
      if (!reportData.value || !reportData.value.income_summary) return 0
      return reportData.value.income_summary.reduce((total, item) => total + (item.income || 0), 0)
    }
    
    const getTotalSpreadIncome = () => {
      if (!reportData.value || !reportData.value.income_summary) return 0
      return reportData.value.income_summary.reduce((total, item) => total + (item.spread_income || 0), 0)
    }

    const getPrintButtonText = () => {
      // 检查是否有差额调节
      const hasAdjustment = reportData.value?.balance_summary?.some(b => b.has_adjustment)
      const hasDifference = reportData.value?.balance_summary?.some(b => b.difference !== 0 && !b.has_adjustment)
      
      if (hasAdjustment) {
        return t('eod.step7.print_summary_report')
      } else if (hasDifference) {
        return t('eod.step7.print_difference_report')
      } else {
        return t('eod.step7.print_payment_slip')
      }
    }
    
    const shouldShowGenerateButton = computed(() => {
      // 如果没有差额处理，则显示生成报表按钮
      const hasAdjustment = reportData.value?.balance_summary?.some(b => b.has_adjustment)
      const hasDifference = reportData.value?.balance_summary?.some(b => b.difference !== 0 && !b.has_adjustment)
      return !hasAdjustment && !hasDifference
    })

    const shouldShowSecondReport = computed(() => {
      // 如果有差额调节或有差额但未调节，则显示第二个报表选项
      const hasAdjustment = reportData.value?.balance_summary?.some(b => b.has_adjustment)
      const hasDifference = reportData.value?.balance_summary?.some(b => b.difference !== 0 && !b.has_adjustment)
      return hasAdjustment || hasDifference
    })

    const getSecondReportLabel = () => {
      // 检查是否有差额调节
      const hasAdjustment = reportData.value?.balance_summary?.some(b => b.has_adjustment)
      const hasDifference = reportData.value?.balance_summary?.some(b => b.difference !== 0 && !b.has_adjustment)
      
      if (hasAdjustment) {
        return t('eod.step7.difference_adjustment_report')
      } else if (hasDifference) {
        return t('eod.step7.difference_report')
      } else {
        return t('eod.step7.payment_slip')
      }
    }

    const getSecondReportDescription = () => {
      // 检查是否有差额调节
      const hasAdjustment = reportData.value?.balance_summary?.some(b => b.has_adjustment)
      const hasDifference = reportData.value?.balance_summary?.some(b => b.difference !== 0 && !b.has_adjustment)
      
      if (hasAdjustment) {
        return t('eod.step7.difference_adjustment_desc')
      } else if (hasDifference) {
        return t('eod.step7.difference_report_desc')
      } else {
        return t('eod.step7.simple_mode_desc')
      }
    }
    
    // 生命周期
    onMounted(() => {
      // 自动生成简单模式报表
      generateReport()
    })
    
    return {
      t,
      reportData,
      reportMode,
      printCopies,
      paperSize,
      customWidth,
      customHeight,
      isGenerating,
      isPrinting,
      printHistory,
      printFrame,
      generateReport,
      printReport,
      onPrintFrameLoad,
      getPreviewStyle,
      proceedToNext,
      getBalanceClass,
      formatAmount,
      formatDateTime,
      formatRate,
      getTotalIncome,
      getTotalSpreadIncome,
      getTranslatedCurrencyName,
      getTranslatedStatus,
      getPrintButtonText,
      shouldShowGenerateButton,
      getStatusClass,
      getReportModeLabel,
      shouldShowSecondReport,
      getSecondReportLabel,
      getSecondReportDescription
    }
  }
}
</script>

<style scoped>
.step-content {
  padding: 1rem 0;
}

.step-header h4 {
  color: #495057;
  margin-bottom: 0.5rem;
}

.report-preview {
  max-width: 100%;
  overflow: auto;
}

.report-header h3 {
  color: #495057;
  font-weight: bold;
}

.section-title {
  color: #495057;
  font-weight: 600;
  border-bottom: 2px solid #007bff;
  padding-bottom: 3px;
  margin-bottom: 8px;
}

.signature-area {
  padding: 10px 0;
}

.signature-line {
  border-bottom: 1px solid #000;
  height: 25px;
  margin: 8px 0;
}

.table-sm th,
.table-sm td {
  padding: 0.25rem;
  font-size: 0.875rem;
  line-height: 1.2;
}

.table-sm {
  margin-bottom: 0.5rem;
}

.form-check-label strong {
  color: #495057;
}

.card.bg-light {
  border: 1px solid #e9ecef;
}

.card-body {
  padding: 1rem;
}

.report-section {
  margin-bottom: 0.8rem;
}

.report-footer {
  margin-top: 1rem;
}

@media print {
  .step-content {
    padding: 0;
  }
  
  .card {
    border: none;
    box-shadow: none;
  }
  
  .btn {
    display: none;
  }
}
</style> 
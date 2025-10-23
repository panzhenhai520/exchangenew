<template>
  <div class="modal fade" :id="modalId" tabindex="-1" ref="modalRef">
    <div class="modal-dialog modal-xl-custom modal-dialog-scrollable">
      <div class="modal-content">
        <div class="modal-header bg-warning text-dark">
          <h5 class="modal-title">
            <font-awesome-icon :icon="['fas', 'exclamation-triangle']" class="me-2" />
            {{ $t('compliance.reservationRequired') }} - {{ reportTypeName }}
          </h5>
          <button type="button" class="btn-close" @click="closeModal"></button>
        </div>
        <div class="modal-body">
          <!-- 触发警告信息 -->
          <div class="alert alert-warning">
            <h6 class="alert-heading">
              <font-awesome-icon :icon="['fas', 'info-circle']" class="me-2" />
              {{ $t('compliance.triggerAlertTitle') }}
            </h6>
            <p class="mb-2">{{ triggerMessage }}</p>
            <hr />
            <p class="mb-0 small">
              <strong>{{ $t('compliance.reportType') }}:</strong> {{ reportType }}<br />
              <strong>{{ $t('compliance.allowContinue') }}:</strong> {{ allowContinue ? $t('common.yes') : $t('common.no') }}
            </p>
          </div>

          <!-- 交易信息摘要 -->
          <div class="card mb-3">
            <div class="card-header bg-light">
              <h6 class="mb-0">{{ $t('compliance.transactionSummary') }}</h6>
            </div>
            <div class="card-body">
              <div class="row">
                <div class="col-md-4 col-6 mb-2">
                  <small class="text-muted">{{ $t('compliance.direction') }}:</small>
                  <div><strong>{{ formatDirection(transactionData.exchangeMode) }}</strong></div>
                </div>
                <div class="col-md-4 col-6 mb-2">
                  <small class="text-muted">{{ $t('compliance.foreignCurrency') }}:</small>
                  <div><strong>{{ getForeignCurrency() }}</strong></div>
                </div>
                <div class="col-md-4 col-6 mb-2">
                  <small class="text-muted">{{ $t('compliance.localAmount') }}:</small>
                  <div><strong>{{ formatCurrency(getLocalAmount()) }} {{ getBaseCurrency() }}</strong></div>
                </div>
                <div class="col-md-4 col-6 mb-2">
                  <small class="text-muted">{{ $t('compliance.exchangeRate') }}:</small>
                  <div><strong>{{ transactionData.rate }}</strong></div>
                </div>
                <div class="col-md-4 col-6 mb-2">
                  <small class="text-muted">{{ $t('compliance.customerId') }}:</small>
                  <div><strong>{{ transactionData.customerId || '-' }}</strong></div>
                </div>
                <div class="col-md-4 col-6 mb-2">
                  <small class="text-muted">{{ $t('compliance.customerName') }}:</small>
                  <div><strong>{{ transactionData.customerName || '-' }}</strong></div>
                </div>
              </div>
            </div>
          </div>

          <!-- 动态表单 -->
          <div class="card">
            <div class="card-header bg-primary text-white">
              <h6 class="mb-0">{{ $t('compliance.fillRequiredInfo') }}</h6>
          </div>
            <div class="card-body">
              <div v-if="formLoading" class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
              <span class="visually-hidden">{{ $t('common.loading') }}</span>
                </div>
                <p class="mt-2 text-muted">{{ $t('compliance.loadingForm') }}</p>
              </div>

              <DynamicFormImproved
                v-else-if="Object.keys(initialFormData).length > 0"
                :report-type="reportType"
                :initial-data="initialFormData"
                :show-check-trigger="false"
                submit-button-text=""
                @submit="handleFormSubmit"
                @update:formData="onFormDataUpdate"
                ref="dynamicFormRef"
              />
              <div v-else class="text-center py-3">
                <div class="spinner-border spinner-border-sm text-primary me-2"></div>
                <span class="text-muted">{{ $t('compliance.generatingReportNumber') }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="closeModal">
            <font-awesome-icon :icon="['fas', 'times']" class="me-1" />
            {{ $t('common.cancel') }}
          </button>
          <button
            type="button"
            class="btn btn-primary"
            @click="submitReservation"
            :disabled="submitting"
          >
            <span v-if="submitting" class="spinner-border spinner-border-sm me-2"></span>
            <font-awesome-icon v-else :icon="['fas', 'check']" class="me-1" />
            {{ submitting ? $t('compliance.submitting') : $t('compliance.submitReservation') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { Modal } from 'bootstrap'
import DynamicFormImproved from '@/components/amlo/DynamicForm/DynamicFormImproved.vue'
import repformService from '@/services/api/repformService'
import { splitAddress } from '@/utils/addressParser'

export default {
  name: 'ReservationModal',
  components: {
    DynamicFormImproved
  },
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    reportType: {
      type: String,
      required: true
    },
    triggerMessage: {
      type: String,
      default: ''
    },
    transactionData: {
      type: Object,
      required: true
    },
    allowContinue: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:visible', 'submit', 'cancel'],
  setup(props, { emit }) {
    const { t } = useI18n()

    const modalId = 'reservationModal'
    const modalRef = ref(null)
    const dynamicFormRef = ref(null)
    let modalInstance = null

    const formLoading = ref(false)
    const submitting = ref(false)
    const formData = ref({})

    const getTriggerType = (reportType) => {
      const mapping = {
        'AMLO-1-01': 'CTR',
        'AMLO-1-02': 'ATR',
        'AMLO-1-03': 'STR'
      }
      return mapping[reportType] || 'CTR'
    }

    // 计算属性
    const reportTypeName = computed(() => {
      const names = {
        'AMLO-1-01': t('compliance.ctr'),
        'AMLO-1-02': t('compliance.atr'),
        'AMLO-1-03': t('compliance.str'),
        'BOT_BuyFX': 'BOT Buy FX',
        'BOT_SellFX': 'BOT Sell FX',
        'BOT_FCD': 'BOT FCD',
        'BOT_Provider': 'BOT Provider'
      }
      return names[props.reportType] || props.reportType
    })

    // 获取用户和分支信息
    const getUserInfo = () => {
      try {
        const userInfo = localStorage.getItem('user')
        if (userInfo) {
          const user = JSON.parse(userInfo)
          console.log('[ReservationModal] getUserInfo返回:', {
            username: user.username,
            hasBranch: !!user.branch,
            branch_name: user.branch?.branch_name,
            company_name: user.branch?.company_name,
            institution_type: user.branch?.institution_type
          })
          return user
        }
      } catch (e) {
        console.error('[ReservationModal] 获取用户信息失败:', e)
      }
      return null
    }

    // 初始表单数据（从交易数据预填充）- 大幅增强版，支持双向交易
    const normalizeDigits = (value, length, fallback) => {
      const digits = String(value || '').replace(/\D/g, '')
      const base = digits || fallback || ''.padStart(length, '0')
      return base.slice(0, length).padStart(length, '0')
    }

    // 生成AMLO报告编号
    const generateReportNumber = async () => {
      try {
        const user = getUserInfo()
        const branchId = user?.branch?.id || user?.branch_id || 1
        const currencyCode = getForeignCurrency()
        
        console.log('[ReservationModal] 生成报告编号参数:', {
          branchId,
          currencyCode,
          reportType: props.reportType
        })

        // 使用统一的api服务而不是直接使用fetch
        const api = (await import('../../services/api')).default
        
        const response = await api.post('/report-numbers/amlo/generate', {
          branch_id: branchId,
          currency_code: currencyCode,
          transaction_id: props.transactionData.transactionId || null
        })
        
        if (response.data.success) {
          console.log('[ReservationModal] 报告编号生成成功:', response.data.data.report_number)
          return response.data.data.report_number
        } else {
          console.error('[ReservationModal] 报告编号生成失败:', response.data.message)
          return null
        }
      } catch (error) {
        console.error('[ReservationModal] 报告编号生成异常:', error)
        return null
      }
    }

    // 初始化表单数据
    const initialFormData = ref({})
    
    const initializeFormData = async () => {
      console.log('[ReservationModal] ===== 开始初始化表单数据 =====')
      console.log('[ReservationModal] transactionData:', props.transactionData)

      const user = getUserInfo()
      const foreignCurrency = getForeignCurrency()
      const transDate = new Date()

      // 判断交易类型和方向
      const isBuyForeign = props.transactionData.exchangeMode === 'buy_foreign'
      const isSellForeign = props.transactionData.exchangeMode === 'sell_foreign'
      const isDualDirection = props.transactionData.exchangeMode === 'dual_direction'

      console.log('[ReservationModal] 交易模式:', {
        isBuyForeign,
        isSellForeign,
        isDualDirection,
        exchangeMode: props.transactionData.exchangeMode
      })

      // 金额处理 - 根据交易模式确定
      let foreignAmount = 0
      let localAmount = 0
      let depositLocalCurrency = 0
      let depositThb = 0
      let withdrawForeignCurrency = 0
      let depositForeignCurrency = 0
      let withdrawLocalCurrency = 0
      let withdrawThb = 0

      if (isDualDirection) {
        // 双向交易：使用汇总数据
        console.log('[ReservationModal] 处理双向交易数据')

        const totalBuyLocalAmount = props.transactionData.totalBuyLocalAmount || 0
        const totalSellLocalAmount = props.transactionData.totalSellLocalAmount || 0
        const totalBuyForeignAmount = props.transactionData.totalBuyForeignAmount || 0
        const totalSellForeignAmount = props.transactionData.totalSellForeignAmount || 0

        console.log('[ReservationModal] 双向交易汇总:', {
          totalBuyLocalAmount,
          totalSellLocalAmount,
          totalBuyForeignAmount,
          totalSellForeignAmount
        })

        // 买入交易：客户存入本币，取出外币
        depositLocalCurrency = totalBuyLocalAmount
        depositThb = totalBuyLocalAmount
        withdrawForeignCurrency = totalBuyForeignAmount

        // 卖出交易：客户存入外币，取出本币
        depositForeignCurrency = totalSellForeignAmount
        withdrawLocalCurrency = totalSellLocalAmount
        withdrawThb = totalSellLocalAmount

        // 总金额：本币总额
        localAmount = Math.abs(props.transactionData.totalAmountThb || 0)
        foreignAmount = totalBuyForeignAmount + totalSellForeignAmount

      } else {
        // 单向交易：买入或卖出
        foreignAmount = Math.abs(parseFloat(props.transactionData.fromAmount) || 0)
        localAmount = Math.abs(parseFloat(props.transactionData.toAmount) || 0)

        if (isBuyForeign) {
          // 买入外币 = 客户存入本币，取出外币
          depositLocalCurrency = localAmount
          depositThb = localAmount
          withdrawForeignCurrency = foreignAmount
        } else if (isSellForeign) {
          // 卖出外币 = 客户存入外币，取出本币
          depositForeignCurrency = foreignAmount
          withdrawLocalCurrency = localAmount
          withdrawThb = localAmount
        }
      }

      console.log('[ReservationModal] 计算后的金额:', {
        foreignAmount,
        localAmount,
        depositLocalCurrency,
        depositThb,
        withdrawForeignCurrency,
        depositForeignCurrency,
        withdrawLocalCurrency,
        withdrawThb
      })

      // 确定交易类型和方向
      let transactionType = 'exchange'
      let direction = 'mixed'

      if (isBuyForeign) {
        transactionType = 'buy_foreign'
        direction = 'buy'
      } else if (isSellForeign) {
        transactionType = 'sell_foreign'
        direction = 'sell'
      } else if (isDualDirection) {
        transactionType = 'dual_direction'
        // 根据净金额判断主要方向
        if (depositLocalCurrency > withdrawLocalCurrency) {
          direction = 'buy'  // 净买入外币
        } else if (withdrawLocalCurrency > depositLocalCurrency) {
          direction = 'sell'  // 净卖出外币
        } else {
          direction = 'mixed'  // 买卖相等
        }
      }

      console.log('[ReservationModal] 交易类型和方向:', { transactionType, direction })

      // 证件类型处理
      const idType = props.transactionData.idType || 'national_id'
      console.log('[ReservationModal] 证件类型:', idType)

      // 分离姓名（如果包含空格，分为名和姓）
      const customerNameParts = (props.transactionData.customerName || '').split(' ')
      const customerFirstName = customerNameParts[0] || ''
      const customerLastName = customerNameParts.slice(1).join(' ') || ''

      const reporterInstitutionCode = normalizeDigits(user?.branch?.amlo_institution_code || user?.amlo_institution_code, 3, '000')
      const reporterBranchCode = normalizeDigits(user?.branch?.amlo_branch_code || user?.amlo_branch_code, 3, '000')
      const reportYearFull = getYearForDate(transDate)
      const reportYearSuffix = String(reportYearFull).slice(-2)

      // 生成报告编号
      const generatedReportNumber = await generateReportNumber()

      const formData = {
        // === 交易人信息 (maker_*) ===
        maker_firstname: customerFirstName,
        maker_lastname: customerLastName,
        maker_company_name: props.transactionData.customerName || '',  // 如果是公司，使用完整名称
        maker_id_number: props.transactionData.customerId || '0000000000000', // 提供默认证件号
        maker_id_type_national: idType === 'national_id',
        maker_id_type_passport: idType === 'passport',
        maker_id_type_company: idType === 'tax_id',

        // === 交易人地址信息 (maker_address_*) ===
        maker_address_number: '-',  // 门牌/详细地址（必填，默认占位符）
        maker_address_village: '',  // 村/大楼（非必填）
        maker_address_lane: '',  // 巷（非必填）
        maker_address_road: '',  // 路（非必填）
        maker_address_subdistrict: '-',  // 街道（必填，默认占位符）
        maker_address_district: '-',  // 区（必填，默认占位符）
        maker_address_province: '-',  // 省（必填，默认占位符）
        maker_address_postalcode: '',  // 邮编（非必填）

        // === 交易人国籍 ===
        maker_birthplace_country: props.transactionData.customerCountryCode || 'TH',  // 出生国家/注册国

        // === 报告机构信息 (reporter_*) ===
        reporter_institution_type: user?.branch?.institution_type || user?.branch?.company_name || 'money_changer',
        reporter_institution_name: user?.branch?.company_name || user?.branch?.branch_name || '',
        reporter_branch_name: user?.branch?.branch_name || '',
        reporter_institution_code: reporterInstitutionCode,
        reporter_branch_code: reporterBranchCode,
        reporter_signature_date_day: transDate.getDate(),
        reporter_signature_date_month: transDate.getMonth() + 1,
        reporter_signature_date_year: reportYearFull,  // 自动判断：泰铢=佛历，非泰铢=公历

        // === 报告日期 ===
        report_date_day: transDate.getDate(),
        report_date_month: transDate.getMonth() + 1,
        report_date_year: reportYearFull,  // 自动判断：泰铢=佛历，非泰铢=公历
        report_year_suffix: reportYearSuffix,
        report_number_prefix: `${reporterInstitutionCode}-${reporterBranchCode}-${reportYearSuffix}`,
        report_number: generatedReportNumber || '',  // 自动生成的报告编号

        // === 交易日期 (transaction_date_*) ===
        transaction_date_day: transDate.getDate(),
        transaction_date_month: transDate.getMonth() + 1,
        transaction_date_year: getYearForDate(transDate),  // 自动判断：泰铢=佛历，非泰铢=公历

        // === 交易金额 ===
        total_amount: localAmount,  // 总金额（本币）

        // === 存款信息 (deposit_*) ===
        deposit_thb_amount: depositThb,  // 存入泰铢金额
        deposit_currency_code: foreignCurrency,  // 存入外币代码
        deposit_currency_amount: depositForeignCurrency,  // 存入外币金额
        deposit_cash: depositThb > 0,  // 如果有存入泰铢，默认是现金

        // === 取款信息 (withdrawal_*) ===
        withdrawal_thb_amount: withdrawThb,  // 取出泰铢金额
        withdrawal_currency_code: foreignCurrency,  // 取出外币代码
        withdrawal_currency_amount: withdrawForeignCurrency,  // 取出外币金额
        withdrawal_cash: withdrawForeignCurrency > 0,  // 如果有取出外币，默认是现金

        // === Checkbox选项 ===
        is_first_report: true,  // 默认是首次报告（大多数情况）
        is_amendment_report: false,  // 不是修正报告
        joint_party_exists: false,  // 默认无共同交易人
        exchange_currency_exists: true,  // 确定是外币兑换
        maker_type_person: true,  // 默认是个人（非公司）
        maker_type_juristic: false,  // 默认不是法人

        // === 交易目的和来源 ===
        transaction_purpose: props.transactionData.purpose || 'tourism',
        transaction_source: props.transactionData.fundingSource || props.transactionData.source || '',

        // === 其他信息 ===
        exchange_other_transaction: '',  // 其他交易说明
        exchange_other_description: props.transactionData.remarks || '',
      }

      if (props.transactionData.address) {
        const parsedAddress = splitAddress(props.transactionData.address)
        formData.maker_address_number = parsedAddress.number || formData.maker_address_number
        formData.maker_address_road = parsedAddress.road || formData.maker_address_road
        formData.maker_address_subdistrict = parsedAddress.subdistrict || formData.maker_address_subdistrict
        formData.maker_address_district = parsedAddress.district || formData.maker_address_district
        formData.maker_address_province = parsedAddress.province || formData.maker_address_province
        formData.maker_address_postalcode = parsedAddress.postalcode || formData.maker_address_postalcode
      }

      if (props.transactionData.exchangeType) {
        formData.exchange_type = props.transactionData.exchangeType
      }
      if (props.transactionData.fundingSource) {
        formData.funding_source = props.transactionData.fundingSource
      }
      if (props.transactionData.assetValue) {
        formData.asset_value = props.transactionData.assetValue
      }

      initialFormData.value = formData
      
      console.log('[ReservationModal] ===== 表单数据初始化完成 =====')
      console.log('[ReservationModal] 生成的报告编号:', generatedReportNumber)
      console.log('[ReservationModal] 最终formData:', formData)
    }

    // 格式化方向
    const formatDirection = (mode) => {
      if (mode === 'buy_foreign') {
        return t('exchange.customerBuyForeign')
      } else if (mode === 'sell_foreign') {
        return t('exchange.customerSellForeign')
      } else if (mode === 'dual_direction') {
        return t('exchange.dual_direction')  // Fixed: use underscore instead of camelCase
      } else if (mode === 'buy') {
        return t('exchange.buy')
      } else if (mode === 'sell') {
        return t('exchange.sell')
      }
      return mode
    }

    // 获取本币代码
    const getBaseCurrency = () => {
      // 从localStorage获取用户的本币信息
      try {
        const userInfo = localStorage.getItem('user')
        if (userInfo) {
          const user = JSON.parse(userInfo)
          if (user.branch_currency && user.branch_currency.code) {
            return user.branch_currency.code
          }
        }
      } catch (e) {
        console.error('[ReservationModal] 获取本币失败:', e)
      }
      return 'THB' // 默认泰铢
    }

    // 判断是否使用佛历（Buddhist Era）
    const shouldUseBuddhistEra = () => {
      const baseCurrency = getBaseCurrency()
      // 如果本币是泰铢，使用佛历；否则使用公历
      return baseCurrency === 'THB'
    }

    // 获取年份（根据本币自动判断佛历/公历）
    const getYearForDate = (date) => {
      const gregorianYear = date.getFullYear()
      return shouldUseBuddhistEra() ? gregorianYear + 543 : gregorianYear
    }

    // 获取外币代码（非本币的那个）
    const getForeignCurrency = () => {
      const baseCurrency = getBaseCurrency()
      const fromCurrency = props.transactionData.fromCurrency
      const toCurrency = props.transactionData.toCurrency

      // 返回不是本币的那个币种
      if (fromCurrency && fromCurrency !== baseCurrency) {
        return fromCurrency
      } else if (toCurrency && toCurrency !== baseCurrency) {
        return toCurrency
      }

      // 如果都没有，优先返回fromCurrency
      return fromCurrency || toCurrency || 'USD'
    }

    // 获取本币金额
    const getLocalAmount = () => {
      const totalAmountThb = props.transactionData.totalAmountThb || props.transactionData.toAmount || 0
      return Math.abs(parseFloat(totalAmountThb))
    }

    // 格式化货币
    const formatCurrency = (value) => {
      if (!value) return '0.00'
      return parseFloat(value).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      })
    }

    // 表单数据更新
    const onFormDataUpdate = (data) => {
      formData.value = data
    }

    // 表单提交回调
    const handleFormSubmit = (data) => {
      formData.value = data
    }

    // 提交预约
    const submitReservation = async () => {
      // 触发动态表单的验证和提交
      if (dynamicFormRef.value && dynamicFormRef.value.submitForm) {
        try {
          await dynamicFormRef.value.submitForm()
          
          // 如果验证通过，继续提交预约
          submitting.value = true

          const reservationData = {
            report_type: props.reportType,
            customer_id: props.transactionData.customerId,
            customer_name: props.transactionData.customerName,
            customer_country_code: props.transactionData.customerCountryCode,
            currency_id: props.transactionData.currencyId,
            direction: props.transactionData.exchangeMode === 'buy_foreign' ? 'sell' : 'buy',
            amount: Math.abs(parseFloat(props.transactionData.fromAmount)),
            local_amount: Math.abs(parseFloat(props.transactionData.toAmount)),
            rate: props.transactionData.rate,
            trigger_type: getTriggerType(props.reportType),
            form_data: formData.value,
            exchange_type: props.transactionData.exchangeType || formData.value.exchange_type || 'normal',
            funding_source: props.transactionData.fundingSource || formData.value.funding_source || null,
            asset_value: props.transactionData.assetValue || formData.value.asset_value || null
          }

          const response = await repformService.saveReservation(reservationData)

          if (response.data.success) {
            emit('submit', {
              reservation_id: response.data.reservation_id,
              report_type: props.reportType
            })
            closeModal()
          } else {
            alert(response.data.message || t('compliance.saveFailed'))
          }
        } catch (error) {
          console.error('Submit reservation error:', error)
          console.error('Error response data:', error.response?.data)

          // 显示详细的验证错误
          let errorMessage = error.response?.data?.message || error.message || t('compliance.saveFailed')
          if (error.response?.data?.errors && Array.isArray(error.response.data.errors)) {
            errorMessage += '\n\n详细错误:\n' + error.response.data.errors.join('\n')
          }

          alert(errorMessage)
        } finally {
          submitting.value = false
        }
      } else {
        // 如果动态表单没有准备好，直接提交现有数据
        submitting.value = true
        
        try {
        const reservationData = {
            report_type: props.reportType,
            customer_id: props.transactionData.customerId,
            customer_name: props.transactionData.customerName,
            customer_country_code: props.transactionData.customerCountryCode,
            currency_id: props.transactionData.currencyId,
            direction: props.transactionData.fromCurrency === 'THB' ? 'sell' : 'buy',
            amount: props.transactionData.fromAmount,
            local_amount: props.transactionData.toAmount,
            rate: props.transactionData.rate,
            trigger_type: getTriggerType(props.reportType),
            form_data: formData.value,
            transaction_data: props.transactionData,
            exchange_type: props.transactionData.exchangeType || 'normal',
            funding_source: props.transactionData.fundingSource || null,
            asset_value: props.transactionData.assetValue || null
          }

          const response = await repformService.saveReservation(reservationData)

        if (response.data.success) {
            emit('submit', {
            reservation_id: response.data.reservation_id,
              report_type: props.reportType
            })
            closeModal()
          } else {
            alert(response.data.message || t('compliance.saveFailed'))
          }
        } catch (error) {
          console.error('Submit reservation error:', error)
          alert(t('compliance.saveFailed'))
        } finally {
          submitting.value = false
        }
      }
    }

    // 打开模态框
    const openModal = async () => {
      console.log('[ReservationModal] ===== 打开模态框 =====')
      console.log('[ReservationModal] props.transactionData:', JSON.stringify(props.transactionData, null, 2))

      // 初始化表单数据
      await initializeFormData()
      console.log('[ReservationModal] initialFormData计算结果:', JSON.stringify(initialFormData.value, null, 2))

      if (modalRef.value) {
        modalInstance = new Modal(modalRef.value, {
          backdrop: 'static',
          keyboard: false
        })
        modalInstance.show()
      }
    }

    // 关闭模态框
    const closeModal = () => {
      if (modalInstance) {
        modalInstance.hide()
      }
      emit('update:visible', false)
      emit('cancel')
    }

    // 监听visible变化
    watch(() => props.visible, (newValue) => {
      if (newValue) {
        nextTick(() => {
          openModal()
        })
      } else {
        if (modalInstance) {
          modalInstance.hide()
        }
      }
    })

    onMounted(() => {
      if (props.visible) {
        openModal()
      }
    })

    return {
      modalId,
      modalRef,
      dynamicFormRef,
      formLoading,
      submitting,
      formData,
      reportTypeName,
      initialFormData,
      formatDirection,
      formatCurrency,
      getBaseCurrency,
      getForeignCurrency,
      getLocalAmount,
      onFormDataUpdate,
      handleFormSubmit,
      submitReservation,
      closeModal
    }
  }
}
</script>

<style scoped>
/* 自定义超大模态窗口 */
.modal-xl-custom {
  max-width: 95% !important;
  width: 1600px !important;
  margin: 1rem auto !important;
}

/* 确保滚动容器正常工作 */
.modal-dialog-scrollable {
  max-height: calc(100vh - 2rem) !important;
}

.modal-dialog-scrollable .modal-body {
  overflow-y: auto !important;
  max-height: calc(100vh - 200px) !important;
}

/* 响应式设计：大屏幕优化 */
@media (min-width: 1400px) {
  .modal-xl-custom {
    width: 1600px !important;
  }
}

@media (min-width: 1200px) and (max-width: 1399px) {
  .modal-xl-custom {
    width: 1400px !important;
  }
}

@media (min-width: 992px) and (max-width: 1199px) {
  .modal-xl-custom {
    width: 1200px !important;
  }
}

/* 响应式设计：中小屏幕优化 */
@media (max-width: 991px) {
  .modal-xl-custom {
    max-width: 95% !important;
    width: auto !important;
    margin: 0.5rem !important;
  }
}

@media (max-width: 768px) {
  .modal-xl-custom {
    margin: 0.5rem;
    max-width: calc(100% - 1rem) !important;
  }

  .card-body .row > div {
    padding: 0.25rem;
  }

  .alert {
    font-size: 0.875rem;
  }
}

/* 确保在小屏幕上表单元素适当缩放 */
@media (max-width: 576px) {
  .modal-xl-custom {
    max-width: 100% !important;
    margin: 0 !important;
  }

  .form-label {
    font-size: 0.875rem;
  }

  .form-control,
  .form-select {
    font-size: 0.875rem;
  }
}
</style>

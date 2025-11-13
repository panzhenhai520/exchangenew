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
                @fill-report="submitReservationAndViewPDF"
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
          <!-- 【填写报告】按钮 - 下载PDF（会自动提交预约） -->
          <button
            type="button"
            class="btn btn-info"
            @click="downloadPDFReport"
            :disabled="downloading"
          >
            <span v-if="downloading" class="spinner-border spinner-border-sm me-2"></span>
            <font-awesome-icon v-else :icon="['fas', 'download']" class="me-1" />
            {{ downloading ? $t('common.downloading') || '下载中...' : $t('amlo.form.fillReport') || '填写报告' }}
          </button>

          <!-- 【上传报告】按钮 - 上传填写好的PDF -->
          <button
            type="button"
            class="btn btn-success"
            @click="triggerUploadPDF"
            :disabled="!currentReservationId || uploading"
          >
            <span v-if="uploading" class="spinner-border spinner-border-sm me-2"></span>
            <font-awesome-icon v-else :icon="['fas', 'upload']" class="me-1" />
            {{ uploading ? $t('common.uploading') || '上传中...' : ($t('amlo.uploadReport') || '上传报告') }}
          </button>
          <input
            type="file"
            ref="pdfFileInput"
            accept="application/pdf"
            style="display: none"
            @change="handlePDFUpload"
          />

          <!-- 【用户签名】按钮 - 打开签名页面 -->
          <button
            type="button"
            class="btn btn-warning"
            @click="openSignaturePage"
            :disabled="!uploadedPDF"
          >
            <font-awesome-icon :icon="['fas', 'signature']" class="me-1" />
            {{ $t('amlo.userSignature') || '用户签名' }}
          </button>

          <!-- 【取消】按钮 -->
          <button type="button" class="btn btn-secondary" @click="closeModal">
            <font-awesome-icon :icon="['fas', 'times']" class="me-1" />
            {{ $t('common.cancel') }}
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- 上传进度Modal -->
  <div v-if="showUploadProgress" class="modal fade show d-block" tabindex="-1" style="background-color: rgba(0,0,0,0.5);">
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content">
        <div class="modal-header bg-info text-white">
          <h5 class="modal-title">
            <i class="fas fa-cloud-upload-alt me-2"></i>
            {{ uploadSuccess ? '上传成功' : '上传报告' }}
          </h5>
          <button v-if="uploadSuccess" type="button" class="btn-close btn-close-white" @click="closeUploadProgressModal"></button>
        </div>
        <div class="modal-body">
          <!-- 上传进度条 -->
          <div v-if="!uploadSuccess" class="mb-3">
            <div class="d-flex justify-content-between mb-2">
              <span>上传进度</span>
              <span>{{ uploadProgress }}%</span>
            </div>
            <div class="progress" style="height: 25px;">
              <div
                class="progress-bar progress-bar-striped progress-bar-animated"
                role="progressbar"
                :style="`width: ${uploadProgress}%`"
                :aria-valuenow="uploadProgress"
                aria-valuemin="0"
                aria-valuemax="100"
              >
                {{ uploadProgress }}%
              </div>
            </div>
          </div>

          <!-- 上传成功提示 -->
          <div v-if="uploadSuccess" class="text-center py-4">
            <i class="fas fa-check-circle text-success" style="font-size: 4rem;"></i>
            <h4 class="mt-3 text-success">上传成功！</h4>
            <p class="mt-3 mb-4 text-muted">
              您的报告已成功上传，请点击【用户签名】按钮进行签名。
            </p>
            <button type="button" class="btn btn-warning btn-lg" @click="closeUploadProgressAndOpenSignature">
              <i class="fas fa-signature me-2"></i>立即签名
            </button>
          </div>

          <!-- 错误提示 -->
          <div v-if="uploadError" class="alert alert-danger">
            <i class="fas fa-exclamation-triangle me-2"></i>
            {{ uploadError }}
          </div>
        </div>
        <div v-if="uploadSuccess" class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="closeUploadProgressModal">
            <i class="fas fa-times me-1"></i>稍后签名
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { Modal } from 'bootstrap'
import DynamicFormImproved from '@/components/amlo/DynamicForm/DynamicFormImproved.vue'
import repformService from '@/services/api/repformService'
import { splitAddress } from '@/utils/addressParser'
import { useOpenOnDisplay } from '@/utils/useOpenOnDisplay'
import api from '@/services/api'

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
    const { openOnDisplay } = useOpenOnDisplay()

    const modalId = 'reservationModal'
    const modalRef = ref(null)
    const dynamicFormRef = ref(null)
    let modalInstance = null

    const formLoading = ref(false)
    const submitting = ref(false)
    const formData = ref({})
    const currentReservationId = ref(null) // 当前预约ID
    const downloading = ref(false) // 下载中状态
    const uploading = ref(false) // 上传中状态
    const uploadedPDF = ref(false) // 是否已上传PDF
    const pdfFileInput = ref(null) // 文件输入框引用
    const showUploadProgress = ref(false) // 显示上传进度Modal
    const uploadProgress = ref(0) // 上传进度百分比
    const uploadSuccess = ref(false) // 上传成功标志
    const uploadError = ref(null) // 上传错误信息

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

      // 使用完整姓名（不要按空格分割，避免截断像"PAN ZHEN HAI"这样的名字）
      const customerFullName = props.transactionData.customerName || ''

      const reporterInstitutionCode = normalizeDigits(user?.branch?.amlo_institution_code || user?.amlo_institution_code, 3, '000')
      const reporterBranchCode = normalizeDigits(user?.branch?.amlo_branch_code || user?.amlo_branch_code, 3, '000')
      const reportYearFull = getYearForDate(transDate)
      const reportYearSuffix = String(reportYearFull).slice(-2)

      // 不在前端预生成报告编号，由后端在保存时生成（避免重复编号问题）
      // const generatedReportNumber = await generateReportNumber()

      const formData = {
        // === 交易人信息 (maker_*) ===
        maker_firstname: customerFullName,  // 使用完整姓名，不截断
        maker_company_name: customerFullName,  // 公司名称也使用完整名称
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
        report_number: '',  // 留空，由后端在保存时自动生成（避免重复编号问题）

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
      console.log('[ReservationModal] 报告编号将由后端自动生成')
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

          // 🔧 修复: 直接使用exchangeMode作为direction，不要重新计算！
          // exchangeMode可能是: 'buy', 'sell', 'dual_direction'
          let direction = props.transactionData.exchangeMode

          // 只有当exchangeMode是旧格式'buy_foreign'/'sell_foreign'时才转换
          if (direction === 'buy_foreign') {
            direction = 'sell'  // 网点卖出外币（客户买入）
          } else if (direction === 'sell_foreign') {
            direction = 'buy'   // 网点买入外币（客户卖出）
          }
          // 否则保持原值: 'buy', 'sell', 'dual_direction'

          console.log('[ReservationModal] 确定direction:', {
            exchangeMode: props.transactionData.exchangeMode,
            finalDirection: direction
          })

          const reservationData = {
            report_type: props.reportType,
            customer_id: props.transactionData.customerId,
            customer_name: props.transactionData.customerName,
            customer_country_code: props.transactionData.customerCountryCode,
            currency_id: props.transactionData.currencyId,
            direction: direction,  // 使用修复后的direction
            amount: Math.abs(parseFloat(props.transactionData.fromAmount)),
            local_amount: Math.abs(parseFloat(props.transactionData.toAmount)),
            rate: props.transactionData.rate,
            trigger_type: getTriggerType(props.reportType),
            form_data: formData.value,
            denomination_data: props.transactionData.combinations || [],  // 面值组合数据
            exchange_type: props.transactionData.exchangeType || formData.value.exchange_type || 'normal',
            funding_source: props.transactionData.fundingSource || formData.value.funding_source || null,
            asset_value: props.transactionData.assetValue || formData.value.asset_value || null
          }

          const response = await repformService.saveReservation(reservationData)

          if (response.data.success) {
            // 保存当前预约ID，供后续上传和签名使用
            currentReservationId.value = response.data.reservation_id

            // 检查是否有报告生成失败的警告
            if (response.data.warning || response.data.report_creation_failed) {
              console.warn('[ReservationModal] ⚠️ 报告生成失败:', response.data.warning)
              alert(`⚠️ 警告\n\n${response.data.warning || '报告生成失败，请联系技术支持'}`)
            }

            emit('submit', {
              reservation_id: response.data.reservation_id,
              report_type: props.reportType
            })
            // 不要立即关闭模态框，让用户可以下载、上传和签名
            // closeModal()
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
        // 🔧 修复: 使用相同的direction逻辑
        let direction = props.transactionData.exchangeMode

        // 只有当exchangeMode是旧格式时才转换
        if (direction === 'buy_foreign') {
          direction = 'sell'
        } else if (direction === 'sell_foreign') {
          direction = 'buy'
        }
        // 否则保持原值: 'buy', 'sell', 'dual_direction'

        console.log('[ReservationModal] (简化路径) 确定direction:', {
          exchangeMode: props.transactionData.exchangeMode,
          finalDirection: direction
        })

        const reservationData = {
            report_type: props.reportType,
            customer_id: props.transactionData.customerId,
            customer_name: props.transactionData.customerName,
            customer_country_code: props.transactionData.customerCountryCode,
            currency_id: props.transactionData.currencyId,
            direction: direction,  // 使用修复后的direction
            amount: props.transactionData.fromAmount,
            local_amount: props.transactionData.toAmount,
            rate: props.transactionData.rate,
            trigger_type: getTriggerType(props.reportType),
            form_data: formData.value,
            denomination_data: props.transactionData.combinations || [],  // 面值组合数据
            transaction_data: props.transactionData,
            exchange_type: props.transactionData.exchangeType || 'normal',
            funding_source: props.transactionData.fundingSource || null,
            asset_value: props.transactionData.assetValue || null
          }

          const response = await repformService.saveReservation(reservationData)

        if (response.data.success) {
            // 检查是否有报告生成失败的警告
            if (response.data.warning || response.data.report_creation_failed) {
              console.warn('[ReservationModal] ⚠️ 报告生成失败:', response.data.warning)
              alert(`⚠️ 警告\n\n${response.data.warning || '报告生成失败，请联系技术支持'}`)
            }

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

    // 【填写报告】- 下载PDF报告（如果还没有预约ID，先提交预约）
    const downloadPDFReport = async () => {
      downloading.value = true
      try {
        // 如果还没有预约ID，先提交预约
        if (!currentReservationId.value) {
          console.log('[ReservationModal] 还没有预约ID，先提交预约...')

          // 触发表单验证
          if (dynamicFormRef.value && dynamicFormRef.value.submitForm) {
            await dynamicFormRef.value.submitForm()
          }

          // 构建预约数据
          let direction = props.transactionData.exchangeMode
          if (direction === 'buy_foreign') {
            direction = 'sell'
          } else if (direction === 'sell_foreign') {
            direction = 'buy'
          }

          const reservationData = {
            report_type: props.reportType,
            customer_id: props.transactionData.customerId,
            customer_name: props.transactionData.customerName,
            customer_country_code: props.transactionData.customerCountryCode,
            currency_id: props.transactionData.currencyId,
            direction: direction,
            amount: Math.abs(parseFloat(props.transactionData.fromAmount)),
            local_amount: Math.abs(parseFloat(props.transactionData.toAmount)),
            rate: props.transactionData.rate,
            trigger_type: getTriggerType(props.reportType),
            form_data: formData.value,
            denomination_data: props.transactionData.combinations || [],
            exchange_type: props.transactionData.exchangeType || formData.value.exchange_type || 'normal',
            funding_source: props.transactionData.fundingSource || formData.value.funding_source || null,
            asset_value: props.transactionData.assetValue || formData.value.asset_value || null
          }

          console.log('[ReservationModal] 提交预约数据:', reservationData)

          const response = await repformService.saveReservation(reservationData)

          if (!response.data.success) {
            alert(response.data.message || t('compliance.saveFailed'))
            return
          }

          currentReservationId.value = response.data.reservation_id
          console.log('[ReservationModal] ✅ 预约创建成功，ID:', currentReservationId.value)

          // 🔧 注意：不在这里触发submit事件，等签名提交成功后再触发
        }

        // 现在有预约ID了，开始下载PDF
        console.log('[ReservationModal] 开始下载PDF报告, reservation_id:', currentReservationId.value)

        const timestamp = Date.now()
        const pdfResponse = await api.get(`/amlo/reservations/${currentReservationId.value}/generate-pdf?refresh=${timestamp}`, {
          responseType: 'blob'
        })

        // 创建下载链接
        const blob = new Blob([pdfResponse.data], { type: 'application/pdf' })
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url

        // 获取报告编号作为文件名
        const reportNumber = formData.value.report_number || currentReservationId.value
        link.download = `${reportNumber}.pdf`

        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(url)

        console.log('[ReservationModal] ✅ PDF下载成功')

        // 显示详细的下载成功信息，包含文件名和保存位置
        const downloadMessage = `PDF下载成功！\n\n` +
          `文件名：${reportNumber}.pdf\n` +
          `保存位置：浏览器默认下载文件夹\n\n` +
          `请填写完成后，点击【上传报告】按钮上传。`
        alert(downloadMessage)

      } catch (error) {
        console.error('[ReservationModal] ❌ 下载PDF失败:', error)
        const errorMsg = error.response?.data?.message || error.message
        alert(t('amlo.downloadFailed') || `下载失败: ${errorMsg}`)
      } finally {
        downloading.value = false
      }
    }

    // 【上传报告】- 触发文件选择（如果没有预约ID，先提示点击【填写报告】）
    const triggerUploadPDF = () => {
      if (!currentReservationId.value) {
        alert(t('amlo.pleaseDownloadFirst') || '请先点击【填写报告】按钮提交预约并下载PDF')
        return
      }
      pdfFileInput.value?.click()
    }

    // 【上传报告】- 处理文件上传（带进度显示）
    const handlePDFUpload = async (event) => {
      const file = event.target.files?.[0]
      if (!file) return

      if (file.type !== 'application/pdf') {
        alert(t('amlo.pleaseSelectPDF') || '请选择PDF文件')
        return
      }

      // 重置上传状态
      uploading.value = true
      showUploadProgress.value = true
      uploadProgress.value = 0
      uploadSuccess.value = false
      uploadError.value = null

      try {
        console.log('[ReservationModal] 开始上传PDF文件, reservation_id:', currentReservationId.value)
        console.log('[ReservationModal] 文件信息:', {
          name: file.name,
          type: file.type,
          size: file.size
        })

        const uploadFormData = new FormData()
        uploadFormData.append('file', file) // 使用'file'作为参数名，匹配后端接口

        console.log('[ReservationModal] FormData内容:', {
          hasFile: uploadFormData.has('file'),
          fileFromFormData: uploadFormData.get('file')
        })

        // 不要手动设置Content-Type，让浏览器自动设置（包含boundary）
        // 使用空的 transformRequest 避免 axios 默认配置干扰 FormData
        // 添加 onUploadProgress 回调追踪上传进度
        const response = await api.post(
          `/amlo/reservations/${currentReservationId.value}/upload-filled-pdf`,
          uploadFormData,
          {
            transformRequest: [(data) => data], // 直接返回 FormData，不做任何转换
            headers: {
              'Content-Type': undefined // 让浏览器自动设置
            },
            onUploadProgress: (progressEvent) => {
              // 计算上传进度百分比
              if (progressEvent.total) {
                uploadProgress.value = Math.round((progressEvent.loaded * 100) / progressEvent.total)
                console.log('[ReservationModal] 上传进度:', uploadProgress.value + '%')
              }
            }
          }
        )

        console.log('[ReservationModal] 上传响应:', response.data)

        if (response.data.success) {
          uploadedPDF.value = true
          uploadSuccess.value = true
          console.log('[ReservationModal] ✅ PDF上传成功')
          // 上传成功，显示在Modal中，不需要alert
        } else {
          console.error('[ReservationModal] 上传失败:', response.data)
          uploadError.value = response.data.message || (t('amlo.uploadFailed') || '上传失败')
        }

      } catch (error) {
        console.error('[ReservationModal] ❌ 上传PDF失败:', error)
        console.error('[ReservationModal] 错误详情:', {
          status: error.response?.status,
          statusText: error.response?.statusText,
          data: error.response?.data,
          message: error.message
        })

        let errorMsg = error.response?.data?.message || error.message || '未知错误'
        if (error.response?.status === 401) {
          errorMsg = '未授权，请重新登录'
        } else if (error.response?.status === 404) {
          errorMsg = '未找到预约记录'
        } else if (error.response?.status === 400) {
          errorMsg = error.response?.data?.message || '请求参数错误'
        }

        uploadError.value = (t('amlo.uploadFailed') || '上传失败') + ': ' + errorMsg
      } finally {
        uploading.value = false
        // 清空文件输入框，允许重新上传相同文件
        if (pdfFileInput.value) {
          pdfFileInput.value.value = ''
        }
      }
    }

    // 关闭上传进度Modal
    const closeUploadProgressModal = () => {
      showUploadProgress.value = false
      uploadProgress.value = 0
      uploadSuccess.value = false
      uploadError.value = null
    }

    // 关闭上传进度Modal并打开签名页面
    const closeUploadProgressAndOpenSignature = () => {
      closeUploadProgressModal()
      openSignaturePage()
    }

    // 【用户签名】- 打开签名页面（复用现有的PDFViewerWindow）
    const openSignaturePage = async () => {
      if (!uploadedPDF.value || !currentReservationId.value) {
        alert(t('amlo.pleaseUploadFirst') || '请先上传填写好的报告')
        return
      }

      try {
        console.log('[ReservationModal] 打开签名页面, reservation_id:', currentReservationId.value)

        // 构建PDF查看器URL（复用现有的PDFViewerWindow）
        const baseUrl = window.location.origin
        const pdfViewerPath = '/amlo/pdf-viewer'
        const params = new URLSearchParams({
          id: currentReservationId.value,
          title: `${props.reportType} - ${formData.value.report_number || currentReservationId.value}`,
          reportType: props.reportType
        })
        const url = `${baseUrl}${pdfViewerPath}?${params.toString()}`

        console.log('[ReservationModal] PDF Viewer URL:', url)

        // 使用useOpenOnDisplay打开窗口（自动在扩展显示器上，全屏显示）
        const pdfWindow = await openOnDisplay({
          url: url,
          target: 'AMLOSignatureWindow',
          preferNonPrimary: true,
          includeTaskbarArea: false, // 使用可用工作区（最大化效果）
          fallbackGuess: 'right',
          features: 'width=1920,height=1080,left=0,top=0,fullscreen=yes,toolbar=no,menubar=no,location=no,status=no'
        })

        if (!pdfWindow) {
          alert(t('compliance.popupBlocked') || '弹出窗口被阻止，请允许弹出窗口后重试')
          console.error('[ReservationModal] PDF签名窗口打开失败 - 弹窗被阻止')
        } else {
          console.log('[ReservationModal] ✅ PDF签名窗口已在扩展显示器上打开')
          // 不显示提示，窗口会自动在顶部显示提示条
        }

      } catch (error) {
        console.error('[ReservationModal] ❌ 打开签名页面失败:', error)
        alert(t('amlo.openSignatureFailed') || `打开签名页面失败: ${error.message}`)
      }
    }

    // 提交预约并自动打开PDF查看器（用于【填写报告】按钮）
    const submitReservationAndViewPDF = async (formDataFromEvent) => {
      console.log('[ReservationModal] ===== submitReservationAndViewPDF 被调用 =====')
      console.log('[ReservationModal] formDataFromEvent:', formDataFromEvent)

      try {
        // 更新表单数据
        formData.value = formDataFromEvent

        submitting.value = true

        // 确定direction（复用submitReservation的逻辑）
        let direction = props.transactionData.exchangeMode

        // 只有当exchangeMode是旧格式'buy_foreign'/'sell_foreign'时才转换
        if (direction === 'buy_foreign') {
          direction = 'sell'  // 网点卖出外币（客户买入）
        } else if (direction === 'sell_foreign') {
          direction = 'buy'   // 网点买入外币（客户卖出）
        }
        // 否则保持原值: 'buy', 'sell', 'dual_direction'

        console.log('[ReservationModal] direction:', direction)

        // 构建预约数据（复用submitReservation的逻辑）
        const reservationData = {
          report_type: props.reportType,
          customer_id: props.transactionData.customerId,
          customer_name: props.transactionData.customerName,
          customer_country_code: props.transactionData.customerCountryCode,
          currency_id: props.transactionData.currencyId,
          direction: direction,
          amount: Math.abs(parseFloat(props.transactionData.fromAmount)),
          local_amount: Math.abs(parseFloat(props.transactionData.toAmount)),
          rate: props.transactionData.rate,
          trigger_type: getTriggerType(props.reportType),
          form_data: formData.value,
          denomination_data: props.transactionData.combinations || [],
          exchange_type: props.transactionData.exchangeType || formData.value.exchange_type || 'normal',
          funding_source: props.transactionData.fundingSource || formData.value.funding_source || null,
          asset_value: props.transactionData.assetValue || formData.value.asset_value || null
        }

        console.log('[ReservationModal] 提交预约数据:', reservationData)

        // 提交预约
        const response = await repformService.saveReservation(reservationData)

        if (response.data.success) {
          const reservationId = response.data.reservation_id
          currentReservationId.value = reservationId // 保存当前预约ID
          console.log('[ReservationModal] ✅ 预约创建成功，ID:', reservationId)

          // 检查是否有报告生成失败的警告
          if (response.data.warning || response.data.report_creation_failed) {
            console.warn('[ReservationModal] ⚠️ 报告生成失败:', response.data.warning)
            alert(`⚠️ 警告\n\n${response.data.warning || '报告生成失败，请联系技术支持'}`)
          }

          // 先发出submit事件
          emit('submit', {
            reservation_id: reservationId,
            report_type: props.reportType
          })

          // 只有当报告成功创建时才打开PDF查看器
          if (response.data.report_id && !response.data.report_creation_failed) {
            // 然后打开PDF查看器（使用useOpenOnDisplay在扩展显示器上打开）
            console.log('[ReservationModal] 打开PDF查看器...')

            // 构建PDF查看器URL
            const baseUrl = window.location.origin
            const pdfViewerPath = '/amlo/pdf-viewer'
            const params = new URLSearchParams({
              id: reservationId,
              title: `${props.reportType} - ${reservationId}`,
              reportType: props.reportType
            })
            const url = `${baseUrl}${pdfViewerPath}?${params.toString()}`

            console.log('[ReservationModal] PDF Viewer URL:', url)

            // 使用useOpenOnDisplay打开窗口（自动在扩展显示器上，全屏显示）
            const pdfWindow = await openOnDisplay({
              url: url,                        // PDF查看器URL
              target: 'AMLOPDFViewer',        // 窗口名称（复用同一窗口）
              preferNonPrimary: true,         // 优先选择非主屏（扩展显示器）
              includeTaskbarArea: false,      // 使用可用工作区（避开任务栏），等效最大化
              fallbackGuess: 'right',         // 不支持多屏API时，猜测扩展屏在右侧
              features: 'width=1920,height=1080,left=0,top=0,fullscreen=yes,toolbar=no,menubar=no,location=no,status=no'
            })

            if (!pdfWindow) {
              alert(t('compliance.popupBlocked') || '弹出窗口被阻止，请允许弹出窗口后重试')
              console.error('[ReservationModal] PDF窗口打开失败 - 弹窗被阻止')
            } else {
              console.log('[ReservationModal] ✅ PDF查看器窗口已在扩展显示器上打开')
            }
          } else if (response.data.report_creation_failed) {
            console.warn('[ReservationModal] 报告生成失败，跳过打开PDF查看器')
          }

          // 关闭模态框
          closeModal()

        } else {
          console.error('[ReservationModal] ❌ 预约创建失败:', response.data.message)
          alert(response.data.message || t('compliance.saveFailed'))
        }
      } catch (error) {
        console.error('[ReservationModal] ❌ 提交预约失败:', error)
        console.error('[ReservationModal] 错误详情:', error.response?.data)

        // 显示详细的验证错误
        let errorMessage = error.response?.data?.message || error.message || t('compliance.saveFailed')
        if (error.response?.data?.errors && Array.isArray(error.response.data.errors)) {
          errorMessage += '\n\n详细错误:\n' + error.response.data.errors.join('\n')
        }

        alert(errorMessage)
      } finally {
        submitting.value = false
      }
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

    // 监听来自PDF窗口的消息
    const handleMessageFromPDFWindow = (event) => {
      // 安全检查：确保消息来源可信
      if (!event.data || !event.data.type) return

      if (event.data.type === 'CLOSE_RESERVATION_MODAL') {
        console.log('[ReservationModal] 收到PDF窗口的关闭请求，关闭模态框...')
        closeModal()
      } else if (event.data.type === 'SIGNATURE_SUBMITTED') {
        console.log('[ReservationModal] 收到签名提交成功消息，触发submit事件...')
        // 🔧 签名提交成功后，触发submit事件，通知父组件显示"预约已提交"消息
        emit('submit', {
          reservation_id: event.data.reservation_id,
          report_type: event.data.report_type
        })
      }
    }

    onMounted(() => {
      if (props.visible) {
        openModal()
      }

      // 添加消息监听器
      window.addEventListener('message', handleMessageFromPDFWindow)
    })

    onUnmounted(() => {
      // 移除消息监听器
      window.removeEventListener('message', handleMessageFromPDFWindow)
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
      submitReservationAndViewPDF,
      closeModal,
      // 新增的状态和方法
      currentReservationId,
      downloading,
      uploading,
      uploadedPDF,
      pdfFileInput,
      downloadPDFReport,
      triggerUploadPDF,
      handlePDFUpload,
      openSignaturePage,
      // 上传进度相关
      showUploadProgress,
      uploadProgress,
      uploadSuccess,
      uploadError,
      closeUploadProgressModal,
      closeUploadProgressAndOpenSignature
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

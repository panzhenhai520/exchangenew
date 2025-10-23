<template>
  <div class="dynamic-form-improved">
    <div v-if="loading" class="loading-container">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">{{ $t('common.loading') }}</span>
      </div>
      <p class="mt-2 text-muted">{{ $t('amlo.form.loadingForm') }}</p>
    </div>

    <div v-else>
      <!-- 打印按钮 -->
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h5 class="mb-0">{{ $t('amlo.form.fillReport') }}</h5>
        <button type="button" class="btn btn-outline-primary btn-sm" @click="printBlankPDF">
          <font-awesome-icon :icon="['fas', 'print']" class="me-1" />
          {{ printButtonText }}
        </button>
      </div>

      <!-- 字段分组（可折叠） -->
      <div class="accordion" id="fieldGroups">
        <div
          v-for="(group, groupIndex) in fieldGroups"
          :key="groupIndex"
          class="accordion-item"
        >
          <h2 class="accordion-header" :id="'heading' + groupIndex">
            <button
              class="accordion-button"
              :class="{ collapsed: !group.expanded }"
              type="button"
              @click="toggleGroup(groupIndex)"
            >
              <font-awesome-icon :icon="['fas', 'folder-open']" class="me-2" v-if="group.expanded" />
              <font-awesome-icon :icon="['fas', 'folder']" class="me-2" v-else />
              {{ group.group_name }}
              <span class="badge bg-secondary ms-2">{{ group.fields.length }} {{ $t('common.fields') }}</span>
            </button>
          </h2>
          <div
            :id="'collapse' + groupIndex"
            class="accordion-collapse collapse"
            :class="{ show: group.expanded }"
            :aria-labelledby="'heading' + groupIndex"
          >
            <div class="accordion-body">
              <!-- 表单字段 -->
              <div class="row">
                <div
                  v-for="field in group.fields"
                  :key="field.id"
                  :class="getFieldColumnClass(field)"
                >
                  <FormField
                    :field="field"
                    :value="formData[field.field_name]"
                    :errors="fieldErrors[field.field_name]"
                    @update:value="handleFieldUpdate(field.field_name, $event)"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 提交按钮 -->
      <div class="mt-4 d-flex justify-content-end gap-2">
        <button type="button" class="btn btn-secondary" @click="handleReset">
          <font-awesome-icon :icon="['fas', 'undo']" class="me-1" />
          {{ $t('common.reset') }}
        </button>
        <button
          type="button"
          class="btn btn-primary"
          @click="handleSubmit"
          :disabled="submitting"
        >
          <span v-if="submitting" class="spinner-border spinner-border-sm me-2"></span>
          <font-awesome-icon v-else :icon="['fas', 'check']" class="me-1" />
          {{ submitting ? $t('common.submitting') : (submitButtonText || $t('common.submit')) }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import FormField from './FormField.vue'

export default {
  name: 'DynamicFormImproved',
  components: {
    FormField
  },
  props: {
    reportType: {
      type: String,
      required: true
    },
    initialData: {
      type: Object,
      default: () => ({})
    },
    submitButtonText: {
      type: String,
      default: ''
    },
    showCheckTrigger: {
      type: Boolean,
      default: false
    }
  },
  emits: ['submit', 'update:formData'],
  setup(props, { emit }) {
    const { t, locale } = useI18n()

    // 状态
    const loading = ref(false)
    const submitting = ref(false)
    const fieldGroups = ref([])
    const formData = ref({})
    const fieldErrors = ref({})

    // 计算当前语言代码
    const currentLanguage = computed(() => {
      const localeValue = locale.value
      const langMap = { 'zh-CN': 'zh', 'en-US': 'en', 'th-TH': 'th' }
      return langMap[localeValue] || 'zh'
    })

    // 计算打印按钮文本（根据报告类型动态显示）
    const printButtonText = computed(() => {
      const reportTypeNames = {
        'AMLO-1-01': 'CTR AMLO-1-01',
        'AMLO-1-02': 'ATR AMLO-1-02',
        'AMLO-1-03': 'STR AMLO-1-03',
        'BOT_BuyFX': 'BOT Buy FX',
        'BOT_SellFX': 'BOT Sell FX',
        'BOT_FCD': 'BOT FCD',
        'BOT_Provider': 'BOT Provider'
      }

      const reportName = reportTypeNames[props.reportType] || props.reportType
      return `${t('amlo.form.print')} ${reportName}`
    })

    // 获取字段列宽类
    const getFieldColumnClass = (field) => {
      const fieldType = field.field_type

      // 根据字段类型决定占用宽度
      if (fieldType === 'textarea' || fieldType === 'TEXT') {
        return 'col-12' // 文本域占满整行
      }

      // checkbox字段可以更窄
      if (fieldType === 'BOOLEAN' || fieldType === 'checkbox') {
        return 'col-12 col-md-4 col-lg-3' // checkbox占更少空间
      }

      // 使用响应式列宽：大屏幕3列，中等屏幕2列，小屏幕1列
      return 'col-12 col-md-6 col-lg-4' // 响应式：lg及以上3列，md 2列，sm 1列
    }

    // 加载表单定义
    const loadFormDefinition = async () => {
      loading.value = true
      try {
        const response = await fetch(`/api/repform/form-definition/${props.reportType}?language=${currentLanguage.value}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        })

        const result = await response.json()

        if (result.success) {
          // 处理字段分组
          if (result.data.field_groups && result.data.field_groups.length > 0) {
            fieldGroups.value = result.data.field_groups.map((group, index) => ({
              ...group,
              expanded: index === 0 // 默认展开第一组
            }))
          } else {
            // 如果没有分组，创建一个默认分组
            fieldGroups.value = [{
              group_name: t('common.formFields'),
              fields: result.data.fields || [],
              expanded: true
            }]
          }

          // 初始化表单数据，并自动填充已知字段
          await initializeFormData()
        } else {
          console.error('加载表单定义失败:', result.message)
        }
      } catch (error) {
        console.error('加载表单定义异常:', error)
      } finally {
        loading.value = false
      }
    }

    // 生成AMLO报告编号
    const generateReportNumber = async () => {
      try {
        // 获取用户信息
        const userInfo = localStorage.getItem('user')
        if (!userInfo) {
          console.warn('[DynamicFormImproved] 未找到用户信息，无法生成报告编号')
          return null
        }
        
        const user = JSON.parse(userInfo)
        const branchId = user?.branch?.id || user?.branch_id || 1
        
        // 获取币种代码 - 从表单数据中获取，如果没有则使用默认值
        let currencyCode = 'USD' // 默认币种
        if (props.initialData && props.initialData.deposit_currency_code) {
          currencyCode = props.initialData.deposit_currency_code
        } else if (props.initialData && props.initialData.withdrawal_currency_code) {
          currencyCode = props.initialData.withdrawal_currency_code
        }
        
        console.log('[DynamicFormImproved] 生成报告编号参数:', {
          branchId,
          currencyCode,
          reportType: props.reportType
        })

        // 使用统一的api服务而不是直接使用fetch
        const api = (await import('../../../services/api')).default
        
        const response = await api.post('/report-numbers/amlo/generate', {
          branch_id: branchId,
          currency_code: currencyCode,
          transaction_id: props.initialData?.transaction_id || null
        })
        
        if (response.data.success) {
          console.log('[DynamicFormImproved] 报告编号生成成功:', response.data.data.report_number)
          return response.data.data.report_number
        } else {
          console.error('[DynamicFormImproved] 报告编号生成失败:', response.data.message)
          return null
        }
      } catch (error) {
        console.error('[DynamicFormImproved] 报告编号生成异常:', error)
        return null
      }
    }

    // 初始化表单数据（包含自动填充）- 改进版
    const initializeFormData = async () => {
      console.log('[DynamicFormImproved] ===== 开始初始化表单数据 =====')
      console.log('[DynamicFormImproved] reportType:', props.reportType)
      console.log('[DynamicFormImproved] initialData:', JSON.stringify(props.initialData, null, 2))
      console.log('[DynamicFormImproved] fieldGroups数量:', fieldGroups.value.length)

      const data = {}
      let filledCount = 0
      let totalCount = 0
      
      // 生成报告编号
      const generatedReportNumber = await generateReportNumber()
      if (generatedReportNumber) {
        data.report_number = generatedReportNumber
        filledCount++
        console.log(`[DynamicFormImproved] 📋 report_number = ${generatedReportNumber} (自动生成)`)
      }

      // 遍历所有字段分组
      fieldGroups.value.forEach((group, groupIndex) => {
        console.log(`[DynamicFormImproved] 处理分组 ${groupIndex}: ${group.group_name}, 字段数: ${group.fields.length}`)

        group.fields.forEach(field => {
          const fieldName = field.field_name
          const fieldType = field.field_type
          totalCount++

          // 优先使用initialData中的值（如果已明确提供）
          // 修复：不再排除空字符串和0，只检查undefined和null
          if (props.initialData && props.initialData[fieldName] !== undefined && props.initialData[fieldName] !== null) {
            data[fieldName] = props.initialData[fieldName]
            filledCount++
            console.log(`[DynamicFormImproved] ✅ ${fieldName} = ${JSON.stringify(props.initialData[fieldName])} (来自initialData)`)
          }
          // BOOLEAN/checkbox类型特殊处理 - 默认false，除非initialData明确指定
          else if (fieldType === 'BOOLEAN' || fieldType === 'checkbox') {
            // 只有initialData明确设置为true时才为true
            data[fieldName] = props.initialData?.[fieldName] === true ? true : false
            console.log(`[DynamicFormImproved] ⬜ ${fieldName} = ${data[fieldName]} (boolean默认值)`)
          }
          // 日期字段自动填充当前日期
          else if ((fieldType === 'DATE' || fieldType === 'DATETIME') && !field.default_value) {
            data[fieldName] = new Date().toISOString().split('T')[0]
            filledCount++
            console.log(`[DynamicFormImproved] 📅 ${fieldName} = ${data[fieldName]} (自动当前日期)`)
          }
          // 如果数据库有默认值，使用默认值
          else if (field.default_value) {
            data[fieldName] = field.default_value
            console.log(`[DynamicFormImproved] 🔧 ${fieldName} = ${field.default_value} (数据库默认值)`)
          }
          // 数字类型默认0
          else if (fieldType === 'INT' || fieldType === 'DECIMAL') {
            // 为生日字段提供合理的默认值
            if (fieldName.includes('birthdate_day')) {
              data[fieldName] = 1
            } else if (fieldName.includes('birthdate_month')) {
              data[fieldName] = 1
            } else if (fieldName.includes('birthdate_year')) {
              data[fieldName] = 1990
            } else {
              data[fieldName] = 0
            }
            console.log(`[DynamicFormImproved] 🔢 ${fieldName} = ${data[fieldName]} (数字默认值)`)
          }
          // 其他类型默认空字符串
          else {
            data[fieldName] = ''
            console.log(`[DynamicFormImproved] 📝 ${fieldName} = '' (空字符串默认值)`)
          }
        })
      })

      formData.value = data
      console.log(`[DynamicFormImproved] ===== 表单初始化完成 =====`)
      console.log(`[DynamicFormImproved] 总字段数: ${totalCount}, 已填充: ${filledCount}`)
      console.log(`[DynamicFormImproved] 最终formData:`, JSON.stringify(formData.value, null, 2))
    }

    // 切换分组展开/折叠
    const toggleGroup = (groupIndex) => {
      fieldGroups.value[groupIndex].expanded = !fieldGroups.value[groupIndex].expanded
    }

    // 字段更新
    const handleFieldUpdate = (fieldName, value) => {
      formData.value[fieldName] = value
      // 清除该字段的错误
      if (fieldErrors.value[fieldName]) {
        delete fieldErrors.value[fieldName]
      }
      // 发送更新事件
      emit('update:formData', formData.value)
    }

    // 表单提交
    const handleSubmit = async () => {
      // 简单验证
      const errors = {}
      let hasError = false

      fieldGroups.value.forEach(group => {
        group.fields.forEach(field => {
          if (field.is_required) {
            const value = formData.value[field.field_name]
            if (!value || (typeof value === 'string' && value.trim() === '')) {
              errors[field.field_name] = [t('common.fieldRequired')]
              hasError = true
            }
          }
        })
      })

      if (hasError) {
        fieldErrors.value = errors
        alert(t('amlo.form.validationFailed'))
        return
      }

      // 清空错误
      fieldErrors.value = {}
      submitting.value = true

      try {
        emit('submit', formData.value)
      } finally {
        submitting.value = false
      }
    }

    // 重置表单
    const handleReset = async () => {
      await initializeFormData()
      fieldErrors.value = {}
    }

    // 打印空白PDF模板 - 改进版支持下载
    const printBlankPDF = () => {
      const pdfMap = {
        'AMLO-1-01': 'รายงาน ปปง 1-01 ซื้อขายเกิน 500,000 บาท ยกเว้นเงินบาทแลก.pdf',
        'AMLO-1-02': 'รายงาน ปปง 1-02 ซื้อขายเกิน 800,000 บาท ยกเว้นเงินบาทแลก.pdf',
        'AMLO-1-03': 'รายงาน ปปง 1-03  ซื้อขายระหว่างนิติบุคลล.pdf'
      }

      const pdfFileName = pdfMap[props.reportType]
      if (pdfFileName) {
        // 构建PDF URL
        const pdfUrl = `/api/amlo/blank-form/${props.reportType}`

        // 使用fetch下载并打开
        fetch(pdfUrl, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        })
        .then(response => {
          if (!response.ok) {
            throw new Error('PDF文件获取失败')
          }
          return response.blob()
        })
        .then(blob => {
          // 创建blob URL
          const blobUrl = window.URL.createObjectURL(blob)

          // 打开新窗口显示PDF
          window.open(blobUrl, '_blank')

          // 同时触发下载（可选）
          const link = document.createElement('a')
          link.href = blobUrl
          link.download = pdfFileName
          document.body.appendChild(link)
          link.click()
          document.body.removeChild(link)

          // 清理blob URL
          setTimeout(() => {
            window.URL.revokeObjectURL(blobUrl)
          }, 100)
        })
        .catch(error => {
          console.error('打印PDF失败:', error)
          alert(t('amlo.form.pdfNotFound') + ': ' + error.message)
        })
      } else {
        alert(t('amlo.form.pdfNotFound'))
      }
    }

    // 监听报告类型变化
    watch(() => props.reportType, () => {
      loadFormDefinition()
    })

    // 监听initialData变化
    watch(() => props.initialData, async (newVal, oldVal) => {
      console.log('[DynamicFormImproved] ===== initialData变化监听触发 =====')
      console.log('[DynamicFormImproved] oldVal:', JSON.stringify(oldVal, null, 2))
      console.log('[DynamicFormImproved] newVal:', JSON.stringify(newVal, null, 2))
      console.log('[DynamicFormImproved] fieldGroups.value.length:', fieldGroups.value.length)

      if (fieldGroups.value.length > 0) {
        console.log('[DynamicFormImproved] 触发重新初始化表单数据')
        await initializeFormData()
      } else {
        console.warn('[DynamicFormImproved] fieldGroups为空，跳过初始化')
      }
    }, { deep: true, immediate: false })

    // 组件挂载
    onMounted(() => {
      loadFormDefinition()
    })

    // 暴露submitForm方法供父组件调用
    const submitForm = () => {
      return handleSubmit()
    }

    return {
      loading,
      submitting,
      fieldGroups,
      formData,
      fieldErrors,
      printButtonText,
      getFieldColumnClass,
      toggleGroup,
      handleFieldUpdate,
      handleSubmit,
      handleReset,
      printBlankPDF,
      submitForm
    }
  }
}
</script>

<style scoped>
.dynamic-form-improved {
  padding: 20px;
  background: #fff;
  border-radius: 8px;
}

.loading-container {
  text-align: center;
  padding: 40px 20px;
}

.accordion-item {
  margin-bottom: 16px;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  overflow: hidden;
}

.accordion-button {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  color: #495057;
  font-weight: 600;
  padding: 12px 20px;
  border: none;
}

.accordion-button:not(.collapsed) {
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
  color: #1976d2;
  box-shadow: none;
}

.accordion-button:hover {
  background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%);
}

.accordion-button:focus {
  box-shadow: none;
  border-color: #dee2e6;
}

.accordion-body {
  padding: 20px;
  background: #fafafa;
}

.accordion-body .row {
  margin: 0 -8px;
}

.accordion-body .row > div {
  padding: 0 8px;
  margin-bottom: 16px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .dynamic-form-improved {
    padding: 12px;
  }

  .accordion-button {
    font-size: 0.9rem;
    padding: 10px 15px;
  }

  .accordion-body {
    padding: 15px;
  }

  .accordion-body .row > div {
    margin-bottom: 12px;
  }
}
</style>

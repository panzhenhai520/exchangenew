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
                <template v-for="field in group.fields" :key="field.id">
                  <!-- 特殊处理: 交易者类型字段 - 合并显示为单选组 -->
                  <div
                    v-if="field.field_name === 'maker_type_person'"
                    class="col-12 col-md-6 col-lg-4"
                  >
                    <a-form-item
                      :label="$t('amlo.form.transactorType.label')"
                      :required="field.is_required"
                    >
                      <a-radio-group
                        :value="formData.maker_type_person ? 'person' : 'juristic'"
                        @change="handleTransactorTypeChange"
                      >
                        <a-radio value="person">
                          {{ $t('amlo.form.transactorType.person') }}
                        </a-radio>
                        <a-radio value="juristic">
                          {{ $t('amlo.form.transactorType.juristic') }}
                        </a-radio>
                      </a-radio-group>
                    </a-form-item>
                  </div>

                  <!-- 跳过maker_type_juristic字段,因为已在上面合并显示 -->
                  <div
                    v-else-if="field.field_name !== 'maker_type_juristic'"
                    :class="getFieldColumnClass(field)"
                  >
                    <FormField
                      :field="field"
                      :value="formData[field.field_name]"
                      :errors="fieldErrors[field.field_name]"
                      @update:value="handleFieldUpdate(field.field_name, $event)"
                    />
                  </div>
                </template>
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
import {
  normalizeFieldDefinition,
  normalizeFieldGroup,
  readValidationRules,
  resolveFieldLabel
} from './fieldHelpers.js'
import repformService from '@/services/api/repformService'

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
  emits: ['submit', 'update:formData', 'view-pdf'],
  setup(props, { emit }) {
    const { t, locale } = useI18n()
    const HIDDEN_FIELDS = new Set(['maker_lastname'])

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

    // 打印按钮文本 - 统一显示"填写AMLO报告"
    const printButtonText = computed(() => {
      return t('amlo.form.fillReport') || '填写AMLO报告'
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
        const result = await repformService.getFormDefinition(props.reportType, currentLanguage.value)
          .then(res => res.data)
          .catch(error => {
            console.error('[DynamicFormImproved] 获取表单定义失败:', error)
            throw error
          })

        if (result?.success) {
          // 处理字段分组
          if (result.data.field_groups && result.data.field_groups.length > 0) {
            fieldGroups.value = result.data.field_groups.map((group, index) => {
              const normalized = normalizeFieldGroup(group)
              normalized.fields = (normalized.fields || []).filter(
                (field) => !HIDDEN_FIELDS.has(field.field_name)
              )
              return {
                ...normalized,
                expanded: index === 0 // 默认展开第一个
              }
            })
          } else {
            const fallbackFields = (result.data.fields || [])
              .map(normalizeFieldDefinition)
              .filter((field) => !HIDDEN_FIELDS.has(field.field_name))
            // 如果没有分组，创建一个默认分组
            fieldGroups.value = [{
              group_name: t('common.formFields'),
              fields: fallbackFields,
              expanded: true
            }]
          }

          // 初始化表单数据，并自动填充已知字段
          await initializeFormData()
        } else {
          console.error('[DynamicFormImproved] 表单定义响应异常:', result)
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
          console.warn('[DynamicFormImproved] ⚠️ 报告编号将由后端在提交时自动生成')
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
        } else if (props.initialData && props.initialData.currency_code) {
          currencyCode = props.initialData.currency_code
        }

        console.log('[DynamicFormImproved] 生成报告编号参数:', {
          branchId,
          currencyCode,
          reportType: props.reportType,
          initialData: props.initialData
        })

        // 使用统一的api服务而不是直接使用fetch
        const api = (await import('../../../services/api')).default

        const response = await api.post('/report-numbers/amlo/generate', {
          branch_id: branchId,
          currency_code: currencyCode,
          transaction_id: props.initialData?.transaction_id || null
        })

        if (response.data.success) {
          console.log('[DynamicFormImproved] ✅ 报告编号生成成功:', response.data.data.report_number)
          return response.data.data.report_number
        } else {
          console.error('[DynamicFormImproved] ❌ 报告编号生成失败:', response.data.message)
          console.warn('[DynamicFormImproved] ⚠️ 报告编号将由后端在提交时自动生成')
          return null
        }
      } catch (error) {
        console.error('[DynamicFormImproved] ❌ 报告编号生成异常:', error)
        console.error('[DynamicFormImproved] 错误详情:', error.response?.data || error.message)

        // 如果是权限错误，给出明确提示
        if (error.response?.status === 403) {
          console.warn('[DynamicFormImproved] ⚠️ 权限不足: 需要amlo_report_generate权限')
          console.warn('[DynamicFormImproved] ⚠️ 报告编号将由后端在提交时自动生成')
        } else if (error.response?.status === 401) {
          console.warn('[DynamicFormImproved] ⚠️ 未登录或登录已过期')
        } else {
          console.warn('[DynamicFormImproved] ⚠️ 报告编号将由后端在提交时自动生成')
        }

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
          const rules = readValidationRules(field)
          totalCount++

          // 🔥 特殊处理：如果是report_number字段且已经自动生成，不要被initialData覆盖
          if (fieldName === 'report_number' && data.report_number) {
            console.log(`[DynamicFormImproved] 🔒 report_number = ${data.report_number} (保留自动生成的值，不被initialData覆盖)`)
            return
          }

          // 优先使用initialData中的值（如果已明确提供）
          // 修复：不再排除空字符串和0，只检查undefined和null
          if (props.initialData && Object.prototype.hasOwnProperty.call(props.initialData, fieldName) &&
            props.initialData[fieldName] !== null && props.initialData[fieldName] !== undefined) {
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
            const defaultDateInput = rules.default_value || new Date().toISOString()
            let defaultDate = new Date(defaultDateInput)
            if (Number.isNaN(defaultDate.getTime())) {
              defaultDate = new Date()
            }
            data[fieldName] = defaultDate.toISOString().split('T')[0]
            filledCount++
            console.log(`[DynamicFormImproved] 📅 ${fieldName} = ${data[fieldName]} (自动当前日期)`)
          }
          // 如果数据库有默认值，使用默认值
          else if (field.default_value) {
            data[fieldName] = field.default_value
            console.log(`[DynamicFormImproved] 🔧 ${fieldName} = ${field.default_value} (数据库默认值)`)
          }
          else if (rules.default_value !== undefined) {
            data[fieldName] = rules.default_value
            console.log(`[DynamicFormImproved] 🔧 ${fieldName} = ${rules.default_value} (规则默认值)`)
          }
          // 数字类型默认0
          else if (fieldType === 'INT' || fieldType === 'DECIMAL' || fieldType === 'NUMBER') {
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
          else if (fieldType === 'ENUM') {
            data[fieldName] = rules.multiple ? [] : ''
            console.log(`[DynamicFormImproved] 🔽 ${fieldName} = ${JSON.stringify(data[fieldName])} (枚举默认值)`)
          }
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

    // 处理交易者类型变更 (互斥选择)
    const handleTransactorTypeChange = (e) => {
      const value = e.target.value
      if (value === 'person') {
        // 选择个人
        formData.value.maker_type_person = true
        formData.value.maker_type_juristic = false
        console.log('[DynamicFormImproved] 交易者类型: 个人')
      } else if (value === 'juristic') {
        // 选择法人
        formData.value.maker_type_person = false
        formData.value.maker_type_juristic = true
        console.log('[DynamicFormImproved] 交易者类型: 法人')
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
            const isEmptyString = typeof value === 'string' && value.trim() === ''
            const isEmptyArray = Array.isArray(value) && value.length === 0
            const isEmpty =
              value === null ||
              value === undefined ||
              value === '' ||
              isEmptyString ||
              isEmptyArray

            if (isEmpty) {
              const label = resolveFieldLabel(field) || field.field_name
              errors[field.field_name] = [`${label} ${t('common.fieldRequired')}`]
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

    // 查看已填写的PDF报告 - 在笔屏全屏显示
    const printBlankPDF = () => {
      console.log('[DynamicFormImproved] 触发view-pdf事件')
      // 触发父组件的PDF查看事件，传递当前表单数据
      emit('view-pdf', {
        reportType: props.reportType,
        formData: formData.value,
        initialData: props.initialData
      })
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
      handleTransactorTypeChange, // 新增: 交易者类型变更处理
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

<template>
  <div class="dynamic-form">
    <a-spin :spinning="loading">
      <a-form
        :model="formData"
        :label-col="labelCol"
        :wrapper-col="wrapperCol"
        @finish="handleSubmit"
      >
        <!-- 表单字段动态渲染 -->
        <FormField
          v-for="field in formFields"
          :key="field.field_id"
          :field="field"
          :value="formData[field.field_name]"
          :errors="fieldErrors[field.field_name]"
          @update:value="handleFieldUpdate(field.field_name, $event)"
        />

        <!-- 提交按钮 -->
        <a-form-item :wrapper-col="{ offset: labelCol.span, span: wrapperCol.span }">
          <a-space>
            <a-button type="primary" html-type="submit" :loading="submitting">
              {{ submitButtonText }}
            </a-button>
            <a-button @click="handleReset">
              {{ $t('common.reset') }}
            </a-button>
            <a-button v-if="showCheckTrigger" @click="handleCheckTrigger" :loading="checkingTrigger">
              {{ $t('amlo.form.checkTrigger') }}
            </a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-spin>

    <!-- 触发条件检查结果弹窗 -->
    <a-modal
      v-model:visible="triggerResultVisible"
      :title="$t('amlo.form.triggerResult')"
      :footer="null"
      width="600px"
    >
      <div v-if="triggerResult">
        <a-alert
          :type="triggerResult.is_triggered ? 'warning' : 'success'"
          :message="triggerResult.is_triggered ? $t('amlo.form.triggered') : $t('amlo.form.notTriggered')"
          show-icon
          style="margin-bottom: 16px"
        />

        <div v-if="triggerResult.is_triggered && triggerResult.matched_rules.length > 0">
          <h4>{{ $t('amlo.form.matchedRules') }}</h4>
          <a-list
            :data-source="triggerResult.matched_rules"
            size="small"
          >
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta>
                  <template #title>
                    {{ item.rule_name }}
                  </template>
                  <template #description>
                    {{ item.description }}
                  </template>
                </a-list-item-meta>
              </a-list-item>
            </template>
          </a-list>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import { useAMLOStore } from '@/stores/amlo'
import FormField from './FormField.vue'
import { validateForm } from './FormValidation.js'
import { buildFormData, resetFormData } from './FormUtils.js'
import { normalizeFieldDefinition } from './fieldHelpers.js'

export default {
  name: 'DynamicForm',
  components: {
    FormField
  },
  props: {
    reportType: {
      type: String,
      required: true,
      validator: (value) => ['AMLO-1-01', 'AMLO-1-02', 'AMLO-1-03'].includes(value)
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
      default: true
    },
    labelCol: {
      type: Object,
      default: () => ({ span: 6 })
    },
    wrapperCol: {
      type: Object,
      default: () => ({ span: 16 })
    }
  },
  emits: ['submit', 'update:formData'],
  setup(props, { emit }) {
    const { t } = useI18n()
    const amloStore = useAMLOStore()

    // 状态
    const loading = ref(false)
    const submitting = ref(false)
    const checkingTrigger = ref(false)
    const formFields = ref([])
    const formData = ref({})
    const fieldErrors = ref({})
    const triggerResultVisible = ref(false)
    const triggerResult = ref(null)

    // 计算属性
    const currentLanguage = computed(() => {
      // 根据i18n当前语言返回对应的语言代码
      const locale = t('locale')
      const langMap = { 'zh-CN': 'zh', 'en-US': 'en', 'th-TH': 'th' }
      return langMap[locale] || 'zh'
    })

    // 加载表单定义
    const loadFormDefinition = async () => {
      loading.value = true
      try {
        const response = await amloStore.fetchFormDefinition(props.reportType, currentLanguage.value)
        if (response.success) {
          const normalizedFields = (response.data.fields || []).map(normalizeFieldDefinition)
          formFields.value = normalizedFields
          // 初始化表单数据
          formData.value = buildFormData(normalizedFields, props.initialData)
        } else {
          message.error(response.message || t('amlo.form.loadFailed'))
        }
      } catch (error) {
        console.error('加载表单定义失败:', error)
        message.error(t('amlo.form.loadError'))
      } finally {
        loading.value = false
      }
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
      // 验证表单
      const validation = validateForm(formData.value, formFields.value)
      if (!validation.valid) {
        fieldErrors.value = validation.errors
        message.error(t('amlo.form.validationFailed'))
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
    const handleReset = () => {
      formData.value = resetFormData(formFields.value)
      fieldErrors.value = {}
    }

    // 检查触发条件
    const handleCheckTrigger = async () => {
      checkingTrigger.value = true
      try {
        const response = await amloStore.checkTrigger(props.reportType, formData.value)
        if (response.success) {
          triggerResult.value = response.data
          triggerResultVisible.value = true
        } else {
          message.error(response.message || t('amlo.form.checkTriggerFailed'))
        }
      } catch (error) {
        console.error('检查触发条件失败:', error)
        message.error(t('amlo.form.checkTriggerError'))
      } finally {
        checkingTrigger.value = false
      }
    }

    // 监听报告类型变化
    watch(() => props.reportType, () => {
      loadFormDefinition()
    })

    // 组件挂载
    onMounted(() => {
      loadFormDefinition()
    })

    return {
      loading,
      submitting,
      checkingTrigger,
      formFields,
      formData,
      fieldErrors,
      triggerResultVisible,
      triggerResult,
      handleFieldUpdate,
      handleSubmit,
      handleReset,
      handleCheckTrigger
    }
  }
}
</script>

<style scoped>
.dynamic-form {
  padding: 24px;
  background: #fff;
  border-radius: 4px;
}
</style>

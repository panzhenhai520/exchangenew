<template>
  <a-form-item
    :label="fieldLabel"
    :name="field.field_name"
    :required="isRequired"
    :validate-status="hasError ? 'error' : ''"
    :help="errorMessage"
  >
    <component
      :is="fieldComponent"
      :field="field"
      :value="value"
      @update:value="handleUpdate"
    />
  </a-form-item>
</template>

<script>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import TextField from './FieldTypes/TextField.vue'
import NumberField from './FieldTypes/NumberField.vue'
import DateField from './FieldTypes/DateField.vue'
import SelectField from './FieldTypes/SelectField.vue'
import CheckboxField from './FieldTypes/CheckboxField.vue'
import TextareaField from './FieldTypes/TextareaField.vue'

export default {
  name: 'FormField',
  components: {
    TextField,
    NumberField,
    DateField,
    SelectField,
    CheckboxField,
    TextareaField
  },
  props: {
    field: {
      type: Object,
      required: true
    },
    value: {
      type: [String, Number, Boolean, Array, Object],
      default: null
    },
    errors: {
      type: Array,
      default: () => []
    }
  },
  emits: ['update:value'],
  setup(props, { emit }) {
    const { t } = useI18n()

    // 字段标签
    const fieldLabel = computed(() => {
      return props.field.field_label || props.field.field_name
    })

    // 是否必填
    const isRequired = computed(() => {
      return props.field.is_required || false
    })

    // 是否有错误
    const hasError = computed(() => {
      return props.errors && props.errors.length > 0
    })

    // 错误消息
    const errorMessage = computed(() => {
      if (hasError.value) {
        return props.errors.join(', ')
      }
      return ''
    })

    // 字段组件映射
    const fieldComponent = computed(() => {
      const typeMap = {
        'text': 'TextField',
        'number': 'NumberField',
        'date': 'DateField',
        'select': 'SelectField',
        'checkbox': 'CheckboxField',
        'textarea': 'TextareaField'
      }
      return typeMap[props.field.field_type] || 'TextField'
    })

    // 处理值更新
    const handleUpdate = (newValue) => {
      emit('update:value', newValue)
    }

    return {
      fieldLabel,
      isRequired,
      hasError,
      errorMessage,
      fieldComponent,
      handleUpdate
    }
  }
}
</script>

<style scoped>
/* FormField样式 */
</style>

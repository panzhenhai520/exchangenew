<template>
  <a-select
    :value="value"
    :placeholder="placeholder"
    :disabled="field.is_readonly"
    :mode="isMultiple ? 'multiple' : undefined"
    :options="selectOptions"
    style="width: 100%"
    @update:value="handleChange"
  />
</template>

<script>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { readValidationRules, resolveFieldLabel } from '../fieldHelpers.js'

export default {
  name: 'SelectField',
  props: {
    field: {
      type: Object,
      required: true
    },
    value: {
      type: [String, Array],
      default: null
    }
  },
  emits: ['update:value'],
  setup(props, { emit }) {
    const { locale } = useI18n()

    const rules = computed(() => readValidationRules(props.field))

    const placeholder = computed(() => {
      return props.field.placeholder || resolveFieldLabel(props.field)
    })

    const isMultiple = computed(() => {
      return rules.value.multiple === true
    })

    const currentLocale = computed(() => locale.value || 'zh-CN')

    const selectOptions = computed(() => {
      const currentRules = rules.value

      const normalizeOption = (option) => {
        if (typeof option === 'string') {
          return { label: option, value: option }
        }
        if (
          option &&
          typeof option === 'object' &&
          option.value !== undefined
        ) {
          return {
            value: option.value,
            label: resolveOptionLabel(option)
          }
        }
        return null
      }

      if (Array.isArray(currentRules.options) && currentRules.options.length > 0) {
        return currentRules.options
          .map(normalizeOption)
          .filter(option => option !== null)
      }

      if (Array.isArray(currentRules.enum_values)) {
        return currentRules.enum_values
          .map(normalizeOption)
          .filter(option => option !== null)
      }

      if (Array.isArray(currentRules.choices)) {
        return currentRules.choices
          .map(normalizeOption)
          .filter(option => option !== null)
      }

      return []
    })

    const resolveOptionLabel = (option) => {
      const localeKey = currentLocale.value
      const localeMap = {
        'zh-CN': ['label_zh', 'label_cn', 'label'],
        'zh': ['label_zh', 'label_cn', 'label'],
        'en-US': ['label_en', 'label'],
        'en': ['label_en', 'label'],
        'th-TH': ['label_th', 'label'],
        'th': ['label_th', 'label']
      }

      if (option.labels && typeof option.labels === 'object') {
        const nested = option.labels[localeKey] || option.labels[localeKey.split('-')[0]] || option.labels.default
        if (nested) {
          return nested
        }
      }

      const keys = localeMap[localeKey] || ['label']
      for (const key of keys) {
        if (option[key]) {
          return option[key]
        }
      }
      return option.label || option.value
    }

    const handleChange = (newValue) => {
      emit('update:value', newValue)
    }

    return {
      isMultiple,
      selectOptions,
      placeholder,
      handleChange
    }
  }
}
</script>

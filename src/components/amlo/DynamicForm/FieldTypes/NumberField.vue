<template>
  <a-input-number
    :value="value"
    :placeholder="placeholder"
    :min="minValue"
    :max="maxValue"
    :precision="precision"
    :disabled="field.is_readonly"
    style="width: 100%"
    @update:value="handleChange"
  />
</template>

<script>
import { computed } from 'vue'
import { readValidationRules, resolveFieldLabel } from '../fieldHelpers.js'

export default {
  name: 'NumberField',
  props: {
    field: {
      type: Object,
      required: true
    },
    value: {
      type: Number,
      default: null
    }
  },
  emits: ['update:value'],
  setup(props, { emit }) {
    const rules = computed(() => readValidationRules(props.field))

    const placeholder = computed(() => {
      return props.field.placeholder || resolveFieldLabel(props.field)
    })

    const minValue = computed(() => {
      const currentRules = rules.value
      if (currentRules.min_value !== undefined) {
        return currentRules.min_value
      }
      return props.field.min_value !== undefined ? props.field.min_value : undefined
    })

    const maxValue = computed(() => {
      const currentRules = rules.value
      if (currentRules.max_value !== undefined) {
        return currentRules.max_value
      }
      return props.field.max_value !== undefined ? props.field.max_value : undefined
    })

    const precision = computed(() => {
      const fieldType = (props.field.field_type || '').toUpperCase()
      if (fieldType === 'INT') {
        return 0
      }
      const currentRules = rules.value
      if (currentRules.precision !== undefined) {
        return currentRules.precision
      }
      if (props.field.field_scale !== undefined) {
        return props.field.field_scale
      }
      return 2
    })

    const handleChange = (newValue) => {
      emit('update:value', newValue)
    }

    return {
      minValue,
      maxValue,
      precision,
      placeholder,
      handleChange
    }
  }
}
</script>

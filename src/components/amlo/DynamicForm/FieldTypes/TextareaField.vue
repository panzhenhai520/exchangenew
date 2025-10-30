<template>
  <a-textarea
    :value="value"
    :placeholder="placeholder"
    :maxlength="maxLength"
    :rows="rows"
    :disabled="field.is_readonly"
    :show-count="true"
    @update:value="handleChange"
  />
</template>

<script>
import { computed } from 'vue'
import { readValidationRules, resolveFieldLabel } from '../fieldHelpers.js'

export default {
  name: 'TextareaField',
  props: {
    field: {
      type: Object,
      required: true
    },
    value: {
      type: String,
      default: ''
    }
  },
  emits: ['update:value'],
  setup(props, { emit }) {
    const rules = computed(() => readValidationRules(props.field))

    const placeholder = computed(() => {
      return props.field.placeholder || resolveFieldLabel(props.field)
    })

    const maxLength = computed(() => {
      const currentRules = rules.value
      if (currentRules.max_length) {
        return currentRules.max_length
      }
      if (props.field.field_length) {
        return props.field.field_length
      }
      return 500
    })

    const rows = computed(() => {
      const currentRules = rules.value
      if (currentRules.rows) {
        return currentRules.rows
      }
      return 4
    })

    const handleChange = (newValue) => {
      emit('update:value', newValue)
    }

    return {
      maxLength,
      placeholder,
      rows,
      handleChange
    }
  }
}
</script>

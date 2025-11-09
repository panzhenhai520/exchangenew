<template>
  <a-input
    :value="value"
    :placeholder="placeholder"
    :maxlength="maxLength"
    :disabled="field.is_readonly"
    @update:value="handleChange"
  />
</template>

<script>
import { computed } from 'vue'
import { readValidationRules, resolveFieldLabel } from '../fieldHelpers.js'

export default {
  name: 'TextField',
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
      return undefined
    })

    const handleChange = (newValue) => {
      emit('update:value', newValue)
    }

    return {
      maxLength,
      placeholder,
      handleChange
    }
  }
}
</script>

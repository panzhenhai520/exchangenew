<template>
  <a-input
    :value="value"
    :placeholder="field.placeholder || field.field_label"
    :maxlength="maxLength"
    :disabled="field.is_readonly"
    @update:value="handleChange"
  />
</template>

<script>
import { computed } from 'vue'

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
    const maxLength = computed(() => {
      if (props.field.validation_rules) {
        try {
          const rules = JSON.parse(props.field.validation_rules)
          return rules.max_length || undefined
        } catch (e) {
          return undefined
        }
      }
      return undefined
    })

    const handleChange = (newValue) => {
      emit('update:value', newValue)
    }

    return {
      maxLength,
      handleChange
    }
  }
}
</script>

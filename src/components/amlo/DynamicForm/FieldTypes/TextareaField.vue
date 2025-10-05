<template>
  <a-textarea
    :value="value"
    :placeholder="field.placeholder || field.field_label"
    :maxlength="maxLength"
    :rows="rows"
    :disabled="field.is_readonly"
    :show-count="true"
    @update:value="handleChange"
  />
</template>

<script>
import { computed } from 'vue'

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
    const maxLength = computed(() => {
      if (props.field.validation_rules) {
        try {
          const rules = JSON.parse(props.field.validation_rules)
          return rules.max_length || 500
        } catch (e) {
          return 500
        }
      }
      return 500
    })

    const rows = computed(() => {
      if (props.field.validation_rules) {
        try {
          const rules = JSON.parse(props.field.validation_rules)
          return rules.rows || 4
        } catch (e) {
          return 4
        }
      }
      return 4
    })

    const handleChange = (newValue) => {
      emit('update:value', newValue)
    }

    return {
      maxLength,
      rows,
      handleChange
    }
  }
}
</script>

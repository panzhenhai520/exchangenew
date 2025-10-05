<template>
  <a-select
    :value="value"
    :placeholder="field.placeholder || field.field_label"
    :disabled="field.is_readonly"
    :mode="isMultiple ? 'multiple' : undefined"
    :options="selectOptions"
    style="width: 100%"
    @update:value="handleChange"
  />
</template>

<script>
import { computed } from 'vue'

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
    const isMultiple = computed(() => {
      if (props.field.validation_rules) {
        try {
          const rules = JSON.parse(props.field.validation_rules)
          return rules.multiple === true
        } catch (e) {
          return false
        }
      }
      return false
    })

    const selectOptions = computed(() => {
      if (props.field.validation_rules) {
        try {
          const rules = JSON.parse(props.field.validation_rules)
          if (rules.enum_values && Array.isArray(rules.enum_values)) {
            return rules.enum_values.map(item => ({
              label: item,
              value: item
            }))
          }
        } catch (e) {
          return []
        }
      }
      return []
    })

    const handleChange = (newValue) => {
      emit('update:value', newValue)
    }

    return {
      isMultiple,
      selectOptions,
      handleChange
    }
  }
}
</script>

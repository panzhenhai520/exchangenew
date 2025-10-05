<template>
  <a-input-number
    :value="value"
    :placeholder="field.placeholder || field.field_label"
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
    const minValue = computed(() => {
      if (props.field.validation_rules) {
        try {
          const rules = JSON.parse(props.field.validation_rules)
          return rules.min_value !== undefined ? rules.min_value : undefined
        } catch (e) {
          return undefined
        }
      }
      return undefined
    })

    const maxValue = computed(() => {
      if (props.field.validation_rules) {
        try {
          const rules = JSON.parse(props.field.validation_rules)
          return rules.max_value !== undefined ? rules.max_value : undefined
        } catch (e) {
          return undefined
        }
      }
      return undefined
    })

    const precision = computed(() => {
      if (props.field.validation_rules) {
        try {
          const rules = JSON.parse(props.field.validation_rules)
          return rules.precision !== undefined ? rules.precision : 2
        } catch (e) {
          return 2
        }
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
      handleChange
    }
  }
}
</script>

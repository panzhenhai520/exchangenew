<template>
  <a-checkbox
    :checked="value"
    :disabled="field.is_readonly"
    @update:checked="handleChange"
  >
    {{ checkboxLabel }}
  </a-checkbox>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'CheckboxField',
  props: {
    field: {
      type: Object,
      required: true
    },
    value: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:value'],
  setup(props, { emit }) {
    const checkboxLabel = computed(() => {
      return props.field.placeholder || ''
    })

    const handleChange = (checked) => {
      emit('update:value', checked)
    }

    return {
      checkboxLabel,
      handleChange
    }
  }
}
</script>

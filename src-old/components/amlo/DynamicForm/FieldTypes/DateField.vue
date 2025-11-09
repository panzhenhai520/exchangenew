<template>
  <a-date-picker
    :value="dateValue"
    :placeholder="placeholder"
    :disabled="field.is_readonly"
    :format="dateFormat"
    style="width: 100%"
    @update:value="handleChange"
  />
</template>

<script>
import { computed } from 'vue'
import dayjs from 'dayjs'
import { resolveFieldLabel } from '../fieldHelpers.js'

export default {
  name: 'DateField',
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
    const dateFormat = 'DD/MM/YYYY'

    const placeholder = computed(() => {
      return props.field.placeholder || resolveFieldLabel(props.field)
    })

    const dateValue = computed(() => {
      if (props.value) {
        return dayjs(props.value, dateFormat)
      }
      return null
    })

    const handleChange = (date) => {
      if (date) {
        emit('update:value', date.format(dateFormat))
      } else {
        emit('update:value', '')
      }
    }

    return {
      dateFormat,
      dateValue,
      placeholder,
      handleChange
    }
  }
}
</script>

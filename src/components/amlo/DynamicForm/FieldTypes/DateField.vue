<template>
  <a-date-picker
    :value="dateValue"
    :placeholder="field.placeholder || field.field_label"
    :disabled="field.is_readonly"
    :format="dateFormat"
    style="width: 100%"
    @update:value="handleChange"
  />
</template>

<script>
import { computed } from 'vue'
import dayjs from 'dayjs'

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
      handleChange
    }
  }
}
</script>

<template>
  <div class="date-range-picker">
    <a-space>
      <span>{{ $t('bot.report.queryDate') }}:</span>
      <a-date-picker
        :value="dateValue"
        :format="dateFormat"
        @change="handleChange"
      />
      <a-button @click="handleToday">{{ $t('bot.report.today') }}</a-button>
      <a-button @click="handleYesterday">{{ $t('bot.report.yesterday') }}</a-button>
    </a-space>
  </div>
</template>

<script>
import { computed } from 'vue'
import dayjs from 'dayjs'

export default {
  name: 'DateRangePicker',
  props: {
    date: {
      type: String,
      default: ''
    }
  },
  emits: ['update:date', 'change'],
  setup(props, { emit }) {
    const dateFormat = 'YYYY-MM-DD'

    const dateValue = computed(() => {
      return props.date ? dayjs(props.date) : null
    })

    const handleChange = (date) => {
      const dateStr = date ? date.format(dateFormat) : ''
      emit('update:date', dateStr)
      emit('change', dateStr)
    }

    const handleToday = () => {
      const today = dayjs().format(dateFormat)
      emit('update:date', today)
      emit('change', today)
    }

    const handleYesterday = () => {
      const yesterday = dayjs().subtract(1, 'day').format(dateFormat)
      emit('update:date', yesterday)
      emit('change', yesterday)
    }

    return {
      dateFormat,
      dateValue,
      handleChange,
      handleToday,
      handleYesterday
    }
  }
}
</script>

<style scoped>
.date-range-picker {
  padding: 16px;
  background: #fafafa;
  border-radius: 4px;
}
</style>

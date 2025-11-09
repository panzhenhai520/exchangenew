<template>
  <a-card class="summary-card" :style="{ borderColor: color }">
    <a-statistic
      :title="title"
      :value="amount"
      :precision="2"
      :value-style="{ color: color }"
    >
      <template #suffix>THB</template>
    </a-statistic>
    <div class="count-text">
      {{ $t('bot.report.transactionCount') }}: {{ count }}
    </div>
  </a-card>
</template>

<script>
export default {
  name: 'SummaryCard',
  props: {
    title: {
      type: String,
      required: true
    },
    amount: {
      type: Number,
      default: 0
    },
    count: {
      type: Number,
      default: 0
    },
    color: {
      type: String,
      default: '#1890ff'
    }
  }
}
</script>

<style scoped>
.summary-card {
  border-left: 4px solid;
}

.count-text {
  margin-top: 8px;
  color: #666;
  font-size: 14px;
}
</style>

<template>
  <div class="buy-fx-table">
    <a-table
      :columns="columns"
      :data-source="tableData"
      :loading="loading"
      :pagination="false"
      row-key="transaction_id"
    >
      <template #amount="{ text }">
        {{ formatAmount(text) }}
      </template>
    </a-table>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

export default {
  name: 'BuyFXTable',
  props: {
    loading: {
      type: Boolean,
      default: false
    },
    data: {
      type: Object,
      default: null
    }
  },
  setup(props) {
    const { t } = useI18n()

    const columns = [
      { title: t('bot.report.transactionId'), dataIndex: 'transaction_id', key: 'transaction_id', width: 120 },
      { title: t('bot.report.currency'), dataIndex: 'currency_code', key: 'currency_code', width: 100 },
      { title: t('bot.report.foreignAmount'), dataIndex: 'foreign_amount', key: 'foreign_amount', width: 150, slots: { customRender: 'amount' } },
      { title: t('bot.report.exchangeRate'), dataIndex: 'exchange_rate', key: 'exchange_rate', width: 120 },
      { title: t('bot.report.thbAmount'), dataIndex: 'thb_amount', key: 'thb_amount', width: 150, slots: { customRender: 'amount' } },
      { title: t('bot.report.transactionTime'), dataIndex: 'transaction_time', key: 'transaction_time', width: 150 }
    ]

    const tableData = computed(() => {
      return props.data?.transactions || []
    })

    const formatAmount = (value) => {
      return value ? value.toFixed(2) : '0.00'
    }

    return {
      columns,
      tableData,
      formatAmount
    }
  }
}
</script>

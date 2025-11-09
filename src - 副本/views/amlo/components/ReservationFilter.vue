<template>
  <div class="reservation-filter">
    <a-form layout="inline">
      <a-form-item :label="$t('amlo.reservation.status')">
        <a-select
          v-model:value="filterData.status"
          :placeholder="$t('common.pleaseSelect')"
          style="width: 150px"
          allow-clear
        >
          <a-select-option value="pending">{{ $t('amlo.reservation.pending') }}</a-select-option>
          <a-select-option value="approved">{{ $t('amlo.reservation.approved') }}</a-select-option>
          <a-select-option value="rejected">{{ $t('amlo.reservation.rejected') }}</a-select-option>
          <a-select-option value="completed">{{ $t('amlo.reservation.completed') }}</a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item :label="$t('amlo.reservation.reportType')">
        <a-select
          v-model:value="filterData.report_type"
          :placeholder="$t('common.pleaseSelect')"
          style="width: 180px"
          allow-clear
        >
          <a-select-option value="AMLO-1-01">AMLO-1-01</a-select-option>
          <a-select-option value="AMLO-1-02">AMLO-1-02</a-select-option>
          <a-select-option value="AMLO-1-03">AMLO-1-03</a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item :label="$t('amlo.reservation.dateRange')">
        <a-range-picker
          v-model:value="filterData.dateRange"
          :format="dateFormat"
          style="width: 280px"
        />
      </a-form-item>

      <a-form-item :label="$t('amlo.reservation.customerName')">
        <a-input
          v-model:value="filterData.customer_name"
          :placeholder="$t('common.pleaseInput')"
          style="width: 180px"
          allow-clear
        />
      </a-form-item>

      <a-form-item>
        <a-space>
          <a-button type="primary" @click="handleFilter">
            {{ $t('common.search') }}
          </a-button>
          <a-button @click="handleReset">
            {{ $t('common.reset') }}
          </a-button>
        </a-space>
      </a-form-item>
    </a-form>
  </div>
</template>

<script>
import { reactive } from 'vue'

export default {
  name: 'ReservationFilter',
  emits: ['filter', 'reset'],
  setup(props, { emit }) {
    const dateFormat = 'DD/MM/YYYY'

    const filterData = reactive({
      status: undefined,
      report_type: undefined,
      dateRange: undefined,
      customer_name: undefined
    })

    const handleFilter = () => {
      const params = {}

      if (filterData.status) {
        params.status = filterData.status
      }

      if (filterData.report_type) {
        params.report_type = filterData.report_type
      }

      if (filterData.dateRange && filterData.dateRange.length === 2) {
        params.start_date = filterData.dateRange[0].format('YYYY-MM-DD')
        params.end_date = filterData.dateRange[1].format('YYYY-MM-DD')
      }

      if (filterData.customer_name) {
        params.customer_name = filterData.customer_name
      }

      emit('filter', params)
    }

    const handleReset = () => {
      filterData.status = undefined
      filterData.report_type = undefined
      filterData.dateRange = undefined
      filterData.customer_name = undefined
      emit('reset')
    }

    return {
      dateFormat,
      filterData,
      handleFilter,
      handleReset
    }
  }
}
</script>

<style scoped>
.reservation-filter {
  margin-bottom: 16px;
  padding: 16px;
  background: #fafafa;
  border-radius: 4px;
}
</style>

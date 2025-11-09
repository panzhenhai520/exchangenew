<template>
  <div class="report-filter">
    <a-form layout="inline">
      <a-form-item :label="$t('amlo.report.reportType')">
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

      <a-form-item :label="$t('amlo.report.isReported')">
        <a-select
          v-model:value="filterData.is_reported"
          :placeholder="$t('common.pleaseSelect')"
          style="width: 150px"
          allow-clear
        >
          <a-select-option :value="false">{{ $t('amlo.report.notReported') }}</a-select-option>
          <a-select-option :value="true">{{ $t('amlo.report.reported') }}</a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item :label="$t('amlo.report.reportDate')">
        <a-range-picker
          v-model:value="filterData.dateRange"
          :format="dateFormat"
          style="width: 280px"
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
  name: 'ReportFilter',
  emits: ['filter', 'reset'],
  setup(props, { emit }) {
    const dateFormat = 'DD/MM/YYYY'

    const filterData = reactive({
      report_type: undefined,
      is_reported: undefined,
      dateRange: undefined
    })

    const handleFilter = () => {
      const params = {}

      if (filterData.report_type) {
        params.report_type = filterData.report_type
      }

      if (filterData.is_reported !== undefined) {
        params.is_reported = filterData.is_reported
      }

      if (filterData.dateRange && filterData.dateRange.length === 2) {
        params.start_date = filterData.dateRange[0].format('YYYY-MM-DD')
        params.end_date = filterData.dateRange[1].format('YYYY-MM-DD')
      }

      emit('filter', params)
    }

    const handleReset = () => {
      filterData.report_type = undefined
      filterData.is_reported = undefined
      filterData.dateRange = undefined
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
.report-filter {
  margin-bottom: 16px;
  padding: 16px;
  background: #fafafa;
  border-radius: 4px;
}
</style>

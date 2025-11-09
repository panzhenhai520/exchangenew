<template>
  <a-button
    type="link"
    size="small"
    :loading="loading"
    @click="handleExport"
  >
    <template #icon>
      <DownloadOutlined />
    </template>
    {{ $t('bot.report.exportExcel') }}
  </a-button>
</template>

<script>
import { DownloadOutlined } from '@ant-design/icons-vue'

export default {
  name: 'ExcelExportButton',
  components: {
    DownloadOutlined
  },
  props: {
    loading: {
      type: Boolean,
      default: false
    }
  },
  emits: ['export'],
  setup(props, { emit }) {
    const handleExport = () => {
      emit('export')
    }

    return {
      handleExport
    }
  }
}
</script>

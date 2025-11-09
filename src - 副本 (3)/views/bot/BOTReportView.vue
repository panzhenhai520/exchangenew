<template>
  <div class="bot-report-view">
    <a-card>
      <template #title>
        <span>{{ $t('bot.report.title') }}</span>
      </template>

      <!-- 日期选择器 -->
      <DateRangePicker
        v-model:date="queryDate"
        @change="handleDateChange"
      />

      <!-- 汇总卡片 -->
      <a-row :gutter="16" style="margin-top: 16px">
        <a-col :span="12">
          <SummaryCard
            :title="$t('bot.report.buyFXSummary')"
            :amount="buyFXTotalAmount"
            :count="buyFXTotalCount"
            color="#1890ff"
          />
        </a-col>
        <a-col :span="12">
          <SummaryCard
            :title="$t('bot.report.sellFXSummary')"
            :amount="sellFXTotalAmount"
            :count="sellFXTotalCount"
            color="#52c41a"
          />
        </a-col>
      </a-row>

      <!-- Tab切换 -->
      <a-tabs v-model:activeKey="activeTab" style="margin-top: 24px">
        <!-- 买入外币 -->
        <a-tab-pane key="buy" :tab="$t('bot.report.buyFX')">
          <template #tab>
            <span>
              {{ $t('bot.report.buyFX') }}
              <ExcelExportButton
                :loading="buyFXLoading"
                @export="handleExportBuyFX"
              />
            </span>
          </template>
          <BuyFXTable
            :loading="buyFXLoading"
            :data="buyFXData"
          />
        </a-tab-pane>

        <!-- 卖出外币 -->
        <a-tab-pane key="sell" :tab="$t('bot.report.sellFX')">
          <template #tab>
            <span>
              {{ $t('bot.report.sellFX') }}
              <ExcelExportButton
                :loading="sellFXLoading"
                @export="handleExportSellFX"
              />
            </span>
          </template>
          <SellFXTable
            :loading="sellFXLoading"
            :data="sellFXData"
          />
        </a-tab-pane>
      </a-tabs>
    </a-card>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { useBOTStore } from '@/stores/bot'
import DateRangePicker from './components/DateRangePicker.vue'
import SummaryCard from './components/SummaryCard.vue'
import BuyFXTable from './components/BuyFXTable.vue'
import SellFXTable from './components/SellFXTable.vue'
import ExcelExportButton from './components/ExcelExportButton.vue'

export default {
  name: 'BOTReportView',
  components: {
    DateRangePicker,
    SummaryCard,
    BuyFXTable,
    SellFXTable,
    ExcelExportButton
  },
  setup() {
    const { t } = useI18n()
    const botStore = useBOTStore()

    // 状态
    const activeTab = ref('buy')
    const queryDate = ref(botStore.getYesterdayDate())
    const buyFXLoading = ref(false)
    const sellFXLoading = ref(false)
    const buyFXData = computed(() => botStore.buyFXData)
    const sellFXData = computed(() => botStore.sellFXData)

    // 汇总数据
    const buyFXTotalAmount = computed(() => botStore.buyFXTotalAmount)
    const buyFXTotalCount = computed(() => botStore.buyFXTotalCount)
    const sellFXTotalAmount = computed(() => botStore.sellFXTotalAmount)
    const sellFXTotalCount = computed(() => botStore.sellFXTotalCount)

    // 加载买入外币数据
    const loadBuyFX = async () => {
      buyFXLoading.value = true
      try {
        await botStore.fetchBuyFX(queryDate.value)
      } catch (error) {
        console.error('加载买入外币失败:', error)
        message.error(t('bot.report.loadFailed'))
      } finally {
        buyFXLoading.value = false
      }
    }

    // 加载卖出外币数据
    const loadSellFX = async () => {
      sellFXLoading.value = true
      try {
        await botStore.fetchSellFX(queryDate.value)
      } catch (error) {
        console.error('加载卖出外币失败:', error)
        message.error(t('bot.report.loadFailed'))
      } finally {
        sellFXLoading.value = false
      }
    }

    // 日期变化
    const handleDateChange = (date) => {
      queryDate.value = date
      loadBuyFX()
      loadSellFX()
    }

    // 导出买入Excel
    const handleExportBuyFX = async () => {
      try {
        await botStore.exportBuyFXExcel(queryDate.value)
        message.success(t('bot.report.exportSuccess'))
      } catch (error) {
        console.error('导出Excel失败:', error)
        message.error(t('bot.report.exportFailed'))
      }
    }

    // 导出卖出Excel
    const handleExportSellFX = async () => {
      try {
        await botStore.exportSellFXExcel(queryDate.value)
        message.success(t('bot.report.exportSuccess'))
      } catch (error) {
        console.error('导出Excel失败:', error)
        message.error(t('bot.report.exportFailed'))
      }
    }

    // 组件挂载
    onMounted(() => {
      loadBuyFX()
      loadSellFX()
    })

    return {
      activeTab,
      queryDate,
      buyFXLoading,
      sellFXLoading,
      buyFXData,
      sellFXData,
      buyFXTotalAmount,
      buyFXTotalCount,
      sellFXTotalAmount,
      sellFXTotalCount,
      handleDateChange,
      handleExportBuyFX,
      handleExportSellFX
    }
  }
}
</script>

<style scoped>
.bot-report-view {
  padding: 24px;
}
</style>

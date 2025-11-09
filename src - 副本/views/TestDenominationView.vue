<template>
  <div class="container-fluid py-4">
    <div class="row">
      <div class="col-12">
        <h2 class="mb-4">面值系统测试页面</h2>
        
        <!-- 面值选择器测试 -->
        <div class="card mb-4">
          <div class="card-header">
            <h5>面值选择器测试</h5>
          </div>
          <div class="card-body">
            <DenominationSelector
              :currency-id="1"
              currency-code="USD"
              :allow-multiple="true"
              v-model="denominationData"
              @change="handleDenominationChange"
            />
            
            <div v-if="denominationData" class="mt-3">
              <h6>选择结果:</h6>
              <pre>{{ JSON.stringify(denominationData, null, 2) }}</pre>
            </div>
          </div>
        </div>
        
        <!-- 面值汇率管理测试 -->
        <div class="card mb-4">
          <div class="card-header">
            <h5>面值汇率管理测试</h5>
          </div>
          <div class="card-body">
            <DenominationRateManager />
          </div>
        </div>
        
        <!-- 兑换界面测试 -->
        <div class="card mb-4">
          <div class="card-header">
            <h5>兑换界面测试</h5>
          </div>
          <div class="card-body">
            <ExchangeViewWithDenominations />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import DenominationSelector from '@/components/DenominationSelector.vue'
import DenominationRateManager from '@/components/DenominationRateManager.vue'
import ExchangeViewWithDenominations from '@/views/ExchangeViewWithDenominations.vue'

export default {
  name: 'TestDenominationView',
  components: {
    DenominationSelector,
    DenominationRateManager,
    ExchangeViewWithDenominations
  },
  data() {
    return {
      denominationData: null
    }
  },
  methods: {
    handleDenominationChange(data) {
      console.log('面值数据变化:', data)
      this.denominationData = data
    }
  }
}
</script>

<style scoped>
.card {
  margin-bottom: 1rem;
}

pre {
  background-color: #f8f9fa;
  padding: 1rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
}
</style>
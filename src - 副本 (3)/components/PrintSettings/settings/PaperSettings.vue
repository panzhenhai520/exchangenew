<template>
  <div class="paper-settings">
    <div class="row g-2">
      <div class="col-12">
        <label class="form-label-sm">纸张类型</label>
        <select 
          :value="settings.paper_size.value.name" 
          @change="updatePaperSize('name', $event.target.value)"
          class="form-select form-select-sm"
        >
          <option value="A4">A4 (210×297mm)</option>
          <option value="A5">A5 (148×210mm)</option>
          <option value="Letter">Letter (216×279mm)</option>
          <option value="Legal">Legal (216×356mm)</option>
          <option value="custom">自定义</option>
        </select>
      </div>
      <div class="col-12">
        <label class="form-label-sm">纸张方向</label>
        <select 
          :value="settings.paper_size.value.orientation" 
          @change="updatePaperSize('orientation', $event.target.value)"
          class="form-select form-select-sm"
        >
          <option value="portrait">纵向 (Portrait)</option>
          <option value="landscape">横向 (Landscape)</option>
        </select>
      </div>
      <div class="col-6" v-if="settings.paper_size.value.name === 'custom'">
        <label class="form-label-sm">宽度 (mm)</label>
        <input 
          type="number" 
          class="form-control form-control-sm" 
          :value="settings.paper_size.value.width"
          @input="updatePaperSize('width', parseFloat($event.target.value) || 0)"
          min="50"
          max="500"
        >
      </div>
      <div class="col-6" v-if="settings.paper_size.value.name === 'custom'">
        <label class="form-label-sm">高度 (mm)</label>
        <input 
          type="number" 
          class="form-control form-control-sm" 
          :value="settings.paper_size.value.height"
          @input="updatePaperSize('height', parseFloat($event.target.value) || 0)"
          min="50"
          max="500"
        >
      </div>
    </div>
    
    <!-- 页边距设置 -->
    <div class="row g-2 mt-2">
      <div class="col-12"><small class="text-muted">页边距设置 (mm)</small></div>
      <div class="col-6">
        <label class="form-label-sm">上</label>
        <input 
          type="number" 
          class="form-control form-control-sm" 
          :value="settings.margins.value.top"
          @input="updateMargins('top', parseFloat($event.target.value) || 0)"
          min="0"
          max="200"
          step="0.5"
        >
      </div>
      <div class="col-6">
        <label class="form-label-sm">右</label>
        <input 
          type="number" 
          class="form-control form-control-sm" 
          :value="settings.margins.value.right"
          @input="updateMargins('right', parseFloat($event.target.value) || 0)"
          min="0"
          max="200"
          step="0.5"
        >
      </div>
      <div class="col-6">
        <label class="form-label-sm">下</label>
        <input 
          type="number" 
          class="form-control form-control-sm" 
          :value="settings.margins.value.bottom"
          @input="updateMargins('bottom', parseFloat($event.target.value) || 0)"
          min="0"
          max="200"
          step="0.5"
        >
      </div>
      <div class="col-6">
        <label class="form-label-sm">左</label>
        <input 
          type="number" 
          class="form-control form-control-sm" 
          :value="settings.margins.value.left"
          @input="updateMargins('left', parseFloat($event.target.value) || 0)"
          min="0"
          max="200"
          step="0.5"
        >
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PaperSettings',
  props: {
    settings: {
      type: Object,
      required: true
    }
  },
  emits: ['update-settings'],
  methods: {
    updatePaperSize(property, value) {
      console.log('Updating paper size:', property, value) // 调试日志
      
      this.$emit('update-settings', {
        path: 'paper_size.value',
        update: {
          ...this.settings.paper_size.value,
          [property]: value
        }
      })
    },
    
    updateMargins(property, value) {
      console.log('Updating margins:', property, value) // 调试日志
      
      this.$emit('update-settings', {
        path: 'margins.value',
        update: {
          ...this.settings.margins.value,
          [property]: value
        }
      })
    }
  }
}
</script>

<style scoped>
.paper-settings {
  font-size: 0.8rem;
}

.form-label-sm {
  margin-bottom: 2px;
  font-weight: 500;
  font-size: 0.75rem;
}

.form-control-sm, .form-select-sm {
  font-size: 0.75rem;
  padding: 2px 6px;
}

.row.g-2 {
  --bs-gutter-x: 0.5rem;
  --bs-gutter-y: 0.5rem;
}
</style> 
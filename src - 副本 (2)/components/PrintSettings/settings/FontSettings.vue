<template>
  <div class="font-settings">
    <div class="row g-2">
      <div class="col-12">
        <label class="form-label-sm">字体族</label>
        <select 
          :value="settings.font_settings.value.family" 
          @change="updateFont('family', $event.target.value)"
          class="form-select form-select-sm"
        >
          <option value="SimSun">宋体</option>
          <option value="SimHei">黑体</option>
          <option value="KaiTi">楷体</option>
          <option value="Microsoft YaHei">微软雅黑</option>
          <option value="Arial">Arial</option>
          <option value="Times New Roman">Times New Roman</option>
        </select>
      </div>
      <div class="col-6">
        <label class="form-label-sm">字体大小</label>
        <input 
          type="number" 
          class="form-control form-control-sm" 
          :value="settings.font_settings.value.size"
          @input="updateFont('size', parseFloat($event.target.value) || 12)"
          min="8"
          max="24"
        >
      </div>
      <div class="col-6">
        <label class="form-label-sm">字体颜色</label>
        <input 
          type="color" 
          class="form-control form-control-color form-control-sm" 
          :value="settings.font_settings.value.color"
          @input="updateFont('color', $event.target.value)"
        >
      </div>
    </div>

    <div class="form-check form-switch">
      <input 
        class="form-check-input" 
        type="checkbox" 
        :checked="settings.font_settings.value.bold"
        @change="updateFont('bold', $event.target.checked)"
      >
      <label class="form-check-label" style="font-size: 0.7rem;">
        粗体
      </label>
    </div>
  </div>
</template>

<script>
export default {
  name: 'FontSettings',
  props: {
    settings: {
      type: Object,
      required: true
    }
  },
  emits: ['update-settings'],
  methods: {
    updateFont(property, value) {
      console.log('Updating font:', property, value) // 调试日志
      
      this.$emit('update-settings', {
        path: 'font_settings.value',
        update: {
          ...this.settings.font_settings.value,
          [property]: value
        }
      })
    }
  }
}
</script>

<style scoped>
.font-settings {
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

.form-check-label {
  margin-left: 0.25rem;
}
</style> 
<template>
  <div class="content-settings">
    <div class="mb-2">
      <label class="form-label" style="font-size: 0.7rem;">对齐方式</label>
      <select 
        :value="settings.layout_settings.value.alignment" 
        @change="updateContent('alignment', $event.target.value)"
        class="form-select form-select-sm"
      >
        <option value="left">左对齐</option>
        <option value="center">居中</option>
        <option value="right">右对齐</option>
      </select>
    </div>

    <div class="mb-2">
      <label class="form-label" style="font-size: 0.7rem;">行间距</label>
      <input 
        type="number" 
        class="form-control form-control-sm" 
        :value="settings.layout_settings.value.line_spacing"
        @input="updateContent('line_spacing', $event.target.value)"
        min="1"
        max="3"
        step="0.1"
      >
    </div>
  </div>
</template>

<script>
export default {
  name: 'ContentSettings',
  props: {
    settings: {
      type: Object,
      required: true
    }
  },
  emits: ['update-settings'],
  methods: {
    updateContent(property, value) {
      this.$emit('update-settings', {
        path: 'layout_settings.value',
        update: {
          ...this.settings.layout_settings.value,
          [property]: property === 'line_spacing' ? parseFloat(value) || 1.2 : value
        }
      })
    }
  }
}
</script>

<style scoped>
.content-settings {
  font-size: 0.8rem;
}

.form-label {
  margin-bottom: 2px;
  font-weight: 500;
}

.form-control-sm, .form-select-sm {
  font-size: 0.75rem;
  padding: 2px 6px;
}
</style> 
<template>
  <div class="layout-settings">
    <div class="row g-2">
      <div class="col-6">
        <label class="form-label-sm">行间距</label>
        <input 
          type="number" 
          class="form-control form-control-sm" 
          :value="settings.layout_settings.value.line_spacing || 1.5"
          @input="updateLayout('line_spacing', $event.target.value)"
          step="0.1"
          min="1.0"
          max="3.0"
        >
      </div>
      <div class="col-6">
        <label class="form-label-sm">内容样式</label>
        <select 
          :value="settings.layout_settings.value.content_style" 
          @change="updateLayout('content_style', $event.target.value)"
          class="form-select form-select-sm"
        >
          <option value="table">表格格式</option>
          <option value="simple">简洁格式</option>
        </select>
      </div>
      
      <div class="col-6">
        <label class="form-label-sm">标题对齐</label>
        <select 
          :value="settings.layout_settings.value.title_alignment || 'center'" 
          @change="updateLayout('title_alignment', $event.target.value)"
          class="form-select form-select-sm"
        >
          <option value="left">左对齐</option>
          <option value="center">居中</option>
          <option value="right">右对齐</option>
        </select>
      </div>
      <div class="col-6">
        <label class="form-label-sm">内容对齐</label>
        <select 
          :value="settings.layout_settings.value.alignment || 'left'" 
          @change="updateLayout('alignment', $event.target.value)"
          class="form-select form-select-sm"
        >
          <option value="left">左对齐</option>
          <option value="center">居中</option>
          <option value="right">右对齐</option>
        </select>
      </div>
      
      <div class="col-12">
        <label class="form-label-sm">字段标签宽度 (%)</label>
        <input 
          type="number" 
          class="form-control form-control-sm" 
          :value="settings.layout_settings.value.field_label_width || 40"
          @input="updateLayout('field_label_width', $event.target.value)"
          min="20"
          max="60"
        >
      </div>
      
      <!-- 表格尺寸设置 -->
      <div class="col-6" v-if="settings.layout_settings.value.content_style === 'table'">
        <label class="form-label-sm">表格宽度 (mm)</label>
        <input 
          type="number" 
          class="form-control form-control-sm" 
          :value="settings.layout_settings.value.table_width || 160"
          @input="updateLayout('table_width', $event.target.value)"
          min="80"
          max="200"
          step="5"
        >
      </div>
      <div class="col-6" v-if="settings.layout_settings.value.content_style === 'table'">
        <label class="form-label-sm">表格高度 (mm)</label>
        <input 
          type="number" 
          class="form-control form-control-sm" 
          :value="settings.layout_settings.value.table_height || 80"
          @input="updateLayout('table_height', $event.target.value)"
          min="40"
          max="150"
          step="5"
        >
      </div>
      
      <div class="col-12">
        <div class="form-check">
          <input 
            type="checkbox" 
            class="form-check-input" 
            id="showFieldLabels"
            :checked="settings.layout_settings.value.show_field_labels"
            @change="updateLayout('show_field_labels', $event.target.checked)"
          >
          <label class="form-check-label" for="showFieldLabels">显示字段标签</label>
        </div>
      </div>
      <div class="col-12">
        <div class="form-check">
          <input 
            type="checkbox" 
            class="form-check-input" 
            id="tableBorder"
            :checked="settings.layout_settings.value.table_border"
            @change="updateLayout('table_border', $event.target.checked)"
          >
          <label class="form-check-label" for="tableBorder">显示表格边框</label>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'LayoutSettings',
  props: {
    settings: {
      type: Object,
      required: true
    }
  },
  emits: ['update-settings'],
  methods: {
    updateLayout(property, value) {
      const processedValue = ['line_spacing', 'field_label_width', 'table_width', 'table_height'].includes(property) 
        ? parseFloat(value) || 0 
        : value
        
      this.$emit('update-settings', {
        path: 'layout_settings.value',
        update: {
          ...this.settings.layout_settings.value,
          [property]: processedValue
        }
      })
    }
  }
}
</script>

<style scoped>
.layout-settings {
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

.form-check-label {
  margin-left: 0.25rem;
}

.row.g-2 {
  --bs-gutter-x: 0.5rem;
  --bs-gutter-y: 0.5rem;
}
</style> 
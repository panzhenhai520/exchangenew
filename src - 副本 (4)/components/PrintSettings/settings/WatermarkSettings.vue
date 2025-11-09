<template>
  <div class="watermark-settings">
    <div class="row g-2">
      <div class="col-12">
        <div class="form-check">
          <input 
            type="checkbox" 
            class="form-check-input" 
            id="watermarkEnabled"
            :checked="settings.advanced_settings.value.watermark_enabled"
            @change="updateWatermark('watermark_enabled', $event.target.checked)"
          >
          <label class="form-check-label" for="watermarkEnabled">启用水印</label>
        </div>
      </div>
      
      <div v-if="settings.advanced_settings.value.watermark_enabled" class="col-12">
        <div class="row g-2">
          <div class="col-12">
            <label class="form-label-sm">水印文字</label>
            <input 
              type="text" 
              class="form-control form-control-sm" 
              :value="settings.advanced_settings.value.watermark_text"
              @input="updateWatermark('watermark_text', $event.target.value)"
            >
          </div>
          <div class="col-12">
            <label class="form-label-sm">透明度 ({{ Math.round(settings.advanced_settings.value.watermark_opacity * 100) }}%)</label>
            <input 
              type="range" 
              class="form-range" 
              :value="settings.advanced_settings.value.watermark_opacity"
              @input="updateWatermark('watermark_opacity', $event.target.value)"
              min="0.1"
              max="0.5"
              step="0.1"
            >
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'WatermarkSettings',
  props: {
    settings: {
      type: Object,
      required: true
    }
  },
  emits: ['update-settings'],
  methods: {
    updateWatermark(property, value) {
      this.$emit('update-settings', {
        path: 'advanced_settings.value',
        update: {
          ...this.settings.advanced_settings.value,
          [property]: property === 'watermark_opacity' ? parseFloat(value) || 0.1 : value
        }
      })
    }
  }
}
</script>

<style scoped>
.watermark-settings {
  font-size: 0.8rem;
}

.form-label-sm {
  margin-bottom: 2px;
  font-weight: 500;
  font-size: 0.75rem;
}

.form-control-sm {
  font-size: 0.75rem;
  padding: 2px 6px;
}

.form-check-label {
  margin-left: 0.25rem;
}

.form-range {
  margin-bottom: 0.5rem;
}

.row.g-2 {
  --bs-gutter-x: 0.5rem;
  --bs-gutter-y: 0.5rem;
}
</style> 
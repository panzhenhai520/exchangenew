<template>
  <div class="signature-settings">
    <div class="row g-2">
      <div class="col-12">
        <label class="form-label-sm">签名样式</label>
        <select 
          :value="settings.signature_settings.value.signature_style" 
          @change="updateSignature('signature_style', $event.target.value)"
          class="form-select form-select-sm"
        >
          <option value="none">不显示签名区域</option>
          <option value="single">单签名框</option>
          <option value="double">双签名框</option>
        </select>
      </div>
      <div v-if="settings.signature_settings.value.signature_style !== 'none'" class="col-12">
        <div class="form-check">
          <input 
            type="checkbox" 
            class="form-check-input" 
            id="showDateLine"
            :checked="settings.signature_settings.value.show_date_line"
            @change="updateSignature('show_date_line', $event.target.checked)"
          >
          <label class="form-check-label" for="showDateLine">显示日期线</label>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SignatureSettings',
  props: {
    settings: {
      type: Object,
      required: true
    }
  },
  emits: ['update-settings'],
  methods: {
    updateSignature(property, value) {
      this.$emit('update-settings', {
        path: 'signature_settings.value',
        update: {
          ...this.settings.signature_settings.value,
          [property]: value
        }
      })
    }
  }
}
</script>

<style scoped>
.signature-settings {
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
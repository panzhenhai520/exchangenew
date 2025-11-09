<template>
  <div class="logo-settings">
    <div class="row g-2">
      <div class="col-12">
        <div class="form-check">
          <input 
            type="checkbox" 
            class="form-check-input" 
            id="showLogo"
            :checked="settings.header_settings.value.show_logo"
            @change="updateLogo('show_logo', $event.target.checked)"
          >
          <label class="form-check-label" for="showLogo">显示Logo</label>
        </div>
      </div>
      
      <div v-if="settings.header_settings.value.show_logo" class="col-12">
        <div class="logo-upload-section">
          <div class="logo-upload-area" @click="triggerLogoUpload" @dragover.prevent @drop="handleLogoDrop">
            <div v-if="settings.header_settings.value.logo_data" class="current-logo">
              <img :src="settings.header_settings.value.logo_data" alt="当前Logo" class="logo-preview">
              <div class="logo-actions">
                <button @click.stop="triggerLogoUpload" class="btn btn-sm btn-outline-primary me-1">
                  <i class="fas fa-upload"></i> 更换
                </button>
                <button @click.stop="deleteLogo" class="btn btn-sm btn-outline-danger">
                  <i class="fas fa-trash"></i> 删除
                </button>
              </div>
            </div>
            <div v-else class="upload-placeholder">
              <i class="fas fa-cloud-upload-alt fa-2x mb-2"></i>
              <p class="mb-1">点击或拖拽上传Logo</p>
              <small class="text-muted">支持 PNG, JPG, GIF, SVG 格式，最大2MB</small>
            </div>
            <input ref="logoInput" type="file" @change="handleLogoUpload" accept="image/*" style="display: none;">
          </div>
          <div class="row g-1 mt-2">
            <div class="col-6">
              <label class="form-label-sm">宽度 (px)</label>
              <input 
                type="number" 
                class="form-control form-control-sm" 
                :value="settings.header_settings.value.logo_width"
                @input="updateLogo('logo_width', $event.target.value)"
                min="50"
                max="300"
              >
            </div>
            <div class="col-6">
              <label class="form-label-sm">高度 (px)</label>
              <input 
                type="number" 
                class="form-control form-control-sm" 
                :value="settings.header_settings.value.logo_height"
                @input="updateLogo('logo_height', $event.target.value)"
                min="30"
                max="200"
              >
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'LogoSettings',
  props: {
    settings: {
      type: Object,
      required: true
    }
  },
  emits: ['update-settings'],
  methods: {
    updateLogo(property, value) {
      const processedValue = ['logo_width', 'logo_height'].includes(property) 
        ? parseFloat(value) || 0 
        : value
        
      this.$emit('update-settings', {
        path: 'header_settings.value',
        update: {
          ...this.settings.header_settings.value,
          [property]: processedValue
        }
      })
    },
    
    triggerLogoUpload() {
      this.$refs.logoInput.click()
    },
    
    handleLogoUpload(event) {
      const file = event.target.files[0]
      if (file) {
        this.processLogoFile(file)
      }
    },
    
    handleLogoDrop(event) {
      event.preventDefault()
      const file = event.dataTransfer.files[0]
      if (file && file.type.startsWith('image/')) {
        this.processLogoFile(file)
      }
    },
    
    processLogoFile(file) {
      if (file.size > 2 * 1024 * 1024) {
        this.$toast.error(this.$t('printSettings.messages.fileTooLarge'))
        return
      }
      
      const reader = new FileReader()
      reader.onload = (e) => {
        this.updateLogo('logo_data', e.target.result)
      }
      reader.readAsDataURL(file)
    },
    
    deleteLogo() {
      this.updateLogo('logo_data', '')
    }
  }
}
</script>

<style scoped>
.logo-settings {
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

.logo-upload-section {
  margin-top: 8px;
}

.logo-upload-area {
  border: 2px dashed #ddd;
  border-radius: 4px;
  padding: 15px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.3s;
}

.logo-upload-area:hover {
  border-color: #007bff;
}

.current-logo {
  position: relative;
}

.logo-preview {
  max-width: 100px;
  max-height: 60px;
  object-fit: contain;
  margin-bottom: 8px;
}

.logo-actions {
  display: flex;
  justify-content: center;
  gap: 4px;
}

.upload-placeholder {
  color: #666;
}

.upload-placeholder i {
  color: #ccc;
}
</style> 
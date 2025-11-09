<template>
  <div class="title-settings">
    <!-- 标题字体 -->
    <div class="mb-2">
      <label class="form-label" style="font-size: 0.7rem;">字体</label>
      <select 
        :value="settings.header_settings.value.title_font_family || 'SimSun'" 
        @change="updateHeaderSetting('title_font_family', $event.target.value)"
        class="form-select form-select-sm"
      >
        <option value="SimSun">宋体</option>
        <option value="SimHei">黑体</option>
        <option value="Microsoft YaHei">微软雅黑</option>
        <option value="KaiTi">楷体</option>
        <option value="FangSong">仿宋</option>
        <option value="Arial">Arial</option>
        <option value="Times New Roman">Times New Roman</option>
      </select>
    </div>

    <!-- 字体大小 -->
    <div class="mb-2">
      <label class="form-label" style="font-size: 0.7rem;">字体大小</label>
      <div class="input-group input-group-sm">
        <input 
          type="number" 
          class="form-control form-control-sm" 
          :value="settings.header_settings.value.title_size"
          @input="updateHeaderSetting('title_size', $event.target.value)"
          min="8"
          max="72"
          step="1"
        >
        <span class="input-group-text">px</span>
      </div>
    </div>

    <!-- 字体颜色 -->
    <div class="mb-2">
      <label class="form-label" style="font-size: 0.7rem;">字体颜色</label>
      <div class="input-group input-group-sm">
        <input 
          type="color" 
          class="form-control form-control-color form-control-sm" 
          :value="settings.header_settings.value.title_color"
          @input="updateHeaderSetting('title_color', $event.target.value)"
          style="width: 40px; height: 30px;"
        >
        <input 
          type="text" 
          class="form-control form-control-sm" 
          :value="settings.header_settings.value.title_color"
          @input="updateHeaderSetting('title_color', $event.target.value)"
          placeholder="#000000"
          style="font-family: monospace;"
        >
      </div>
    </div>

    <!-- 字体粗细 -->
    <div class="mb-2">
      <div class="form-check form-switch">
        <input 
          class="form-check-input" 
          type="checkbox" 
          id="titleBold"
          :checked="settings.header_settings.value.title_bold"
          @change="updateHeaderSetting('title_bold', $event.target.checked)"
        >
        <label class="form-check-label" for="titleBold" style="font-size: 0.7rem;">
          粗体
        </label>
      </div>
    </div>

    <!-- 标题对齐方式 -->
    <div class="mb-2">
      <label class="form-label" style="font-size: 0.7rem;">对齐方式</label>
      <div class="btn-group w-100" role="group">
        <input 
          type="radio" 
          class="btn-check" 
          id="titleLeft" 
          :checked="settings.layout_settings.value.title_alignment === 'left'"
          @change="updateLayoutSetting('title_alignment', 'left')"
        >
        <label class="btn btn-outline-secondary btn-sm" for="titleLeft" style="font-size: 0.7rem;">
          <i class="fas fa-align-left"></i>
        </label>
        
        <input 
          type="radio" 
          class="btn-check" 
          id="titleCenter" 
          :checked="settings.layout_settings.value.title_alignment === 'center'"
          @change="updateLayoutSetting('title_alignment', 'center')"
        >
        <label class="btn btn-outline-secondary btn-sm" for="titleCenter" style="font-size: 0.7rem;">
          <i class="fas fa-align-center"></i>
        </label>
        
        <input 
          type="radio" 
          class="btn-check" 
          id="titleRight" 
          :checked="settings.layout_settings.value.title_alignment === 'right'"
          @change="updateLayoutSetting('title_alignment', 'right')"
        >
        <label class="btn btn-outline-secondary btn-sm" for="titleRight" style="font-size: 0.7rem;">
          <i class="fas fa-align-right"></i>
        </label>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TitleSettings',
  props: {
    settings: {
      type: Object,
      required: true
    }
  },
  emits: ['update-settings'],
  methods: {
    updateHeaderSetting(property, value) {
      const newValue = property === 'title_size' ? parseInt(value) || 16 : 
                       property === 'title_bold' ? value : value
      
      this.$emit('update-settings', {
        path: 'header_settings.value',
        update: {
          ...this.settings.header_settings.value,
          [property]: newValue
        }
      })
    },
    
    updateLayoutSetting(property, value) {
      this.$emit('update-settings', {
        path: 'layout_settings.value',
        update: {
          ...this.settings.layout_settings.value,
          [property]: value
        }
      })
    }
  }
}
</script>

<style scoped>
.title-settings {
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

.btn-group .btn-sm {
  padding: 2px 8px;
}

.form-control-color {
  padding: 1px;
  border-radius: 4px;
}

.input-group-sm .input-group-text {
  font-size: 0.75rem;
  padding: 2px 8px;
}

.form-check {
  padding-left: 1.5em;
}

.form-check-input {
  margin-left: -1.5em;
}

.row.g-1 {
  --bs-gutter-x: 0.25rem;
  --bs-gutter-y: 0.25rem;
}
</style> 
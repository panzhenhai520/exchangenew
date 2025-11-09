<template>
  <div class="settings-panel">
    <!-- 选中元素的属性调整 -->
    <div v-if="selectedElement" class="element-properties mb-2">
      <div class="card">
        <div class="card-header py-1">
          <h6 class="mb-0" style="font-size: 0.8rem;">
            <i class="fas fa-cog me-1"></i>{{ getElementLabel(selectedElement) }} 属性
          </h6>
        </div>
        <div class="card-body py-1">
          <div class="row g-1">
            <div class="col-6">
              <label class="form-label-sm" style="font-size: 0.7rem;">X位置 (mm)</label>
              <input 
                type="number" 
                class="form-control form-control-sm"
                style="font-size: 0.7rem; height: 24px;"
                step="0.1"
                :value="getElementPosition(selectedElement, 'left')"
                @input="updateElementPosition(selectedElement, 'left', parseFloat($event.target.value) || 0)"
              >
            </div>
            <div class="col-6">
              <label class="form-label-sm" style="font-size: 0.7rem;">Y位置 (mm)</label>
              <input 
                type="number" 
                class="form-control form-control-sm"
                style="font-size: 0.7rem; height: 24px;"
                step="0.1"
                :value="getElementPosition(selectedElement, 'top')"
                @input="updateElementPosition(selectedElement, 'top', parseFloat($event.target.value) || 0)"
              >
            </div>
            <div class="col-6" v-if="getElementPosition(selectedElement, 'width') !== null">
              <label class="form-label-sm" style="font-size: 0.7rem;">宽度 (mm)</label>
              <input 
                type="number" 
                class="form-control form-control-sm"
                style="font-size: 0.7rem; height: 24px;"
                step="0.1"
                :value="getElementPosition(selectedElement, 'width')"
                @input="updateElementPosition(selectedElement, 'width', parseFloat($event.target.value) || 0)"
              >
            </div>
            <div class="col-6" v-if="getElementPosition(selectedElement, 'height') !== null">
              <label class="form-label-sm" style="font-size: 0.7rem;">高度 (mm)</label>
              <input 
                type="number" 
                class="form-control form-control-sm"
                style="font-size: 0.7rem; height: 24px;"
                step="0.1"
                :value="getElementPosition(selectedElement, 'height')"
                @input="updateElementPosition(selectedElement, 'height', parseFloat($event.target.value) || 0)"
              >
            </div>
            <div class="col-12">
              <div class="form-check" style="font-size: 0.7rem;">
                <input 
                  type="checkbox" 
                  class="form-check-input"
                  style="transform: scale(0.8);"
                  :checked="getElementVisibility(selectedElement)"
                  @change="updateElementVisibility(selectedElement, $event.target.checked)"
                >
                <label class="form-check-label" style="font-size: 0.7rem;">显示此元素</label>
              </div>
            </div>
            
            <!-- 字体设置 -->
            <div class="col-12" v-if="shouldShowFontSettings(selectedElement)">
              <hr style="margin: 8px 0;">
              <small class="text-muted" style="font-size: 0.65rem;">字体设置</small>
            </div>
            <div class="col-6" v-if="shouldShowFontSettings(selectedElement)">
              <label class="form-label-sm" style="font-size: 0.7rem;">字体</label>
              <select 
                class="form-select form-select-sm"
                style="font-size: 0.7rem; height: 24px;"
                :value="getElementFont(selectedElement, 'fontFamily')"
                @change="updateElementFont(selectedElement, 'fontFamily', $event.target.value)"
              >
                <option value="SimSun">宋体</option>
                <option value="SimHei">黑体</option>
                <option value="KaiTi">楷体</option>
                <option value="Microsoft YaHei">微软雅黑</option>
                <option value="Arial">Arial</option>
                <option value="Times New Roman">Times New Roman</option>
              </select>
            </div>
            <div class="col-6" v-if="shouldShowFontSettings(selectedElement)">
              <label class="form-label-sm" style="font-size: 0.7rem;">大小</label>
              <input 
                type="number" 
                class="form-control form-control-sm"
                style="font-size: 0.7rem; height: 24px;"
                min="8"
                max="48"
                :value="getElementFont(selectedElement, 'fontSize')"
                @input="updateElementFont(selectedElement, 'fontSize', parseFloat($event.target.value) || 12)"
              >
            </div>
            <div class="col-6" v-if="shouldShowFontSettings(selectedElement)">
              <label class="form-label-sm" style="font-size: 0.7rem;">颜色</label>
              <input 
                type="color" 
                class="form-control form-control-color form-control-sm"
                style="font-size: 0.7rem; height: 24px;"
                :value="getElementFont(selectedElement, 'color')"
                @input="updateElementFont(selectedElement, 'color', $event.target.value)"
              >
            </div>
            <div class="col-6" v-if="shouldShowFontSettings(selectedElement)">
              <div class="form-check" style="font-size: 0.7rem; margin-top: 20px;">
                <input 
                  type="checkbox" 
                  class="form-check-input"
                  style="transform: scale(0.8);"
                  :checked="getElementFont(selectedElement, 'fontWeight') === 'bold'"
                  @change="updateElementFont(selectedElement, 'fontWeight', $event.target.checked ? 'bold' : 'normal')"
                >
                <label class="form-check-label" style="font-size: 0.7rem;">粗体</label>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Vue手风琴设置面板 -->
    <div class="vue-accordion">
      <!-- 纸张设置 -->
      <div class="accordion-item">
        <div class="accordion-header">
          <button 
            class="accordion-button" 
            :class="{ 'collapsed': !panelStates.paper }"
            type="button" 
            @click="togglePanel('paper')"
          >
            <i class="fas fa-file-alt me-2"></i>纸张设置
            <i class="fas fa-chevron-down ms-auto accordion-arrow" :class="{ 'rotated': panelStates.paper }"></i>
          </button>
        </div>
        <div class="accordion-collapse" :class="{ 'show': panelStates.paper }">
          <div class="accordion-body">
            <PaperSettings 
              :settings="settings"
              @update-settings="$emit('update-settings', $event)"
            />
          </div>
        </div>
      </div>

      <!-- Logo设置 -->
      <div class="accordion-item">
        <div class="accordion-header">
          <button 
            class="accordion-button" 
            :class="{ 'collapsed': !panelStates.logo }"
            type="button" 
            @click="togglePanel('logo')"
          >
            <i class="fas fa-image me-2"></i>Logo设置
            <i class="fas fa-chevron-down ms-auto accordion-arrow" :class="{ 'rotated': panelStates.logo }"></i>
          </button>
        </div>
        <div class="accordion-collapse" :class="{ 'show': panelStates.logo }">
          <div class="accordion-body">
            <LogoSettings 
              :settings="settings"
              @update-settings="$emit('update-settings', $event)"
            />
          </div>
        </div>
      </div>

      <!-- 布局设置 -->
      <div class="accordion-item">
        <div class="accordion-header">
          <button 
            class="accordion-button" 
            :class="{ 'collapsed': !panelStates.layout }"
            type="button" 
            @click="togglePanel('layout')"
          >
            <i class="fas fa-th-large me-2"></i>布局设置
            <i class="fas fa-chevron-down ms-auto accordion-arrow" :class="{ 'rotated': panelStates.layout }"></i>
          </button>
        </div>
        <div class="accordion-collapse" :class="{ 'show': panelStates.layout }">
          <div class="accordion-body">
            <LayoutSettings 
              :settings="settings"
              @update-settings="$emit('update-settings', $event)"
            />
          </div>
        </div>
      </div>

      <!-- 签名设置 -->
      <div class="accordion-item">
        <div class="accordion-header">
          <button 
            class="accordion-button" 
            :class="{ 'collapsed': !panelStates.signature }"
            type="button" 
            @click="togglePanel('signature')"
          >
            <i class="fas fa-signature me-2"></i>签名设置
            <i class="fas fa-chevron-down ms-auto accordion-arrow" :class="{ 'rotated': panelStates.signature }"></i>
          </button>
        </div>
        <div class="accordion-collapse" :class="{ 'show': panelStates.signature }">
          <div class="accordion-body">
            <SignatureSettings 
              :settings="settings"
              @update-settings="$emit('update-settings', $event)"
            />
          </div>
        </div>
      </div>

      <!-- 高级设置 -->
      <div class="accordion-item">
        <div class="accordion-header">
          <button 
            class="accordion-button" 
            :class="{ 'collapsed': !panelStates.advanced }"
            type="button" 
            @click="togglePanel('advanced')"
          >
            <i class="fas fa-cogs me-2"></i>高级设置
            <i class="fas fa-chevron-down ms-auto accordion-arrow" :class="{ 'rotated': panelStates.advanced }"></i>
          </button>
        </div>
        <div class="accordion-collapse" :class="{ 'show': panelStates.advanced }">
          <div class="accordion-body">
            <WatermarkSettings 
              :settings="settings"
              @update-settings="$emit('update-settings', $event)"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import PaperSettings from './settings/PaperSettings.vue'
import LayoutSettings from './settings/LayoutSettings.vue'
import SignatureSettings from './settings/SignatureSettings.vue'
import LogoSettings from './settings/LogoSettings.vue'
import WatermarkSettings from './settings/WatermarkSettings.vue'

export default {
  name: 'PrintSettingsPanel',
  components: {
    PaperSettings,
    LayoutSettings,
    SignatureSettings,
    LogoSettings,
    WatermarkSettings
  },
  props: {
    settings: {
      type: Object,
      required: true
    },
    elementPositions: {
      type: Object,
      required: true
    },
    selectedElement: {
      type: String,
      default: null
    }
  },
  emits: [
    'update-settings',
    'update-element-position'
  ],
  data() {
    return {
      // 控制各个面板的展开/收缩状态
      panelStates: {
        paper: true,    // 纸张设置默认展开
        logo: false,    // Logo设置默认收缩
        layout: false,  // 布局设置默认收缩
        signature: false, // 签名设置默认收缩
        advanced: false   // 高级设置默认收缩
      }
    }
  },
  methods: {
    // 切换面板展开/收缩状态
    togglePanel(panelName) {
      this.panelStates[panelName] = !this.panelStates[panelName]
    },

    getElementLabel(elementType) {
      const labels = {
        logo: 'Logo',
        title: '标题',
        subtitle: '副标题',
        branch: '网点信息',
        content: '内容',
        signature: '签名',
        watermark: '水印'
      }
      return labels[elementType] || elementType
    },
    
    getElementPosition(elementType, property) {
      const position = this.elementPositions[elementType]
      return position ? position[property] || 0 : 0
    },
    
    updateElementPosition(elementType, property, value) {
      console.log('Updating element position:', elementType, property, value) // 调试日志
      
      this.$emit('update-element-position', {
        elementType,
        [property]: value
      })
    },
    
    getElementVisibility(elementType) {
      // 检查元素在elementPositions中的visible属性
      const position = this.elementPositions[elementType]
      if (position && Object.prototype.hasOwnProperty.call(position, 'visible')) {
        return position.visible
      }
      
      // 根据元素类型检查settings中的显示设置
      switch (elementType) {
        case 'logo':
          return this.settings.header_settings?.value?.show_logo || false
        case 'watermark':
          return this.settings.advanced_settings?.value?.watermark_enabled || false
        case 'branch':
          return this.settings.header_settings?.value?.show_branch_info || false
        default:
          return true // 默认显示
      }
    },
    
    updateElementVisibility(elementType, visible) {
      console.log('Updating element visibility:', elementType, visible) // 调试日志
      
      // 更新elementPositions中的visible属性
      this.$emit('update-element-position', {
        elementType,
        visible: visible
      })
      
      // 同时更新settings中对应的显示设置
      switch (elementType) {
        case 'logo':
          this.$emit('update-settings', {
            path: 'header_settings.value',
            update: {
              ...this.settings.header_settings.value,
              show_logo: visible
            }
          })
          break
        case 'watermark':
          this.$emit('update-settings', {
            path: 'advanced_settings.value',
            update: {
              ...this.settings.advanced_settings.value,
              watermark_enabled: visible
            }
          })
          break
        case 'branch':
          this.$emit('update-settings', {
            path: 'header_settings.value',
            update: {
              ...this.settings.header_settings.value,
              show_branch_info: visible
            }
          })
          break
      }
    },
    
    shouldShowFontSettings(elementType) {
      // 根据元素类型决定是否显示字体设置
      const textElements = ['title', 'subtitle', 'content', 'branch', 'signature']
      return textElements.includes(elementType)
    },
    
    getElementFont(elementType, property) {
      const position = this.elementPositions[elementType]
      if (!position) return this.getDefaultFontValue(property)
      
      switch (property) {
        case 'fontFamily':
          return position.fontFamily || 'SimSun'
        case 'fontSize':
          return position.fontSize || 12
        case 'color':
          return position.color || '#000000'
        case 'fontWeight':
          return position.fontWeight || 'normal'
        default:
          return null
      }
    },
    
    getDefaultFontValue(property) {
      const defaults = {
        fontFamily: 'SimSun',
        fontSize: 12,
        color: '#000000',
        fontWeight: 'normal'
      }
      return defaults[property] || null
    },
    
    updateElementFont(elementType, property, value) {
      console.log('Updating element font:', elementType, property, value) // 调试日志
      
      this.$emit('update-element-position', {
        elementType,
        [property]: value
      })
    }
  }
}
</script>

<style scoped>
.settings-panel {
  height: 100%;
  background: white;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 10px;
  overflow-y: auto;
}

.element-properties {
  border-bottom: 1px solid #eee;
  padding-bottom: 10px;
  margin-bottom: 10px;
}

.card {
  border: 1px solid #dee2e6;
  border-radius: 4px;
}

.card-header {
  background: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
  padding: 6px 10px;
}

.card-body {
  padding: 8px 10px;
}

/* Vue手风琴样式 */
.vue-accordion {
  width: 100%;
}

.accordion-item {
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  margin-bottom: 2px;
  overflow: hidden;
}

.accordion-header {
  border-bottom: 1px solid #e0e0e0;
}

.accordion-button {
  background: #f8f9fa;
  border: none;
  padding: 8px 12px;
  text-align: left;
  width: 100%;
  font-size: 0.8rem;
  font-weight: 500;
  color: #495057;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  transition: all 0.2s ease;
}

.accordion-button:hover {
  background: #e9ecef;
}

.accordion-button:not(.collapsed) {
  background: #e7f3ff;
  color: #0066cc;
}

.accordion-button.collapsed {
  background: #f8f9fa;
  color: #495057;
}

.accordion-arrow {
  transition: transform 0.2s ease;
  font-size: 0.7rem;
}

.accordion-arrow.rotated {
  transform: rotate(180deg);
}

.accordion-collapse {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.3s ease;
}

.accordion-collapse.show {
  max-height: 500px; /* 足够大的值来容纳内容 */
}

.accordion-body {
  padding: 12px;
  font-size: 0.75rem;
  border-top: 1px solid #e0e0e0;
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

.row.g-1 {
  --bs-gutter-x: 0.25rem;
  --bs-gutter-y: 0.25rem;
}

.row.g-2 {
  --bs-gutter-x: 0.5rem;
  --bs-gutter-y: 0.5rem;
}

/* 滚动条样式 */
.settings-panel::-webkit-scrollbar {
  width: 6px;
}

.settings-panel::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.settings-panel::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.settings-panel::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

@media (max-width: 1200px) {
  .settings-panel {
    position: static;
    max-height: none;
    height: auto;
  }
}
</style> 
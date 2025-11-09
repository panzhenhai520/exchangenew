<template>
  <div class="layout-editor-panel">
    <div class="editor-header">
      <h6 class="mb-0">
        <i class="fas fa-edit me-2"></i>{{ $t('printSettings.panels.editor') }}
      </h6>
    </div>
    
    <div class="editor-content">
      <!-- 简化的内嵌布局编辑器 -->
      <div class="mini-canvas" :style="miniCanvasStyle">
        <!-- 边距可视化指示器 -->
        <div class="margin-indicator" :style="marginIndicatorStyle"></div>
        
        <div class="mini-content" :style="miniContentStyle">
          <!-- Logo区域 - 可拖拽 -->
          <div 
            v-if="shouldShowLogo"
            class="editable-element logo-element"
            :class="{ 'selected': selectedElement === 'logo' }"
            :style="getEditableElementStyle('logo')"
            @click="selectElement('logo')"
            @mousedown="startDrag($event, 'logo')"
          >
            <img :src="settings.header_settings.value.logo_data" alt="Logo" class="logo-image-editable" 
                 :style="getEditableLogoStyle()">
            <div class="element-overlay">{{ $t('printSettings.elements.logo') }}</div>
          </div>

          <!-- 标题区域 - 可拖拽 -->
          <div 
            class="editable-element title-element"
            :class="{ 'selected': selectedElement === 'title' }"
            :style="getEditableElementStyle('title')"
            @click="selectElement('title')"
            @mousedown="startDrag($event, 'title')"
          >
            <div class="title-content" :style="getEditableTitleStyle()">
              {{ getDocumentTypeName(currentDocumentType) }}
            </div>
            <div class="element-overlay">{{ $t('printSettings.elements.title') }}</div>
          </div>
          
          <!-- 副标题区域 - 独立的可拖拽元素 -->
          <div 
            class="editable-element subtitle-element"
            :class="{ 'selected': selectedElement === 'subtitle' }"
            :style="getEditableElementStyle('subtitle')"
            @click="selectElement('subtitle')"
            @mousedown="startDrag($event, 'subtitle')"
          >
            <div class="subtitle-content" :style="getEditableSubtitleStyle()">
              {{ getDocumentTypeEnglishName(currentDocumentType) }}
            </div>
            <div class="element-overlay">{{ $t('printSettings.elements.subtitle') }}</div>
          </div>

          <!-- 网点信息 - 可拖拽 -->
          <div 
            v-if="settings.header_settings.value.show_branch_info"
            class="editable-element branch-element"
            :class="{ 'selected': selectedElement === 'branch' }"
            :style="getEditableElementStyle('branch')"
            @click="selectElement('branch')"
            @mousedown="startDrag($event, 'branch')"
          >
            <div class="branch-content" :style="getEditableBranchStyle()">{{ $t('printSettings.sample.branchInfo') }}</div>
            <div class="element-overlay">{{ $t('printSettings.elements.branch') }}</div>
          </div>

          <!-- 交易内容区域 - 可拖拽 -->
          <div 
            class="editable-element content-element"
            :class="{ 'selected': selectedElement === 'content' }"
            :style="getEditableElementStyle('content')"
            @click="selectElement('content')"
            @mousedown="startDrag($event, 'content')"
          >
            <div v-if="settings.layout_settings.value.content_style === 'table'" class="content-table" :style="getEditableTableStyle()">
              <table class="table-editable" :class="{'bordered': settings.layout_settings.value.table_border}" :style="getContentFontStyle()">
                <tbody>
                  <tr v-for="(item, index) in sampleData.slice(0, 3)" :key="index">
                    <td :style="{width: settings.layout_settings.value.field_label_width + '%'}">{{ item.label }}</td>
                    <td>{{ item.value }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-else class="content-simple" :style="getContentFontStyle()">
              <div v-for="(item, index) in sampleData.slice(0, 3)" :key="index" class="content-line">
                <span v-if="settings.layout_settings.value.show_field_labels">{{ item.label }}</span>{{ item.value }}
              </div>
            </div>
            <div class="element-overlay">{{ $t('printSettings.elements.content') }}</div>
          </div>

          <!-- 签名区域 - 可拖拽 -->
          <div 
            v-if="settings.signature_settings.value.signature_style !== 'none'"
            class="editable-element signature-element"
            :class="{ 'selected': selectedElement === 'signature' }"
            :style="getEditableElementStyle('signature')"
            :key="settings.signature_settings.value.signature_style"
            @click="selectElement('signature')"
            @mousedown="startDrag($event, 'signature')"
          >
            <div class="signature-content" :style="getEditableSignatureStyle()">
              <div v-if="settings.signature_settings.value.signature_style === 'single'" 
                   class="single-signature-editable"
                   key="single-edit">
                <div class="signature-line-editable"></div>
                <div class="signature-label-editable" :style="getEditableSignatureLabelStyle()">{{ settings.signature_settings.value.single_label || '签名/Signature' }}</div>
              </div>
              <div v-else-if="settings.signature_settings.value.signature_style === 'double'" 
                   class="double-signature-editable"
                   key="double-edit">
                <div class="signature-row-editable">
                  <div class="signature-col-editable">
                    <div class="signature-line-editable"></div>
                    <div class="signature-label-editable" :style="getEditableSignatureLabelStyle()">{{ settings.signature_settings.value.left_label || 'Customer' }}</div>
                  </div>
                  <div class="signature-col-editable">
                    <div class="signature-line-editable"></div>
                    <div class="signature-label-editable" :style="getEditableSignatureLabelStyle()">{{ settings.signature_settings.value.right_label || 'Teller' }}</div>
                  </div>
                </div>
              </div>
            </div>
            <div class="element-overlay">签名区域</div>
          </div>

          <!-- 水印 - 可拖拽 -->
          <div 
            v-if="settings.advanced_settings.value.watermark_enabled"
            class="editable-element watermark-element"
            :class="{ 'selected': selectedElement === 'watermark' }"
            :style="getEditableElementStyle('watermark')"
            @click="selectElement('watermark')"
            @mousedown="startDrag($event, 'watermark')"
          >
            <div class="watermark-content" :style="getEditableWatermarkStyle()">
              {{ settings.advanced_settings.value.watermark_text }}
            </div>
            <div class="element-overlay">水印</div>
          </div>
        </div>
      </div>
      
   
    </div>
  </div>
</template>

<script>
export default {
  name: 'PrintLayoutEditor',
  props: {
    settings: {
      type: Object,
      required: true
    },
    elementPositions: {
      type: Object,
      required: true
    },
    currentDocumentType: {
      type: String,
      required: true
    },
    selectedElement: {
      type: String,
      default: null
    },
    unifiedScale: {
      type: Number,
      required: true
    },
    miniCanvasStyle: {
      type: Object,
      required: true
    },
    miniContentStyle: {
      type: Object,
      required: true
    }
  },
  emits: [
    'select-element',
    'start-drag',
    'update-element-position'
  ],
  data() {
    return {
      isDragging: false,
      dragStartX: 0,
      dragStartY: 0,
      dragStartLeft: 0,
      dragStartTop: 0,
      dragElement: null
    }
  },
  computed: {
    shouldShowLogo() {
      return this.elementPositions.logo && 
             this.elementPositions.logo.visible && 
             this.settings.header_settings.value.show_logo && 
             this.settings.header_settings.value.logo_data
    },
    
    sampleData() {
      return [
        { label: '交易编号/No:', value: 'A005202506180001' },
        { label: '交易日期/Date:', value: '2025-06-18 15:30:00' },
        { label: '交易金额/Amount:', value: '55.0 EUR' },
        { label: '兑换金额/Exchange:', value: '7.44 USD' },
        { label: '交易汇率/Rate:', value: '1 USD = 7.3932 EUR' }
      ]
    },
    
    marginIndicatorStyle() {
      const margins = this.settings.margins.value
      const scale = this.unifiedScale
      
      return {
        position: 'absolute',
        top: '0',
        left: '0',
        right: '0',
        bottom: '0',
        border: `${margins.top * scale}px solid rgba(255, 0, 0, 0.1)`,
        borderWidth: `${margins.top * scale}px ${margins.right * scale}px ${margins.bottom * scale}px ${margins.left * scale}px`,
        pointerEvents: 'none',
        zIndex: 1
      }
    }
  },
  mounted() {
    document.addEventListener('mousemove', this.handleMouseMove)
    document.addEventListener('mouseup', this.handleMouseUp)
  },
  beforeUnmount() {
    document.removeEventListener('mousemove', this.handleMouseMove)
    document.removeEventListener('mouseup', this.handleMouseUp)
  },
  methods: {
    // 统一的字体大小缩放方法 - 与PDF生成完全一致
    getScaledFontSize(fontSize) {
      if (!fontSize) return '12px'
      // 移除额外的缩放系数，确保与PDF生成一致
      const fontScale = this.unifiedScale // 直接使用统一缩放，不再乘以0.85
      return Math.max(fontSize * fontScale, 8) + 'px' // 最小字体8px
    },

    selectElement(elementType) {
      this.$emit('select-element', elementType)
    },
    
    startDrag(event, elementType) {
      event.preventDefault()
      this.isDragging = true
      this.dragElement = elementType
      this.dragStartX = event.clientX
      this.dragStartY = event.clientY
      
      const position = this.elementPositions[elementType]
      this.dragStartLeft = position ? position.left : 0
      this.dragStartTop = position ? position.top : 0
      
      this.selectElement(elementType)
      this.$emit('start-drag', { elementType, event })
    },
    
    handleMouseMove(event) {
      if (!this.isDragging || !this.dragElement) return
      
      const deltaX = event.clientX - this.dragStartX
      const deltaY = event.clientY - this.dragStartY
      
      // 转换为实际坐标 - 确保与PDF坐标系统一致
      const newLeft = this.dragStartLeft + (deltaX / this.unifiedScale)
      const newTop = this.dragStartTop + (deltaY / this.unifiedScale)
      
      // 边界检查 - 基于A4纸张实际尺寸（毫米）
      const maxLeft = 210 - 20 // A4宽度减去边距
      const maxTop = 297 - 20   // A4高度减去边距
      
      const finalLeft = Math.max(0, Math.min(newLeft, maxLeft))
      const finalTop = Math.max(0, Math.min(newTop, maxTop))
      
      this.$emit('update-element-position', {
        elementType: this.dragElement,
        left: finalLeft,
        top: finalTop
      })
    },
    
    handleMouseUp() {
      if (this.isDragging) {
        this.isDragging = false
        this.dragElement = null
      }
    },
    
    getEditableElementStyle(elementType) {
      const position = this.elementPositions[elementType]
      if (!position) return {}
      
      const style = {
        position: 'absolute',
        left: position.left * this.unifiedScale + 'px',
        top: position.top * this.unifiedScale + 'px',
        cursor: 'move',
        border: this.selectedElement === elementType ? '2px solid #007bff' : '1px dashed #ccc',
        backgroundColor: 'rgba(255, 255, 255, 0.8)',
        minHeight: '20px',
        minWidth: '50px'
      }
      
      if (position.width) {
        style.width = position.width * this.unifiedScale + 'px'
      }
      
      if (position.height) {
        style.height = position.height * this.unifiedScale + 'px'
      }
      
      // 应用字体设置 - 与预览面板保持一致
      if (position.fontFamily) {
        style.fontFamily = position.fontFamily
      }
      
      if (position.fontSize) {
        style.fontSize = this.getScaledFontSize(position.fontSize)
      }
      
      if (position.color) {
        style.color = position.color
      }
      
      if (position.fontWeight) {
        style.fontWeight = position.fontWeight
      }
      
      return style
    },
    
    getEditableLogoStyle() {
      return {
        width: this.settings.header_settings.value.logo_width * this.unifiedScale + 'px',
        height: this.settings.header_settings.value.logo_height * this.unifiedScale + 'px',
        objectFit: 'contain',
        display: 'block'
      }
    },
    
    getEditableTitleStyle() {
      const titlePosition = this.elementPositions.title
      return {
        fontSize: this.getScaledFontSize(titlePosition?.fontSize || this.settings.header_settings.value.title_size),
        fontWeight: this.settings.header_settings.value.title_bold ? 'bold' : 'normal',
        color: titlePosition?.color || this.settings.header_settings.value.title_color || '#000000',
        fontFamily: titlePosition?.fontFamily || this.settings.header_settings.value.title_font_family || 'SimHei',
        textAlign: this.settings.layout_settings.value.title_alignment
      }
    },
    
    getEditableSubtitleStyle() {
      const subtitlePosition = this.elementPositions.subtitle
      return {
        fontSize: this.getScaledFontSize(subtitlePosition?.fontSize || 10),
        color: subtitlePosition?.color || '#666',
        fontFamily: subtitlePosition?.fontFamily || 'SimSun',
        textAlign: subtitlePosition?.textAlign || 'center'
      }
    },
    
    getEditableTableStyle() {
      const tableWidth = this.settings.layout_settings.value.table_width || 160
      const tableHeight = this.settings.layout_settings.value.table_height || 80
      
      return {
        fontSize: this.getScaledFontSize(12),
        width: tableWidth * this.unifiedScale + 'px',
        height: tableHeight * this.unifiedScale + 'px',
        overflow: 'hidden'
      }
    },
    
    getEditableSignatureStyle() {
      return {
        fontSize: this.getScaledFontSize(12)
      }
    },
    
    getEditableWatermarkStyle() {
      return {
        fontSize: this.getScaledFontSize(24),
        opacity: this.settings.advanced_settings.value.watermark_opacity,
        color: '#999',
        transform: 'rotate(-45deg)',
        transformOrigin: 'center'
      }
    },
    
    getDocumentTypeName(type) {
      const names = {
        exchange: '外币兑换交易凭证',
        reversal: '交易冲正凭证',
        balance_adjustment: '余额调节单据',
        initial_balance: '余额初始化单据',
        eod_report: '日终报告'
      }
      return names[type] || '打印单据'
    },
    
    getDocumentTypeEnglishName(type) {
      const names = {
        exchange: 'FOREIGN EXCHANGE RECEIPT',
        reversal: 'REVERSAL RECEIPT',
        balance_adjustment: 'BALANCE ADJUSTMENT',
        initial_balance: 'BALANCE INITIALIZATION',
        eod_report: 'EOD REPORT'
      }
      return names[type] || 'PRINT DOCUMENT'
    },
    
    getContentFontStyle() {
      const position = this.elementPositions.content
      if (!position) return { fontSize: this.getScaledFontSize(12) }
      
      const style = {}
      
      if (position.fontFamily) {
        style.fontFamily = position.fontFamily
      }
      
      if (position.fontSize) {
        style.fontSize = this.getScaledFontSize(position.fontSize)
      }
      
      if (position.color) {
        style.color = position.color
      }
      
      if (position.fontWeight) {
        style.fontWeight = position.fontWeight
      }
      
      return style
    },
    
    getEditableBranchStyle() {
      const position = this.elementPositions.branch
      if (!position) return {}
      
      const style = {
        fontSize: this.getScaledFontSize(position.fontSize || 8),
        color: position.color || '#666',
        fontFamily: position.fontFamily || 'SimSun',
        textAlign: position.textAlign || 'center'
      }
      
      return style
    },

    getEditableSignatureLabelStyle() {
      // 签名标签字体缩放 - 与PreviewPanel保持一致，使用signature元素的fontSize设置
      const position = this.elementPositions.signature
      const baseFontSize = position?.fontSize || 8 // 默认8px，与其他内容保持一致
      const fontScale = this.unifiedScale * 0.85
      return {
        fontSize: Math.max(baseFontSize * fontScale, 6) + 'px',
        textAlign: 'center',
        marginBottom: '5px',
        marginTop: '2px'
      }
    }
  }
}
</script>

<style scoped>
.layout-editor-panel {
  height: 100%;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: white;
}

.editor-header {
  background: #f8f9fa;
  padding: 10px 15px;
  border-bottom: 1px solid #dee2e6;
  border-radius: 6px 6px 0 0;
}

.editor-header h6 {
  color: #495057;
  font-weight: 600;
}

.editor-content {
  height: calc(100% - 60px);
  overflow: hidden;
  padding: 5px;
}

.mini-canvas {
  border: 1px solid #ddd;
  position: relative;
  margin: 0 auto;
  background-color: white;
  background-image: 
    linear-gradient(rgba(0,0,0,.1) 1px, transparent 1px), 
    linear-gradient(90deg, rgba(0,0,0,.1) 1px, transparent 1px);
  overflow-y: auto;
}

.mini-content {
  position: relative;
  height: 100%;
}

.editable-element {
  border: 1px dashed #ccc;
  position: absolute;
  cursor: move;
  background: rgba(255, 255, 255, 0.8);
  transition: all 0.2s ease;
  min-height: 20px;
  min-width: 50px;
}

.editable-element:hover {
  border-color: #007bff;
  background: rgba(0, 123, 255, 0.1);
}

.editable-element.selected {
  border: 2px solid #007bff;
  background: rgba(0, 123, 255, 0.15);
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.element-overlay {
  position: absolute;
  top: -20px;
  left: 0;
  background: #007bff;
  color: white;
  padding: 2px 6px;
  font-size: 10px;
  border-radius: 3px;
  white-space: nowrap;
  opacity: 0;
  transition: opacity 0.2s ease;
  pointer-events: none;
}

.editable-element:hover .element-overlay,
.editable-element.selected .element-overlay {
  opacity: 1;
}

.table-editable {
  width: 100%;
  border-collapse: collapse;
}

.table-editable.bordered {
  border: 1px solid #dee2e6;
}

.table-editable.bordered td {
  border: 1px solid #dee2e6;
  padding: 2px 4px;
}

.content-line {
  margin-bottom: 2px;
}

.signature-row {
  display: flex;
  justify-content: space-between;
}

.signature-col {
  flex: 1;
  text-align: center;
  margin: 0 5px;
}

.signature-row-editable {
  display: flex;
  justify-content: space-between;
  gap: 5px;
}

.signature-col-editable {
  flex: 1;
  text-align: center;
  min-width: 0;
}

.single-signature-editable {
  text-align: center;
}

.signature-line-editable {
  border-bottom: 1px solid #333;
  height: 10px;
  margin: 2px auto;
  width: 80%;
}

.signature-label-editable {
  /* font-size 由内联样式控制，不使用固定值 */
  text-align: center;
  margin-top: 2px;
}

.editor-tip {
  background: #fff3cd;
  border: 1px solid #ffeaa7;
  border-radius: 4px;
  padding: 8px 12px;
  font-size: 0.8rem;
}

/* 滚动条样式 */
.editor-content::-webkit-scrollbar {
  width: 6px;
}

.editor-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.editor-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.editor-content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style> 
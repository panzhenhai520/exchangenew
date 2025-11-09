<template>
  <div class="preview-panel">
    <div class="editor-header">
      <h6 class="mb-0">
        <i class="fas fa-eye me-2"></i>{{ $t('printSettings.panels.preview') }}
      </h6>
    </div>
    
    <div class="preview-content">
      <div class="preview-container">
        <div class="preview-page" :style="previewPageStyle">
          <!-- 边距可视化指示器 -->
          <div class="margin-indicator" :style="marginIndicatorStyle"></div>
          
          <div class="preview-content" :style="previewContentStyle">
            <!-- Logo预览 -->
            <div v-if="shouldShowLogo" 
                 class="preview-logo" 
                 :style="getPreviewElementStyle('logo')">
              <img :src="settings.header_settings.value.logo_data" alt="Logo" class="logo-image" 
                   :style="logoImageStyle">
            </div>

            <!-- 标题预览 -->
            <div class="preview-title" :style="getPreviewElementStyle('title')">
              {{ getDocumentTypeName(currentDocumentType) }}
            </div>
            <div class="preview-subtitle" :style="getPreviewElementStyle('subtitle')">
              {{ getDocumentTypeEnglishName(currentDocumentType) }}
            </div>

            <!-- 网点信息预览 -->
            <div v-if="settings.header_settings.value.show_branch_info" 
                 class="preview-branch-info" 
                 :style="getPreviewElementStyle('branch')">
              {{ $t('printSettings.sample.branchInfo') }}
            </div>

            <!-- 内容预览 -->
            <div class="preview-body" :style="getPreviewElementStyle('content')">
              <!-- 表格样式 -->
              <div v-if="settings.layout_settings.value.content_style === 'table'" 
                   class="preview-table" 
                   :style="previewTableStyle">
                <table class="table table-sm" :class="{'table-bordered': settings.layout_settings.value.table_border}" 
                       :style="getContentStyle()">
                  <tbody>
                    <tr v-for="(item, index) in sampleData" :key="index">
                      <td :style="{width: settings.layout_settings.value.field_label_width + '%'}">{{ item.label }}</td>
                      <td>{{ item.value }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              
              <!-- 简单样式 -->
              <div v-else class="preview-simple" :style="getContentStyle()">
                <div v-for="(item, index) in sampleData" :key="index" class="preview-line">
                  <span v-if="settings.layout_settings.value.show_field_labels">{{ item.label }}</span>{{ item.value }}
                </div>
              </div>
            </div>

            <!-- 签名预览 -->
            <div v-if="settings.signature_settings.value.signature_style !== 'none'" 
                 class="preview-signature" 
                 :style="getPreviewElementStyle('signature')"
                 :key="settings.signature_settings.value.signature_style">
              <!-- 单签名 -->
              <div v-if="settings.signature_settings.value.signature_style === 'single'" 
                   class="single-signature"
                   key="single">
                <div class="signature-line" :style="singleSignatureLineStyle"></div>
                <div class="signature-label" :style="getSignatureLabelStyle()">{{ settings.signature_settings.value.single_label || '签名/Signature' }}</div>
                <div v-if="settings.signature_settings.value.show_date_line" class="date-line" :style="getDateLineStyle()">
                  日期：_______________
                </div>
              </div>
              
              <!-- 双签名 -->
              <div v-else-if="settings.signature_settings.value.signature_style === 'double'" 
                   class="double-signature"
                   key="double">
                <div class="signature-container">
                  <div class="signature-item">
                    <div class="signature-line" :style="doubleSignatureLineStyle"></div>
                    <div class="signature-label" :style="getSignatureLabelStyle()">{{ settings.signature_settings.value.left_label || 'Customer' }}</div>
                    <div v-if="settings.signature_settings.value.show_date_line" class="date-line" :style="getDateLineStyle()">
                      日期：_______________
                    </div>
                  </div>
                  <div class="signature-item">
                    <div class="signature-line" :style="doubleSignatureLineStyle"></div>
                    <div class="signature-label" :style="getSignatureLabelStyle()">{{ settings.signature_settings.value.right_label || 'Teller' }}</div>
                    <div v-if="settings.signature_settings.value.show_date_line" class="date-line" :style="getDateLineStyle()">
                      日期：_______________
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 水印预览 -->
            <div v-if="settings.advanced_settings.value.watermark_enabled" 
                 class="preview-watermark" 
                 :style="getPreviewElementStyle('watermark')">
              {{ settings.advanced_settings.value.watermark_text }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PrintPreviewPanel',
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
    unifiedScale: {
      type: Number,
      required: true
    },
    previewPageStyle: {
      type: Object,
      required: true
    },
    previewContentStyle: {
      type: Object,
      required: true
    }
  },
  computed: {
    shouldShowLogo() {
      return this.elementPositions.logo && 
             this.elementPositions.logo.visible && 
             this.settings.header_settings.value.show_logo && 
             this.settings.header_settings.value.logo_data
    },
    
    logoImageStyle() {
      return {
        width: this.settings.header_settings.value.logo_width * this.unifiedScale + 'px',
        height: this.settings.header_settings.value.logo_height * this.unifiedScale + 'px',
        objectFit: 'contain',
        display: 'block'
      }
    },
    
    signatureLineStyle() {
      return {
        width: this.settings.signature_settings.value.signature_width * 0.5 + 'px'
      }
    },
    
    singleSignatureLineStyle() {
      return {
        width: (this.settings.signature_settings.value.signature_width || 150) * 0.5 + 'px',
        margin: '0 auto'
      }
    },
    
    doubleSignatureLineStyle() {
      return {
        width: (this.settings.signature_settings.value.signature_width || 150) * 0.3 + 'px',
        margin: '0 auto'
      }
    },
    
    previewTableStyle() {
      const tableWidth = this.settings.layout_settings.value.table_width || 160
      const tableHeight = this.settings.layout_settings.value.table_height || 80
      
      return {
        textAlign: this.settings.layout_settings.value.table_alignment,
        width: tableWidth * this.unifiedScale + 'px',
        height: tableHeight * this.unifiedScale + 'px',
        overflow: 'hidden'
      }
    },
    
    sampleData() {
      return [
        { label: this.$t('printSettings.sample.transactionNo'), value: 'A005202506180001' },
        { label: this.$t('printSettings.sample.transactionDate'), value: '2025-06-18 15:30:00' },
        { label: this.$t('printSettings.sample.amount'), value: '55.0 EUR' },
        { label: this.$t('printSettings.sample.exchange'), value: '7.44 USD' },
        { label: this.$t('printSettings.sample.rate'), value: '1 USD = 7.3932 EUR' },
        { label: this.$t('printSettings.sample.customerName'), value: '张三' },
        { label: this.$t('printSettings.sample.idNumber'), value: '123456' },
        { label: this.$t('printSettings.sample.purpose'), value: '商务' },
        { label: this.$t('printSettings.sample.remarks'), value: '654321' }
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
  methods: {
    getContentStyle() {
      const position = this.elementPositions.content
      if (!position) return {}
      
      const style = {}
      
      // 只应用字体设置，不包含定位
      if (position.fontFamily) {
        style.fontFamily = position.fontFamily
      }
      
      if (position.fontSize) {
        // 优化字体大小缩放，使其更接近实际打印效果
        const fontScale = this.unifiedScale * 0.85 // 字体缩放比例稍小于整体缩放
        style.fontSize = Math.max(position.fontSize * fontScale, 8) + 'px' // 最小字体8px
      }
      
      if (position.color) {
        style.color = position.color
      }
      
      if (position.fontWeight) {
        style.fontWeight = position.fontWeight
      }
      
      return style
    },
    
    getPreviewElementStyle(elementType) {
      const position = this.elementPositions[elementType]
      if (!position) return {}
      
      const style = {
        position: 'absolute',
        left: position.left * this.unifiedScale + 'px',
        top: position.top * this.unifiedScale + 'px'
      }
      
      if (position.width) {
        style.width = position.width * this.unifiedScale + 'px'
      }
      
      if (position.height) {
        style.height = position.height * this.unifiedScale + 'px'
      }
      
      if (position.textAlign) {
        style.textAlign = position.textAlign
      }
      
      // 应用字体设置
      if (position.fontFamily) {
        style.fontFamily = position.fontFamily
      }
      
      if (position.fontSize) {
        // 与PDF生成保持完全一致的字体大小缩放
        const fontScale = this.unifiedScale // 移除0.85系数，确保与PDF一致
        style.fontSize = Math.max(position.fontSize * fontScale, 8) + 'px' // 最小字体8px
      }
      
      if (position.color) {
        style.color = position.color
      }
      
      if (position.fontWeight) {
        style.fontWeight = position.fontWeight
      }
      
      return style
    },
    
    getDocumentTypeName(type) {
      const names = {
        exchange: '外币兑换交易凭证',
        reversal: '交易冲正凭证',
        balance_adjustment: '余额调节单据',
        balance_initialization: '余额初始化单据',
        eod_report: '日终报告'
      }
      return names[type] || '打印单据'
    },
    
    getDocumentTypeEnglishName(type) {
      const names = {
        exchange: 'FOREIGN EXCHANGE TRANSACTION RECEIPT',
        reversal: 'TRANSACTION REVERSAL RECEIPT',
        balance_adjustment: 'BALANCE ADJUSTMENT RECEIPT',
        balance_initialization: 'BALANCE INITIALIZATION RECEIPT',
        eod_report: 'END OF DAY REPORT'
      }
      return names[type] || 'PRINT DOCUMENT'
    },

    getSignatureLabelStyle() {
      // 签名标签字体缩放 - 与PDF生成保持一致
      const position = this.elementPositions.signature
      const baseFontSize = position?.fontSize || 8 // 默认8px，与其他内容保持一致
      const fontScale = this.unifiedScale // 移除0.85系数，确保与PDF一致
      return {
        fontSize: Math.max(baseFontSize * fontScale, 6) + 'px',
        textAlign: 'center',
        marginBottom: '5px',
        marginTop: '2px'
      }
    },

    getDateLineStyle() {
      // 日期行字体缩放 - 与PDF生成保持一致
      const fontScale = this.unifiedScale // 移除0.85系数，确保与PDF一致
      return {
        fontSize: Math.max(8 * fontScale, 5) + 'px',
        textAlign: 'center',
        marginTop: '5px'
      }
    }
  }
}
</script>

<style scoped>
.preview-panel {
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

.preview-content {
  padding: 5px;
  height: calc(100% - 60px);
  overflow: hidden;
}

.preview-container {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  min-height: 100%;
  padding: 0;
  overflow-y: auto;
}

.preview-page {
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  margin: 0 auto;
  position: relative;
}

.preview-content {
  position: relative;
  height: 100%;
}

.preview-title {
  font-weight: bold;
  font-size: 16px;
  text-align: center;
  margin-bottom: 5px;
  /* 基础字体大小，实际大小由内联样式控制 */
}

.preview-subtitle {
  font-size: 12px;
  text-align: center;
  color: #666;
  margin-bottom: 15px;
  /* 基础字体大小，实际大小由内联样式控制 */
}

.preview-branch-info {
  text-align: center;
  font-size: 12px;
  margin-bottom: 15px;
  color: #333;
  /* 基础字体大小，实际大小由内联样式控制 */
}

.preview-table table {
  background: white;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.preview-table table.table-bordered {
  border: 1px solid #dee2e6;
}

.preview-table table.table-bordered td {
  border-color: #dee2e6;
  padding: 4px 8px;
}

.preview-simple .preview-line {
  margin-bottom: 5px;
}

.preview-signature {
  margin-top: 20px;
}

.single-signature {
  text-align: center;
}

.double-signature {
  width: 100%;
}

.signature-container {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
}

.signature-item {
  flex: 1;
  text-align: center;
  min-width: 0;
}

.signature-line {
  border-bottom: 1px solid #333;
  height: 20px;
  margin: 5px auto;
}

.signature-label {
  text-align: center;
  /* font-size 由内联样式控制，不使用固定值 */
  margin-bottom: 5px;
  margin-top: 2px;
}

.date-line {
  /* font-size 由内联样式控制，不使用固定值 */
  text-align: center;
  margin-top: 5px;
}

.double-signature .row {
  margin: 0;
}

.double-signature .col-6 {
  padding: 0 10px;
}

.preview-watermark {
  font-family: 'Arial', sans-serif;
  letter-spacing: 2px;
  opacity: 0.3;
  color: #999;
  font-size: 24px;
  font-weight: bold;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) rotate(-45deg);
  pointer-events: none;
  z-index: 1;
}

.logo-image {
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

/* 滚动条样式 */
.preview-content::-webkit-scrollbar {
  width: 6px;
}

.preview-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.preview-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.preview-content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style> 
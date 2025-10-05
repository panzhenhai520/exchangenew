<template>
  <div class="layout-editor-container">
    <div class="editor-header">
      <h5 class="mb-0">
        <font-awesome-icon :icon="['fas', 'edit']" class="me-2" />
        可视化布局编辑器
      </h5>
      <div class="editor-actions">
        <button type="button" class="btn btn-success btn-sm me-2" @click="saveLayout">
          <font-awesome-icon :icon="['fas', 'save']" class="me-1" />
          应用布局
        </button>
        <button type="button" class="btn btn-outline-secondary btn-sm me-2" @click="resetLayout">
          <font-awesome-icon :icon="['fas', 'undo']" class="me-1" />
          重置
        </button>
        <button type="button" class="btn btn-outline-danger btn-sm" @click="closeEditor">
          <font-awesome-icon :icon="['fas', 'times']" class="me-1" />
          关闭
        </button>
      </div>
    </div>

    <div class="editor-body">
      <div class="editor-canvas" :style="canvasStyle" ref="canvas">
        <!-- Logo元素 -->
        <div 
          v-if="settings.header_settings.show_logo && settings.header_settings.logo_data"
          class="draggable-element logo-element"
          :class="{ 'selected': selectedElement === 'logo' }"
          :style="getElementStyle('logo')"
          @mousedown="startDrag($event, 'logo')"
          @click="selectElement('logo')"
        >
          <div class="element-content">
            <img :src="settings.header_settings.logo_data" alt="Logo" class="logo-image">
          </div>
          <div class="drag-handle">
            <font-awesome-icon :icon="['fas', 'arrows-alt']" />
          </div>
        </div>

        <!-- 标题元素 -->
        <div 
          class="draggable-element title-element"
          :class="{ 'selected': selectedElement === 'title' }"
          :style="getElementStyle('title')"
          @mousedown="startDrag($event, 'title')"
          @click="selectElement('title')"
        >
          <div class="element-content">
            <h5 class="mb-1">TEST - 外汇兑换单据</h5>
            <small>FOREIGN EXCHANGE TRANSACTION RECEIPT</small>
          </div>
          <div class="drag-handle">
            <font-awesome-icon :icon="['fas', 'arrows-alt']" />
          </div>
        </div>

        <!-- 交易编号 -->
        <div 
          class="draggable-element field-element"
          :class="{ 'selected': selectedElement === 'transactionNo' }"
          :style="getElementStyle('transactionNo')"
          @mousedown="startDrag($event, 'transactionNo')"
          @click="selectElement('transactionNo')"
        >
          <div class="element-content">
            <span v-if="settings.layout_settings.show_field_labels" class="field-label">单据号：</span>
            <span class="field-value">EX2024010100001</span>
          </div>
          <div class="drag-handle">
            <font-awesome-icon :icon="['fas', 'arrows-alt']" />
          </div>
        </div>

        <!-- 交易时间 -->
        <div 
          class="draggable-element field-element"
          :class="{ 'selected': selectedElement === 'transactionTime' }"
          :style="getElementStyle('transactionTime')"
          @mousedown="startDrag($event, 'transactionTime')"
          @click="selectElement('transactionTime')"
        >
          <div class="element-content">
            <span v-if="settings.layout_settings.show_field_labels" class="field-label">交易时间：</span>
            <span class="field-value">2024-01-01 10:30:00</span>
          </div>
          <div class="drag-handle">
            <font-awesome-icon :icon="['fas', 'arrows-alt']" />
          </div>
        </div>

        <!-- 币种信息 -->
        <div 
          class="draggable-element field-element"
          :class="{ 'selected': selectedElement === 'currency' }"
          :style="getElementStyle('currency')"
          @mousedown="startDrag($event, 'currency')"
          @click="selectElement('currency')"
        >
          <div class="element-content">
            <span v-if="settings.layout_settings.show_field_labels" class="field-label">币种：</span>
            <span class="field-value">USD - 美元</span>
          </div>
          <div class="drag-handle">
            <font-awesome-icon :icon="['fas', 'arrows-alt']" />
          </div>
        </div>

        <!-- 金额信息 -->
        <div 
          class="draggable-element field-element"
          :class="{ 'selected': selectedElement === 'amount' }"
          :style="getElementStyle('amount')"
          @mousedown="startDrag($event, 'amount')"
          @click="selectElement('amount')"
        >
          <div class="element-content">
            <span v-if="settings.layout_settings.show_field_labels" class="field-label">金额：</span>
            <span class="field-value">1,000.00</span>
          </div>
          <div class="drag-handle">
            <font-awesome-icon :icon="['fas', 'arrows-alt']" />
          </div>
        </div>

        <!-- 签名区域 -->
        <div 
          v-if="settings.signature_settings && settings.signature_settings.signature_style !== 'none'"
          class="draggable-element signature-element"
          :class="{ 'selected': selectedElement === 'signature' }"
          :style="getElementStyle('signature')"
          @mousedown="startDrag($event, 'signature')"
          @click="selectElement('signature')"
        >
          <div class="element-content">
            <div class="row g-2">
              <div class="col-6">
                <div class="signature-box text-center">
                  <div>客户签名/Customer</div>
                  <div class="signature-line"></div>
                  <small>日期/Date:_____________</small>
                </div>
              </div>
              <div class="col-6">
                <div class="signature-box text-center">
                  <div>柜员签名/Teller</div>
                  <div class="signature-line"></div>
                  <small>日期/Date:_____________</small>
                </div>
              </div>
            </div>
          </div>
          <div class="drag-handle">
            <font-awesome-icon :icon="['fas', 'arrows-alt']" />
          </div>
        </div>

        <!-- 底部说明 -->
        <div 
          class="draggable-element notice-element"
          :class="{ 'selected': selectedElement === 'notice' }"
          :style="getElementStyle('notice')"
          @mousedown="startDrag($event, 'notice')"
          @click="selectElement('notice')"
        >
          <div class="element-content">
            <div class="small">注：此凭证为交易有效凭据，请妥善保管。</div>
            <div class="small">Note: This is valid proof of transaction. Please keep it safe.</div>
          </div>
          <div class="drag-handle">
            <font-awesome-icon :icon="['fas', 'arrows-alt']" />
          </div>
        </div>
      </div>

      <!-- 元素属性面板 -->
      <div v-if="selectedElement" class="element-properties">
        <div class="card">
          <div class="card-header py-2">
            <h6 class="mb-0">
              <font-awesome-icon :icon="['fas', 'cog']" class="me-2" />
              {{ getElementName(selectedElement) }} 属性设置
            </h6>
          </div>
          <div class="card-body py-2">
            <div class="row g-2">
              <div class="col-3">
                <label class="form-label-sm">左边距</label>
                <div class="input-group input-group-sm">
                  <input 
                    type="number" 
                    class="form-control" 
                    :value="elementPositions[selectedElement]?.left || 0"
                    @input="updateElementPosition(selectedElement, 'left', $event.target.value)"
                    min="0"
                    step="1"
                  >
                  <span class="input-group-text">px</span>
                </div>
              </div>
              <div class="col-3">
                <label class="form-label-sm">上边距</label>
                <div class="input-group input-group-sm">
                  <input 
                    type="number" 
                    class="form-control" 
                    :value="elementPositions[selectedElement]?.top || 0"
                    @input="updateElementPosition(selectedElement, 'top', $event.target.value)"
                    min="0"
                    step="1"
                  >
                  <span class="input-group-text">px</span>
                </div>
              </div>
              <div class="col-3">
                <label class="form-label-sm">宽度</label>
                <div class="input-group input-group-sm">
                  <input 
                    type="number" 
                    class="form-control" 
                    :value="elementPositions[selectedElement]?.width || ''"
                    @input="updateElementPosition(selectedElement, 'width', $event.target.value)"
                    min="50"
                    step="10"
                    placeholder="auto"
                  >
                  <span class="input-group-text">px</span>
                </div>
              </div>
              <div class="col-3">
                <label class="form-label-sm">对齐方式</label>
                <select 
                  class="form-select form-select-sm"
                  :value="elementPositions[selectedElement]?.textAlign || 'left'"
                  @change="updateElementPosition(selectedElement, 'textAlign', $event.target.value)"
                >
                  <option value="left">左对齐</option>
                  <option value="center">居中</option>
                  <option value="right">右对齐</option>
                </select>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="editor-footer">
      <div class="alert alert-info py-2 mb-0">
        <div class="d-flex align-items-center">
          <font-awesome-icon :icon="['fas', 'lightbulb']" class="me-2" />
          <span class="small">
            <strong>使用提示：</strong>
            点击元素选中，拖拽移动位置，或在属性面板中精确调整数值。调整完成后点击"应用布局"保存更改。
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PrintLayoutEditorView',
  data() {
    return {
      settings: {
        paper_size: { width: 210, height: 297 },
        margins: { top: 25, bottom: 10, left: 28, right: 10 },
        font_settings: { family: 'SimHei', size: 8 },
        header_settings: { show_logo: false, show_branch_info: true, logo_data: null },
        layout_settings: { show_field_labels: true, content_style: 'simple' },
        signature_settings: { signature_style: 'double' }
      },
      elementPositions: {
        logo: { top: 3, left: 0, width: 50, textAlign: 'center' },
        title: { left: 101, textAlign: 'center', top: 10, width: null },
        transactionNo: { left: 322, textAlign: 'left', top: 61, width: 300 },
        transactionTime: { left: 0, textAlign: 'left', top: 70, width: 300 },
        currency: { left: 10, textAlign: 'left', top: 100, width: 300 },
        amount: { left: 10, textAlign: 'left', top: 130, width: 300 },
        signature: { left: 10, textAlign: 'center', top: 200, width: null },
        notice: { left: 10, textAlign: 'center', top: 280, width: null }
      },
      selectedElement: null,
      isDragging: false,
      dragStartX: 0,
      dragStartY: 0,
      dragStartLeft: 0,
      dragStartTop: 0
    };
  },
  computed: {
    canvasStyle() {
      const { width, height } = this.settings.paper_size;
      const scale = Math.min(600 / width, 800 / height, 1);
      
      return {
        width: `${width * scale}px`,
        height: `${height * scale}px`,
        transform: `scale(${scale})`,
        transformOrigin: 'top left',
        backgroundColor: 'white',
        border: '1px solid #ddd',
        position: 'relative',
        margin: '0 auto',
        backgroundImage: 
          'linear-gradient(rgba(0,0,0,.05) 1px, transparent 1px), ' +
          'linear-gradient(90deg, rgba(0,0,0,.05) 1px, transparent 1px)',
        backgroundSize: '20px 20px'
      };
    }
  },
  mounted() {
    this.loadSettingsFromURL();
    document.addEventListener('mousemove', this.onDrag);
    document.addEventListener('mouseup', this.stopDrag);
    
    // 监听窗口关闭事件
    window.addEventListener('beforeunload', () => {
      if (window.opener) {
        window.opener.postMessage({ type: 'editor-closed' }, window.location.origin);
      }
    });
  },
  beforeUnmount() {
    document.removeEventListener('mousemove', this.onDrag);
    document.removeEventListener('mouseup', this.stopDrag);
  },
  methods: {
    loadSettingsFromURL() {
      const urlParams = new URLSearchParams(window.location.search);
      const settingsParam = urlParams.get('settings');
      
      if (settingsParam) {
        try {
          const parsedSettings = JSON.parse(settingsParam);
          this.settings = { ...this.settings, ...parsedSettings };
          if (parsedSettings.element_positions) {
            this.elementPositions = { ...this.elementPositions, ...parsedSettings.element_positions };
          }
        } catch (error) {
          console.error('解析设置参数失败:', error);
        }
      }
    },

    getElementStyle(element) {
      const pos = this.elementPositions[element] || {};
      const style = {
        position: 'absolute',
        left: `${pos.left || 0}px`,
        top: `${pos.top || 0}px`,
        textAlign: pos.textAlign || 'left',
        zIndex: this.selectedElement === element ? 1000 : 1
      };
      
      if (pos.width) {
        style.width = `${pos.width}px`;
      }
      
      return style;
    },

    selectElement(element) {
      this.selectedElement = element;
    },

    startDrag(event, element) {
      event.preventDefault();
      this.isDragging = true;
      this.selectedElement = element;
      
      this.dragStartX = event.clientX;
      this.dragStartY = event.clientY;
      this.dragStartLeft = this.elementPositions[element]?.left || 0;
      this.dragStartTop = this.elementPositions[element]?.top || 0;
      
      document.body.style.userSelect = 'none';
    },

    onDrag(event) {
      if (!this.isDragging || !this.selectedElement) return;
      
      const deltaX = event.clientX - this.dragStartX;
      const deltaY = event.clientY - this.dragStartY;
      
      const newLeft = Math.max(0, this.dragStartLeft + deltaX);
      const newTop = Math.max(0, this.dragStartTop + deltaY);
      
      this.updateElementPosition(this.selectedElement, 'left', newLeft);
      this.updateElementPosition(this.selectedElement, 'top', newTop);
    },

    stopDrag() {
      this.isDragging = false;
      document.body.style.userSelect = '';
    },

    updateElementPosition(element, property, value) {
      if (!this.elementPositions[element]) {
        this.elementPositions[element] = {};
      }
      
      this.elementPositions[element][property] = 
        property === 'width' && value === '' ? null : parseInt(value) || 0;
    },

    getElementName(element) {
      const names = {
        logo: 'Logo图标',
        title: '标题区域',
        transactionNo: '交易编号',
        transactionTime: '交易时间',
        currency: '币种信息',
        amount: '金额信息',
        signature: '签名区域',
        notice: '底部说明'
      };
      return names[element] || element;
    },

    saveLayout() {
      // 发送布局更新消息给父窗口
      if (window.opener) {
        window.opener.postMessage({
          type: 'layout-updated',
          positions: this.elementPositions
        }, window.location.origin);
        
        this.$toast.success(this.$t('printSettings.messages.layoutApplied'));
      }
    },

    resetLayout() {
      if (!confirm('确定要重置布局为默认位置吗？')) {
        return;
      }
      
      this.elementPositions = {
        logo: { top: 3, left: 0, width: 50, textAlign: 'center' },
        title: { left: 101, textAlign: 'center', top: 10, width: null },
        transactionNo: { left: 322, textAlign: 'left', top: 61, width: 300 },
        transactionTime: { left: 0, textAlign: 'left', top: 70, width: 300 },
        currency: { left: 10, textAlign: 'left', top: 100, width: 300 },
        amount: { left: 10, textAlign: 'left', top: 130, width: 300 },
        signature: { left: 10, textAlign: 'center', top: 200, width: null },
        notice: { left: 10, textAlign: 'center', top: 280, width: null }
      };
      this.selectedElement = null;
    },

    closeEditor() {
      window.close();
    }
  }
};
</script>

<style scoped>
.layout-editor-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f8f9fa;
}

.editor-header {
  background: white;
  border-bottom: 1px solid #dee2e6;
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.editor-body {
  flex: 1;
  padding: 1rem;
  overflow: auto;
  position: relative;
}

.editor-canvas {
  margin: 0 auto;
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.draggable-element {
  cursor: move;
  transition: all 0.2s ease;
  user-select: none;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.draggable-element:hover {
  box-shadow: 0 4px 8px rgba(0,0,0,0.2);
  transform: translateY(-1px);
}

.draggable-element.selected {
  border: 2px solid #007bff !important;
  box-shadow: 0 0 0 3px rgba(0,123,255,0.25);
  z-index: 1000 !important;
}

.drag-handle {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 16px;
  height: 16px;
  background-color: #007bff;
  border: 2px solid white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: move;
  opacity: 0;
  transition: opacity 0.2s ease;
  font-size: 8px;
  color: white;
}

.draggable-element:hover .drag-handle,
.draggable-element.selected .drag-handle {
  opacity: 1;
}

.element-content {
  padding: 6px;
  background: white;
  border-radius: 4px;
  min-height: 20px;
  border: 1px solid #dee2e6;
}

.field-element .element-content {
  display: flex;
  align-items: center;
  gap: 6px;
}

.field-label {
  font-weight: 600;
  color: #495057;
  white-space: nowrap;
  font-size: 12px;
}

.field-value {
  color: #212529;
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

.title-element .element-content h5 {
  margin: 0;
  font-size: 14px;
  font-weight: bold;
  color: #212529;
}

.title-element .element-content small {
  font-size: 10px;
  color: #6c757d;
  display: block;
  margin-top: 2px;
}

.signature-element .signature-box {
  border: 1px solid #dee2e6;
  border-radius: 4px;
  padding: 6px;
  margin: 2px;
  min-height: 40px;
  background: #f8f9fa;
  font-size: 10px;
}

.signature-element .signature-line {
  border-bottom: 1px solid #666;
  height: 12px;
  margin: 4px 0 2px;
}

.notice-element .element-content {
  text-align: center;
  font-size: 10px;
  color: #6c757d;
  font-style: italic;
}

.logo-image {
  max-width: 80px;
  max-height: 40px;
  object-fit: contain;
}

.element-properties {
  position: fixed;
  bottom: 20px;
  left: 20px;
  right: 20px;
  z-index: 1001;
}

.element-properties .card {
  border: 1px solid #007bff;
  box-shadow: 0 4px 8px rgba(0,123,255,0.2);
}

.element-properties .card-header {
  background-color: rgba(0,123,255,0.1);
  border-bottom: 1px solid #007bff;
}

.editor-footer {
  background: white;
  border-top: 1px solid #dee2e6;
  padding: 0.75rem 1rem;
}

.form-label-sm {
  font-size: 0.875rem;
  margin-bottom: 0.25rem;
}
</style> 
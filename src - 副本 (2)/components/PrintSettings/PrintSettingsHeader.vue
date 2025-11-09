<template>
  <div class="print-settings-header">
    <!-- 页面标题和语言切换 -->
    <div class="page-header">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h2 class="mb-0">{{ $t('printSettings.title') }}</h2>
        <!-- 语言切换器 -->
        <div class="language-switcher">
          <select 
            :value="currentLanguage" 
            @change="$emit('language-change', $event.target.value)" 
            class="form-select form-select-sm" 
            style="width: auto;"
          >
            <option value="zh-CN">中文</option>
            <option value="en-US">English</option>
            <option value="th-TH">ไทย</option>
          </select>
        </div>
      </div>
      <p class="text-muted">{{ $t('printSettings.subtitle') }}</p>
    </div>

    <!-- 单据类型选择器 -->
    <div class="document-type-selector mb-4">
      <div class="row align-items-center">
        <div class="col-md-3">
          <label class="form-label">{{ $t('printSettings.documentType') }}</label>
          <select 
            :value="currentDocumentType" 
            @change="$emit('document-type-change', $event.target.value)" 
            class="form-select"
          >
            <option value="exchange">{{ $t('printSettings.documentTypes.exchange') }}</option>
            <option value="reversal">{{ $t('printSettings.documentTypes.reversal') }}</option>
            <option value="balance_adjustment">{{ $t('printSettings.documentTypes.balance_adjustment') }}</option>
            <option value="initial_balance">{{ $t('printSettings.documentTypes.initial_balance') }}</option>
            <option value="eod_report">{{ $t('printSettings.documentTypes.eod_report') }}</option>
          </select>
        </div>
        
        <div class="col-md-3">
          <label class="form-label">{{ $t('printSettings.layoutSelect') }}</label>
          <div class="d-flex">
            <select 
              :value="currentLayoutName" 
              @change="$emit('layout-change', $event.target.value)" 
              class="form-select me-2"
            >
              <option v-for="layout in availableLayouts" :key="layout.layout_name || layout.name" :value="layout.layout_name || layout.name">
                {{ layout.layout_name || layout.name }}{{ layout.is_default ? ' ⭐' : '' }}
              </option>
            </select>
            
            <!-- 布局管理按钮 -->
            <button @click="$emit('show-layout-manager')" class="btn btn-outline-primary layout-manager-btn" title="布局管理">
              <font-awesome-icon :icon="['fas', 'plus']" />
            </button>
          </div>
        </div>
        
        <div class="col-md-6">
          <!-- 纸张信息显示 -->
          <div class="paper-info-display mb-2" style="font-size: 0.75rem; color: #666;">
            <strong>{{ $t('printSettings.tips.paperInfo') }}</strong>
            {{ $t('printSettings.tips.actualSize') }} {{ paperInfo.width }}×{{ paperInfo.height }}mm 
            ({{ paperInfo.orientation === 'portrait' ? $t('printSettings.paper.portrait') : $t('printSettings.paper.landscape') }}) 
            → {{ $t('printSettings.tips.displaySize') }} {{ Math.round(paperInfo.displayWidth) }}×{{ Math.round(paperInfo.displayHeight) }}px 
            | {{ $t('printSettings.tips.scale') }} {{ Math.round(paperInfo.scale * 100) }}% 
            | {{ $t('printSettings.tips.ratio') }}1:{{ Math.round(1/paperInfo.scale * 10)/10 }}
            <span v-if="paperInfo.orientation === 'portrait'" style="color: blue;"> 📄</span>
            <span v-else style="color: green;"> 📰</span>
          </div>
          
          <div class="d-flex justify-content-end">
            <button @click="$emit('save-settings')" class="btn btn-primary btn-sm save-button" :disabled="saving">
              <font-awesome-icon :icon="['fas', 'save']" />
              {{ saving ? $t('printSettings.saving') : $t('printSettings.save') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PrintSettingsHeader',
  props: {
    currentLanguage: {
      type: String,
      required: true
    },
    currentDocumentType: {
      type: String,
      required: true
    },
    currentLayoutName: {
      type: String,
      required: true
    },
    availableLayouts: {
      type: Array,
      default: () => []
    },
    paperInfo: {
      type: Object,
      required: true
    },
    saving: {
      type: Boolean,
      default: false
    }
  },
  emits: [
    'language-change',
    'document-type-change', 
    'layout-change',
    'show-layout-manager',
    'save-settings'
  ],
  methods: {
    getLayoutKey(layoutName) {
      return layoutName.toLowerCase().replace(/[^a-z0-9]/g, '_')
    }
  }
}
</script>

<style scoped>
.print-settings-header {
  margin-bottom: 20px;
}

.page-header h2 {
  color: #333;
  font-weight: 600;
}

.language-switcher select {
  min-width: 100px;
}

.paper-info-display {
  background: #f8f9fa;
  padding: 8px 12px;
  border-radius: 4px;
  border: 1px solid #e9ecef;
}

.paper-info-display strong {
  color: #007bff;
}

.document-type-selector .row {
  align-items: end;
}

.layout-manager-btn {
  min-width: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.save-button {
  margin-right: 20px;
}

@media (max-width: 768px) {
  .document-type-selector .row > div {
    width: 100% !important;
    margin-bottom: 15px;
  }
  
  .document-type-selector .text-end {
    text-align: left !important;
  }
  
  .paper-info-display {
    font-size: 0.7rem !important;
  }
}
</style> 
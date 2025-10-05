<template>
  <div class="print-settings-container" style="margin: 0; padding: 0;">
    <!-- 调试信息 -->
    <div v-if="!componentsLoaded" style="padding: 20px; text-align: center;">
      <p>正在加载打印设置组件...</p>
    </div>
    

    
    <div v-else>
      <!-- 头部组件 -->
      <PrintSettingsHeader
        :current-language="currentLanguage"
        :current-document-type="currentDocumentType"
        :current-layout-name="currentLayoutName"
        :available-layouts="availableLayouts"
        :paper-info="paperInfo"
        :saving="saving"
        @language-change="changeLanguage"
        @document-type-change="loadSettingsForDocumentType"
        @layout-change="loadLayoutSettings"
        @show-layout-manager="openLayoutManager"
        @save-settings="saveSettings"
      />

      <div class="row" style="margin: 0; display: flex; width: 100%;">
        <!-- 左栏：预览页面(36%) -->
        <div style="width: 36%; padding: 0 5px; flex-shrink: 0;">
          <PrintPreviewPanel
            :settings="settings"
            :element-positions="elementPositions"
            :current-document-type="currentDocumentType"
            :unified-scale="unifiedScale"
            :preview-page-style="previewPageStyle"
            :preview-content-style="previewContentStyle"
          />
        </div>

        <!-- 中栏：布局编辑器(36%) -->
        <div style="width: 36%; padding: 0 5px; flex-shrink: 0;">
          <PrintLayoutEditor
            :settings="settings"
            :element-positions="elementPositions"
            :current-document-type="currentDocumentType"
            :selected-element="selectedElement"
            :unified-scale="unifiedScale"
            :mini-canvas-style="miniCanvasStyle"
            :mini-content-style="miniContentStyle"
            @select-element="selectedElement = $event"
            @start-drag="handleStartDrag"
            @update-element-position="handleUpdateElementPosition"
          />
        </div>

        <!-- 右栏：属性设置面板(28%) -->
        <div style="width: 28%; padding: 0 5px; flex-shrink: 0;">
          <PrintSettingsPanel
            :settings="settings"
            :element-positions="elementPositions"
            :selected-element="selectedElement"
            @update-settings="handleUpdateSettings"
            @update-element-position="handleUpdateElementPosition"
          />
        </div>
      </div>

      <div class="col-md-6 text-end">
        <!-- 纸张信息显示 -->
        <div class="paper-info-display mb-2" style="font-size: 0.75rem; color: #666; text-align: left;">
          <strong>{{ $t('printSettings.tips.paperInfo') }}</strong>
          {{ $t('printSettings.tips.actualSize') }} {{ paperDimensions.width }}×{{ paperDimensions.height }}mm 
          ({{ settings.paper_size.value.orientation === 'portrait' ? $t('printSettings.paper.portrait') : $t('printSettings.paper.landscape') }}) 
          → {{ $t('printSettings.tips.displaySize') }} {{ Math.round(displayDimensions.width) }}×{{ Math.round(displayDimensions.height) }}px 
          | {{ $t('printSettings.tips.scale') }} {{ Math.round(unifiedScale * 100) }}% 
          | {{ $t('printSettings.tips.ratio') }}1:{{ Math.round(1/unifiedScale * 10)/10 }}
          <span v-if="settings.paper_size.value.orientation === 'portrait'" style="color: blue;"> 📄</span>
          <span v-else style="color: green;"> 📰</span>
        </div>
        
        <button @click="extractFrontendFormats" class="btn btn-outline-info btn-sm me-2" :disabled="extracting">
          <i class="fas fa-download"></i> 
          {{ extracting ? '提取中...' : '提取前端格式' }}
        </button>
        <button @click="resetSettings" class="btn btn-outline-warning btn-sm">
          <i class="fas fa-undo"></i> {{ $t('printSettings.reset') }}
        </button>
      </div>
    </div>

    <!-- 消息提示 -->
    <div v-if="message" class="alert" :class="messageType === 'success' ? 'alert-success' : 'alert-danger'" 
         style="position: fixed; top: 20px; right: 20px; z-index: 1050; min-width: 300px;">
      {{ message }}
      <button type="button" class="btn-close" @click="clearMessage"></button>
    </div>

    <!-- 布局管理模态窗口 -->
    <div class="modal-overlay" v-if="showLayoutManager" @click="closeLayoutManager">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>布局管理</h3>
          <button class="close-btn" @click="closeLayoutManager">&times;</button>
        </div>
        <div class="modal-body">
          <div class="document-type-info">
            <p><strong>当前单据类型：</strong> {{ documentTypeDisplayName }}</p>
            <p><strong>⚠️ 注意：所有操作仅影响当前单据类型 "{{ documentTypeDisplayName }}" 的布局，不会影响其他单据类型的默认布局</strong></p>
          </div>
          
          <!-- 布局表格 -->
          <div class="layout-table-container">
            <table class="layout-table">
              <thead>
                <tr>
                  <th>布局名称</th>
                  <th>状态</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="layout in availableLayouts" :key="layout.layout_name">
                  <td>
                    <div v-if="editingLayoutName === layout.layout_name" class="edit-layout-name">
                      <input 
                        v-model="editLayoutNameValue" 
                        @keyup.enter="saveLayoutName(layout.layout_name)"
                        @keyup.esc="cancelEditLayoutName"
                        class="layout-name-edit-input"
                        ref="layoutNameInput"
                      />
                      <button @click="saveLayoutName(layout.layout_name)" class="btn-save-name">保存</button>
                      <button @click="cancelEditLayoutName" class="btn-cancel-name">取消</button>
                    </div>
                    <div v-else class="layout-name-display">
                      <span>{{ layout.layout_name }}</span>
                      <button 
                        @click="startEditLayoutName(layout.layout_name)" 
                        class="btn-edit-name"
                        title="修改布局名称"
                      >
                        <i class="icon-edit">✏️</i>
                      </button>
                    </div>
                  </td>
                  <td>
                    <span v-if="layout.is_default" class="default-badge">默认</span>
                    <span v-else class="normal-badge">普通</span>
                  </td>
                  <td>
                    <div class="action-buttons">
                      <!-- 新增：切换到这个布局按钮 -->
                      <button 
                        v-if="layout.layout_name !== currentLayoutName"
                        @click="switchToLayout(layout.layout_name)"
                        class="btn-switch"
                        title="切换到这个布局"
                      >
                        切换到这个布局
                      </button>
                      
                      <button 
                        v-if="!layout.is_default" 
                        @click="setDefaultLayout(layout.layout_name)"
                        class="btn-set-default"
                        :title="`设为${documentTypeDisplayName}的默认布局`"
                      >
                        设为默认
                      </button>
                      <button 
                        @click="duplicateLayout(layout.layout_name)"
                        class="btn-duplicate"
                        title="复制这个布局"
                      >
                        复制
                      </button>
                      <button 
                        @click="resetLayoutToDefault(layout.layout_name)"
                        class="btn-reset"
                        title="初始化单据格式，恢复到出厂状态"
                      >
                        初始化单据格式
                      </button>
                      <button 
                        v-if="!layout.is_default && availableLayouts.length > 1" 
                        @click="deleteLayout(layout.layout_name)"
                        class="btn-delete"
                        title="删除这个布局"
                      >
                        删除
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 新建布局 -->
          <div class="create-layout-section">
            <h4>新建布局：</h4>
            <div class="create-form">
              <input 
                v-model="newLayoutName" 
                placeholder="输入新布局名称" 
                class="layout-name-input"
                @keyup.enter="createLayout"
              />
              <button @click="createLayout" class="btn-create">创建布局</button>
            </div>
            <p class="create-hint">新布局将基于当前布局设置创建</p>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeLayoutManager" class="btn-close-modal">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import PrintSettingsHeader from '@/components/PrintSettings/PrintSettingsHeader.vue'
import PrintPreviewPanel from '@/components/PrintSettings/PrintPreviewPanel.vue'
import PrintLayoutEditor from '@/components/PrintSettings/PrintLayoutEditor.vue'
import PrintSettingsPanel from '@/components/PrintSettings/PrintSettingsPanel.vue'

export default {
  name: 'PrintSettingsViewModular',
  components: {
    PrintSettingsHeader,
    PrintPreviewPanel,
    PrintLayoutEditor,
    PrintSettingsPanel
  },
  setup() {
    // 响应式数据
    const currentLanguage = ref('zh-CN')
    const currentDocumentType = ref('exchange')
          const currentLayoutName = ref('')
    const availableLayouts = ref([])
    const selectedElement = ref(null)
    const saving = ref(false)
    const showLayoutManager = ref(false)
    const message = ref('')
    const messageType = ref('success')
    const componentsLoaded = ref(false)
    const newLayoutName = ref('')
    const editingLayoutName = ref('')
    const editLayoutNameValue = ref('')
    const extracting = ref(false)

    // 设置数据
    const settings = reactive({
      paper_size: {
        value: {
          width: 210,
          height: 297,
          name: 'A4',
          orientation: 'portrait'
        }
      },
      margins: {
        value: {
          top: 10,
          right: 10,
          bottom: 10,
          left: 10
        }
      },
      font_settings: {
        value: {
          family: 'SimSun',
          size: 12,
          bold: false,
          color: '#000000'
        }
      },
      header_settings: {
        value: {
          show_logo: false,
          show_branch_info: true,
          title_size: 16,
          title_bold: true,
          title_color: '#000000',
          title_font_family: 'SimHei',
          logo_width: 120,
          logo_height: 60,
          logo_alignment: 'center',
          logo_margin: 10,
          logo_data: null,
          logo_position: 'header'
        }
      },
      layout_settings: {
        value: {
          line_spacing: 1.2,
          table_border: true,
          auto_page_break: true,
          content_style: 'table',
          alignment: 'left',
          table_alignment: 'center',
          title_alignment: 'center',
          row_spacing: 'normal',
          field_label_width: 40,
          section_spacing: 15,
          show_field_labels: true
        }
      },
      signature_settings: {
        value: {
          signature_style: 'double',
          show_date_line: true,
          single_label: '签名/Signature',
                  left_label: 'Customer',
        right_label: 'Teller',
          signature_height: 40,
          signature_width: 150,
          date_format: 'YYYY年MM月DD日'
        }
      },
      advanced_settings: {
        value: {
          watermark_enabled: false,
          watermark_text: '样本',
          watermark_opacity: 0.1,
          page_numbering: false,
          header_line: true,
          footer_line: true,
          print_quality: 'high',
          color_mode: 'color'
        }
      }
    })

    // 元素位置数据
    const elementPositions = reactive({
      logo: { top: 5, left: 10, width: 30, height: 30, textAlign: 'center', visible: true, fontFamily: 'SimSun', fontSize: 8, color: '#000000' },
      title: { top: 15, left: 50, width: 110, height: 20, textAlign: 'center', visible: true, fontFamily: 'SimHei', fontSize: 12, color: '#000000' },
      subtitle: { top: 25, left: 50, width: 110, height: 15, textAlign: 'center', visible: true, fontFamily: 'SimSun', fontSize: 10, color: '#000000' },
      branch: { top: 35, left: 50, width: 110, height: 15, textAlign: 'center', visible: true, fontFamily: 'SimSun', fontSize: 8, color: '#000000' },
      content: { top: 50, left: 10, width: 190, height: 100, textAlign: 'left', visible: true, fontFamily: 'SimSun', fontSize: 8, color: '#000000' },
      signature: { top: 200, left: 10, width: 190, height: 40, textAlign: 'center', visible: true, fontFamily: 'SimSun', fontSize: 8, color: '#000000' },
      watermark: { top: 120, left: 80, width: 50, height: 30, textAlign: 'center', visible: true, fontFamily: 'SimSun', fontSize: 24, color: '#cccccc' }
    })

    // 计算属性
    const documentTypeDisplayName = computed(() => {
      const types = {
        'exchange': '外汇兑换',
        'reversal': '交易冲正',
        'balance_adjustment': '余额调整',
        'initial_balance': '余额初始化',
        'eod_report': '日终报告'
      }
      return types[currentDocumentType.value] || currentDocumentType.value
    })

    const paperDimensions = computed(() => {
      const { name, width, height, orientation } = settings.paper_size.value
      
      let paperWidth, paperHeight
      
      if (name === 'custom') {
        paperWidth = width
        paperHeight = height
      } else {
        const sizes = {
          'A4': { width: 210, height: 297 },
          'A5': { width: 148, height: 210 },
          'Letter': { width: 216, height: 279 },
          'Legal': { width: 216, height: 356 }
        }
        const size = sizes[name] || sizes['A4']
        paperWidth = size.width
        paperHeight = size.height
      }
      
      // 根据方向调整
      if (orientation === 'landscape') {
        return { width: Math.max(paperWidth, paperHeight), height: Math.min(paperWidth, paperHeight) }
      } else {
        return { width: Math.min(paperWidth, paperHeight), height: Math.max(paperWidth, paperHeight) }
      }
    })

    // 动态缩放比例 - 根据容器大小和纸张方向优化
    const baseScale = computed(() => {
      const containerWidth = 460  // 容器宽度
      const containerHeight = 600 // 容器高度
      const { width, height } = paperDimensions.value
      
      // 计算缩放比例，优先保证纸张能充分利用容器空间
      const scaleX = (containerWidth - 20) / width  // 减20px留边距
      const scaleY = (containerHeight - 40) / height // 减40px留边距
      const baseRatio = Math.min(scaleX, scaleY)
      
      // 根据纸张方向和类型调整最终缩放比例
      const orientation = settings.paper_size.value.orientation
      
      if (orientation === 'portrait') {
        // 纵向：优先适配宽度，保证纸张宽度充分利用容器
        return Math.min(baseRatio * 0.95, 2.2) // 95%的容器利用率
      } else {
        // 横向：适配高度，确保横向纸张能完整显示
        return Math.min(baseRatio * 0.9, 1.8)  // 90%的容器利用率
      }
    })

    // 使用固定比例计算显示尺寸
    const displayDimensions = computed(() => {
      const { width, height } = paperDimensions.value
      return {
        width: width * baseScale.value,
        height: height * baseScale.value
      }
    })

    // 为了兼容性，保留unifiedScale但使用baseScale
    const unifiedScale = computed(() => {
      return baseScale.value
    })

    const paperInfo = computed(() => {
      return {
        width: paperDimensions.value.width,
        height: paperDimensions.value.height,
        orientation: settings.paper_size.value.orientation,
        displayWidth: displayDimensions.value.width,
        displayHeight: displayDimensions.value.height,
        scale: unifiedScale.value
      }
    })

    const previewPageStyle = computed(() => {
      const { width, height } = displayDimensions.value
      return {
        width: `${width}px`,
        height: `${height}px`,
        border: '1px solid #ddd',
        backgroundColor: 'white',
        position: 'relative',
        margin: '10px auto',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }
    })

    const previewContentStyle = computed(() => {
      const margins = settings.margins.value
      const scale = unifiedScale.value
      
      return {
        padding: `${margins.top * scale}px ${margins.right * scale}px ${margins.bottom * scale}px ${margins.left * scale}px`,
        height: '100%',
        position: 'relative'
      }
    })

    const miniCanvasStyle = computed(() => {
      const { width, height } = displayDimensions.value
      
      return {
        width: `${width}px`,
        height: `${height}px`,
        backgroundColor: 'white',
        border: '1px solid #ddd',
        position: 'relative',
        margin: '0 auto',
        backgroundImage: 
          'linear-gradient(rgba(0,0,0,.1) 1px, transparent 1px), ' +
          'linear-gradient(90deg, rgba(0,0,0,.1) 1px, transparent 1px)',
        backgroundSize: `${20 * unifiedScale.value}px ${20 * unifiedScale.value}px`
      }
    })

    const miniContentStyle = computed(() => {
      const margins = settings.margins.value
      const scale = unifiedScale.value
      
      return {
        padding: `${margins.top * scale}px ${margins.right * scale}px ${margins.bottom * scale}px ${margins.left * scale}px`,
        height: '100%',
        position: 'relative'
      }
    })

    // 方法
    const showMessage = (msg, type = 'success') => {
      message.value = msg
      messageType.value = type
      setTimeout(() => {
        clearMessage()
      }, 3000)
    }

    const clearMessage = () => {
      message.value = ''
    }

    const changeLanguage = (lang) => {
      currentLanguage.value = lang
      // 这里可以添加语言切换逻辑
    }

    const loadSettingsForDocumentType = async (docType) => {
      currentDocumentType.value = docType
      // 重置当前布局名称，让loadAvailableLayouts选择默认布局
      currentLayoutName.value = ''
      await loadAvailableLayouts()
      await loadSettings()
    }

    const loadLayoutSettings = async (layoutName) => {
      currentLayoutName.value = layoutName
      await loadSettings()
    }

    const loadAvailableLayouts = async () => {
      try {
        // 使用现有的layouts/list API，它已经包含了默认布局信息
        const response = await fetch('/api/print-settings/layouts/list?' + new URLSearchParams({
          document_type: currentDocumentType.value
        }), {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
          }
        })
        
        if (response.ok) {
          const data = await response.json()
          if (data.success && data.layouts) {
            // 使用从现有API获取的布局列表，保留API返回的is_default值
            availableLayouts.value = data.layouts.map(layout => ({
              layout_name: layout.name,
              name: layout.name,
              is_default: layout.is_default  // 使用API返回的is_default值
            }))
            
            // 如果只有一个布局且不是默认布局，将其标记为默认
            if (data.layouts.length === 1) {
              const singleLayout = data.layouts[0]
              if (!singleLayout.is_default) {
                // 更新本地显示状态（UI立即显示为默认）
                availableLayouts.value[0].is_default = true
                console.log(`检测到唯一布局 ${singleLayout.name}，标记为默认`)
              }
            }
            
            // 如果当前没有设置布局名称，使用默认布局
            if (!currentLayoutName.value) {
              const defaultLayout = availableLayouts.value.find(layout => layout.is_default)
              if (defaultLayout) {
                currentLayoutName.value = defaultLayout.layout_name
              } else if (data.layouts.length > 0) {
                // 如果没有默认布局，使用第一个布局
                currentLayoutName.value = data.layouts[0].name
              }
            }
            
            console.log('从现有API获取布局列表:', availableLayouts.value)
            console.log('当前布局名称:', currentLayoutName.value)
          }
        } else {
          // 如果没有布局，使用默认值
          availableLayouts.value = [{ layout_name: 'default', name: 'default', is_default: true }]
          currentLayoutName.value = 'default'
        }
      } catch (error) {
        console.error('加载可用布局失败:', error)
        availableLayouts.value = [{ layout_name: 'default', name: 'default', is_default: true }]
        currentLayoutName.value = 'default'
      }
    }

    const loadSettings = async () => {
      try {
        console.log(`加载设置: ${currentDocumentType.value} - ${currentLayoutName.value}`)
        
        // 调用API获取打印设置
        const response = await fetch('/api/print-settings/templates?' + new URLSearchParams({
          document_type: currentDocumentType.value,
          layout_name: currentLayoutName.value
        }), {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
          }
        })
        
        if (response.ok) {
          const data = await response.json()
          if (data.success && data.settings) {
            // 更新设置数据
            Object.keys(data.settings).forEach(key => {
              if (settings[key]) {
                settings[key].value = data.settings[key].value || data.settings[key]
              }
            })
            
            // 更新元素位置数据
            if (data.settings.element_positions) {
              // 处理包装在.value中的数据格式
              const elementPositionsData = data.settings.element_positions.value || data.settings.element_positions
              Object.keys(elementPositionsData).forEach(key => {
                if (elementPositions[key]) {
                  Object.assign(elementPositions[key], elementPositionsData[key])
                }
              })
              console.log('元素位置数据更新完成:', elementPositions)
            }
            
            console.log('设置加载成功:', data.settings)
          }
        } else {
          console.warn('使用默认设置')
        }
        
        componentsLoaded.value = true
      } catch (error) {
        console.error('加载设置失败:', error)
        showMessage('加载设置失败: ' + error.message, 'error')
        componentsLoaded.value = true
      }
    }

    const handleUpdateSettings = (update) => {
      console.log('更新设置:', update) // 调试日志
      const { path, update: updateData } = update
      const pathParts = path.split('.')
      
      let target = settings
      for (let i = 0; i < pathParts.length - 1; i++) {
        target = target[pathParts[i]]
      }
      
      target[pathParts[pathParts.length - 1]] = updateData
    }

    const handleUpdateElementPosition = (update) => {
      console.log('更新元素位置:', update) // 调试日志
      const { elementType, ...position } = update
      
      if (!elementPositions[elementType]) {
        elementPositions[elementType] = {}
      }
      
      Object.assign(elementPositions[elementType], position)
    }

    const handleStartDrag = (event) => {
      console.log('开始拖拽:', event)
    }

    const saveSettings = async () => {
      saving.value = true
      try {
        console.log('保存设置:', settings, elementPositions)
        
        // 准备保存数据
        const saveData = {
          document_type: currentDocumentType.value,
          layout_name: currentLayoutName.value,
          settings: {
            paper_size: settings.paper_size,
            margins: settings.margins,
            font_settings: settings.font_settings,
            header_settings: settings.header_settings,
            layout_settings: settings.layout_settings,
            signature_settings: settings.signature_settings,
            advanced_settings: settings.advanced_settings
          },
          elementPositions: elementPositions  // 使用正确的字段名
        }
        
        // 1. 保存到print_settings表
        const response = await fetch('/api/print-settings/templates', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
          },
          body: JSON.stringify(saveData)
        })
        
        const data = await response.json()
        
        if (response.ok && data.success) {
          showMessage('设置保存成功', 'success')
          console.log('设置保存成功:', data)
        } else {
          throw new Error(data.message || '保存失败')
        }
      } catch (error) {
        console.error('保存设置失败:', error)
        showMessage('保存设置失败: ' + error.message, 'error')
      } finally {
        saving.value = false
      }
    }

    const openLayoutManager = () => {
      showLayoutManager.value = true
    }

    const closeLayoutManager = () => {
      showLayoutManager.value = false
    }

    const switchToLayout = async (layoutName) => {
      try {
        currentLayoutName.value = layoutName
        await loadSettings()
        closeLayoutManager()
        showMessage(`已切换到布局: ${layoutName} (这是临时切换，不会改变默认设置)`, 'success')
      } catch (error) {
        console.error('切换布局失败:', error)
        showMessage('切换布局失败: ' + error.message, 'error')
      }
    }

    const setDefaultLayout = async (layoutName) => {
      try {
        // 使用模板设置默认布局API，确保print_templates表得到正确更新
        const response = await fetch('/api/print-settings/templates/set-default', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
          },
          body: JSON.stringify({
            document_type: currentDocumentType.value,
            layout_name: layoutName
          })
        })
        
        const data = await response.json()
        if (response.ok && data.success) {
          // 更新布局列表中的默认状态
          availableLayouts.value.forEach(layout => {
            layout.is_default = layout.layout_name === layoutName
          })
          showMessage(`已设置 ${layoutName} 为 ${documentTypeDisplayName.value} 的默认布局`, 'success')
          console.log('默认布局设置成功，print_templates表已更新')
        } else {
          throw new Error(data.message || '设置默认布局失败')
        }
      } catch (error) {
        console.error('设置默认布局失败:', error)
        showMessage('设置默认布局失败: ' + error.message, 'error')
      }
    }

    const duplicateLayout = async (layoutName) => {
      try {
        const newName = prompt(`请输入新布局名称 (基于: ${layoutName})`, `${layoutName}_副本`)
        if (newName && newName.trim()) {
          const response = await fetch('/api/print-settings/templates/duplicate', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
            },
            body: JSON.stringify({
              document_type: currentDocumentType.value,
              source_layout_name: layoutName,
              new_layout_name: newName.trim()
            })
          })
          
          const data = await response.json()
          if (response.ok && data.success) {
            await loadAvailableLayouts()
            showMessage(`布局 ${newName.trim()} 创建成功`, 'success')
          } else {
            throw new Error(data.message || '复制布局失败')
          }
        }
      } catch (error) {
        console.error('复制布局失败:', error)
        showMessage('复制布局失败: ' + error.message, 'error')
      }
    }

    const resetLayoutToDefault = async (layoutName) => {
      if (confirm(`确定要将布局 "${layoutName}" 初始化为出厂格式吗？\n这将恢复到前端硬编码的默认设置，丢失所有自定义设置！`)) {
        try {
          // 调用新的恢复出厂格式API
          const response = await fetch('/api/print-settings/restore-factory-defaults', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
            },
            body: JSON.stringify({
              document_type: currentDocumentType.value,
              layout_name: layoutName
            })
          })

          const data = await response.json()
          if (response.ok && data.success) {
            await loadAvailableLayouts()
            // 如果重置的是当前布局，重新加载设置
            if (currentLayoutName.value === layoutName) {
              await loadSettings()
            }
            showMessage(`${data.message} - 已恢复为前端硬编码格式`, 'success')
          } else {
            throw new Error(data.message || '恢复出厂格式失败')
          }
        } catch (error) {
          console.error('恢复出厂格式失败:', error)
          showMessage('恢复出厂格式失败: ' + error.message, 'error')
        }
      }
    }

    const deleteLayout = async (layoutName) => {
      if (confirm(`确定要删除布局 "${layoutName}" 吗？`)) {
        try {
          const response = await fetch('/api/print-settings/layouts/delete', {
            method: 'DELETE',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
            },
            body: JSON.stringify({
              document_type: currentDocumentType.value,
              layout_name: layoutName
            })
          })
          
          const data = await response.json()
          if (response.ok && data.success) {
            await loadAvailableLayouts()
            // 如果删除的是当前布局，切换到默认布局
            if (currentLayoutName.value === layoutName) {
              const defaultLayout = availableLayouts.value.find(l => l.is_default)
              if (defaultLayout) {
                currentLayoutName.value = defaultLayout.layout_name
                await loadSettings()
              }
            }
            showMessage(`布局 ${layoutName} 已删除`, 'success')
          } else {
            throw new Error(data.message || '删除布局失败')
          }
        } catch (error) {
          console.error('删除布局失败:', error)
          showMessage('删除布局失败: ' + error.message, 'error')
        }
      }
    }

    const createLayout = async () => {
      if (newLayoutName.value && newLayoutName.value.trim()) {
        try {
          const response = await fetch('/api/print-settings/templates/create', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
            },
            body: JSON.stringify({
              document_type: currentDocumentType.value,
              layout_name: newLayoutName.value.trim(),
              base_layout_name: currentLayoutName.value
            })
          })
          
          const data = await response.json()
          if (response.ok && data.success) {
            await loadAvailableLayouts()
            const createdName = newLayoutName.value.trim()
            newLayoutName.value = ''
            showMessage(`布局 ${createdName} 创建成功`, 'success')
          } else {
            throw new Error(data.message || '创建布局失败')
          }
        } catch (error) {
          console.error('创建布局失败:', error)
          showMessage('创建布局失败: ' + error.message, 'error')
        }
      }
    }

    // 编辑布局名称相关方法
    const startEditLayoutName = (layoutName) => {
      editingLayoutName.value = layoutName
      editLayoutNameValue.value = layoutName
      // 使用nextTick确保输入框渲染后再聚焦
      nextTick(() => {
        const input = document.querySelector('.layout-name-edit-input')
        if (input) {
          input.focus()
          input.select()
        }
      })
    }

    const cancelEditLayoutName = () => {
      editingLayoutName.value = ''
      editLayoutNameValue.value = ''
    }

    const saveLayoutName = async (oldLayoutName) => {
      const newName = editLayoutNameValue.value.trim()
      
      if (!newName) {
        showMessage('布局名称不能为空', 'error')
        return
      }
      
      if (newName === oldLayoutName) {
        cancelEditLayoutName()
        return
      }
      
      // 检查新名称是否已存在
      if (availableLayouts.value.some(layout => layout.layout_name === newName)) {
        showMessage('布局名称已存在', 'error')
        return
      }
      
      try {
        const response = await fetch('/api/print-settings/templates/rename', {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
          },
          body: JSON.stringify({
            document_type: currentDocumentType.value,
            old_layout_name: oldLayoutName,
            new_layout_name: newName
          })
        })
        
        const data = await response.json()
        if (response.ok && data.success) {
          // 如果修改的是当前布局，更新当前布局名称
          if (currentLayoutName.value === oldLayoutName) {
            currentLayoutName.value = newName
          }
          
          await loadAvailableLayouts()
          cancelEditLayoutName()
          showMessage(`布局名称已更新为 "${newName}"`, 'success')
        } else {
          throw new Error(data.message || '修改布局名称失败')
        }
      } catch (error) {
        console.error('修改布局名称失败:', error)
        showMessage('修改布局名称失败: ' + error.message, 'error')
      }
    }

    const resetSettings = async () => {
      // 重置当前布局到出厂格式
      await resetLayoutToDefault(currentLayoutName.value)
    }

    const extractFrontendFormats = async () => {
      extracting.value = true
      
      try {
        // 定义各业务类型的前端默认格式
        const frontendFormats = {
          'exchange': {
            paper_size: {
              value: { width: 210, height: 297, name: 'A4', orientation: 'portrait' },
              description: '纸张大小和方向设置'
            },
            margins: {
              value: { top: 20, right: 20, bottom: 20, left: 20 },
              description: '页面边距设置'
            },
            font_settings: {
              value: { family: 'SimSun', size: 10, color: '#000000', bold: false },
              description: '全局字体设置'
            },
            header_settings: {
              value: { 
                show_logo: true, 
                show_branch_info: true, 
                title_size: 16, 
                title_bold: true,
                logo_width: 120,
                logo_height: 60,
                logo_alignment: 'center'
              },
              description: '页眉设置'
            },
            layout_settings: {
              value: { 
                line_spacing: 1.2, 
                table_border: true, 
                auto_page_break: true,
                content_style: 'table'
              },
              description: '布局设置'
            },
            signature_settings: {
              value: {
                signature_style: 'double',
                show_date_line: true,
                single_label: '签名/Signature',
                          left_label: 'Customer',
          right_label: 'Teller'
              },
              description: '签名设置'
            },
            element_positions: {
              value: {
                logo: { top: 5, left: 105, width: 120, height: 60, textAlign: 'center', visible: true },
                title: { top: 25, left: 105, width: 0, height: 20, textAlign: 'center', visible: true },
                subtitle: { top: 45, left: 105, width: 0, height: 15, textAlign: 'center', visible: true },
                branch: { top: 65, left: 105, width: 0, height: 15, textAlign: 'center', visible: true },
                content: { top: 85, left: 20, width: 170, height: 120, textAlign: 'left', visible: true },
                signature: { top: 220, left: 20, width: 170, height: 40, textAlign: 'left', visible: true }
              },
              description: '元素位置设置'
            }
          },
          'reversal': {
            // 冲正业务格式（可以基于exchange修改）
            paper_size: {
              value: { width: 210, height: 297, name: 'A4', orientation: 'portrait' },
              description: '纸张大小和方向设置'
            },
            margins: {
              value: { top: 20, right: 20, bottom: 20, left: 20 },
              description: '页面边距设置'
            },
            font_settings: {
              value: { family: 'SimSun', size: 10, color: '#000000', bold: false },
              description: '全局字体设置'
            },
            header_settings: {
              value: { show_logo: true, show_branch_info: true, title_size: 16, title_bold: true },
              description: '页眉设置'
            },
            layout_settings: {
              value: { line_spacing: 1.2, table_border: true, auto_page_break: true, content_style: 'table' },
              description: '布局设置'
            }
          },
          'balance_adjustment': {
            // 余额调节格式
            paper_size: {
              value: { width: 210, height: 297, name: 'A4', orientation: 'portrait' },
              description: '纸张大小和方向设置'
            },
            margins: {
              value: { top: 20, right: 20, bottom: 20, left: 20 },
              description: '页面边距设置'
            },
            font_settings: {
              value: { family: 'SimSun', size: 10, color: '#000000', bold: false },
              description: '全局字体设置'
            }
          },
          'balance_summary': {
            // 期初余额汇总格式
            paper_size: {
              value: { width: 210, height: 297, name: 'A4', orientation: 'portrait' },
              description: '纸张大小和方向设置'
            },
            margins: {
              value: { top: 20, right: 20, bottom: 20, left: 20 },
              description: '页面边距设置'
            }
          },
          'initial_balance': {
            // 余额初始化凭据格式
            paper_size: {
              value: { width: 210, height: 297, name: 'A4', orientation: 'portrait' },
              description: '纸张大小和方向设置'
            },
            margins: {
              value: { top: 20, right: 20, bottom: 20, left: 20 },
              description: '页面边距设置'
            },
            font_settings: {
              value: { family: 'SimSun', size: 10, color: '#000000', bold: false },
              description: '全局字体设置'
            },
            header_settings: {
              value: { 
                show_logo: true, 
                show_branch_info: true, 
                title_size: 16, 
                title_bold: true,
                logo_width: 120,
                logo_height: 60,
                logo_alignment: 'center'
              },
              description: '页眉设置'
            },
            layout_settings: {
              value: { 
                line_spacing: 1.2, 
                table_border: true, 
                auto_page_break: true,
                content_style: 'table'
              },
              description: '布局设置'
            },
            signature_settings: {
              value: {
                signature_style: 'double',
                show_date_line: true,
                single_label: '签名/Signature',
                left_label: '操作员签名/Operator',
                right_label: '复核签名/Reviewer'
              },
              description: '签名设置'
            },
            element_positions: {
              value: {
                logo: { top: 5, left: 105, width: 120, height: 60, textAlign: 'center', visible: true },
                title: { top: 25, left: 105, width: 0, height: 20, textAlign: 'center', visible: true },
                subtitle: { top: 45, left: 105, width: 0, height: 15, textAlign: 'center', visible: true },
                branch: { top: 65, left: 105, width: 0, height: 15, textAlign: 'center', visible: true },
                content: { top: 85, left: 20, width: 170, height: 120, textAlign: 'left', visible: true },
                signature: { top: 220, left: 20, width: 170, height: 40, textAlign: 'left', visible: true }
              },
              description: '元素位置设置'
            }
          },
          'eod_report': {
            // 日结报表格式
            paper_size: {
              value: { width: 210, height: 297, name: 'A4', orientation: 'portrait' },
              description: '纸张大小和方向设置'
            },
            margins: {
              value: { top: 15, right: 15, bottom: 15, left: 15 },
              description: '页面边距设置'
            }
          }
        }
        
        // 调用后端API保存格式
        const response = await fetch('/api/print-settings/extract-frontend-formats', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify({
            formats: frontendFormats
          })
        })
        
        const result = await response.json()
        
        if (result.success) {
          showMessage('前端格式提取成功！已为所有业务类型创建默认模板。')
          console.log('创建的模板:', result.created_templates)
          
          // 刷新布局列表并重新加载当前设置
          await loadAvailableLayouts()
          await loadSettings()  // 自动重新加载设置，相当于自动保存
        } else {
          showMessage(`提取失败: ${result.message}`)
        }
        
      } catch (error) {
        console.error('提取前端格式失败:', error)
        showMessage('提取前端格式失败，请检查网络连接')
      } finally {
        extracting.value = false
      }
    }

    // 生命周期
    onMounted(async () => {
      try {
        // 先加载布局列表，再加载设置
        await loadAvailableLayouts()
        await loadSettings()
        nextTick(() => {
          // 初始化完成后的逻辑
          console.log('初始化完成:', {
            currentLayoutName: currentLayoutName.value,
            availableLayouts: availableLayouts.value
          })
        })
      } catch (error) {
        console.error('初始化失败:', error)
        componentsLoaded.value = true
      }
    })

    return {
      // 响应式数据
      currentLanguage,
      currentDocumentType,
      currentLayoutName,
      availableLayouts,
      selectedElement,
      saving,
      showLayoutManager,
      message,
      messageType,
      settings,
      elementPositions,
      componentsLoaded,
      newLayoutName,
      editingLayoutName,
      editLayoutNameValue,
      extracting,
      
      // 计算属性
      documentTypeDisplayName,
      paperDimensions,
      baseScale,
      displayDimensions,
      paperInfo,
      unifiedScale,
      previewPageStyle,
      previewContentStyle,
      miniCanvasStyle,
      miniContentStyle,
      
      // 方法
      showMessage,
      changeLanguage,
      loadSettingsForDocumentType,
      loadLayoutSettings,
      loadAvailableLayouts,
      loadSettings,
      handleUpdateSettings,
      handleUpdateElementPosition,
      handleStartDrag,
      saveSettings,
      clearMessage,
      openLayoutManager,
      closeLayoutManager,
              switchToLayout,
        setDefaultLayout,
              duplicateLayout,
      resetLayoutToDefault,
      deleteLayout,
      createLayout,
      startEditLayoutName,
      cancelEditLayoutName,
      saveLayoutName,
      resetSettings,
      extractFrontendFormats
    }
  }
}
</script>

<style scoped>
.print-settings-container {
  padding: 20px;
  background: #f8f9fa;
  min-height: 100vh;
}

.alert {
  border-radius: 6px;
  font-size: 0.9rem;
}

.alert-success {
  background-color: #d4edda;
  border-color: #c3e6cb;
  color: #155724;
}

.alert-danger {
  background-color: #f8d7da;
  border-color: #f5c6cb;
  color: #721c24;
}

/* 模态窗口样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  max-width: 800px;
  width: 90%;
  max-height: 80%;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #ddd;
  background: #f8f9fa;
  border-radius: 8px 8px 0 0;
}

.modal-header h3 {
  margin: 0;
  color: #333;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
}

.close-btn:hover {
  color: #333;
  background: #e9ecef;
}

.modal-body {
  padding: 20px;
}

.modal-footer {
  padding: 15px 20px;
  border-top: 1px solid #ddd;
  background: #f8f9fa;
  border-radius: 0 0 8px 8px;
  text-align: right;
}

.document-type-info {
  margin-bottom: 20px;
  padding: 15px;
  background: #fff3cd;
  border-radius: 6px;
  border: 1px solid #ffeaa7;
  border-left: 4px solid #ffc107;
}

.document-type-info p {
  margin: 5px 0;
}

.document-type-info p:last-child {
  color: #856404;
  font-weight: 500;
}

/* 布局名称编辑样式 */
.layout-name-display {
  display: flex;
  align-items: center;
  gap: 8px;
}

.layout-name-display span {
  flex: 1;
}

.btn-edit-name {
  background: none;
  border: none;
  padding: 2px 4px;
  cursor: pointer;
  color: #666;
  font-size: 12px;
  opacity: 0.7;
  transition: opacity 0.2s;
}

.btn-edit-name:hover {
  opacity: 1;
  color: #007bff;
}

.edit-layout-name {
  display: flex;
  align-items: center;
  gap: 6px;
}

.layout-name-edit-input {
  flex: 1;
  padding: 4px 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  min-width: 120px;
}

.layout-name-edit-input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.btn-save-name, .btn-cancel-name {
  padding: 4px 8px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: background-color 0.2s;
}

.btn-save-name {
  background-color: #28a745;
  color: white;
}

.btn-save-name:hover {
  background-color: #218838;
}

.btn-cancel-name {
  background-color: #6c757d;
  color: white;
}

.btn-cancel-name:hover {
  background-color: #5a6268;
}

.layout-table-container {
  margin-bottom: 30px;
}

.layout-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.layout-table th,
.layout-table td {
  padding: 12px 15px;
  text-align: left;
  border-bottom: 1px solid #e9ecef;
}

.layout-table th {
  background: #f8f9fa;
  font-weight: 600;
  color: #333;
}

.layout-table tbody tr:hover {
  background: #f8f9fa;
}

.default-badge {
  background: #28a745;
  color: white;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
}

.normal-badge {
  background: #6c757d;
  color: white;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
}

.action-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.btn-switch {
  background: #007bff;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-switch:hover {
  background: #0056b3;
  transform: translateY(-1px);
}

.btn-set-default {
  background: #28a745;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-set-default:hover {
  background: #1e7e34;
  transform: translateY(-1px);
}

.btn-duplicate {
  background: #17a2b8;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-duplicate:hover {
  background: #117a8b;
  transform: translateY(-1px);
}

.btn-reset {
  background: #ffc107;
  color: #212529;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-reset:hover {
  background: #e0a800;
  transform: translateY(-1px);
}

.btn-delete {
  background: #dc3545;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-delete:hover {
  background: #c82333;
  transform: translateY(-1px);
}

.create-layout-section {
  border-top: 2px solid #e9ecef;
  padding-top: 20px;
}

.create-layout-section h4 {
  margin-bottom: 15px;
  color: #333;
}

.create-form {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.layout-name-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.layout-name-input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.btn-create {
  background: #007bff;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn-create:hover {
  background: #0056b3;
}

.create-hint {
  font-size: 12px;
  color: #6c757d;
  margin: 0;
}

.btn-close-modal {
  background: #6c757d;
  color: white;
  border: none;
  padding: 8px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn-close-modal:hover {
  background: #545b62;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .print-settings-container .row > div {
    width: 100% !important;
    margin-bottom: 20px;
  }
}

@media (max-width: 768px) {
  .print-settings-container {
    padding: 10px;
  }
  
  .modal-content {
    width: 95%;
    max-height: 90%;
  }
  
  .modal-header,
  .modal-body,
  .modal-footer {
    padding: 15px;
  }
  
  .action-buttons {
    flex-direction: column;
    gap: 5px;
  }
  
  .create-form {
    flex-direction: column;
  }
}
</style> 
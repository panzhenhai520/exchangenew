import api from './api'

/**
 * 打印设置服务
 * 提供统一的打印格式应用功能
 */
class PrintSettingsService {
  constructor() {
    this.cachedSettings = null
  }

  /**
   * 获取打印设置
   */
  async getPrintSettings() {
    try {
      if (this.cachedSettings) {
        return this.cachedSettings
      }

      const response = await api.get('/system/print-settings')
      if (response.data.success) {
        this.cachedSettings = response.data.settings
        return this.cachedSettings
      } else {
        console.warn('获取打印设置失败，使用默认设置')
        return this.getDefaultSettings()
      }
    } catch (error) {
      console.error('获取打印设置出错:', error)
      return this.getDefaultSettings()
    }
  }

  /**
   * 获取默认打印设置
   */
  getDefaultSettings() {
    return {
      paper_size: {
        value: {
          width: 210,
          height: 297,
          name: 'A4'
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
          bold: false
        }
      },
      header_settings: {
        value: {
          show_logo: true,
          show_branch_info: true,
          title_size: 16,
          title_bold: true
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
          field_label_width: 40,
          show_field_labels: true,
          table_width: 160,
          table_height: 120
        }
      },
      custom_paper: {
        value: {
          enabled: false,
          width: 80,
          height: 200,
          name: '自定义'
        }
      }
    }
  }

  /**
   * 生成打印样式CSS
   */
  async generatePrintCSS() {
    const settings = await this.getPrintSettings()
    
    // 选择纸张设置
    const paperSettings = settings.custom_paper?.value?.enabled 
      ? settings.custom_paper.value 
      : settings.paper_size.value

    const margins = settings.margins.value
    const fontSettings = settings.font_settings.value
    const layoutSettings = settings.layout_settings.value

    return `
      @media print {
        @page {
          size: ${paperSettings.width}mm ${paperSettings.height}mm;
          margin: ${margins.top}mm ${margins.right}mm ${margins.bottom}mm ${margins.left}mm;
        }
        
        /* 隐藏所有内容 */
        * {
          visibility: hidden !important;
        }
        
        /* 只显示打印区域 */
        #printArea,
        #printArea * {
          visibility: visible !important;
        }
        
        /* 重置页面布局 */
        body {
          font-family: '${fontSettings.family}', serif !important;
          font-size: ${fontSettings.size}pt !important;
          font-weight: ${fontSettings.bold ? 'bold' : 'normal'} !important;
          line-height: ${layoutSettings.line_spacing} !important;
          color: black !important;
          background: white !important;
          margin: 0 !important;
          padding: 0 !important;
        }
        
        /* 打印区域定位 */
        #printArea {
          position: absolute !important;
          left: 0 !important;
          top: 0 !important;
          width: 100% !important;
          height: auto !important;
          overflow: visible !important;
          background: white !important;
          color: black !important;
        }
        
        /* 凭证容器 */
        .receipt-container {
          width: 100% !important;
          padding: 0 !important;
          margin: 0 !important;
          font-family: '${fontSettings.family}', serif !important;
          font-size: ${fontSettings.size}pt !important;
          line-height: ${layoutSettings.line_spacing} !important;
          color: black !important;
          background: white !important;
        }
        
        /* 标题样式 */
        .receipt-container h5 {
          font-size: ${settings.header_settings?.value?.title_size || 16}pt !important;
          font-weight: ${settings.header_settings?.value?.title_bold ? 'bold' : 'normal'} !important;
          text-align: center !important;
          margin: 0 0 10pt 0 !important;
          color: black !important;
        }
        
        /* 表格样式 */
        .receipt-table {
          width: 100% !important;
          border-collapse: collapse !important;
          margin: 5pt 0 !important;
        }
        
        .receipt-table td {
          padding: 2pt 4pt !important;
          font-size: ${Math.max(fontSettings.size - 1, 10)}pt !important;
          line-height: ${layoutSettings.line_spacing} !important;
          vertical-align: top !important;
          color: black !important;
          ${layoutSettings.table_border ? 'border-bottom: 1px solid black !important;' : ''}
        }
        
        .receipt-table td:first-child {
          font-weight: bold !important;
          width: 35% !important;
        }
        
        /* 签名框样式 */
        .signature-box {
          border: ${layoutSettings.table_border ? '1px solid black' : '1px solid #ccc'} !important;
          padding: 8pt !important;
          margin: 4pt !important;
          min-height: 25pt !important;
          text-align: center !important;
          color: black !important;
          background: white !important;
        }
        
        .signature-line {
          border-bottom: 1px solid black !important;
          height: 12pt !important;
          margin: 4pt 0 2pt !important;
        }
        
        /* 注意事项样式 */
        .notice-section {
          margin-top: 10pt !important;
          padding-top: 5pt !important;
          border-top: 1px solid black !important;
          text-align: center !important;
          font-size: ${Math.max(fontSettings.size - 2, 9)}pt !important;
          color: black !important;
        }
        
        /* 小字体 */
        .receipt-container small {
          font-size: ${Math.max(fontSettings.size - 3, 8)}pt !important;
          color: black !important;
        }
        
        /* Bootstrap网格系统 */
        .row {
          display: flex !important;
          flex-wrap: wrap !important;
          margin: 0 !important;
        }
        
        .col-6 {
          flex: 0 0 50% !important;
          max-width: 50% !important;
          padding: 0 2pt !important;
        }
        
        /* 文本对齐 */
        .text-center {
          text-align: center !important;
        }
        
        /* 边距控制 */
        .mb-1 { margin-bottom: 3pt !important; }
        .mb-2 { margin-bottom: 6pt !important; }
        .mt-1 { margin-top: 3pt !important; }
        .g-2 > * { padding: 2pt !important; }
        
        /* 表格边框控制 */
        ${layoutSettings.table_border ? `
          .receipt-table,
          .receipt-table th,
          .receipt-table td {
            border: 1px solid black !important;
          }
        ` : ''}
        
        /* 隐藏不需要的元素 */
        .modal-header,
        .modal-footer,
        .btn,
        .btn-close {
          display: none !important;
          visibility: hidden !important;
        }
      }
    `
  }

  /**
   * 清空缓存的设置
   */
  clearCache() {
    this.cachedSettings = null
  }
}

// 创建单例
const printSettingsService = new PrintSettingsService()

export default printSettingsService 
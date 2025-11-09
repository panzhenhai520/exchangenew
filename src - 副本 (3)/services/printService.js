/**
 * 统一打印服务组件
 * 提供PDF生成、获取、打印的完整解决方案
 */

class PrintService {
  constructor() {
    this.activeWindows = new Set(); // 跟踪活动的打印窗口
  }

  /**
   * 统一的PDF打印方法
   * @param {Object} config 打印配置
   * @param {string} config.generateApiUrl - PDF生成API路径
   * @param {string} config.downloadApiUrl - PDF下载API路径
   * @param {Object} config.requestData - 请求数据 (可选)
   * @param {string} config.successMessage - 成功消息
   * @param {string} config.errorPrefix - 错误消息前缀
   * @param {Object} config.toast - Toast对象 (可选)
   * @param {boolean} config.autoClose - 是否自动关闭窗口 (默认true)
   * @param {number} config.windowTimeout - 窗口自动关闭时间(ms) (默认20000)
   * @param {boolean} config.hideWindow - 是否隐藏PDF窗口 (默认true)
   * @param {boolean} config.useHtmlMode - 是否使用HTML转PDF模式 (默认false)
   * @returns {Promise<boolean>} 打印是否成功
   */
  async printPDF(config) {
    const {
      generateApiUrl,
      downloadApiUrl,
      requestData = {},
      successMessage = 'PDF生成成功',
      errorPrefix = '打印失败',
      toast = null,
      autoClose = true,
      windowTimeout = 20000, // 延长到20秒，给用户更多时间进行打印操作
      hideWindow = true,
      useHtmlMode = false
    } = config;

    try {
      console.log(`开始生成PDF: ${generateApiUrl}, HTML模式: ${useHtmlMode}`);
      
      // 添加HTML模式参数到请求数据
      const finalRequestData = {
        ...requestData,
        use_html_mode: useHtmlMode
      };
      
      // 1. 调用后端API生成PDF
      const response = await this._callGenerateAPI(generateApiUrl, finalRequestData);
      
      if (!response.success) {
        throw new Error(response.message || 'PDF生成失败');
      }
      
      console.log('PDF生成成功:', response);
      
      // 2. 显示成功消息 - 使用后端返回的完整消息，避免前端硬编码
      const fullSuccessMessage = response.message || successMessage;
      
      this._showMessage(toast, 'success', fullSuccessMessage);
      
      // 3. 获取并打印PDF，自动拼接language参数
      let language = 'zh';
      if (localStorage.getItem('language')) {
        const locale = localStorage.getItem('language');
        if (locale === 'en-US') language = 'en';
        else if (locale === 'th-TH') language = 'th';
      }
      let downloadUrlWithLang = downloadApiUrl;
      if (downloadUrlWithLang.indexOf('?') === -1) {
        downloadUrlWithLang += `?language=${language}`;
      } else {
        downloadUrlWithLang += `&language=${language}`;
      }
      await this._downloadAndPrintPDF(downloadUrlWithLang, autoClose, windowTimeout, hideWindow);
      
      return true;
      
    } catch (error) {
      console.error('PDF打印失败:', error);
      const errorMessage = `${errorPrefix}: ${error.response?.data?.message || error.message || '未知错误'}`;
      this._showMessage(toast, 'error', errorMessage);
      return false;
    }
  }

  /**
   * 简化的HTML打印方法 (用于交易冲正等简单场景)
   * @param {Object} config 打印配置
   * @param {string} config.printAreaId - 打印区域ID (当前版本未使用，保留用于向后兼容)
   * @param {string} config.printStyles - 打印样式CSS
   * @param {string} config.successMessage - 成功消息
   * @param {Object} config.toast - Toast对象 (可选)
   */
  async printHTML(config) {
    const {
      printStyles = '',
      successMessage = '打印完成',
      toast = null
    } = config;

    try {
      console.log('开始HTML打印...');
      
      // 创建打印样式
      const printStyle = document.createElement('style');
      printStyle.id = 'unified-print-styles';
      printStyle.textContent = this._getDefaultPrintStyles() + printStyles;
      
      // 添加样式到页面
      document.head.appendChild(printStyle);
      
      // 直接触发浏览器打印预览
      window.print();
      
      // 打印完成后移除样式
      setTimeout(() => {
        const existingStyle = document.getElementById('unified-print-styles');
        if (existingStyle) {
          document.head.removeChild(existingStyle);
        }
      }, 1000);
      
      console.log('HTML打印完成');
      this._showMessage(toast, 'success', successMessage);
      
      return true;
      
    } catch (error) {
      console.error('HTML打印失败:', error);
      this._showMessage(toast, 'error', '打印失败，请重试');
      return false;
    }
  }

  /**
   * 调用PDF生成API
   * @private
   */
  async _callGenerateAPI(apiUrl, requestData) {
    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error('未找到认证信息，请重新登录');
    }

    // 【调试】记录API调用参数
    console.log('【调试】_callGenerateAPI - API URL:', apiUrl);
    console.log('【调试】_callGenerateAPI - 请求数据:', requestData);

    const response = await fetch(`/api/${apiUrl}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(requestData)
    });

    if (!response.ok) {
      let errorMessage = 'API调用失败';
      try {
        const errorData = await response.json();
        errorMessage = errorData.message || errorMessage;
      } catch (jsonError) {
        // 如果响应不是JSON格式，使用响应状态文本
        errorMessage = response.statusText || `HTTP ${response.status}`;
      }
      throw new Error(errorMessage);
    }

    try {
      return await response.json();
    } catch (jsonError) {
      console.error('JSON解析失败:', jsonError);
      throw new Error('服务器返回了无效的JSON数据');
    }
  }

  /**
   * 下载并打印PDF
   * @private
   */
  async _downloadAndPrintPDF(downloadUrl, autoClose, windowTimeout, hideWindow) {
    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error('未找到认证信息，请重新登录');
    }

    console.log('开始获取PDF数据用于打印...');

    // 使用fetch获取PDF文件
    const pdfFetchResponse = await fetch(`/api/${downloadUrl}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!pdfFetchResponse.ok) {
      let errorMessage = '获取PDF文件失败';
      try {
        const errorData = await pdfFetchResponse.json();
        errorMessage = errorData.message || errorMessage;
      } catch (jsonError) {
        // 如果响应不是JSON格式，使用响应状态文本
        errorMessage = pdfFetchResponse.statusText || `HTTP ${pdfFetchResponse.status}`;
      }
      throw new Error(errorMessage);
    }

    // 获取PDF blob数据
    const pdfBlob = await pdfFetchResponse.blob();
    const blobUrl = window.URL.createObjectURL(pdfBlob);

    console.log('PDF blob URL创建成功，准备打印...');

    if (hideWindow) {
      // 使用iframe方式，完全不显示窗口
      this._printWithIframe(blobUrl);
    } else {
      // 使用传统窗口方式
      const printWindow = window.open(blobUrl, '_blank', 'width=800,height=600,scrollbars=yes,resizable=yes');
      
      if (!printWindow) {
        window.URL.revokeObjectURL(blobUrl);
        throw new Error('无法打开打印窗口，请检查浏览器设置');
      }

      // 管理打印窗口
      this._managePrintWindow(printWindow, blobUrl, autoClose, windowTimeout);
    }
  }

  /**
   * 使用iframe进行静默打印，优化版本
   * @private
   */
  _printWithIframe(blobUrl) {
    // 创建完全隐藏的iframe
    const iframe = document.createElement('iframe');
    iframe.style.display = 'none';
    iframe.style.position = 'absolute';
    iframe.style.width = '0px';
    iframe.style.height = '0px';
    iframe.style.border = 'none';
    iframe.style.visibility = 'hidden';
    iframe.src = blobUrl;
    
    // 添加到body
    document.body.appendChild(iframe);

    // 设置iframe属性以优化打印
    iframe.onload = () => {
      try {
        console.log('PDF iframe加载完成，准备打印...');
        
        // 延迟确保PDF完全渲染
        setTimeout(() => {
          try {
            // 获取iframe的window对象
            const iframeWindow = iframe.contentWindow;
            
            if (iframeWindow) {
              // 聚焦到iframe
              iframeWindow.focus();
              
              // 触发打印
              iframeWindow.print();
              
              console.log('打印预览已触发，等待用户操作...');
              
              // 设置清理机制 - 不依赖打印事件，而是检测文档状态
              this._setupIframeCleanup(iframe, blobUrl);
            } else {
              console.error('无法访问iframe的window对象');
              this._cleanupIframe(iframe, blobUrl);
            }
          } catch (error) {
            console.error('触发打印时出错:', error);
            this._cleanupIframe(iframe, blobUrl);
          }
        }, 1000); // 增加延迟确保PDF完全加载
        
      } catch (error) {
        console.error('iframe onload处理失败:', error);
        this._cleanupIframe(iframe, blobUrl);
      }
    };

    // 错误处理
    iframe.onerror = () => {
      console.error('iframe加载失败');
      this._cleanupIframe(iframe, blobUrl);
    };
  }

  /**
   * 设置iframe清理机制
   * @private
   */
  _setupIframeCleanup(iframe, blobUrl) {
    let isCleanedUp = false;

    // 方法1: 监听页面可见性变化
    const handleVisibilityChange = () => {
      // 当页面重新获得焦点时，延迟清理（用户可能完成了打印）
      if (!document.hidden) {
        setTimeout(() => {
          console.log('页面重新获得焦点，清理打印资源');
          if (!isCleanedUp) {
            isCleanedUp = true;
            this._cleanupIframe(iframe, blobUrl);
            removeAllListeners();
          }
        }, 2000);
      }
    };

    // 方法2: 监听窗口焦点变化
    const handleWindowFocus = () => {
      setTimeout(() => {
        console.log('窗口重新获得焦点，清理打印资源');
        if (!isCleanedUp) {
          isCleanedUp = true;
          this._cleanupIframe(iframe, blobUrl);
          removeAllListeners();
        }
      }, 2000);
    };

    // 方法3: 键盘事件监听（ESC键取消打印）
    const handleKeydown = (event) => {
      if (event.key === 'Escape') {
        console.log('检测到ESC键，用户可能取消了打印');
        if (!isCleanedUp) {
          isCleanedUp = true;
          this._cleanupIframe(iframe, blobUrl);
          removeAllListeners();
        }
      }
    };

    // 移除所有事件监听器的函数
    const removeAllListeners = () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('focus', handleWindowFocus);
      document.removeEventListener('keydown', handleKeydown);
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };

    // 添加事件监听器
    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('focus', handleWindowFocus);
    document.addEventListener('keydown', handleKeydown);

    // 设置一个较长的超时时间作为最后的清理保障（10分钟）
    const timeoutId = setTimeout(() => {
      console.log('打印超时，强制清理资源');
      if (!isCleanedUp) {
        isCleanedUp = true;
        this._cleanupIframe(iframe, blobUrl);
        removeAllListeners();
      }
    }, 10 * 60 * 1000);
  }

  /**
   * 清理iframe和相关资源
   * @private
   */
  _cleanupIframe(iframe, blobUrl) {
    try {
      if (iframe && iframe.parentNode) {
        document.body.removeChild(iframe);
      }
      if (blobUrl) {
        window.URL.revokeObjectURL(blobUrl);
      }
      console.log('iframe和blob资源已清理');
    } catch (error) {
      console.error('清理资源时出错:', error);
    }
  }

  /**
   * 管理打印窗口的生命周期
   * @private
   */
  _managePrintWindow(printWindow, blobUrl, autoClose, windowTimeout) {
    this.activeWindows.add(printWindow);
    let windowClosed = false;

    // 检查窗口是否被用户手动关闭
    const checkWindow = setInterval(() => {
      if (printWindow.closed) {
        windowClosed = true;
        clearInterval(checkWindow);
        window.URL.revokeObjectURL(blobUrl);
        this.activeWindows.delete(printWindow);
      }
    }, 500);

    // PDF加载完成后触发打印
    printWindow.addEventListener('load', () => {
      if (!windowClosed) {
        setTimeout(() => {
          if (!windowClosed && !printWindow.closed) {
            printWindow.print();

            // 自动关闭窗口
            if (autoClose) {
              setTimeout(() => {
                if (!windowClosed && !printWindow.closed) {
                  window.URL.revokeObjectURL(blobUrl);
                  printWindow.close();
                  this.activeWindows.delete(printWindow);
                }
                clearInterval(checkWindow);
              }, windowTimeout);
            }
          }
        }, 1000);
      }
    });

    // 如果load事件在3秒内没有触发，手动触发打印
    setTimeout(() => {
      if (!windowClosed && !printWindow.closed) {
        try {
          printWindow.print();
        } catch (e) {
          console.warn('手动触发打印失败:', e);
        }
      }
    }, 3000);
  }

  /**
   * 显示消息
   * @private
   */
  _showMessage(toast, type, message) {
    if (toast && typeof toast[type] === 'function') {
      toast[type](message);
    } else {
      // 降级到alert
      alert(message);
    }
  }

  /**
   * 获取默认的打印样式
   * @private
   */
  _getDefaultPrintStyles() {
    return `
      @media print {
        @page {
          size: A4;
          margin: 10mm;
        }
        
        body * {
          visibility: hidden !important;
        }
        
        #printArea, #printArea * {
          visibility: visible !important;
        }
        
        #printArea {
          position: absolute;
          left: 0;
          top: 0;
          width: 100%;
          padding: 0;
          margin: 0;
        }
        
        .modal, .modal-dialog, .modal-content {
          visibility: hidden !important;
          display: none !important;
        }
        
        .modal-backdrop {
          display: none !important;
        }
        
        .modal-header, .modal-footer, .btn-close {
          display: none !important;
        }
        
        .receipt-container {
          padding: 0 !important;
          border: none !important;
          font-family: 'SimSun', serif !important;
          font-size: 12pt !important;
          color: black !important;
          background: white !important;
        }
        
        .receipt-table {
          width: 100% !important;
          border-collapse: collapse !important;
        }
        
        .receipt-table td {
          padding: 4px 8px !important;
          border-bottom: 1px solid black !important;
          font-size: 12pt !important;
        }
        
        .signature-box {
          border: 1px solid black !important;
          padding: 10px !important;
          margin: 5px 0 !important;
        }
        
        .signature-line {
          border-bottom: 1px solid black !important;
          height: 20px !important;
          margin: 5px 0 !important;
        }
        
        .notice-section {
          border-top: 1px solid black !important;
          padding-top: 10px !important;
          margin-top: 15px !important;
          text-align: center !important;
        }
      }
    `;
  }

  /**
   * 关闭所有活动的打印窗口
   */
  closeAllPrintWindows() {
    this.activeWindows.forEach(window => {
      if (!window.closed) {
        window.close();
      }
    });
    this.activeWindows.clear();
  }

  /**
   * 预设配置 - 外币兑换打印
   */
  static getExchangeConfig(transactionDetails, toast, useHtmlMode = false, language = 'zh') {
    // 【调试】记录传入的语言参数
    console.log('【调试】getExchangeConfig - 传入的language参数:', language);
    
    // 根据语言设置消息
    const messages = {
      'zh': {
        success: '外币兑换票据生成成功',
        error: '生成外币兑换PDF时出错'
      },
      'en': {
        success: 'Exchange receipt generated successfully',
        error: 'Error generating exchange PDF'
      },
      'th': {
        success: 'สร้างใบเสร็จแลกเปลี่ยนสำเร็จ',
        error: 'เกิดข้อผิดพลาดในการสร้าง PDF แลกเปลี่ยน'
      }
    };
    
    const msg = messages[language] || messages['zh'];
    
    return {
      generateApiUrl: `exchange/transactions/${transactionDetails.id}/print-receipt`,
      downloadApiUrl: `exchange/transactions/${transactionDetails.transaction_no}/download-receipt`,
      requestData: {
        language: language  // 传递语言参数
      },
      successMessage: msg.success,
      errorPrefix: msg.error,
      toast: toast,
      useHtmlMode: useHtmlMode
    };
  }

  /**
   * 预设配置 - 余额调节打印
   */
  static getBalanceAdjustConfig(adjustmentDetails, toast) {
    // 【修复】安全获取语言设置，避免locale undefined错误
    let language = 'zh';
    try {
      // 【关键修复】优先从localStorage获取语言设置，因为toast可能没有$i18n
      const storedLocale = localStorage.getItem('language') || 'zh-CN';
      console.log('【调试】getBalanceAdjustConfig - localStorage locale:', storedLocale);
      
      if (storedLocale === 'en-US') {
        language = 'en';
      } else if (storedLocale === 'th-TH') {
        language = 'th';
      } else {
        language = 'zh'; // zh-CN 或其他中文格式
      }
      
      // 备用方案：如果toast有$i18n，也检查一下
      if (toast && toast.$i18n && toast.$i18n.locale) {
        const locale = toast.$i18n.locale;
        console.log('【调试】getBalanceAdjustConfig - toast.$i18n.locale:', locale);
        if (locale === 'en-US') {
          language = 'en';
        } else if (locale === 'th-TH') {
          language = 'th';
        }
      }
      
      console.log('【调试】getBalanceAdjustConfig - 最终语言:', language);
    } catch (error) {
      console.warn('获取语言设置失败，使用默认中文:', error);
      language = 'zh';
    }
    
    // 【修复】根据语言设置本地化消息
    const messages = {
      'zh': {
        success: '余额调节单据生成成功',
        error: '生成余额调节PDF时出错'
      },
      'en': {
        success: 'Balance adjustment receipt generated successfully',
        error: 'Error generating balance adjustment PDF'
      },
      'th': {
        success: 'ใบเสร็จการปรับยอดคงเหลือสร้างสำเร็จ',
        error: 'เกิดข้อผิดพลาดในการสร้าง PDF การปรับยอดคงเหลือ'
      }
    };
    
    const msg = messages[language] || messages['zh'];
    let successMessage = msg.success;
    let errorPrefix = msg.error;
    
    return {
      generateApiUrl: `balance-management/adjust/transactions/${adjustmentDetails.transaction_id}/print-receipt`,
      downloadApiUrl: `balance-management/adjust/transactions/${adjustmentDetails.transaction_no}/download-receipt?language=${language}`,
      requestData: {
        language: language  // 使用安全获取的语言设置
      },
      successMessage: successMessage,
      errorPrefix: errorPrefix,
      toast: toast,
      useHtmlMode: false
    };
  }

  /**
   * 预设配置 - 初始余额单个打印
   */
  static getInitialBalanceConfig(transactionId, transactionNo, toast) {
    // 获取语言设置
    let language = 'zh';
    try {
      const storedLocale = localStorage.getItem('language') || 'zh-CN';
      if (storedLocale === 'en-US') {
        language = 'en';
      } else if (storedLocale === 'th-TH') {
        language = 'th';
      }
    } catch (error) {
      console.warn('获取语言设置失败，使用默认中文:', error);
      language = 'zh';
    }
    
    return {
      generateApiUrl: `balance-management/initial/transactions/${transactionId}/print-receipt`,
      downloadApiUrl: `balance-management/initial/transactions/${transactionNo}/download-receipt?language=${language}`,
      successMessage: '期初余额单据生成成功',
      errorPrefix: '打印期初余额单据失败',
      toast: toast,
      useHtmlMode: false
    };
  }

  /**
   * 预设配置 - 初始余额汇总打印
   */
  static getInitialBalanceSummaryConfig(transactionRecords, toast, language = 'zh') {
    return {
      generateApiUrl: 'balance-management/initial/print-summary',
      downloadApiUrl: '', // 将在生成后动态设置
      requestData: {
        transaction_records: transactionRecords.map(item => ({
          currency_code: item.currency_code,
          old_balance: item.old_balance,
          new_balance: item.new_balance,
          change: item.change,
          transaction_no: item.transaction_no
        })),
        language: language  // 添加语言参数
      },
      successMessage: '期初余额汇总单据生成成功',
      errorPrefix: '生成汇总PDF失败',
      toast: toast
    };
  }

  /**
   * 特殊的汇总打印方法 - 用于初始余额汇总
   */
  async printSummaryPDF(config) {
    const {
      generateApiUrl,
      requestData = {},
      successMessage = 'PDF生成成功',
      errorPrefix = '打印失败',
      toast = null,
      autoClose = true,
              windowTimeout = 20000 // 延长到20秒，给用户更多时间进行打印操作
    } = config;

    try {
      console.log(`开始生成汇总PDF: ${generateApiUrl}`);
      console.log('传递的请求数据:', requestData);
      console.log('语言参数:', requestData.language);
      
      // 1. 调用后端API生成PDF
      const response = await this._callGenerateAPI(generateApiUrl, requestData);
      
      if (!response.success) {
        throw new Error(response.message || 'PDF生成失败');
      }
      
      console.log('汇总PDF生成成功:', response);
      
      // 2. 显示成功消息 - 使用后端返回的完整消息，避免前端硬编码
      const fullSuccessMessage = response.message || successMessage;
      this._showMessage(toast, 'success', fullSuccessMessage);
      
      // 3. 动态构建下载URL并打印PDF
      const downloadApiUrl = `balance-management/initial/download-summary/${response.summary_no}?language=${requestData.language || 'zh'}`;
      await this._downloadAndPrintPDF(downloadApiUrl, autoClose, windowTimeout, true);
      
      return true;
      
    } catch (error) {
      console.error('汇总PDF打印失败:', error);
      const errorMessage = `${errorPrefix}: ${error.response?.data?.message || error.message || '未知错误'}`;
      this._showMessage(toast, 'error', errorMessage);
      return false;
    }
  }

  /**
   * 预设配置 - 交易冲正PDF打印
   */
  static getReversalConfig(reversalTransactionId, toast, language = 'zh') {
    // 【修复】根据语言设置本地化消息
    const messages = {
      'zh': {
        success: '交易冲正单据生成成功',
        error: '生成交易冲正PDF时出错'
      },
      'en': {
        success: 'Transaction reversal receipt generated successfully',
        error: 'Error generating transaction reversal PDF'
      },
      'th': {
        success: 'ใบเสร็จการยกเลิกธุรกรรมสร้างสำเร็จ',
        error: 'เกิดข้อผิดพลาดในการสร้าง PDF การยกเลิกธุรกรรม'
      }
    };
    
    const msg = messages[language] || messages['zh'];
    
    return {
      generateApiUrl: `transactions/reversal/${reversalTransactionId}/print-receipt`,
      downloadApiUrl: `transactions/reversal/[TRANSACTION_NO]/download-receipt`, // 将在调用时动态替换
      requestData: {
        language: language  // 添加语言参数
      },
      successMessage: msg.success,
      errorPrefix: msg.error,
      toast: toast,
      useHtmlMode: false
    };
  }

  /**
   * 预设配置 - 交易冲正HTML打印 (已弃用，保留用于向后兼容)
   */
  static getReversalHTMLConfig(toast) {
    return {
      printAreaId: 'printArea',
      successMessage: '交易冲正凭证打印完成',
      toast: toast
    };
  }

  /**
   * 交易冲正专用PDF打印方法 - 处理动态URL替换
   */
  async printReversalPDF(config, transactionNo) {
    // 动态替换下载URL中的交易号
    const finalConfig = {
      ...config,
      downloadApiUrl: config.downloadApiUrl.replace('[TRANSACTION_NO]', transactionNo)
    };
    
    return await this.printPDF(finalConfig);
  }
}

// 创建单例实例
const printService = new PrintService();

// 导出类和实例
export { PrintService };
export default printService; 
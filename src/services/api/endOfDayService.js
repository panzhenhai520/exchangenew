import api from './index';
import axios from 'axios'; // Added missing import for axios
import { API_PREFIX } from '@/config/apiConfig';

/**
 * 日结操作相关API服务
 */
export default {
  /**
   * 获取日结状态
   * @returns {Promise} 包含日结状态的Promise
   */
  getEndOfDayStatus(date, branchId) {
    return api.get('/end_of_day/status', {
      params: { date, branch_id: branchId }
    });
  },

  /**
   * 获取日结汇总信息
   * @param {string} date 日期
   * @param {string|number} branchId 网点ID
   * @returns {Promise} 包含日结汇总信息的Promise
   */
  getSummary(date, branchId) {
    return api.get('/end_of_day/summary', {
      params: { date, branch_id: branchId }
    });
  },

  /**
   * 开始日结操作
   * @param {Object} data 日结参数
   * @returns {Promise} 日结操作结果的Promise
   */
  processEndOfDay(data = {}) {
    return api.post('/end_of_day/start', {
      date: data.date,
      branch_id: data.branchId
    });
  },

  /**
   * 获取日结历史
   * @param {Object} params 查询参数
   * @returns {Promise} 包含日结历史的Promise
   */
  getEndOfDayHistory(params = {}) {
    return api.get('/end_of_day/history', { 
      params: {
        branch_id: params.branchId,
        start_date: params.startDate,
        end_date: params.endDate
      }
    });
  },

  /**
   * 获取特定日结记录详情
   * @param {number|string} id 日结记录ID
   * @returns {Promise} 包含日结记录详情的Promise
   */
  getEndOfDayDetail(id) {
    return api.get(`/end_of_day/${id}`);
  },

  /**
   * 确认日结操作
   * @param {number|string} id 日结记录ID
   * @returns {Promise} 确认结果的Promise
   */
  confirmEndOfDay(id) {
    return api.post(`/end_of_day/${id}/confirm`);
  },

  /**
   * 取消日结操作
   * @param {number|string} id 日结记录ID
   * @param {Object} reason 取消原因
   * @returns {Promise} 取消结果的Promise
   */
  cancelEndOfDay(id, reason) {
    return api.post(`/end_of_day/${id}/cancel`, { reason });
  },

  /**
   * 获取日结报表
   * @param {string} date 日期
   * @param {string|number} branchId 网点ID
   * @returns {Promise} 包含报表URL的Promise
   */
  getReport(date, branchId) {
    return api.get('/end_of_day/report', {
      params: { date, branch_id: branchId }
    });
  },

  /**
   * 生成收入统计报表
   * @param {number|string} eodId 日结ID
   * @returns {Promise} 包含收入统计结果的Promise
   */
  generateIncomeStatistics(eodId) {
    return api.post(`/end_of_day/${eodId}/income-statistics`);
  },

  /**
   * 确认报表为最终版本
   * @param {number|string} eodId 日结ID
   * @returns {Promise} 确认结果的Promise
   */
  finalizeReports(eodId) {
    return api.post(`/end_of_day/${eodId}/finalize-reports`);
  },

  /**
   * 打印收入报表
   * @param {number|string} eodId 日结ID
   * @param {Object} options 打印选项
   * @returns {Promise} 打印结果的Promise
   */
  printIncomeReports(eodId, options = {}) {
    return api.post(`/end_of_day/${eodId}/print-reports`, {
      report_type: 'income',
      language: options.language || 'zh'
    });
  },

  /**
   * 打印综合报表
   * @param {number|string} eodId 日结ID
   * @param {Object} options 打印选项
   * @returns {Promise} 打印结果的Promise
   */
  printComprehensiveReports(eodId, options = {}) {
    return api.post(`/end_of_day/${eodId}/print-comprehensive-reports`, {
      report_type: 'comprehensive',
      language: options.language || 'zh'
    });
  },

  /**
   * 获取日结历史记录
   * @param {Object} params 查询参数
   * @returns {Promise} 包含历史记录的Promise
   */
  getEodHistory(params = {}) {
    return api.get('/end_of_day/history', {
      params: {
        page: params.page || 1,
        per_page: params.per_page || 20,
        start_date: params.start_date,
        end_date: params.end_date
      }
    });
  },

  /**
   * 获取日结历史详细信息
   * @param {number|string} eodId 日结ID
   * @returns {Promise} 包含详细信息的Promise
   */
  getEodHistoryDetail(eodId) {
    return api.get(`/end_of_day/${eodId}/history-detail`);
  },

  /**
   * 重新打印日结报表
   * @param {number|string} eodId 日结ID
   * @param {Object} options 打印选项
   * @returns {Promise} 重新打印结果的Promise
   */
  reprintEodReports(eodId, options = {}) {
    return api.post(`/end_of_day/${eodId}/reprint-reports`, {
      report_type: options.report_type || 'all',
      language: options.language || 'zh'
    });
  },

  /**
   * 获取币种交易明细
   * @param {string} currencyCode 币种代码
   * @param {Object} options 查询选项
   * @returns {Promise} 包含交易明细的Promise
   */
  getCurrencyTransactionDetails(currencyCode, options = {}) {
    return api.get(`/reports/income/currency/${currencyCode}/transactions`, {
      params: {
        date: options.date || new Date().toISOString().split('T')[0],
        branch_id: options.branch_id,
        page: options.page || 1,
        per_page: options.per_page || 20
      }
    });
  },

  /**
   * 获取日结记录的PDF文件列表
   * @param {number|string} eodId 日结ID
   * @returns {Promise} 包含PDF文件列表的Promise
   */
  getEodPdfFiles(eodId) {
    return api.get(`/end_of_day/${eodId}/pdf-files`);
  },

  /**
   * 下载收入报表PDF文件（从manager目录）
   * @param {number|string} eodId 日结ID
   * @returns {Promise} 返回PDF文件的Blob
   */
  downloadIncomeReport(eodId) {
    return api.get(`/end_of_day/${eodId}/download-income-report`, {
      responseType: 'blob'
    });
  },

  /**
   * 获取特定PDF文件
   * @param {number|string} eodId 日结ID
   * @param {string} filename 文件名
   * @returns {Promise} 包含PDF文件URL的Promise
   */
  getEodPdfFile(eodId, filename) {
    // 根据文件名类型构建正确的URL
    let url = ''
    
    if (filename.includes('income')) {
      // 收入报表
      const language = filename.includes('_en') ? 'en' : filename.includes('_th') ? 'th' : 'zh'
      url = `/end_of_day/history/${eodId}/income-pdf/view?language=${language}`
    } else if (filename.includes('cashout')) {
      // 交款报表
      const language = filename.includes('_en') ? 'en' : filename.includes('_th') ? 'th' : 'zh'
      url = `/end_of_day/history/${eodId}/cashout-pdf/view?language=${language}`
    } else if (filename.includes('Diff')) {
      // 差额报表
      const language = filename.includes('_en') ? 'en' : filename.includes('_th') ? 'th' : 'zh'
      url = `/end_of_day/history/${eodId}/difference-pdf/view?language=${language}`
    } else {
      // 默认收入报表
      url = `/end_of_day/history/${eodId}/income-pdf/view`
    }
    
    const fullUrl = `${API_PREFIX}${url}`
    
    return axios.get(fullUrl, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json'
      },
      responseType: 'blob'
    });
  }
};

import api from './index';

/**
 * AMLO审核API服务
 * 提供预约审核、报告上报的核心接口
 */
export default {
  /**
   * 查询预约记录列表
   * @param {Object} params 查询参数
   * @param {string} params.status 状态过滤 (pending/approved/rejected/completed/reported)
   * @param {number} params.page 页码，默认1
   * @param {number} params.page_size 每页记录数，默认20
   * @param {string} params.start_date 开始日期
   * @param {string} params.end_date 结束日期
   * @param {string} params.customer_id 客户证件号
   * @param {string} params.report_type 报告类型
   * @returns {Promise} 包含预约记录列表的Promise
   */
  getReservations(params = {}) {
    return api.get('/amlo/reservations', { params });
  },

  /**
   * 审核预约记录
   * @param {number} reservationId 预约记录ID
   * @param {Object} data 审核数据
   * @param {string} data.action 操作 (approve/reject)
   * @param {string} data.rejection_reason 驳回原因（驳回时必填）
   * @param {string} data.remarks 备注信息
   * @returns {Promise} 包含审核结果的Promise
   */
  auditReservation(reservationId, data) {
    return api.post(`/amlo/reservations/${reservationId}/audit`, data);
  },

  /**
   * 反审核预约记录
   * @param {number} reservationId 预约记录ID
   * @param {Object} data 反审核数据
   * @param {string} data.remarks 备注信息
   * @returns {Promise} 包含反审核结果的Promise
   */
  reverseAudit(reservationId, data = {}) {
    return api.post(`/amlo/reservations/${reservationId}/reverse-audit`, data);
  },

  /**
   * 查询AMLO报告列表
   * @param {Object} params 查询参数
   * @param {boolean} params.is_reported 是否已上报
   * @param {number} params.page 页码，默认1
   * @param {number} params.page_size 每页记录数，默认20
   * @param {string} params.start_date 开始日期
   * @param {string} params.end_date 结束日期
   * @param {string} params.report_type 报告类型
   * @param {string} params.customer_id 客户证件号
   * @returns {Promise} 包含报告列表的Promise
   */
  getReports(params = {}) {
    return api.get('/amlo/reports', { params });
  },

  /**
   * 批量上报AMLO报告
   * @param {Array<number>} reportIds 报告ID数组
   * @returns {Promise} 包含批量上报结果的Promise
   */
  batchReport(reportIds) {
    return api.post('/amlo/reports/batch-report', {
      report_ids: reportIds
    });
  },

  /**
   * 完成预约（交易完成后）
   * @param {number} reservationId 预约记录ID
   * @param {Object} data 完成数据
   * @param {number} data.linked_transaction_id 关联交易ID
   * @returns {Promise} 包含完成结果的Promise
   */
  completeReservation(reservationId, data) {
    return api.post(`/amlo/reservations/${reservationId}/complete`, data);
  },

  /**
   * 生成AMLO报告PDF文件
   * @param {number} reportId 报告ID
   * @returns {Promise} 返回PDF文件流
   */
  generateReportPDF(reportId) {
    return api.get(`/amlo/reports/${reportId}/generate-pdf`, {
      responseType: 'blob'
    });
  },

  /**
   * 批量生成AMLO报告PDF文件（打包为ZIP）
   * @param {Array<number>} reportIds 报告ID数组
   * @returns {Promise} 返回ZIP文件流
   */
  batchGeneratePDF(reportIds) {
    return api.post('/amlo/reports/batch-generate-pdf', {
      report_ids: reportIds
    }, {
      responseType: 'blob'
    });
  }
};

import api from './index';

/**
 * RepForm核心API服务
 * 提供动态报告生成的核心接口
 */
export default {
  /**
   * 获取所有报告类型列表
   * @returns {Promise} 包含报告类型的Promise
   */
  getReportTypes() {
    return api.get('/repform/report-types');
  },

  /**
   * 获取表单定义
   * @param {string} reportType 报告类型 (AMLO-1-01, AMLO-1-02, etc.)
   * @param {string} language 语言 (zh/en/th)，默认zh
   * @returns {Promise} 包含表单定义的Promise
   */
  getFormDefinition(reportType, language = 'zh') {
    return api.get(`/repform/form-definition/${reportType}`, {
      params: { language }
    });
  },

  /**
   * 获取表单Schema（供前端渲染）
   * @param {string} reportType 报告类型
   * @param {string} language 语言 (zh/en/th)，默认zh
   * @returns {Promise} 包含表单Schema的Promise
   */
  getFormSchema(reportType, language = 'zh') {
    return api.get(`/repform/form-schema/${reportType}`, {
      params: { language }
    });
  },

  /**
   * 检查触发条件
   * @param {Object} data 检查数据
   * @param {string} data.report_type 报告类型
   * @param {Object} data.data 交易数据 {total_amount, currency_code, customer_id}
   * @param {number} data.branch_id 分支ID
   * @returns {Promise} 包含触发结果的Promise
   * @example
   * checkTrigger({
   *   report_type: 'AMLO-1-01',
   *   data: {
   *     total_amount: 6000000,
   *     currency_code: 'USD',
   *     customer_id: '1234567890123'
   *   },
   *   branch_id: 1
   * })
   */
  checkTrigger(data) {
    return api.post('/repform/check-trigger', data);
  },

  /**
   * 验证表单数据
   * @param {string} reportType 报告类型
   * @param {Object} formData 表单数据
   * @returns {Promise} 包含验证结果的Promise
   */
  validateForm(reportType, formData) {
    return api.post('/repform/validate-form', {
      report_type: reportType,
      form_data: formData
    });
  },

  /**
   * 保存预约兑换记录
   * @param {Object} data 预约数据
   * @param {string} data.customer_id 客户证件号
   * @param {string} data.customer_name 客户姓名
   * @param {string} data.customer_country_code 客户国家代码
   * @param {number} data.currency_id 币种ID
   * @param {string} data.direction 方向 (buy/sell)
   * @param {number} data.amount 外币金额
   * @param {number} data.local_amount 本币金额
   * @param {number} data.rate 汇率
   * @param {string} data.trigger_type 触发类型 (CTR/ATR/STR)
   * @param {string} data.report_type 报告类型
   * @param {Object} data.form_data 表单数据
   * @param {string} data.exchange_type 兑换类型
   * @param {string} data.funding_source 资金来源
   * @returns {Promise} 包含保存结果的Promise
   */
  saveReservation(data) {
    return api.post('/repform/save-reservation', data);
  },

  /**
   * 获取预约记录详情
   * @param {number} reservationId 预约记录ID
   * @returns {Promise} 包含预约记录详情的Promise
   */
  getReservation(reservationId) {
    return api.get(`/repform/reservation/${reservationId}`);
  },

  /**
   * 获取客户历史交易统计
   * @param {string} customerId 客户证件号
   * @param {number} days 统计天数，默认30
   * @returns {Promise} 包含客户历史统计的Promise
   */
  getCustomerHistory(customerId, days = 30) {
    return api.get(`/repform/customer-history/${customerId}`, {
      params: { days }
    });
  }
};

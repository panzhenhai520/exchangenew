import api from './index';

/**
 * 交易查询相关API服务
 */
export default {
  /**
   * 查询交易记录
   * @param {Object} params 查询参数
   * @returns {Promise} 包含交易记录的Promise
   */
  queryTransactions(params = {}) {
    return api.get('/transactions/query', { params });
  },

  /**
   * 获取交易详情
   * @param {number|string} id 交易ID
   * @returns {Promise} 包含交易详情的Promise
   */
  getTransaction(id) {
    return api.get(`/transactions/${id}`);
  },

  /**
   * 获取最近交易
   * @param {number} limit 限制数量
   * @returns {Promise} 包含最近交易的Promise
   */
  getRecentTransactions(limit = 10) {
    return api.get('/transactions/recent', { params: { limit } });
  },

  /**
   * 获取交易统计
   * @param {Object} params 统计参数
   * @returns {Promise} 包含交易统计的Promise
   */
  getTransactionStats(params = {}) {
    return api.get('/transactions/stats', { params });
  },

  /**
   * 导出交易记录
   * @param {Object} params 导出参数
   * @returns {Promise} 导出结果的Promise
   */
  exportTransactions(params = {}) {
    return api.get('/transactions/export', { 
      params,
      responseType: 'blob' 
    });
  },

  /**
   * 取消交易
   * @param {number|string} id 交易ID
   * @param {Object} reason 取消原因
   * @returns {Promise} 取消结果的Promise
   */
  cancelTransaction(id, reason) {
    return api.post(`/transactions/${id}/cancel`, { reason });
  }
};

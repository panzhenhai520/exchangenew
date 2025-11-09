import api from './index';

/**
 * 余额查询相关API服务
 */
export default {
  /**
   * 获取余额列表
   * @param {Object} params 查询参数
   * @returns {Promise} 包含余额列表的Promise
   */
  getBalances(params = {}) {
    return api.get('/balances/query', { params });
  },

  /**
   * 获取特定货币的余额
   * @param {number|string} currencyId 货币ID
   * @returns {Promise} 包含特定货币余额的Promise
   */
  getCurrencyBalance(currencyId) {
    return api.get(`/balances/currency/${currencyId}`);
  },

  /**
   * 获取特定分支机构的余额
   * @param {number|string} branchId 分支机构ID
   * @returns {Promise} 包含特定分支机构余额的Promise
   */
  getBranchBalance(branchId) {
    return api.get(`/balances/branch/${branchId}`);
  },

  /**
   * 获取余额历史记录
   * @param {Object} params 查询参数
   * @returns {Promise} 包含余额历史记录的Promise
   */
  getBalanceHistory(params = {}) {
    return api.get('/balances/history', { params });
  },

  /**
   * 调整余额
   * @param {Object} adjustmentData 调整数据
   * @returns {Promise} 调整结果的Promise
   */
  adjustBalance(adjustmentData) {
    return api.post('/balance-management/adjust', adjustmentData);
  },

  /**
   * 获取当前余额
   * @param {number} currencyId 币种ID
   * @returns {Promise} 当前余额信息
   */
  getCurrentBalance(currencyId) {
    return api.get(`/balance-management/current/${currencyId}`);
  },

  /**
   * 获取余额报警状态
   * @param {number} currencyId 币种ID
   * @returns {Promise} 余额报警状态信息
   */
  getAlertStatus(currencyId) {
    return api.get(`/balance-management/alert-status/${currencyId}`);
  },

  /**
   * 检查交易对余额的影响
   * @param {Object} transactionData 交易数据
   * @returns {Promise} 交易影响分析
   */
  checkTransactionImpact(transactionData) {
    return api.post('/balance-management/check-transaction-impact', transactionData);
  }
};

// 兼容性导出
export const balanceService = {
  getCurrentBalance: (currencyId) => api.get(`/balance-management/current/${currencyId}`),
  getAlertStatus: (currencyId) => api.get(`/balance-management/alert-status/${currencyId}`),
  checkTransactionImpact: (data) => api.post('/balance-management/check-transaction-impact', data)
};

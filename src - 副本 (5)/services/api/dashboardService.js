import api from './index';
import rateService from './rateService';

/**
 * 仪表盘相关API服务
 */
export default {
  /**
   * 获取仪表盘概览数据
   * @returns {Promise} 包含仪表盘概览数据的Promise
   */
  getDashboardOverview() {
    return api.get('/dashboard/overview');
  },

  /**
   * 获取交易统计数据
   * @param {Object} params 查询参数
   * @returns {Promise} 包含交易统计数据的Promise
   */
  getTransactionStats(params = {}) {
    return api.get('/dashboard/transaction_stats', { params });
  },

  /**
   * 获取货币余额统计
   * @returns {Promise} 包含货币余额统计的Promise
   */
  getCurrencyBalanceStats() {
    return api.get('/dashboard/currency_balance_stats');
  },

  /**
   * 获取分支机构统计
   * @returns {Promise} 包含分支机构统计的Promise
   */
  getBranchStats() {
    return api.get('/dashboard/branch_stats');
  },

  /**
   * 获取操作员统计
   * @returns {Promise} 包含操作员统计的Promise
   */
  getOperatorStats() {
    return api.get('/dashboard/operator_stats');
  },

  /**
   * 获取时间段内的交易趋势
   * @param {Object} params 查询参数
   * @returns {Promise} 包含交易趋势的Promise
   */
  getTransactionTrends(params = {}) {
    return api.get('/dashboard/transaction_trends', { params });
  },

  /**
   * 获取当前汇率
   * @returns {Promise} 包含当前汇率的Promise
   */
  getCurrentRates() {
    return rateService.getCurrentRates();
  },

  /**
   * 获取最近交易
   * @param {number} limit 限制数量
   * @returns {Promise} 包含最近交易的Promise
   */
  getRecentTransactions(limit = 10) {
    return api.get('/dashboard/recent_transactions', { params: { limit } });
  },

  /**
   * 获取业务统计数据
   * @returns {Promise} 包含业务统计数据的Promise
   */
  getBusinessStats() {
    return api.get('/dashboard/business-stats');
  }
};

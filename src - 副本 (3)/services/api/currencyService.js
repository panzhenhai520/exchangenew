import api from './index';
import rateService from './rateService';

/**
 * 货币服务API
 */
export default {
  /**
   * 获取所有支持的币种
   * @returns {Promise} 包含货币列表的Promise
   */
  getCurrencies() {
    // 调用系统管理的币种API，获取所有币种
    return api.get('/system/currencies');
  },

  /**
   * 获取网点可用的外币列表
   * @returns {Promise} 包含网点可用外币列表的Promise
   */
  getBranchCurrencies() {
    // 使用 available_currencies 接口，它会自动使用当前用户的 branch_id
    return api.get('/rates/available_currencies');
  },

  /**
   * 获取当前汇率
   * @returns {Promise} 包含当前汇率的Promise
   */
  getExchangeRates() {
    return rateService.getCurrentRates();
  },

  /**
   * 获取特定币种的汇率历史
   * @param {string} currencyCode 币种代码
   * @param {Object} [params] 查询参数
   * @returns {Promise} 包含特定币种汇率历史的Promise
   */
  getCurrencyRateHistory(currencyCode, params) {
    return rateService.getCurrencyRateHistory(currencyCode, params);
  },

  /**
   * 执行货币兑换交易
   * @param {Object} exchangeData 兑换数据
   * @returns {Promise} 兑换结果的Promise
   */
  executeExchangeTransaction(exchangeData) {
    return api.post('/exchange/execute', exchangeData);
  },

  /**
   * 获取货币兑换历史
   * @param {Object} params 查询参数
   * @returns {Promise} 包含兑换历史的Promise
   */
  getExchangeHistory(params) {
    return api.get('/exchange/history', { params });
  }
};

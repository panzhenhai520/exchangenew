import api from './index';

/**
 * BOT报告API服务
 * 提供BOT报表查询和导出的核心接口
 */
export default {
  /**
   * 检查BOT触发条件
   * @param {Object} data 检查数据
   * @param {boolean} data.use_fcd 是否使用FCD账户
   * @param {string} data.direction 交易方向 (buy/sell)
   * @param {number} data.local_amount 本币金额
   * @param {number} data.verification_amount 验证金额(换算后)
   * @param {string} data.currency_code 货币代码
   * @param {number} data.branch_id 网点ID(可选)
   * @returns {Promise} 包含触发结果的Promise
   * @example
   * checkBOTTrigger({
   *   use_fcd: false,
   *   direction: 'buy',
   *   local_amount: 2000000,
   *   verification_amount: 50000,
   *   currency_code: 'USD'
   * })
   */
  checkBOTTrigger(data) {
    return api.post('/bot/check-trigger', data);
  },

  /**
   * 查询T+1买入外币报表数据
   * @param {string} date 交易日期，默认昨天 (格式: YYYY-MM-DD)
   * @returns {Promise} 包含买入外币报表数据的Promise
   */
  getT1BuyFX(date) {
    return api.get('/bot/t1-buy-fx', {
      params: { date }
    });
  },

  /**
   * 查询T+1卖出外币报表数据
   * @param {string} date 交易日期，默认昨天 (格式: YYYY-MM-DD)
   * @returns {Promise} 包含卖出外币报表数据的Promise
   */
  getT1SellFX(date) {
    return api.get('/bot/t1-sell-fx', {
      params: { date }
    });
  },

  /**
   * 导出BOT完整报表Excel（从manager目录）
   * @param {string} date 保留兼容性（可为null）
   * @param {number} month 月份 (1-12)
   * @param {number} year 年份 (公历)
   * @returns {Promise} 返回Excel文件流
   */
  exportBuyFX(date, month, year) {
    const params = {};
    if (month && year) {
      params.month = month;
      params.year = year;
    } else if (date) {
      // 从日期解析年月（兼容旧代码）
      const d = new Date(date);
      params.month = d.getMonth() + 1;
      params.year = d.getFullYear();
    }
    
    return api.get('/bot/export-buy-fx', {
      params,
      responseType: 'blob'
    });
  },

  /**
   * 导出BOT完整报表Excel（与exportBuyFX相同）
   * @param {string} date 保留兼容性（可为null）
   * @param {number} month 月份 (1-12)
   * @param {number} year 年份 (公历)
   * @returns {Promise} 返回Excel文件流
   */
  exportSellFX(date, month, year) {
    return this.exportBuyFX(date, month, year);
  },

  /**
   * 保存BOT买入外币报表记录
   * @param {Object} data 报表数据
   * @param {number} data.transaction_id 交易ID
   * @param {string} data.report_date 报表日期
   * @param {Object} data.json_data JSON数据
   * @returns {Promise} 包含保存结果的Promise
   */
  saveBuyFX(data) {
    return api.post('/bot/save-buy-fx', data);
  },

  /**
   * 保存BOT卖出外币报表记录
   * @param {Object} data 报表数据
   * @param {number} data.transaction_id 交易ID
   * @param {string} data.report_date 报表日期
   * @param {Object} data.json_data JSON数据
   * @returns {Promise} 包含保存结果的Promise
   */
  saveSellFX(data) {
    return api.post('/bot/save-sell-fx', data);
  },

  /**
   * 导出多Sheet Excel文件（包含买入和卖出）
   * @param {string} date 交易日期 (格式: YYYY-MM-DD)
   * @returns {Promise} 返回多Sheet Excel文件流
   */
  async exportMultiSheetExcel(date) {
    // 注意：这个API需要后端支持，目前前端可以分别下载两个文件
    // 或者在前端合并两个请求的结果
    const [buyResponse, sellResponse] = await Promise.all([
      this.exportBuyFX(date),
      this.exportSellFX(date)
    ]);

    return {
      buyData: buyResponse,
      sellData: sellResponse
    };
  },

  /**
   * 获取BOT触发配置
   * @returns {Promise} 包含触发配置的Promise
   */
  getTriggerConfig() {
    return api.get('/bot/trigger-config');
  },

  /**
   * 保存BOT触发配置
   * @param {Object} config 配置数据
   * @returns {Promise} 包含保存结果的Promise
   */
  saveTriggerConfig(config) {
    return api.post('/bot/trigger-config', config);
  }
};

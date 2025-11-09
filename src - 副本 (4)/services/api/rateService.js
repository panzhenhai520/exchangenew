import api from './index';

/**
 * 汇率管理相关 API 服务
 */
export default {
  /**
   * 获取当前汇率（用于兑换和显示）
   * @param {boolean} publishedOnly 是否只获取当日发布的汇率
   * @returns {Promise}
   */
  getCurrentRates(publishedOnly = false) {
    return api.get('/rates/all', {
      params: {
        include_publish_info: true,  // 添加参数，请求包含发布信息
        published_only: publishedOnly  // 是否只返回当日发布的汇率
      }
    });
  },

  /**
   * ✅ 兼容旧调用名：getExchangeRatePairs
   * 实际调用的是 getCurrentRates
   */
  getExchangeRatePairs() {
    return this.getCurrentRates();
  },

  /**
   * 获取支持的币种列表
   * @returns {Promise}
   */
  getCurrencies() {
    return api.get('/rates/available_currencies');
  },

  /**
   * 获取全部汇率数据（例如用于汇率看板）
   * @returns {Promise}
   */
  getExchangeRates() {
    return api.get('/rates/all');
  },

  /**
   * 获取历史汇率记录
   * @param {Object} params 查询参数
   * @returns {Promise}
   */
  getHistoricalRates(params = {}) {
    return api.get('/rates/historical', { params });
  },

  /**
   * 更新单个汇率记录
   * @param {Object} rateData 汇率数据
   * @returns {Promise}
   */
  updateRate(rateData) {
    return api.post('/rates/set_rate', rateData);
  },

  /**
   * 批量更新汇率记录
   * @param {Array} ratesData 汇率数组
   * @returns {Promise}
   */
  batchUpdateRates(ratesData) {
    return api.post('/rates/batch_update', { rates: ratesData });
  },

  /**
   * 获取特定币种的历史汇率
   * @param {string} currencyCode 币种代码
   * @param {Object} params 查询参数
   * @returns {Promise}
   */
  getCurrencyRateHistory(currencyCode, params = {}) {
    return api.get(`/rates/currency/${currencyCode}/history`, { params });
  },

  /**
   * 获取汇率历史数据（用于仪表盘图表）
   * @param {number} currencyId 币种ID
   * @param {number} days 天数
   * @returns {Promise}
   */
  getRateHistory(currencyId, days = 7) {
    return api.get(`/rates/currency/${currencyId}/history`, { params: { days } });
  },

  /**
   * 发布每日汇率
   * @param {string} [targetDate] 可选的目标日期，格式：YYYY-MM-DD
   * @returns {Promise}
   */
  publishDailyRates(targetDate) {
    return api.post('/rates/publish_daily_rates', targetDate ? { target_date: targetDate } : {});
  },

  /**
   * 新增币种
   * @param {Object} currencyData 币种数据
   * @returns {Promise}
   */
  addCurrency(currencyData) {
    return api.post('/rates/add_currency', currencyData);
  },

  /**
   * 删除币种
   * @param {string} currencyCode 币种代码
   * @returns {Promise}
   */
  deleteCurrency(currencyCode) {
    return api.delete(`/rates/currencies/${currencyCode}`);
  },

  /**
   * 获取币种模板列表
   * @returns {Promise} 包含币种模板列表的Promise
   */
  getCurrencyTemplates(excludeCurrencyCodes = '') {
    const params = new URLSearchParams();
    if (excludeCurrencyCodes) {
      params.append('exclude_currency_codes', excludeCurrencyCodes);
    }
    return api.get(`/rates/currency_templates?${params.toString()}`);
  },

  /**
   * 获取今日有汇率的币种列表
   * @param {boolean} publishedOnly 是否只返回当日发布的货币
   * @returns {Promise}
   */
  getAvailableCurrencies(publishedOnly = false) {
    return api.get('/rates/available_currencies', {
      params: {
        published_only: publishedOnly
      }
    });
  },

  /**
   * 获取可用币种列表（支持是否需要汇率的过滤）
   * @param {Object} params 查询参数
   * @param {boolean} params.require_rate 是否需要有汇率
   * @param {boolean} params.include_base 是否包含本币
   * @returns {Promise}
   */
  getAvailableCurrenciesWithRate(params = {}) {
    return api.get('/rates/available_currencies', { params });
  },

  /**
   * 验证货币兑换交易（检查余额等）
   * @param {Object} transactionData 交易数据
   * @returns {Promise}
   */
  async validateExchangeTransaction(transactionData) {
    const userInfo = JSON.parse(localStorage.getItem('user') || '{}');
    console.log('验证交易 - 用户信息:', JSON.stringify(userInfo, null, 2));
    console.log('验证交易 - 原始交易数据:', JSON.stringify(transactionData, null, 2));
    
    // 根据交易模式确定类型：sell_foreign表示客户卖出外币，即网点买入外币
    const type = transactionData.exchangeMode === 'sell_foreign' ? 'buy' : 'sell';
    console.log('验证交易 - 交易类型:', type);
    
    try {
      // 获取币种ID
      const currencyId = await this.getCurrencyId(
        type === 'buy' ? transactionData.fromCurrency : transactionData.toCurrency
      );
      console.log('验证交易 - 币种ID:', currencyId);
      
      // 构造请求数据
      const requestData = {
        type: type,
        currency_id: currencyId,
        amount: type === 'buy' ? transactionData.fromAmount : transactionData.toAmount, // 外币金额
        customer_name: transactionData.customerName || '',
        customer_id: transactionData.customerId || ''
      };
      
      console.log('验证交易 - API请求数据:', JSON.stringify(requestData, null, 2));
      
      // 只验证交易，不执行
      const response = await api.post('/exchange/validate', requestData);
      console.log('验证交易 - API响应:', JSON.stringify(response.data, null, 2));
      return response;
    } catch (error) {
      console.error('验证交易失败 - 错误详情:', {
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        message: error.message
      });
      throw error;
    }
  },

  /**
   * 执行货币兑换交易
   * @param {Object} transactionData 交易数据
   * @returns {Promise}
   */
  async executeExchangeTransaction(transactionData) {
    console.log('执行交易 - 开始验证');
    console.log('交易数据详情:', {
      原始数据: transactionData,
      exchangeMode: transactionData.exchangeMode,
      amountType: transactionData.amountType,
      fromAmount: transactionData.fromAmount,
      toAmount: transactionData.toAmount,
      fromCurrency: transactionData.fromCurrency,
      toCurrency: transactionData.toCurrency,
      rate: transactionData.rate
    });

    try {
      // 先验证交易
      await this.validateExchangeTransaction(transactionData);
      
      console.log('执行交易 - 验证通过，准备执行');
      
      // 根据交易模式确定类型：sell_foreign表示客户卖出外币，即网点买入外币
      const type = transactionData.exchangeMode === 'sell_foreign' ? 'buy' : 'sell';
      
      // 保持原始输入的精度
      const rate = String(transactionData.rate); // 转换为字符串以保持精确值
      
      // 确定具体的交易状态
      const STATES = {
        S1: 'SELL_HAVE',    // 网点卖出外币，【用户支付】，输入的是本币，计算外币
        S2: 'SELL_WANT',    // 网点卖出外币，【顾客需要】，输入的是外币，计算本币
        B1: 'BUY_HAVE',     // 网点买入外币，【用户支付】，输入的是外币，计算本币
        B2: 'BUY_WANT'      // 网点买入外币，【顾客需要】，输入的是本币，计算外币
      };

      // 根据type和amountType确定当前状态
      const currentState = type === 'sell' 
        ? (transactionData.amountType === 'have' ? STATES.S1 : STATES.S2)
        : (transactionData.amountType === 'have' ? STATES.B1 : STATES.B2);

      let amount, localAmount;
      
      // 根据不同状态设置金额，amount写入exchange_transactions表的amount字段，localAmount写入local_amount字段
      switch (currentState) {
        case STATES.S1:  // 网点卖出外币，【用户支付】
          console.log('S1状态 - 用户支付本币，网点卖出外币:', {
            输入本币金额: transactionData.fromAmount,
            计算外币金额: transactionData.toAmount,
            当前状态: currentState
          });
          localAmount = Number(transactionData.fromAmount).toFixed(2);  // 用户输入的本币金额，确保为正数
          amount = (-Number(transactionData.toAmount)).toFixed(2);      // 计算出的外币，加负号
          console.log('S1状态 - 最终金额:', {
            localAmount,
            amount
          });
          break;

        case STATES.S2:  // 网点卖出外币，【顾客需要】
          amount = (-Number(transactionData.toAmount)).toFixed(2);    // 用户需要的外币，加负号 -> amount字段
          localAmount = Number(transactionData.fromAmount).toFixed(2); // 计算出的本币金额
          break;

        case STATES.B1:  // 网点买入外币，【用户支付】
          amount = Number(transactionData.fromAmount).toFixed(2);         // 用户输入的外币金额
          localAmount = (-Number(transactionData.toAmount)).toFixed(2);   // 计算出的本币金额，加负号
          break;

        case STATES.B2:  // 网点买入外币，【顾客需要】
          localAmount = (-Number(transactionData.toAmount)).toFixed(2);   // 计算出的本币金额，加负号
          amount = Number(transactionData.fromAmount).toFixed(2);         // 用户需要的外币金额
          break;
      }

      console.log('交易计算 - 详细信息:', {
        type,
        rate,
        currentState,
        fromAmount: transactionData.fromAmount,
        toAmount: transactionData.toAmount,
        localAmount: localAmount + ' -> local_amount字段',
        amount: amount + ' -> amount字段',
        amountType: transactionData.amountType
      });

      // 构造请求数据，确保金额正确写入对应的数据库字段
      const requestData = {
        type: type,
        currency_id: await this.getCurrencyId(
          type === 'buy' ? transactionData.fromCurrency : transactionData.toCurrency
        ),
        amount: amount,                // 写入exchange_transactions表的amount字段
        customer_name: transactionData.customerName,
        customer_id: transactionData.customerId,
        exchange_rate: rate,
        local_amount: localAmount,     // 写入exchange_transactions表的local_amount字段
        amountType: transactionData.amountType,
        // 添加用途和备注字段
        purpose: transactionData.purpose || '',
        remarks: transactionData.remarks || ''
      };
      
      console.log('执行交易 - API请求数据:', JSON.stringify(requestData, null, 2));
      
      // 执行交易
      const response = await api.post('/exchange/perform', requestData);
      console.log('执行交易 - API响应:', JSON.stringify(response.data, null, 2));
      return response;
    } catch (error) {
      console.error('执行交易失败 - 错误详情:', {
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        message: error.message
      });
      throw error;
    }
  },

  /**
   * 根据币种代码获取币种ID
   * @param {string} currencyCode 
   * @returns {Promise<number>}
   */
  async getCurrencyId(currencyCode) {
    const response = await api.get(`/currencies/code/${currencyCode}`);
    if (response.data && response.data.success) {
      return response.data.currency.id;
    }
    throw new Error(`Currency not found for code: ${currencyCode}`);
  },

  getBranchCurrency() {
    return api.get('/branch/current');
  }
};

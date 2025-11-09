import api from './index';

/**
 * 币种管理服务API
 */
export default {
  /**
   * 获取所有币种模板
   * @returns {Promise} 包含币种模板列表的Promise
   */
  getCurrencyTemplates() {
    return api.get('/currency-management/templates');
  },

  /**
   * 获取ISO标准国家数据
   * @returns {Promise} 包含国家数据列表的Promise
   */
  getISOCountries() {
    return api.get('/currency-management/iso-countries');
  },

  /**
   * 获取ISO标准货币数据（去重）
   * @returns {Promise} 包含货币数据列表的Promise
   */
  getISOCurrencies() {
    return api.get('/currency-management/iso-currencies');
  },

  /**
   * 新增币种模板
   * @param {Object} templateData 币种模板数据
   * @returns {Promise} 包含新增结果的Promise
   */
  addCurrencyTemplate(templateData) {
    return api.post('/currency-management/templates', templateData);
  },

  /**
   * 更新币种模板
   * @param {number} templateId 模板ID
   * @param {Object} templateData 更新的币种模板数据
   * @returns {Promise} 包含更新结果的Promise
   */
  updateCurrencyTemplate(templateId, templateData) {
    return api.put(`/currency-management/templates/${templateId}`, templateData);
  },

  /**
   * 删除币种模板
   * @param {number} templateId 模板ID
   * @returns {Promise} 包含删除结果的Promise
   */
  deleteCurrencyTemplate(templateId) {
    return api.delete(`/currency-management/templates/${templateId}`);
  },

  /**
   * 上传币种图标
   * @param {Object} fileData 文件数据 {file_data: base64, filename: string}
   * @returns {Promise} 包含上传结果的Promise
   */
  uploadFlag(fileData) {
    return api.post('/currency-management/upload-flag', fileData);
  },

  /**
   * 初始化币种模板数据
   * @param {boolean} force 是否强制重新初始化
   * @returns {Promise} 包含初始化结果的Promise
   */
  initCurrencyTemplates(force = false) {
    return api.post('/currency-management/init-templates', { force });
  }
}; 
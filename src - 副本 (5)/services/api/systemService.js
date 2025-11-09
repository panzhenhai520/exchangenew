import api from '../api';

/**
 * 系统维护相关 API 服务
 */
export default {
  /**
   * 获取所有币种（用于系统管理）
   * @returns {Promise}
   */
  async getCurrencies() {
    try {
      const response = await api.get('/system/currencies');
      return response;
    } catch (error) {
      if (error.response?.status === 403) {
        throw new Error('没有系统管理权限');
      }
      throw error;
    }
  }
}; 
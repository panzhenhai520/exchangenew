/**
 * 规范管理API服务
 * 处理兑换提醒信息维护、票据文件查看、余额报警设置的前端API调用
 */

import axios from 'axios';

// API基础URL
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? '/api/standards' 
  : 'http://192.168.0.18:5001/api/standards';

// 创建axios实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// 请求拦截器 - 添加认证token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = token.startsWith('Bearer ') ? token : `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器 - 处理错误
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token过期或无效，跳转到登录页
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

const standardsService = {
  // ==================== 兑换提醒信息维护 API ====================
  
  /**
   * 获取兑换提醒信息列表
   */
  getPurposeLimits() {
    return apiClient.get('/purpose-limits');
  },

  /**
   * 创建兑换提醒信息
   * @param {Object} data - 提醒信息数据
   */
  createPurposeLimit(data) {
    return apiClient.post('/purpose-limits', data);
  },

  /**
   * 更新兑换提醒信息
   * @param {number} id - 提醒信息ID
   * @param {Object} data - 更新数据
   */
  updatePurposeLimit(id, data) {
    return apiClient.put(`/purpose-limits/${id}`, data);
  },

  /**
   * 删除兑换提醒信息
   * @param {number} id - 提醒信息ID
   */
  deletePurposeLimit(id) {
    return apiClient.delete(`/purpose-limits/${id}`);
  },

  // ==================== 票据文件查看 API ====================

  /**
   * 获取可用的年份列表
   */
  getAvailableYears() {
    return apiClient.get('/receipt-files/years');
  },

  /**
   * 获取指定年份的可用月份列表
   * @param {string} year - 年份
   */
  getAvailableMonths(year) {
    return apiClient.get(`/receipt-files/months/${year}`);
  },

  /**
   * 获取指定年月的票据文件列表
   * @param {string} year - 年份
   * @param {string} month - 月份
   */
  getReceiptFiles(year, month) {
    return apiClient.get(`/receipt-files/${year}/${month}`);
  },

  /**
   * 记录票据打印操作
   * @param {string} filename - 文件名
   */
  recordPrintAction(filename) {
    return apiClient.post('/receipt-files/print', { filename });
  },

  // ==================== 余额报警设置 API ====================

  /**
   * 获取余额报警设置
   */
  getBalanceAlerts() {
    return apiClient.get('/balance-alerts');
  },

  /**
   * 创建或更新余额报警设置
   * @param {Object} data - 报警设置数据
   */
  createOrUpdateBalanceAlert(data) {
    return apiClient.post('/balance-alerts', data);
  },

  /**
   * 删除余额报警设置
   * @param {number} id - 报警设置ID
   */
  deleteBalanceAlert(id) {
    return apiClient.delete(`/balance-alerts/${id}`);
  },

  // ==================== 币种相关 API ====================

  /**
   * 获取可用的币种列表
   * 使用币种模板API获取所有币种模板，包括自定义图标信息
   * 这样规范管理可以提前设置所有币种的规范，不依赖汇率发布状态
   */
  getAvailableCurrencies() {
    // 使用currency_templates端点获取完整的币种信息，包括custom_flag_filename
    return apiClient.get('/rates/currency_templates');
  }
};

export default standardsService; 
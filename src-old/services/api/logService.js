import api from './index';

/**
 * 操作日志相关API服务
 */
export default {
  /**
   * 获取操作日志
   * @param {Object} params 查询参数
   * @returns {Promise} 包含操作日志的Promise
   */
  getSystemLogs(params = {}) {
    return api.get('system/logs', { params });
  },

  /**
   * 获取操作日志
   * @param {Object} params 查询参数
   * @returns {Promise} 包含操作日志的Promise
   */
  getOperationLogs(params = {}) {
    return api.get('system/logs', { params: { ...params, log_type: 'operation' } });
  },

  /**
   * 获取登录日志
   * @param {Object} params 查询参数
   * @returns {Promise} 包含登录日志的Promise
   */
  getLoginLogs(params = {}) {
    return api.get('system/logs', { params: { ...params, log_type: 'login' } });
  },

  /**
   * 获取日志详情
   * @param {number|string} id 日志ID
   * @returns {Promise} 包含日志详情的Promise
   */
  getLogDetail(id) {
    return api.get(`system/logs/${id}`);
  },

  /**
   * 导出日志
   * @param {Object} params 导出参数
   * @returns {Promise} 导出结果的Promise
   */
  exportLogs(params = {}) {
    return api.get('system/logs/export', { 
      params,
      responseType: 'blob' 
    });
  },

  /**
   * 记录新日志
   * @param {Object} logData 日志数据
   * @returns {Promise} 记录结果的Promise
   */
  createLog(logData) {
    return api.post('system/logs', logData);
  },

  // 日志管理相关API
  /**
   * 获取日志统计信息
   * @returns {Promise} 包含日志统计的Promise
   */
  getLogStats() {
    return api.get('log-management/stats');
  },

  /**
   * 获取日志文件列表
   * @returns {Promise} 包含日志文件列表的Promise
   */
  getLogFiles() {
    return api.get('log-management/files');
  },

  /**
   * 获取日志文件内容
   * @param {string} filename 文件名
   * @returns {Promise} 包含日志内容的Promise
   */
  getLogContent(filename) {
    return api.get(`log-management/files/${filename}/content`);
  },

  /**
   * 删除日志文件
   * @param {string} filename 文件名
   * @returns {Promise} 删除结果的Promise
   */
  deleteLogFile(filename) {
    return api.delete(`log-management/files/${filename}`);
  },

  /**
   * 清理日志文件
   * @param {Object} params 清理参数
   * @returns {Promise} 清理结果的Promise
   */
  cleanupLogs(params = {}) {
    return api.post('log-management/cleanup', params);
  },

  /**
   * 归档日志文件
   * @returns {Promise} 归档结果的Promise
   */
  archiveLogs() {
    return api.post('log-management/archive');
  },

  /**
   * 压缩日志文件
   * @returns {Promise} 压缩结果的Promise
   */
  compressLogs() {
    return api.post('log-management/compress');
  },

  /**
   * 导出日志文件
   * @returns {Promise} 导出结果的Promise
   */
  exportLogFiles() {
    return api.get('log-management/export');
  },

  /**
   * 获取最近操作记录
   * @returns {Promise} 包含最近操作记录的Promise
   */
  getRecentOperations() {
    return api.get('log-management/operations');
  },

  /**
   * 记录页面访问日志
   * @param {Object} accessData 页面访问数据
   * @returns {Promise} 记录结果的Promise
   */
  recordPageAccess(accessData) {
    return api.post('log-management/page-access', accessData);
  }
};

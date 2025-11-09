import api from './index';

/**
 * 操作员管理相关API服务
 */
export default {
  /**
   * 获取所有操作员
   * @param {Object} params 查询参数
   * @returns {Promise} 包含操作员列表的Promise
   */
  getOperators(params = {}) {
    return api.get('/operators', { params });
  },

  /**
   * 获取操作员详情
   * @param {number|string} id 操作员ID
   * @returns {Promise} 包含操作员详情的Promise
   */
  getOperator(id) {
    return api.get(`/operators/${id}`);
  },

  /**
   * 创建新操作员
   * @param {Object} operatorData 操作员数据
   * @returns {Promise} 创建结果的Promise
   */
  createOperator(operatorData) {
    return api.post('/operators', operatorData);
  },

  /**
   * 更新操作员
   * @param {number|string} id 操作员ID
   * @param {Object} operatorData 操作员数据
   * @returns {Promise} 更新结果的Promise
   */
  updateOperator(id, operatorData) {
    return api.put(`/operators/${id}`, operatorData);
  },

  /**
   * 删除操作员
   * @param {number|string} id 操作员ID
   * @returns {Promise} 删除结果的Promise
   */
  deleteOperator(id) {
    return api.delete(`/operators/${id}`);
  },

  /**
   * 获取操作员权限
   * @param {number|string} id 操作员ID
   * @returns {Promise} 包含操作员权限的Promise
   */
  getOperatorPermissions(id) {
    return api.get(`/operators/${id}/permissions`);
  },

  /**
   * 更新操作员权限
   * @param {number|string} id 操作员ID
   * @param {Object} permissionData 权限数据
   * @returns {Promise} 更新结果的Promise
   */
  updateOperatorPermissions(id, permissionData) {
    return api.put(`/operators/${id}/permissions`, permissionData);
  }
};

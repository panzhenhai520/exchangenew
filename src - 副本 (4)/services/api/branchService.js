import api from './index';

/**
 * 分支机构管理相关API服务
 */
export default {
  /**
   * 获取所有分支机构
   * @param {Object} params 查询参数
   * @returns {Promise} 包含分支机构列表的Promise
   */
  getBranches(params = {}) {
    console.log('Requesting branches from:', '/system/branches/');
    return api.get('/system/branches/', { params });
  },

  /**
   * 获取分支机构详情
   * @param {number|string} id 分支机构ID
   * @returns {Promise} 包含分支机构详情的Promise
   */
  getBranch(id) {
    return api.get(`/system/branches/${id}`);
  },

  /**
   * 创建新分支机构
   * @param {Object} branchData 分支机构数据
   * @returns {Promise} 创建结果的Promise
   */
  createBranch(branchData) {
    return api.post('/system/branches/', branchData);
  },

  /**
   * 更新分支机构
   * @param {number|string} id 分支机构ID
   * @param {Object} branchData 分支机构数据
   * @returns {Promise} 更新结果的Promise
   */
  updateBranch(id, branchData) {
    return api.put(`/system/branches/${id}`, branchData);
  },

  /**
   * 检查网点是否可以删除
   * @param {number|string} id 网点ID
   * @returns {Promise} 检查结果的Promise
   */
  checkBranchCanDelete(id) {
    return api.get(`/system/branches/${id}/check-delete`);
  },

  /**
   * 删除分支机构
   * @param {number|string} id 分支机构ID
   * @returns {Promise} 删除结果的Promise
   */
  deleteBranch(id) {
    return api.delete(`/system/branches/${id}`);
  },

  /**
   * 获取分支机构统计信息
   * @returns {Promise} 包含统计信息的Promise
   */
  getBranchStats() {
    return api.get('/system/branches/stats');
  }
};

import api from './index';

/**
 * 用户管理相关API服务
 */
export default {
  /**
   * 获取所有用户
   * @param {Object} params 查询参数
   * @returns {Promise} 包含用户列表的Promise
   */
  getUsers(params = {}) {
    return api.get('/users/', { params });
  },

  /**
   * 获取用户详情
   * @param {number|string} id 用户ID
   * @returns {Promise} 包含用户详情的Promise
   */
  getUser(id) {
    return api.get(`/users/${id}`);
  },

  /**
   * 创建新用户
   * @param {Object} userData 用户数据
   * @returns {Promise} 创建结果的Promise
   */
  createUser(userData) {
    return api.post('/users/', userData);
  },

  /**
   * 更新用户
   * @param {number|string} id 用户ID
   * @param {Object} userData 用户数据
   * @returns {Promise} 更新结果的Promise
   */
  updateUser(id, userData) {
    return api.put(`/users/${id}`, userData);
  },

  /**
   * 删除用户
   * @param {number|string} id 用户ID
   * @returns {Promise} 删除结果的Promise
   */
  deleteUser(id) {
    return api.delete(`/users/${id}`);
  },

  /**
   * 检查用户业务流水
   * @param {number|string} id 用户ID
   * @returns {Promise} 包含业务检查结果的Promise
   */
  checkUserBusiness(id) {
    return api.get(`/users/${id}/check-business`);
  },

  /**
   * 重置用户密码
   * @param {number|string} id 用户ID
   * @returns {Promise} 重置结果的Promise
   */
  resetPassword(id) {
    return api.post(`/users/${id}/reset_password`);
  },

  // 新增活跃状态相关API
  /**
   * 获取用户活跃状态记录
   * @param {number|string} userId 用户ID
   * @param {Object} params 查询参数
   * @returns {Promise} 包含活跃记录的Promise
   */
  getUserActivities(userId, params = {}) {
    return api.get(`/users/${userId}/activities`, { params });
  },

  /**
   * 获取活跃状态统计摘要
   * @param {Object} params 查询参数
   * @returns {Promise} 包含统计摘要的Promise
   */
  getActivitiesSummary(params = {}) {
    return api.get('/users/activities/summary', { params });
  },

  /**
   * 获取在线用户列表
   * @param {Object} params 查询参数
   * @returns {Promise} 包含在线用户列表的Promise
   */
  getOnlineUsers(params = {}) {
    return api.get('/users/online', { params });
  },

  // 权限相关API
  /**
   * 获取权限国际化描述
   * @param {string} language 语言代码 (zh, en, th)
   * @returns {Promise} 包含权限翻译的Promise
   */
  getPermissionTranslations(language = 'zh') {
    return api.get('/permissions/translations', { params: { language } });
  },

  /**
   * 创建或更新权限翻译
   * @param {Object} translationData 翻译数据
   * @returns {Promise} 创建结果的Promise
   */
  createPermissionTranslation(translationData) {
    return api.post('/permissions/translations', translationData);
  },

  /**
   * 获取所有权限
   * @param {string} language 语言代码 (zh, en, th)
   * @returns {Promise} 包含权限列表的Promise
   */
  getPermissions(language = null) {
    const params = {}
    if (language) {
      params.lang = language
    }
    return api.get('/permissions', { params });
  },

  /**
   * 获取所有角色
   * @returns {Promise} 包含角色列表的Promise
   */
  getRoles() {
    return api.get('/roles');
  },

  /**
   * 创建角色
   * @param {Object} roleData 角色数据
   * @returns {Promise} 创建结果的Promise
   */
  createRole(roleData) {
    return api.post('/roles', roleData);
  },

  /**
   * 更新角色
   * @param {number|string} id 角色ID
   * @param {Object} roleData 角色数据
   * @returns {Promise} 更新结果的Promise
   */
  updateRole(id, roleData) {
    return api.put(`/roles/${id}`, roleData);
  },

  /**
   * 删除角色
   * @param {number|string} id 角色ID
   * @returns {Promise} 删除结果的Promise
   */
  deleteRole(id) {
    return api.delete(`/roles/${id}`);
  },

  /**
   * 激活用户
   * @param {number} id 用户ID
   * @returns {Promise} 激活结果的Promise
   */
  activateUser(id) {
    return api.put(`/users/${id}/activate`);
  },

  /**
   * 停用用户
   * @param {number} id 用户ID
   * @returns {Promise} 停用结果的Promise
   */
  deactivateUser(id) {
    return api.put(`/users/${id}/deactivate`);
  }
};

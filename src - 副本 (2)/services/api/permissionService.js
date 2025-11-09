import api from './index';

/**
 * 权限管理相关API服务
 */
export default {
  /**
   * 获取所有角色
   * @returns {Promise} 包含角色列表的Promise
   */
  getRoles() {
    return api.get('/permissions/roles');
  },

  /**
   * 获取角色详情
   * @param {number|string} id 角色ID
   * @returns {Promise} 包含角色详情的Promise
   */
  getRole(id) {
    return api.get(`/permissions/roles/${id}`);
  },

  /**
   * 创建新角色
   * @param {Object} roleData 角色数据
   * @returns {Promise} 创建结果的Promise
   */
  createRole(roleData) {
    return api.post('/permissions/roles', roleData);
  },

  /**
   * 更新角色
   * @param {number|string} id 角色ID
   * @param {Object} roleData 角色数据
   * @returns {Promise} 更新结果的Promise
   */
  updateRole(id, roleData) {
    return api.put(`/permissions/roles/${id}`, roleData);
  },

  /**
   * 删除角色
   * @param {number|string} id 角色ID
   * @returns {Promise} 删除结果的Promise
   */
  deleteRole(id) {
    return api.delete(`/permissions/roles/${id}`);
  },

  /**
   * 获取所有权限
   * @returns {Promise} 包含权限列表的Promise
   */
  getPermissions() {
    return api.get('/permissions/');
  },

  /**
   * 获取权限详情
   * @param {number|string} id 权限ID
   * @returns {Promise} 包含权限详情的Promise
   */
  getPermission(id) {
    return api.get(`/permissions/${id}`);
  },

  /**
   * 创建新权限
   * @param {Object} permissionData 权限数据
   * @returns {Promise} 创建结果的Promise
   */
  createPermission(permissionData) {
    return api.post('/permissions/', permissionData);
  },

  /**
   * 更新权限
   * @param {number|string} id 权限ID
   * @param {Object} permissionData 权限数据
   * @returns {Promise} 更新结果的Promise
   */
  updatePermission(id, permissionData) {
    return api.put(`/permissions/${id}`, permissionData);
  },

  /**
   * 删除权限
   * @param {number|string} id 权限ID
   * @returns {Promise} 删除结果的Promise
   */
  deletePermission(id) {
    return api.delete(`/permissions/${id}`);
  },

  /**
   * 获取用户权限
   * @returns {Promise} 包含当前用户权限的Promise
   */
  getUserPermissions() {
    return api.get('/user/permissions');
  }
};

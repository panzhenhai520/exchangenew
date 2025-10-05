import api from './index';

/**
 * 认证相关API服务
 */
export default {
  /**
   * 用户登录
   * @param {Object} credentials 登录凭证
   * @returns {Promise} 登录结果的Promise
   */
  async login(credentials) {
    try {
      // 登录获取token
      const loginResponse = await api.post('/auth/login', credentials);
      
      if (loginResponse.data.success) {
        // 保存token
        localStorage.setItem('token', loginResponse.data.token);
        
        // 获取用户信息
        const userResponse = await api.get('/auth/user');
        if (userResponse.data.success) {
          // 获取网点本币信息
          const currencyResponse = await api.get(`/currencies/${userResponse.data.user.branch_currency_id}`);
          if (currencyResponse.data.success) {
            const user = {
              ...userResponse.data.user,
              branch_currency: currencyResponse.data.currency
            };
            localStorage.setItem('user', JSON.stringify(user));
          }
        }
        
        return loginResponse;
      }
      
      throw new Error(loginResponse.data.message || '登录失败');
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  },

  /**
   * 用户登出
   * @returns {Promise} 登出结果的Promise
   */
  logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    localStorage.removeItem('branch_info');
  },

  /**
   * 获取当前用户信息
   * @returns {Promise} 包含用户信息的Promise
   */
  getCurrentUser() {
    return api.get('/auth/user');
  },

  /**
   * 修改密码
   * @param {Object} passwordData 密码数据
   * @returns {Promise} 修改结果的Promise
   */
  changePassword(passwordData) {
    return api.post('/auth/change_password', passwordData);
  },

  /**
   * 刷新令牌
   * @returns {Promise} 刷新结果的Promise
   */
  refreshToken() {
    return api.post('/auth/refresh');
  },

  /**
   * 验证令牌
   * @returns {Promise} 验证结果的Promise
   */
  verifyToken() {
    return api.post('/auth/verify');
  }
};

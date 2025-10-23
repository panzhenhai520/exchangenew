import { defineStore } from 'pinia';
import api from '@/services/api';
import { usePermissionStore } from './permission';

export const useUserStore = defineStore('user', {
  state: () => ({
    user: null,
    token: null,
    isAuthenticated: false,
    loading: false
  }),
  
  actions: {
    async login(credentials) {
      this.loading = true;
      try {
        const response = await api.post('auth/login', credentials);
        
        if (response.data.success) {
          const { token, user, permissions } = response.data;
          
          this.setUser(user);
          this.setToken(token);
          
          // Store permissions
          localStorage.setItem('permissions', JSON.stringify(permissions || []));
          
          // Update permission store
          const permissionStore = usePermissionStore();
          permissionStore.setPermissions(permissions || []);
          
          return { success: true };
        } else {
          return { 
            success: false, 
            message: response.data.message || 'Login failed' 
          };
        }
      } catch (error) {
        console.error('Login error:', error);
        return { 
          success: false, 
          message: error.response?.data?.message || 'Network error' 
        };
      } finally {
        this.loading = false;
      }
    },
    
    async logout() {
      try {
        // 调用后端API记录退出日志
        await api.post('auth/logout');
      } catch (error) {
        console.error('退出登录API调用失败:', error);
        // 即使API调用失败，也继续清除本地数据
      }
      
      // 清除本地数据
      this.user = null;
      this.token = null;
      this.isAuthenticated = false;
      
      // Clear local storage
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      localStorage.removeItem('permissions');
      
      // Clear permissions
      const permissionStore = usePermissionStore();
      permissionStore.clearPermissions();
      
      // Clear API authorization header
      delete api.defaults.headers.common['Authorization'];
    },
    
    setUser(user) {
      this.user = user;
      this.isAuthenticated = true;
      localStorage.setItem('user', JSON.stringify(user));
    },
    
    setToken(token) {
      this.token = token;
      localStorage.setItem('token', token);
      
      // Authorization头现在由API拦截器统一处理，不需要在这里设置
    },
    
    checkAuth() {
      const token = localStorage.getItem('token');
      const user = localStorage.getItem('user');
      const permissions = localStorage.getItem('permissions');
      
      if (token && user) {
        this.token = token;
        this.user = JSON.parse(user);
        this.isAuthenticated = true;
        
        // Restore permissions
        if (permissions) {
          const permissionStore = usePermissionStore();
          permissionStore.setPermissions(JSON.parse(permissions));
        }
      }
    }
  },
  
  getters: {
    currentUser: (state) => state.user,
    isLoggedIn: (state) => state.isAuthenticated
  }
});

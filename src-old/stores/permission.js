import { defineStore } from 'pinia';

export const usePermissionStore = defineStore('permission', {
  state: () => ({
    permissions: []
  }),
  
  actions: {
    setPermissions(permissions) {
      this.permissions = permissions;
    },
    
    clearPermissions() {
      this.permissions = [];
    }
  },
  
  getters: {
    hasPermission: (state) => (permission) => {
      return state.permissions.includes(permission);
    },
    
    hasAnyPermission: (state) => (permissions) => {
      return permissions.some(permission => state.permissions.includes(permission));
    }
  }
});

<template>
  <div class="container py-4">
    <div class="row mb-4">
      <div class="col">
        <div class="d-flex justify-content-between align-items-center mb-4">
          <h2 class="page-title-bold">
            <font-awesome-icon :icon="['fas', 'user-tag']" class="me-2" />
            {{ $t('system_maintenance.role_management.title') }}
          </h2>
        </div>
        <p class="text-center text-muted">
          {{ $t('system_maintenance.role_management.subtitle') }}
        </p>
      </div>
    </div>
    
    <!-- 角色列表 - 全宽度显示 -->
    <div class="row">
      <div class="col-12">
        <div class="card shadow-sm">
          <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
            <h5 class="mb-0">
              <i class="fas fa-user-tag me-2"></i>
              {{ $t('system_maintenance.role_management.role_list') }} ({{ $t('system_maintenance.role_management.total_roles', { count: roles.length }) }})
            </h5>
            <button class="btn btn-sm btn-light" @click="showAddRoleModal">
              <i class="fas fa-plus me-1"></i> {{ $t('system_maintenance.role_management.add_role') }}
            </button>
          </div>
          <div class="card-body">
            <div v-if="loading" class="text-center py-4">
              <i class="fas fa-spinner fa-spin me-2"></i>
              {{ $t('system_maintenance.table.loading') }}
            </div>
            <div v-else>
              <!-- 角色网格布局 -->
              <div class="row">
                <div v-for="role in roles" :key="role.id" class="col-md-6 col-lg-4 mb-4">
                  <div class="role-card">
                    <div class="card border-0 shadow-sm h-100">
                      <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-3">
                          <div class="flex-grow-1">
                            <h5 class="role-title mb-1">
                              <i class="fas fa-user-tag text-primary me-2"></i>
                              {{ getRoleDisplayName(role.name) }}
                              <span v-if="isSystemAdminRole(role.name)" class="badge bg-danger ms-2">
                                <i class="fas fa-shield-alt me-1"></i>{{ $t('system_maintenance.role_management.protected_role') }}
                              </span>
                            </h5>
                            <p class="card-text text-muted mb-2" style="font-size: 0.9rem;">
                              {{ getRoleDescription(role) }}
                            </p>
                          </div>
                        </div>
                        
                        <!-- 权限统计 -->
                        <div class="d-flex align-items-center text-muted mb-3">
                          <small>
                            <i class="fas fa-shield-alt me-1"></i>
                            {{ $t('system_maintenance.role_management.permission_count') }}: <span class="badge bg-secondary">{{ role.permissions ? role.permissions.length : 0 }}</span>
                          </small>
                        </div>
                        
                        <!-- 权限预览 -->
                        <div v-if="role.permissions && role.permissions.length > 0" class="mb-3">
                          <small class="text-muted d-block mb-2">{{ $t('system_maintenance.role_management.permission_preview') }}:</small>
                          <div class="permission-preview">
                            <span 
                              v-for="perm in role.permissions.slice(0, 6)" 
                              :key="perm.id" 
                              class="badge bg-light text-dark me-1 mb-1"
                              style="font-size: 0.7rem;"
                              :title="perm.description"
                            >
                              {{ perm.name || perm.permission_name }}
                            </span>
                            <span v-if="role.permissions.length > 6" class="badge bg-secondary mb-1" style="font-size: 0.7rem;">
                              +{{ role.permissions.length - 6 }}
                            </span>
                          </div>
                        </div>
                        
                        <!-- 操作按钮 -->
                        <div class="d-flex gap-2">
                          <button 
                            class="btn btn-sm btn-outline-primary flex-fill" 
                            @click="editRole(role)" 
                            :disabled="role.name === 'App'"
                            :title="role.name === 'App' ? 'App角色不允许编辑' : $t('system_maintenance.role_management.actions.edit')"
                          >
                            <i class="fas fa-edit me-1"></i> {{ $t('system_maintenance.role_management.actions.edit') }}
                          </button>
                          <button class="btn btn-sm btn-outline-info" @click="viewRolePermissions(role)" :title="$t('system_maintenance.role_management.actions.view')">
                            <i class="fas fa-eye me-1"></i> {{ $t('system_maintenance.role_management.actions.view') }}
                          </button>
                          <button 
                            v-if="!isSystemAdminRole(role.name) && role.name !== 'App'" 
                            class="btn btn-sm btn-outline-danger" 
                            @click="confirmDeleteRole(role)" 
                            :title="role.name === 'App' ? 'App角色不允许删除' : $t('system_maintenance.role_management.actions.delete')"
                          >
                            <i class="fas fa-trash"></i>
                          </button>
                          <span 
                            v-else 
                            class="btn btn-sm btn-outline-secondary disabled" 
                            :title="$t('system_maintenance.role_management.messages.protected_role_delete')"
                          >
                            <i class="fas fa-shield-alt"></i>
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- 空状态 -->
              <div v-if="roles.length === 0" class="text-center py-5 text-muted">
                <i class="fas fa-user-tag fa-3x mb-3"></i>
                <h5>{{ $t('system_maintenance.table.no_data') }}</h5>
                <p>{{ $t('system_maintenance.role_management.messages.create_success') }}</p>
                <button class="btn btn-primary" @click="showAddRoleModal">
                  <i class="fas fa-plus me-1"></i> {{ $t('system_maintenance.role_management.actions.create') }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加/编辑角色模态框 -->
    <div class="modal fade" id="roleModal" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ isEditing ? $t('system_maintenance.role_management.edit_role') : $t('system_maintenance.role_management.add_role') }}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <form>
              <div class="mb-3">
                <label for="role_name" class="form-label">{{ $t('system_maintenance.role_management.role_name') }} <span class="text-danger">*</span></label>
                <input 
                  type="text" 
                  class="form-control" 
                  id="role_name" 
                  v-model="currentRole.role_name"
                  :placeholder="$t('system_maintenance.role_management.form.role_name_required')"
                  :disabled="isEditing && currentRole.role_name === '系统管理员'"
                >
                <div v-if="isEditing && currentRole.role_name === '系统管理员'" class="form-text text-warning">
                  <i class="fas fa-shield-alt me-1"></i> {{ $t('system_maintenance.role_management.form.protected_role_name') }}
                </div>
              </div>
              <div class="mb-3">
                <label for="description" class="form-label">{{ $t('system_maintenance.role_management.description') }}</label>
                <textarea 
                  class="form-control" 
                  id="description" 
                  rows="3" 
                  v-model="currentRole.description"
                  :placeholder="$t('system_maintenance.role_management.form.role_name_required')"
                ></textarea>
              </div>
              <div class="mb-3">
                <label class="form-label">
                  {{ $t('system_maintenance.role_management.permissions') }}
                  <small class="text-muted">({{ $t('system_maintenance.role_management.form.selected_count', { count: currentRole.permission_ids.length }) }})</small>
                </label>
                
                <!-- 全选/全不选按钮 -->
                <div class="mb-2">
                  <button type="button" class="btn btn-sm btn-outline-primary me-2" @click="selectAllPermissions">
                    <i class="fas fa-check-square me-1"></i> {{ $t('system_maintenance.role_management.form.select_all') }}
                  </button>
                  <button type="button" class="btn btn-sm btn-outline-secondary" @click="clearAllPermissions">
                    <i class="fas fa-square me-1"></i> {{ $t('system_maintenance.role_management.form.clear_all') }}
                  </button>
                </div>
                
                <!-- 权限列表 - 紧凑式布局 -->
                <div class="permissions-container">
                  <div class="row g-2">
                    <div v-for="perm in permissions" :key="perm.id" class="col-md-4">
                      <div class="permission-item">
                        <input 
                          class="form-check-input" 
                          type="checkbox" 
                          :id="'modal_perm_' + perm.id" 
                          :value="perm.id"
                          v-model="currentRole.permission_ids"
                        >
                        <label class="permission-label" :for="'modal_perm_' + perm.id">
                          <div class="permission-content">
                            <i class="fas fa-key permission-icon"></i>
                            <div class="permission-text">
                              <div class="permission-name">{{ perm.description }}</div>
                              <div class="permission-desc">{{ perm.permission_name }}</div>
                            </div>
                          </div>
                        </label>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">{{ $t('system_maintenance.form.cancel') }}</button>
            <button type="button" class="btn btn-primary" @click="saveRole" :disabled="saving">
              <i class="fas fa-spinner fa-spin me-1" v-if="saving"></i>
              {{ isEditing ? $t('system_maintenance.role_management.messages.update_success') : $t('system_maintenance.role_management.messages.create_success') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 权限详情模态框 -->
    <div class="modal fade" id="permissionsModal" tabindex="-1">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ $t('system_maintenance.role_management.permissions') }}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body">
            <h6>{{ $t('system_maintenance.role_management.role_name') }}：{{ selectedRole?.name }}</h6>
            <p class="text-muted">{{ selectedRole?.description }}</p>
            <hr>
            <div class="row">
              <div v-for="permission in selectedRole?.permissions" :key="permission.id" class="col-md-6 mb-2">
                <div class="card">
                  <div class="card-body py-2">
                    <div class="d-flex align-items-center">
                      <i class="fas fa-key text-primary me-2"></i>
                      <div>
                        <h6 class="card-title mb-1">{{ permission.name || permission.permission_name }}</h6>
                        <p class="card-text small text-muted mb-0">{{ permission.description }}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import userService from '@/services/api/userService'
import * as bootstrap from 'bootstrap'
import { useI18n } from 'vue-i18n'

export default {
  name: 'RoleManagementView',
  setup() {
    const { t } = useI18n();
    return { t };
  },
  data() {
    return {
      roles: [],
      permissions: [],
      currentRole: {
        role_name: '',
        description: '',
        permission_ids: []
      },
      selectedRole: null,
      isEditing: false,
      saving: false,
      loading: false
    }
  },
  computed: {
    // 移除权限分类，不再需要
  },
  watch: {
    // 监听语言切换
    '$i18n.locale': {
      handler() {
        // 当语言切换时，重新加载权限数据
        this.loadPermissions()
      },
      immediate: false
    }
  },
  async mounted() {
    await this.loadData()
  },
  methods: {
    async loadData() {
      this.loading = true
      try {
        await Promise.all([
          this.loadRoles(),
          this.loadPermissions()
        ])
      } catch (error) {
        console.error('加载数据失败:', error)
        this.$toast?.error(this.t('system_maintenance.role_management.messages.load_data_failed'))
      } finally {
        this.loading = false
      }
    },
    async loadRoles() {
      try {
        const response = await userService.getRoles()
        if (response.data.success) {
          this.roles = response.data.roles
        }
      } catch (error) {
        console.error('加载角色失败:', error)
      }
    },
    async loadPermissions() {
      try {
        // 获取当前语言并转换为简化格式
        const currentLanguage = this.$i18n.locale
        const langCode = currentLanguage.split('-')[0] // 将 'en-US' 转换为 'en'
        console.log('Current language:', currentLanguage, 'Simplified:', langCode)
        const response = await userService.getPermissions(langCode)
        if (response.data.success) {
          this.permissions = response.data.permissions
          console.log('Loaded permissions:', this.permissions)
        }
      } catch (error) {
        console.error('加载权限失败:', error)
      }
    },
    showAddRoleModal() {
      this.isEditing = false
      this.currentRole = {
        role_name: '',
        description: '',
        permission_ids: []
      }
      const modal = new bootstrap.Modal(document.getElementById('roleModal'))
      modal.show()
    },
    editRole(role) {
      this.isEditing = true
      console.log('编辑角色数据:', role)
      console.log('角色权限数据:', role.permissions)
      
      // 安全地提取权限ID
      let permissionIds = []
      if (role.permissions && Array.isArray(role.permissions)) {
        permissionIds = role.permissions.map(p => {
          // 处理权限对象可能是字典或对象的情况
          if (typeof p === 'object') {
            return p.id || p.permission_id || p.Id
          }
          return p
        }).filter(id => id !== undefined && id !== null)
      }
      
      console.log('提取的权限IDs:', permissionIds)
      
      this.currentRole = {
        id: role.id,
        role_name: role.name,
        description: role.description,
        permission_ids: permissionIds
      }
      const modal = new bootstrap.Modal(document.getElementById('roleModal'))
      modal.show()
    },
    async saveRole() {
      // 基础验证
      if (!this.currentRole.role_name.trim()) {
        this.$toast?.error(this.t('system_maintenance.role_management.form.role_name_required'))
        return
      }

      // 检查角色名称长度
      if (this.currentRole.role_name.trim().length > 50) {
        this.$toast?.error(this.t('system_maintenance.role_management.form.role_name_max_length'))
        return
      }

      // 检查是否选择了权限
      if (!this.currentRole.permission_ids || this.currentRole.permission_ids.length === 0) {
        if (!confirm(this.t('system_maintenance.role_management.form.no_permissions_warning'))) {
          return
        }
      }

      this.saving = true
      console.log('开始保存角色:', JSON.stringify(this.currentRole, null, 2))
      
      try {
        let response
        if (this.isEditing) {
          console.log('更新角色:', this.currentRole.id)
          response = await userService.updateRole(this.currentRole.id, this.currentRole)
        } else {
          console.log('创建新角色')
          response = await userService.createRole(this.currentRole)
        }

        console.log('API响应:', response)

        if (response.data.success) {
          const message = this.isEditing ? this.t('system_maintenance.role_management.messages.update_success') : this.t('system_maintenance.role_management.messages.create_success')
          this.$toast?.success(message)
          console.log(message)
          
          // 重新加载角色列表
          await this.loadRoles()
          
          // 关闭模态框
          const modalElement = document.getElementById('roleModal')
          const modalInstance = bootstrap.Modal.getInstance(modalElement)
          if (modalInstance) {
            modalInstance.hide()
          }
        } else {
          const errorMsg = response.data.message || this.t('system_maintenance.role_management.messages.unknown_error')
          console.error('操作失败:', errorMsg)
          this.$toast?.error(errorMsg)
        }
      } catch (error) {
        console.error('保存角色失败:', error)
        
        // 提取更详细的错误信息
        let errorMessage = this.t('system_maintenance.role_management.messages.save_role_failed')
        
        if (error.response) {
          console.error('错误响应状态:', error.response.status)
          console.error('错误响应数据:', error.response.data)
          
          if (error.response.status === 400) {
            errorMessage = error.response.data.message || this.t('system_maintenance.role_management.messages.request_error')
          } else if (error.response.status === 401) {
            errorMessage = this.t('system_maintenance.role_management.messages.login_expired')
            // 可以在这里跳转到登录页面
          } else if (error.response.status === 403) {
            errorMessage = this.t('system_maintenance.role_management.messages.permission_denied')
          } else if (error.response.status === 500) {
            errorMessage = error.response.data.message || this.t('system_maintenance.role_management.messages.server_error')
          } else {
            errorMessage = error.response.data.message || `${this.t('system_maintenance.role_management.messages.unknown_error')} (HTTP ${error.response.status})`
          }
        } else if (error.request) {
          console.error('网络请求失败:', error.request)
          errorMessage = this.t('system_maintenance.role_management.messages.network_error')
        } else {
          console.error('其他错误:', error.message)
          errorMessage = error.message || this.t('system_maintenance.role_management.messages.unknown_error')
        }
        
        this.$toast?.error(errorMessage)
      } finally {
        this.saving = false
        console.log('角色保存操作完成')
      }
    },
    viewRolePermissions(role) {
      this.selectedRole = role
      const modal = new bootstrap.Modal(document.getElementById('permissionsModal'))
      modal.show()
    },
    async confirmDeleteRole(role) {
      // 防止删除系统管理员角色
      if (role.name === '系统管理员') {
        this.$toast?.error(this.t('system_maintenance.role_management.messages.protected_role_delete'))
        return
      }
      
      if (confirm(this.t('system_maintenance.role_management.messages.confirm_delete', { name: role.name }))) {
        try {
          const response = await userService.deleteRole(role.id)
          if (response.data.success) {
            this.$toast?.success(this.t('system_maintenance.role_management.messages.delete_success'))
            await this.loadRoles()
          } else {
            this.$toast?.error(response.data.message || this.t('system_maintenance.role_management.messages.delete_failed'))
          }
        } catch (error) {
          console.error('删除角色失败:', error)
          this.$toast?.error(this.t('system_maintenance.role_management.messages.delete_role_failed'))
        }
      }
    },
    formatDate(dateStr) {
      if (!dateStr) return '-'
      return new Date(dateStr).toLocaleString('zh-CN')
    },
    getRoleDisplayName(roleName) {
      if (!roleName) {
        return this.$t('system_maintenance.user_management.role_names.unassigned') || '未分配';
      }
      
      // 系统管理员角色根据当前语言进行翻译
      if (roleName === '系统管理员') {
        return this.$t('system_maintenance.role_management.system_admin')
      }
      // 分行管理员角色根据当前语言进行翻译
      if (roleName === '分行管理员') {
        return this.$t('system_maintenance.role_management.branch_admin')
      }
      // 窗口操作员角色根据当前语言进行翻译
      if (roleName === '窗口操作员') {
        return this.$t('system_maintenance.role_management.window_operator')
      }
      // 其他角色保持原名称
      return roleName
    },
    isSystemAdminRole(roleName) {
      return roleName === '系统管理员';
    },
    getRoleDescription(role) {
      // 系统管理员角色描述根据当前语言进行翻译
      if (this.isSystemAdminRole(role.name) || role.description === 'SYSTEM_ADMIN_DESCRIPTION') {
        return this.$t('system_maintenance.role_management.system_admin_description')
      }
      // 分行管理员角色描述根据当前语言进行翻译
      if (role.name === '分行管理员' || role.description === 'BRANCH_ADMIN_DESCRIPTION') {
        return this.$t('system_maintenance.role_management.branch_admin_description')
      }
      // 其他角色保持原描述
      return role.description || this.$t('system_maintenance.role_management.no_description')
    },
    selectAllPermissions() {
      this.currentRole.permission_ids = this.permissions.map(p => p.id)
    },
    clearAllPermissions() {
      this.currentRole.permission_ids = []
    }
  }
}
</script> 

<style scoped>
.role-card .card {
  transition: all 0.2s;
  height: 100%;
}

.role-card .card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(0,0,0,0.15);
}

.permission-preview .badge {
  margin-bottom: 0.25rem;
}

.card {
  border: none;
  border-radius: 10px;
}

.table th {
  border-top: none;
  font-weight: 600;
}

.badge {
  font-size: 0.75em;
}

.btn-group-sm > .btn, .btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
}

/* 权限选择框样式优化 */
.form-check.p-3.border.rounded {
  transition: all 0.2s;
  cursor: pointer;
}

.form-check.p-3.border.rounded:hover {
  background-color: #f8f9fa;
  border-color: #007bff !important;
}

.form-check.p-3.border.rounded:has(.form-check-input:checked) {
  background-color: #e3f2fd;
  border-color: #007bff !important;
}

.form-check-label {
  cursor: pointer;
}

/* 权限选择区域紧凑布局 */
.permissions-container {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #dee2e6;
  border-radius: 0.375rem;
  padding: 0.75rem;
  background-color: #f8f9fa;
}

.permission-item {
  display: flex;
  align-items: center;
  padding: 0.5rem;
  border: 1px solid #e9ecef;
  border-radius: 0.25rem;
  background-color: white;
  transition: all 0.15s ease-in-out;
  cursor: pointer;
  min-height: 50px;
}

.permission-item:hover {
  border-color: #007bff;
  box-shadow: 0 1px 3px rgba(0,123,255,0.1);
}

.permission-item:has(.form-check-input:checked) {
  background-color: #e3f2fd;
  border-color: #007bff;
}

.permission-item .form-check-input {
  margin: 0;
  margin-right: 0.5rem;
  flex-shrink: 0;
}

.permission-label {
  flex: 1;
  margin: 0;
  cursor: pointer;
  display: flex;
  align-items: center;
}

.permission-content {
  display: flex;
  align-items: center;
  width: 100%;
}

.permission-icon {
  color: #007bff;
  margin-right: 0.5rem;
  flex-shrink: 0;
  font-size: 0.875rem;
}

.permission-text {
  flex: 1;
  min-width: 0;
}

.permission-name {
  font-weight: 500;
  font-size: 0.8rem;
  line-height: 1.2;
  margin-bottom: 0.125rem;
  color: #212529;
}

.permission-desc {
  font-size: 0.7rem;
  color: #6c757d;
  line-height: 1.1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 滚动条样式 */
.permissions-container::-webkit-scrollbar {
  width: 6px;
}

.permissions-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.permissions-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.permissions-container::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 角色卡片网格布局 */
.role-card {
  height: 100%;
}

.role-card .card-body {
  display: flex;
  flex-direction: column;
}

.role-card .d-flex.gap-2 {
  margin-top: auto;
}

/* 角色标题样式 */
.role-title {
  font-size: 1.25rem !important;
  font-weight: 600 !important;
  color: #212529 !important;
  line-height: 1.3;
}

.role-title .fas.fa-user-tag {
  font-size: 1.1rem;
}

.role-title .badge {
  font-size: 0.7rem;
  vertical-align: middle;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .col-lg-4 {
    margin-bottom: 1rem;
  }
  
  /* 小屏幕下权限项调整为两列 */
  .permissions-container .col-md-4 {
    flex: 0 0 50%;
    max-width: 50%;
  }
  
  .permission-name {
    font-size: 0.75rem;
  }
  
  .permission-desc {
    font-size: 0.65rem;
  }
  
  /* 小屏幕下角色标题调整 */
  .role-title {
    font-size: 1.1rem !important;
  }
  
  .role-title .fas.fa-user-tag {
    font-size: 1rem;
  }
}

@media (max-width: 576px) {
  /* 超小屏幕下权限项调整为单列 */
  .permissions-container .col-md-4 {
    flex: 0 0 100%;
    max-width: 100%;
  }
  
  /* 超小屏幕下角色标题进一步调整 */
  .role-title {
    font-size: 1rem !important;
  }
}
</style> 
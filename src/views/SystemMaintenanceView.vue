<template>
  <div class="container py-4">
    <div class="row">
      <div class="col-12">
        <div class="d-flex justify-content-between align-items-center mb-4">
          <h2 class="page-title-bold">
            <font-awesome-icon :icon="['fas', 'cogs']" class="me-2" />
            {{ $t('system_maintenance.title') }}
          </h2>
        </div>
        
        <!-- 网点列表 -->
        <div class="card">
      <div class="card-header d-flex justify-content-between align-items-center">
        <h5 class="mb-0">
          {{ isDevMode ? $t('system_maintenance.branch_management.branch_list') : $t('system_maintenance.branch_management.branch_info') }}
          <span v-if="!isDevMode" class="badge bg-info ms-2">{{ $t('system_maintenance.branch_management.current_branch') }}</span>
        </h5>
        <button 
          v-if="isDevMode" 
          class="btn btn-primary" 
          @click="showAddBranchModal" 
          :disabled="!!error"
        >
          <font-awesome-icon :icon="['fas', 'plus']" class="me-1" />
          {{ $t('system_maintenance.branch_management.add_branch') }}
        </button>
      </div>
      <div class="card-body">
        <div v-if="error" class="alert alert-danger mb-3">
          {{ error }}
        </div>
        <div class="table-responsive">
          <table class="table table-striped table-hover">
            <thead>
              <tr>
                <th width="60">{{ $t('system_maintenance.table.serial_number') }}</th>
                <th>{{ $t('system_maintenance.branch_management.branch_code') }}</th>
                <th>{{ $t('system_maintenance.branch_management.branch_name') }}</th>
                <th>{{ $t('system_maintenance.branch_management.address') }}</th>
                <th>{{ $t('system_maintenance.branch_management.manager_name') }}</th>
                <th>{{ $t('system_maintenance.branch_management.phone_number') }}</th>
                <th>{{ $t('system_maintenance.branch_management.base_currency') }}</th>
                <th>{{ $t('system_maintenance.branch_management.is_active') }}</th>
                <th width="120">{{ $t('system_maintenance.table.actions') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="loading">
                <td colspan="9" class="text-center py-3">
                  <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">{{ $t('system_maintenance.table.loading') }}</span>
                  </div>
                </td>
              </tr>
              <tr v-else-if="error">
                <td colspan="9" class="text-center py-3">
                  <span class="text-muted">{{ $t('system_maintenance.table.cannot_load') }}</span>
                </td>
              </tr>
              <tr v-else-if="filteredBranches.length === 0">
                <td colspan="9" class="text-center py-3">
                  {{ isDevMode ? $t('system_maintenance.table.no_data') : $t('system_maintenance.table.cannot_get_branch') }}
                </td>
              </tr>
              <tr v-for="(branch, index) in filteredBranches" :key="branch.id">
                <td class="text-center">{{ index + 1 }}</td>
                <td>
                  <span class="badge bg-light text-dark">{{ branch.branch_code }}</span>
                </td>
                <td>{{ branch.branch_name }}</td>
                <td>{{ branch.address || '-' }}</td>
                <td>{{ branch.manager_name || '-' }}</td>
                <td>{{ branch.phone_number || '-' }}</td>
                <td>
                  <span class="badge bg-info">{{ branch.base_currency }}</span>
                </td>
                <td>
                  <span class="badge" :class="branch.is_active ? 'bg-success' : 'bg-danger'">
                    {{ branch.is_active ? $t('system_maintenance.branch_management.status.active') : $t('system_maintenance.branch_management.status.inactive') }}
                  </span>
                </td>
                <td>
                  <button class="btn btn-sm btn-primary me-2" @click="editBranch(branch)">
                    <font-awesome-icon :icon="['fas', 'edit']" />
                  </button>
                  <button 
                    v-if="isDevMode"
                    class="btn btn-sm btn-danger" 
                    @click="deleteBranch(branch)"
                    :disabled="branch.has_business_data"
                    :title="branch.has_business_data ? $t('system_maintenance.table.has_business_data') : $t('system_maintenance.table.delete_branch')"
                  >
                    <font-awesome-icon :icon="['fas', 'trash']" />
                  </button>
                  <span v-else class="text-muted small">{{ $t('system_maintenance.table.edit_only') }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
      </div>
    </div>

    <!-- 新增/编辑网点弹窗 -->
    <div class="modal fade" id="branchModal" tabindex="-1">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ editingBranch ? $t('system_maintenance.branch_management.edit_branch') : $t('system_maintenance.branch_management.add_branch') }}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="saveBranch">
              <div class="mb-3">
                <label class="form-label">{{ $t('system_maintenance.branch_management.branch_code') }} <span class="text-danger">*</span></label>
                <div class="input-group">
                  <input 
                    type="text" 
                    class="form-control" 
                    v-model="branchForm.branch_code" 
                    :disabled="editingBranch"
                    required
                  />
                  <button 
                    v-if="!editingBranch" 
                    class="btn btn-outline-secondary" 
                    type="button"
                    @click="showBranchCodeHelp"
                  >
                    <font-awesome-icon :icon="['fas', 'question-circle']" />
                  </button>
                </div>
                <small class="text-muted" v-if="!editingBranch">
                  {{ $t('system_maintenance.branch_code_help.code_format') }}
                </small>
              </div>
              <div class="mb-3">
                <label class="form-label">{{ $t('system_maintenance.branch_management.branch_name') }} <span class="text-danger">*</span></label>
                <input 
                  type="text" 
                  class="form-control" 
                  v-model="branchForm.branch_name" 
                  required
                />
              </div>
              <div class="mb-3">
                <label class="form-label">{{ $t('system_maintenance.branch_management.address') }}</label>
                <input 
                  type="text" 
                  class="form-control" 
                  v-model="branchForm.address"
                />
              </div>
              <div class="mb-3">
                <label class="form-label">{{ $t('system_maintenance.branch_management.manager_name') }}</label>
                <input 
                  type="text" 
                  class="form-control" 
                  v-model="branchForm.manager_name"
                />
              </div>
              <div class="mb-3">
                <label class="form-label">{{ $t('system_maintenance.branch_management.phone_number') }}</label>
                <input 
                  type="tel" 
                  class="form-control" 
                  v-model="branchForm.phone_number"
                />
              </div>
              <div class="mb-3">
                <label class="form-label">{{ $t('system_maintenance.branch_management.base_currency') }} <span class="text-danger">*</span></label>
                <select class="form-select currency-select" v-model="branchForm.base_currency_id" required>
                  <option value="">{{ $t('system_maintenance.form.select_currency') }}</option>
                  <option v-for="currency in currencies" :key="currency.id" :value="currency.id">
                    {{ currency.currency_code }} - {{ currency.currency_name }}
                  </option>
                </select>
              </div>
              <div class="mb-3">
                <label class="form-label">{{ $t('system_maintenance.branch_management.company_full_name') }}</label>
                <input
                  type="text"
                  class="form-control"
                  v-model="branchForm.company_full_name"
                  :placeholder="$t('system_maintenance.branch_management.company_full_name_placeholder')"
                />
                <small class="text-muted">{{ $t('system_maintenance.branch_management.company_full_name_help') }}</small>
              </div>
              <div class="mb-3">
                <label class="form-label">{{ $t('system_maintenance.branch_management.tax_registration_number') }}</label>
                <input
                  type="text"
                  class="form-control"
                  v-model="branchForm.tax_registration_number"
                  :placeholder="$t('system_maintenance.branch_management.tax_registration_number_placeholder')"
                />
                <small class="text-muted">{{ $t('system_maintenance.branch_management.tax_registration_number_help') }}</small>
              </div>
              <div class="mb-3" v-if="editingBranch">
                <div class="form-check">
                  <input 
                    type="checkbox" 
                    class="form-check-input" 
                    id="is_active" 
                    v-model="branchForm.is_active"
                  />
                  <label class="form-check-label" for="is_active">{{ $t('system_maintenance.form.enable_status') }}</label>
                </div>
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">{{ $t('system_maintenance.form.cancel') }}</button>
            <button type="button" class="btn btn-primary" @click="saveBranch" :disabled="saving">
              {{ saving ? $t('system_maintenance.form.saving') : $t('system_maintenance.form.save') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 网点代码帮助弹窗 -->
    <div class="modal fade" id="branchCodeHelpModal" tabindex="-1">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ $t('system_maintenance.branch_code_help.title') }}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body">
            <h6>{{ $t('system_maintenance.branch_code_help.existing_codes') }}</h6>
            <div class="table-responsive">
              <table class="table table-sm">
                <thead>
                  <tr>
                    <th>{{ $t('system_maintenance.branch_management.branch_code') }}</th>
                    <th>{{ $t('system_maintenance.branch_management.branch_name') }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="branch in branches" :key="branch.id">
                    <td><code>{{ branch.branch_code }}</code></td>
                    <td>{{ branch.branch_name }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <hr>
            <h6>{{ $t('system_maintenance.branch_code_help.code_rules') }}</h6>
            <ul class="mb-0">
              <li>{{ $t('system_maintenance.branch_code_help.head_office') }}</li>
              <li>{{ $t('system_maintenance.branch_code_help.branch_office') }}
                <ul>
                  <li>{{ $t('system_maintenance.branch_code_help.examples.beijing') }}</li>
                  <li>{{ $t('system_maintenance.branch_code_help.examples.shanghai') }}</li>
                  <li>{{ $t('system_maintenance.branch_code_help.examples.guangzhou') }}</li>
                </ul>
              </li>
              <li>{{ $t('system_maintenance.branch_code_help.sub_branch') }}
                <ul>
                  <li>{{ $t('system_maintenance.branch_code_help.examples.beijing_sub1') }}</li>
                  <li>{{ $t('system_maintenance.branch_code_help.examples.beijing_sub2') }}</li>
                </ul>
              </li>
            </ul>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-primary" data-bs-dismiss="modal">{{ $t('system_maintenance.form.understand') }}</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 提示消息 -->
    <div class="toast-container position-fixed bottom-0 end-0 p-3">
      <div class="toast" :class="{ show: toast.show }" role="alert">
        <div class="toast-header" :class="getToastHeaderClass">
          <strong class="me-auto">{{ getToastTitle }}</strong>
          <button type="button" class="btn-close" @click="hideToast"></button>
        </div>
        <div class="toast-body">
          {{ toast.message }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import { Modal } from 'bootstrap';
import currencyService from '@/services/api/currencyService';
import branchService from '@/services/api/branchService';
import { showSafeError, getSafeErrorMessage } from '@/utils/errorHandler';
import { useI18n } from 'vue-i18n';

export default {
  name: 'SystemMaintenanceView',
  setup() {
    const { t } = useI18n();
    const route = useRoute();
    const branches = ref([]);
    const currencies = ref([]);
    const editingBranch = ref(null);
    const saving = ref(false);
    const branchModal = ref(null);
    const loading = ref(false);
    const branchCodeHelpModal = ref(null);
    const error = ref(null);
    const toast = reactive({
      show: false,
      type: 'success',
      message: ''
    });

    // 检测是否为开发模式
    const isDevMode = computed(() => {
      return route.query.dev === 'true';
    });

    // 获取当前用户的网点ID
    const getCurrentUserBranchId = () => {
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      return user.branch_id;
    };

    // 过滤网点列表
    const filteredBranches = computed(() => {
      if (isDevMode.value) {
        // 开发模式：显示所有网点
        console.log('开发模式：显示所有网点', branches.value.length, '个');
        return branches.value;
      } else {
        // 普通模式：只显示当前用户的网点
        const currentBranchId = getCurrentUserBranchId();
        const filtered = branches.value.filter(branch => branch.id === currentBranchId);
        console.log('普通模式：当前用户网点ID =', currentBranchId, '，过滤后网点数量 =', filtered.length);
        return filtered;
      }
    });

    const branchForm = ref({
      branch_code: '',
      branch_name: '',
      address: '',
      manager_name: '',
      phone_number: '',
      base_currency_id: '',
      company_full_name: '',
      tax_registration_number: '',
      is_active: true
    });

    const getToastHeaderClass = computed(() => {
      return {
        'bg-success text-white': toast.type === 'success',
        'bg-danger text-white': toast.type === 'error',
        'bg-warning': toast.type === 'warning'
      };
    });

    const getToastTitle = computed(() => {
      switch (toast.type) {
        case 'success':
          return t('common.success_title');
        case 'error':
          return t('common.error_title');
        case 'warning':
          return t('common.warning_title');
        default:
          return t('common.info_title');
      }
    });

    const showToast = (message, type = 'success') => {
      toast.message = message;
      toast.type = type;
      toast.show = true;
      setTimeout(() => {
        toast.show = false;
      }, 3000);
    };

    const hideToast = () => {
      toast.show = false;
    };

    const checkPermissions = () => {
      // 检查权限
      const userPermissions = JSON.parse(localStorage.getItem('userPermissions') || '[]');
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      
      console.log('检查网点管理权限:', {
        userPermissions,
        userRole: user.role_name,
        hasBranchManage: userPermissions.includes('branch_manage'),
        hasSystemManage: userPermissions.includes('system_manage'),
        isDevMode: isDevMode.value,
        userBranchId: user.branch_id
      });
      
      if (isDevMode.value) {
        // 开发模式：需要完整的网点管理权限
        if (!userPermissions.includes('branch_manage') && !userPermissions.includes('system_manage')) {
          error.value = t('system_maintenance.permissions.no_branch_manage');
          return false;
        }
      } else {
        // 普通模式：只需要基本的登录权限，因为只能编辑自己的网点
        if (!user.branch_id) {
          error.value = t('system_maintenance.permissions.no_branch_info');
          return false;
        }
      }
      return true;
    };

    const fetchBranches = async () => {
      loading.value = true;
      error.value = null;
      try {
        console.log('开始获取网点列表...');
        const response = await branchService.getBranches();
        console.log('获取网点列表响应:', response);
        
        if (response.data.success) {
          branches.value = response.data.branches;
          console.log('成功获取网点列表:', branches.value);
        } else {
          console.error('获取网点列表失败:', response.data.message);
          const safeMessage = getSafeErrorMessage({ response }, t('system_maintenance.messages.fetch_branches_failed'));
          error.value = safeMessage;
          showToast(safeMessage, 'error');
        }
      } catch (error) {
        console.error('获取网点列表出错:', error);
        showSafeError(error, showToast, '获取网点列表');
        error.value = getSafeErrorMessage(error, '获取网点列表失败');
      } finally {
        loading.value = false;
      }
    };

    const fetchCurrencies = async () => {
      try {
        const response = await currencyService.getCurrencies();
        if (response.data.success) {
          currencies.value = response.data.currencies;
        } else {
          const safeMessage = getSafeErrorMessage({ response }, t('system_maintenance.messages.fetch_currencies_failed'));
          showToast(safeMessage, 'error');
        }
      } catch (err) {
        console.error('Failed to fetch currencies:', err);
        showSafeError(err, showToast, t('system_maintenance.messages.fetch_currencies_failed'));
      }
    };

    const showAddBranchModal = () => {
      editingBranch.value = null;
      branchForm.value = {
        branch_code: '',
        branch_name: '',
        address: '',
        manager_name: '',
        phone_number: '',
        base_currency_id: '',
        is_active: true
      };
      if (!branchModal.value) {
        branchModal.value = new Modal(document.getElementById('branchModal'));
      }
      branchModal.value.show();
    };

    const showBranchCodeHelp = () => {
      if (!branchCodeHelpModal.value) {
        branchCodeHelpModal.value = new Modal(document.getElementById('branchCodeHelpModal'));
      }
      branchCodeHelpModal.value.show();
    };

    const editBranch = (branch) => {
      editingBranch.value = branch;
      branchForm.value = {
        branch_code: branch.branch_code,
        branch_name: branch.branch_name,
        address: branch.address || '',
        manager_name: branch.manager_name || '',
        phone_number: branch.phone_number || '',
        base_currency_id: branch.base_currency_id,
        is_active: branch.is_active
      };
      if (!branchModal.value) {
        branchModal.value = new Modal(document.getElementById('branchModal'));
      }
      branchModal.value.show();
    };

    const saveBranch = async () => {
      saving.value = true;
      try {
        console.log('保存网点信息 - 表单数据:', branchForm.value);
        
        let response;
        if (editingBranch.value) {
          console.log('更新网点 - ID:', editingBranch.value.id);
          response = await branchService.updateBranch(editingBranch.value.id, branchForm.value);
        } else {
          console.log('创建新网点');
          response = await branchService.createBranch(branchForm.value);
        }

        if (response.data.success) {
          console.log('网点保存成功 - 响应数据:', response.data);
          showToast(editingBranch.value ? t('system_maintenance.messages.branch_update_success') : t('system_maintenance.messages.branch_add_success'));
          branchModal.value.hide();
          await fetchBranches();
        } else {
          const safeMessage = getSafeErrorMessage({ response }, t('system_maintenance.messages.save_failed'));
          throw new Error(safeMessage);
        }
      } catch (error) {
        console.error('保存网点信息出错:', error);
        showSafeError(error, showToast, t('system_maintenance.messages.save_failed'));
      } finally {
        saving.value = false;
      }
    };

    const deleteBranch = async (branch) => {
      // 首先检查网点是否有业务数据
      try {
        const checkResponse = await branchService.checkBranchCanDelete(branch.id);
        if (!checkResponse.data.success) {
                  const safeMessage = getSafeErrorMessage({ response: checkResponse }, t('system_maintenance.messages.check_branch_data_failed'));
        showToast(safeMessage, 'error');
          return;
        }
        
        if (!checkResponse.data.can_delete) {
          const reasons = checkResponse.data.reasons || [];
          let message = t('system_maintenance.messages.cannot_delete_branch') + '\n';
          reasons.forEach(reason => {
            message += `• ${reason}\n`;
          });
          alert(message);
          return;
        }
      } catch (error) {
        console.error('检查网点数据出错:', error);
        // 如果检查API不存在，继续执行删除，但给出警告
        if (error.response?.status !== 404) {
          showSafeError(error, showToast, t('system_maintenance.messages.check_branch_data_failed'));
          return;
        }
      }

      // 确认删除
      const confirmMessage = t('system_maintenance.messages.confirm_delete', { name: branch.branch_name });
      if (!confirm(confirmMessage)) {
        return;
      }

      try {
        const response = await branchService.deleteBranch(branch.id);
        if (response.data.success) {
          showToast(t('system_maintenance.messages.branch_delete_success'));
          await fetchBranches();
        } else {
          const safeMessage = getSafeErrorMessage({ response }, t('system_maintenance.messages.delete_failed'));
          throw new Error(safeMessage);
        }
      } catch (error) {
        console.error('删除网点出错:', error);
        showSafeError(error, showToast, t('system_maintenance.messages.delete_failed'));
      }
    };

    onMounted(() => {
      // 先检查权限，再加载数据
      if (checkPermissions()) {
        fetchBranches();
        fetchCurrencies();
      }
    });

    return {
      branches,
      currencies,
      editingBranch,
      saving,
      branchForm,
      toast,
      error,
      loading,
      isDevMode,
      filteredBranches,
      getToastHeaderClass,
      getToastTitle,
      showToast,
      hideToast,
      showAddBranchModal,
      editBranch,
      saveBranch,
      deleteBranch,
      showBranchCodeHelp
    };
  }
};
</script>

<style scoped>
.toast {
  opacity: 0;
  transition: opacity 0.3s ease;
}

.toast.show {
  opacity: 1;
}

.currency-select {
  max-height: 200px;
  overflow-y: auto;
}

/* 自定义滚动条样式 */
.currency-select::-webkit-scrollbar {
  width: 8px;
}

.currency-select::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.currency-select::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.currency-select::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.table th {
  white-space: nowrap;
}
</style> 
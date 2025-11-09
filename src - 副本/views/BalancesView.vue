<template>
  <div class="container-fluid py-4">
    <div class="row">
      <div class="col-12">
        <div class="d-flex justify-content-between align-items-center mb-4">
          <h2 class="page-title-bold">
            <font-awesome-icon :icon="['fas', 'coins']" class="me-2" />
            {{ $t('balance.query_title') }}
          </h2>
        </div>
        
        <div class="card mb-4">
          <div class="card-header">
            <h5 class="mb-0">{{ $t('balance.query_conditions') }}</h5>
          </div>
          <div class="card-body">
            <form @submit.prevent="handleSearch">
              <div class="row g-3 align-items-end">
                <div class="col-md-3">
                  <div class="mb-3">
                    <label for="branch" class="form-label">{{ $t('balance.branch') }}</label>
                    <select
                      id="branch"
                      class="form-select"
                      v-model="searchForm.branchId"
                      :disabled="!isAdmin"
                    >
                      <option v-if="isAdmin" value="">{{ $t('balance.all_branches') }}</option>
                      <option v-for="b in branches" :key="b.id" :value="b.id">
                        {{ b.branch_code }} - {{ b.branch_name }}
                      </option>
                    </select>
                  </div>
                </div>
                <div class="col-md-3">
                  <div class="mb-3">
                    <label for="currency" class="form-label">{{ $t('balance.currency') }}</label>
                    <currency-select
                      id="currency"
                      v-model="selectedCurrencyCode"
                      api-endpoint="/balance-management/currency-templates"
                      @change="onCurrencyChange"
                    />
                  </div>
                </div>
                
                <!-- 查询按钮组 -->
                <div class="col-md-6">
                  <div class="d-flex gap-2">
                    <button type="submit" class="btn btn-primary" :disabled="loading">
                      <font-awesome-icon :icon="['fas', 'search']" class="me-2" />
                      {{ $t('balance.search') }}
                    </button>
                    <button type="button" class="btn btn-secondary" @click="resetSearch" :disabled="loading">
                      <font-awesome-icon :icon="['fas', 'undo']" class="me-2" />
                      {{ $t('balance.reset') }}
                    </button>
                    <button type="button" class="btn btn-outline-primary" @click="refreshData" :disabled="loading">
                      <font-awesome-icon :icon="['fas', 'sync']" class="me-2" :spin="loading" />
                      {{ $t('balance.refresh') }}
                    </button>
                    <button 
                      type="button" 
                      class="btn btn-outline-secondary" 
                      @click="exportData"
                      v-if="balances.length > 0"
                      :disabled="loading"
                    >
                      <font-awesome-icon :icon="['fas', 'file-export']" class="me-2" />
                      {{ $t('balance.export') }}
                    </button>
                  </div>
                </div>
              </div>
            </form>
          </div>
        </div>
        
        <div class="card">
          <div class="card-header d-flex justify-content-between align-items-center">
            <h5 class="mb-0">{{ $t('balance.balance_list') }}</h5>
            <div class="text-muted">
              {{ $t('balance.total_records', { count: balances.length }) }}
            </div>
          </div>
          <div class="card-body">
            <!-- 错误提示 -->
            <div v-if="error" class="alert alert-danger" role="alert">
              <font-awesome-icon :icon="['fas', 'exclamation-triangle']" class="me-2" />
              {{ error }}
            </div>
            
            <!-- 加载状态 -->
            <div v-if="loading" class="text-center py-4">
              <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">{{ $t('balance.loading') }}</span>
              </div>
              <p class="mt-2">{{ $t('balance.loading_data') }}</p>
            </div>
            
            <div v-else>
              <div class="table-responsive">
                <table class="table table-striped table-hover table-bordered">
                  <thead class="table-light">
                    <tr>
                      <th>{{ $t('balance.headers.branch') }}</th>
                      <th>{{ $t('balance.headers.currency') }}</th>
                      <th class="text-end balance-column">{{ $t('balance.headers.balance') }}</th>
                      <th class="text-center time-column">{{ $t('balance.headers.last_update_time') }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-if="balances.length === 0">
                      <td colspan="4" class="text-center py-4">{{ $t('balance.no_data') }}</td>
                    </tr>
                    <tr v-for="bal in balances" :key="bal.id">
                      <td>{{ bal.branchName }}</td>
                      <td>
                        <div class="d-flex align-items-center">
                          <CurrencyFlag :code="bal.currencyCode" :custom-filename="bal.custom_flag_filename" class="me-1" />
                          {{ getCurrencyDisplayName(bal) }} ({{ bal.currencyCode }})
                          <span v-if="isBaseCurrency(bal)" class="badge bg-primary ms-1 base-currency-badge">本币</span>
                        </div>
                      </td>
                      <td class="text-end balance-column">{{ formatAmount(bal.balance) }}</td>
                      <td class="text-center time-column">{{ formatDateTime(bal.updatedAt) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed, getCurrentInstance } from 'vue';
import { useI18n } from 'vue-i18n';
import { formatDateTime, formatAmount } from '@/utils/formatters';
import CurrencyFlag from '@/components/CurrencyFlag.vue';
import CurrencySelect from '@/components/CurrencySelect.vue';
import { getCurrencyDisplayName as getCurrencyDisplayNameFromUtils } from '@/utils/currencyTranslator';

export default {
  name: 'BalancesView',
  components: {
    CurrencyFlag,
    CurrencySelect
  },
  
  setup() {
    const { proxy: app } = getCurrentInstance();
    const { t } = useI18n();
    
    const searchForm = ref({
      branchId: '',
      currencyId: ''
    });
    
    const loading = ref(false);
    const error = ref(null);
    const balances = ref([]);
    const branches = ref([]);
    const selectedCurrencyCode = ref('');
    const today = new Date().toISOString().split('T')[0];

    // 从localStorage获取当前用户信息
    const userInfo = JSON.parse(localStorage.getItem('user') || '{}');
    const userPermissions = JSON.parse(localStorage.getItem('userPermissions') || '[]');
    
    // 判断是否有管理员权限或全部网点查询权限
    const isAdmin = computed(() => {
      // 检查角色名称
      const isAdminRole = ['admin', 'administrator', 'Admin', 'Administrator', '系统管理员'].includes(userInfo.role_name) || 
                         (userInfo.role_name === '系统管理员');
      // 检查是否有相关权限
      const hasBranchManage = userPermissions.includes('branch_manage');
      const hasSystemManage = userPermissions.includes('system_manage');
      
      return isAdminRole || hasBranchManage || hasSystemManage;
    });

    // 初始化表单，默认选中当前用户的网点
    searchForm.value.branchId = userInfo.branch_id;

    // 获取网点列表
    const fetchBranches = async () => {
      try {
        loading.value = true;
        const response = await app.$api.get('/auth/branches');
        if (response.data.success) {
          // 如果是管理员，显示所有网点；否则只显示当前用户的网点
          if (isAdmin.value) {
            branches.value = response.data.branches;
          } else {
            // 非管理员只显示自己的网点
            const currentBranch = response.data.branches.find(b => b.id == userInfo.branch_id);
            branches.value = currentBranch ? [currentBranch] : [];
          }
          
          // 默认选中当前用户的网点
          searchForm.value.branchId = userInfo.branch_id;
          
          // 获取完网点后立即查询余额
          handleSearch();
        } else {
          throw new Error(response.data.message || t('balance.get_branches_failed'));
        }
      } catch (err) {
        error.value = t('balance.get_branches_failed');
        console.error('获取网点列表失败:', err);
      } finally {
        loading.value = false;
      }
    };





    // 币种选择变化处理
    const onCurrencyChange = (currencyCode, currency) => {
      console.log('=== 币种选择变化调试 ===');
      console.log('币种代码:', currencyCode);
      console.log('币种对象:', currency);
      
      selectedCurrencyCode.value = currencyCode;
      
      // 设置币种ID用于查询
      if (currency && currency.id) {
        searchForm.value.currencyId = currency.id;
        console.log('✅ 设置币种ID:', currency.id);
        console.log('✅ 币种名称:', currency.currency_name);
        console.log('✅ 币种代码:', currency.currency_code);
      } else {
        searchForm.value.currencyId = '';
        console.log('❌ 币种对象无效或缺少ID，清空选择');
        console.log('币种对象详情:', currency);
      }
      
      console.log('当前searchForm.currencyId:', searchForm.value.currencyId);
      console.log('=======================');
      
      // 币种选择变化后自动查询
      handleSearch();
    };

    // 获取币种显示名称
    const getCurrencyDisplayName = (bal) => {
      if (!bal) return ''
      
      // 使用新的币种显示函数
      return getCurrencyDisplayNameFromUtils(bal.currencyCode, bal)
    };

    // 获取货币国旗表情
    const getCurrencyFlag = (code) => {
      const flagMap = {
        USD: '🇺🇸',
        EUR: '🇪🇺',
        GBP: '🇬🇧',
        JPY: '🇯🇵',
        AUD: '🇦🇺',
        CAD: '🇨🇦',
        CHF: '🇨🇭',
        CNY: '🇨🇳',
        SGD: '🇸🇬',
        RUB: '🇷🇺',
        HKD: '🇭🇰',
        TWD: '🇹🇼',
        KRW: '🇰🇷',
        THB: '🇹🇭',
        MYR: '🇲🇾',
        IDR: '🇮🇩',
        PHP: '🇵🇭',
        INR: '🇮🇳'
      };
      return flagMap[code] || code;
    };

    // 查询余额
    const handleSearch = async () => {
      loading.value = true;
      error.value = null;
      
      try {
        const params = {
          branch_id: searchForm.value.branchId,
          currency_id: searchForm.value.currencyId || undefined
        };
        
        console.log('=== 查询参数调试 ===');
        console.log('查询参数:', params);
        console.log('当前选择的币种代码:', selectedCurrencyCode.value);
        console.log('当前设置的币种ID:', searchForm.value.currencyId);
        console.log('是否包含currency_id参数:', params.currency_id !== undefined);
        console.log('==================');
        
        const response = await app.$api.get('balance-management/query', { params });
        
        console.log('=== 查询结果调试 ===');
        console.log('API响应:', response.data);
        console.log('返回的余额数量:', response.data.balances?.length || 0);
        if (response.data.balances && response.data.balances.length > 0) {
          console.log('第一个余额记录:', response.data.balances[0]);
        }
        console.log('==================');
        
        if (response.data.success) {
          // 对余额数据进行排序，让当前网点的本币显示在第一行
          const sortedBalances = sortBalancesWithBaseCurrencyFirst(response.data.balances);
          balances.value = sortedBalances;
        } else {
          // 处理多语言错误信息
          const errorMessage = response.data.message;
          if (errorMessage === 'no_permission_view_other_branch_balance') {
            error.value = t('queries.balance_query.errors.no_permission_view_other_branch_balance');
          } else {
            error.value = errorMessage || t('balance.query_failed');
          }
        }
      } catch (err) {
        // 处理多语言错误信息
        const errorMessage = err.response?.data?.message;
        if (errorMessage === 'no_permission_view_other_branch_balance') {
          error.value = t('queries.balance_query.errors.no_permission_view_other_branch_balance');
        } else {
          error.value = errorMessage || t('balance.query_failed');
        }
        console.error('查询失败:', err);
      } finally {
        loading.value = false;
      }
    };

    // 排序余额数据，让当前网点的本币显示在第一行
    const sortBalancesWithBaseCurrencyFirst = (balancesData) => {
      if (!balancesData || balancesData.length === 0) {
        return balancesData;
      }

      // 获取当前网点的本币信息
      const currentBranch = branches.value.find(b => b.id == userInfo.branch_id);
      if (!currentBranch) {
        return balancesData;
      }

      // 分离本币和其他币种
      const baseCurrencyBalances = [];
      const otherCurrencyBalances = [];

      balancesData.forEach(balance => {
        // 检查是否是当前网点的本币
        if (balance.branchId == userInfo.branch_id && 
            balance.currencyId == currentBranch.base_currency?.id) {
          baseCurrencyBalances.push(balance);
        } else {
          otherCurrencyBalances.push(balance);
        }
      });

      // 本币排在前面，其他币种按币种代码排序
      const sortedOtherCurrencies = otherCurrencyBalances.sort((a, b) => 
        a.currencyCode.localeCompare(b.currencyCode)
      );

      return [...baseCurrencyBalances, ...sortedOtherCurrencies];
    };

    // 判断是否是当前网点的本币
    const isBaseCurrency = (balance) => {
      const currentBranch = branches.value.find(b => b.id == userInfo.branch_id);
      if (!currentBranch) {
        return false;
      }
      // 通过币种ID判断是否是本币
      return balance.branchId == userInfo.branch_id && 
             balance.currencyId == currentBranch.base_currency?.id;
    };

    // 重置查询条件
    const resetSearch = () => {
      searchForm.value = {
        date: new Date().toISOString().split('T')[0],
        branchId: userInfo.branch_id,  // 重置时也设置为当前网点
        currencyId: ''
      };
      selectedCurrencyCode.value = '';
      // 触发币种选择器的清空事件
      onCurrencyChange('', null);
    };

    // 刷新数据
    const refreshData = () => {
      handleSearch();
    };

    // 导出数据
    const exportData = async () => {
      try {
        loading.value = true;
        
        // 构建导出参数
        const params = {
          date: searchForm.value.date,
          branch_id: searchForm.value.branchId,
          currency_id: searchForm.value.currencyId || undefined
        };
        
        // 调用导出API
        const response = await app.$api.get('balance-management/export', { params });
        
        if (response.data.success) {
          // 构建下载链接
          const downloadUrl = `${window.location.origin.replace(':8080', ':5001')}${response.data.download_url}`;
          
          // 创建下载链接并触发下载
          const link = document.createElement('a');
          link.href = downloadUrl;
          link.download = response.data.filename;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          
          // 显示成功消息
          if (app?.$toast) {
            app.$toast.success(t('balance.export_success'));
          } else {
            alert(t('balance.export_success'));
          }
        } else {
          error.value = response.data.message || t('balance.export_failed');
        }
      } catch (err) {
        error.value = t('balance.export_failed');
        console.error('导出失败:', err);
      } finally {
        loading.value = false;
      }
    };

    onMounted(async () => {
      // 获取网点信息
      await fetchBranches();
    });

    return {
      searchForm,
      loading,
      error,
      balances,
      branches,
      selectedCurrencyCode,
      today,
      isAdmin,
      handleSearch,
      resetSearch,
      refreshData,
      exportData,
      getCurrencyFlag,
      getCurrencyDisplayName,
      formatDateTime,
      formatAmount,
      isBaseCurrency,
      onCurrencyChange
    };
  }
};
</script>

<style scoped>
.currency-flag {
  font-size: 1.2em;
  margin-right: 0.5em;
}

.form-label {
  font-weight: 500;
}

.table th {
  white-space: nowrap;
  background-color: #f8f9fa;
  font-family: inherit !important;
}

.table td {
  vertical-align: middle;
}

.table-bordered {
  border: 1px solid #dee2e6;
}

.table-bordered th,
.table-bordered td {
  border: 1px solid #dee2e6;
}

.table-hover tbody tr:hover {
  background-color: rgba(0, 123, 255, 0.05);
}

.balance-column {
  padding-right: 1.5rem !important;
  font-weight: 600;
  font-family: 'Roboto Mono', monospace;
}

/* 表头保持默认字体，只有数据单元格使用等宽字体 */
.balance-column th,
th.balance-column {
  font-family: inherit !important;
  min-width: 120px;
}

/* 确保所有表头使用相同字体 */
.table thead th {
  font-family: inherit !important;
}

.time-column {
  padding-left: 1.5rem !important;
  font-size: 0.9rem;
  color: #6c757d;
  white-space: nowrap;
}

.time-column th {
  min-width: 160px;
}

.base-currency-badge {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.25rem 0.5rem;
  border-radius: 0.375rem;
  background-color: #007bff !important;
  color: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* 响应式布局 */
@media (max-width: 768px) {
  .col-md-2, .col-md-3, .col-md-5 {
    margin-bottom: 1rem;
  }
  
  .d-flex.gap-2 {
    flex-wrap: wrap;
    gap: 0.5rem !important;
  }
  
  .btn {
    font-size: 0.875rem;
    padding: 0.375rem 0.75rem;
  }
}

@media (max-width: 576px) {
  .table-responsive {
    font-size: 0.875rem;
  }
  
  .table td, .table th {
    padding: 0.5rem 0.25rem;
  }
  
  .balance-column, .time-column {
    padding-left: 0.25rem !important;
    padding-right: 0.25rem !important;
  }
}
</style>

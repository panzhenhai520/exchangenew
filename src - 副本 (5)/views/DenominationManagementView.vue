<template>
  <div class="container-fluid py-4">
    <div class="row">
      <div class="col-12">
        <div class="d-flex justify-content-between align-items-center mb-4">
          <h2 class="page-title-bold">
            <font-awesome-icon :icon="['fas', 'coins']" class="me-2" />
            {{ $t('denominations.title') }}
          </h2>
          <div class="btn-group">
            <button class="btn btn-primary" @click="showAddModal = true">
              <i class="fas fa-plus me-2"></i>
              {{ $t('denominations.add_denomination') }}
            </button>
            <button class="btn btn-outline-primary" @click="goToRateManagement">
              <i class="fas fa-chart-line me-2"></i>
              {{ $t('denominations.manage_rates') }}
            </button>
          </div>
        </div>
        
        <!-- 币种选择 -->
        <div class="row mb-4">
          <div class="col-md-6">
            <div class="card">
              <div class="card-header">
                <h6 class="mb-0">
                  <i class="fas fa-flag me-2"></i>
                  {{ $t('denominations.select_currency') }}
                </h6>
              </div>
              <div class="card-body">
                <select
                  class="form-select"
                  v-model="selectedCurrencyId"
                  @change="loadDenominations"
                >
                  <option value="">{{ $t('denominations.select_currency_placeholder') }}</option>
                  <option
                    v-for="currency in currencies"
                    :key="currency.id"
                    :value="currency.id"
                  >
                    <CurrencyFlag :code="currency.currency_code" class="me-2" />
                    {{ currency.currency_code }} - {{ getCurrencyName(currency.currency_code) }}
                  </option>
                </select>
              </div>
            </div>
          </div>
          <div class="col-md-6">
            <div class="card">
              <div class="card-header">
                <h6 class="mb-0">
                  <i class="fas fa-info-circle me-2"></i>
                  {{ $t('denominations.currency_info') }}
                </h6>
              </div>
              <div class="card-body" v-if="selectedCurrency">
                <div class="row g-2">
                  <div class="col-6">
                    <small class="text-muted">{{ $t('denominations.currency_code') }}:</small>
                    <div class="fw-bold">{{ selectedCurrency.currency_code }}</div>
                  </div>
                  <div class="col-6">
                    <small class="text-muted">{{ $t('denominations.denomination_count') }}:</small>
                    <div class="fw-bold">{{ denominations.length }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 面值列表 -->
        <div v-if="selectedCurrencyId && denominations.length > 0" class="row">
          <div class="col-12">
            <div class="card">
              <div class="card-header d-flex justify-content-between align-items-center">
                <h6 class="mb-0">
                  <i class="fas fa-list me-2"></i>
                  {{ $t('denominations.denomination_list') }}
                </h6>
                <div class="btn-group btn-group-sm">
                  <button class="btn btn-outline-primary" @click="sortByValue">
                    <i class="fas fa-sort-numeric-up me-1"></i>
                    {{ $t('denominations.sort_by_value') }}
                  </button>
                  <button class="btn btn-outline-primary" @click="sortByType">
                    <i class="fas fa-sort me-1"></i>
                    {{ $t('denominations.sort_by_type') }}
                  </button>
                </div>
              </div>
              <div class="card-body p-0">
                <div class="table-responsive">
                  <table class="table table-hover mb-0">
                    <thead class="table-light">
                      <tr>
                        <th width="5%">{{ $t('denominations.sort_order') }}</th>
                        <th width="15%">{{ $t('denominations.denomination_value') }}</th>
                        <th width="10%">{{ $t('denominations.type') }}</th>
                        <th width="10%">{{ $t('denominations.status') }}</th>
                        <th width="15%">{{ $t('denominations.created_at') }}</th>
                        <th width="15%">{{ $t('denominations.updated_at') }}</th>
                        <th width="30%">{{ $t('denominations.actions') }}</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="denom in sortedDenominations" :key="denom.id">
                        <td>
                          <input
                            type="number"
                            class="form-control form-control-sm"
                            v-model="denom.sort_order"
                            @change="updateSortOrder(denom)"
                            min="0"
                            style="width: 60px;"
                          />
                        </td>
                        <td class="denomination-value-cell">
                          <div class="d-flex align-items-center">
                            <i :class="denom.denomination_type === 'bill' ? 'fas fa-money-bill text-success me-2' : 'fas fa-coins text-warning me-2'"></i>
                            <span class="fw-bold">{{ formatDenominationValue(denom.denomination_value) }}</span>
                          </div>
                        </td>
                        <td>
                          <span class="badge" :class="denom.denomination_type === 'bill' ? 'bg-success' : 'bg-warning'">
                            {{ $t(`exchange.${denom.denomination_type}`) }}
                          </span>
                        </td>
                        <td>
                          <span class="badge" :class="denom.is_active ? 'bg-success' : 'bg-secondary'">
                            {{ denom.is_active ? $t('denominations.active') : $t('denominations.inactive') }}
                          </span>
                        </td>
                        <td>
                          <small class="text-muted">{{ formatDateTime(denom.created_at) }}</small>
                        </td>
                        <td>
                          <small class="text-muted">{{ formatDateTime(denom.updated_at) }}</small>
                        </td>
                        <td>
                          <div class="btn-group btn-group-sm">
                            <button
                              class="btn btn-outline-primary"
                              @click="editDenomination(denom)"
                              :title="$t('denominations.edit')"
                            >
                              <i class="fas fa-edit"></i>
                            </button>
                            <button
                              class="btn btn-outline-warning"
                              @click="toggleStatus(denom)"
                              :title="denom.is_active ? $t('denominations.deactivate') : $t('denominations.activate')"
                            >
                              <i :class="denom.is_active ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
                            </button>
                            <button
                              class="btn btn-outline-danger"
                              @click="deleteDenomination(denom)"
                              :disabled="!canDelete(denom)"
                              :title="$t('denominations.delete')"
                            >
                              <i class="fas fa-trash"></i>
                            </button>
                          </div>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 无面值提示 -->
        <div v-else-if="selectedCurrencyId && denominations.length === 0" class="row">
          <div class="col-12">
            <div class="alert alert-info text-center">
              <i class="fas fa-info-circle me-2"></i>
              {{ $t('denominations.no_denominations') }}
              <button class="btn btn-sm btn-primary ms-2" @click="showAddModal = true">
                <i class="fas fa-plus me-1"></i>
                {{ $t('denominations.add_first_denomination') }}
              </button>
            </div>
          </div>
        </div>
        
        <!-- 加载状态 -->
        <div v-if="loading" class="text-center py-4">
          <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">{{ $t('denominations.loading') }}</span>
              </div>
              <div class="mt-2">{{ $t('denominations.loading') }}</div>
        </div>
      </div>
    </div>
    
    <!-- 添加/编辑面值模态框 -->
    <div class="modal fade" id="denominationModal" tabindex="-1" data-bs-backdrop="static">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              <i class="fas fa-coins me-2"></i>
              {{ isEditing ? $t('denominations.edit_denomination') : $t('denominations.add_denomination') }}
            </h5>
            <button type="button" class="btn-close" @click="closeModal"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="saveDenomination">
              <div class="mb-3">
                <label class="form-label">{{ $t('denominations.denomination_value') }} <span class="text-danger">*</span></label>
                <input
                  type="number"
                  class="form-control"
                  v-model="formData.denomination_value"
                  step="0.01"
                  min="0"
                  required
                  :placeholder="$t('denominations.enter_denomination_value')"
                />
              </div>
              
              <div class="mb-3">
                <label class="form-label">{{ $t('denominations.type') }} <span class="text-danger">*</span></label>
                <div class="row g-2">
                  <div class="col-6">
                    <label class="form-check-label w-100" style="cursor: pointer;">
                      <input
                        type="radio"
                        class="form-check-input"
                        v-model="formData.denomination_type"
                        value="bill"
                        required
                      />
                      <div class="card h-100" :class="{ 'border-primary': formData.denomination_type === 'bill' }">
                        <div class="card-body text-center">
                          <i class="fas fa-money-bill text-success fa-2x mb-2"></i>
                          <div class="fw-bold">{{ $t('exchange.bill') }}</div>
                        </div>
                      </div>
                    </label>
                  </div>
                  <div class="col-6">
                    <label class="form-check-label w-100" style="cursor: pointer;">
                      <input
                        type="radio"
                        class="form-check-input"
                        v-model="formData.denomination_type"
                        value="coin"
                        required
                      />
                      <div class="card h-100" :class="{ 'border-primary': formData.denomination_type === 'coin' }">
                        <div class="card-body text-center">
                          <i class="fas fa-coins text-warning fa-2x mb-2"></i>
                          <div class="fw-bold">{{ $t('exchange.coin') }}</div>
                        </div>
                      </div>
                    </label>
                  </div>
                </div>
              </div>
              
              <div class="mb-3">
                <label class="form-label">{{ $t('denominations.sort_order') }}</label>
                <input
                  type="number"
                  class="form-control"
                  v-model="formData.sort_order"
                  min="0"
                  :placeholder="$t('denominations.enter_sort_order')"
                />
              </div>
              
              <div class="mb-3">
                <div class="form-check">
                  <input
                    type="checkbox"
                    class="form-check-input"
                    v-model="formData.is_active"
                    id="is_active"
                  />
                  <label class="form-check-label" for="is_active">
                    {{ $t('denominations.is_active') }}
                  </label>
                </div>
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeModal">
              {{ $t('denominations.cancel') }}
            </button>
            <button type="button" class="btn btn-primary" @click="saveDenomination" :disabled="saving">
              <i class="fas fa-save me-1" :class="{ 'fa-spin': saving }"></i>
              {{ saving ? $t('denominations.saving') : $t('denominations.save') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import CurrencyFlag from '@/components/CurrencyFlag.vue'
import { getCurrencyName } from '@/utils/currencyTranslator'
import { Modal } from 'bootstrap'

export default {
  name: 'DenominationManagementView',
  components: {
    CurrencyFlag
  },
  data() {
    return {
      currencies: [],
      selectedCurrencyId: null,
      selectedCurrency: null,
      denominations: [],
      loading: false,
      saving: false,
      showAddModal: false,
      isEditing: false,
      formData: {
        denomination_value: '',
        denomination_type: 'bill',
        sort_order: 0,
        is_active: true
      },
      editingId: null
    }
  },
  computed: {
    sortedDenominations() {
      return [...this.denominations].sort((a, b) => {
        if (a.sort_order !== b.sort_order) {
          return a.sort_order - b.sort_order;
        }
        return a.denomination_value - b.denomination_value;
      });
    }
  },
  mounted() {
    this.loadCurrencies();
    
    // 检查URL参数中是否有币种ID
    const currencyId = this.$route.query.currency_id;
    if (currencyId) {
      this.selectedCurrencyId = parseInt(currencyId);
      console.log('从URL参数获取币种ID:', this.selectedCurrencyId);
    }
  },
  methods: {
    async loadCurrencies() {
      this.loading = true;
      try {
        const response = await this.$api.get('/system/currencies');
        if (response.data.success && response.data.currencies) {
          this.currencies = response.data.currencies.filter(c => !c.is_base);
        } else {
          this.currencies = [];
          console.warn('币种数据为空或格式不正确:', response.data);
        }
      } catch (error) {
        console.error('加载币种失败:', error);
        this.$toast.error('加载币种失败');
        this.currencies = [];
      } finally {
        this.loading = false;
      }
    },
    
    async loadDenominations() {
      if (!this.selectedCurrencyId) {
        this.denominations = [];
        this.selectedCurrency = null;
        return;
      }
      
      this.loading = true;
      try {
        const response = await this.$api.get(`/denominations/${this.selectedCurrencyId}`);
        if (response.data.success) {
          this.denominations = response.data.data;
          this.selectedCurrency = this.currencies.find(c => c.id === this.selectedCurrencyId);
        } else {
          this.$toast.error(response.data.message || '加载面值失败');
        }
      } catch (error) {
        console.error('加载面值失败:', error);
        this.$toast.error('加载面值失败');
      } finally {
        this.loading = false;
      }
    },
    
    editDenomination(denom) {
      this.isEditing = true;
      this.editingId = denom.id;
      this.formData = {
        denomination_value: denom.denomination_value,
        denomination_type: denom.denomination_type,
        sort_order: denom.sort_order,
        is_active: denom.is_active
      };
      this.showAddModal = true;
    },
    
    async saveDenomination() {
      if (!this.formData.denomination_value || !this.formData.denomination_type) {
        this.$toast.error('请填写完整信息');
        return;
      }
      
      this.saving = true;
      try {
        const data = {
          currency_id: this.selectedCurrencyId,
          denomination_value: parseFloat(this.formData.denomination_value),
          denomination_type: this.formData.denomination_type,
          sort_order: parseInt(this.formData.sort_order) || 0,
          is_active: this.formData.is_active
        };
        
        let response;
        if (this.isEditing) {
          response = await this.$api.put(`/denominations/${this.editingId}`, data);
        } else {
          response = await this.$api.post('/denominations', data);
        }
        
        if (response.data.success) {
          this.$toast.success(this.isEditing ? '面值更新成功' : '面值创建成功');
          this.closeModal();
          this.loadDenominations();
        } else {
          this.$toast.error(response.data.message || '保存失败');
        }
      } catch (error) {
        console.error('保存面值失败:', error);
        this.$toast.error('保存面值失败');
      } finally {
        this.saving = false;
      }
    },
    
    async toggleStatus(denom) {
      try {
        const response = await this.$api.put(`/denominations/${denom.id}`, {
          is_active: !denom.is_active
        });
        
        if (response.data.success) {
          denom.is_active = !denom.is_active;
          this.$toast.success(denom.is_active ? '面值已激活' : '面值已停用');
        } else {
          this.$toast.error(response.data.message || '操作失败');
        }
      } catch (error) {
        console.error('切换状态失败:', error);
        this.$toast.error('切换状态失败');
      }
    },
    
    async deleteDenomination(denom) {
      if (!this.canDelete(denom)) {
        this.$toast.warning('该面值存在汇率记录，无法删除');
        return;
      }
      
      if (!confirm('确定要删除这个面值吗？')) {
        return;
      }
      
      try {
        const response = await this.$api.delete(`/denominations/${denom.id}`);
        if (response.data.success) {
          this.$toast.success('面值删除成功');
          this.loadDenominations();
        } else {
          this.$toast.error(response.data.message || '删除失败');
        }
      } catch (error) {
        console.error('删除面值失败:', error);
        this.$toast.error('删除面值失败');
      }
    },
    
    async updateSortOrder(denom) {
      try {
        const response = await this.$api.put(`/denominations/${denom.id}`, {
          sort_order: denom.sort_order
        });
        
        if (!response.data.success) {
          this.$toast.error('更新排序失败');
          this.loadDenominations(); // 重新加载以恢复原值
        }
      } catch (error) {
        console.error('更新排序失败:', error);
        this.$toast.error('更新排序失败');
        this.loadDenominations(); // 重新加载以恢复原值
      }
    },
    
    sortByValue() {
      this.denominations.sort((a, b) => a.denomination_value - b.denomination_value);
    },
    
    sortByType() {
      this.denominations.sort((a, b) => {
        if (a.denomination_type !== b.denomination_type) {
          return a.denomination_type.localeCompare(b.denomination_type);
        }
        return a.denomination_value - b.denomination_value;
      });
    },
    
    closeModal() {
      // 先关闭Bootstrap模态窗口
      const modalElement = document.getElementById('denominationModal');
      if (modalElement) {
        const modal = Modal.getInstance(modalElement);
        if (modal) {
          modal.hide();
        }
      }
      
      // 然后重置状态
      this.showAddModal = false;
      this.isEditing = false;
      this.editingId = null;
      this.formData = {
        denomination_value: '',
        denomination_type: 'bill',
        sort_order: 0,
        is_active: true
      };
    },
    
    goToRateManagement() {
      this.$router.push('/rates?tab=denomination-rates');
    },
    
    canDelete(/* denom */) {
      // 检查是否有相关汇率记录
      // 这里需要根据实际业务逻辑来判断
      return true; // 暂时返回true，实际应该检查数据库
    },
    
    formatDenominationValue(value) {
      return new Intl.NumberFormat('zh-CN', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
      }).format(value);
    },
    
    formatDateTime(dateTime) {
      if (!dateTime) return '-';
      return new Date(dateTime).toLocaleString('zh-CN');
    },
    
    getCurrencyName(code) {
      return getCurrencyName(code);
    }
  },
  watch: {
    selectedCurrencyId(newId) {
      if (newId) {
        this.loadDenominations();
      } else {
        this.denominations = [];
        this.selectedCurrency = null;
      }
    },
    showAddModal(newVal) {
      if (newVal) {
        // 显示模态框
        this.$nextTick(() => {
          const modal = new Modal(document.getElementById('denominationModal'));
          modal.show();
        });
      }
    }
  }
}
</script>

<style scoped>
.page-title-bold {
  font-weight: 600;
  color: #2c3e50;
}

.denomination-value-cell {
  font-size: 1.1rem;
}

.table th {
  font-weight: 600;
  font-size: 0.875rem;
  border-top: none;
}

.table td {
  vertical-align: middle;
}

.btn-group-sm .btn {
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
}

.form-check-input:checked + .card {
  border-color: var(--bs-primary) !important;
  box-shadow: 0 0 0 0.2rem rgba(13, 110, 253, 0.25);
}

.modal-header {
  border-bottom: 1px solid #dee2e6;
}

.modal-footer {
  border-top: 1px solid #dee2e6;
}

.card {
  transition: all 0.2s ease;
}

.card:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}
</style>
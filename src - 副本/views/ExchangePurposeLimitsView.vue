<template>
  <div class="container-fluid py-4">
    <div class="row">
      <div class="col-12">
        <div class="d-flex justify-content-between align-items-center mb-4">
          <h2>
            <font-awesome-icon :icon="['fas', 'clipboard-list']" class="me-2" />
            兑换提示信息维护
          </h2>
          <button class="btn btn-primary" @click="showAddModal">
            <font-awesome-icon :icon="['fas', 'plus']" class="me-1" />
            新增用途限额
          </button>
        </div>

        <div class="card">
          <div class="card-header">
            <h5 class="mb-0">交易用途限额管理</h5>
          </div>
          <div class="card-body">
            <!-- 筛选条件 -->
            <div class="row mb-3">
              <div class="col-md-3">
                <label class="form-label">币种筛选</label>
                <select class="form-select" v-model="filterCurrency" @change="fetchPurposeLimits">
                  <option value="">全部币种</option>
                  <option v-for="currency in currencies" :key="currency.currency_code" :value="currency.currency_code">
                    {{ currency.currency_code }} - {{ currency.currency_name }}
                  </option>
                </select>
              </div>
              <div class="col-md-3">
                <label class="form-label">状态筛选</label>
                <select class="form-select" v-model="filterStatus" @change="fetchPurposeLimits">
                  <option value="">全部状态</option>
                  <option value="true">启用</option>
                  <option value="false">停用</option>
                </select>
              </div>
            </div>

            <!-- 数据表格 -->
            <div class="table-responsive">
              <table class="table table-striped table-hover">
                <thead>
                  <tr>
                    <th width="60">序号</th>
                    <th>用途名称</th>
                    <th>币种</th>
                    <th>限额</th>
                    <th>提示信息</th>
                    <th>状态</th>
                    <th>创建时间</th>
                    <th width="120">操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="loading">
                    <td colspan="8" class="text-center py-3">
                      <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">加载中...</span>
                      </div>
                    </td>
                  </tr>
                  <tr v-else-if="purposeLimits.length === 0">
                    <td colspan="8" class="text-center py-3">
                      <span class="text-muted">暂无数据</span>
                    </td>
                  </tr>
                  <tr v-for="(item, index) in purposeLimits" :key="item.id">
                    <td class="text-center">{{ index + 1 }}</td>
                    <td>
                      <span class="badge bg-info">{{ item.purpose_name }}</span>
                    </td>
                    <td>{{ item.currency_code }}</td>
                    <td class="text-end">{{ formatAmount(item.max_amount) }}</td>
                    <td>
                      <span class="text-truncate d-inline-block" style="max-width: 200px;" :title="item.display_message">
                        {{ item.display_message }}
                      </span>
                    </td>
                    <td>
                      <span class="badge" :class="item.is_active ? 'bg-success' : 'bg-danger'">
                        {{ item.is_active ? '启用' : '停用' }}
                      </span>
                    </td>
                    <td>{{ formatDateTime(item.created_at) }}</td>
                    <td>
                      <button class="btn btn-sm btn-primary me-1" @click="editItem(item)">
                        <font-awesome-icon :icon="['fas', 'edit']" />
                      </button>
                      <button class="btn btn-sm btn-danger" @click="deleteItem(item)">
                        <font-awesome-icon :icon="['fas', 'trash']" />
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- 新增/编辑弹窗 -->
        <div class="modal fade" id="purposeLimitModal" tabindex="-1">
          <div class="modal-dialog">
            <div class="modal-content">
              <div class="modal-header">
                <h5 class="modal-title">{{ editingItem ? '编辑用途限额' : '新增用途限额' }}</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
              </div>
              <div class="modal-body">
                <form @submit.prevent="saveItem">
                  <div class="mb-3">
                    <label class="form-label">用途名称 <span class="text-danger">*</span></label>
                    <input 
                      type="text" 
                      class="form-control" 
                      v-model="form.purpose_name" 
                      required
                      placeholder="如：旅行、商务、留学等"
                    />
                  </div>
                  <div class="mb-3">
                    <label class="form-label">币种 <span class="text-danger">*</span></label>
                    <select class="form-select" v-model="form.currency_code" required>
                      <option value="">请选择币种</option>
                      <option v-for="currency in currencies" :key="currency.currency_code" :value="currency.currency_code">
                        {{ currency.currency_code }} - {{ currency.currency_name }}
                      </option>
                    </select>
                  </div>
                  <div class="mb-3">
                    <label class="form-label">限额 <span class="text-danger">*</span></label>
                    <div class="input-group">
                      <input 
                        type="number" 
                        class="form-control" 
                        v-model="form.max_amount" 
                        required
                        min="0"
                        step="0.01"
                        placeholder="0.00"
                      />
                      <span class="input-group-text">{{ form.currency_code || 'XXX' }}</span>
                    </div>
                  </div>
                  <div class="mb-3">
                    <label class="form-label">提示信息 <span class="text-danger">*</span></label>
                    <textarea 
                      class="form-control" 
                      v-model="form.display_message" 
                      required
                      rows="3"
                      placeholder="如：旅行用途最高限额 800,000 THB"
                    ></textarea>
                  </div>
                  <div class="mb-3">
                    <div class="form-check">
                      <input 
                        type="checkbox" 
                        class="form-check-input" 
                        id="is_active" 
                        v-model="form.is_active"
                      />
                      <label class="form-check-label" for="is_active">启用状态</label>
                    </div>
                  </div>
                </form>
              </div>
              <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                <button type="button" class="btn btn-primary" @click="saveItem" :disabled="saving">
                  {{ saving ? '保存中...' : '保存' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { Modal } from 'bootstrap'

export default {
  name: 'ExchangePurposeLimitsView',
  data() {
    return {
      purposeLimits: [],
      currencies: [],
      loading: false,
      saving: false,
      editingItem: null,
      modal: null,
      filterCurrency: '',
      filterStatus: '',
      form: {
        purpose_name: '',
        currency_code: '',
        max_amount: '',
        display_message: '',
        is_active: true
      }
    }
  },
  methods: {
    async fetchPurposeLimits() {
      this.loading = true;
      try {
        const params = {};
        if (this.filterCurrency) params.currency_code = this.filterCurrency;
        if (this.filterStatus !== '') params.is_active = this.filterStatus;

        const response = await this.$api.get('system/purpose-limits', { params });
        if (response.data.success) {
          this.purposeLimits = response.data.purpose_limits;
        } else {
          this.$toast.error(response.data.message || '获取数据失败');
        }
      } catch (error) {
        console.error('获取用途限额失败:', error);
        this.$toast.error('获取数据失败');
      } finally {
        this.loading = false;
      }
    },

    async fetchCurrencies() {
      try {
        const response = await this.$api.get('/currencies');
        if (response.data.success) {
          this.currencies = response.data.currencies;
        }
      } catch (error) {
        console.error('获取币种失败:', error);
      }
    },

    showAddModal() {
      this.editingItem = null;
      this.form = {
        purpose_name: '',
        currency_code: '',
        max_amount: '',
        display_message: '',
        is_active: true
      };
      this.showModal();
    },

    editItem(item) {
      this.editingItem = item;
      this.form = {
        purpose_name: item.purpose_name,
        currency_code: item.currency_code,
        max_amount: item.max_amount,
        display_message: item.display_message,
        is_active: item.is_active
      };
      this.showModal();
    },

    showModal() {
      if (!this.modal) {
        this.modal = new Modal(document.getElementById('purposeLimitModal'));
      }
      this.modal.show();
    },

    async saveItem() {
      this.saving = true;
      try {
        let response;
        if (this.editingItem) {
          response = await this.$api.put(`system/purpose-limits/${this.editingItem.id}`, this.form);
        } else {
          response = await this.$api.post('system/purpose-limits', this.form);
        }

        if (response.data.success) {
          this.$toast.success(this.editingItem ? '更新成功' : '添加成功');
          this.modal.hide();
          await this.fetchPurposeLimits();
        } else {
          this.$toast.error(response.data.message || '保存失败');
        }
      } catch (error) {
        console.error('保存失败:', error);
        this.$toast.error('保存失败');
      } finally {
        this.saving = false;
      }
    },

    async deleteItem(item) {
      if (!confirm('确定要删除这条记录吗？')) return;
      
      try {
        const response = await this.$api.delete(`system/purpose-limits/${item.id}`);
        if (response.data.success) {
          this.$toast.success('删除成功');
          await this.fetchPurposeLimits();
        } else {
          this.$toast.error(response.data.message || '删除失败');
        }
      } catch (error) {
        console.error('删除失败:', error);
        this.$toast.error('删除失败');
      }
    },

    formatAmount(amount) {
      return new Intl.NumberFormat('zh-CN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(amount);
    },

    formatDateTime(dateTime) {
      if (!dateTime) return '-';
      return new Date(dateTime).toLocaleString('zh-CN');
    }
  },

  async mounted() {
    await this.fetchCurrencies();
    await this.fetchPurposeLimits();
  }
}
</script>

<style scoped>
.table th {
  white-space: nowrap;
}

.text-truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style> 
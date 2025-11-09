<template>
  <div class="transaction-report-config">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h6 class="mb-0">
        <font-awesome-icon :icon="['fas', 'file-invoice']" class="me-2" />
        {{ $t('standards.transaction_report.title') }}
      </h6>
      <button class="btn btn-primary btn-sm" @click="showAddConfigModal">
        <font-awesome-icon :icon="['fas', 'plus']" class="me-1" />
        {{ $t('standards.transaction_report.add_trigger') }}
      </button>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="text-center py-4">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">{{ $t('common.loading') }}</span>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else-if="configs.length === 0" class="text-center py-4 text-muted">
      <font-awesome-icon :icon="['fas', 'inbox']" size="3x" class="mb-3 opacity-50" />
      <p>{{ $t('standards.transaction_report.no_config') }}</p>
    </div>

    <!-- 配置列表 -->
    <div v-else class="table-responsive">
      <table class="table table-hover">
        <thead>
          <tr>
            <th>{{ $t('standards.transaction_report.report_type') }}</th>
            <th>{{ $t('standards.transaction_report.trigger_amount') }}</th>
            <th>{{ $t('standards.transaction_report.currency') }}</th>
            <th>{{ $t('standards.transaction_report.enabled') }}</th>
            <th>{{ $t('standards.transaction_report.actions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="config in configs" :key="config.id">
            <td>
              <span class="badge" :class="getReportTypeBadgeClass(config.report_type)">
                {{ config.report_type }}
              </span>
              <br />
              <small class="text-muted">{{ getReportTypeName(config.report_type) }}</small>
            </td>
            <td>
              <strong>{{ formatAmount(config.threshold_amount) }}</strong> THB
              <br />
              <small class="text-muted">{{ $t('standards.transaction_report.time_window') }}: {{ config.time_window_days }}{{ $t('standards.transaction_report.days') }}</small>
            </td>
            <td>
              <span v-if="config.currency_code">{{ config.currency_code }}</span>
              <span v-else class="text-muted">{{ $t('standards.transaction_report.all_currencies') }}</span>
            </td>
            <td>
              <div class="form-check form-switch">
                <input
                  class="form-check-input"
                  type="checkbox"
                  :id="'switch-' + config.id"
                  :checked="config.is_enabled"
                  @change="toggleEnabled(config)"
                />
                <label class="form-check-label" :for="'switch-' + config.id">
                  {{ config.is_enabled ? $t('common.enabled') : $t('common.disabled') }}
                </label>
              </div>
            </td>
            <td>
              <button class="btn btn-sm btn-outline-primary me-1" @click="editConfig(config)">
                <font-awesome-icon :icon="['fas', 'edit']" />
              </button>
              <button class="btn btn-sm btn-outline-danger" @click="deleteConfig(config)">
                <font-awesome-icon :icon="['fas', 'trash']" />
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 添加/编辑配置模态框 -->
    <div class="modal fade" id="configModal" tabindex="-1" ref="configModal">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              {{ editingConfig ? $t('standards.transaction_report.edit_config') : $t('standards.transaction_report.add_config') }}
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body">
            <!-- 模式切换标签 -->
            <ul class="nav nav-tabs mb-3" role="tablist">
              <li class="nav-item" role="presentation">
                <button
                  class="nav-link"
                  :class="{ active: configMode === 'simple' }"
                  @click="configMode = 'simple'"
                  type="button"
                >
                  <font-awesome-icon :icon="['fas', 'sliders-h']" class="me-1" />
                  {{ $t('standards.trigger.simple_mode') }}
                </button>
              </li>
              <li class="nav-item" role="presentation">
                <button
                  class="nav-link"
                  :class="{ active: configMode === 'advanced' }"
                  @click="configMode = 'advanced'"
                  type="button"
                >
                  <font-awesome-icon :icon="['fas', 'cogs']" class="me-1" />
                  {{ $t('standards.trigger.advanced_mode') }}
                </button>
              </li>
            </ul>

            <form @submit.prevent="saveConfig">
              <!-- 报告类型 (两种模式都显示) -->
              <div class="mb-3">
                <label class="form-label">{{ $t('standards.transaction_report.report_type') }}</label>
                <select class="form-select" v-model="formData.report_type" required>
                  <option value="AMLO-1-01">AMLO-1-01 - CTR (现金交易报告)</option>
                  <option value="AMLO-1-02">AMLO-1-02 - ATR (累计交易报告)</option>
                  <option value="AMLO-1-03">AMLO-1-03 - STR (可疑交易报告)</option>
                </select>
              </div>

              <!-- 简单模式表单 -->
              <div v-if="configMode === 'simple'">
                <div class="mb-3">
                  <label class="form-label">{{ $t('standards.transaction_report.threshold_amount') }} (THB)</label>
                  <input
                    type="number"
                    class="form-control"
                    v-model.number="formData.threshold_amount"
                    min="0"
                    step="0.01"
                    required
                  />
                  <small class="form-text text-muted">
                    {{ $t('standards.transaction_report.threshold_hint') }}
                  </small>
                </div>

                <div class="mb-3">
                  <label class="form-label">{{ $t('standards.transaction_report.time_window') }} ({{ $t('standards.transaction_report.days') }})</label>
                  <input
                    type="number"
                    class="form-control"
                    v-model.number="formData.time_window_days"
                    min="1"
                    max="365"
                    required
                  />
                  <small class="form-text text-muted">
                    {{ $t('standards.transaction_report.time_window_hint') }}
                  </small>
                </div>

                <div class="mb-3">
                  <label class="form-label">{{ $t('standards.transaction_report.currency') }}</label>
                  <select class="form-select" v-model="formData.currency_code">
                    <option value="">{{ $t('standards.transaction_report.all_currencies') }}</option>
                    <option v-for="currency in availableCurrencies" :key="currency.code" :value="currency.code">
                      {{ currency.code }} - {{ currency.name }}
                    </option>
                  </select>
                </div>
              </div>

              <!-- 高级模式 - 规则构建器 -->
              <div v-else-if="configMode === 'advanced'">
                <AdvancedTriggerRuleBuilder
                  v-model="advancedRuleExpression"
                  :availableCurrencies="availableCurrencies"
                />
              </div>

              <!-- 启用开关 (两种模式都显示) -->
              <div class="mb-3">
                <div class="form-check form-switch">
                  <input
                    class="form-check-input"
                    type="checkbox"
                    id="enabledSwitch"
                    v-model="formData.is_enabled"
                  />
                  <label class="form-check-label" for="enabledSwitch">
                    {{ $t('standards.transaction_report.enable_trigger') }}
                  </label>
                </div>
              </div>

              <div class="d-flex justify-content-end">
                <button type="button" class="btn btn-secondary me-2" data-bs-dismiss="modal">
                  {{ $t('common.cancel') }}
                </button>
                <button type="submit" class="btn btn-primary">
                  {{ $t('common.save') }}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import { Modal } from 'bootstrap';
import axios from 'axios';
import AdvancedTriggerRuleBuilder from './AdvancedTriggerRuleBuilder.vue';

export default {
  name: 'TransactionReportConfig',
  components: {
    AdvancedTriggerRuleBuilder
  },
  setup() {
    const loading = ref(false);
    const configs = ref([]);
    const availableCurrencies = ref([]);
    const editingConfig = ref(null);
    const configModal = ref(null);
    const configMode = ref('simple'); // 'simple' or 'advanced'
    let modalInstance = null;

    const formData = ref({
      report_type: 'AMLO-1-01',
      threshold_amount: 450000,
      time_window_days: 1,
      currency_code: '',
      is_enabled: true
    });

    const advancedRuleExpression = ref({
      logic: 'AND',
      conditions: [
        { field: 'amount', operator: '>=', value: 450000 }
      ]
    });

    // 获取配置列表
    const loadConfigs = async () => {
      loading.value = true;
      try {
        const response = await axios.get('/api/compliance/trigger-rules');
        if (response.data.success) {
          const rawData = response.data.data || response.data.rules || [];

          // 转换后端数据格式为前端期望的格式
          configs.value = rawData.map(rule => {
            // 从rule_expression中提取threshold_amount, time_window_days, currency_code
            let threshold_amount = 450000;
            let time_window_days = 1;
            let currency_code = '';

            if (rule.rule_expression && rule.rule_expression.conditions) {
              rule.rule_expression.conditions.forEach(condition => {
                if (condition.field === 'amount') {
                  threshold_amount = condition.value;
                } else if (condition.field === 'time_window_days') {
                  time_window_days = condition.value;
                } else if (condition.field === 'currency_code') {
                  currency_code = condition.value;
                }
              });
            }

            return {
              id: rule.id,
              report_type: rule.report_type,
              threshold_amount,
              time_window_days,
              currency_code,
              is_enabled: rule.is_active,
              is_active: rule.is_active
            };
          });
        }
      } catch (error) {
        console.error('加载配置失败:', error);
      } finally {
        loading.value = false;
      }
    };

    // 加载可用币种
    const loadCurrencies = async () => {
      try {
        const response = await axios.get('/api/currencies');
        if (response.data.success) {
          availableCurrencies.value = response.data.currencies;
        }
      } catch (error) {
        console.error('加载币种失败:', error);
      }
    };

    // 显示添加配置模态框
    const showAddConfigModal = () => {
      editingConfig.value = null;
      configMode.value = 'simple';
      formData.value = {
        report_type: 'AMLO-1-01',
        threshold_amount: 450000,
        time_window_days: 1,
        currency_code: '',
        is_enabled: true
      };
      advancedRuleExpression.value = {
        logic: 'AND',
        conditions: [
          { field: 'amount', operator: '>=', value: 450000 }
        ]
      };
      modalInstance.show();
    };

    // 编辑配置
    const editConfig = (config) => {
      editingConfig.value = config;
      formData.value = { ...config };

      // 检测是否应该使用高级模式
      // 如果rule_expression包含多个条件或使用了复杂操作符，则使用高级模式
      if (config.rule_expression && config.rule_expression.conditions) {
        const conditions = config.rule_expression.conditions;
        const hasMultipleConditions = conditions.length > 1;
        const hasComplexOperators = conditions.some(c =>
          ['in', 'not in', '!=', '<', '>'].includes(c.operator)
        );

        if (hasMultipleConditions || hasComplexOperators || config.rule_expression.logic === 'OR') {
          configMode.value = 'advanced';
          advancedRuleExpression.value = { ...config.rule_expression };
        } else {
          configMode.value = 'simple';
        }
      } else {
        configMode.value = 'simple';
      }

      modalInstance.show();
    };

    // 保存配置
    const saveConfig = async () => {
      try {
        let ruleExpression;

        // 根据配置模式选择规则表达式
        if (configMode.value === 'advanced') {
          // 高级模式：直接使用高级规则构建器的输出
          ruleExpression = advancedRuleExpression.value;
        } else {
          // 简单模式：从表单数据构建规则表达式
          ruleExpression = {
            logic: 'AND',
            conditions: [
              {
                field: 'amount',
                operator: '>=',
                value: formData.value.threshold_amount
              }
            ]
          };

          // 如果指定了币种，添加币种条件
          if (formData.value.currency_code) {
            ruleExpression.conditions.push({
              field: 'currency_code',
              operator: '=',
              value: formData.value.currency_code
            });
          }

          // 添加时间窗口条件（转换为天数）
          if (formData.value.time_window_days && formData.value.time_window_days > 0) {
            ruleExpression.conditions.push({
              field: 'time_window_days',
              operator: '<=',
              value: formData.value.time_window_days
            });
          }
        }

        // 构建后端期望的数据结构
        const requestData = {
          rule_name: `${formData.value.report_type}_${Date.now()}`,
          report_type: formData.value.report_type,
          rule_expression: ruleExpression,
          priority: 50,
          is_active: formData.value.is_enabled,
          message_cn: `触发报告: ${formData.value.report_type}`
        };

        const url = editingConfig.value
          ? `/api/compliance/trigger-rules/${editingConfig.value.id}`
          : '/api/compliance/trigger-rules';

        const method = editingConfig.value ? 'put' : 'post';

        const response = await axios[method](url, requestData);

        if (response.data.success) {
          alert('保存成功');
          modalInstance.hide();
          await loadConfigs();
        }
      } catch (error) {
        console.error('保存配置失败:', error);
        alert('保存失败: ' + (error.response?.data?.message || error.message));
      }
    };

    // 切换启用状态
    const toggleEnabled = async (config) => {
      try {
        const response = await axios.put(`/api/compliance/trigger-rules/${config.id}`, {
          is_active: !config.is_active
        });

        if (response.data.success) {
          config.is_active = !config.is_active;
          // 同步更新is_enabled用于显示
          config.is_enabled = config.is_active;
        }
      } catch (error) {
        console.error('更新状态失败:', error);
        alert('更新失败: ' + (error.response?.data?.message || error.message));
      }
    };

    // 删除配置
    const deleteConfig = async (config) => {
      if (!confirm('确定要删除这个配置吗？')) {
        return;
      }

      try {
        const response = await axios.delete(`/api/compliance/trigger-rules/${config.id}`);
        if (response.data.success) {
          alert('删除成功');
          await loadConfigs();
        }
      } catch (error) {
        console.error('删除配置失败:', error);
        alert('删除失败: ' + (error.response?.data?.message || error.message));
      }
    };

    // 获取报告类型徽章样式
    const getReportTypeBadgeClass = (reportType) => {
      const classes = {
        'AMLO-1-01': 'bg-primary',
        'AMLO-1-02': 'bg-warning',
        'AMLO-1-03': 'bg-danger'
      };
      return classes[reportType] || 'bg-secondary';
    };

    // 获取报告类型名称
    const getReportTypeName = (reportType) => {
      const names = {
        'AMLO-1-01': '现金交易报告(CTR)',
        'AMLO-1-02': '累计交易报告(ATR)',
        'AMLO-1-03': '可疑交易报告(STR)'
      };
      return names[reportType] || reportType;
    };

    // 格式化金额
    const formatAmount = (amount) => {
      return parseFloat(amount).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      });
    };

    onMounted(() => {
      modalInstance = new Modal(configModal.value);
      loadConfigs();
      loadCurrencies();
    });

    return {
      loading,
      configs,
      availableCurrencies,
      editingConfig,
      configModal,
      configMode,
      formData,
      advancedRuleExpression,
      showAddConfigModal,
      editConfig,
      saveConfig,
      toggleEnabled,
      deleteConfig,
      getReportTypeBadgeClass,
      getReportTypeName,
      formatAmount
    };
  }
};
</script>

<style scoped>
.transaction-report-config {
  padding: 1rem;
}

.table {
  background-color: #fff;
}

.badge {
  font-size: 0.875rem;
  padding: 0.375rem 0.75rem;
}
</style>

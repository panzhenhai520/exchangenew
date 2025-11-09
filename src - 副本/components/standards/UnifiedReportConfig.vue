<template>
  <div class="unified-report-config">
    <!-- 顶部标题和操作按钮 -->
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h6 class="mb-0">
        <font-awesome-icon :icon="['fas', 'file-alt']" class="me-2" />
        {{ $t('standards.unified_report.title') }}
      </h6>
      <button class="btn btn-primary btn-sm" @click="showAddConfigModal">
        <font-awesome-icon :icon="['fas', 'plus']" class="me-1" />
        {{ $t('standards.unified_report.add_rule') }}
      </button>
    </div>

    <!-- 类别标签 -->
    <ul class="nav nav-tabs mb-3" role="tablist">
      <li class="nav-item" role="presentation">
        <button
          class="nav-link"
          :class="{ active: activeCategory === 'AMLO' }"
          @click="activeCategory = 'AMLO'"
          type="button"
        >
          <font-awesome-icon :icon="['fas', 'shield-alt']" class="me-1" />
          AMLO {{ $t('standards.unified_report.reports') }}
          <span class="badge bg-primary ms-2">{{ getConfigCount('AMLO') }}</span>
        </button>
      </li>
      <li class="nav-item" role="presentation">
        <button
          class="nav-link"
          :class="{ active: activeCategory === 'BOT' }"
          @click="activeCategory = 'BOT'"
          type="button"
        >
          <font-awesome-icon :icon="['fas', 'bank']" class="me-1" />
          BOT {{ $t('standards.unified_report.reports') }}
          <span class="badge bg-success ms-2">{{ getConfigCount('BOT') }}</span>
        </button>
      </li>
    </ul>

    <!-- 加载状态 -->
    <div v-if="loading" class="text-center py-4">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">{{ $t('common.loading') }}</span>
      </div>
    </div>

    <!-- 配置列表 -->
    <div v-else>
      <!-- 空状态 -->
      <div v-if="filteredConfigs.length === 0" class="text-center py-4 text-muted">
        <font-awesome-icon :icon="['fas', 'inbox']" size="3x" class="mb-3 opacity-50" />
        <p>{{ $t('standards.unified_report.no_config') }}</p>
      </div>

      <!-- 配置卡片列表 -->
      <div v-else class="row g-3">
        <div v-for="config in filteredConfigs" :key="config.id" class="col-md-6 col-lg-4">
          <div class="card h-100 config-card" :class="{ 'border-success': config.is_active, 'border-secondary': !config.is_active }">
            <div class="card-header d-flex justify-content-between align-items-center">
              <span class="badge" :class="getCategoryBadgeClass(config.report_category)">
                {{ config.report_category }}
              </span>
              <span class="badge" :class="getReportTypeBadgeClass(config.report_type)">
                {{ config.report_type }}
              </span>
            </div>
            <div class="card-body">
              <h6 class="card-title">{{ getReportTypeName(config.report_type) }}</h6>

              <!-- 规则摘要 -->
              <div class="rule-summary mb-2">
                <small class="text-muted">
                  <font-awesome-icon :icon="['fas', 'sitemap']" class="me-1" />
                  {{ getRuleSummary(config) }}
                </small>
              </div>

              <!-- 条件数量 -->
              <div class="condition-count mb-2">
                <span class="badge bg-light text-dark">
                  <font-awesome-icon :icon="['fas', 'filter']" class="me-1" />
                  {{ getConditionCount(config) }} {{ $t('standards.unified_report.conditions') }}
                </span>
              </div>

              <!-- 状态开关 -->
              <div class="form-check form-switch mt-3">
                <input
                  class="form-check-input"
                  type="checkbox"
                  :id="'switch-' + config.id"
                  :checked="config.is_active"
                  @change="toggleEnabled(config)"
                />
                <label class="form-check-label" :for="'switch-' + config.id">
                  {{ config.is_active ? $t('common.enabled') : $t('common.disabled') }}
                </label>
              </div>
            </div>
            <div class="card-footer bg-transparent d-flex justify-content-end gap-2">
              <button class="btn btn-sm btn-outline-primary" @click="editConfig(config)">
                <font-awesome-icon :icon="['fas', 'edit']" />
                {{ $t('common.edit') }}
              </button>
              <button class="btn btn-sm btn-outline-danger" @click="deleteConfig(config)">
                <font-awesome-icon :icon="['fas', 'trash']" />
                {{ $t('common.delete') }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加/编辑配置模态框 -->
    <div class="modal fade" id="configModal" tabindex="-1" ref="configModal">
      <div class="modal-dialog modal-xl">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              {{ editingConfig ? $t('standards.unified_report.edit_rule') : $t('standards.unified_report.add_rule') }}
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="saveConfig">
              <div class="row g-3">
                <!-- 报告类别 -->
                <div class="col-md-4">
                  <label class="form-label">{{ $t('standards.unified_report.category') }}</label>
                  <select class="form-select" v-model="formData.report_category" @change="onCategoryChange" required>
                    <option value="AMLO">AMLO - {{ $t('standards.unified_report.anti_money_laundering') }}</option>
                    <option value="BOT">BOT - {{ $t('standards.unified_report.bank_of_thailand') }}</option>
                  </select>
                </div>

                <!-- 报告类型 -->
                <div class="col-md-4">
                  <label class="form-label">{{ $t('standards.unified_report.report_type') }}</label>
                  <select class="form-select" v-model="formData.report_type" required>
                    <optgroup v-if="formData.report_category === 'AMLO'" :label="$t('standards.unified_report.amlo_reports')">
                      <option value="AMLO-1-01">AMLO-1-01 - CTR ({{ $t('standards.unified_report.cash_transaction') }})</option>
                      <option value="AMLO-1-02">AMLO-1-02 - ATR ({{ $t('standards.unified_report.asset_transaction') }})</option>
                      <option value="AMLO-1-03">AMLO-1-03 - STR ({{ $t('standards.unified_report.suspicious_transaction') }})</option>
                    </optgroup>
                    <optgroup v-if="formData.report_category === 'BOT'" :label="$t('standards.unified_report.bot_reports')">
                      <option value="BOT-BuyFX">BOT-BuyFX ({{ $t('standards.unified_report.buy_foreign_currency') }})</option>
                      <option value="BOT-SellFX">BOT-SellFX ({{ $t('standards.unified_report.sell_foreign_currency') }})</option>
                      <option value="BOT-FCD">BOT-FCD ({{ $t('standards.unified_report.foreign_currency_deposit') }})</option>
                      <option value="BOT-Provider">BOT-Provider ({{ $t('standards.unified_report.balance_provider') }})</option>
                    </optgroup>
                  </select>
                </div>

                <!-- 优先级 -->
                <div class="col-md-4">
                  <label class="form-label">{{ $t('standards.unified_report.priority') }}</label>
                  <input
                    type="number"
                    class="form-control"
                    v-model.number="formData.priority"
                    min="1"
                    max="100"
                    required
                  />
                  <small class="form-text text-muted">{{ $t('standards.unified_report.priority_hint') }}</small>
                </div>
              </div>

              <!-- 配置模式切换 -->
              <ul class="nav nav-tabs my-3" role="tablist">
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

              <!-- 简单模式表单 -->
              <div v-if="configMode === 'simple'" class="simple-config-form">
                <div class="row g-3">
                  <div class="col-md-6">
                    <label class="form-label">{{ $t('standards.unified_report.threshold_amount') }} ({{ getThresholdCurrency() }})</label>
                    <input
                      type="number"
                      class="form-control"
                      v-model.number="formData.threshold_amount"
                      min="0"
                      step="0.01"
                      required
                    />
                    <small class="form-text text-muted">{{ getThresholdHint() }}</small>
                  </div>

                  <div class="col-md-6">
                    <label class="form-label">{{ $t('standards.unified_report.currency') }}</label>
                    <select class="form-select" v-model="formData.currency_code">
                      <option value="">{{ $t('standards.unified_report.all_currencies') }}</option>
                      <option v-for="currency in availableCurrencies" :key="currency.code" :value="currency.code">
                        {{ currency.code }} - {{ currency.name }}
                      </option>
                    </select>
                  </div>
                </div>
              </div>

              <!-- 高级模式 - 规则构建器 -->
              <div v-else-if="configMode === 'advanced'">
                <AdvancedTriggerRuleBuilder
                  v-model="advancedRuleExpression"
                  :availableCurrencies="availableCurrencies"
                />
              </div>

              <!-- 启用开关 -->
              <div class="mt-3">
                <div class="form-check form-switch">
                  <input
                    class="form-check-input"
                    type="checkbox"
                    id="enabledSwitch"
                    v-model="formData.is_active"
                  />
                  <label class="form-check-label" for="enabledSwitch">
                    {{ $t('standards.unified_report.enable_rule') }}
                  </label>
                </div>
              </div>

              <div class="d-flex justify-content-end mt-3 gap-2">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
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
import { ref, computed, onMounted } from 'vue';
import { Modal } from 'bootstrap';
import axios from 'axios';
import AdvancedTriggerRuleBuilder from './AdvancedTriggerRuleBuilder.vue';

export default {
  name: 'UnifiedReportConfig',
  components: {
    AdvancedTriggerRuleBuilder
  },
  setup() {
    const loading = ref(false);
    const configs = ref([]);
    const availableCurrencies = ref([]);
    const activeCategory = ref('AMLO');
    const editingConfig = ref(null);
    const configModal = ref(null);
    const configMode = ref('simple');
    let modalInstance = null;

    const formData = ref({
      report_category: 'AMLO',
      report_type: 'AMLO-1-01',
      threshold_amount: 450000,
      currency_code: '',
      priority: 50,
      is_active: true
    });

    const advancedRuleExpression = ref({
      logic: 'AND',
      conditions: [
        { field: 'amount', operator: '>=', value: 450000 }
      ]
    });

    // 计算属性：过滤后的配置
    const filteredConfigs = computed(() => {
      return configs.value.filter(c => c.report_category === activeCategory.value);
    });

    // 获取配置数量
    const getConfigCount = (category) => {
      return configs.value.filter(c => c.report_category === category).length;
    };

    // 获取类别徽章样式
    const getCategoryBadgeClass = (category) => {
      return category === 'AMLO' ? 'bg-primary' : 'bg-success';
    };

    // 获取报告类型徽章样式
    const getReportTypeBadgeClass = (reportType) => {
      const classes = {
        'AMLO-1-01': 'bg-info',
        'AMLO-1-02': 'bg-warning',
        'AMLO-1-03': 'bg-danger',
        'BOT-BuyFX': 'bg-primary',
        'BOT-SellFX': 'bg-success',
        'BOT-FCD': 'bg-warning',
        'BOT-Provider': 'bg-info'
      };
      return classes[reportType] || 'bg-secondary';
    };

    // 获取报告类型名称
    const getReportTypeName = (reportType) => {
      const names = {
        'AMLO-1-01': '现金交易报告(CTR)',
        'AMLO-1-02': '资产交易报告(ATR)',
        'AMLO-1-03': '可疑交易报告(STR)',
        'BOT-BuyFX': 'BOT买入外币',
        'BOT-SellFX': 'BOT卖出外币',
        'BOT-FCD': 'BOT外币存款',
        'BOT-Provider': 'BOT余额调节'
      };
      return names[reportType] || reportType;
    };

    // 获取规则摘要
    const getRuleSummary = (config) => {
      if (!config.rule_expression || !config.rule_expression.conditions) {
        return '未配置条件';
      }

      const logic = config.rule_expression.logic === 'AND' ? '且' : '或';
      const conditionCount = config.rule_expression.conditions.length;

      // 获取第一个条件的描述
      const firstCondition = config.rule_expression.conditions[0];
      if (firstCondition.field === 'amount') {
        const value = parseFloat(firstCondition.value).toLocaleString('en-US');
        return `金额 >= ${value}${conditionCount > 1 ? ` (${logic}${conditionCount - 1}个条件)` : ''}`;
      }

      return `${conditionCount}个条件 (${logic})`;
    };

    // 获取条件数量
    const getConditionCount = (config) => {
      if (!config.rule_expression || !config.rule_expression.conditions) {
        return 0;
      }
      return config.rule_expression.conditions.length;
    };

    // 获取阈值货币
    const getThresholdCurrency = () => {
      return formData.value.report_category === 'AMLO' ? 'THB' : 'USD等值';
    };

    // 获取阈值提示
    const getThresholdHint = () => {
      const hints = {
        'AMLO-1-01': '建议: 450,000 THB (现金交易报告)',
        'AMLO-1-02': '建议: 8,000,000 THB (资产交易报告)',
        'AMLO-1-03': '可疑交易无固定阈值',
        'BOT-BuyFX': '建议: 20,000 USD等值',
        'BOT-SellFX': '建议: 20,000 USD等值',
        'BOT-FCD': '建议: 50,000 USD等值',
        'BOT-Provider': '建议: 20,000 USD等值'
      };
      return hints[formData.value.report_type] || '';
    };

    // 类别改变时更新报告类型
    const onCategoryChange = () => {
      if (formData.value.report_category === 'AMLO') {
        formData.value.report_type = 'AMLO-1-01';
        formData.value.threshold_amount = 450000;
      } else {
        formData.value.report_type = 'BOT-BuyFX';
        formData.value.threshold_amount = 20000;
      }
    };

    // 加载配置列表
    const loadConfigs = async () => {
      loading.value = true;
      try {
        const response = await axios.get('/api/compliance/trigger-rules');
        if (response.data.success) {
          const rawData = response.data.data || response.data.rules || [];

          configs.value = rawData.map(rule => {
            // 从rule_expression中提取信息
            let threshold_amount = 0;
            let currency_code = '';

            if (rule.rule_expression && rule.rule_expression.conditions) {
              rule.rule_expression.conditions.forEach(condition => {
                if (condition.field === 'amount') {
                  threshold_amount = condition.value;
                } else if (condition.field === 'currency_code') {
                  currency_code = condition.value;
                }
              });
            }

            // 推断报告类别
            let report_category = 'AMLO';
            if (rule.report_type && rule.report_type.startsWith('BOT')) {
              report_category = 'BOT';
            }

            return {
              id: rule.id,
              report_category,
              report_type: rule.report_type,
              rule_expression: rule.rule_expression,
              threshold_amount,
              currency_code,
              priority: rule.priority || 50,
              is_active: rule.is_active,
              rule_name: rule.rule_name
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
        report_category: activeCategory.value,
        report_type: activeCategory.value === 'AMLO' ? 'AMLO-1-01' : 'BOT-BuyFX',
        threshold_amount: activeCategory.value === 'AMLO' ? 450000 : 20000,
        currency_code: '',
        priority: 50,
        is_active: true
      };
      advancedRuleExpression.value = {
        logic: 'AND',
        conditions: [
          { field: 'amount', operator: '>=', value: formData.value.threshold_amount }
        ]
      };
      modalInstance.show();
    };

    // 编辑配置
    const editConfig = (config) => {
      editingConfig.value = config;
      formData.value = { ...config };

      // 检测配置模式
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

        if (configMode.value === 'advanced') {
          ruleExpression = advancedRuleExpression.value;
        } else {
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

          if (formData.value.currency_code) {
            ruleExpression.conditions.push({
              field: 'currency_code',
              operator: '=',
              value: formData.value.currency_code
            });
          }
        }

        const requestData = {
          rule_name: `${formData.value.report_category}_${formData.value.report_type}_${Date.now()}`,
          report_type: formData.value.report_type,
          rule_expression: ruleExpression,
          priority: formData.value.priority,
          is_active: formData.value.is_active,
          message_cn: `${formData.value.report_category}报告: ${formData.value.report_type}`
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

    onMounted(() => {
      modalInstance = new Modal(configModal.value);
      loadConfigs();
      loadCurrencies();
    });

    return {
      loading,
      configs,
      availableCurrencies,
      activeCategory,
      filteredConfigs,
      editingConfig,
      configModal,
      configMode,
      formData,
      advancedRuleExpression,
      getConfigCount,
      getCategoryBadgeClass,
      getReportTypeBadgeClass,
      getReportTypeName,
      getRuleSummary,
      getConditionCount,
      getThresholdCurrency,
      getThresholdHint,
      onCategoryChange,
      showAddConfigModal,
      editConfig,
      saveConfig,
      toggleEnabled,
      deleteConfig
    };
  }
};
</script>

<style scoped>
.unified-report-config {
  padding: 1rem;
}

.config-card {
  transition: all 0.2s ease;
  border-width: 2px;
}

.config-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.config-card .card-header {
  background-color: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
}

.rule-summary {
  font-size: 0.875rem;
  line-height: 1.4;
}

.condition-count {
  font-size: 0.875rem;
}

.simple-config-form {
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 0.25rem;
}

.badge {
  font-size: 0.75rem;
  padding: 0.375rem 0.625rem;
}

.nav-tabs .nav-link {
  font-weight: 500;
}

.nav-tabs .nav-link.active {
  font-weight: 600;
}
</style>

<template>
  <div class="advanced-trigger-builder">
    <div class="rule-header mb-3">
      <div class="d-flex justify-content-between align-items-center">
        <h6 class="mb-0">
          <font-awesome-icon :icon="['fas', 'sitemap']" class="me-2" />
          {{ $t('standards.trigger.advanced_conditions') }}
        </h6>
        <div class="btn-group btn-group-sm" role="group">
          <button
            type="button"
            class="btn"
            :class="{ 'btn-primary': ruleLogic === 'AND', 'btn-outline-secondary': ruleLogic !== 'AND' }"
            @click="ruleLogic = 'AND'"
          >
            AND ({{ $t('standards.trigger.all_conditions') }})
          </button>
          <button
            type="button"
            class="btn"
            :class="{ 'btn-primary': ruleLogic === 'OR', 'btn-outline-secondary': ruleLogic !== 'OR' }"
            @click="ruleLogic = 'OR'"
          >
            OR ({{ $t('standards.trigger.any_condition') }})
          </button>
        </div>
      </div>
    </div>

    <!-- 条件列表 -->
    <div class="conditions-list">
      <div
        v-for="(condition, index) in conditions"
        :key="index"
        class="condition-item mb-2 p-3 border rounded bg-light"
      >
        <div class="row g-2">
          <!-- 字段选择 -->
          <div class="col-md-3">
            <label class="form-label small">{{ $t('standards.trigger.field') }}</label>
            <select class="form-select form-select-sm" v-model="condition.field">
              <option value="amount">{{ $t('standards.trigger.field_amount') }}</option>
              <option value="currency_code">{{ $t('standards.trigger.field_currency') }}</option>
              <option value="customer_country_code">{{ $t('standards.trigger.field_country') }}</option>
              <option value="transaction_type">{{ $t('standards.trigger.field_transaction_type') }}</option>
              <option value="payment_method">{{ $t('standards.trigger.field_payment_method') }}</option>
              <option value="time_window_days">{{ $t('standards.trigger.field_time_window') }}</option>
              <option value="accumulated_amount">{{ $t('standards.trigger.field_accumulated_amount') }}</option>
            </select>
          </div>

          <!-- 操作符选择 -->
          <div class="col-md-2">
            <label class="form-label small">{{ $t('standards.trigger.operator') }}</label>
            <select class="form-select form-select-sm" v-model="condition.operator">
              <option value="=">= ({{ $t('standards.trigger.equals') }})</option>
              <option value="!=">!= ({{ $t('standards.trigger.not_equals') }})</option>
              <option value=">=">&gt;= ({{ $t('standards.trigger.greater_equal') }})</option>
              <option value="<=">&lt;= ({{ $t('standards.trigger.less_equal') }})</option>
              <option value=">">&gt; ({{ $t('standards.trigger.greater') }})</option>
              <!-- eslint-disable-next-line vue/no-parsing-error -->
              <option value="<">&lt; ({{ $t('standards.trigger.less') }})</option>
              <option value="in">IN ({{ $t('standards.trigger.in_list') }})</option>
              <option value="not in">NOT IN ({{ $t('standards.trigger.not_in_list') }})</option>
            </select>
          </div>

          <!-- 值输入 -->
          <div class="col-md-5">
            <label class="form-label small">{{ $t('standards.trigger.value') }}</label>

            <!-- 数值输入 (金额、时间窗口等) -->
            <input
              v-if="['amount', 'time_window_days', 'accumulated_amount'].includes(condition.field)"
              type="number"
              class="form-control form-control-sm"
              v-model.number="condition.value"
              :placeholder="getFieldPlaceholder(condition.field)"
              step="0.01"
            />

            <!-- 多值输入 (IN/NOT IN操作符) -->
            <input
              v-else-if="['in', 'not in'].includes(condition.operator)"
              type="text"
              class="form-control form-control-sm"
              v-model="condition.valueText"
              @blur="parseMultiValue(condition)"
              :placeholder="$t('standards.trigger.multi_value_hint')"
            />

            <!-- 币种选择 -->
            <select
              v-else-if="condition.field === 'currency_code'"
              class="form-select form-select-sm"
              v-model="condition.value"
            >
              <option value="">{{ $t('standards.trigger.all_currencies') }}</option>
              <option v-for="currency in availableCurrencies" :key="currency.code" :value="currency.code">
                {{ currency.code }} - {{ currency.name }}
              </option>
            </select>

            <!-- 国家代码选择 -->
            <select
              v-else-if="condition.field === 'customer_country_code'"
              class="form-select form-select-sm"
              v-model="condition.value"
            >
              <option value="">{{ $t('standards.trigger.all_countries') }}</option>
              <option value="TH">TH - {{ $t('standards.trigger.thailand') }}</option>
              <option value="CN">CN - {{ $t('standards.trigger.china') }}</option>
              <option value="US">US - {{ $t('standards.trigger.usa') }}</option>
              <option value="JP">JP - {{ $t('standards.trigger.japan') }}</option>
              <option value="KR">KR - {{ $t('standards.trigger.korea') }}</option>
            </select>

            <!-- 交易类型选择 -->
            <select
              v-else-if="condition.field === 'transaction_type'"
              class="form-select form-select-sm"
              v-model="condition.value"
            >
              <option value="buy">{{ $t('standards.trigger.buy') }}</option>
              <option value="sell">{{ $t('standards.trigger.sell') }}</option>
            </select>

            <!-- 付款方式选择 -->
            <select
              v-else-if="condition.field === 'payment_method'"
              class="form-select form-select-sm"
              v-model="condition.value"
            >
              <option value="cash">{{ $t('standards.trigger.cash') }}</option>
              <option value="instrument_cheque">{{ $t('standards.trigger.instrument_cheque') }}</option>
              <option value="instrument_draft">{{ $t('standards.trigger.instrument_draft') }}</option>
              <option value="instrument_other">{{ $t('standards.trigger.instrument_other') }}</option>
              <option value="other">{{ $t('standards.trigger.other_method') }}</option>
            </select>

            <!-- 默认文本输入 -->
            <input
              v-else
              type="text"
              class="form-control form-control-sm"
              v-model="condition.value"
            />
          </div>

          <!-- 删除按钮 -->
          <div class="col-md-2 d-flex align-items-end">
            <button
              type="button"
              class="btn btn-sm btn-outline-danger w-100"
              @click="removeCondition(index)"
              :disabled="conditions.length === 1"
            >
              <font-awesome-icon :icon="['fas', 'trash']" />
              {{ $t('standards.trigger.remove') }}
            </button>
          </div>
        </div>

        <!-- 条件说明 -->
        <div class="condition-description mt-2">
          <small class="text-muted">
            <font-awesome-icon :icon="['fas', 'info-circle']" class="me-1" />
            {{ getConditionDescription(condition) }}
          </small>
        </div>
      </div>

      <!-- 添加条件按钮 -->
      <button
        type="button"
        class="btn btn-sm btn-outline-primary w-100"
        @click="addCondition"
      >
        <font-awesome-icon :icon="['fas', 'plus']" class="me-1" />
        {{ $t('standards.trigger.add_condition') }}
      </button>
    </div>

    <!-- 规则预览 -->
    <div class="rule-preview mt-3 p-3 bg-light border rounded">
      <h6 class="mb-2">
        <font-awesome-icon :icon="['fas', 'eye']" class="me-2" />
        {{ $t('standards.trigger.rule_preview') }}
      </h6>
      <div class="preview-content">
        <code class="d-block p-2 bg-white rounded">{{ getRuleExpression() }}</code>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch } from 'vue';

export default {
  name: 'AdvancedTriggerRuleBuilder',
  props: {
    modelValue: {
      type: Object,
      default: () => ({
        logic: 'AND',
        conditions: [
          { field: 'amount', operator: '>=', value: 450000 }
        ]
      })
    },
    availableCurrencies: {
      type: Array,
      default: () => []
    }
  },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    const ruleLogic = ref(props.modelValue.logic || 'AND');
    const conditions = ref(
      props.modelValue.conditions && props.modelValue.conditions.length > 0
        ? props.modelValue.conditions.map(c => ({
            ...c,
            valueText: Array.isArray(c.value) ? c.value.join(', ') : c.value
          }))
        : [{ field: 'amount', operator: '>=', value: 450000 }]
    );

    // 添加条件
    const addCondition = () => {
      conditions.value.push({
        field: 'amount',
        operator: '>=',
        value: 0
      });
    };

    // 删除条件
    const removeCondition = (index) => {
      if (conditions.value.length > 1) {
        conditions.value.splice(index, 1);
      }
    };

    // 解析多值输入 (用于IN/NOT IN操作符)
    const parseMultiValue = (condition) => {
      if (['in', 'not in'].includes(condition.operator)) {
        const values = condition.valueText.split(',').map(v => v.trim()).filter(v => v);
        condition.value = values;
      }
    };

    // 获取字段占位符
    const getFieldPlaceholder = (field) => {
      const placeholders = {
        'amount': '例如: 450000',
        'time_window_days': '例如: 1',
        'accumulated_amount': '例如: 500000'
      };
      return placeholders[field] || '';
    };

    // 获取条件描述
    const getConditionDescription = (condition) => {
      const fieldNames = {
        'amount': '交易金额',
        'currency_code': '币种代码',
        'customer_country_code': '客户国家代码',
        'transaction_type': '交易类型',
        'payment_method': '付款方式',
        'time_window_days': '时间窗口(天)',
        'accumulated_amount': '累计金额'
      };

      const operatorNames = {
        '=': '等于',
        '!=': '不等于',
        '>=': '大于等于',
        '<=': '小于等于',
        '>': '大于',
        '<': '小于',
        'in': '在列表中',
        'not in': '不在列表中'
      };

      const fieldName = fieldNames[condition.field] || condition.field;
      const operatorName = operatorNames[condition.operator] || condition.operator;
      let value = condition.value;

      // 格式化值显示
      if (Array.isArray(value)) {
        value = value.join(', ');
      } else if (condition.field === 'amount' || condition.field === 'accumulated_amount') {
        value = parseFloat(value).toLocaleString('en-US', { minimumFractionDigits: 2 });
      }

      return `当 ${fieldName} ${operatorName} ${value}`;
    };

    // 获取规则表达式
    const getRuleExpression = () => {
      return JSON.stringify({
        logic: ruleLogic.value,
        conditions: conditions.value.map(c => ({
          field: c.field,
          operator: c.operator,
          value: c.value
        }))
      }, null, 2);
    };

    // 监听变化并触发更新
    watch([ruleLogic, conditions], () => {
      const expression = {
        logic: ruleLogic.value,
        conditions: conditions.value.map(c => ({
          field: c.field,
          operator: c.operator,
          value: c.value
        }))
      };
      emit('update:modelValue', expression);
    }, { deep: true });

    return {
      ruleLogic,
      conditions,
      addCondition,
      removeCondition,
      parseMultiValue,
      getFieldPlaceholder,
      getConditionDescription,
      getRuleExpression
    };
  }
};
</script>

<style scoped>
.advanced-trigger-builder {
  max-width: 100%;
}

.condition-item {
  transition: all 0.2s ease;
}

.condition-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.preview-content code {
  font-size: 0.85rem;
  white-space: pre-wrap;
  word-break: break-all;
}

.btn-group-sm .btn {
  font-size: 0.875rem;
}

.form-label.small {
  font-size: 0.875rem;
  margin-bottom: 0.25rem;
}
</style>

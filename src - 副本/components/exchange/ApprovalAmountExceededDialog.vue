<template>
  <a-modal
    v-model:visible="visible"
    :title="$t('exchange.approval_amount_exceeded_title')"
    :width="600"
    :closable="false"
    :maskClosable="false"
  >
    <div class="approval-exceeded-content">
      <!-- 警告图标 -->
      <div class="warning-icon">
        <exclamation-circle-outlined style="font-size: 48px; color: #ff4d4f;" />
      </div>

      <!-- 错误信息 -->
      <div class="error-message">
        <p class="main-message">{{ errorData.message }}</p>
      </div>

      <!-- 金额对比 -->
      <div class="amount-comparison">
        <a-row :gutter="16">
          <a-col :span="12">
            <div class="amount-card approved">
              <div class="label">{{ $t('exchange.approved_amount') }}</div>
              <div class="value">{{ formatCurrency(errorData.approved_amount) }}</div>
            </div>
          </a-col>
          <a-col :span="12">
            <div class="amount-card actual">
              <div class="label">{{ $t('exchange.actual_amount') }}</div>
              <div class="value exceeded">{{ formatCurrency(errorData.actual_amount) }}</div>
            </div>
          </a-col>
        </a-row>
      </div>

      <!-- 预约信息 -->
      <div class="reservation-info">
        <a-descriptions :column="1" size="small" bordered>
          <a-descriptions-item :label="$t('exchange.reservation_no')">
            {{ errorData.reservation_no }}
          </a-descriptions-item>
          <a-descriptions-item :label="$t('exchange.report_type')">
            {{ errorData.report_type }}
          </a-descriptions-item>
          <a-descriptions-item :label="$t('exchange.exceed_amount')">
            <span class="exceed-value">
              {{ formatCurrency(errorData.actual_amount - errorData.approved_amount) }}
            </span>
          </a-descriptions-item>
        </a-descriptions>
      </div>

      <!-- 操作建议 -->
      <div class="suggestions">
        <p class="suggestions-title">{{ $t('exchange.suggestions') }}</p>
        <ol class="suggestions-list">
          <li>{{ $t('exchange.suggestion_reduce_amount', { amount: formatCurrency(errorData.approved_amount) }) }}</li>
          <li>{{ $t('exchange.suggestion_resubmit_approval') }}</li>
        </ol>
      </div>
    </div>

    <!-- 底部按钮 -->
    <template #footer>
      <a-space>
        <a-button @click="handleCancel">
          {{ $t('common.cancel') }}
        </a-button>
        <a-button type="primary" ghost @click="handleReduceAmount">
          {{ $t('exchange.reduce_amount') }}
        </a-button>
        <a-button type="primary" @click="handleResubmit">
          {{ $t('exchange.resubmit_approval') }}
        </a-button>
      </a-space>
    </template>
  </a-modal>
</template>

<script setup>
import { ref, computed } from 'vue';
import { ExclamationCircleOutlined } from '@ant-design/icons-vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  errorData: {
    type: Object,
    default: () => ({
      message: '',
      approved_amount: 0,
      actual_amount: 0,
      reservation_id: null,
      reservation_no: '',
      report_type: ''
    })
  }
});

const emit = defineEmits(['update:modelValue', 'reduce-amount', 'resubmit-approval', 'cancel']);

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
});

// 格式化货币
const formatCurrency = (amount) => {
  if (typeof amount !== 'number') {
    amount = parseFloat(amount) || 0;
  }
  return new Intl.NumberFormat('th-TH', {
    style: 'currency',
    currency: 'THB',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(amount);
};

// 处理降低金额
const handleReduceAmount = () => {
  emit('reduce-amount', props.errorData.approved_amount);
  visible.value = false;
};

// 处理重新提交审核
const handleResubmit = () => {
  emit('resubmit-approval', props.errorData);
  visible.value = false;
};

// 处理取消
const handleCancel = () => {
  emit('cancel');
  visible.value = false;
};
</script>

<style scoped lang="scss">
.approval-exceeded-content {
  padding: 20px 0;

  .warning-icon {
    text-align: center;
    margin-bottom: 20px;
  }

  .error-message {
    text-align: center;
    margin-bottom: 24px;

    .main-message {
      font-size: 16px;
      font-weight: 500;
      color: #262626;
      margin: 0;
    }
  }

  .amount-comparison {
    margin-bottom: 24px;

    .amount-card {
      background: #f5f5f5;
      border-radius: 8px;
      padding: 16px;
      text-align: center;

      &.approved {
        border: 2px solid #52c41a;
      }

      &.actual {
        border: 2px solid #ff4d4f;
      }

      .label {
        font-size: 12px;
        color: #8c8c8c;
        margin-bottom: 8px;
      }

      .value {
        font-size: 24px;
        font-weight: bold;
        color: #262626;

        &.exceeded {
          color: #ff4d4f;
        }
      }
    }
  }

  .reservation-info {
    margin-bottom: 24px;

    .exceed-value {
      color: #ff4d4f;
      font-weight: bold;
    }
  }

  .suggestions {
    background: #e6f7ff;
    border: 1px solid #91d5ff;
    border-radius: 4px;
    padding: 16px;

    .suggestions-title {
      font-weight: 500;
      color: #262626;
      margin-bottom: 8px;
    }

    .suggestions-list {
      margin: 0;
      padding-left: 20px;

      li {
        margin-bottom: 4px;
        color: #595959;

        &:last-child {
          margin-bottom: 0;
        }
      }
    }
  }
}
</style>

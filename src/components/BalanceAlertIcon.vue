<template>
  <div class="balance-alert-icon" v-if="alertStatus !== 'normal'">
    <font-awesome-icon 
      :icon="alertIcon" 
      :class="alertClass"
      :title="alertMessage"
    />
    <span class="alert-text" v-if="showText">{{ alertMessage }}</span>
  </div>
</template>

<script>
export default {
  name: 'BalanceAlertIcon',
  props: {
    alertStatus: {
      type: String,
      default: 'normal'
    }, // 'critical_low', 'warning_low', 'normal', 'warning_high', 'critical_high'
    alertMessage: {
      type: String,
      default: ''
    },
    showText: {
      type: Boolean,
      default: false
    }
  },
  computed: {
    alertIcon() {
      const icons = {
        'critical_low': ['fas', 'exclamation-triangle'],
        'warning_low': ['fas', 'exclamation-circle'],
        'warning_high': ['fas', 'info-circle'],
        'critical_high': ['fas', 'exclamation-triangle']
      };
      return icons[this.alertStatus] || ['fas', 'check-circle'];
    },
    alertClass() {
      return {
        'text-danger': this.alertStatus === 'critical_low',
        'text-warning': this.alertStatus === 'warning_low',
        'text-info': this.alertStatus === 'warning_high',
        'text-primary': this.alertStatus === 'critical_high',
        'text-success': this.alertStatus === 'normal',
        'pulse-animation': this.alertStatus.includes('critical')
      };
    }
  }
};
</script>

<style scoped>
.balance-alert-icon {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.alert-text {
  font-size: 0.875rem;
  font-weight: 500;
}

.pulse-animation {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
  100% {
    opacity: 1;
  }
}

/* 工具提示样式 */
.balance-alert-icon [title] {
  cursor: help;
}
</style> 
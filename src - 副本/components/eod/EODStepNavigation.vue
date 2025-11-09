<template>
  <div class="d-flex justify-content-between align-items-center">
    <div>
      <button 
        v-if="showPreviousButton && currentStep <= 6"
        class="btn btn-outline-secondary me-2"
        @click="handlePreviousStep"
        :disabled="loading"
      >
        <font-awesome-icon :icon="['fas', 'arrow-left']" class="me-1" />
        {{ t('eod.navigation.previous_step') }}
      </button>
    </div>
    
    <div>
      <button 
        v-if="showCancelButton"
        class="btn btn-outline-danger"
        @click="handleCancelEOD"
        :disabled="loading"
      >
        <font-awesome-icon :icon="['fas', 'times']" class="me-1" />
        {{ currentStep >= 7 ? t('eod.navigation.smart_cancel') : t('eod.navigation.cancel_eod') }}
      </button>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import api from '@/services/api/index.js'

export default {
  name: 'EODStepNavigation',
  props: {
    eodId: {
      type: [Number, String],
      required: true
    },
    currentStep: {
      type: Number,
      default: 1
    },
    loading: {
      type: Boolean,
      default: false
    },
    showPreviousButton: {
      type: Boolean,
      default: true
    },
    showCancelButton: {
      type: Boolean,
      default: true
    }
  },
  emits: ['previous-step', 'cancel-eod', 'error', 'success'],
  setup(props, { emit }) {
    const { t } = useI18n()
    const showConfirmDialog = ref(false)
    const confirmReason = ref('')
    const actionType = ref('')
    
    const handlePreviousStep = async () => {
      // 前端验证：第7步后不允许回退（交款完成后）
      if (props.currentStep >= 7) {
        emit('error', t('eod.step_rollback_after_cashout_error'))
        return
      }
      
      // 前端验证：第1步不允许回退
      if (props.currentStep <= 1) {
        emit('error', t('eod.step_rollback_first_step_error'))
        return
      }
      
      // 计算目标步骤号
      const targetStep = props.currentStep - 1
      
      // 【调试】记录前端传递的参数
      console.log('🔍 前端回退调试信息:')
      console.log('  - 当前步骤:', props.currentStep)
      console.log('  - 目标步骤:', targetStep)
      console.log('  - EOD ID:', props.eodId)
      
      // 验证目标步骤号
      if (targetStep < 1 || targetStep >= props.currentStep) {
        emit('error', t('eod.step_rollback_invalid_target', { target: targetStep }))
        return
      }
      
      try {
        const response = await api.post(`/eod-step/${props.eodId}/rollback/${targetStep}`, {
          reason: t('eod.step_rollback_reason')
        })
        
        if (response.data.success) {
          // 【修复】后端现在直接返回翻译后的消息
          emit('success', response.data.message || t('eod.step_rollback_default'))
          emit('previous-step', response.data)
        } else {
          emit('error', response.data.message || t('eod.step_rollback_failed'))
        }
      } catch (error) {
        console.error('回退失败:', error)
        
        // 特殊处理令牌过期的情况
        if (error.isTokenExpired && error.isEODFlow) {
          emit('error', error.userMessage || t('eod.token_expired_eod_flow'))
        } else if (error.response?.status === 401) {
          emit('error', t('eod.token_expired'))
        } else {
          emit('error', error.response?.data?.message || error.message || t('eod.eod_network_error'))
        }
      }
    }
    
    const handleCancelEOD = async () => {
      try {
        const response = await api.post(`/eod-step/${props.eodId}/cancel-complete`, {
          reason: props.currentStep >= 7 ? t('eod.smart_cancel_reason') : t('eod.normal_cancel_reason')
        })
        
        if (response.data.success) {
          emit('success', t('eod.cancel_success'))
          emit('cancel-eod', response.data)
        } else {
          emit('error', response.data.message || t('eod.cancel_failed'))
        }
      } catch (error) {
        emit('error', error.response?.data?.message || t('eod.eod_network_error'))
      }
    }
    
    return {
      t,
      showConfirmDialog,
      confirmReason,
      actionType,
      handlePreviousStep,
      handleCancelEOD
    }
  }
}
</script>

<style scoped>
.btn {
  min-width: 80px;
}
</style>

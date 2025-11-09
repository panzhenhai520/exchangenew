<template>
  <div class="step-content">
    <div class="step-header mb-4">
      <h4>{{ $t('eod.step8.title') }}</h4>
      <p class="text-muted">{{ $t('eod.step8.description') }}</p>
    </div>

    <div v-if="!isCompleted">
      <div class="card">
        <div class="card-header">
          <h6 class="mb-0">{{ $t('eod.step8.completion_confirmation') }}</h6>
        </div>
        <div class="card-body">
          <div class="alert alert-info">
            <h6 class="alert-heading">
              <font-awesome-icon :icon="['fas', 'info-circle']" class="me-2" />
              {{ $t('eod.step8.about_to_complete') }}
            </h6>
            <p class="mb-2">{{ $t('eod.step8.confirm_following') }}</p>
            <ul class="mb-0">
              <li>{{ $t('eod.step8.all_steps_completed') }}</li>
              <li>{{ $t('eod.step8.reports_printed_verified') }}</li>
              <li>{{ $t('eod.step8.cash_out_completed') }}</li>
              <li>{{ $t('eod.step8.signatures_completed') }}</li>
            </ul>
          </div>

          <!-- 日结汇总信息 -->
          <div class="row mb-4">
            <div class="col-md-6">
              <div class="card bg-light">
                <div class="card-body">
                  <h6 class="card-title">
                    <font-awesome-icon :icon="['fas', 'calendar-alt']" class="me-2 text-primary" />
                    {{ $t('eod.step8.eod_info') }}
                  </h6>
                  <p class="mb-1"><strong>{{ $t('eod.step8.eod_date') }}:</strong> {{ eodDate }}</p>
                  <p class="mb-1"><strong>{{ $t('eod.step8.operator') }}:</strong> {{ operatorName }}</p>
                  <p class="mb-1"><strong>{{ $t('eod.step8.branch') }}:</strong> {{ branchName }}</p>
                  <p class="mb-0"><strong>{{ $t('eod.step8.start_time') }}:</strong> {{ formatDateTime(startTime) }}</p>
                </div>
              </div>
            </div>
            <div class="col-md-6">
              <div class="card bg-light">
                <div class="card-body">
                  <h6 class="card-title">
                    <font-awesome-icon :icon="['fas', 'check-circle']" class="me-2 text-success" />
                    {{ $t('eod.step8.completion_status') }}
                  </h6>
                  <p class="mb-1">
                    <span class="badge bg-success me-2">✓</span>
                    {{ $t('eod.step8.balance_verification_completed') }}
                  </p>
                  <p class="mb-1">
                    <span class="badge bg-success me-2">✓</span>
                    {{ $t('eod.step8.cash_out_completed_status') }}
                  </p>
                  <p class="mb-1">
                    <span class="badge bg-success me-2">✓</span>
                    {{ $t('eod.step8.report_generation_completed') }}
                  </p>
                  <p class="mb-0">
                    <span :class="isCompleted ? 'badge bg-success me-2' : 'badge bg-warning me-2'">
                      {{ isCompleted ? '✓' : '⏳' }}
                    </span>
                    {{ isCompleted ? $t('eod.step8.eod_completed') : $t('eod.step8.awaiting_final_confirmation') }}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <!-- 完成确认 -->
          <div class="card border-success">
            <div class="card-header bg-success text-white">
              <h6 class="mb-0">
                <font-awesome-icon :icon="['fas', 'clipboard-check']" class="me-2" />
                {{ $t('eod.step8.final_confirmation') }}
              </h6>
            </div>
            <div class="card-body">
              <div class="form-check mb-3">
                <input
                  class="form-check-input"
                  type="checkbox"
                  id="confirm-steps"
                  v-model="confirmSteps"
                />
                <label class="form-check-label" for="confirm-steps">
                  {{ $t('eod.step8.confirm_all_steps') }}
                </label>
              </div>
              
              <div class="form-check mb-3">
                <input
                  class="form-check-input"
                  type="checkbox"
                  id="confirm-reports"
                  v-model="confirmReports"
                />
                <label class="form-check-label" for="confirm-reports">
                  {{ $t('eod.step8.confirm_reports_printed') }}
                </label>
              </div>
              
              <div class="form-check mb-3">
                <input
                  class="form-check-input"
                  type="checkbox"
                  id="confirm-handover"
                  v-model="confirmHandover"
                />
                <label class="form-check-label" for="confirm-handover">
                  {{ $t('eod.step8.confirm_cash_handover') }}
                </label>
              </div>

              <div class="mb-3">
                <label for="completion-notes" class="form-label">{{ $t('eod.step8.completion_notes') }}</label>
                <textarea
                  id="completion-notes"
                  class="form-control"
                  rows="3"
                  v-model="completionNotes"
                  :placeholder="$t('eod.step8.completion_notes_placeholder')"
                ></textarea>
              </div>

              <div class="d-grid">
                <button 
                  class="btn btn-success btn-lg"
                  @click="completeEOD"
                  :disabled="!canComplete || loading || isProcessing"
                >
                  <span v-if="isProcessing">
                    <span class="spinner-border spinner-border-sm me-2" role="status"></span>
                    {{ $t('eod.step8.completing') }}
                  </span>
                  <span v-else>
                    <font-awesome-icon :icon="['fas', 'flag-checkered']" class="me-2" />
                    {{ $t('eod.step8.confirm_completion_button') }}
                  </span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

              <!-- EOD Completion Success Page -->
    <div v-else class="text-center py-5">
      <div class="mb-4">
        <font-awesome-icon :icon="['fas', 'check-circle']" size="4x" class="text-success" />
      </div>
      <h3 class="text-success mb-3">{{ $t('eod.step8.eod_completed_success') }}</h3>
      <p class="text-muted mb-4">{{ $t('eod.step8.eod_completed_message', { date: eodDate }) }}</p>
      
      <div class="card mx-auto" style="max-width: 500px;">
        <div class="card-body">
          <h6 class="card-title">{{ $t('eod.step8.completion_info') }}</h6>
          <div class="row text-start">
            <div class="col-6">
              <p class="mb-1"><strong>{{ $t('eod.step8.completion_time') }}:</strong></p>
              <p class="mb-1"><strong>{{ $t('eod.step8.duration') }}:</strong></p>
              <p class="mb-0"><strong>{{ $t('common.status') }}:</strong></p>
            </div>
            <div class="col-6">
              <p class="mb-1">{{ formatDateTime(completionTime) }}</p>
              <p class="mb-1">{{ formatDuration() }}</p>
              <p class="mb-0"><span class="badge bg-success">{{ $t('eod.step8.status_completed') }}</span></p>
            </div>
          </div>
        </div>
      </div>

      <div class="mt-4">
        <p class="text-muted">{{ $t('eod.step8.redirect_message') }}</p>
        <div class="progress" style="height: 4px;">
          <div 
            class="progress-bar bg-success" 
            role="progressbar" 
            :style="{ width: progressWidth + '%' }"
          ></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { eodAPI } from '../../../api/eod'
import { formatDateTime } from '@/utils/formatters'

export default {
  name: 'Step8Complete',
  emits: ['complete', 'error'],
  props: {
    eodId: {
      type: [Number, String],
      required: true
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  setup(props, { emit }) {
    const { t } = useI18n()
    
    // 响应式数据
    const isCompleted = ref(false)
    const isProcessing = ref(false)
    const confirmSteps = ref(false)
    const confirmReports = ref(false)
    const confirmHandover = ref(false)
    const completionNotes = ref('')
    const completionTime = ref(null)
    const progressWidth = ref(0)
    
    // 计算属性
    const canComplete = computed(() => {
      return confirmSteps.value && confirmReports.value && confirmHandover.value
    })
    
    const currentUser = computed(() => {
      try {
        return JSON.parse(localStorage.getItem('user') || '{}')
      } catch {
        return {}
      }
    })
    
    const eodDate = computed(() => {
      return new Date().toISOString().split('T')[0]
    })
    
    const operatorName = computed(() => {
      return currentUser.value.name || t('eod.step8.unknown_operator')
    })
    
    const branchName = computed(() => {
      return currentUser.value.branch_name || t('eod.step8.unknown_branch')
    })
    
    const startTime = computed(() => {
      // 这里应该从日结数据中获取开始时间
      return new Date()
    })
    
    // 检查日结是否已完成
    const checkEODStatus = async () => {
      try {
        const result = await eodAPI.getStatus(props.eodId)
        if (result.success && result.eod_status) {
          const eodStatus = result.eod_status
          // 如果日结状态为已完成，直接设置为完成状态
          if (eodStatus.status === 'completed') {
            isCompleted.value = true
            completionTime.value = new Date(eodStatus.completed_at || new Date())
            // 设置进度条为100%
            progressWidth.value = 100
            
            // 开始倒计时动画
            startCountdown()
            
            // 3秒后触发完成事件，跳转到仪表板
            setTimeout(() => {
              emit('complete', {
                completion_time: completionTime.value,
                notes: '日结已完成'
              })
            }, 3000)
          }
        }
      } catch (error) {
        console.error(t('eod.step8.check_status_failed'), error)
      }
    }
    
    // 方法
    const completeEOD = async () => {
      if (!canComplete.value) {
        emit('error', '请确认所有必要项目后再完成日结')
        return
      }
      
      try {
        isProcessing.value = true
        
        const result = await eodAPI.complete(props.eodId)
        
        if (result.success) {
          completionTime.value = new Date()
          isCompleted.value = true
          
          // 开始倒计时动画
          startCountdown()
          
          // 3秒后触发完成事件
          setTimeout(() => {
            emit('complete', {
              completion_time: completionTime.value,
              notes: completionNotes.value
            })
          }, 3000)
        } else {
          emit('error', result.message || t('eod.step8.complete_eod_failed'))
        }
      } catch (error) {
                  console.error(t('eod.step8.complete_eod_failed'), error)
        
        // 【会话自动恢复机制】当遇到会话过期错误时，自动尝试恢复
        const errorMessage = error.response?.data?.message || error.message || ''
        if (errorMessage.includes('会话锁定无效或已过期')) {
          console.log('检测到会话过期，尝试自动恢复...')
          try {
            // 尝试自动恢复会话
            const recoveryResult = await eodAPI.autoRecoverSession(props.eodId)
            if (recoveryResult.success) {
              console.log(t('eod.step8.session_recovery_success'))
              // 重新尝试完成日结
              const retryResult = await eodAPI.complete(props.eodId)
              if (retryResult.success) {
                completionTime.value = new Date()
                isCompleted.value = true
                startCountdown()
                setTimeout(() => {
                  emit('complete', {
                    completion_time: completionTime.value,
                    notes: completionNotes.value
                  })
                }, 3000)
                return
              }
            }
          } catch (recoveryError) {
            console.error(t('eod.step8.session_recovery_failed'), recoveryError)
          }
        }
        
        emit('error', errorMessage || t('eod.step8.complete_eod_failed'))
      } finally {
        isProcessing.value = false
      }
    }
    
    const startCountdown = () => {
      let progress = 0
      const interval = setInterval(() => {
        progress += 100 / 30 // 3秒内完成，每100ms更新一次
        progressWidth.value = Math.min(progress, 100)
        
        if (progress >= 100) {
          clearInterval(interval)
        }
      }, 100)
    }
    
    const formatDuration = () => {
      if (!completionTime.value) return t('eod.step8.unknown_duration')
      
      const duration = completionTime.value - startTime.value
      const minutes = Math.floor(duration / 60000)
      const seconds = Math.floor((duration % 60000) / 1000)
      
      return t('eod.step8.time_format_duration', { minutes, seconds })
    }
    
    // 生命周期
    onMounted(() => {
      checkEODStatus()
    })
    
    return {
      t,
      isCompleted,
      isProcessing,
      confirmSteps,
      confirmReports,
      confirmHandover,
      completionNotes,
      completionTime,
      progressWidth,
      canComplete,
      eodDate,
      operatorName,
      branchName,
      startTime,
      completeEOD,
      formatDateTime,
      formatDuration
    }
  }
}
</script>

<style scoped>
.step-content {
  padding: 1rem 0;
}

.step-header h4 {
  color: #495057;
  margin-bottom: 0.5rem;
}

.card.bg-light {
  border: 1px solid #e9ecef;
}

.card.border-success {
  border-color: #28a745 !important;
}

.form-check-label {
  font-weight: 500;
}

.progress {
  border-radius: 2px;
}

.badge {
  font-size: 0.75rem;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.text-center.py-5 {
  animation: fadeIn 0.5s ease-in-out;
}
</style> 
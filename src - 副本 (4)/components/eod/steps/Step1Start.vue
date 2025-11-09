<template>
  <div class="step-content">
    <div class="step-header mb-3">
      <h4>
        {{ t('eod.step1.title') }}
        <span v-if="timeRangeInfo" class="text-muted ms-2" style="font-size: 0.65em; font-weight: normal;">
          {{ timeRangeInfo.overall_start_time }} - {{ timeRangeInfo.overall_end_time }}
        </span>
      </h4>
      <p class="text-muted">{{ t('eod.step1.description') }}</p>
    </div>

    <div class="row equal-height-row">
      <div class="col-md-6">
        <div class="card h-100 shadow-sm">
          <div class="card-header bg-light">
            <h6 class="mb-0 text-primary">
              <font-awesome-icon :icon="['fas', 'calendar-alt']" class="me-2" />
              {{ t('eod.step1.settings') }}
            </h6>
          </div>
          <div class="card-body d-flex flex-column">
            <form @submit.prevent="startEOD">
              <div class="mb-3">
                <label for="eod-date" class="form-label">{{ t('eod.step1.eod_date') }}</label>
                <input
                  type="date"
                  id="eod-date"
                  class="form-control"
                  v-model="selectedDate"
                  :max="maxDate"
                  required
                  @change="calculateTimeRange"
                />
                <div class="form-text">{{ t('eod.step1.date_help') }}</div>
              </div>

              <div class="mb-3">
                <label for="branch-info" class="form-label">{{ t('eod.step1.current_branch') }}</label>
                <input
                  type="text"
                  id="branch-info"
                  class="form-control"
                  :value="branchInfo"
                  readonly
                />
              </div>

              <div class="mb-3">
                <label for="operator-info" class="form-label">{{ t('eod.step1.operator') }}</label>
                <input
                  type="text"
                  id="operator-info"
                  class="form-control"
                  :value="operatorInfo"
                  readonly
                />
              </div>

              <div class="d-grid mt-auto">
                <button 
                  type="submit" 
                  class="btn btn-primary"
                  :disabled="loading || isProcessing"
                >
                  <span v-if="isProcessing">
                    <span class="spinner-border spinner-border-sm me-2" role="status"></span>
                    {{ t('eod.step1.starting') }}
                  </span>
                  <span v-else>
                    <font-awesome-icon :icon="['fas', 'play']" class="me-2" />
                    {{ t('eod.step1.start_eod') }}
                  </span>
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>

      <div class="col-md-6">
        <EODHistoryList />
      </div>
    </div>



    <!-- 清理会话按钮 -->
    <div class="mt-4">
      <div class="card border-warning">
        <div class="card-header bg-warning bg-opacity-10">
          <h6 class="mb-0 text-warning">
            <font-awesome-icon :icon="['fas', 'tools']" class="me-2" />
            {{ t('eod.step1.session_management') }}
          </h6>
        </div>
        <div class="card-body">
          <p class="text-muted mb-2">
            {{ t('eod.step1.session_help') }}
          </p>
          <button 
            class="btn btn-warning btn-sm"
            @click="cleanupSession"
            :disabled="isCleaningSession"
          >
            <span v-if="isCleaningSession">
              <span class="spinner-border spinner-border-sm me-2" role="status"></span>
              {{ t('eod.step1.cleaning') }}
            </span>
            <span v-else>
              <font-awesome-icon :icon="['fas', 'broom']" class="me-1" />
              {{ t('eod.step1.cleanup_session') }}
            </span>
          </button>
        </div>
      </div>
    </div>

    <!-- 已存在的日结提示 -->
    <div v-if="existingEOD" class="alert alert-warning mt-4">
      <h6 class="alert-heading">
        <font-awesome-icon :icon="['fas', 'exclamation-triangle']" class="me-2" />
        {{ t('eod.step1.existing_eod_detected') }}
      </h6>
      <p class="mb-2">
        {{ t('eod.step1.existing_eod_message', { date: existingEOD.date, id: existingEOD.id }) }}
      </p>
      <div class="d-flex gap-2">
        <button 
          class="btn btn-outline-primary btn-sm"
          @click="continueExisting"
          :disabled="loading"
        >
          <font-awesome-icon :icon="['fas', 'play']" class="me-1" />
          {{ t('eod.step1.continue_existing') }}
        </button>
        <button 
          class="btn btn-outline-danger btn-sm"
          @click="cancelExisting"
          :disabled="loading"
        >
          <font-awesome-icon :icon="['fas', 'times']" class="me-1" />
          {{ t('eod.step1.cancel_existing') }}
        </button>
      </div>
    </div>

    <!-- 已完成的日结提示 -->
    <div v-if="completedEOD" class="alert alert-info mt-4">
      <h6 class="alert-heading">
        <font-awesome-icon :icon="['fas', 'info-circle']" class="me-2" />
        {{ t('eod.step1.completed_eod_detected') }}
      </h6>
      <p class="mb-2">
        {{ t('eod.step1.completed_eod_message', { date: completedEOD.date, id: completedEOD.eod_id }) }}
      </p>
      <div class="d-flex gap-2">
        <button 
          class="btn btn-outline-danger btn-sm"
          @click="cancelCompleted"
          :disabled="loading"
        >
          <font-awesome-icon :icon="['fas', 'undo']" class="me-1" />
          {{ t('eod.step1.cancel_completed') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { eodAPI } from '../../../api/eod'
import EODHistoryList from '../EODHistoryList.vue'

export default {
  name: 'Step1Start',
  components: {
    EODHistoryList
  },
  emits: ['next', 'error', 'success'],
  props: {
    loading: {
      type: Boolean,
      default: false
    }
  },
  setup(props, { emit }) {
    const { t } = useI18n()
    
    // 响应式数据
    const selectedDate = ref(new Date().toISOString().split('T')[0])
    const isProcessing = ref(false)
    const isCleaningSession = ref(false)
    const existingEOD = ref(null)
    const completedEOD = ref(null)
    const timeRangeInfo = ref(null)
    const loadingTimeRange = ref(false)
    
    // 计算属性
    const maxDate = computed(() => {
      return new Date().toISOString().split('T')[0]
    })
    
    const currentUser = computed(() => {
      try {
        return JSON.parse(localStorage.getItem('user') || '{}')
      } catch {
        return {}
      }
    })
    
    const branchInfo = computed(() => {
      const user = currentUser.value
      return user.branch_name ? `${user.branch_name} (${user.branch_code || ''})` : t('eod.step1.unknown_branch')
    })
    
    const operatorInfo = computed(() => {
      const user = currentUser.value
      return user.name ? `${user.name} (${user.login_code || ''})` : t('eod.step1.unknown_operator')
    })
    
    // 方法
    const calculateTimeRange = async () => {
      if (!selectedDate.value) return
      
      try {
        loadingTimeRange.value = true
        
        // 获取网点的上一次日结信息
        const user = currentUser.value
        if (!user.branch_id) return
        
        const result = await eodAPI.getLatestEOD(user.branch_id, selectedDate.value)
        
        let startTime, endTime
        
        if (result.success && result.latest_eod) {
          // 有上一次日结，从上次日结完成时间开始
          startTime = new Date(result.latest_eod.completed_at)
          endTime = new Date() // 当前时间
        } else {
          // 【修复】没有上一次日结，检查是否有第一笔交易时间信息
          if (result.first_transaction && result.first_transaction.suggested_start_time) {
            // 使用第一笔交易时间作为开始时间
            startTime = new Date(result.first_transaction.suggested_start_time)
            endTime = new Date() // 当前时间
          } else {
            // 如果没有任何交易记录，才使用选择日期的0点开始
            startTime = new Date(selectedDate.value + 'T00:00:00')
            endTime = new Date() // 当前时间
          }
        }
        
        timeRangeInfo.value = {
          overall_start_time: formatDateTime(startTime),
          overall_end_time: formatDateTime(endTime),
          has_previous_eod: result.success && result.latest_eod
        }
      } catch (error) {
        console.error('计算时间范围失败:', error)
        // 【修复】使用更合理的备用方案
        // 如果API调用失败，尝试使用选择日期前一天的数据作为备用
        const selectedDateObj = new Date(selectedDate.value)
        const prevDay = new Date(selectedDateObj)
        prevDay.setDate(prevDay.getDate() - 1)
        
        // 使用前一天的最后时刻作为可能的开始时间
        const startTime = new Date(prevDay.toISOString().split('T')[0] + 'T23:59:59')
        const endTime = new Date()
        
        timeRangeInfo.value = {
          overall_start_time: formatDateTime(startTime),
          overall_end_time: formatDateTime(endTime),
          has_previous_eod: false
        }
      } finally {
        loadingTimeRange.value = false
      }
    }
    
    const formatDateTime = (date) => {
      if (!date) return '未知时间'
      
      const d = typeof date === 'string' ? new Date(date) : date
      const year = d.getFullYear()
      const month = String(d.getMonth() + 1).padStart(2, '0')
      const day = String(d.getDate()).padStart(2, '0')
      const hours = String(d.getHours()).padStart(2, '0')
      const minutes = String(d.getMinutes()).padStart(2, '0')
      const seconds = String(d.getSeconds()).padStart(2, '0')
      
      return `${year}/${month}/${day} ${hours}:${minutes}:${seconds}`
    }
    
    const startEOD = async () => {
      try {
        isProcessing.value = true
        
        const result = await eodAPI.start(selectedDate.value)
        
        if (result.success) {
          emit('next', {
            eod_id: result.eod_id,
            date: selectedDate.value,
            status: result.status,
            is_locked: true,
            step: 2,  // 开始日结成功后，应该进入第2步
            from_api_call: true  // 添加标志，表示这是API调用完成
          })
        } else {
          // 检查是否是已完成的日结需要取消
          if (result.can_cancel && result.eod_id) {
            completedEOD.value = {
              eod_id: result.eod_id,
              date: selectedDate.value
            }
          } else {
            emit('error', result.message || '开始日结失败')
          }
        }
      } catch (error) {
        console.error('开始日结失败:', error)
        emit('error', error.response?.data?.message || error.message || '开始日结失败')
      } finally {
        isProcessing.value = false
      }
    }
    // 清理会话锁定
    const cleanupSession = async () => {
      if (!confirm(t('eod.step1.confirm_cleanup_session'))) return
      
      try {
        isCleaningSession.value = true
        
        const result = await eodAPI.cleanupSession()
        
        if (result.success) {
          const message = result.message || '清理完成'
          emit('success', message)
          
          setTimeout(() => {
            window.location.reload()
          }, 2000)
        } else {
          emit('error', result.message || '清理会话锁定失败')
        }
      } catch (error) {
        console.error('清理会话锁定失败:', error)
        emit('error', error.response?.data?.message || error.message || '清理会话锁定失败')
      } finally {
        isCleaningSession.value = false
      }
    }
    
    const continueExisting = async () => {
      try {
        isProcessing.value = true
        
        // 先调用继续现有流程API，设置会话ID
        const result = await eodAPI.continueEOD(existingEOD.value.id)
        
        if (result.success) {
          // 继续API调用成功后，重新获取EOD状态信息
          const statusResult = await eodAPI.getStatus(existingEOD.value.id)
          
          if (statusResult.success) {
            const eodStatus = statusResult.eod_status
            
            // 根据EOD状态确定应该跳转到哪一步
            let nextStep = 1
            if (eodStatus.step && eodStatus.step > 1) {
              // 如果已经有步骤信息，使用当前步骤
              nextStep = eodStatus.step
            } else if (eodStatus.status) {
              // 根据状态判断应该跳转到的步骤
              switch (eodStatus.status) {
                case 'started':
                case 'balance_extracted':
                  nextStep = 2
                  break
                case 'balance_calculated':
                  nextStep = 3
                  break
                case 'balance_verified':
                  // 如果余额已核对，检查是否有交款记录
                  if (eodStatus.cash_out_completed) {
                    nextStep = 7  // 跳转到报表步骤
                  } else {
                    nextStep = 4  // 跳转到余额核对步骤
                  }
                  break
                case 'verification_handled':
                  nextStep = 5
                  break
                case 'cash_out_completed':
                  nextStep = 7  // 跳转到报表步骤
                  break
                case 'report_generated':
                  nextStep = 7
                  break
                case 'completed':
                  nextStep = 8
                  break
                default:
                  nextStep = 2  // 默认跳转到第二步
              }
            } else {
              // 如果没有明确的状态，默认跳转到第二步
              nextStep = 2
            }
            
            console.log(`继续现有流程：EOD ID=${eodStatus.id}, 状态=${eodStatus.status}, 跳转到步骤=${nextStep}`)
            
            emit('next', {
              eod_id: eodStatus.id,
              date: eodStatus.date,
              status: eodStatus.status,
              is_locked: eodStatus.is_locked,
              step: nextStep,
              step_status: eodStatus.step_status || 'processing',
              from_api_call: false  // 标记为继续现有流程
            })
          } else {
            emit('error', statusResult.message || '获取日结状态失败，请刷新页面重试')
          }
        } else {
          emit('error', result.message || '继续现有流程失败，请刷新页面重试')
        }
      } catch (error) {
        console.error('继续现有流程失败:', error)
        const errorMessage = error.response?.data?.message || error.message || '继续现有流程失败，请刷新页面重试'
        emit('error', errorMessage)
      } finally {
        isProcessing.value = false
      }
    }
    
    const cancelExisting = async () => {
      if (!confirm(t('eod.step1.confirm_cancel_existing'))) return
      
      try {
        isProcessing.value = true
        await eodAPI.cancel(existingEOD.value.id, '用户取消现有流程')
        existingEOD.value = null
      } catch (error) {
        emit('error', '取消现有日结失败: ' + error.message)
      } finally {
        isProcessing.value = false
      }
    }
    
    const checkExistingEOD = async () => {
      try {
        const lockStatus = await eodAPI.checkBusinessLock()
        if (lockStatus.is_locked && lockStatus.eod_id) {
          const eodStatus = await eodAPI.getStatus(lockStatus.eod_id)
          if (eodStatus.success) {
            existingEOD.value = eodStatus.eod_status
          }
        }
      } catch (error) {
        console.error('检查现有日结失败:', error)
      }
    }
    
    const checkCompletedEOD = async (date) => {
      try {
        const result = await eodAPI.checkCompleted(date)
        if (result.success && result.has_completed) {
          // 显示信息提示，但不阻止操作
          console.log(`检测到 ${date} 已有完成的日结 (ID: ${result.eod_id})，但允许开始新的日结`)
          completedEOD.value = null // 不显示阻止界面
        } else {
          completedEOD.value = null
        }
      } catch (error) {
        console.error('检查已完成日结失败:', error)
        completedEOD.value = null
      }
    }
    
    const cancelCompleted = async () => {
      if (!confirm(t('eod.step1.confirm_cancel_completed'))) return
      
      try {
        isProcessing.value = true
        await eodAPI.cancel(completedEOD.value.eod_id, '用户取消已完成的日结')
        completedEOD.value = null
        // 取消成功后，可以重新开始日结
        alert('已完成的日结记录已删除，现在可以重新进行日结。')
      } catch (error) {
        emit('error', '取消已完成的日结失败: ' + error.message)
      } finally {
        isProcessing.value = false
      }
    }
    
    // 生命周期
    onMounted(() => {
      checkExistingEOD()
      checkCompletedEOD(selectedDate.value)
      calculateTimeRange()
    })
    
    // 监听日期变化
    watch(selectedDate, (newDate) => {
      checkCompletedEOD(newDate)
      calculateTimeRange()
    })
    
    return {
      t,
      selectedDate,
      isProcessing,
      isCleaningSession,
      existingEOD,
      completedEOD,
      timeRangeInfo,
      loadingTimeRange,
      maxDate,
      branchInfo,
      operatorInfo,
      calculateTimeRange,
      cleanupSession,
      startEOD,
      continueExisting,
      cancelExisting,
      cancelCompleted
    }
  }
}
</script>

<style scoped>
.step-content {
  padding: 0.5rem 0;
}

.step-header h4 {
  color: #495057;
  margin-bottom: 0.25rem;
}

.step-header p {
  margin-bottom: 0;
}

.card {
  border: 1px solid #e9ecef;
  box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
}

.card-body {
  padding: 1rem;
}

.alert ul, .alert ol {
  padding-left: 1.2rem;
}

.alert li {
  margin-bottom: 0.25rem;
}

.form-label {
  margin-bottom: 0.25rem;
  font-weight: 500;
}

.mb-3 {
  margin-bottom: 0.75rem !important;
}

/* 紧凑型文字样式 */
.compact-alert {
  padding: 0.75rem;
}

.compact-heading {
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
}

.compact-text {
  font-size: 0.8rem;
  line-height: 1.4;
}

.compact-text li {
  margin-bottom: 0.15rem;
}

/* 等高卡片布局 */
.equal-height-row {
  display: flex;
  flex-wrap: wrap;
}

.equal-height-row > [class*='col-'] {
  display: flex;
  flex-direction: column;
}

/* 表单优化 */
.form-control {
  border-radius: 0.25rem;
  border: 1px solid #d1d3e2;
  transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
}

.form-control:focus {
  border-color: #bac8f3;
  box-shadow: 0 0 0 0.2rem rgba(78, 115, 223, 0.25);
}

.btn {
  border-radius: 0.25rem;
  font-weight: 500;
  transition: all 0.15s ease-in-out;
}

.btn-primary {
  background: linear-gradient(135deg, #4e73df 0%, #224abe 100%);
  border: none;
}

.btn-primary:hover {
  background: linear-gradient(135deg, #224abe 0%, #1e3a8a 100%);
  transform: translateY(-1px);
}

/* 增强紧凑样式 */
.compact-alert {
  background: transparent;
  border: none;
  border-radius: 0.25rem;
}

.compact-heading {
  color: #495057;
  font-weight: 600;
}
</style> 
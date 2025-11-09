<!-- eslint-disable vue/no-ref-as-operand -->
<!-- eslint-disable no-unused-vars -->
<!-- eslint-disable no-undef -->
<template>
  <div class="container-fluid py-4">
    <div class="row">
      <div class="col-12">
        <div class="d-flex justify-content-between align-items-center mb-4">
          <h2 class="page-title-bold">
            <font-awesome-icon :icon="['fas', 'calendar-check']" class="me-2" />
            {{ $t('eod.title') }}
          </h2>
        </div>
        
        <!-- 错误提示 - 优先显示 -->
        <div v-if="error && !error.includes('特性开关') && !error.includes('无权限进行日结操作')" class="alert alert-danger mb-4">
          <font-awesome-icon :icon="['fas', 'exclamation-circle']" class="me-2" />
          {{ error }}
          <button class="btn btn-outline-danger btn-sm ms-3" @click="clearError">
            <font-awesome-icon :icon="['fas', 'times']" class="me-1" />
            {{ $t('common.close') }}
          </button>
        </div>

        <!-- 成功提示 - 只在没有错误时显示 -->
        <div v-if="successMessage && !successMessage.includes('特性开关') && !error" class="alert alert-success mb-4">
          <div class="d-flex align-items-center justify-content-between">
            <div>
              <font-awesome-icon :icon="['fas', 'check-circle']" class="me-2" />
              {{ successMessage }}
            </div>
            <!-- 继续现有日结按钮 -->
            <div v-if="successMessage.includes('继续现有') && eodData.id" class="ms-3">
              <button 
                class="btn btn-success btn-sm"
                @click="continueExistingEOD"
                :disabled="loading"
              >
                <font-awesome-icon :icon="['fas', 'play']" class="me-1" />
                {{ $t('eod.step1.continue_existing') }}
              </button>
            </div>
          </div>
        </div>

        <!-- 特殊处理：当有权限错误时，显示继续按钮 -->
        <div v-if="error && error.includes('无权限进行日结操作')" class="alert alert-warning mb-4">
          <div class="d-flex align-items-center justify-content-between">
            <div>
              <font-awesome-icon :icon="['fas', 'exclamation-triangle']" class="me-2" />
              {{ error }}
            </div>
            <!-- 继续现有日结按钮 -->
            <div class="ms-3">
              <button 
                class="btn btn-warning btn-sm"
                @click="continueExistingEOD"
                :disabled="loading"
              >
                <font-awesome-icon :icon="['fas', 'play']" class="me-1" />
                {{ $t('eod.step1.continue_existing') }}
              </button>
            </div>
          </div>
        </div>



        <div class="row g-4">
          <!-- 左侧：步骤指示器 -->
          <div class="col-md-3">
            <div class="card shadow-sm">
              <div class="card-header bg-light">
                <h6 class="mb-0 text-primary">
                  <font-awesome-icon :icon="['fas', 'list-ol']" class="me-2" />
                  {{ $t('eod.steps_navigation') }}
                </h6>
              </div>
              <div class="card-body p-0">
                <div class="list-group list-group-flush">
                  <div 
                    v-for="(step, index) in steps" 
                    :key="index"
                    class="list-group-item d-flex align-items-center step-item-compact"
                    :class="{
                      'active': currentStep === index + 1,
                      'list-group-item-success': step.status === 'completed',
                      'list-group-item-danger': step.status === 'failed',
                      'list-group-item-warning': step.status === 'processing'
                    }"
                  >
                    <div class="step-number me-2">
                      <span v-if="step.status === 'completed'" class="badge bg-success rounded-circle step-badge-sm">
                        <font-awesome-icon :icon="['fas', 'check']" />
                      </span>
                      <span v-else-if="step.status === 'failed'" class="badge bg-danger rounded-circle step-badge-sm">
                        <font-awesome-icon :icon="['fas', 'times']" />
                      </span>
                      <span v-else-if="step.status === 'processing'" class="badge bg-warning rounded-circle step-badge-sm">
                        <font-awesome-icon :icon="['fas', 'spinner']" spin />
                      </span>
                      <span v-else class="badge bg-secondary rounded-circle step-badge-sm">{{ index + 1 }}</span>
                    </div>
                    <div class="step-info">
                      <div class="step-title-sm">{{ step.title }}</div>
                      <small class="text-muted step-desc-sm">{{ step.description }}</small>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 日结信息卡片 -->
            <div v-if="eodData.id" class="card mt-3 shadow-sm">
              <div class="card-header bg-light">
                <h6 class="mb-0 card-title-sm text-success">
                  <font-awesome-icon :icon="['fas', 'info-circle']" class="me-2" />
                  {{ $t('eod.eod_info') }}
                </h6>
              </div>
              <div class="card-body">
                <p class="mb-1 info-text-sm"><strong>{{ $t('eod.eod_id') }}:</strong> {{ eodData.id }}</p>
                <p class="mb-1 info-text-sm"><strong>{{ $t('eod.date') }}:</strong> {{ eodData.date }}</p>
                <p class="mb-1 info-text-sm"><strong>{{ $t('eod.eod_status') }}:</strong> 
                  <span :class="getStatusClass(eodData.status)">{{ getStatusText(eodData.status) }}</span>
                </p>
                <p class="mb-0 info-text-sm"><strong>{{ $t('eod.lock_status') }}:</strong> 
                  <span :class="eodData.is_locked ? 'text-danger' : 'text-success'">
                    {{ eodData.is_locked ? $t('common.locked') : $t('common.unlocked') }}
                  </span>
                </p>
              </div>
            </div>

            <!-- 特性开关控制面板 - 已隐藏 -->
            <!-- <div class="card mt-3 shadow-sm">
              <div class="card-header bg-light d-flex justify-content-between align-items-center">
                <h6 class="mb-0 card-title-sm text-secondary">
                  <font-awesome-icon :icon="['fas', 'cog']" class="me-2" />
                  {{ $t('eod.feature_flags') }}
                </h6>
                <button 
                  class="btn btn-sm btn-outline-secondary"
                  @click="toggleFeaturePanel"
                  :title="showFeaturePanel ? $t('common.collapse') : $t('common.expand')"
                >
                  <font-awesome-icon :icon="['fas', showFeaturePanel ? 'chevron-up' : 'chevron-down']" />
                </button>
              </div>
              <div v-if="showFeaturePanel" class="card-body">
                <div v-if="error && error.includes('特性开关')" class="alert alert-danger alert-sm mb-3">
                  <font-awesome-icon :icon="['fas', 'exclamation-triangle']" class="me-2" />
                  {{ error }}
                  <button class="btn btn-sm btn-outline-danger ms-2" @click="clearError">
                    <font-awesome-icon :icon="['fas', 'times']" />
                  </button>
                </div>
                
                <div v-if="successMessage && successMessage.includes('特性开关')" class="alert alert-success alert-sm mb-3">
                  <font-awesome-icon :icon="['fas', 'check-circle']" class="me-2" />
                  {{ successMessage }}
                </div>
                
                <div v-if="featureFlags.length === 0 && !loadingFeatures" class="text-muted text-center py-2">
                  <small>{{ $t('eod.no_feature_flags') }}</small>
                </div>
                <div v-else-if="loadingFeatures" class="text-center py-2">
                  <font-awesome-icon :icon="['fas', 'spinner']" spin class="me-2" />
                  <small>{{ $t('common.loading') }}</small>
                </div>
                <div v-else>
                  <div v-for="flag in featureFlags" :key="flag.key" class="mb-3">
                    <div class="form-check form-switch">
                      <input 
                        class="form-check-input" 
                        type="checkbox" 
                        :id="flag.key"
                        :checked="flag.enabled"
                        @change="toggleFeatureFlag(flag.key, $event.target.checked)"
                        :disabled="updatingFeature === flag.key"
                      />
                      <label class="form-check-label" :for="flag.key">
                        <div class="d-flex flex-column">
                          <small class="fw-bold">{{ flag.description }}</small>
                          <small class="text-muted">{{ flag.key }}</small>
                        </div>
                      </label>
                      <div v-if="updatingFeature === flag.key" class="spinner-border spinner-border-sm ms-2" role="status">
                        <span class="visually-hidden">{{ $t('common.updating') }}</span>
                      </div>
                    </div>
                  </div>
                  <div class="text-center mt-3">
                    <button 
                      class="btn btn-sm btn-outline-primary"
                      @click="loadFeatureFlags"
                      :disabled="loadingFeatures"
                    >
                      <font-awesome-icon :icon="['fas', 'sync-alt']" class="me-1" />
                      {{ $t('common.refresh') }}
                    </button>
                  </div>
                </div>
              </div>
            </div> -->
          </div>

          <!-- 中间：步骤内容 -->
          <div class="col-md-9">
            <div class="card shadow-sm">
              <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
                <h5 class="mb-0">
                  <font-awesome-icon :icon="['fas', 'play-circle']" class="me-2" />
                  {{ getStepTitle(currentStep - 1) }}
                </h5>
                <div>
                  <span class="badge bg-light text-primary">{{ $t('eod.step_progress', { current: currentStep, total: 8 }) }}</span>
                </div>
              </div>
              <div class="card-body">
                <!-- 步骤1: 开始日结 -->
                <div v-if="currentStep === 1">
                  <Step1Start 
                    @next="handleStepComplete"
                    @error="handleError"
                    @success="handleStepSuccess"
                    :loading="loading"
                  />
                </div>

                <!-- 步骤2: 提取余额 -->
                <div v-else-if="currentStep === 2">
                  <Step2Balance 
                    v-if="eodData.id"
                    :eod-id="eodData.id"
                    @next="handleStepComplete"
                    @error="handleError"
                    :loading="loading"
                  />
                  <div v-else class="text-center py-4">
                    <div class="spinner-border text-primary" role="status">
                      <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2 text-muted">正在初始化日结数据...</p>
                  </div>
                </div>

                <!-- 步骤3: 计算理论余额 -->
                <div v-else-if="currentStep === 3">
                  <Step3Calculate 
                    v-if="eodData.id"
                    :eod-id="eodData.id"
                    @next="handleStepComplete"
                    @error="handleError"
                    :loading="loading"
                  />
                  <div v-else class="text-center py-4">
                    <div class="spinner-border text-primary" role="status">
                      <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2 text-muted">正在初始化日结数据...</p>
                  </div>
                </div>

                <!-- 步骤4: 核对余额 -->
                <div v-else-if="currentStep === 4">
                  <Step4Verify 
                    v-if="eodData.id"
                    :eod-id="eodData.id"
                    @next="handleStepComplete"
                    @error="handleError"
                    :loading="loading"
                  />
                  <div v-else class="text-center py-4">
                    <div class="spinner-border text-primary" role="status">
                      <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2 text-muted">正在初始化日结数据...</p>
                  </div>
                </div>

                <!-- 步骤5: 处理核对结果 -->
                <div v-else-if="currentStep === 5">
                  <Step5Result 
                    v-if="eodData.id"
                    :eod-id="eodData.id"
                    :eod-status="eodData"
                    :verification-results="verificationResults"
                    :auto-generate-income-stats="autoGenerateIncomeStats"
                    @next="handleStepComplete"
                    @cancel="handleCancel"
                    @error="handleError"
                    @session-recovery-needed="handleSessionRecovery"
                    :loading="loading"
                  />
                  <div v-else class="text-center py-4">
                    <div class="spinner-border text-primary" role="status">
                      <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2 text-muted">正在初始化日结数据...</p>
                  </div>
                </div>

                <!-- 步骤6: 完成交款 -->
                <div v-else-if="currentStep === 6">
                  <Step6CashOut 
                    v-if="eodData.id"
                    :eod-id="eodData.id"
                    @next="handleStepComplete"
                    @error="handleError"
                    :loading="loading"
                  />
                  <div v-else class="text-center py-4">
                    <div class="spinner-border text-primary" role="status">
                      <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2 text-muted">正在初始化日结数据...</p>
                  </div>
                </div>

                <!-- 步骤7: 生成报表 -->
                <div v-else-if="currentStep === 7">
                  <Step7Report 
                    v-if="eodData.id"
                    :eod-id="eodData.id"
                    @next="handleStepComplete"
                    @error="handleError"
                    @success="handleStepSuccess"
                    :loading="loading"
                  />
                  <div v-else class="text-center py-4">
                    <div class="spinner-border text-primary" role="status">
                      <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2 text-muted">正在初始化日结数据...</p>
                  </div>
                </div>

                <!-- 步骤8: 完成日结 -->
                <div v-else-if="currentStep === 8">
                  <Step8Complete 
                    v-if="eodData.id"
                    :eod-id="eodData.id"
                    @complete="handleComplete"
                    @error="handleError"
                    :loading="loading"
                  />
                </div>


              </div>

              <!-- 步骤导航组件 -->
              <div v-if="!isEODCompleted && eodData.id" class="card-footer">
                <!-- 导航操作提示区域 -->
                <div v-if="navigationError || navigationSuccess" class="mb-3">
                  <!-- 导航错误提示 -->
                  <div v-if="navigationError" class="alert alert-danger d-flex align-items-center">
                    <font-awesome-icon :icon="['fas', 'exclamation-circle']" class="me-2" />
                    {{ navigationError }}
                    <button type="button" class="btn-close ms-auto" @click="clearNavigationError"></button>
                  </div>
                  
                  <!-- 导航成功提示 -->
                  <div v-if="navigationSuccess" class="alert alert-success d-flex align-items-center">
                    <font-awesome-icon :icon="['fas', 'check-circle']" class="me-2" />
                    {{ navigationSuccess }}
                    <button type="button" class="btn-close ms-auto" @click="clearNavigationSuccess"></button>
                  </div>
                </div>
                
                <EODStepNavigation
                  :eod-id="eodData.id"
                  :current-step="currentStep"
                  :loading="loading"
                  :show-previous-button="currentStep > 1 && currentStep <= 8"
                  :show-cancel-button="eodData.status === 'processing'"
                  @previous-step="handlePreviousStep"
                  @cancel-eod="handleCancelFromNavigation"
                  @error="handleNavigationError"
                  @success="handleNavigationSuccess"
                />
              </div>
            </div>
          </div>


        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
// import axios from 'axios'  // 已移除，使用统一的api服务
import api from '../services/api'
import Step1Start from '../components/eod/steps/Step1Start.vue'
import Step2Balance from '../components/eod/steps/Step2Balance.vue'
import Step3Calculate from '../components/eod/steps/Step3Calculate.vue'
import Step4Verify from '../components/eod/steps/Step4Verify.vue'
import Step5Result from '../components/eod/steps/Step5Result.vue'
import Step6CashOut from '../components/eod/steps/Step6CashOut.vue'
import Step7Report from '../components/eod/steps/Step7Report.vue'
import Step8Complete from '../components/eod/steps/Step8Complete.vue'
import EODStepNavigation from '../components/eod/EODStepNavigation.vue'
import { eodAPI } from '../api/eod'
import { translateErrorMessage } from '../utils/errorTranslator'

export default {
  name: 'EndOfDayView',
  components: {
    Step1Start,
    Step2Balance,
    Step3Calculate,
    Step4Verify,
    Step5Result,
    Step6CashOut,
    Step7Report,
    Step8Complete,
    EODStepNavigation
  },
  setup() {
    const router = useRouter()
    const { t } = useI18n()
    
    // 响应式数据
    const currentStep = ref(1)
    const loading = ref(false)
    const error = ref('')
    const successMessage = ref('')
    const navigationError = ref('')
    const navigationSuccess = ref('')
    const verificationResults = ref([])
    const isEODCompleted = ref(false)
    const todayEODHistory = ref([])
    const autoGenerateIncomeStats = ref(false)
    
    // 特性开关相关数据
    const showFeaturePanel = ref(false)
    const featureFlags = ref([])
    const loadingFeatures = ref(false)
    const updatingFeature = ref('')
    
    // 日结数据
    const eodData = reactive({
      id: null,
      date: '',
      status: '',
      is_locked: false,
      step: 1,
      step_status: ''
    })
    
    // 步骤定义 - 使用函数获取多语言标题和描述
    const steps = reactive([
      { get title() { return getStepTitle(0) }, get description() { return getStepDescription(0) }, status: 'pending' },
      { get title() { return getStepTitle(1) }, get description() { return getStepDescription(1) }, status: 'pending' },
      { get title() { return getStepTitle(2) }, get description() { return getStepDescription(2) }, status: 'pending' },
      { get title() { return getStepTitle(3) }, get description() { return getStepDescription(3) }, status: 'pending' },
      { get title() { return getStepTitle(4) }, get description() { return getStepDescription(4) }, status: 'pending' },
      { get title() { return getStepTitle(5) }, get description() { return getStepDescription(5) }, status: 'pending' },
      { get title() { return getStepTitle(6) }, get description() { return getStepDescription(6) }, status: 'pending' },
      { get title() { return getStepTitle(7) }, get description() { return getStepDescription(7) }, status: 'pending' }
    ])
    
    // 计算属性
    const currentUser = computed(() => {
      try {
        return JSON.parse(localStorage.getItem('user') || '{}')
      } catch {
        return {}
      }
    })
    
    // 方法
    const clearError = () => {
      error.value = ''
    }
    
    const handleError = (errorMsg) => {
      // 翻译错误消息
      const translatedError = translateErrorMessage(errorMsg, t)
      error.value = translatedError
      steps[currentStep.value - 1].status = 'failed'
    }
    
    const handleStepSuccess = (message) => {
      successMessage.value = message
      // 清除错误消息
      error.value = ''
    }
    
    const handleNavigationError = (errorMsg) => {
      // 翻译错误消息
      const translatedError = translateErrorMessage(errorMsg, t)
      navigationError.value = translatedError
      // 自动清除导航错误消息（5秒后）
      setTimeout(() => {
        navigationError.value = ''
      }, 5000)
    }
    
    const handleNavigationSuccess = (message) => {
      navigationSuccess.value = message
      // 自动清除导航成功消息（3秒后）
      setTimeout(() => {
        navigationSuccess.value = ''
      }, 3000)
    }
    
    const clearNavigationError = () => {
      navigationError.value = ''
    }
    
    const clearNavigationSuccess = () => {
      navigationSuccess.value = ''
    }
    
    const handleStepComplete = async (data) => {
      // 更新日结数据
      if (data) {
        if (data.eod_id) eodData.id = data.eod_id
        if (data.verification_results) verificationResults.value = data.verification_results
        
        // 处理自动生成收入统计的标志
        if (data.auto_generate_income_stats !== undefined) {
          autoGenerateIncomeStats.value = data.auto_generate_income_stats
        }
        
        Object.assign(eodData, data)
      }
      
      // 检查是否是"继续现有流程"的情况
      const isContinueExisting = data && data.step && !data.from_api_call
      
      // 如果是API调用完成，直接跳转到指定步骤
      if (data && data.from_api_call && data.step) {
        currentStep.value = data.step
        
        // 更新步骤状态：之前的步骤标记为完成
        for (let i = 0; i < data.step - 1; i++) {
          steps[i].status = 'completed'
        }
        
        // 当前步骤标记为处理中
        if (data.step <= steps.length) {
          steps[data.step - 1].status = 'processing'
        }
        
        // 【修复】强制继续时显示特殊消息
        if (data.forced_continue) {
          successMessage.value = t('eod.step_messages.force_continued_message')
        } else {
          successMessage.value = t('eod.step_messages.step_completed_enter_next', { 
            prevStep: data.step - 1, 
            nextStep: data.step 
          })
        }
        
        // 【修复】强制继续时不重新获取状态，避免步骤号被覆盖
        return
      }
      
      if (isContinueExisting) {
        // 继续现有流程：检查当前步骤状态，决定进入哪一步
        let targetStep = data.step
        
        // 如果当前步骤已完成，进入下一步
        if (data.step_status === 'completed' && data.step < 8) {
          targetStep = data.step + 1
        }
        
        currentStep.value = targetStep
        
        // 更新步骤状态
        for (let i = 0; i < currentStep.value - 1; i++) {
          steps[i].status = 'completed'
        }
        
        // 设置当前步骤状态
        if (data.step_status === 'completed' && targetStep > data.step) {
          // 如果进入了下一步，当前步骤为processing
          steps[currentStep.value - 1].status = 'processing'
          successMessage.value = `已继续现有日结流程，当前步骤: ${currentStep.value}`
        } else {
          // 如果当前步骤未完成，保持原状态
          steps[currentStep.value - 1].status = data.step_status === 'completed' ? 'completed' : 'processing'
          successMessage.value = `已继续现有日结流程，当前步骤: ${currentStep.value}`
        }
        
        // 强制重新渲染组件
        nextTick(() => {
          // 触发响应式更新
          currentStep.value = targetStep
          
          // 清除错误消息
          error.value = ''
        })
      } else {
        // 正常步骤完成：先标记当前步骤完成，然后同步状态
        steps[currentStep.value - 1].status = 'completed'
        
        // 【修复】强制继续时不重新获取状态，避免步骤号被覆盖
        if (data.forced_continue) {
          // 强制继续时保持当前步骤号，不重新获取状态
          successMessage.value = t('eod.step_messages.force_continued_message')
        } else {
          // 对于API调用完成的情况，重新获取后端真实状态
          try {
            if (eodData.id) {
              const result = await eodAPI.getStatus(eodData.id)
              if (result.success) {
                const realStatus = result.eod_status
                currentStep.value = realStatus.step || currentStep.value
                
                // 更新日结数据为后端真实状态
                Object.assign(eodData, realStatus)
                
                // 更新步骤状态
                for (let i = 0; i < currentStep.value - 1; i++) {
                  steps[i].status = 'completed'
                }
                if (realStatus.step_status === 'processing') {
                  steps[currentStep.value - 1].status = 'processing'
                } else if (realStatus.step_status === 'completed') {
                  steps[currentStep.value - 1].status = 'completed'
                }
              }
            }
          } catch (error) {
            console.error('获取EOD状态失败:', error)
            // 如果获取状态失败，使用原有逻辑（递增步骤）
            if (currentStep.value < 8) {
              currentStep.value++
            }
          }
          
          successMessage.value = t('eod.step_messages.eod_completed')
        }
      }
    }
    
    const handleCancel = () => {
      // 重置到第一步
      currentStep.value = 1
      eodData.id = null
      eodData.status = ''
      eodData.is_locked = false
      
      // 清理日结会话ID
      if (api.clearEODSessionId) {
        api.clearEODSessionId()
      }
      
      // 重置所有步骤状态
      steps.forEach(step => {
        step.status = 'pending'
      })
      
      successMessage.value = t('eod.step_messages.eod_cancelled_simple')
    }
    
    const handleComplete = () => {
      // 标记日结已完成
      isEODCompleted.value = true
      
      // 更新步骤状态 - 第8步也标记为完成
      steps[7].status = 'completed'
      
      // 更新日结数据状态
      eodData.status = 'completed'
      eodData.step_status = 'completed'
      
      // 清理日结会话ID
      if (api.clearEODSessionId) {
        api.clearEODSessionId()
      }
      
      // 更新成功消息
      successMessage.value = t('eod.step_messages.eod_completed')
      
      // 3秒后跳转到仪表板
      setTimeout(() => {
        router.push('/dashboard')
      }, 3000)
    }
    
    const handlePreviousStep = (result) => {
      if (result.success) {
        // 回到上一步 - 使用正确的字段名
        const targetStep = result.current_step || result.new_step
        currentStep.value = targetStep
        
        // 重置当前步骤及之后的步骤状态
        for (let i = currentStep.value; i < steps.length; i++) {
          steps[i].status = 'pending'
        }
        
        // 强制重新渲染组件
        nextTick(() => {
          // 触发响应式更新
          currentStep.value = targetStep
          
          // 清除可能的缓存数据
          error.value = ''
          successMessage.value = ''
          
          // 如果是第一步，清空EOD数据
          if (currentStep.value === 1) {
            Object.assign(eodData, {
              id: null,
              eod_no: '',
              date: null,
              step: 1,
              step_status: 'pending',
              status: 'pending',
              balance_data: null,
              created_at: null,
              step_timestamps: {}
            })
          }
        })
        
        // 导航成功消息将由EODStepNavigation组件发出
      }
    }
    
    const handleCancelFromNavigation = (result) => {
      if (result && result.success) {
        handleCancel()
        // 导航成功消息将由EODStepNavigation组件发出
      }
    }
    
    // 继续现有日结
    const continueExistingEOD = async () => {
      if (!eodData.id) {
        error.value = '没有可继续的日结'
        return
      }
      
      loading.value = true
      try {
        const continueResult = await eodAPI.continueEOD(eodData.id)
        if (continueResult.success && continueResult.session_id) {
          // 设置现有的会话ID到前端
          if (api.setEODSessionId) {
            api.setEODSessionId(continueResult.session_id)
          }
          successMessage.value = '成功恢复日结会话，可以继续操作'
          // 清除错误消息
          error.value = ''
          // 直接重新获取日结状态，避免权限检查
          try {
            const eodStatus = await eodAPI.getStatus(eodData.id)
            if (eodStatus.success) {
              Object.assign(eodData, eodStatus.eod_status)
              currentStep.value = eodData.step || 1
              
              for (let i = 0; i < currentStep.value - 1; i++) {
                steps[i].status = 'completed'
              }
              if (eodData.step_status === 'processing') {
                steps[currentStep.value - 1].status = 'processing'
              } else if (eodData.step_status === 'completed') {
                steps[currentStep.value - 1].status = 'completed'
              }
            }
          } catch (statusError) {
            console.error('获取日结状态失败:', statusError)
          }
          // 3秒后清除成功消息
          setTimeout(() => {
            successMessage.value = ''
          }, 3000)
        } else {
          error.value = continueResult.message || '继续日结失败'
        }
      } catch (continueError) {
        console.error('继续日结失败:', continueError)
        const errorMessage = continueError.response?.data?.message || continueError.message || '继续日结失败'
        const translatedError = translateErrorMessage(errorMessage, t)
        error.value = translatedError
      } finally {
        loading.value = false
      }
    }
    
    // 处理会话恢复请求（来自Step5Result组件）
    const handleSessionRecovery = async () => {
      console.log('收到会话恢复请求，开始自动恢复...')
      try {
        // 调用现有的继续日结逻辑
        await continueExistingEOD()
        console.log('会话恢复完成')
      } catch (recoveryError) {
        console.error('会话恢复失败:', recoveryError)
      }
    }
    
    const cancelEOD = async () => {
      try {
        loading.value = true
        
        // 使用统一的API服务，确保包含认证信息
        const response = await api.post(`/eod-step/${eodData.id}/cancel-complete`, {
          reason: '用户取消日结'
        })
        
        if (response.data.success) {
          handleCancel()
          successMessage.value = t('eod.step_messages.eod_cancelled_simple')
        } else {
          const errorMessage = response.data.message || '取消日结失败'
          const translatedError = translateErrorMessage(errorMessage, t)
          error.value = translatedError
        }
      } catch (err) {
        const errorMsg = err.response?.data?.message || err.message || '取消日结失败'
        const translatedError = translateErrorMessage(errorMsg, t)
        error.value = translatedError
      } finally {
        loading.value = false
      }
    }
    
    const getStatusClass = (status) => {
      switch (status) {
        case 'completed': return 'text-success'
        case 'processing': return 'text-warning'
        case 'cancelled': return 'text-danger'
        default: return 'text-muted'
      }
    }
    
    const getStatusText = (status) => {
      switch (status) {
        case 'completed': return t('eod.status.completed')
        case 'processing': return t('eod.status.processing')
        case 'cancelled': return t('eod.status.cancelled')
        default: return t('eod.status.pending')
      }
    }
    
    const formatTime = (dateTime) => {
      if (!dateTime) return '未知'
      
      const date = new Date(dateTime)
      return new Intl.DateTimeFormat('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      }).format(date)
    }
    
    // 特性开关相关方法
    const toggleFeaturePanel = () => {
      showFeaturePanel.value = !showFeaturePanel.value
      if (showFeaturePanel.value && featureFlags.value.length === 0) {
        loadFeatureFlags()
      }
    }
    
    const loadFeatureFlags = async () => {
      try {
        loadingFeatures.value = true
        // 使用统一的api服务，确保包含认证信息
        const response = await api.get('feature-flags/eod-settings')
        if (response.data.success) {
          featureFlags.value = Object.values(response.data.features)
        } else {
          const errorMessage = response.data.message || '未知错误'
          const translatedError = translateErrorMessage(errorMessage, t)
          error.value = '加载特性开关失败: ' + translatedError
        }
      } catch (err) {
        console.error('加载特性开关失败:', err)
        const errorMessage = err.response?.data?.message || err.message || '网络错误'
        const translatedError = translateErrorMessage(errorMessage, t)
        error.value = '加载特性开关失败: ' + translatedError
      } finally {
        loadingFeatures.value = false
      }
    }
    
    const toggleFeatureFlag = async (featureName, enabled) => {
      try {
        updatingFeature.value = featureName
        // 使用统一的api服务，确保包含认证信息
        const response = await api.post(`feature-flags/${featureName}`, {
          enabled: enabled
        })
        
        if (response.data.success) {
          // 更新本地状态
          const flagIndex = featureFlags.value.findIndex(f => f.key === featureName)
          if (flagIndex !== -1) {
            featureFlags.value[flagIndex].enabled = enabled
          }
          
          // 显示成功消息
          successMessage.value = `特性开关 ${featureName} 已${enabled ? '启用' : '关闭'}`
          
          // 清除成功消息
          setTimeout(() => {
            successMessage.value = ''
          }, 3000)
        } else {
          const errorMessage = response.data.message || '未知错误'
          const translatedError = translateErrorMessage(errorMessage, t)
          error.value = '设置特性开关失败: ' + translatedError
          // 恢复checkbox状态
          const flagIndex = featureFlags.value.findIndex(f => f.key === featureName)
          if (flagIndex !== -1) {
            featureFlags.value[flagIndex].enabled = !enabled
          }
        }
      } catch (err) {
        console.error('设置特性开关失败:', err)
        const errorMessage = err.response?.data?.message || err.message || '网络错误'
        const translatedError = translateErrorMessage(errorMessage, t)
        error.value = '设置特性开关失败: ' + translatedError
        // 恢复checkbox状态
        const flagIndex = featureFlags.value.findIndex(f => f.key === featureName)
        if (flagIndex !== -1) {
          featureFlags.value[flagIndex].enabled = !enabled
        }
      } finally {
        updatingFeature.value = ''
      }
    }
    
    // 获取当天日结历史
    const loadTodayEODHistory = async () => {
      try {
        const today = new Date().toISOString().split('T')[0]
        const result = await eodAPI.getTodayHistory(today)
        if (result.success) {
          todayEODHistory.value = result.history || []
        }
      } catch (error) {
        console.error('获取当天日结历史失败:', error)
        todayEODHistory.value = []
      }
    }
    
    // 检查是否有进行中的日结
    const checkExistingEOD = async () => {
      try {
        const lockStatus = await eodAPI.checkBusinessLock()
        if (lockStatus.is_locked && lockStatus.eod_id) {
          const eodStatus = await eodAPI.getStatus(lockStatus.eod_id)
          if (eodStatus.success) {
            Object.assign(eodData, eodStatus.eod_status)
            currentStep.value = eodData.step || 1
            
            for (let i = 0; i < currentStep.value - 1; i++) {
              steps[i].status = 'completed'
            }
            if (eodData.step_status === 'processing') {
              steps[currentStep.value - 1].status = 'processing'
            } else if (eodData.step_status === 'completed') {
              steps[currentStep.value - 1].status = 'completed'
            }
            
            // 如果已经有成功消息（说明用户已经点击了继续按钮），就不要重复显示
            if (!successMessage.value || !successMessage.value.includes('继续现有')) {
              successMessage.value = t('eod.system_messages.continue_existing_eod')
            }
            // 清除错误消息
            error.value = ''
            return
          }
        }
        
        const today = new Date().toISOString().split('T')[0]
        const completedEOD = await eodAPI.checkCompleted(today)
        if (completedEOD.has_completed) {
          successMessage.value = t('eod.system_messages.completed_eod_detected', { eod_id: completedEOD.eod_id })
          currentStep.value = 1
          steps.forEach(step => {
            step.status = 'pending'
          })
          // 重置eodData
          Object.assign(eodData, {
            id: null,
            date: '',
            status: '',
            is_locked: false,
            step: 1,
            step_status: ''
          })
          isEODCompleted.value = false
        } else {
          // 确保没有进行中的日结时，eodData被正确重置
          Object.assign(eodData, {
            id: null,
            date: '',
            status: '',
            is_locked: false,
            step: 1,
            step_status: ''
          })
        }
      } catch (err) {
        console.error('检查现有日结失败:', err)
        // 翻译并设置错误消息
        const errorMessage = err.response?.data?.message || err.message || '检查现有日结失败'
        const translatedError = translateErrorMessage(errorMessage, t)
        error.value = translatedError
        // 出错时也重置eodData
        Object.assign(eodData, {
          id: null,
          date: '',
          status: '',
          is_locked: false,
          step: 1,
          step_status: ''
        })
      }
    }
    
    // 简单的步骤标题获取函数
    const getStepTitle = (index) => {
      const stepTitles = [
        t('eod.step1_title', '开始日结'),
        t('eod.step2_title', '提取余额'), 
        t('eod.step3_title', '计算余额'),
        t('eod.step4_title', '核对余额'),
        t('eod.step5_title', '核对结果'),
        t('eod.step6_title', '收入统计'),
        t('eod.step7_title', '交款'),
        t('eod.step8_title', '确认完成')
      ]
      return stepTitles[index] || t('eod.unknown_step', '未知步骤')
    }

    // 步骤描述获取函数
    const getStepDescription = (index) => {
      const stepDescriptions = [
        t('eod.step1_desc', '营业锁定'),
        t('eod.step2_desc', '获取当前余额'),
        t('eod.step3_desc', '计算理论余额'),
        t('eod.step4_desc', '理论vs实际'),
        t('eod.step5_desc', '处理核对结果'),
        t('eod.step6_desc', '交款并解锁'),
        t('eod.step7_desc', '日结报表'),
        t('eod.step8_desc', '完成流程')
      ]
      return stepDescriptions[index] || t('eod.unknown_step_desc', '未知步骤')
    }

    // 生命周期
    onMounted(() => {
      checkExistingEOD()
      loadTodayEODHistory()
    })
    
    return {
      currentStep,
      loading,
      error,
      successMessage,
      navigationError,
      navigationSuccess,
      verificationResults,
      eodData,
      steps,
      currentUser,
      isEODCompleted,
      todayEODHistory,
      autoGenerateIncomeStats,
      showFeaturePanel,
      featureFlags,
      loadingFeatures,
      updatingFeature,
      clearError,
      handleError,
      handleStepSuccess,
      handleNavigationError,
      handleNavigationSuccess,
      clearNavigationError,
      clearNavigationSuccess,
      handleStepComplete,
      handleCancel,
      handleComplete,
      handlePreviousStep,
      handleCancelFromNavigation,
      handleSessionRecovery,
      continueExistingEOD,
      cancelEOD,
      getStatusClass,
      getStatusText,
      formatTime,
      toggleFeaturePanel,
      loadFeatureFlags,
      toggleFeatureFlag,
      getStepTitle,
      getStepDescription
    }
  }
}
</script>

<style scoped>
.step-number {
  min-width: 32px;
}

.step-info {
  flex: 1;
}

.step-title {
  font-weight: 500;
  font-size: 0.9rem;
}

.list-group-item.active {
  background-color: #e3f2fd;
  border-color: #90caf9;
  color: #1976d2;
}

.list-group-item.active .step-title,
.list-group-item.active .text-muted {
  color: #1976d2 !important;
  font-weight: 600;
}

.card-footer {
  background-color: #f8f9fa;
  border-top: 1px solid #dee2e6;
}

.alert-sm {
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
}

.alert-sm .btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
}

.step-item-compact {
  padding: 0.5rem 0.75rem;
}

.step-badge-sm {
  width: 1.2rem;
  height: 1.2rem;
  font-size: 0.6rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.step-title-sm {
  font-weight: 500;
  font-size: 0.8rem;
}

.step-desc-sm {
  font-size: 0.7rem;
}

.card-title-sm {
  font-size: 0.9rem;
}

.info-text-sm {
  font-size: 0.8rem;
}

@media (max-width: 768px) {
  .col-md-3, .col-md-4, .col-md-5 {
    margin-bottom: 1rem;
  }
  
  .step-item-compact {
    padding: 0.75rem;
  }
  
  .step-title-sm {
    font-size: 0.85rem;
  }
}

.card.shadow-sm {
  border: 1px solid #e3e6f0;
  border-radius: 0.35rem;
}

h2 {
  color: #5a5c69;
  font-weight: 600;
}
</style>
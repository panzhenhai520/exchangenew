<template>
  <div class="container-fluid py-4">
    <div class="row">
      <div class="col-12">
        <!-- 页面标题区域 -->
        <div class="mb-4">
          <div class="d-flex align-items-center mb-2">
            <h2 class="page-title-bold mb-0">
              <font-awesome-icon :icon="['fas', 'trash-alt']" class="me-2 text-danger" />
              {{ $t('data_clear.title') }}
            </h2>
          </div>
          <div class="alert alert-warning py-2 mb-0">
            <div class="d-flex align-items-center">
              <font-awesome-icon :icon="['fas', 'shield-alt']" class="me-2 text-warning" />
              <small class="mb-0">{{ $t('data_clear.subtitle') }}</small>
            </div>
          </div>
        </div>

        <!-- 权限检查 -->
        <div v-if="!hasPermission" class="alert alert-danger">
          <font-awesome-icon :icon="['fas', 'exclamation-triangle']" class="me-2" />
          <strong>{{ $t('data_clear.permission_denied') }}</strong>
        </div>

        <!-- 成功提示 -->
        <div v-if="lastClearSuccess" class="alert alert-success alert-dismissible fade show" role="alert">
          <font-awesome-icon :icon="['fas', 'check-circle']" class="me-2" />
          <strong>{{ $t('data_clear.clear_success') }}</strong>
          <small class="d-block mt-1">{{ $t('data_clear.clear_time') }}：{{ formatDateTime(lastClearTime) }}</small>
          <button type="button" class="btn-close" @click="lastClearSuccess = false"></button>
        </div>

        <!-- 主要操作区域 -->
        <div v-else class="row">
          <!-- 左侧：操作面板 -->
          <div class="col-md-8">
            <div class="card border-danger">
              <div class="card-header bg-danger text-white">
                <h5 class="mb-0">
                  <font-awesome-icon :icon="['fas', 'exclamation-triangle']" class="me-2" />
                  {{ $t('data_clear.data_clear_operation') }}
                </h5>
              </div>
              <div class="card-body">
                <!-- 当前网点信息 -->
                <div class="mb-4">
                  <div class="alert alert-info">
                    <h6><strong>{{ $t('data_clear.current_branch_info') }}</strong></h6>
                    <div class="row">
                      <div class="col-md-6">
                        <p><strong>{{ $t('system_maintenance.branch_management.branch_name') }}:</strong> {{ currentBranchName }}</p>
                        <p><strong>{{ $t('system_maintenance.branch_management.branch_code') }}:</strong> {{ currentBranchCode }}</p>
                      </div>
                      <div class="col-md-6">
                        <p><strong>{{ $t('log_query.operator') }}:</strong> {{ currentUserName }}</p>
                        <p><strong>{{ $t('data_clear.clear_status') }}:</strong> 
                          <span v-if="canClear" class="badge bg-success">{{ $t('data_clear.can_clear') }}</span>
                          <span v-else class="badge bg-danger">{{ $t('data_clear.cannot_clear') }}</span>
                        </p>
                      </div>
                    </div>
                    <div v-if="branchStatus && branchStatus.data_stats" class="mt-2">
                      <strong>{{ $t('data_clear.data_stats') }}:</strong> 
                      {{ $t('data_clear.transactions') }} {{ branchStatus.data_stats.transactions || 0 }} {{ $t('common.records') }}，
                      {{ $t('data_clear.adjustments') }} {{ branchStatus.data_stats.adjustments || 0 }} {{ $t('common.records') }}，
                      {{ $t('data_clear.eod_reports') }} {{ branchStatus.data_stats.eod_reports || 0 }} {{ $t('common.records') }}
                    </div>
                    <div v-if="!canClear && blockingReason" class="alert alert-warning mt-2">
                      <strong>{{ $t('data_clear.blocking_reason') }}:</strong> {{ blockingReason }}
                    </div>
                  </div>
                </div>

                <!-- 操作选项 -->
                <div class="mb-4">
                  <h6 class="text-danger mb-3">
                    <font-awesome-icon :icon="['fas', 'cog']" class="me-2" />
                    {{ $t('data_clear.clear_options') }}
                  </h6>
                  
                  <!-- 清理测试用户和角色选项 -->
                  <div class="form-check mb-3">
                    <input 
                      v-model="clearTestUsersRoles" 
                      class="form-check-input" 
                      type="checkbox" 
                      id="clearTestUsersRoles"
                    />
                    <label class="form-check-label" for="clearTestUsersRoles">
                      <strong class="text-danger">{{ $t('data_clear.clear_test_users_roles') }}</strong>
                      <br>
                      <small class="text-muted">{{ $t('data_clear.clear_test_users_roles_desc') }}</small>
                    </label>
                  </div>
                </div>

                <!-- 操作按钮 -->
                <div class="d-flex justify-content-end">
                  <button 
                    class="btn btn-danger btn-lg" 
                    :disabled="!canClear || clearing"
                    @click="showClearModal"
                  >
                    <span v-if="clearing" class="spinner-border spinner-border-sm me-2"></span>
                    <font-awesome-icon :icon="['fas', 'trash-alt']" class="me-2" />
                    {{ getClearButtonText() }}
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- 右侧：操作历史 -->
          <div class="col-md-4">

            <!-- 操作历史 -->
            <div v-if="resetHistory.length > 0" class="card mt-3">
              <div class="card-header">
                <h6 class="mb-0">
                  <font-awesome-icon :icon="['fas', 'history']" class="me-2" />
                  {{ $t('data_clear.clear_history') }}
                </h6>
              </div>
              <div class="card-body">
                <div v-for="record in resetHistory" :key="record.id" class="border-bottom pb-2 mb-2">
                  <div class="d-flex justify-content-between mb-2">
                    <strong>{{ record.operator_name }}</strong>
                    <small class="text-muted">{{ formatDateTime(record.reset_date) }}</small>
                  </div>
                  
                  <!-- 基本信息 -->
                  <div class="mb-2">
                    <div class="row g-2">
                      <div class="col-6">
                        <small class="text-muted">{{ $t('system_maintenance.branch_management.branch_code') }}:</small>
                        <span class="ms-1">{{ parseDetails(record.details).branch_id || $t('common.unknown') }}</span>
                      </div>
                      <div class="col-6">
                        <small class="text-muted">{{ $t('system_maintenance.branch_management.branch_name') }}:</small>
                        <span class="ms-1">{{ parseDetails(record.details).branch_name || $t('common.unknown') }}</span>
                      </div>
                    </div>
                    <div class="mt-1">
                      <small class="text-muted">{{ $t('data_clear.clear_reason') }}:</small>
                      <span class="ms-1">{{ parseDetails(record.details).reason || $t('common.unknown') }}</span>
                    </div>
                  </div>
                  

                  
                  <!-- 数据统计表格 -->
                  <div v-if="parseDetails(record.details).data_stats" class="mt-2">
                    <small class="text-muted d-block mb-1">{{ $t('data_clear.data_stats') }}:</small>
                    <div class="table-responsive">
                      <table class="table table-sm table-bordered mb-0">
                        <tbody>
                          <tr v-for="(count, key) in parseDetails(record.details).data_stats" :key="key" class="small">
                            <td class="text-muted" style="width: 40%">{{ formatDataKey(key) }}</td>
                            <td class="text-end fw-bold">{{ count }}</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 清空确认模态框 -->
    <div v-if="showModal" class="modal fade show" style="display: block; background: rgba(0,0,0,0.5)">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header bg-danger text-white">
            <h5 class="modal-title">{{ $t('data_clear.confirm_clear') }}</h5>
            <button type="button" class="btn-close btn-close-white" @click="closeModal"></button>
          </div>
          <div class="modal-body">
            <div class="alert alert-warning">
              <strong>{{ $t('common.warning') }}：</strong>{{ $t('data_clear.warning_message', { branch: currentBranchName }) }}
            </div>
            
            <!-- 清空原因 -->
            <div class="mb-3">
              <label class="form-label">
                <strong>{{ $t('data_clear.clear_reason') }}</strong>
                <span class="text-danger">*</span>
              </label>
              <textarea 
                v-model="clearReason" 
                class="form-control" 
                rows="3" 
                :placeholder="$t('data_clear.form.reason_placeholder')"
                :class="{ 'is-invalid': clearReason && clearReason.length < 10 }"
              ></textarea>
              <div v-if="clearReason && clearReason.length < 10" class="invalid-feedback">
                                 {{ $t('data_clear.form.reason_too_short') }}
              </div>
            </div>

            <!-- 安全密码输入 -->
            <div class="mb-3">
              <label class="form-label">
                <strong>{{ $t('data_clear.security_password') }}</strong>
                <span class="text-danger">*</span>
              </label>
              <input 
                v-model="securityPassword" 
                type="password" 
                class="form-control" 
                :placeholder="$t('data_clear.form.password_placeholder')"
                :class="{ 'is-valid': securityPassword === 'www.59697.com', 'is-invalid': securityPassword && securityPassword !== 'www.59697.com' }"
              />
              <div v-if="securityPassword && securityPassword !== 'www.59697.com'" class="invalid-feedback">
                {{ $t('data_clear.messages.invalid_password') }}
              </div>
              <div class="form-text">
                {{ $t('data_clear.form.password_help') }}
              </div>
            </div>

            <!-- 清理测试用户和角色确认 -->
            <div v-if="clearTestUsersRoles" class="mb-3">
              <div class="alert alert-warning">
                <font-awesome-icon :icon="['fas', 'exclamation-triangle']" class="me-2" />
                <strong>{{ $t('data_clear.clear_test_users_roles_warning') }}</strong>
              </div>
              <div class="form-check">
                <input 
                  v-model="confirmClearTestUsersRoles" 
                  class="form-check-input" 
                  type="checkbox" 
                  id="confirmClearTestUsersRoles"
                />
                <label class="form-check-label text-warning" for="confirmClearTestUsersRoles">
                  <strong>{{ $t('data_clear.clear_test_users_roles_confirm') }}</strong>
                </label>
              </div>
            </div>

            <!-- 最终确认 -->
            <div class="mb-3">
              <div class="form-check">
                <input 
                  v-model="finalConfirm" 
                  class="form-check-input" 
                  type="checkbox" 
                  id="finalConfirm"
                />
                <label class="form-check-label text-danger" for="finalConfirm">
                  <strong>{{ $t('data_clear.final_confirm') }}</strong>
                </label>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="closeModal">{{ $t('common.cancel') }}</button>
            <button 
              class="btn btn-danger" 
              :disabled="!canExecuteClear || clearing"
              @click="executeClear"
            >
              <span v-if="clearing" class="spinner-border spinner-border-sm me-2"></span>
              {{ $t('data_clear.confirm_clear') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'
import { formatDateTime } from '@/utils/formatters'

export default {
  name: 'DataClearView',
  data() {
    return {
      loading: false,
      clearing: false,
      hasPermission: false,
      currentBranchId: null,
      currentBranchName: '',
      currentBranchCode: '',
      currentUserName: '',
      branchStatus: null,
      clearReason: '',
      securityPassword: '',
      finalConfirm: false,
      resetHistory: [],
      showModal: false,
      canClear: false,
      blockingReason: '',
      lastClearSuccess: false,
      lastClearTime: null,
      clearTestUsersRoles: false,
      confirmClearTestUsersRoles: false
    }
  },
  computed: {
    canExecuteClear() {
      const basicConditions = this.clearReason.length >= 10 &&
                             this.securityPassword === 'www.59697.com' &&
                             this.finalConfirm
      
      // 如果选择了清理测试用户和角色，需要额外确认
      if (this.clearTestUsersRoles) {
        return basicConditions && this.confirmClearTestUsersRoles
      }
      
      return basicConditions
    }
  },
  async created() {
    await this.checkPermission()
    if (this.hasPermission) {
      await this.loadCurrentBranchInfo()
      await this.loadBranchStatus()
    }
  },
  methods: {
    async checkPermission() {
      try {
        const userPermissions = JSON.parse(localStorage.getItem('userPermissions') || '[]')
        const userData = JSON.parse(localStorage.getItem('user') || '{}')
        
        this.hasPermission = userPermissions.includes('system_manage') || userData.role === 'admin'
      } catch (error) {
        console.error('检查权限失败:', error)
        this.hasPermission = false
      }
    },

    async loadCurrentBranchInfo() {
      try {
        const userData = JSON.parse(localStorage.getItem('user') || '{}')
        console.log('用户数据:', userData)
        
        this.currentBranchId = userData.branch_id
        this.currentBranchName = userData.branch_name || '未知网点'
        this.currentBranchCode = userData.branch_code || ''
        this.currentUserName = userData.name || userData.username || '未知用户'
        
        console.log('当前网点ID:', this.currentBranchId)
        console.log('当前网点名称:', this.currentBranchName)
        
        if (!this.currentBranchId) {
          throw new Error('无法获取当前网点信息，请重新登录')
        }
      } catch (error) {
        console.error('加载当前网点信息失败:', error)
        this.$toast?.error('加载当前网点信息失败: ' + error.message)
      }
    },

    async loadBranchStatus() {
      if (!this.currentBranchId) {
        console.warn('网点ID为空，无法加载状态')
        this.branchStatus = null
        this.resetHistory = []
        this.canClear = false
        this.blockingReason = '网点信息缺失'
        return
      }

      try {
        this.loading = true
        console.log('开始加载网点状态，网点ID:', this.currentBranchId)
        
        // 加载网点状态
        const statusResponse = await api.get(`operating-status/check-clear-permission/${this.currentBranchId}`)
        console.log('网点状态响应:', statusResponse.data)
        
        if (statusResponse.data.success) {
          this.branchStatus = statusResponse.data
          this.canClear = statusResponse.data.can_clear || false
          this.blockingReason = statusResponse.data.blocking_reason || ''
          console.log('网点状态加载成功，可清空:', this.canClear)
        } else {
          throw new Error(statusResponse.data.message || '获取网点状态失败')
        }

        // 加载清空历史
        try {
          const historyResponse = await api.get(`operating-status/reset-history/${this.currentBranchId}`)
          console.log('清空历史响应:', historyResponse.data)
          
          if (historyResponse.data.success) {
            this.resetHistory = historyResponse.data.data || []
          }
        } catch (historyError) {
          console.warn('加载清空历史失败，但不影响主功能:', historyError)
          this.resetHistory = []
        }
        
      } catch (error) {
        console.error('加载网点状态失败:', error)
        console.error('错误详情:', error.response?.data || error.message)
        
        let errorMessage = '加载网点状态失败'
        if (error.response?.status === 403) {
          errorMessage = '权限不足，无法访问清空功能'
        } else if (error.response?.status === 404) {
          errorMessage = '网点不存在或API接口未找到'
        } else if (error.response?.data?.message) {
          errorMessage = error.response.data.message
        } else {
          errorMessage += ': ' + error.message
        }
        
        this.$toast?.error(errorMessage)
        this.canClear = false
        this.blockingReason = errorMessage
      } finally {
        this.loading = false
      }
    },

    showClearModal() {
      if (!this.currentBranchId || !this.canClear) return
      this.showModal = true
    },

    closeModal() {
      this.showModal = false
      this.clearReason = ''
      this.securityPassword = ''
      this.finalConfirm = false
      this.confirmClearTestUsersRoles = false
    },
    
    getClearButtonText() {
      if (this.clearing) {
        return this.$t('data_clear.clearing')
      }
      
      if (this.clearTestUsersRoles) {
        return this.$t('data_clear.clear_both')
      }
      
      return this.$t('data_clear.clear_current_branch')
    },

    async executeClear() {
      if (!this.canExecuteClear) return

      try {
        this.clearing = true
        
        const requestData = {
          confirm_code: this.securityPassword,
          reason: this.clearReason,
          clear_test_users_roles: this.clearTestUsersRoles
        }
        
        const response = await api.post(`operating-status/clear-data/${this.currentBranchId}`, requestData)

        if (response.data.success) {
          let successMessage = '✅ 营业数据清空成功！\n\n' + 
                `网点：${this.currentBranchName}\n` +
                `清空数据统计：\n` +
                `- 交易记录：${response.data.cleared_data?.transactions || 0} 条\n` +
                `- 余额调节：${response.data.cleared_data?.adjustments || 0} 条\n` +
                `- 日结报告：${response.data.cleared_data?.eod_histories || 0} 条\n` +
                `- 第 ${response.data.reset_count || 1} 次重置`
          
          // 如果清理了测试用户和角色，添加相关信息
          if (this.clearTestUsersRoles && response.data.test_users_roles_cleared) {
            successMessage += `\n\n🧹 测试用户和角色清理统计：\n` +
                            `- 删除用户：${response.data.test_users_roles_cleared.deleted_users || 0} 个\n` +
                            `- 删除角色：${response.data.test_users_roles_cleared.deleted_roles || 0} 个`
          }
          
          this.$toast?.success('操作成功！')
          alert(successMessage)
          
          this.closeModal()
          // 设置成功状态
          this.lastClearSuccess = true
          this.lastClearTime = new Date()
          // 重新加载状态
          await this.loadBranchStatus()
          
          // 3秒后清除成功状态
          setTimeout(() => {
            this.lastClearSuccess = false
          }, 3000)
        } else {
          throw new Error(response.data.message || '操作失败')
        }
      } catch (error) {
        console.error('操作失败:', error)
        this.$toast?.error(error.response?.data?.message || error.message || '操作失败')
      } finally {
        this.clearing = false
      }
    },

    parseDetails(detailsString) {
      if (!detailsString || typeof detailsString !== 'string') {
        return {}
      }
      
      const result = {}
      
      // 解析网点ID
      const branchIdMatch = detailsString.match(/网点ID:\s*(\d+)/)
      if (branchIdMatch) {
        result.branch_id = branchIdMatch[1]
      }
      
      // 解析网点名称
      const branchNameMatch = detailsString.match(/网点名称:\s*([^,]+)/)
      if (branchNameMatch) {
        result.branch_name = branchNameMatch[1].trim()
      }
      
      // 解析清空原因
      const reasonMatch = detailsString.match(/原因:\s*([^,]+)/)
      if (reasonMatch) {
        result.reason = reasonMatch[1].trim()
      }
      
      // 解析数据统计
      const statsMatch = detailsString.match(/清空前统计:\s*({.+})/)
      if (statsMatch) {
        try {
          result.data_stats = JSON.parse(statsMatch[1])
        } catch (e) {
          console.warn('解析数据统计失败:', e)
        }
      }
      
      return result
    },

    formatDataKey(key) {
      const keyMap = {
        'transactions': '交易记录',
        'adjustments': '余额调节',
        'currency_balances': '币种余额',
        'eod_histories': '日结历史',
        'eod_statuses': '日结状态',
        'system_logs': '系统日志',
        'activity_logs': '活动日志',
        'transaction_alerts': '交易提醒',
        'rate_publish_records': '汇率发布记录',
        'receipt_sequences': '票据序列',
        'display_access_logs': '显示访问日志',
        'daily_income_reports': '日收入报表',
        'daily_foreign_stock': '日外汇库存'
      }
      return keyMap[key] || key
    },

    formatDateTime
  }

}
</script>

<style scoped>
.border-danger {
  border-color: #dc3545 !important;
}

.border-warning {
  border-color: #ffc107 !important;
}

.feature-card-compact {
  transition: all 0.3s ease;
}

.feature-card-compact:hover {
  transform: translateY(-2px);
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15) !important;
}

.alert {
  border-radius: 0.375rem;
}

.form-check-label {
  font-weight: 500;
}

.modal {
  z-index: 1050;
}
</style> 
import api from '../services/api/index'

// 获取当前用户分支ID
const getCurrentBranchId = () => {
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    return user.branch_id
  } catch {
    return null
  }
}

// EOD API 服务
export const eodAPI = {
  // 步骤1: 开始日结
  async start(date = null) {
    const branchId = getCurrentBranchId()
    if (!branchId) {
      throw new Error('无法获取分支信息')
    }
    
    const response = await api.post('/end_of_day/start', {
      branch_id: branchId,
      date: date || new Date().toISOString().split('T')[0]
    })
    
    return response.data
  },

  // 步骤2: 提取余额
  async extractBalance(eodId) {
    const response = await api.get(`/end_of_day/${eodId}/balance`)
    
    return response.data
  },

  // 步骤3: 计算理论余额
  async calculateBalance(eodId) {
    const response = await api.get(`/end_of_day/${eodId}/calc`)
    
    return response.data
  },

  // 步骤4: 核对余额
  async verifyBalance(eodId) {
    const response = await api.get(`/end_of_day/${eodId}/check`)
    
    return response.data
  },

  // 处理余额差额选择
  async handleBalanceDifference(eodId, action, reason = '') {
    const response = await api.post(`/end_of_day/${eodId}/handle_difference`, {
      action, // 'cancel', 'force', 'adjust'
      reason
    })
    
    return response.data
  },

  // 执行日结差额调节
  async adjustEODDifference(eodId, adjustData) {
    const response = await api.post(`/end_of_day/${eodId}/adjust_difference`, {
      adjust_data: adjustData
    })
    
    return response.data
  },

  // 步骤5: 处理核对结果
  async handleVerification(eodId, action, reason = '') {
    const response = await api.post(`/end_of_day/${eodId}/verify`, {
      action, // 'continue' or 'cancel'
      reason
    })
    
    return response.data
  },

  // 步骤6: 完成交款
  async processCashOut(eodId, cashOutData) {
    // 兼容旧版本调用方式
    if (Array.isArray(cashOutData)) {
      cashOutData = {
        cash_out_data: cashOutData
      }
    }
    
    const response = await api.post(`/end_of_day/${eodId}/cashout`, cashOutData)
    
    return response.data
  },

  // 步骤8: 生成报表（最终报表）
  async generateReport(eodId, mode = 'simple') {
    const response = await api.get(`/end_of_day/${eodId}/report`, {
      params: { mode }
    })
    
    return response.data
  },

  // 打印差额调节报告
  async printDifferenceAdjustmentReport(eodId, language = 'zh') {
    const response = await api.get(`/end_of_day/${eodId}/print_difference_adjustment_report`, {
      params: { language }
    })
    
    return response.data
  },

  // 打印差额报告
  async printDifferenceReport(eodId, language = 'zh') {
    try {
      const response = await api.get(`/end_of_day/${eodId}/print_difference_report?language=${language}`);
      return response.data;
    } catch (error) {
      console.error('打印差额报告失败:', error);
      throw error;
    }
  },

  // 获取币种详细交易流水
  async getCurrencyTransactionsDetail(eodId, currencyCode, options = {}) {
    try {
      const response = await api.get(`/end_of_day/${eodId}/currency/${currencyCode}/transactions`, {
        params: {
          page: options.page || 1,
          per_page: options.per_page || 50
        }
      });
      return response.data;
    } catch (error) {
      console.error('获取币种交易详情失败:', error);
      throw error;
    }
  },

  // 步骤7: 预览报表（不检查步骤状态）
  async previewReport(eodId, mode = 'simple') {
    const response = await api.get(`/end_of_day/${eodId}/preview`, {
      params: { mode }
    })
    
    return response.data
  },

  // 打印报表
  async printReport(eodId, mode = 'simple', language = 'zh') {
    const response = await api.post(`/end_of_day/${eodId}/print`, {
      mode,
      language
    })
    
    return response.data
  },

  // 步骤8: 完成日结
  async complete(eodId) {
    const response = await api.post(`/end_of_day/${eodId}/complete`, {})
    
    return response.data
  },

  // 获取日结状态
  async getStatus(eodId) {
    const response = await api.get(`/end_of_day/${eodId}/status`)
    
    return response.data
  },

  // 检查营业锁定状态
  async checkBusinessLock() {
    const branchId = getCurrentBranchId()
    if (!branchId) {
      throw new Error('无法获取分支信息')
    }
    
    const response = await api.get('/end_of_day/lock-status', {
      params: { branch_id: branchId }
    })
    
    return response.data
  },

  // 取消日结
  async cancel(eodId, reason) {
    const response = await api.post(`/end_of_day/${eodId}/cancel`, {
      reason
    })
    
    return response.data
  },

  // 检查指定日期是否有已完成的日结
  async checkCompleted(date) {
    const response = await api.get('/end_of_day/check_completed', {
      params: { date }
    })
    
    return response.data
  },

  // 获取当天日结历史
  async getTodayHistory(date) {
    const response = await api.get('/end_of_day/today_history', {
      params: { date }
    })
    
    return response.data
  },

  // 获取最新的日结记录
  async getLatestEOD(branchId, beforeDate = null) {
    const response = await api.get('/end_of_day/latest', {
      params: { 
        branch_id: branchId,
        before_date: beforeDate
      }
    })
    
    return response.data
  },

  // 兼容性接口 - 获取日结汇总
  async getSummary(date = null) {
    const branchId = getCurrentBranchId()
    if (!branchId) {
      throw new Error('无法获取分支信息')
    }
    
    const response = await api.get('/end_of_day/summary', {
      params: { 
        branch_id: branchId,
        date: date || new Date().toISOString().split('T')[0]
      }
    })
    
    return response.data
  },

  // 生成收入统计
  async generateIncomeStatistics(eodId, options = {}) {
    const response = await api.post(`/end_of_day/${eodId}/income-statistics`, {
      language: options.language || 'zh'
    }, {
      timeout: 60000 // 增加超时时间到60秒
    })
    
    return response.data
  },

  // 确认报表为最终版本
  async finalizeReports(eodId) {
    const response = await api.post(`/end_of_day/${eodId}/finalize-reports`)
    
    return response.data
  },

  // 打印收入报表
  async printIncomeReports(eodId, options = {}) {
    const response = await api.post(`/end_of_day/${eodId}/print-reports`, {
      report_type: 'income',
      language: options.language || 'zh'
    })
    
    return response.data
  },

  // 下载收入报表PDF
  async downloadIncomeReport(eodId, options = {}) {
    const response = await api.get(`/end_of_day/${eodId}/download-income-report`, {
      responseType: 'blob',
      params: {
        language: options.language || 'zh'
      }
    })
    
    return response
  },

  // 打印综合报表（外币收入、外币库存、本币库存）
  async printComprehensiveReports(eodId, options = {}) {
    const response = await api.post(`/end_of_day/${eodId}/print-comprehensive-reports`, {
      report_type: 'comprehensive',
      language: options.language || 'zh'
    })
    
    return response.data
  },

  // 获取币种交易明细
  async getCurrencyTransactionDetails(currencyCode, options = {}) {
    const response = await api.get(`/reports/income/currency/${currencyCode}/transactions`, {
      params: {
        date: options.date || new Date().toISOString().split('T')[0],
        branch_id: options.branch_id || getCurrentBranchId(),
        page: options.page || 1,
        per_page: options.per_page || 20
      }
    })
    
    return response.data
  },

  // 获取本币交易明细
  async getBaseCurrencyTransactionDetails(eodId, currencyCode, options = {}) {
    const response = await api.get(`/end_of_day/${eodId}/base-currency/${currencyCode}/transactions`, {
      params: {
        page: options.page || 1,
        per_page: options.per_page || 20
      }
    })
    
    return response.data
  },

  // 继续现有日结流程
  async continueEOD(eodId) {
    const response = await api.post(`/end_of_day/${eodId}/continue`, {
      session_id: api.getEODSessionId ? api.getEODSessionId() : `eod_continue_${Date.now()}`,
      ip_address: '127.0.0.1', // 在前端无法获取真实IP，使用默认值
      user_agent: navigator.userAgent || 'Unknown'
    })
    
    return response.data
  },

  // 清理日结会话
  async cleanupSession() {
    const response = await api.post('/end_of_day/cleanup-session', {})
    
    return response.data
  },

  // 获取日结历史记录
  async getEODHistory(params = {}) {
    const response = await api.get('/end_of_day/history', {
      params: {
        page: params.page || 1,
        per_page: params.per_page || 20,
        start_date: params.start_date,
        end_date: params.end_date
      }
    })
    
    return response.data
  },

  // 检查现有日结
  async checkExistingEOD() {
    const response = await api.get('/end_of_day/check_existing')
    
    return response.data
  },

  // 取消已完成日结
  async cancelCompletedEOD(eodId) {
    const response = await api.post(`/end_of_day/${eodId}/cancel_completed`)
    
    return response.data
  }
}

export default eodAPI 
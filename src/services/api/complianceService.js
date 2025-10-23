import api from './index'

/**
 * 合规配置服务
 * 提供触发规则、字段定义等配置管理功能
 */
const complianceService = {
  /**
   * 获取触发规则列表
   * @param {Object} params - 查询参数 { report_type, is_active }
   * @returns {Promise}
   */
  async getTriggerRules(params = {}) {
    try {
      const response = await api.get('/compliance/trigger-rules', { params })
      return response.data
    } catch (error) {
      console.error('Get trigger rules error:', error)
      throw error
    }
  },

  /**
   * 创建触发规则
   * @param {Object} data - 规则数据
   * @returns {Promise}
   */
  async createTriggerRule(data) {
    try {
      const response = await api.post('/compliance/trigger-rules', data)
      return response.data
    } catch (error) {
      console.error('Create trigger rule error:', error)
      throw error
    }
  },

  /**
   * 更新触发规则
   * @param {Number} ruleId - 规则ID
   * @param {Object} data - 更新数据
   * @returns {Promise}
   */
  async updateTriggerRule(ruleId, data) {
    try {
      const response = await api.put(`/compliance/trigger-rules/${ruleId}`, data)
      return response.data
    } catch (error) {
      console.error('Update trigger rule error:', error)
      throw error
    }
  },

  /**
   * 获取报告字段定义列表
   * @param {Object} params - 查询参数 { report_type, is_active }
   * @returns {Promise}
   */
  async getReportFields(params = {}) {
    try {
      const response = await api.get('/compliance/fields', { params })
      return response.data
    } catch (error) {
      console.error('Get report fields error:', error)
      throw error
    }
  },

  /**
   * 创建报告字段定义
   * @param {Object} data - 字段数据
   * @returns {Promise}
   */
  async createReportField(data) {
    try {
      const response = await api.post('/compliance/fields', data)
      return response.data
    } catch (error) {
      console.error('Create report field error:', error)
      throw error
    }
  },

  /**
   * 更新报告字段定义
   * @param {Number} fieldId - 字段ID
   * @param {Object} data - 更新数据
   * @returns {Promise}
   */
  async updateReportField(fieldId, data) {
    try {
      const response = await api.put(`/compliance/fields/${fieldId}`, data)
      return response.data
    } catch (error) {
      console.error('Update report field error:', error)
      throw error
    }
  },

  /**
   * 获取资金来源列表
   * @param {Object} params - 查询参数 { is_active }
   * @returns {Promise}
   */
  async getFundingSources(params = {}) {
    try {
      const response = await api.get('/compliance/funding-sources', { params })
      return response.data
    } catch (error) {
      console.error('Get funding sources error:', error)
      throw error
    }
  }
}

export default complianceService

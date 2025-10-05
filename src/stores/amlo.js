/**
 * AMLO合规报告 Pinia Store
 * 管理AMLO预约、审核、报告的状态和API调用
 */

import { defineStore } from 'pinia'
import axios from 'axios'

const API_BASE_URL = process.env.VUE_APP_API_BASE_URL || 'http://127.0.0.1:5001'

export const useAMLOStore = defineStore('amlo', {
  state: () => ({
    // 预约记录列表
    reservations: [],
    reservationsTotal: 0,
    reservationsPage: 1,
    reservationsPageSize: 20,
    reservationsLoading: false,

    // 报告列表
    reports: [],
    reportsTotal: 0,
    reportsPage: 1,
    reportsPageSize: 20,
    reportsLoading: false,

    // 当前选中的记录
    currentReservation: null,
    currentReport: null,

    // 报告类型列表
    reportTypes: [],

    // 表单定义
    formDefinitions: {},

    // 客户历史记录
    customerHistory: null,
  }),

  getters: {
    /**
     * 获取待审核的预约数量
     */
    pendingReservationsCount: (state) => {
      return state.reservations.filter(r => r.status === 'pending').length
    },

    /**
     * 获取待上报的报告数量
     */
    unreportedReportsCount: (state) => {
      return state.reports.filter(r => !r.is_reported).length
    },

    /**
     * 计算预约分页总页数
     */
    reservationsTotalPages: (state) => {
      return Math.ceil(state.reservationsTotal / state.reservationsPageSize)
    },

    /**
     * 计算报告分页总页数
     */
    reportsTotalPages: (state) => {
      return Math.ceil(state.reportsTotal / state.reportsPageSize)
    },
  },

  actions: {
    /**
     * 获取报告类型列表
     */
    async fetchReportTypes() {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/repform/report-types`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        })

        if (response.data.success) {
          this.reportTypes = response.data.data
        }

        return response.data
      } catch (error) {
        console.error('获取报告类型失败:', error)
        throw error
      }
    },

    /**
     * 获取表单定义
     */
    async fetchFormDefinition(reportType, language = 'zh') {
      try {
        const response = await axios.get(
          `${API_BASE_URL}/api/repform/form-definition/${reportType}`,
          {
            params: { language },
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
          }
        )

        if (response.data.success) {
          this.formDefinitions[reportType] = response.data.data
        }

        return response.data
      } catch (error) {
        console.error('获取表单定义失败:', error)
        throw error
      }
    },

    /**
     * 检查触发条件
     */
    async checkTrigger(reportType, data) {
      try {
        const response = await axios.post(
          `${API_BASE_URL}/api/repform/check-trigger`,
          { report_type: reportType, data },
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
          }
        )

        return response.data
      } catch (error) {
        console.error('检查触发条件失败:', error)
        throw error
      }
    },

    /**
     * 保存预约记录
     */
    async saveReservation(reservationData) {
      try {
        const response = await axios.post(
          `${API_BASE_URL}/api/repform/save-reservation`,
          reservationData,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
          }
        )

        return response.data
      } catch (error) {
        console.error('保存预约失败:', error)
        throw error
      }
    },

    /**
     * 获取预约记录列表
     */
    async fetchReservations(params = {}) {
      this.reservationsLoading = true

      try {
        const response = await axios.get(`${API_BASE_URL}/api/amlo/reservations`, {
          params: {
            page: this.reservationsPage,
            page_size: this.reservationsPageSize,
            ...params
          },
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        })

        if (response.data.success) {
          this.reservations = response.data.data.items
          this.reservationsTotal = response.data.data.total
          this.reservationsPage = response.data.data.page
        }

        return response.data
      } catch (error) {
        console.error('获取预约列表失败:', error)
        throw error
      } finally {
        this.reservationsLoading = false
      }
    },

    /**
     * 审核预约记录
     */
    async auditReservation(reservationId, action, data = {}) {
      try {
        const response = await axios.post(
          `${API_BASE_URL}/api/amlo/reservations/${reservationId}/audit`,
          { action, ...data },
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
          }
        )

        // 审核成功后刷新列表
        if (response.data.success) {
          await this.fetchReservations()
        }

        return response.data
      } catch (error) {
        console.error('审核预约失败:', error)
        throw error
      }
    },

    /**
     * 反审核预约记录
     */
    async reverseAuditReservation(reservationId, remarks = '') {
      try {
        const response = await axios.post(
          `${API_BASE_URL}/api/amlo/reservations/${reservationId}/reverse-audit`,
          { remarks },
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
          }
        )

        // 反审核成功后刷新列表
        if (response.data.success) {
          await this.fetchReservations()
        }

        return response.data
      } catch (error) {
        console.error('反审核失败:', error)
        throw error
      }
    },

    /**
     * 完成预约
     */
    async completeReservation(reservationId, transactionId) {
      try {
        const response = await axios.post(
          `${API_BASE_URL}/api/amlo/reservations/${reservationId}/complete`,
          { linked_transaction_id: transactionId },
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
          }
        )

        return response.data
      } catch (error) {
        console.error('完成预约失败:', error)
        throw error
      }
    },

    /**
     * 获取报告列表
     */
    async fetchReports(params = {}) {
      this.reportsLoading = true

      try {
        const response = await axios.get(`${API_BASE_URL}/api/amlo/reports`, {
          params: {
            page: this.reportsPage,
            page_size: this.reportsPageSize,
            ...params
          },
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        })

        if (response.data.success) {
          this.reports = response.data.data.items
          this.reportsTotal = response.data.data.total
          this.reportsPage = response.data.data.page
        }

        return response.data
      } catch (error) {
        console.error('获取报告列表失败:', error)
        throw error
      } finally {
        this.reportsLoading = false
      }
    },

    /**
     * 批量上报报告
     */
    async batchReportSubmit(reportIds) {
      try {
        const response = await axios.post(
          `${API_BASE_URL}/api/amlo/reports/batch-report`,
          { report_ids: reportIds },
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
          }
        )

        // 上报成功后刷新列表
        if (response.data.success) {
          await this.fetchReports()
        }

        return response.data
      } catch (error) {
        console.error('批量上报失败:', error)
        throw error
      }
    },

    /**
     * 生成PDF
     */
    async generatePDF(reportId) {
      try {
        const response = await axios.get(
          `${API_BASE_URL}/api/amlo/reports/${reportId}/generate-pdf`,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            responseType: 'blob'
          }
        )

        // 创建下载链接
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `AMLO_Report_${reportId}.pdf`)
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)

        return { success: true, message: 'PDF下载成功' }
      } catch (error) {
        console.error('生成PDF失败:', error)
        throw error
      }
    },

    /**
     * 批量生成PDF（ZIP）
     */
    async batchGeneratePDF(reportIds) {
      try {
        const response = await axios.post(
          `${API_BASE_URL}/api/amlo/reports/batch-generate-pdf`,
          { report_ids: reportIds },
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            responseType: 'blob'
          }
        )

        // 创建下载链接
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
        link.setAttribute('download', `AMLO_Reports_${timestamp}.zip`)
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)

        return { success: true, message: 'PDF批量下载成功' }
      } catch (error) {
        console.error('批量生成PDF失败:', error)
        throw error
      }
    },

    /**
     * 获取客户历史记录
     */
    async fetchCustomerHistory(customerId, days = 30) {
      try {
        const response = await axios.get(
          `${API_BASE_URL}/api/repform/customer-history/${customerId}`,
          {
            params: { days },
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
          }
        )

        if (response.data.success) {
          this.customerHistory = response.data.data
        }

        return response.data
      } catch (error) {
        console.error('获取客户历史失败:', error)
        throw error
      }
    },

    /**
     * 设置当前预约
     */
    setCurrentReservation(reservation) {
      this.currentReservation = reservation
    },

    /**
     * 设置当前报告
     */
    setCurrentReport(report) {
      this.currentReport = report
    },

    /**
     * 重置状态
     */
    resetState() {
      this.reservations = []
      this.reports = []
      this.currentReservation = null
      this.currentReport = null
      this.customerHistory = null
    },
  },
})

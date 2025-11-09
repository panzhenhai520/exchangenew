/**
 * BOT报表 Pinia Store
 * 管理BOT买入/卖出外币报表的状态和API调用
 */

import { defineStore } from 'pinia'
import api from '@/services/api'  // 使用配置好baseURL的axios实例
// import { API_PREFIX } from '@/config/apiConfig' // 不再需要，axios已配置baseURL

export const useBOTStore = defineStore('bot', {
  state: () => ({
    // 买入外币报表
    buyFXData: null,
    buyFXLoading: false,

    // 卖出外币报表
    sellFXData: null,
    sellFXLoading: false,

    // 查询日期
    queryDate: null,
  }),

  getters: {
    /**
     * 获取买入外币总金额（泰铢）
     */
    buyFXTotalAmount: (state) => {
      return state.buyFXData?.total_amount_thb || 0
    },

    /**
     * 获取卖出外币总金额（泰铢）
     */
    sellFXTotalAmount: (state) => {
      return state.sellFXData?.total_amount_thb || 0
    },

    /**
     * 获取买入外币总笔数
     */
    buyFXTotalCount: (state) => {
      return state.buyFXData?.total_count || 0
    },

    /**
     * 获取卖出外币总笔数
     */
    sellFXTotalCount: (state) => {
      return state.sellFXData?.total_count || 0
    },
  },

  actions: {
    /**
     * 查询T+1买入外币报表
     */
    async fetchBuyFX(date = null) {
      this.buyFXLoading = true

      try {
        const queryDate = date || this.queryDate || this.getYesterdayDate()

        const response = await api.get('bot/t1-buy-fx', {
          params: { date: queryDate },
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        })

        if (response.data.success) {
          this.buyFXData = response.data.data
          this.queryDate = queryDate
        }

        return response.data
      } catch (error) {
        console.error('查询买入外币报表失败:', error)
        throw error
      } finally {
        this.buyFXLoading = false
      }
    },

    /**
     * 查询T+1卖出外币报表
     */
    async fetchSellFX(date = null) {
      this.sellFXLoading = true

      try {
        const queryDate = date || this.queryDate || this.getYesterdayDate()

        const response = await api.get('bot/t1-sell-fx', {
          params: { date: queryDate },
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        })

        if (response.data.success) {
          this.sellFXData = response.data.data
          this.queryDate = queryDate
        }

        return response.data
      } catch (error) {
        console.error('查询卖出外币报表失败:', error)
        throw error
      } finally {
        this.sellFXLoading = false
      }
    },

    /**
     * 导出买入外币Excel
     */
    async exportBuyFXExcel(date = null) {
      try {
        const queryDate = date || this.queryDate || this.getYesterdayDate()

        const response = await api.get('bot/export-buy-fx', {
          params: { date: queryDate },
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          responseType: 'blob'
        })

        // 创建下载链接
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `BOT_BuyFX_${queryDate}.xlsx`)
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)

        return { success: true, message: 'Excel导出成功' }
      } catch (error) {
        console.error('导出买入外币Excel失败:', error)
        throw error
      }
    },

    /**
     * 导出卖出外币Excel
     */
    async exportSellFXExcel(date = null) {
      try {
        const queryDate = date || this.queryDate || this.getYesterdayDate()

        const response = await api.get('bot/export-sell-fx', {
          params: { date: queryDate },
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          responseType: 'blob'
        })

        // 创建下载链接
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `BOT_SellFX_${queryDate}.xlsx`)
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)

        return { success: true, message: 'Excel导出成功' }
      } catch (error) {
        console.error('导出卖出外币Excel失败:', error)
        throw error
      }
    },

    /**
     * 保存买入外币报表记录
     */
    async saveBuyFX(transactionId, reportDate, jsonData) {
      try {
        const response = await api.post(
          'bot/save-buy-fx',
          {
            transaction_id: transactionId,
            report_date: reportDate,
            json_data: jsonData
          },
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
          }
        )

        return response.data
      } catch (error) {
        console.error('保存买入外币记录失败:', error)
        throw error
      }
    },

    /**
     * 保存卖出外币报表记录
     */
    async saveSellFX(transactionId, reportDate, jsonData) {
      try {
        const response = await api.post(
          'bot/save-sell-fx',
          {
            transaction_id: transactionId,
            report_date: reportDate,
            json_data: jsonData
          },
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
          }
        )

        return response.data
      } catch (error) {
        console.error('保存卖出外币记录失败:', error)
        throw error
      }
    },

    /**
     * 获取昨天的日期（YYYY-MM-DD）
     */
    getYesterdayDate() {
      const yesterday = new Date()
      yesterday.setDate(yesterday.getDate() - 1)
      return yesterday.toISOString().split('T')[0]
    },

    /**
     * 设置查询日期
     */
    setQueryDate(date) {
      this.queryDate = date
    },

    /**
     * 重置状态
     */
    resetState() {
      this.buyFXData = null
      this.sellFXData = null
      this.queryDate = null
    },
  },
})

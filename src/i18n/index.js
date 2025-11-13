// ExchangeOK 模块化翻译配置
// 此文件包含完整的模块化翻译系统
import { createI18n } from 'vue-i18n'

// 核心翻译文件（已迁移到模块化文件）
// 所有翻译现在都通过模块化文件加载

// 模块化翻译文件
import zhCN_Common from './modules/common/zh-CN.js'
import enUS_Common from './modules/common/en-US.js'
import thTH_Common from './modules/common/th-TH.js'

import zhCN_EOD from './modules/eod/zh-CN.js'
import enUS_EOD from './modules/eod/en-US.js'
import thTH_EOD from './modules/eod/th-TH.js'

// 处理EOD模块的default导出
const zhCN_EOD_processed = (zhCN_EOD.default || zhCN_EOD)
const enUS_EOD_processed = (enUS_EOD.default || enUS_EOD)
const thTH_EOD_processed = (thTH_EOD.default || thTH_EOD)

// 调试EOD模块内容
console.log('🔍 [i18n调试] thTH_EOD:', thTH_EOD)
console.log('🔍 [i18n调试] thTH_EOD_processed:', thTH_EOD_processed)
console.log('🔍 [i18n调试] thTH_EOD_processed.eod:', thTH_EOD_processed.eod)
console.log('🔍 [i18n调试] thTH_EOD_processed.eod?.adjust_difference:', thTH_EOD_processed.eod?.adjust_difference)

import zhCN_Exchange from './modules/exchange/zh-CN.js'
import enUS_Exchange from './modules/exchange/en-US.js'
import thTH_Exchange from './modules/exchange/th-TH.js'

import zhCN_Dashboard from './modules/dashboard/zh-CN.js'
import enUS_Dashboard from './modules/dashboard/en-US.js'
import thTH_Dashboard from './modules/dashboard/th-TH.js'

import zhCN_Rates from './modules/rates/zh-CN.js'
import enUS_Rates from './modules/rates/en-US.js'
import thTH_Rates from './modules/rates/th-TH.js'

import zhCN_UserMenu from './modules/user_menu/zh-CN.js'
import enUS_UserMenu from './modules/user_menu/en-US.js'
import thTH_UserMenu from './modules/user_menu/th-TH.js'

import zhCN_Footer from './modules/footer/zh-CN.js'
import enUS_Footer from './modules/footer/en-US.js'
import thTH_Footer from './modules/footer/th-TH.js'

import zhCN_Login from './modules/login/zh-CN.js'
import enUS_Login from './modules/login/en-US.js'
import thTH_Login from './modules/login/th-TH.js'

import zhCN_Balance from './modules/balance/zh-CN.js'
import enUS_Balance from './modules/balance/en-US.js'
import thTH_Balance from './modules/balance/th-TH.js'

import zhCN_Menu from './modules/menu/zh-CN.js'
import enUS_Menu from './modules/menu/en-US.js'
import thTH_Menu from './modules/menu/th-TH.js'

import zhCN_BalanceAdjust from './modules/balance_adjust/zh-CN.js'
import enUS_BalanceAdjust from './modules/balance_adjust/en-US.js'
import thTH_BalanceAdjust from './modules/balance_adjust/th-TH.js'

import zhCN_CurrencyManagement from './modules/currencyManagement/zh-CN.js'
import enUS_CurrencyManagement from './modules/currencyManagement/en-US.js'
import thTH_CurrencyManagement from './modules/currencyManagement/th-TH.js'

import zhCN_Currencies from './modules/currencies/zh-CN.js'
import enUS_Currencies from './modules/currencies/en-US.js'
import thTH_Currencies from './modules/currencies/th-TH.js'

import zhCN_Logs from './modules/logs/zh-CN.js'
import enUS_Logs from './modules/logs/en-US.js'
import thTH_Logs from './modules/logs/th-TH.js'

import zhCN_Reports from './modules/reports/zh-CN.js'
import enUS_Reports from './modules/reports/en-US.js'
import thTH_Reports from './modules/reports/th-TH.js'

import zhCN_SystemMaintenance from './modules/system_maintenance/zh-CN.js'
import enUS_SystemMaintenance from './modules/system_maintenance/en-US.js'
import thTH_SystemMaintenance from './modules/system_maintenance/th-TH.js'

import zhCN_QueriesModule from './modules/queries/zh-CN.js'
import enUS_QueriesModule from './modules/queries/en-US.js'
import thTH_QueriesModule from './modules/queries/th-TH.js'

// 处理ES模块的default导出
const zhCN_Queries = (zhCN_QueriesModule.default || zhCN_QueriesModule)
const enUS_Queries = (enUS_QueriesModule.default || enUS_QueriesModule)
const thTH_Queries = (thTH_QueriesModule.default || thTH_QueriesModule)

import zhCN_Standards from './modules/standards/zh-CN.js'
import enUS_Standards from './modules/standards/en-US.js'
import thTH_Standards from './modules/standards/th-TH.js'

import zhCN_Transactions from './modules/transactions/zh-CN.js'
import enUS_Transactions from './modules/transactions/en-US.js'
import thTH_Transactions from './modules/transactions/th-TH.js'

import zhCN_Denominations from './modules/denominations/zh-CN.js'
import enUS_Denominations from './modules/denominations/en-US.js'
import thTH_Denominations from './modules/denominations/th-TH.js'

import zhCN_Profile from './modules/profile/zh-CN.js'
import enUS_Profile from './modules/profile/en-US.js'
import thTH_Profile from './modules/profile/th-TH.js'

import zhCN_Reversals from './modules/reversals/zh-CN.js'
import enUS_Reversals from './modules/reversals/en-US.js'
import thTH_Reversals from './modules/reversals/th-TH.js'

import zhCN_ReversalQuery from './modules/reversal_query/zh-CN.js'
import enUS_ReversalQuery from './modules/reversal_query/en-US.js'


import thTH_ReversalQuery from './modules/reversal_query/th-TH.js'

import zhCN_LocalStockQuery from './modules/local_stock_query/zh-CN.js'
import enUS_LocalStockQuery from './modules/local_stock_query/en-US.js'
import thTH_LocalStockQuery from './modules/local_stock_query/th-TH.js'

import zhCN_BalanceAdjustQuery from './modules/balance_adjust_query/zh-CN.js'
import enUS_BalanceAdjustQuery from './modules/balance_adjust_query/en-US.js'
import thTH_BalanceAdjustQuery from './modules/balance_adjust_query/th-TH.js'

import zhCN_Countries from './modules/countries/zh-CN.js'
import enUS_Countries from './modules/countries/en-US.js'
import thTH_Countries from './modules/countries/th-TH.js'

import zhCN_LogManagement from './modules/logManagement/zh-CN.js'
import enUS_LogManagement from './modules/logManagement/en-US.js'
import thTH_LogManagement from './modules/logManagement/th-TH.js'

import zhCN_Auth from './modules/auth/zh-CN.js'
import enUS_Auth from './modules/auth/en-US.js'
import thTH_Auth from './modules/auth/th-TH.js'

import zhCN_DataClear from './modules/data_clear/zh-CN.js'
import enUS_DataClear from './modules/data_clear/en-US.js'
import thTH_DataClear from './modules/data_clear/th-TH.js'

import zhCN_App from './modules/app/zh-CN.js'
import enUS_App from './modules/app/en-US.js'
import thTH_App from './modules/app/th-TH.js'

import zhCN_AMLO from './modules/amlo/zh-CN.js'
import enUS_AMLO from './modules/amlo/en-US.js'
import thTH_AMLO from './modules/amlo/th-TH.js'

import zhCN_BOT from './modules/bot/zh-CN.js'
import enUS_BOT from './modules/bot/en-US.js'
import thTH_BOT from './modules/bot/th-TH.js'

import zhCN_Compliance from './modules/compliance/zh-CN.js'
import enUS_Compliance from './modules/compliance/en-US.js'
import thTH_Compliance from './modules/compliance/th-TH.js'

import zhCN_Transaction from './modules/transaction/zh-CN.js'
import enUS_Transaction from './modules/transaction/en-US.js'
import thTH_Transaction from './modules/transaction/th-TH.js'

import zhCN_Reservation from './modules/reservation/zh-CN.js'
import enUS_Reservation from './modules/reservation/en-US.js'
import thTH_Reservation from './modules/reservation/th-TH.js'

import zhCN_CustomerHistory from './modules/customer_history/zh-CN.js'
import enUS_CustomerHistory from './modules/customer_history/en-US.js'
import thTH_CustomerHistory from './modules/customer_history/th-TH.js'

// 改进的深度合并函数
function deepMerge(...sources) {
  if (sources.length === 0) return {}
  if (sources.length === 1) return sources[0]
  
  const result = {}
  
  for (const source of sources) {
    if (!source || typeof source !== 'object') continue
    
    for (const key in source) {
      if (Object.prototype.hasOwnProperty.call(source, key)) {
        if (
          source[key] && 
          typeof source[key] === 'object' && 
          !Array.isArray(source[key]) &&
          result[key] && 
          typeof result[key] === 'object' && 
          !Array.isArray(result[key])
        ) {
          result[key] = deepMerge(result[key], source[key])
        } else {
          result[key] = source[key]
        }
      }
    }
  }
  
  return result
}

// 调试合并过程
function debugMerge(moduleName, moduleData, result) {
  console.log(`- 合并${moduleName}模块:`, moduleData ? '成功' : '失败')
  if (moduleData) {
    console.log(`- ${moduleName}模块键:`, Object.keys(moduleData))
    console.log(`- 合并后${moduleName}键存在:`, moduleName in result)
  }
}

// 合并翻译文件
const zhCN_merged = deepMerge(zhCN_Common, zhCN_Dashboard, zhCN_EOD_processed, zhCN_Exchange, zhCN_Rates, zhCN_UserMenu, zhCN_Footer, zhCN_Login, zhCN_Balance, zhCN_Menu, zhCN_BalanceAdjust, zhCN_CurrencyManagement, zhCN_Currencies, zhCN_Countries, zhCN_Logs, zhCN_Reports, zhCN_SystemMaintenance, zhCN_Queries, zhCN_Standards, zhCN_Transactions, zhCN_Reversals, zhCN_ReversalQuery, zhCN_LocalStockQuery, zhCN_BalanceAdjustQuery, zhCN_LogManagement, zhCN_Auth, zhCN_DataClear, zhCN_App, zhCN_Profile, zhCN_AMLO, zhCN_BOT, zhCN_Compliance, zhCN_Transaction, zhCN_Reservation, zhCN_CustomerHistory)

// 调试合并过程
if (process.env.NODE_ENV === 'development') {
  console.log('=== 合并调试信息 ===')
  debugMerge('queries', zhCN_Queries, zhCN_merged)
  debugMerge('eod', zhCN_EOD_processed, zhCN_merged)
  debugMerge('exchange', zhCN_Exchange, zhCN_merged)
  debugMerge('common', zhCN_Common, zhCN_merged)
  debugMerge('app', zhCN_App, zhCN_merged)
  console.log('=== 合并调试信息结束 ===')
}

const messages = {
  'zh-CN': zhCN_merged,
  'zh': deepMerge(zhCN_Common, zhCN_Dashboard, { ...zhCN_EOD_processed }, zhCN_Exchange, zhCN_Rates, zhCN_UserMenu, zhCN_Footer, zhCN_Login, zhCN_Balance, zhCN_Menu, zhCN_BalanceAdjust, zhCN_CurrencyManagement, zhCN_Currencies, zhCN_Countries, zhCN_Logs, zhCN_Reports, zhCN_SystemMaintenance, zhCN_Queries, zhCN_Standards, zhCN_Transactions, zhCN_Denominations, zhCN_Reversals, zhCN_ReversalQuery, zhCN_LocalStockQuery, zhCN_BalanceAdjustQuery, zhCN_LogManagement, zhCN_Auth, zhCN_DataClear, zhCN_App, zhCN_Profile, zhCN_AMLO, zhCN_BOT, zhCN_Compliance, zhCN_Transaction, zhCN_Reservation, zhCN_CustomerHistory),
  'en-US': deepMerge(enUS_Common, enUS_Dashboard, { ...enUS_EOD_processed }, enUS_Exchange, enUS_Rates, enUS_UserMenu, enUS_Footer, enUS_Login, enUS_Balance, enUS_Menu, enUS_BalanceAdjust, enUS_CurrencyManagement, enUS_Currencies, enUS_Countries, enUS_Logs, enUS_Reports, enUS_SystemMaintenance, enUS_Queries, enUS_Standards, enUS_Transactions, enUS_Denominations, enUS_Reversals, enUS_ReversalQuery, enUS_LocalStockQuery, enUS_BalanceAdjustQuery, enUS_LogManagement, enUS_Auth, enUS_DataClear, enUS_App, enUS_Profile, enUS_AMLO, enUS_BOT, enUS_Compliance, enUS_Transaction, enUS_Reservation, enUS_CustomerHistory),
  'en': deepMerge(enUS_Common, enUS_Dashboard, { ...enUS_EOD_processed }, enUS_Exchange, enUS_Rates, enUS_UserMenu, enUS_Footer, enUS_Login, enUS_Balance, enUS_Menu, enUS_BalanceAdjust, enUS_CurrencyManagement, enUS_Currencies, enUS_Countries, enUS_Logs, enUS_Reports, enUS_SystemMaintenance, enUS_Queries, enUS_Standards, enUS_Transactions, enUS_Denominations, enUS_Reversals, enUS_ReversalQuery, enUS_LocalStockQuery, enUS_BalanceAdjustQuery, enUS_LogManagement, enUS_Auth, enUS_DataClear, enUS_App, enUS_Profile, enUS_AMLO, enUS_BOT, enUS_Compliance, enUS_Transaction, enUS_Reservation, enUS_CustomerHistory),
  'th-TH': deepMerge(thTH_Common, thTH_Dashboard, thTH_EOD_processed, thTH_Exchange, thTH_Rates, thTH_UserMenu, thTH_Footer, thTH_Login, thTH_Balance, thTH_Menu, thTH_BalanceAdjust, thTH_CurrencyManagement, thTH_Currencies, thTH_Countries, thTH_Logs, thTH_Reports, thTH_SystemMaintenance, thTH_Queries, thTH_Standards, thTH_Transactions, thTH_Denominations, thTH_Reversals, thTH_ReversalQuery, thTH_LocalStockQuery, thTH_BalanceAdjustQuery, thTH_LogManagement, thTH_Auth, thTH_DataClear, thTH_App, thTH_Profile, thTH_AMLO, thTH_BOT, thTH_Compliance, thTH_Transaction, thTH_Reservation, thTH_CustomerHistory),
  'th': deepMerge(thTH_Common, thTH_Dashboard, thTH_EOD_processed, thTH_Exchange, thTH_Rates, thTH_UserMenu, thTH_Footer, thTH_Login, thTH_Balance, thTH_Menu, thTH_BalanceAdjust, thTH_CurrencyManagement, thTH_Currencies, thTH_Countries, thTH_Logs, thTH_Reports, thTH_SystemMaintenance, thTH_Queries, thTH_Standards, thTH_Transactions, thTH_Denominations, thTH_Reversals, thTH_ReversalQuery, thTH_LocalStockQuery, thTH_BalanceAdjustQuery, thTH_LogManagement, thTH_Auth, thTH_DataClear, thTH_App, thTH_Profile, thTH_AMLO, thTH_BOT, thTH_Compliance, thTH_Transaction, thTH_Reservation, thTH_CustomerHistory)
}

// 调试th-TH语言包合并结果
console.log('🔍 [i18n调试] th-TH messages.eod:', messages['th-TH'].eod)
console.log('🔍 [i18n调试] th-TH messages.eod?.adjust_difference:', messages['th-TH'].eod?.adjust_difference)
console.log('🔍 [i18n调试] th messages.eod:', messages['th'].eod)
console.log('🔍 [i18n调试] th messages.eod?.adjust_difference:', messages['th'].eod?.adjust_difference)

// 调试输出（生产环境可移除）
if (process.env.NODE_ENV === 'development') {
  console.log('i18n模块加载状态:')
  console.log('- 基础模块加载完成')
  console.log('- Common模块加载完成')
  console.log('- EOD模块加载完成')
  console.log('- Exchange模块加载完成')
  console.log('- Reports模块加载完成')
  console.log('- 中文翻译包含common模块:', 'common' in messages['zh-CN'])
  console.log('- 中文翻译包含dashboard模块:', 'dashboard' in messages['zh-CN'])
  console.log('- 中文翻译包含eod模块:', 'eod' in messages['zh-CN'])
  console.log('- 中文翻译包含exchange模块:', 'exchange' in messages['zh-CN'])
  console.log('- 中文翻译包含rates模块:', 'rates' in messages['zh-CN'])
  console.log('- 中文翻译包含user_menu模块:', 'user_menu' in messages['zh-CN'])
  console.log('- 中文翻译包含footer模块:', 'footer' in messages['zh-CN'])
  console.log('- 中文翻译包含login模块:', 'login' in messages['zh-CN'])
  console.log('- 中文翻译包含balance模块:', 'balance' in messages['zh-CN'])
  console.log('- 中文翻译包含menu模块:', 'menu' in messages['zh-CN'])
  console.log('- 中文翻译包含balance_adjust模块:', 'balance_adjust' in messages['zh-CN'])
  console.log('- 中文翻译包含currencyManagement模块:', 'currencyManagement' in messages['zh-CN'])
  console.log('- 中文翻译包含currencies模块:', 'currencies' in messages['zh-CN'])
  console.log('- 中文翻译包含logs模块:', 'logs' in messages['zh-CN'])
  console.log('- 中文翻译包含queries模块:', 'queries' in messages['zh-CN'])
  console.log('- 中文翻译包含app模块:', 'app' in messages['zh-CN'])
  
  // 检查exchange模块的具体内容
  if ('exchange' in messages['zh-CN']) {
    console.log('- exchange模块key数量:', Object.keys(messages['zh-CN'].exchange).length)
    console.log('- exchange.title:', messages['zh-CN'].exchange.title)
    console.log('- exchange.select_foreign_currency:', messages['zh-CN'].exchange.select_foreign_currency)
  } else {
    console.log('- exchange模块合并失败!')
    console.log('- 检查zhCN_Exchange导入:', zhCN_Exchange)
  }
  
  // 检查queries模块的具体内容
  if ('queries' in messages['zh-CN']) {
    console.log('- queries模块key数量:', Object.keys(messages['zh-CN'].queries).length)
    console.log('- queries模块包含initial_balance:', 'initial_balance' in messages['zh-CN'].queries)
    if ('initial_balance' in messages['zh-CN'].queries) {
      console.log('- initial_balance模块key数量:', Object.keys(messages['zh-CN'].queries.initial_balance).length)
      console.log('- initial_balance.title:', messages['zh-CN'].queries.initial_balance.title)
      console.log('- initial_balance.table:', messages['zh-CN'].queries.initial_balance.table ? '存在' : '不存在')
    } else {
      console.log('- initial_balance模块不存在!')
    }
  } else {
    console.log('- queries模块合并失败!')
    console.log('- 检查zhCN_Queries导入:', zhCN_Queries)
    console.log('- zhCN_Queries类型:', typeof zhCN_Queries)
    console.log('- zhCN_Queries是否为对象:', typeof zhCN_Queries === 'object')
    console.log('- zhCN_Queries键:', Object.keys(zhCN_Queries))
    console.log('- zhCN_Queries包含initial_balance:', 'initial_balance' in zhCN_Queries)
    if ('initial_balance' in zhCN_Queries) {
      console.log('- initial_balance.title:', zhCN_Queries.initial_balance.title)
    }
  }
  
  // 检查app模块的具体内容
  if ('app' in messages['zh-CN']) {
    console.log('- app模块key数量:', Object.keys(messages['zh-CN'].app).length)
    console.log('- app模块包含home:', 'home' in messages['zh-CN'].app)
    if ('home' in messages['zh-CN'].app) {
      console.log('- home模块key数量:', Object.keys(messages['zh-CN'].app.home).length)
      console.log('- home.title:', messages['zh-CN'].app.home.title)
      console.log('- home.local_balance:', messages['zh-CN'].app.home.local_balance)
    } else {
      console.log('- home模块不存在!')
    }
  } else {
    console.log('- app模块合并失败!')
    console.log('- 检查zhCN_App导入:', zhCN_App)
    console.log('- zhCN_App类型:', typeof zhCN_App)
    console.log('- zhCN_App是否为对象:', typeof zhCN_App === 'object')
    console.log('- zhCN_App键:', Object.keys(zhCN_App))
  }
  
  // 检查EOD模块的具体内容
  if ('eod' in messages['zh-CN']) {
    console.log('- EOD模块key数量:', Object.keys(messages['zh-CN'].eod).length)
    console.log('- EOD模块包含step5:', 'step5' in messages['zh-CN'].eod)
    if ('step5' in messages['zh-CN'].eod) {
      console.log('- step5模块key数量:', Object.keys(messages['zh-CN'].eod.step5).length)
      console.log('- step5.title:', messages['zh-CN'].eod.step5.title)
      console.log('- step5.verification_overview:', messages['zh-CN'].eod.step5.verification_overview)
      console.log('- step5.income_statistics_title:', messages['zh-CN'].eod.step5.income_statistics_title)
    } else {
      console.log('- step5模块不存在!')
    }
    console.log('- EOD模块包含step4:', 'step4' in messages['zh-CN'].eod)
    if ('step4' in messages['zh-CN'].eod) {
      console.log('- step4.total_currencies:', messages['zh-CN'].eod.step4.total_currencies)
      console.log('- step4.matched_currencies:', messages['zh-CN'].eod.step4.matched_currencies)
    }
    console.log('- EOD模块包含income_statistics_title:', 'income_statistics_title' in messages['zh-CN'].eod)
    console.log('- EOD模块包含income:', 'income' in messages['zh-CN'].eod)
    console.log('- EOD模块包含spread_income:', 'spread_income' in messages['zh-CN'].eod)
    console.log('- EOD模块包含currency_count:', 'currency_count' in messages['zh-CN'].eod)
  } else {
    console.log('- EOD模块合并失败!')
    console.log('- 检查zhCN_EOD_processed导入:', zhCN_EOD_processed)
    console.log('- zhCN_EOD_processed类型:', typeof zhCN_EOD_processed)
    console.log('- zhCN_EOD_processed是否为对象:', typeof zhCN_EOD_processed === 'object')
    console.log('- zhCN_EOD_processed键:', Object.keys(zhCN_EOD_processed))
    console.log('- zhCN_EOD_processed包含eod:', 'eod' in zhCN_EOD_processed)
  }
}

const i18n = createI18n({
  legacy: false,
  locale: localStorage.getItem('language') || 'zh-CN',
  fallbackLocale: false, // 禁用fallback，避免回退到中文
  messages,
  globalInjection: true
})

export default i18n 
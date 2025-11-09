// 币种和国家名称i18n辅助工具
// 使用i18n的currencies模块来获取翻译，替代原有的currencyTranslator.js
import i18n from '@/i18n'

/**
 * 获取货币的多语言名称
 * @param {string} currencyCode - 货币代码 (如 'USD', 'EUR')
 * @param {string} lang - 语言代码 (如 'zh', 'en', 'th')，可选，默认使用当前i18n语言
 * @returns {string} 货币的多语言名称
 */
export function getCurrencyName(currencyCode, lang = null) {
  if (!currencyCode) return ''
  
  // 安全地访问i18n对象
  if (!i18n?.global) {
    console.warn('i18n.global not available, returning currency code')
    return currencyCode
  }
  
  // 确定要使用的语言
  const currentLang = lang || getCurrentLanguage()
  
  try {
    // 使用i18n的currencies模块获取翻译
    const translation = i18n.global.t(`currencies.${currencyCode}`, currentLang)
    
    // 如果找到了翻译，返回翻译结果
    if (translation && translation !== `currencies.${currencyCode}`) {
      return translation
    }
  } catch (error) {
    console.warn(`Failed to get currency translation for ${currencyCode}:`, error)
  }
  
  // 如果没有找到翻译，返回货币代码
  return currencyCode
}

/**
 * 获取国家的多语言名称
 * @param {string} countryCode - 国家代码 (如 'CN', 'US', 'TH')
 * @param {string} lang - 语言代码 (如 'zh', 'en', 'th')，可选，默认使用当前i18n语言
 * @returns {string} 国家的多语言名称
 */
export function getCountryName(countryCode, lang = null) {
  if (!countryCode) return ''
  
  // 确定要使用的语言
  const currentLang = lang || getCurrentLanguage()
  
  try {
    // 使用i18n的currencies模块获取翻译
    const translation = i18n.global.t(`currencies.${countryCode}`, currentLang)
    
    // 如果找到了翻译，返回翻译结果
    if (translation && translation !== `currencies.${countryCode}`) {
      return translation
    }
  } catch (error) {
    console.warn(`Failed to get country translation for ${countryCode}:`, error)
  }
  
  // 如果没有找到翻译，返回国家代码
  return countryCode
}

/**
 * 获取当前语言代码
 * @returns {string} 当前语言代码
 */
function getCurrentLanguage() {
  // 安全地访问i18n对象
  if (!i18n?.global?.locale?.value) {
    console.warn('i18n.global.locale.value not available, using default language')
    return 'zh' // 默认中文
  }
  
  const currentLocale = i18n.global.locale.value
  
  // 语言代码转换：前端使用zh-CN/en-US/th-TH，转换为zh/en/th
  const langMap = {
    'zh-CN': 'zh',
    'en-US': 'en', 
    'th-TH': 'th',
    'zh': 'zh',    // 兼容性
    'en': 'en',    // 兼容性
    'th': 'th'     // 兼容性
  }
  
  return langMap[currentLocale] || 'zh' // 默认中文
}

/**
 * 批量获取货币名称列表
 * @param {Array} currencyCodes - 货币代码数组
 * @param {string} lang - 语言代码，可选
 * @returns {Array} 货币名称数组
 */
export function getCurrencyNames(currencyCodes, lang = null) {
  if (!Array.isArray(currencyCodes)) return []
  
  return currencyCodes.map(code => getCurrencyName(code, lang))
}

/**
 * 批量获取国家名称列表
 * @param {Array} countryCodes - 国家代码数组
 * @param {string} lang - 语言代码，可选
 * @returns {Array} 国家名称数组
 */
export function getCountryNames(countryCodes, lang = null) {
  if (!Array.isArray(countryCodes)) return []
  
  return countryCodes.map(code => getCountryName(code, lang))
}

/**
 * 检查货币代码是否有翻译
 * @param {string} currencyCode - 货币代码
 * @param {string} lang - 语言代码，可选
 * @returns {boolean} 是否有翻译
 */
export function hasCurrencyTranslation(currencyCode, lang = null) {
  if (!currencyCode) return false
  
  const translation = getCurrencyName(currencyCode, lang)
  return translation !== currencyCode
}

/**
 * 检查国家代码是否有翻译
 * @param {string} countryCode - 国家代码
 * @param {string} lang - 语言代码，可选
 * @returns {boolean} 是否有翻译
 */
export function hasCountryTranslation(countryCode, lang = null) {
  if (!countryCode) return false
  
  const translation = getCountryName(countryCode, lang)
  return translation !== countryCode
} 
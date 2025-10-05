// 货币翻译工具 - 统一处理所有货币名称的多语言显示
// 更新版本：支持从后端API动态加载，优先使用i18n的currencies模块，保持向后兼容性
import i18n from '@/i18n';

// 国家代码到多语言名称的映射
const COUNTRY_TRANSLATIONS = {
  'NZ': {
    'zh': '新西兰',
    'en': 'New Zealand',
    'th': 'นิวซีแลนด์'
  },
  'PH': {
    'zh': '菲律宾',
    'en': 'Philippines',
    'th': 'ฟิลิปปินส์'
  },
  'RU': {
    'zh': '俄罗斯',
    'en': 'Russia',
    'th': 'รัสเซีย'
  },
  'SE': {
    'zh': '瑞典',
    'en': 'Sweden',
    'th': 'สวีเดน'
  },
  'SG': {
    'zh': '新加坡',
    'en': 'Singapore',
    'th': 'สิงคโปร์'
  },
  'US': {
    'zh': '美国',
    'en': 'United States',
    'th': 'สหรัฐอเมริกา'
  },
  'CN': {
    'zh': '中国',
    'en': 'China',
    'th': 'จีน'
  },
  'TH': {
    'zh': '泰国',
    'en': 'Thailand',
    'th': 'ไทย'
  },
  'JP': {
    'zh': '日本',
    'en': 'Japan',
    'th': 'ญี่ปุ่น'
  },
  'GB': {
    'zh': '英国',
    'en': 'United Kingdom',
    'th': 'สหราชอาณาจักร'
  },
  'EU': {
    'zh': '欧盟',
    'en': 'European Union',
    'th': 'สหภาพยุโรป'
  },
  'AU': {
    'zh': '澳大利亚',
    'en': 'Australia',
    'th': 'ออสเตรเลีย'
  },
  'CA': {
    'zh': '加拿大',
    'en': 'Canada',
    'th': 'แคนาดา'
  },
  'CH': {
    'zh': '瑞士',
    'en': 'Switzerland',
    'th': 'สวิตเซอร์แลนด์'
  },
  'NO': {
    'zh': '挪威',
    'en': 'Norway',
    'th': 'นอร์เวย์'
  },
  'DK': {
    'zh': '丹麦',
    'en': 'Denmark',
    'th': 'เดนมาร์ก'
  },
  'ZA': {
    'zh': '南非',
    'en': 'South Africa',
    'th': 'แอฟริกาใต้'
  },
  'BR': {
    'zh': '巴西',
    'en': 'Brazil',
    'th': 'บราซิล'
  },
  'IN': {
    'zh': '印度',
    'en': 'India',
    'th': 'อินเดีย'
  },
  'SA': {
    'zh': '沙特阿拉伯',
    'en': 'Saudi Arabia',
    'th': 'ซาอุดีอาระเบีย'
  },
  'AE': {
    'zh': '阿联酋',
    'en': 'United Arab Emirates',
    'th': 'สหรัฐอาหรับเอมิเรตส์'
  },
  'TR': {
    'zh': '土耳其',
    'en': 'Turkey',
    'th': 'ตุรกี'
  },
  'TW': {
    'zh': '台湾',
    'en': 'Taiwan',
    'th': 'ไต้หวัน'
  },
  'BH': {
    'zh': '巴林',
    'en': 'Bahrain',
    'th': 'บาห์เรน'
  }
};

// 保留原有的货币代码到多语言名称的映射作为备用
const CURRENCY_TRANSLATIONS = {
  // 主要货币
  'USD': {
    'zh': '美元',
    'en': 'US Dollar', 
    'th': 'ดอลลาร์สหรัฐ'
  },
  'EUR': {
    'zh': '欧元',
    'en': 'Euro',
    'th': 'ยูโร'
  },
  'GBP': {
    'zh': '英镑', 
    'en': 'British Pound',
    'th': 'ปอนด์อังกฤษ'
  },
  'JPY': {
    'zh': '日元',
    'en': 'Japanese Yen',
    'th': 'เยนญี่ปุ่น'
  },
  'THB': {
    'zh': '泰铢',
    'en': 'Thai Baht',
    'th': 'บาทไทย'
  },
  'CNY': {
    'zh': '人民币',
    'en': 'Chinese Yuan',
    'th': 'หยวนจีน'
  },
  'HKD': {
    'zh': '港币',
    'en': 'Hong Kong Dollar', 
    'th': 'ดอลลาร์ฮ่องกง'
  },
  'SGD': {
    'zh': '新加坡元',
    'en': 'Singapore Dollar',
    'th': 'ดอลลาร์สิงคโปร์'
  },
  'KRW': {
    'zh': '韩元',
    'en': 'South Korean Won',
    'th': 'วอนเกาหลีใต้'
  },
  'MYR': {
    'zh': '马来西亚林吉特',
    'en': 'Malaysian Ringgit',
    'th': 'ริงกิตมาเลเซีย'
  },
  'CAD': {
    'zh': '加拿大元',
    'en': 'Canadian Dollar',
    'th': 'ดอลลาร์แคนาดา'
  },
  'AUD': {
    'zh': '澳大利亚元',
    'en': 'Australian Dollar',
    'th': 'ดอลลาร์ออสเตรเลีย'
  },
  'CHF': {
    'zh': '瑞士法郎',
    'en': 'Swiss Franc',
    'th': 'ฟรังก์สวิส'
  },
  'SEK': {
    'zh': '瑞典克朗',
    'en': 'Swedish Krona',
    'th': 'โครนาสวีเดน'
  },
  'NOK': {
    'zh': '挪威克朗',
    'en': 'Norwegian Krone',
    'th': 'โครนานอร์เวย์'
  },
  'DKK': {
    'zh': '丹麦克朗',
    'en': 'Danish Krone',
    'th': 'โครนาเดนมาร์ก'
  },
  'NZD': {
    'zh': '新西兰元',
    'en': 'New Zealand Dollar',
    'th': 'ดอลลาร์นิวซีแลนด์'
  },
  'ZAR': {
    'zh': '南非兰特',
    'en': 'South African Rand',
    'th': 'แรนด์แอฟริกาใต้'
  },
  'BRL': {
    'zh': '巴西雷亚尔',
    'en': 'Brazilian Real',
    'th': 'เรียลบราซิล'
  },
  'RUB': {
    'zh': '俄罗斯卢布',
    'en': 'Russian Ruble',
    'th': 'รูเบิลรัสเซีย'
  },
  'INR': {
    'zh': '印度卢比',
    'en': 'Indian Rupee',
    'th': 'รูปีอินเดีย'
  },
  'SAR': {
    'zh': '沙特里亚尔',
    'en': 'Saudi Riyal',
    'th': 'ริยัลซาอุดิอาระเบีย'
  },
  'AED': {
    'zh': '阿联酋迪拉姆',
    'en': 'UAE Dirham',
    'th': 'เดอร์แฮมสหรัฐอาหรับเอมิเรตส์'
  },
  'TRY': {
    'zh': '土耳其里拉',
    'en': 'Turkish Lira',
    'th': 'ลีราตุรกี'
  },
  'TWD': {
    'zh': '新台币',
    'en': 'New Taiwan Dollar',
    'th': 'ดอลลาร์ไต้หวันใหม่'
  },
  'BHD': {
    'zh': '巴林第纳尔',
    'en': 'Bahraini Dinar',
    'th': 'ดีนาร์บาห์เรน'
  }
  // 可以继续添加更多货币...
};

// 动态加载的翻译缓存
let dynamicTranslations = null;
let isLoadingTranslations = false;

/**
 * 从后端API动态加载币种翻译
 * @returns {Promise<object>} 翻译对象
 */
export async function loadCurrencyTranslationsFromAPI() {
  if (isLoadingTranslations) {
    // 如果正在加载，等待完成
    return new Promise((resolve) => {
      const checkLoaded = () => {
        if (!isLoadingTranslations) {
          resolve(dynamicTranslations);
        } else {
          setTimeout(checkLoaded, 100);
        }
      };
      checkLoaded();
    });
  }

  if (dynamicTranslations) {
    // 如果已经加载过，直接返回缓存
    return dynamicTranslations;
  }

  isLoadingTranslations = true;

  try {
    // 获取认证token
    const token = localStorage.getItem('token');
    if (!token) {
      console.warn('未找到认证token，跳过API加载币种翻译');
      return null;
    }

    // 调用后端API获取币种翻译
    const response = await fetch('/api/system/currency-translations', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (response.ok) {
      const data = await response.json();
      if (data.success && data.translations) {
        dynamicTranslations = data.translations;
        console.log('✅ 成功从API加载币种翻译:', Object.keys(dynamicTranslations).length, '个币种');
        return dynamicTranslations;
      }
    }
  } catch (error) {
    console.warn('从API加载币种翻译失败:', error);
  } finally {
    isLoadingTranslations = false;
  }

  return null;
}

/**
 * 清除动态翻译缓存，强制重新加载
 */
export function clearCurrencyTranslationsCache() {
  dynamicTranslations = null;
  console.log('🗑️ 已清除币种翻译缓存');
}

/**
 * 获取货币的多语言名称
 * @param {string} currencyCode - 货币代码 (如 'USD', 'EUR')
 * @param {string} lang - 语言代码 (如 'zh', 'en', 'th')，可选，默认使用当前i18n语言
 * @param {object} apiCurrencyNames - 从API获取的货币名称映射，可选
 * @returns {string} 货币的多语言名称
 */
export function getCurrencyName(currencyCode, lang = null, apiCurrencyNames = null) {
  if (!currencyCode) return '';
  
  // 确定要使用的语言
  const currentLang = lang || getCurrentLanguage();
  
  // 1. 优先使用传入的API货币名称
  if (apiCurrencyNames && apiCurrencyNames[currencyCode]) {
    const apiNames = apiCurrencyNames[currencyCode];
    if (apiNames[currentLang]) {
      return apiNames[currentLang];
    }
  }
  
  // 2. 使用动态加载的翻译
  if (dynamicTranslations && dynamicTranslations[currencyCode]) {
    const translations = dynamicTranslations[currencyCode];
    if (translations[currentLang]) {
      return translations[currentLang];
    }
  }
  
  // 3. 尝试使用i18n的currencies模块获取翻译（仅对已知币种）
  const knownCurrencies = ['USD', 'EUR', 'GBP', 'JPY', 'THB', 'CNY', 'HKD', 'SGD', 'KRW', 'MYR', 'CAD', 'AUD', 'CHF', 'SEK', 'NOK', 'DKK', 'NZD', 'ZAR', 'BRL', 'RUB', 'INR', 'SAR', 'AED', 'TRY', 'TWD', 'BHD', 'BND', 'PHP', 'IDR', 'VND', 'LAK', 'KHR', 'MMK', 'BDT', 'PKR', 'LKR', 'NPR', 'MNT', 'KZT', 'UZS', 'KGS', 'TJS', 'TMT', 'AFN', 'IRR', 'IQD', 'SYP', 'LBP', 'JOD', 'ILS', 'QAR', 'KWD'];
  if (knownCurrencies.includes(currencyCode)) {
    try {
      const i18nTranslation = i18n.global.t(`currencies.${currencyCode}`, currentLang);
      if (i18nTranslation && i18nTranslation !== `currencies.${currencyCode}`) {
        return i18nTranslation;
      }
    } catch (error) {
      // 静默处理翻译错误
    }
  }
  
  // 4. 使用本地配置的货币翻译作为备用
  if (CURRENCY_TRANSLATIONS[currencyCode]) {
    const translations = CURRENCY_TRANSLATIONS[currencyCode];
    return translations[currentLang] || translations['zh'] || currencyCode;
  }
  
  // 5. 如果没有找到翻译，返回货币代码
  return currencyCode;
}

/**
 * 获取当前语言代码
 * @returns {string} 当前语言代码
 */
function getCurrentLanguage() {
  const currentLocale = i18n.global.locale.value;
  
  // 语言代码转换：前端使用zh-CN/en-US/th-TH，后端API使用zh/en/th
  const langMap = {
    'zh-CN': 'zh',
    'en-US': 'en', 
    'th-TH': 'th',
    'zh': 'zh',    // 兼容性
    'en': 'en',    // 兼容性
    'th': 'th'     // 兼容性
  };
  
  return langMap[currentLocale] || 'zh'; // 默认中文
}

/**
 * 获取国家的多语言名称
 * @param {string} countryCode - 国家代码 (如 'CN', 'US', 'TH')
 * @param {string} lang - 语言代码 (如 'zh', 'en', 'th')，可选，默认使用当前i18n语言
 * @returns {string} 国家的多语言名称
 */
export function getCountryName(countryCode, lang = null) {
  if (!countryCode) return '';
  
  // 确定要使用的语言
  const currentLang = lang || getCurrentLanguage();
  
  // 1. 使用本地配置的国家翻译
  if (COUNTRY_TRANSLATIONS[countryCode]) {
    const translations = COUNTRY_TRANSLATIONS[countryCode];
    if (translations[currentLang]) {
      return translations[currentLang];
    }
  }
  
  // 2. 尝试使用i18n的currencies模块获取翻译（仅对已知国家）
  const knownCountries = ['NZ', 'PH', 'RU', 'SE', 'SG', 'US', 'CN', 'TH', 'JP', 'GB', 'EU', 'AU', 'CA', 'CH', 'NO', 'DK', 'ZA', 'BR', 'IN'];
  if (knownCountries.includes(countryCode)) {
    try {
      const i18nTranslation = i18n.global.t(`currencies.${countryCode}`, currentLang);
      if (i18nTranslation && i18nTranslation !== `currencies.${countryCode}`) {
        return i18nTranslation;
      }
    } catch (error) {
      // 静默处理翻译错误
    }
  }
  
  // 3. 如果没有找到翻译，返回国家代码
  return countryCode;
}

/**
 * 获取币种显示名称 - 根据是否为自定义币种决定显示方式
 * @param {string} currencyCode - 币种代码
 * @param {Object} currency - 币种对象，包含 custom_flag_filename 等字段
 * @param {string} lang - 语言代码，可选
 * @returns {string} 币种显示名称
 */
export function getCurrencyDisplayName(currencyCode, currency = null, lang = null) {
  if (!currencyCode) return '';
  
  // 检查是否是自定义币种（有custom_flag_filename）
  if (currency && currency.custom_flag_filename) {
    // console.log(`[自定义币种] ${currencyCode} 使用数据库名称: ${currency.currency_name}`);
    return currency.currency_name || currencyCode; // 直接使用数据库中的名称
  }
  
  // 预设币种使用翻译系统
  const currentLang = lang || getCurrentLanguage();
  const translatedName = getCurrencyName(currencyCode, currentLang, null);
  return translatedName || currencyCode;
}

/**
 * 批量获取多个货币的名称
 * @param {Array} currencyCodes - 货币代码数组
 * @param {string} lang - 语言代码，可选
 * @param {object} apiCurrencyNames - 从API获取的货币名称映射，可选
 * @returns {object} 货币代码到名称的映射对象
 */
export function getCurrencyNames(currencyCodes, lang = null, apiCurrencyNames = null) {
  const result = {};
  currencyCodes.forEach(code => {
    result[code] = getCurrencyName(code, lang, apiCurrencyNames);
  });
  return result;
}

/**
 * 检查是否支持指定货币的翻译
 * @param {string} currencyCode - 货币代码
 * @returns {boolean} 是否支持翻译
 */
export function isCurrencySupported(currencyCode) {
  return !!CURRENCY_TRANSLATIONS[currencyCode];
}

/**
 * 获取所有支持的货币代码
 * @returns {Array} 支持的货币代码数组
 */
export function getSupportedCurrencies() {
  return Object.keys(CURRENCY_TRANSLATIONS);
}

/**
 * 动态添加货币翻译
 * @param {string} currencyCode - 货币代码
 * @param {object} translations - 翻译对象，包含 'zh', 'en', 'th' 等语言
 * @example
 * addCurrencyTranslation('BTC', {
 *   'zh': '比特币',
 *   'en': 'Bitcoin',
 *   'th': 'บิตคอยน์'
 * });
 */
export function addCurrencyTranslation(currencyCode, translations) {
  if (!currencyCode || !translations) {
    console.warn('addCurrencyTranslation: 缺少必要参数');
    return false;
  }
  
  // 验证翻译对象格式
  const requiredLanguages = ['zh', 'en', 'th'];
  const hasValidTranslations = requiredLanguages.some(lang => translations[lang]);
  
  if (!hasValidTranslations) {
    console.warn(`addCurrencyTranslation: ${currencyCode} 缺少有效的翻译`);
    return false;
  }
  
  // 添加到本地翻译字典
  CURRENCY_TRANSLATIONS[currencyCode] = translations;
  
  console.log(`✅ 成功添加币种翻译: ${currencyCode}`, translations);
  return true;
}

/**
 * 批量添加货币翻译
 * @param {object} translationsMap - 翻译映射对象
 * @example
 * addCurrencyTranslations({
 *   'BTC': { 'zh': '比特币', 'en': 'Bitcoin', 'th': 'บิตคอยน์' },
 *   'ETH': { 'zh': '以太坊', 'en': 'Ethereum', 'th': 'อีเธอร์' }
 * });
 */
export function addCurrencyTranslations(translationsMap) {
  if (!translationsMap || typeof translationsMap !== 'object') {
    console.warn('addCurrencyTranslations: 参数必须是对象');
    return false;
  }
  
  let successCount = 0;
  let failCount = 0;
  
  Object.entries(translationsMap).forEach(([currencyCode, translations]) => {
    if (addCurrencyTranslation(currencyCode, translations)) {
      successCount++;
    } else {
      failCount++;
    }
  });
  
  console.log(`批量添加币种翻译完成: 成功 ${successCount} 个，失败 ${failCount} 个`);
  return { successCount, failCount };
}

/**
 * 获取所有已配置的货币代码列表
 * @returns {Array} 货币代码数组
 */
export function getConfiguredCurrencies() {
  return Object.keys(CURRENCY_TRANSLATIONS);
}

/**
 * 检查货币是否已配置翻译
 * @param {string} currencyCode - 货币代码
 * @returns {boolean} 是否已配置
 */
export function isCurrencyConfigured(currencyCode) {
  return currencyCode in CURRENCY_TRANSLATIONS;
}

export default {
  getCurrencyName,
  getCurrencyNames,
  isCurrencySupported,
  getSupportedCurrencies,
  addCurrencyTranslation,
  getCountryName,
  loadCurrencyTranslationsFromAPI,
  clearCurrencyTranslationsCache
}; 
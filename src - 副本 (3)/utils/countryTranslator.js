// 国家/地区翻译工具 - 统一处理所有国家/地区名称的多语言显示
import i18n from '@/i18n';

// 国家/地区名称到多语言名称的映射
const COUNTRY_TRANSLATIONS = {
  // 欧洲
  '欧盟': {
    'zh': '欧盟',
    'en': 'European Union',
    'th': 'สหภาพยุโรป'
  },
  '英国': {
    'zh': '英国',
    'en': 'United Kingdom',
    'th': 'สหราชอาณาจักร'
  },
  '瑞士': {
    'zh': '瑞士',
    'en': 'Switzerland',
    'th': 'สวิตเซอร์แลนด์'
  },
  '瑞典': {
    'zh': '瑞典',
    'en': 'Sweden',
    'th': 'สวีเดน'
  },
  '挪威': {
    'zh': '挪威',
    'en': 'Norway',
    'th': 'นอร์เวย์'
  },
  '丹麦': {
    'zh': '丹麦',
    'en': 'Denmark',
    'th': 'เดนมาร์ก'
  },
  '俄罗斯': {
    'zh': '俄罗斯',
    'en': 'Russia',
    'th': 'รัสเซีย'
  },
  
  // 亚洲
  '中国': {
    'zh': '中国',
    'en': 'China',
    'th': 'จีน'
  },
  '日本': {
    'zh': '日本',
    'en': 'Japan',
    'th': 'ญี่ปุ่น'
  },
  '韩国': {
    'zh': '韩国',
    'en': 'South Korea',
    'th': 'เกาหลีใต้'
  },
  '泰国': {
    'zh': '泰国',
    'en': 'Thailand',
    'th': 'ประเทศไทย'
  },
  '印度': {
    'zh': '印度',
    'en': 'India',
    'th': 'อินเดีย'
  },
  '新加坡': {
    'zh': '新加坡',
    'en': 'Singapore',
    'th': 'สิงคโปร์'
  },
  '马来西亚': {
    'zh': '马来西亚',
    'en': 'Malaysia',
    'th': 'มาเลเซีย'
  },
  '菲律宾': {
    'zh': '菲律宾',
    'en': 'Philippines',
    'th': 'ฟิลิปปินส์'
  },
  '香港': {
    'zh': '香港',
    'en': 'Hong Kong',
    'th': 'ฮ่องกง'
  },
  '台湾': {
    'zh': '台湾',
    'en': 'Taiwan',
    'th': 'ไต้หวัน'
  },
  '越南': {
    'zh': '越南',
    'en': 'Vietnam',
    'th': 'เวียดนาม'
  },
  '文莱': {
    'zh': '文莱',
    'en': 'Brunei',
    'th': 'บรูไน'
  },
  
  // 北美洲
  '美国': {
    'zh': '美国',
    'en': 'United States',
    'th': 'สหรัฐอเมริกา'
  },
  '加拿大': {
    'zh': '加拿大',
    'en': 'Canada',
    'th': 'แคนาดา'
  },
  
  // 大洋洲
  '澳大利亚': {
    'zh': '澳大利亚',
    'en': 'Australia',
    'th': 'ออสเตรเลีย'
  },
  '新西兰': {
    'zh': '新西兰',
    'en': 'New Zealand',
    'th': 'นิวซีแลนด์'
  },
  
  // 南美洲
  '巴西': {
    'zh': '巴西',
    'en': 'Brazil',
    'th': 'บราซิล'
  },
  
  // 非洲
  '南非': {
    'zh': '南非',
    'en': 'South Africa',
    'th': 'แอฟริกาใต้'
  },
  
  // 中东
  '阿联酋': {
    'zh': '阿联酋',
    'en': 'United Arab Emirates',
    'th': 'สหรัฐอาหรับเอมิเรตส์'
  },
  '沙特阿拉伯': {
    'zh': '沙特阿拉伯',
    'en': 'Saudi Arabia',
    'th': 'ซาอุดิอาระเบีย'
  },
  '土耳其': {
    'zh': '土耳其',
    'en': 'Turkey',
    'th': 'ตุรกี'
  },
  '巴林': {
    'zh': '巴林',
    'en': 'Bahrain',
    'th': 'บาห์เรน'
  }
};

/**
 * 获取国家/地区的多语言名称
 * @param {string} countryName - 国家/地区名称 (如 '中国', '美国')
 * @param {string} lang - 语言代码 (如 'zh', 'en', 'th')，可选，默认使用当前i18n语言
 * @returns {string} 国家/地区的多语言名称
 */
export function getCountryName(countryName, lang = null) {
  if (!countryName) return '';
  
  // 确定要使用的语言
  const currentLang = lang || getCurrentLanguage();
  
  // 使用本地配置的国家翻译
  if (COUNTRY_TRANSLATIONS[countryName]) {
    const translations = COUNTRY_TRANSLATIONS[countryName];
    return translations[currentLang] || translations['zh'] || countryName;
  }
  
  // 如果没有找到翻译，返回原始名称
  return countryName;
}

/**
 * 获取当前语言代码
 * @returns {string} 语言代码 ('zh', 'en', 'th')
 */
function getCurrentLanguage() {
  try {
    // 语言代码映射
    const langMap = {
      'zh-CN': 'zh',
      'en-US': 'en', 
      'th-TH': 'th'
    };
    
    // 尝试从 localStorage 获取语言设置
    let storedLang = 'zh-CN';
    try {
      storedLang = localStorage.getItem('language') || 'zh-CN';
    } catch (e) {
      // localStorage 可能不可用（如 SSR 环境）
      console.warn('无法访问 localStorage，使用默认语言');
    }
    
    // 如果 i18n 实例可用，优先使用它的当前语言
    if (i18n && i18n.global && i18n.global.locale) {
      try {
        const locale = i18n.global.locale.value || i18n.global.locale;
        return langMap[locale] || langMap[storedLang] || 'zh';
      } catch (e) {
        console.warn('访问 i18n.global.locale 失败:', e);
      }
    }
    
    // 回退到 localStorage
    return langMap[storedLang] || 'zh';
  } catch (error) {
    console.warn('获取语言设置失败，使用默认中文:', error);
    return 'zh';
  }
}

// 默认导出
export default {
  getCountryName
};
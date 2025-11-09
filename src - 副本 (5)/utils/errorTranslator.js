/**
 * 错误消息翻译工具
 * 用于将后端返回的错误消息键翻译为对应的文本
 */

// 错误消息键到翻译键的映射
const ERROR_KEY_MAPPING = {
  // 权限相关错误
  'auth.eod_permission_denied': 'auth.eod_permission_denied',
  'auth.eod_permission_granted': 'auth.eod_permission_granted',
  'auth.missing_permission': 'auth.missing_permission',
  'auth.business_locked': 'auth.business_locked',
  'auth.session_required': 'auth.session_required',
  'auth.transaction_locked': 'auth.transaction_locked',
  'auth.balance_locked': 'auth.balance_locked',
  
  // 通用错误
  'unauthorized': 'auth.unauthorized',
  'forbidden': 'auth.forbidden',
  'permission_denied': 'auth.permission_denied',
  
  // 网络错误
  'network_error': 'common.network_error',
  'timeout': 'common.timeout',
  'connection_failed': 'common.connection_failed',
  
  // 数据错误
  'validation_error': 'common.validation_error',
  'data_not_found': 'common.data_not_found',
  'duplicate_data': 'common.duplicate_data',
  
  // 服务器错误
  'server_error': 'common.server_error',
  'internal_error': 'common.internal_error',
  'service_unavailable': 'common.service_unavailable'
};

/**
 * 翻译错误消息
 * @param {string} message - 错误消息
 * @param {Function} t - i18n翻译函数
 * @returns {string} - 翻译后的错误消息
 */
export function translateErrorMessage(message, t) {
  if (!message || typeof message !== 'string') {
    return message;
  }
  
  console.log('🌍 翻译错误消息:', message);
  
  // 检查是否是错误消息键
  if (ERROR_KEY_MAPPING[message]) {
    const translationKey = ERROR_KEY_MAPPING[message];
    try {
      const translated = t(translationKey);
      console.log('🌍 通过ERROR_KEY_MAPPING翻译:', translationKey, '->', translated);
      // 如果翻译成功且不是原始键值，返回翻译结果
      if (translated && translated !== translationKey) {
        return translated;
      }
    } catch (error) {
      console.warn('翻译错误消息失败:', error);
    }
  }
  
  // 检查消息是否包含常见的错误键模式
  const commonPatterns = [
    /^auth\./,
    /^eod\./,
    /^exchange\./,
    /^common\./
  ];
  
  for (const pattern of commonPatterns) {
    if (pattern.test(message)) {
      try {
        const translated = t(message);
        console.log('🌍 通过模式匹配翻译:', message, '->', translated);
        if (translated && translated !== message) {
          return translated;
        }
      } catch (error) {
        console.warn('🌍 模式匹配翻译失败:', error);
        // 翻译失败，继续检查下一个模式
      }
    }
  }
  
  console.log('🌍 未找到翻译，返回原始消息:', message);
  // 如果没有找到翻译，返回原始消息
  return message;
}

/**
 * 检查消息是否是错误键
 * @param {string} message - 消息
 * @returns {boolean} - 是否是错误键
 */
export function isErrorKey(message) {
  if (!message || typeof message !== 'string') {
    return false;
  }
  
  // 检查是否是已知的错误键
  if (ERROR_KEY_MAPPING[message]) {
    return true;
  }
  
  // 检查是否包含常见的错误键模式
  const commonPatterns = [
    /^auth\./,
    /^eod\./,
    /^exchange\./,
    /^common\./
  ];
  
  return commonPatterns.some(pattern => pattern.test(message));
}

/**
 * 获取错误消息的翻译键
 * @param {string} message - 错误消息
 * @returns {string|null} - 翻译键，如果没有找到则返回null
 */
export function getErrorTranslationKey(message) {
  if (!message || typeof message !== 'string') {
    return null;
  }
  
  // 检查是否是已知的错误键
  if (ERROR_KEY_MAPPING[message]) {
    return ERROR_KEY_MAPPING[message];
  }
  
  // 检查是否包含常见的错误键模式
  const commonPatterns = [
    /^auth\./,
    /^eod\./,
    /^exchange\./,
    /^common\./
  ];
  
  for (const pattern of commonPatterns) {
    if (pattern.test(message)) {
      return message;
    }
  }
  
  return null;
} 
/**
 * 统一错误处理工具
 * 用于屏蔽敏感的系统信息，提供友好的用户提示
 */

// 敏感关键词列表 - 这些信息不应该暴露给前端用户
const SENSITIVE_KEYWORDS = [
  // 数据库相关
  'sqlite', 'mysql', 'postgresql', 'database', 'table', 'column', 'foreign key',
  'constraint', 'index', 'primary key', 'sql', 'query', 'select', 'insert', 
  'update', 'delete', 'drop', 'alter', 'create',
  
  // SQLAlchemy相关
  'sqlalchemy', 'operationalerror', 'integrityerror', 'dataerror',
  'programmingerror', 'interfaceerror', 'databaseerror',
  
  // 系统路径和文件
  'traceback', 'file "/', 'line ', 'module', 'function',
  '/usr/', '/var/', '/home/', '/opt/', 'c:\\', 'd:\\',
  
  // Python相关
  'python', 'flask', 'werkzeug', 'jinja2', 'exception', 'error:',
  'attributeerror', 'typeerror', 'valueerror', 'keyerror',
  
  // 网络和服务器信息
  'localhost', '127.0.0.1', '0.0.0.0', 'port', 'socket',
  'connection refused', 'connection timeout', 'host unreachable'
];

// 友好的错误消息映射
const FRIENDLY_MESSAGES = {
  // 网络连接问题
  'network': '网络连接异常，请检查网络设置后重试',
  'timeout': '请求超时，请稍后重试',
  'connection': '无法连接到服务器，请联系系统管理员',
  
  // 权限问题
  'unauthorized': '登录已过期，请重新登录',
  'forbidden': '您没有执行此操作的权限',
  'permission': '权限不足，请联系管理员',
  
  // 数据问题
  'validation': '输入的数据格式不正确，请检查后重试',
  'duplicate': '数据已存在，请检查后重试',
  'notfound': '请求的数据不存在',
  'conflict': '数据冲突，请刷新页面后重试',
  
  // 服务器问题
  'server': '服务器暂时无法处理请求，请稍后重试',
  'maintenance': '系统正在维护中，请稍后重试',
  'overload': '系统繁忙，请稍后重试',
  
  // 默认消息
  'default': '操作失败，请稍后重试或联系系统管理员'
};

/**
 * 检查错误消息是否包含敏感信息
 * @param {string} message - 错误消息
 * @returns {boolean} - 是否包含敏感信息
 */
function containsSensitiveInfo(message) {
  if (!message || typeof message !== 'string') {
    return false;
  }
  
  const lowerMessage = message.toLowerCase();
  return SENSITIVE_KEYWORDS.some(keyword => 
    lowerMessage.includes(keyword.toLowerCase())
  );
}

/**
 * 根据错误类型和状态码获取友好的错误消息
 * @param {Error} error - 错误对象
 * @param {number} status - HTTP状态码
 * @returns {string} - 友好的错误消息
 */
function getFriendlyMessage(error, status) {
  // 根据HTTP状态码返回对应消息
  switch (status) {
    case 400:
      return FRIENDLY_MESSAGES.validation;
    case 401:
      return FRIENDLY_MESSAGES.unauthorized;
    case 403:
      return FRIENDLY_MESSAGES.forbidden;
    case 404:
      return FRIENDLY_MESSAGES.notfound;
    case 409:
      return FRIENDLY_MESSAGES.conflict;
    case 429:
      return FRIENDLY_MESSAGES.overload;
    case 500:
    case 502:
    case 503:
    case 504:
      return FRIENDLY_MESSAGES.server;
    default:
      break;
  }
  
  // 根据错误类型返回消息
  if (error && error.code) {
    switch (error.code) {
      case 'NETWORK_ERROR':
      case 'ERR_NETWORK':
        return FRIENDLY_MESSAGES.network;
      case 'TIMEOUT':
      case 'ERR_TIMEOUT':
        return FRIENDLY_MESSAGES.timeout;
      case 'ECONNREFUSED':
      case 'ERR_CONNECTION_REFUSED':
        return FRIENDLY_MESSAGES.connection;
      default:
        break;
    }
  }
  
  return FRIENDLY_MESSAGES.default;
}

/**
 * 安全的错误消息处理
 * @param {Error} error - 错误对象
 * @param {string} defaultMessage - 默认错误消息
 * @returns {string} - 安全的错误消息
 */
export function getSafeErrorMessage(error, defaultMessage = '操作失败') {
  try {
    let message = defaultMessage;
    let status = null;
    
    // 提取错误信息
    if (error && error.response) {
      status = error.response.status;
      
      // 优先使用后端返回的消息（如果安全）
      if (error.response.data && error.response.data.message) {
        const serverMessage = error.response.data.message;
        
        // 检查服务器消息是否包含敏感信息
        if (!containsSensitiveInfo(serverMessage)) {
          message = serverMessage;
        } else {
          // 包含敏感信息，使用友好消息
          message = getFriendlyMessage(error, status);
          
          // 在开发环境下记录原始错误（但不显示给用户）
          if (process.env.NODE_ENV === 'development') {
            console.warn('敏感错误信息已屏蔽:', serverMessage);
          }
        }
      } else {
        // 没有服务器消息，根据状态码生成友好消息
        message = getFriendlyMessage(error, status);
      }
    } else if (error && error.message) {
      // 处理客户端错误
      if (!containsSensitiveInfo(error.message)) {
        message = error.message;
      } else {
        message = getFriendlyMessage(error, null);
        
        if (process.env.NODE_ENV === 'development') {
          console.warn('敏感错误信息已屏蔽:', error.message);
        }
      }
    }
    
    return message;
    
  } catch (e) {
    // 错误处理过程中出错，返回最安全的默认消息
    console.error('错误处理器异常:', e);
    return FRIENDLY_MESSAGES.default;
  }
}

/**
 * 处理API请求错误的通用方法
 * @param {Error} error - 错误对象
 * @param {string} operation - 操作描述（如"获取数据"、"保存信息"等）
 * @returns {object} - 包含安全错误信息的对象
 */
export function handleApiError(error, operation = '操作') {
  const safeMessage = getSafeErrorMessage(error, `${operation}失败`);
  const status = error?.response?.status || 0;
  
  // 记录错误日志（开发环境）
  if (process.env.NODE_ENV === 'development') {
    console.group(`🚨 API错误 - ${operation}`);
    console.error('原始错误:', error);
    console.error('状态码:', status);
    console.error('安全消息:', safeMessage);
    console.groupEnd();
  }
  
  return {
    message: safeMessage,
    status: status,
    isNetworkError: !error?.response,
    isServerError: status >= 500,
    isClientError: status >= 400 && status < 500,
    isAuthError: status === 401 || status === 403
  };
}

/**
 * 网络连接检查
 * @returns {boolean} - 是否在线
 */
export function isOnline() {
  return navigator.onLine;
}

/**
 * 显示用户友好的错误提示
 * @param {Error} error - 错误对象
 * @param {Function} showToast - 显示提示的函数
 * @param {string} operation - 操作描述
 */
export function showSafeError(error, showToast, operation = '操作') {
  const errorInfo = handleApiError(error, operation);
  
  // 根据错误类型选择不同的提示方式
  if (errorInfo.isNetworkError && !isOnline()) {
    showToast('网络连接已断开，请检查网络设置', 'error');
  } else if (errorInfo.isAuthError) {
    showToast(errorInfo.message, 'warning');
    // 可以在这里触发重新登录逻辑
  } else {
    showToast(errorInfo.message, 'error');
  }
}

export default {
  getSafeErrorMessage,
  handleApiError,
  showSafeError,
  isOnline
}; 
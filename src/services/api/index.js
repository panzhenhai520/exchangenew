import axios from 'axios';
import router from '@/router';
import { translateErrorMessage } from '../../utils/errorTranslator';

// 全局i18n实例（稍后设置）
let globalI18n = null;

// 设置全局i18n实例的函数
export const setGlobalI18n = (i18n) => {
  globalI18n = i18n;
};

// 创建axios实例
const api = axios.create({
  baseURL: process.env.VUE_APP_API_URL || (process.env.NODE_ENV === 'development' ? 'http://192.168.13.56:5001/api' : '/api'),
  timeout: 60000,  // 增加超时时间到60秒
  headers: {
    'Content-Type': 'application/json'
  },
  // 添加URL编码配置
  transformRequest: [(data, headers) => {
    // 确保URL中的下划线不被转换为空格
    if (headers && headers['Content-Type'] === 'application/json') {
      return JSON.stringify(data);
    }
    return data;
  }]
});

// 生成或获取日结会话ID
const getEODSessionId = () => {
  // 先尝试从sessionStorage获取现有的会话ID
  let sessionId = sessionStorage.getItem('eod_session_id');
  
  if (!sessionId) {
    // 如果没有，生成新的会话ID
    try {
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      const userId = user.id || 'unknown';
      const timestamp = Date.now();
      sessionId = `eod_${userId}_${timestamp}`;
      
      // 保存到sessionStorage
      sessionStorage.setItem('eod_session_id', sessionId);
    } catch (error) {
      console.error('生成会话ID失败:', error);
      // 使用简单的时间戳作为备用方案
      sessionId = `eod_backup_${Date.now()}`;
    }
  }
  
  return sessionId;
};

// 设置日结会话ID（用于恢复现有会话）
const setEODSessionId = (sessionId) => {
  if (sessionId) {
    sessionStorage.setItem('eod_session_id', sessionId);
    console.log('已设置日结会话ID:', sessionId);
  }
};

// 清理日结会话ID
const clearEODSessionId = () => {
  sessionStorage.removeItem('eod_session_id');
  console.log('已清理日结会话ID');
};

// 导出会话管理函数
api.getEODSessionId = getEODSessionId;
api.setEODSessionId = setEODSessionId;
api.clearEODSessionId = clearEODSessionId;

// 检查是否是日结相关的API调用
const isEODRelatedAPI = (url) => {
  return url && (
    url.includes('/end_of_day/') || 
    url.includes('/eod-step/') || 
    url.includes('/eod_step/')
  );
};

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 检查是否是登录相关的API调用
    const isLoginAPI = config.url && (
      config.url.includes('/auth/login') ||
      config.url.includes('/login') ||
      config.url.includes('/auth/refresh')
    );
    
    // 只有在非登录API调用时才添加token
    if (!isLoginAPI) {
      const token = localStorage.getItem('token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    
    // 调试：检查URL是否被修改
    if (config.url && config.url.includes('end_of_day')) {
      console.log('=== API请求URL调试 ===');
      console.log('原始URL:', config.url);
      console.log('baseURL:', config.baseURL);
      console.log('完整请求URL:', config.baseURL + config.url);
      console.log('========================');
      
      // 确保URL中的下划线不被修改
      if (config.url.includes('end_of_day')) {
        config.url = config.url.replace(/end of day/g, 'end_of_day');
      }
    }
    
    // 为日结相关的API调用添加会话ID
    if (isEODRelatedAPI(config.url)) {
      const sessionId = getEODSessionId();
      config.headers['X-Session-ID'] = sessionId;

      // 调试信息
      console.log(`日结API调用: ${config.url}, 会话ID: ${sessionId}`);
    }

    // 添加当前语言到请求头
    if (globalI18n && globalI18n.global && globalI18n.global.locale) {
      config.headers['X-Language'] = globalI18n.global.locale.value;
    } else if (globalI18n && globalI18n.locale) {
      config.headers['X-Language'] = globalI18n.locale;
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // 处理401错误（未授权）
    if (error.response && error.response.status === 401) {
      // 检查是否是EOD流程
      const isEODFlow = error.config?.url?.includes('/end_of_day/') || 
                        error.config?.url?.includes('/eod_step/');
      
      if (isEODFlow) {
        // EOD流程中的令牌失效，给出更友好的错误消息
        // 显示确认对话框
        if (window.confirm('您的登录状态已过期，是否重新登录继续操作？')) {
          // 保存当前路由
          const currentRoute = router.currentRoute.value.fullPath;
          
          // 跳转到登录页
          router.push({
            name: 'login',
            query: { redirect: currentRoute }
          });
        }
        
        // 返回更友好的错误消息
        return Promise.reject({
          ...error,
          message: '登录状态已过期，请重新登录后继续操作'
        });
      }
      
      // 其他401错误的处理
      console.error('用户未授权或token无效');
      
      // 检查是否已经在登录页面
      if (router.currentRoute.value.name !== 'login') {
        // 显示错误消息
        if (window.ElMessage) {
          window.ElMessage.error('登录状态已过期，请重新登录');
        }
        
        // 跳转到登录页
        router.push({
          name: 'login',
          query: { redirect: router.currentRoute.value.fullPath }
        });
      }
    }
    
    // 处理其他错误
    if (error.response && error.response.status >= 500) {
      console.error('服务器错误:', error.response.data);
      if (window.ElMessage) {
        window.ElMessage.error(error.response.data?.message || '服务器错误');
      }
    }
    
    // 翻译错误消息
    if (error.response && error.response.data && error.response.data.message) {
      const originalMessage = error.response.data.message;
      if (globalI18n && globalI18n.t) {
        const translatedMessage = translateErrorMessage(originalMessage, globalI18n.t);
        error.response.data.message = translatedMessage;
      }
    }
    
    return Promise.reject(error);
  }
);

export default api;

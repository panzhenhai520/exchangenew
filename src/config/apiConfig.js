// ⚠️ 重要：优先使用运行时配置 (window.ENV_CONFIG)，然后才是编译时环境变量
// 这样可以在不重新编译的情况下更换IP地址

let rawOrigin = '';

// 1. 尝试从运行时配置读取 (env-config.js)
if (typeof window !== 'undefined' && window.ENV_CONFIG && window.ENV_CONFIG.API_BASE_URL) {
  rawOrigin = window.ENV_CONFIG.API_BASE_URL.replace(/\/$/, '');
  console.log('[apiConfig] ✅ 使用运行时配置:', rawOrigin);
  console.log('[apiConfig] 来源: window.ENV_CONFIG (env-config.js)');
}
// 2. 回退到编译时环境变量
else if (process.env.VUE_APP_API_BASE_URL) {
  rawOrigin = process.env.VUE_APP_API_BASE_URL.replace(/\/$/, '');
  console.log('[apiConfig] ⚠️ 使用编译时配置:', rawOrigin);
  console.log('[apiConfig] 来源: process.env.VUE_APP_API_BASE_URL (.env.local)');
}
// 3. 使用默认值
else {
  rawOrigin = '';
  console.warn('[apiConfig] ❌ 未找到API配置，使用相对路径');
}

// 调试输出
console.log('[apiConfig] 最终配置:');
console.log('  - API_ORIGIN:', rawOrigin);
console.log('  - window.ENV_CONFIG:', window.ENV_CONFIG);
console.log('  - process.env.VUE_APP_API_BASE_URL:', process.env.VUE_APP_API_BASE_URL);

export const API_ORIGIN = rawOrigin;

export const API_BASE_URL = rawOrigin || '';

// 确保API_PREFIX以斜杠结尾，这样axios拼接路径时才能正确工作
// 例如: baseURL="http://host/api/" + url="amlo/reservations" = "http://host/api/amlo/reservations"
export const API_PREFIX = rawOrigin ? `${rawOrigin}/api` : '/api';

console.log('[apiConfig] API_PREFIX已设置为:', API_PREFIX);

export const STATIC_BASE_URL = rawOrigin ? `${rawOrigin}` : '';

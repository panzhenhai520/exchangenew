const rawOrigin = (process.env.VUE_APP_API_BASE_URL || '').replace(/\/$/, '');

// 调试输出
console.log('[apiConfig] VUE_APP_API_BASE_URL:', process.env.VUE_APP_API_BASE_URL);
console.log('[apiConfig] rawOrigin:', rawOrigin);

export const API_ORIGIN = rawOrigin;

export const API_BASE_URL = rawOrigin || '';

// 确保API_PREFIX以斜杠结尾，这样axios拼接路径时才能正确工作
// 例如: baseURL="http://host/api/" + url="amlo/reservations" = "http://host/api/amlo/reservations"
export const API_PREFIX = rawOrigin ? `${rawOrigin}/api/` : '/api/';

console.log('[apiConfig] API_PREFIX已设置为:', API_PREFIX);

export const STATIC_BASE_URL = rawOrigin ? `${rawOrigin}` : '';

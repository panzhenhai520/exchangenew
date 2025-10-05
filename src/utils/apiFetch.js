// API Fetch 工具类，统一处理401错误
import router from '@/router'

/**
 * 包装fetch函数，自动处理401错误
 * @param {string} url - 请求URL
 * @param {object} options - fetch选项
 * @returns {Promise<Response>}
 */
export async function apiFetch(url, options = {}) {
  // 确保URL是完整的API路径
  const fullUrl = url.startsWith('/api/') ? url : `/api/${url}`
  
  // 添加默认headers
  const defaultHeaders = {
    'Content-Type': 'application/json',
  }
  
  // 添加token
  const token = localStorage.getItem('token')
  if (token) {
    defaultHeaders.Authorization = `Bearer ${token}`
  }
  
  // 合并headers
  const headers = {
    ...defaultHeaders,
    ...options.headers
  }
  
  try {
    const response = await fetch(fullUrl, {
      ...options,
      headers
    })
    
    // 检查401错误
    if (response.status === 401) {
      console.warn('API请求返回401，跳转到登录页面')
      
      // 清除本地存储
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      
      // 跳转到登录页面
      if (router.currentRoute.value.name !== 'login') {
        router.push({
          name: 'login',
          query: { redirect: router.currentRoute.value.fullPath }
        })
      }
      
      // 抛出错误
      throw new Error('登录状态已过期，请重新登录')
    }
    
    return response
  } catch (error) {
    // 如果是网络错误或其他错误，也检查是否是401相关
    if (error.message && error.message.includes('401')) {
      console.warn('API请求401错误，跳转到登录页面')
      
      // 清除本地存储
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      
      // 跳转到登录页面
      if (router.currentRoute.value.name !== 'login') {
        router.push({
          name: 'login',
          query: { redirect: router.currentRoute.value.fullPath }
        })
      }
    }
    
    throw error
  }
}

/**
 * 获取JSON响应的辅助函数
 * @param {string} url - 请求URL
 * @param {object} options - fetch选项
 * @returns {Promise<object>}
 */
export async function apiFetchJson(url, options = {}) {
  const response = await apiFetch(url, options)
  
  const contentType = response.headers.get('content-type')
  if (contentType && contentType.includes('application/json')) {
    return await response.json()
  } else {
    const textContent = await response.text()
    console.error('API返回非JSON响应:', textContent)
    throw new Error('服务器返回非JSON响应')
  }
}

export default apiFetch
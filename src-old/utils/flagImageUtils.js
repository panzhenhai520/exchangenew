/**
 * 国旗图片缓存和优化工具
 */

// 图片加载缓存
const imageCache = new Map()
const loadingPromises = new Map()

/**
 * 预加载图片并缓存结果
 * @param {string} src - 图片URL
 * @returns {Promise<boolean>} - 是否加载成功
 */
export const preloadImage = (src) => {
  if (imageCache.has(src)) {
    return Promise.resolve(imageCache.get(src))
  }

  if (loadingPromises.has(src)) {
    return loadingPromises.get(src)
  }

  const promise = new Promise((resolve) => {
    const img = new Image()
    img.onload = () => {
      imageCache.set(src, true)
      loadingPromises.delete(src)
      resolve(true)
    }
    img.onerror = () => {
      imageCache.set(src, false)
      loadingPromises.delete(src)
      resolve(false)
    }
    img.src = src
  })

  loadingPromises.set(src, promise)
  return promise
}

/**
 * 获取优化的国旗URL
 * @param {string} code - 货币代码或国家代码
 * @param {boolean} useCache - 是否使用缓存检查
 * @returns {string} - 图片URL
 */
export const getOptimizedFlagUrl = async (code, useCache = true) => {
  if (!code) return '/flags/unknown.svg'

  const flagUrl = `/flags/${code.toLowerCase()}.svg`
  
  if (!useCache) {
    return flagUrl
  }

  // 检查缓存
  if (imageCache.has(flagUrl)) {
    return imageCache.get(flagUrl) ? flagUrl : '/flags/unknown.svg'
  }

  // 预加载并检查
  const exists = await preloadImage(flagUrl)
  return exists ? flagUrl : '/flags/unknown.svg'
}

/**
 * 处理图片错误的统一函数
 * @param {Event} event - 错误事件
 * @param {string} fallbackUrl - 备用URL，默认为unknown.svg
 */
export const handleImageError = (event, fallbackUrl = '/flags/unknown.svg') => {
  const img = event.target
  
  // 避免无限循环
  if (img.src.includes(fallbackUrl)) {
    return
  }

  // 缓存失败结果
  imageCache.set(img.src, false)
  
  // 设置备用图片
  img.src = fallbackUrl
}

/**
 * 批量预加载常用国旗
 * @param {Array<string>} codes - 需要预加载的代码数组
 */
export const preloadCommonFlags = async (codes = []) => {
  const commonCodes = codes.length > 0 ? codes : [
    'us', 'eu', 'gb', 'jp', 'cn', 'hk', 'tw', 'kr', 'sg', 'th',
    'id', 'my', 'ph', 'in', 'au', 'nz', 'ca', 'unknown'
  ]

  const promises = commonCodes.map(code => preloadImage(`/flags/${code}.svg`))
  await Promise.all(promises)
  
  console.log(`预加载完成: ${commonCodes.length} 个国旗图片`)
}

/**
 * 清除图片缓存
 */
export const clearImageCache = () => {
  imageCache.clear()
  loadingPromises.clear()
} 
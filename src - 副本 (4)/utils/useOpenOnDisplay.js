// useOpenOnDisplay.js
import { shallowRef, computed } from 'vue'

/**
 * 在指定显示器上打开并"最大化"一个新浏览器窗口（铺满可用工作区）。
 * 必须在用户手势回调里调用，避免被弹窗拦截。
 *
 * @param {Object} opts - 配置选项
 * @param {string} opts.url - 要打开的 URL
 * @param {string} [opts.target='_blank'] - window.open 的目标
 * @param {string} [opts.features=''] - 附加的 window.open features
 * @param {number} [opts.screenIndex] - 选屏索引，如果提供则使用该索引
 * @param {boolean} [opts.preferNonPrimary=true] - 是否优先选择非主屏
 * @param {boolean} [opts.includeTaskbarArea=false] - 是否使用整块屏幕（包含任务栏区域）
 * @param {string} [opts.fallbackGuess='right'] - 不支持多屏API时的方向猜测 ('right'|'left'|'above'|'below')
 * @param {boolean} [opts.center90=false] - 是否居中显示并缩放到90%区域
 * @returns {Promise<Window|null>} 打开的窗口对象，如果失败则返回null
 */
export function useOpenOnDisplay() {
  const lastWindow = shallowRef(null)

  const isMultiScreenSupported = computed(() => {
    try {
      return typeof window !== 'undefined' && 'getScreenDetails' in window
    } catch {
      return false
    }
  })

  async function openOnDisplay(opts) {
    console.log('[useOpenOnDisplay] ===== 开始打开窗口 =====')
    console.log('[useOpenOnDisplay] 配置参数:', opts)

    const {
      url,
      target = '_blank',
      features = '',
      screenIndex,
      preferNonPrimary = true,
      includeTaskbarArea = false,
      fallbackGuess = 'right',
      center90 = false,
    } = opts

    // 1) 计算目标区域（left/top/width/height）
    let left = 0
    let top = 0
    let width = window.screen.availWidth
    let height = window.screen.availHeight
    let placedByDetails = false

    console.log('[useOpenOnDisplay] 检查多屏API支持:', 'getScreenDetails' in window)

    // 尝试申请多屏API权限
    if (window.getScreenDetails && !placedByDetails) {
      try {
        console.log('[useOpenOnDisplay] 申请多屏API权限...')
        // 这会触发浏览器权限请求对话框
        await window.getScreenDetails()
        console.log('[useOpenOnDisplay] ✅ 多屏API权限已获得')
      } catch (error) {
        console.warn('[useOpenOnDisplay] ⚠️ 多屏API权限被拒绝:', error.message)
      }
    }

    if (window.getScreenDetails) {
      try {
        console.log('[useOpenOnDisplay] 尝试使用 getScreenDetails API...')
        const details = await window.getScreenDetails()
        const screens = Array.from(details.screens ?? [])
        console.log('[useOpenOnDisplay] 检测到屏幕数量:', screens.length)
        console.log('[useOpenOnDisplay] 屏幕信息:', screens.map(s => ({
          isPrimary: s.isPrimary,
          left: s.left,
          top: s.top,
          width: s.width,
          height: s.height,
          availLeft: s.availLeft,
          availTop: s.availTop,
          availWidth: s.availWidth,
          availHeight: s.availHeight
        })))

        let s

        if (typeof screenIndex === 'number' && screens[screenIndex]) {
          s = screens[screenIndex]
          console.log('[useOpenOnDisplay] 使用指定屏幕索引:', screenIndex)
        } else if (preferNonPrimary) {
          s = screens.find((x) => !x.isPrimary) ?? details.currentScreen ?? screens[0]
          console.log('[useOpenOnDisplay] 优先选择非主屏，选中屏幕:', s.isPrimary ? '主屏' : '扩展屏')
        } else {
          s = details.currentScreen ?? screens[0]
          console.log('[useOpenOnDisplay] 使用当前屏幕')
        }

        // 取工作区或整屏区域
        const area = includeTaskbarArea
          ? { left: s.left, top: s.top, width: s.width, height: s.height }
          : { left: s.availLeft, top: s.availTop, width: s.availWidth, height: s.availHeight }

        console.log('[useOpenOnDisplay] 计算区域:', area)

        if (
          Number.isFinite(area.left) &&
          Number.isFinite(area.top) &&
          Number.isFinite(area.width) &&
          Number.isFinite(area.height)
        ) {
          left = Math.floor(area.left)
          top = Math.floor(area.top)
          width = Math.floor(area.width)
          height = Math.floor(area.height)
          placedByDetails = true
          console.log('[useOpenOnDisplay] ✅ 使用API计算的位置:', { left, top, width, height })
        }
      } catch (error) {
        console.warn('[useOpenOnDisplay] ⚠️ getScreenDetails失败:', error)
        console.log('[useOpenOnDisplay] 错误详情:', error.message)
      }
    } else {
      console.log('[useOpenOnDisplay] ⚠️ 浏览器不支持 getScreenDetails API')
    }

    // 2) 兜底：猜测扩展屏在当前屏右侧（或按 fallbackGuess）
    if (!placedByDetails) {
      console.log('[useOpenOnDisplay] ⚠️ 使用兜底方案计算位置')
      const curLeft = window.screen.availLeft ?? window.screenX ?? 0
      const curTop = window.screen.availTop ?? window.screenY ?? 0
      const curW = window.screen.availWidth || window.outerWidth || 1280
      const curH = window.screen.availHeight || window.outerHeight || 720

      console.log('[useOpenOnDisplay] 当前屏幕信息:', {
        curLeft,
        curTop,
        curW,
        curH,
        fallbackGuess
      })

      switch (fallbackGuess) {
        case 'left':
          left = curLeft - curW
          top = curTop
          width = curW
          height = curH
          break
        case 'above':
          left = curLeft
          top = curTop - curH
          width = curW
          height = curH
          break
        case 'below':
          left = curLeft
          top = curTop + curH
          width = curW
          height = curH
          break
        case 'right':
        default:
          left = curLeft + curW
          top = curTop
          width = curW
          height = curH
          break
      }
      console.log('[useOpenOnDisplay] 兜底方案计算的位置:', { left, top, width, height })
    }

    // 可选：改为居中 90%
    if (center90) {
      const dw = Math.max(200, Math.floor(width * 0.9))
      const dh = Math.max(200, Math.floor(height * 0.9))
      left = left + Math.floor((width - dw) / 2)
      top = top + Math.floor((height - dh) / 2)
      width = dw
      height = dh
    }

    // 3) 打开窗口（某些浏览器会忽略部分 features，所以后面再 moveTo/resizeTo 兜底）
    const featuresStr = [
      `left=${left}`,
      `top=${top}`,
      `width=${width}`,
      `height=${height}`,
      // 建议禁用工具条等（有些 UA 会忽略）
      'toolbar=no,menubar=no,location=no,status=no,resizable=yes,scrollbars=yes',
      features,
    ]
      .filter(Boolean)
      .join(',')

    console.log('[useOpenOnDisplay] 窗口features字符串:', featuresStr)
    console.log('[useOpenOnDisplay] 准备打开窗口:', { url, target })

    const win = window.open(url, target, featuresStr)

    if (!win) {
      console.error('[useOpenOnDisplay] ❌ 窗口打开失败 - 可能被弹窗拦截')
      // 可能被弹窗拦截：请确认调用发生在用户手势回调里（如 @click）
      return null
    }

    console.log('[useOpenOnDisplay] ✅ 窗口已打开')

    // 4) 二次定位，提升一致性（有的浏览器会忽略 features 里的定位参数）
    try {
      console.log('[useOpenOnDisplay] 尝试二次定位窗口:', { left, top, width, height })
      // 注意：有的 UA 限制跨域窗口的 moveTo/resizeTo，但对 opener 打开的窗口通常允许
      win.moveTo(left, top)
      win.resizeTo(width, height)
      console.log('[useOpenOnDisplay] ✅ 二次定位完成')

      // 验证实际位置
      setTimeout(() => {
        console.log('[useOpenOnDisplay] 窗口实际位置:', {
          screenX: win.screenX,
          screenY: win.screenY,
          outerWidth: win.outerWidth,
          outerHeight: win.outerHeight
        })
      }, 100)
    } catch (error) {
      console.error('[useOpenOnDisplay] ⚠️ 二次定位失败:', error)
    }

    try {
      win.focus()
      console.log('[useOpenOnDisplay] ✅ 窗口已聚焦')
    } catch (error) {
      console.error('[useOpenOnDisplay] ⚠️ 窗口聚焦失败:', error)
    }

    lastWindow.value = win
    console.log('[useOpenOnDisplay] ===== 窗口打开完成 =====')
    return win
  }

  return {
    /** 是否支持 getScreenDetails 多屏 API */
    isMultiScreenSupported,
    /** 最近一次打开的窗口句柄 */
    lastWindow,
    /** 在指定显示器上打开并"最大化"窗口 */
    openOnDisplay,
  }
}

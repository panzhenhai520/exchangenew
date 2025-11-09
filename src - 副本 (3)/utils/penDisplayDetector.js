/**
 * PenDisplayDetector - 外接手写板/笔显示器检测工具
 *
 * 功能：
 * 1. 检测浏览器是否支持Pointer Events API
 * 2. 检测是否连接了支持压感的笔设备（Wacom、Surface Pen等）
 * 3. 提供设备信息和能力查询
 *
 * 支持的设备类型：
 * - Wacom笔显示器（Cintiq系列）
 * - Surface Pen
 * - Apple Pencil（iPad）
 * - 其他支持Pointer Events的笔设备
 */

class PenDisplayDetector {
  constructor() {
    this.hasPointerSupport = 'PointerEvent' in window
    this.hasTouchSupport = 'TouchEvent' in window
    this.penDevices = []
    this.isDetecting = false
    this.listeners = []
  }

  /**
   * 检测浏览器是否支持Pointer Events
   * @returns {boolean}
   */
  checkPointerSupport() {
    return this.hasPointerSupport
  }

  /**
   * 检测是否有压感笔设备
   * @returns {Promise<Object>}
   */
  async detectPenDevice() {
    if (!this.hasPointerSupport) {
      return {
        supported: false,
        reason: 'Pointer Events API不支持',
        devices: []
      }
    }

    // 返回当前检测到的设备信息
    return {
      supported: true,
      hasActivePen: this.penDevices.length > 0,
      devices: this.penDevices,
      capabilities: {
        pressure: this.penDevices.some(d => d.hasPressure),
        tilt: this.penDevices.some(d => d.hasTilt),
        eraser: this.penDevices.some(d => d.hasEraser)
      }
    }
  }

  /**
   * 开始监听笔设备事件
   * @param {HTMLElement} element - 要监听的元素
   * @param {Function} onDeviceDetected - 检测到设备时的回调
   */
  startListening(element, onDeviceDetected) {
    if (!this.hasPointerSupport || this.isDetecting) {
      return
    }

    this.isDetecting = true

    const handlePointerEvent = (event) => {
      // 检测笔输入类型
      if (event.pointerType === 'pen') {
        const deviceInfo = {
          type: 'pen',
          pointerId: event.pointerId,
          hasPressure: event.pressure !== undefined && event.pressure !== 0.5,
          pressure: event.pressure || 0,
          hasTilt: event.tiltX !== undefined || event.tiltY !== undefined,
          tiltX: event.tiltX || 0,
          tiltY: event.tiltY || 0,
          hasEraser: event.buttons === 32, // 橡皮擦按钮
          width: event.width,
          height: event.height,
          timestamp: Date.now()
        }

        // 检查是否已经记录了该设备
        const existingDevice = this.penDevices.find(d => d.pointerId === event.pointerId)
        if (!existingDevice) {
          this.penDevices.push(deviceInfo)
          console.log('[PenDisplayDetector] 检测到新笔设备:', deviceInfo)

          if (onDeviceDetected) {
            onDeviceDetected(deviceInfo)
          }
        } else {
          // 更新设备信息
          Object.assign(existingDevice, deviceInfo)
        }
      }
    }

    // 监听多种pointer事件
    const events = ['pointerdown', 'pointermove', 'pointerenter']
    events.forEach(eventName => {
      element.addEventListener(eventName, handlePointerEvent)
      this.listeners.push({ element, eventName, handler: handlePointerEvent })
    })

    console.log('[PenDisplayDetector] 开始监听笔设备事件')
  }

  /**
   * 停止监听
   */
  stopListening() {
    this.listeners.forEach(({ element, eventName, handler }) => {
      element.removeEventListener(eventName, handler)
    })
    this.listeners = []
    this.isDetecting = false
    console.log('[PenDisplayDetector] 停止监听笔设备事件')
  }

  /**
   * 获取当前连接的笔设备列表
   * @returns {Array}
   */
  getConnectedDevices() {
    return this.penDevices
  }

  /**
   * 清除设备列表
   */
  clearDevices() {
    this.penDevices = []
  }

  /**
   * 获取设备能力摘要
   * @returns {Object}
   */
  getCapabilities() {
    return {
      hasPointerSupport: this.hasPointerSupport,
      hasTouchSupport: this.hasTouchSupport,
      hasActivePen: this.penDevices.length > 0,
      deviceCount: this.penDevices.length,
      supportsPressure: this.penDevices.some(d => d.hasPressure),
      supportsTilt: this.penDevices.some(d => d.hasTilt),
      supportsEraser: this.penDevices.some(d => d.hasEraser)
    }
  }

  /**
   * 生成设备信息报告（用于调试）
   * @returns {string}
   */
  generateReport() {
    const caps = this.getCapabilities()
    const lines = [
      '=== 笔设备检测报告 ===',
      `Pointer Events支持: ${caps.hasPointerSupport ? '✓' : '✗'}`,
      `Touch Events支持: ${caps.hasTouchSupport ? '✓' : '✗'}`,
      `检测到笔设备: ${caps.hasActivePen ? '✓' : '✗'}`,
      `设备数量: ${caps.deviceCount}`,
      `支持压感: ${caps.supportsPressure ? '✓' : '✗'}`,
      `支持倾斜: ${caps.supportsTilt ? '✓' : '✗'}`,
      `支持橡皮擦: ${caps.supportsEraser ? '✓' : '✗'}`,
      '',
      '设备详情:'
    ]

    this.penDevices.forEach((device, index) => {
      lines.push(`  设备 ${index + 1}:`)
      lines.push(`    Pointer ID: ${device.pointerId}`)
      lines.push(`    压感: ${device.hasPressure ? `支持 (${device.pressure.toFixed(3)})` : '不支持'}`)
      lines.push(`    倾斜: ${device.hasTilt ? `支持 (X:${device.tiltX}°, Y:${device.tiltY}°)` : '不支持'}`)
      lines.push(`    橡皮擦: ${device.hasEraser ? '支持' : '不支持'}`)
      lines.push(`    尺寸: ${device.width}x${device.height}`)
      lines.push('')
    })

    return lines.join('\n')
  }
}

// 导出单例
export default new PenDisplayDetector()

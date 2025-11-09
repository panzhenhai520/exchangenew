<template>
  <div class="signature-pad-container">
    <!-- 设备状态提示 -->
    <div v-if="showDeviceStatus" class="device-status mb-2">
      <div class="alert alert-sm" :class="deviceStatusClass">
        <i class="fas" :class="deviceStatusIcon"></i>
        {{ deviceStatusText }}
      </div>
    </div>

    <!-- 签字画布区域 -->
    <div class="signature-canvas-wrapper" :style="{ width: canvasWidth, height: canvasHeight }">
      <canvas
        ref="canvasRef"
        class="signature-canvas"
        :width="actualWidth"
        :height="actualHeight"
        @pointerdown="handlePointerDown"
        @pointermove="handlePointerMove"
        @pointerup="handlePointerUp"
        @pointerleave="handlePointerLeave"
        @touchstart.prevent
        @touchmove.prevent
      ></canvas>

      <!-- 空白提示 -->
      <div v-if="isEmpty && !isDrawing" class="signature-placeholder">
        <i class="fas fa-signature"></i>
        <span>{{ placeholder }}</span>
      </div>
    </div>

    <!-- 工具栏 -->
    <div class="signature-toolbar mt-2">
      <button
        type="button"
        class="btn btn-sm btn-outline-danger"
        @click="clear"
        :disabled="isEmpty"
      >
        <i class="fas fa-eraser me-1"></i>{{ $t('common.clear') }}
      </button>
      <button
        v-if="allowUndo"
        type="button"
        class="btn btn-sm btn-outline-secondary"
        @click="undo"
        :disabled="!canUndo"
      >
        <i class="fas fa-undo me-1"></i>{{ $t('common.undo') }}
      </button>
      <button
        v-if="showDeviceInfo"
        type="button"
        class="btn btn-sm btn-outline-info"
        @click="toggleDeviceReport"
      >
        <i class="fas fa-info-circle me-1"></i>设备信息
      </button>
    </div>

    <!-- 设备详细信息（调试用） -->
    <div v-if="showReport" class="device-report mt-2">
      <pre class="mb-0"><code>{{ deviceReport }}</code></pre>
    </div>

    <!-- 当前笔压力显示（调试用） -->
    <div v-if="showPressureIndicator && currentPressure > 0" class="pressure-indicator">
      <div class="pressure-bar-container">
        <div class="pressure-bar" :style="{ width: (currentPressure * 100) + '%' }"></div>
      </div>
      <small class="text-muted">压力: {{ (currentPressure * 100).toFixed(0) }}%</small>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import penDisplayDetector from '@/utils/penDisplayDetector'

export default {
  name: 'SignaturePad',
  props: {
    width: {
      type: [Number, String],
      default: '100%'
    },
    height: {
      type: [Number, String],
      default: 200
    },
    lineWidth: {
      type: Number,
      default: 2
    },
    lineColor: {
      type: String,
      default: '#000000'
    },
    backgroundColor: {
      type: String,
      default: '#ffffff'
    },
    placeholder: {
      type: String,
      default: '请在此处签名'
    },
    showDeviceStatus: {
      type: Boolean,
      default: true
    },
    showPressureIndicator: {
      type: Boolean,
      default: false
    },
    allowUndo: {
      type: Boolean,
      default: true
    },
    showDeviceInfo: {
      type: Boolean,
      default: true
    },
    usePressure: {
      type: Boolean,
      default: true
    },
    initialData: {
      type: String,
      default: null
    }
  },
  emits: ['update:modelValue', 'change', 'start', 'end', 'deviceDetected'],
  setup(props, { emit }) {
    const { t } = useI18n()

    // Refs
    const canvasRef = ref(null)
    const isDrawing = ref(false)
    const isEmpty = ref(true)
    const strokes = ref([])
    const currentStroke = ref([])
    const currentPressure = ref(0)
    const deviceDetected = ref(false)
    const deviceInfo = ref(null)
    const showReport = ref(false)
    const deviceReport = ref('')

    // Canvas dimensions
    const actualWidth = ref(800)
    const actualHeight = ref(200)

    // Computed
    const canvasWidth = computed(() => {
      return typeof props.width === 'number' ? `${props.width}px` : props.width
    })

    const canvasHeight = computed(() => {
      return typeof props.height === 'number' ? `${props.height}px` : props.height
    })

    const deviceStatusClass = computed(() => {
      if (!penDisplayDetector.checkPointerSupport()) {
        return 'alert-danger'
      }
      if (deviceDetected.value) {
        return 'alert-success'
      }
      return 'alert-warning'
    })

    const deviceStatusIcon = computed(() => {
      if (!penDisplayDetector.checkPointerSupport()) {
        return 'fa-times-circle'
      }
      if (deviceDetected.value) {
        return 'fa-check-circle'
      }
      return 'fa-exclamation-triangle'
    })

    const deviceStatusText = computed(() => {
      if (!penDisplayDetector.checkPointerSupport()) {
        return '浏览器不支持笔输入'
      }
      if (deviceDetected.value) {
        const caps = []
        if (deviceInfo.value?.hasPressure) caps.push('压感')
        if (deviceInfo.value?.hasTilt) caps.push('倾斜')
        if (deviceInfo.value?.hasEraser) caps.push('橡皮擦')
        return `笔设备已连接${caps.length > 0 ? ` (${caps.join(', ')})` : ''}`
      }
      return '等待笔输入...'
    })

    const canUndo = computed(() => strokes.value.length > 0)

    // Methods
    const initCanvas = () => {
      const canvas = canvasRef.value
      if (!canvas) return

      const ctx = canvas.getContext('2d')
      ctx.fillStyle = props.backgroundColor
      ctx.fillRect(0, 0, actualWidth.value, actualHeight.value)

      // 如果有初始数据，加载它
      if (props.initialData) {
        loadSignature(props.initialData)
      }
    }

    const getPoint = (event) => {
      const canvas = canvasRef.value
      const rect = canvas.getBoundingClientRect()
      const scaleX = canvas.width / rect.width
      const scaleY = canvas.height / rect.height

      return {
        x: (event.clientX - rect.left) * scaleX,
        y: (event.clientY - rect.top) * scaleY,
        pressure: props.usePressure && event.pressure !== undefined ? event.pressure : 0.5,
        tiltX: event.tiltX || 0,
        tiltY: event.tiltY || 0,
        pointerType: event.pointerType
      }
    }

    const handlePointerDown = (event) => {
      if (event.pointerType === 'pen' && !deviceDetected.value) {
        deviceDetected.value = true
        deviceInfo.value = {
          hasPressure: event.pressure !== undefined && event.pressure !== 0.5,
          hasTilt: event.tiltX !== undefined || event.tiltY !== undefined,
          hasEraser: event.buttons === 32
        }
        emit('deviceDetected', deviceInfo.value)
      }

      isDrawing.value = true
      isEmpty.value = false
      currentStroke.value = []

      const point = getPoint(event)
      currentStroke.value.push(point)
      currentPressure.value = point.pressure

      emit('start', point)
    }

    const handlePointerMove = (event) => {
      if (!isDrawing.value) return

      const point = getPoint(event)
      currentStroke.value.push(point)
      currentPressure.value = point.pressure

      drawLine(
        currentStroke.value[currentStroke.value.length - 2],
        point
      )
    }

    const handlePointerUp = () => {
      if (!isDrawing.value) return

      isDrawing.value = false
      strokes.value.push([...currentStroke.value])
      currentStroke.value = []
      currentPressure.value = 0

      emitSignature()
      emit('end')
    }

    const handlePointerLeave = () => {
      if (isDrawing.value) {
        handlePointerUp()
      }
    }

    const drawLine = (from, to) => {
      const canvas = canvasRef.value
      if (!canvas || !from || !to) return

      const ctx = canvas.getContext('2d')
      ctx.beginPath()
      ctx.moveTo(from.x, from.y)
      ctx.lineTo(to.x, to.y)
      ctx.strokeStyle = props.lineColor

      // 根据压力调整线宽
      const pressureMultiplier = props.usePressure && to.pressure !== undefined ? to.pressure : 0.5
      ctx.lineWidth = props.lineWidth * (0.5 + pressureMultiplier)

      ctx.lineCap = 'round'
      ctx.lineJoin = 'round'
      ctx.stroke()
    }

    const redraw = () => {
      const canvas = canvasRef.value
      if (!canvas) return

      const ctx = canvas.getContext('2d')
      ctx.fillStyle = props.backgroundColor
      ctx.fillRect(0, 0, actualWidth.value, actualHeight.value)

      strokes.value.forEach(stroke => {
        for (let i = 1; i < stroke.length; i++) {
          drawLine(stroke[i - 1], stroke[i])
        }
      })
    }

    const clear = () => {
      strokes.value = []
      currentStroke.value = []
      isEmpty.value = true
      initCanvas()
      emitSignature()
      emit('change', null)
    }

    const undo = () => {
      if (strokes.value.length === 0) return

      strokes.value.pop()
      isEmpty.value = strokes.value.length === 0
      redraw()
      emitSignature()
    }

    const emitSignature = () => {
      const canvas = canvasRef.value
      if (!canvas) return

      const dataURL = canvas.toDataURL('image/png')
      emit('update:modelValue', dataURL)
      emit('change', dataURL)
    }

    const loadSignature = (dataURL) => {
      const canvas = canvasRef.value
      if (!canvas || !dataURL) return

      const ctx = canvas.getContext('2d')
      const img = new Image()
      img.onload = () => {
        ctx.drawImage(img, 0, 0)
        isEmpty.value = false
      }
      img.src = dataURL
    }

    const toggleDeviceReport = () => {
      showReport.value = !showReport.value
      if (showReport.value) {
        deviceReport.value = penDisplayDetector.generateReport()
      }
    }

    // Lifecycle
    onMounted(() => {
      // 计算实际画布尺寸
      if (typeof props.width === 'number') {
        actualWidth.value = props.width
      }
      if (typeof props.height === 'number') {
        actualHeight.value = props.height
      }

      initCanvas()

      // 开始监听笔设备
      penDisplayDetector.startListening(canvasRef.value, (device) => {
        console.log('[SignaturePad] 检测到笔设备:', device)
        deviceDetected.value = true
        deviceInfo.value = device
        emit('deviceDetected', device)
      })
    })

    onUnmounted(() => {
      penDisplayDetector.stopListening()
    })

    // Watch for initial data changes
    watch(() => props.initialData, (newData) => {
      if (newData) {
        loadSignature(newData)
      }
    })

    return {
      canvasRef,
      isDrawing,
      isEmpty,
      currentPressure,
      deviceDetected,
      showReport,
      deviceReport,
      canvasWidth,
      canvasHeight,
      actualWidth,
      actualHeight,
      deviceStatusClass,
      deviceStatusIcon,
      deviceStatusText,
      canUndo,
      handlePointerDown,
      handlePointerMove,
      handlePointerUp,
      handlePointerLeave,
      clear,
      undo,
      toggleDeviceReport,
      t
    }
  }
}
</script>

<style scoped>
.signature-pad-container {
  display: flex;
  flex-direction: column;
}

.device-status .alert {
  margin-bottom: 0.5rem;
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
}

.device-status .alert i {
  margin-right: 0.5rem;
}

.signature-canvas-wrapper {
  position: relative;
  border: 2px solid #dee2e6;
  border-radius: 0.375rem;
  background-color: #ffffff;
  overflow: hidden;
}

.signature-canvas {
  display: block;
  width: 100%;
  height: 100%;
  touch-action: none;
  cursor: crosshair;
}

.signature-placeholder {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #adb5bd;
  pointer-events: none;
  user-select: none;
}

.signature-placeholder i {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.signature-placeholder span {
  font-size: 0.875rem;
}

.signature-toolbar {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.signature-toolbar .btn {
  min-width: 80px;
}

.device-report {
  padding: 0.75rem;
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 0.375rem;
  overflow-x: auto;
}

.device-report pre {
  font-size: 0.75rem;
  line-height: 1.4;
  margin: 0;
}

.pressure-indicator {
  margin-top: 0.5rem;
  padding: 0.5rem;
  background-color: #f8f9fa;
  border-radius: 0.375rem;
}

.pressure-bar-container {
  width: 100%;
  height: 8px;
  background-color: #dee2e6;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.25rem;
}

.pressure-bar {
  height: 100%;
  background: linear-gradient(90deg, #28a745 0%, #ffc107 50%, #dc3545 100%);
  transition: width 0.1s ease;
}

/* 响应式调整 */
@media (max-width: 576px) {
  .signature-toolbar {
    flex-direction: column;
  }

  .signature-toolbar .btn {
    width: 100%;
  }
}
</style>

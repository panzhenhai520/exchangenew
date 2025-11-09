<template>
  <div class="container-fluid py-4">
    <div class="row">
      <div class="col-12">
        <div class="d-flex justify-content-between align-items-center mb-4">
          <h2 class="page-title-bold">
            <font-awesome-icon :icon="['fas', 'signature']" class="me-2" />
            签字板测试页面
          </h2>
        </div>

        <!-- 说明 -->
        <div class="alert alert-info mb-4">
          <h5 class="alert-heading">
            <i class="fas fa-info-circle me-2"></i>
            功能说明
          </h5>
          <p class="mb-2">此页面用于测试外接手写板/笔显示器的检测和签字功能。</p>
          <ul class="mb-0">
            <li><strong>支持设备:</strong> Wacom笔显示器、Surface Pen、Apple Pencil等支持Pointer Events的笔设备</li>
            <li><strong>压感支持:</strong> 自动检测并使用笔压力调整线条粗细</li>
            <li><strong>倾斜支持:</strong> 检测笔的倾斜角度（X/Y轴）</li>
            <li><strong>橡皮擦:</strong> 支持检测橡皮擦按钮</li>
          </ul>
        </div>

        <div class="row">
          <!-- 左侧：签字板 -->
          <div class="col-md-8">
            <div class="card mb-4">
              <div class="card-header bg-primary text-white">
                <h5 class="mb-0">
                  <i class="fas fa-pen-fancy me-2"></i>
                  签字区域
                </h5>
              </div>
              <div class="card-body">
                <SignaturePad
                  v-model="signatureData"
                  :width="'100%'"
                  :height="300"
                  :line-width="3"
                  :line-color="lineColor"
                  :background-color="backgroundColor"
                  :show-device-status="true"
                  :show-pressure-indicator="showPressure"
                  :allow-undo="true"
                  :show-device-info="true"
                  :use-pressure="usePressure"
                  @change="handleSignatureChange"
                  @start="handleDrawStart"
                  @end="handleDrawEnd"
                  @deviceDetected="handleDeviceDetected"
                />
              </div>
            </div>

            <!-- 签名预览 -->
            <div v-if="signatureData" class="card">
              <div class="card-header bg-success text-white">
                <h6 class="mb-0">
                  <i class="fas fa-image me-2"></i>
                  签名预览
                </h6>
              </div>
              <div class="card-body">
                <img :src="signatureData" alt="Signature" class="img-fluid border" />
                <div class="mt-2">
                  <small class="text-muted">
                    数据大小: {{ (signatureData.length / 1024).toFixed(2) }} KB
                  </small>
                </div>
              </div>
            </div>
          </div>

          <!-- 右侧：设置和信息 -->
          <div class="col-md-4">
            <!-- 绘图设置 -->
            <div class="card mb-4">
              <div class="card-header bg-info text-white">
                <h6 class="mb-0">
                  <i class="fas fa-cog me-2"></i>
                  绘图设置
                </h6>
              </div>
              <div class="card-body">
                <div class="mb-3">
                  <label class="form-label">线条颜色</label>
                  <input
                    type="color"
                    class="form-control form-control-color"
                    v-model="lineColor"
                  />
                </div>
                <div class="mb-3">
                  <label class="form-label">背景颜色</label>
                  <input
                    type="color"
                    class="form-control form-control-color"
                    v-model="backgroundColor"
                  />
                </div>
                <div class="form-check mb-2">
                  <input
                    type="checkbox"
                    class="form-check-input"
                    id="usePressure"
                    v-model="usePressure"
                  />
                  <label class="form-check-label" for="usePressure">
                    使用压感调整线宽
                  </label>
                </div>
                <div class="form-check">
                  <input
                    type="checkbox"
                    class="form-check-input"
                    id="showPressure"
                    v-model="showPressure"
                  />
                  <label class="form-check-label" for="showPressure">
                    显示压力指示器
                  </label>
                </div>
              </div>
            </div>

            <!-- 设备信息 -->
            <div class="card mb-4">
              <div class="card-header bg-warning text-dark">
                <h6 class="mb-0">
                  <i class="fas fa-tablet-alt me-2"></i>
                  设备信息
                </h6>
              </div>
              <div class="card-body">
                <div v-if="deviceInfo">
                  <div class="mb-2">
                    <strong>Pointer ID:</strong> {{ deviceInfo.pointerId }}
                  </div>
                  <div class="mb-2">
                    <strong>压感支持:</strong>
                    <span :class="deviceInfo.hasPressure ? 'text-success' : 'text-danger'">
                      {{ deviceInfo.hasPressure ? '✓ 支持' : '✗ 不支持' }}
                    </span>
                  </div>
                  <div v-if="deviceInfo.hasPressure" class="mb-2">
                    <strong>当前压力:</strong>
                    {{ (deviceInfo.pressure * 100).toFixed(0) }}%
                  </div>
                  <div class="mb-2">
                    <strong>倾斜支持:</strong>
                    <span :class="deviceInfo.hasTilt ? 'text-success' : 'text-danger'">
                      {{ deviceInfo.hasTilt ? '✓ 支持' : '✗ 不支持' }}
                    </span>
                  </div>
                  <div v-if="deviceInfo.hasTilt" class="mb-2">
                    <strong>倾斜角度:</strong>
                    X: {{ deviceInfo.tiltX }}°, Y: {{ deviceInfo.tiltY }}°
                  </div>
                  <div class="mb-2">
                    <strong>橡皮擦:</strong>
                    <span :class="deviceInfo.hasEraser ? 'text-success' : 'text-muted'">
                      {{ deviceInfo.hasEraser ? '✓ 激活' : '— 未使用' }}
                    </span>
                  </div>
                  <div class="mb-2">
                    <strong>设备尺寸:</strong>
                    {{ deviceInfo.width }} × {{ deviceInfo.height }} px
                  </div>
                </div>
                <div v-else class="text-muted">
                  <i class="fas fa-info-circle me-2"></i>
                  等待笔输入检测设备...
                </div>
              </div>
            </div>

            <!-- 统计信息 -->
            <div class="card">
              <div class="card-header bg-secondary text-white">
                <h6 class="mb-0">
                  <i class="fas fa-chart-line me-2"></i>
                  绘图统计
                </h6>
              </div>
              <div class="card-body">
                <div class="mb-2">
                  <strong>绘制次数:</strong> {{ drawCount }}
                </div>
                <div class="mb-2">
                  <strong>签名状态:</strong>
                  <span :class="signatureData ? 'text-success' : 'text-muted'">
                    {{ signatureData ? '已签名' : '未签名' }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import SignaturePad from '@/components/amlo/SignaturePad.vue'

export default {
  name: 'SignaturePadTest',
  components: {
    SignaturePad
  },
  setup() {
    const signatureData = ref(null)
    const lineColor = ref('#000000')
    const backgroundColor = ref('#ffffff')
    const usePressure = ref(true)
    const showPressure = ref(true)
    const deviceInfo = ref(null)
    const drawCount = ref(0)

    const handleSignatureChange = (data) => {
      console.log('[SignaturePadTest] 签名数据已更新', data ? `${(data.length / 1024).toFixed(2)} KB` : 'null')
    }

    const handleDrawStart = (point) => {
      console.log('[SignaturePadTest] 开始绘制', point)
      drawCount.value++
    }

    const handleDrawEnd = () => {
      console.log('[SignaturePadTest] 结束绘制')
    }

    const handleDeviceDetected = (device) => {
      console.log('[SignaturePadTest] 检测到笔设备', device)
      deviceInfo.value = device
    }

    return {
      signatureData,
      lineColor,
      backgroundColor,
      usePressure,
      showPressure,
      deviceInfo,
      drawCount,
      handleSignatureChange,
      handleDrawStart,
      handleDrawEnd,
      handleDeviceDetected
    }
  }
}
</script>

<style scoped>
.page-title-bold {
  font-weight: 700;
  color: #212529;
}

.card-header h5,
.card-header h6 {
  margin: 0;
}

.form-control-color {
  width: 100%;
  height: 38px;
}
</style>

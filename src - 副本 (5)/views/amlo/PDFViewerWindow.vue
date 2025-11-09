<template>
  <div class="pdf-viewer-window">
    <!-- Header (Title Only) -->
    <div class="pdf-header">
      <div class="header-left">
        <i class="fas fa-file-pdf me-2"></i>
        <span>{{ title }}</span>
        <span v-if="reportType" class="badge bg-light text-dark ms-2">{{ reportType }}</span>
      </div>
    </div>

    <!-- PDF Content Area -->
    <div class="pdf-content">
      <!-- Loading State -->
      <div v-if="loading" class="loading-container">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">{{ t('common.loading') }}</span>
        </div>
        <p class="mt-3 text-muted">{{ t('amlo.pdfViewer.loadingPDF') }}</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="error-container">
        <div class="alert alert-danger m-4">
          <i class="fas fa-exclamation-triangle me-2"></i>
          {{ error }}
        </div>
        <button class="btn btn-primary" @click="loadPDF">
          <i class="fas fa-redo me-2"></i>{{ t('common.retry') }}
        </button>
      </div>

      <!-- PDF Display (Full Screen, No Pagination Preview) -->
      <div v-else-if="pdfUrl" class="pdf-display">
        <iframe
          :src="pdfUrl + '#toolbar=0&navpanes=0&scrollbar=1'"
          class="pdf-iframe"
          :title="title || t('amlo.pdfViewer.pdfDocument')"
        ></iframe>
      </div>

      <!-- Empty State -->
      <div v-else class="empty-container">
        <i class="fas fa-file-pdf fa-4x text-muted mb-3"></i>
        <p class="text-muted">{{ t('amlo.pdfViewer.noPDFLoaded') }}</p>
      </div>

      <!-- Signature Overlay -->
      <div v-if="showSignaturePad" class="signature-overlay">
        <div class="signature-modal-content">
          <div class="signature-header">
            <h5>
              <i class="fas fa-signature me-2"></i>{{ t('amlo.signature.title') || '签名' }}
            </h5>
            <button type="button" class="btn-close" @click="closeSignaturePad"></button>
          </div>
          <div class="signature-body">
            <SignaturePad
              ref="signaturePadRef"
              :width="600"
              :height="300"
              :lineWidth="2"
              :lineColor="'#000000'"
            />
          </div>
          <div class="signature-footer">
            <button type="button" class="btn btn-warning" @click="closeSignaturePad">
              <i class="fas fa-times me-2"></i>{{ t('common.cancel') }}
            </button>
            <button type="button" class="btn btn-warning" @click="saveSignature">
              <i class="fas fa-check me-2"></i>{{ t('common.confirm') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Action Buttons Footer (统一橙色) -->
    <div class="pdf-footer">
      <!-- 扩展显示器提示 (显示在底部左侧) -->
      <div v-if="showSecondScreenHint" class="extended-screen-hint">
        <i class="fas fa-tv me-2"></i>
        <span>按 <kbd>Win</kbd>+<kbd>Shift</kbd>+<kbd>→</kbd> 移动到副屏</span>
        <button type="button" class="btn-close-hint" @click="closeHint">
          <i class="fas fa-times"></i>
        </button>
      </div>

      <!-- 全屏按钮 - 简化文案 -->
      <button
        type="button"
        class="btn btn-success btn-lg fullscreen-btn"
        @click="toggleFullscreen"
        :title="'全屏显示 (F11)'"
      >
        <i class="fas fa-expand me-2"></i>全屏 <kbd class="ms-2">F11</kbd>
      </button>

      <button
        v-if="pdfUrl && allowSignature"
        type="button"
        class="btn btn-warning btn-lg"
        @click="openSignaturePad"
        :disabled="signatureSaved"
      >
        <i class="fas fa-signature me-2"></i>
        {{ signatureSaved ? (t('amlo.signature.signed') || '已签名') : (t('amlo.signature.sign') || '签名') }}
      </button>
      <!-- 提交按钮已移除：签名点击确定后自动提交 -->
      <button type="button" class="btn btn-warning btn-lg" @click="closeWindow">
        <i class="fas fa-times me-2"></i>{{ t('common.close') }}
      </button>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import api from '@/services/api'
import SignaturePad from '@/components/amlo/SignaturePad.vue'

export default {
  name: 'PDFViewerWindow',
  components: {
    SignaturePad
  },
  setup() {
    const { t } = useI18n()
    const route = useRoute()

    const loading = ref(false)
    const error = ref(null)
    const pdfUrl = ref(null)
    const downloading = ref(false)
    const showSignaturePad = ref(false)
    const signatureSaved = ref(false)
    const signatureData = ref(null)
    const submitting = ref(false)
    const signaturePadRef = ref(null)
    const showSecondScreenHint = ref(false)  // 扩展显示器提示
    const positionCheckTimer = ref(null)  // 窗口位置检测定时器

    const title = ref('')
    const reportType = ref('')
    const reservationId = ref(null)
    const allowPrint = ref(true)
    const allowSignature = ref(true)
    const readonly = ref(false)  // 只读模式标志

    const loadPDF = async () => {
      // Get reservation ID from URL query parameter
      reservationId.value = route.query.id
      title.value = route.query.title || 'AMLO Report'
      reportType.value = route.query.reportType || ''
      // 读取只读模式参数（在报告管理页面查看时为只读）
      readonly.value = route.query.readonly === 'true'
      // 只读模式下禁用签名功能
      if (readonly.value) {
        allowSignature.value = false
        console.log('[PDFViewerWindow] 只读模式已启用，签名和提交按钮将被隐藏')
      }

      if (!reservationId.value) {
        error.value = 'Invalid reservation ID'
        return
      }

      loading.value = true
      error.value = null

      try {
        console.log('[PDFViewerWindow] Loading PDF for reservation:', reservationId.value)

        // Force refresh parameter to prevent caching
        const timestamp = new Date().getTime()
        const response = await api.get(
          `/amlo/reservations/${reservationId.value}/generate-pdf?refresh=${timestamp}`,
          { responseType: 'blob' }
        )

        console.log('[PDFViewerWindow] PDF loaded successfully, size:', response.data.size)

        // Create Blob URL
        const blob = new Blob([response.data], { type: 'application/pdf' })
        pdfUrl.value = URL.createObjectURL(blob)

        console.log('[PDFViewerWindow] PDF URL created:', pdfUrl.value)
      } catch (err) {
        console.error('[PDFViewerWindow] Failed to load PDF:', err)
        error.value = t('amlo.pdfViewer.loadError') + ': ' + (err.response?.data?.message || err.message)
      } finally {
        loading.value = false
      }
    }

    const downloadPDF = async () => {
      if (!pdfUrl.value) return

      downloading.value = true
      try {
        const response = await fetch(pdfUrl.value)
        const blob = await response.blob()

        const link = document.createElement('a')
        link.href = URL.createObjectURL(blob)
        link.download = `${reportType.value || 'AMLO'}_${new Date().getTime()}.pdf`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(link.href)
      } catch (err) {
        console.error('[PDFViewerWindow] Download failed:', err)
        alert(t('amlo.pdfViewer.downloadError'))
      } finally {
        downloading.value = false
      }
    }

    const printPDF = () => {
      if (!pdfUrl.value) return
      window.print()
    }

    const openSignaturePad = () => {
      showSignaturePad.value = true
    }

    const closeSignaturePad = () => {
      showSignaturePad.value = false
    }

    const saveSignature = async () => {
      if (signaturePadRef.value) {
        const data = signaturePadRef.value.toDataURL()
        signatureData.value = data
        signatureSaved.value = true
        showSignaturePad.value = false
        console.log('[PDFViewerWindow] Signature saved, auto-submitting...')

        // 立即自动提交签名（不需要用户再点提交按钮）
        await submitSignature()
      }
    }

    const submitSignature = async () => {
      if (!signatureData.value || !reservationId.value) return

      submitting.value = true
      try {
        // Auto-fill reporter_date with current date in dd/mm/yyyy format
        const now = new Date()
        const day = String(now.getDate()).padStart(2, '0')
        const month = String(now.getMonth() + 1).padStart(2, '0')
        const year = now.getFullYear()
        const reporterDate = `${day}/${month}/${year}`

        console.log('[PDFViewerWindow] Submitting signature with date:', reporterDate)

        await api.post(`/amlo/reservations/${reservationId.value}/signature`, {
          signature: signatureData.value,
          reporter_date: reporterDate
        })

        console.log('[PDFViewerWindow] ✅ 签名提交成功')

        // 静默刷新PDF（不显示提示）
        console.log('[PDFViewerWindow] Reloading PDF to show signature...')
        await loadPDF()

        // 刷新后确保窗口最大化
        maximizeWindow()

        console.log('[PDFViewerWindow] ✅ PDF已更新，签名已显示')
      } catch (error) {
        console.error('[PDFViewerWindow] Submit signature error:', error)
        // 只在失败时显示提示
        alert(t('amlo.signature.submitFailed') || '签名提交失败: ' + (error.response?.data?.message || error.message))
      } finally {
        submitting.value = false
      }
    }

    // 窗口最大化函数
    const maximizeWindow = () => {
      try {
        console.log('[PDFViewerWindow] 尝试最大化窗口...')

        // 方法1: 使用resizeTo设置为屏幕可用尺寸
        const screenWidth = window.screen.availWidth
        const screenHeight = window.screen.availHeight

        window.resizeTo(screenWidth, screenHeight)
        window.moveTo(0, 0)

        console.log('[PDFViewerWindow] resizeTo:', screenWidth, 'x', screenHeight)

        // 方法2: 如果窗口不在扩展显示器上，尝试移动
        const windowLeft = window.screenX || window.screenLeft
        const primaryScreenWidth = 1620

        if (windowLeft < primaryScreenWidth) {
          // 尝试移动到扩展显示器
          const secondScreenLeft = primaryScreenWidth
          window.moveTo(secondScreenLeft, 0)
          window.resizeTo(1920, 1080)
          console.log('[PDFViewerWindow] 尝试移动到扩展显示器:', secondScreenLeft)
        }

        // 方法3: 尝试全屏API（作为备选）
        if (document.documentElement.requestFullscreen) {
          // 注意：全屏API需要用户手势触发，所以这里可能不会立即生效
          // 但作为备选方案保留
          console.log('[PDFViewerWindow] 全屏API可用')
        }

        console.log('[PDFViewerWindow] 最大化完成')
      } catch (e) {
        console.error('[PDFViewerWindow] 最大化失败:', e)
      }
    }

    const closeWindow = () => {
      window.close()
    }

    // 关闭提示框
    const closeHint = () => {
      showSecondScreenHint.value = false
      stopPositionMonitoring()
    }

    // 检查窗口是否在扩展屏上
    const isOnExtendedScreen = () => {
      const currentLeft = window.screenX || window.screenLeft
      const primaryScreenWidth = 1620
      return currentLeft >= primaryScreenWidth
    }

    // 启动窗口位置监控（当提示显示时，定期检查窗口是否移动到扩展屏）
    const startPositionMonitoring = () => {
      // 清除已存在的定时器
      if (positionCheckTimer.value) {
        clearInterval(positionCheckTimer.value)
      }

      console.log('[PDFViewerWindow] 启动窗口位置监控')

      // 每2秒检查一次窗口位置
      positionCheckTimer.value = setInterval(() => {
        if (isOnExtendedScreen()) {
          console.log('[PDFViewerWindow] 检测到窗口已移动到扩展屏，自动隐藏提示')
          showSecondScreenHint.value = false
          stopPositionMonitoring()
        }
      }, 2000)
    }

    // 停止窗口位置监控
    const stopPositionMonitoring = () => {
      if (positionCheckTimer.value) {
        console.log('[PDFViewerWindow] 停止窗口位置监控')
        clearInterval(positionCheckTimer.value)
        positionCheckTimer.value = null
      }
    }

    // 全屏切换函数（简化版：直接全屏，不再尝试移动）
    const toggleFullscreen = async () => {
      try {
        if (!document.fullscreenElement) {
          console.log('[PDFViewerWindow] 进入全屏模式')

          // 直接进入全屏，不再尝试移动窗口
          await document.documentElement.requestFullscreen()
          console.log('[PDFViewerWindow] ✅ 已进入全屏模式')

          // 只读模式（报告管理页面）不显示扩展屏提示
          if (!readonly.value) {
            // 检测窗口位置，如果在主屏幕则显示提示
            if (!isOnExtendedScreen() && !showSecondScreenHint.value) {
              // 延迟显示提示，避免在进入全屏动画时显示
              setTimeout(() => {
                showSecondScreenHint.value = true
                console.log('[PDFViewerWindow] 显示扩展屏提示')
                startPositionMonitoring()  // 启动位置监控
              }, 1000)
            }
          } else {
            console.log('[PDFViewerWindow] 只读模式，不显示扩展屏提示')
          }

        } else {
          // 退出全屏
          await document.exitFullscreen()
          console.log('[PDFViewerWindow] 已退出全屏模式')
        }
      } catch (e) {
        console.error('[PDFViewerWindow] 全屏操作失败:', e)
        alert('全屏失败，请按 F11 键进入全屏')
      }
    }

    onMounted(() => {
      loadPDF()
      console.log('[PDFViewerWindow] Window opened at:', new Date().toISOString())

      // 立即尝试最大化窗口
      setTimeout(() => {
        maximizeWindow()
      }, 100)

      // 检测窗口位置，如果不在扩展显示器上，显示提示（只读模式除外）
      setTimeout(() => {
        // 只读模式（报告管理页面）不显示扩展屏提示
        if (readonly.value) {
          console.log('[PDFViewerWindow] 只读模式，不显示扩展屏提示')
          return
        }

        console.log('[PDFViewerWindow] Window position:', {
          screenX: window.screenX,
          screenLeft: window.screenLeft
        })

        // 如果窗口在主屏幕上，显示提示并启动监控
        if (!isOnExtendedScreen()) {
          console.log('[PDFViewerWindow] 窗口在主屏幕上，显示扩展显示器提示')
          showSecondScreenHint.value = true
          startPositionMonitoring()  // 启动位置监控，自动检测窗口移动
        } else {
          console.log('[PDFViewerWindow] 窗口已在扩展显示器上')
        }
      }, 1000)

      // 监听F11键进行全屏切换
      const handleKeyPress = (e) => {
        if (e.key === 'F11') {
          e.preventDefault()
          toggleFullscreen()
        }
      }
      window.addEventListener('keydown', handleKeyPress)

      // 监听窗口大小变化
      window.addEventListener('resize', () => {
        console.log('[PDFViewerWindow] Window resized:', window.innerWidth, 'x', window.innerHeight)
      })

      // 清理函数
      return () => {
        window.removeEventListener('keydown', handleKeyPress)
      }
    })

    // 组件卸载时清理定时器
    onUnmounted(() => {
      console.log('[PDFViewerWindow] 组件卸载，清理定时器')
      stopPositionMonitoring()
    })

    return {
      t,
      loading,
      error,
      pdfUrl,
      downloading,
      showSignaturePad,
      signatureSaved,
      submitting,
      signaturePadRef,
      showSecondScreenHint,
      title,
      reportType,
      allowPrint,
      allowSignature,
      loadPDF,
      downloadPDF,
      printPDF,
      openSignaturePad,
      closeSignaturePad,
      saveSignature,
      submitSignature,
      closeWindow,
      closeHint,
      toggleFullscreen
    }
  }
}
</script>

<style scoped>
.pdf-viewer-window {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background-color: #2c3e50;
}

.pdf-header {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 1rem;
  background-color: #0d6efd;
  color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header-left {
  display: flex;
  align-items: center;
  font-size: 1.1rem;
  font-weight: 600;
}

.pdf-content {
  flex: 1;
  display: flex;
  overflow: hidden;
  position: relative;
  padding-bottom: 80px; /* Space for footer */
}

.loading-container,
.error-container,
.empty-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background-color: #ecf0f1;
}

.pdf-display {
  width: 100%;
  height: 100%;
  background-color: #525252;
}

.pdf-iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.signature-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.signature-modal-content {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  width: 90%;
  max-width: 700px;
}

.signature-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #dee2e6;
}

.signature-header h5 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
}

.signature-body {
  padding: 1.5rem;
  display: flex;
  justify-content: center;
}

.signature-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid #dee2e6;
}

/* Action Buttons Footer (统一橙色按钮) */
.pdf-footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 1rem;
  background: white;
  border-top: 2px solid #dee2e6;
  display: flex;
  justify-content: center;
  gap: 1rem;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
  z-index: 1000;
}

.pdf-footer .btn {
  min-width: 120px;
}

/* 全屏按钮高亮 */
.fullscreen-btn {
  animation: pulse-green 2s infinite;
  font-weight: 600;
}

.fullscreen-btn kbd {
  background-color: #fff;
  color: #198754;
  padding: 0.15rem 0.4rem;
  border-radius: 0.25rem;
  font-size: 0.8rem;
  border: 1px solid #198754;
}

@keyframes pulse-green {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(25, 135, 84, 0.7);
  }
  50% {
    box-shadow: 0 0 0 10px rgba(25, 135, 84, 0);
  }
}

/* Print styles */
@media print {
  .pdf-header,
  .pdf-footer {
    display: none;
  }

  .pdf-content {
    height: 100vh;
    padding-bottom: 0;
  }

  .pdf-iframe {
    height: 100vh;
  }
}

/* 扩展显示器提示 - 底部左侧提示 */
.extended-screen-hint {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: linear-gradient(135deg, #fff3cd 0%, #ffe8a1 100%);
  border: 2px solid #ffc107;
  border-radius: 0.5rem;
  color: #856404;
  font-size: 0.9rem;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(255, 193, 7, 0.3);
  margin-right: auto;
  animation: fadeInLeft 0.5s ease-out;
}

.extended-screen-hint .fa-tv {
  color: #ff9800;
  font-size: 1.2rem;
}

.extended-screen-hint kbd {
  padding: 0.2rem 0.4rem;
  font-size: 0.85rem;
  font-weight: 700;
  background: #fff;
  color: #856404;
  border: 1px solid #ffc107;
  border-radius: 0.25rem;
  box-shadow: 0 2px 0 #ffc107;
  font-family: 'Courier New', monospace;
}

.btn-close-hint {
  background: none;
  border: none;
  color: #856404;
  cursor: pointer;
  padding: 0.25rem;
  margin-left: 0.5rem;
  opacity: 0.7;
  transition: opacity 0.2s;
}

.btn-close-hint:hover {
  opacity: 1;
}

.btn-close-hint i {
  font-size: 0.9rem;
}

@keyframes fadeInLeft {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}
</style>

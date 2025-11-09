<template>
  <div class="pdf-viewer-window">
    <!-- 扩展显示器提示 (如果窗口不在扩展显示器上) -->
    <div v-if="showSecondScreenHint" class="second-screen-hint">
      <div class="alert alert-info alert-dismissible fade show m-2" role="alert">
        <i class="fas fa-desktop me-2"></i>
        <strong>提示：</strong> 要将此窗口移动到扩展显示器（笔屏），请按 <kbd>Win</kbd> + <kbd>Shift</kbd> + <kbd>→</kbd>
        <button type="button" class="btn-close" @click="showSecondScreenHint = false"></button>
      </div>
    </div>

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
      <!-- 全屏按钮 -->
      <button
        type="button"
        class="btn btn-success btn-lg"
        @click="toggleFullscreen"
        :title="t('common.fullscreen') || '全屏显示'"
      >
        <i class="fas fa-expand me-2"></i>{{ t('common.fullscreen') || '全屏' }}
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
import { ref, onMounted } from 'vue'
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

    const title = ref('')
    const reportType = ref('')
    const reservationId = ref(null)
    const allowPrint = ref(true)
    const allowSignature = ref(true)

    const loadPDF = async () => {
      // Get reservation ID from URL query parameter
      reservationId.value = route.query.id
      title.value = route.query.title || 'AMLO Report'
      reportType.value = route.query.reportType || ''

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

    // 全屏切换函数
    const toggleFullscreen = () => {
      try {
        if (!document.fullscreenElement) {
          // 进入全屏
          document.documentElement.requestFullscreen()
            .then(() => {
              console.log('[PDFViewerWindow] ✅ 已进入全屏模式')
            })
            .catch((err) => {
              console.error('[PDFViewerWindow] ❌ 全屏失败:', err)
              alert('无法进入全屏模式，请按F11键手动全屏')
            })
        } else {
          // 退出全屏
          document.exitFullscreen()
            .then(() => {
              console.log('[PDFViewerWindow] 已退出全屏模式')
            })
        }
      } catch (e) {
        console.error('[PDFViewerWindow] 全屏功能不可用:', e)
        alert('您的浏览器不支持全屏功能，请按F11键手动全屏')
      }
    }

    onMounted(() => {
      loadPDF()
      console.log('[PDFViewerWindow] Window opened at:', new Date().toISOString())

      // 立即尝试最大化窗口
      setTimeout(() => {
        maximizeWindow()
      }, 100)

      // 检测窗口位置，如果不在扩展显示器上，显示提示
      setTimeout(() => {
        const windowLeft = window.screenX || window.screenLeft
        const primaryScreenWidth = 1620  // 用户的主屏幕宽度

        console.log('[PDFViewerWindow] Window position:', {
          screenX: window.screenX,
          screenLeft: window.screenLeft,
          actualLeft: windowLeft,
          primaryScreenWidth: primaryScreenWidth
        })

        // 如果窗口左边距小于主屏幕宽度，说明还在主屏幕上
        if (windowLeft < primaryScreenWidth) {
          console.log('[PDFViewerWindow] 窗口在主屏幕上，显示扩展显示器提示')
          showSecondScreenHint.value = true

          // 10秒后自动隐藏提示
          setTimeout(() => {
            showSecondScreenHint.value = false
          }, 10000)
        } else {
          console.log('[PDFViewerWindow] 窗口已在扩展显示器上')
        }
      }, 1000)

      // 监听窗口大小变化，确保始终最大化
      window.addEventListener('resize', () => {
        console.log('[PDFViewerWindow] Window resized:', window.innerWidth, 'x', window.innerHeight)
      })
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

/* 扩展显示器提示 */
.second-screen-hint {
  position: fixed;
  top: 70px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 9999;
  min-width: 400px;
  max-width: 600px;
}

.second-screen-hint .alert {
  font-size: 1rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  animation: slideDown 0.5s ease-out;
}

.second-screen-hint kbd {
  padding: 0.2rem 0.4rem;
  font-size: 0.9rem;
  background-color: #e9ecef;
  border: 1px solid #adb5bd;
  border-radius: 0.25rem;
  box-shadow: 0 2px 0 rgba(0, 0, 0, 0.1);
}

@keyframes slideDown {
  from {
    transform: translateY(-100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
</style>

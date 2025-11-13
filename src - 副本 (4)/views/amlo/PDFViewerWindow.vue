<template>
  <div class="pdf-viewer-window">
    <div class="pdf-header">
      <div class="header-left">
        <i class="fas fa-file-pdf me-2"></i>
        <span>{{ title }}</span>
        <span v-if="reportType" class="badge bg-light text-dark ms-2">{{ reportType }}</span>
      </div>
    </div>

    <div class="pdf-content">
      <div v-if="loading" class="loading-container">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">{{ t('common.loading') }}</span>
        </div>
        <p class="mt-3 text-muted">{{ t('amlo.pdfViewer.loadingPDF') }}</p>
      </div>

      <div v-else-if="error" class="error-container">
        <div class="alert alert-danger m-4">
          <i class="fas fa-exclamation-triangle me-2"></i>
          {{ error }}
        </div>
        <button class="btn btn-primary" @click="loadPDF">
          <i class="fas fa-redo me-2"></i>{{ t('common.retry') }}
        </button>
      </div>

      <div v-else-if="pdfUrl" class="pdf-display">
        <iframe :src="pdfUrl + '#toolbar=0&navpanes=0&scrollbar=1'" class="pdf-iframe" :title="title || t('amlo.pdfViewer.pdfDocument')"></iframe>
      </div>

      <div v-else class="empty-container">
        <i class="fas fa-file-pdf fa-4x text-muted mb-3"></i>
        <p class="text-muted">{{ t('amlo.pdfViewer.noPDFLoaded') }}</p>
      </div>
    </div>

    <div class="pdf-footer">
      <div class="footer-hint">
        <i class="fas fa-info-circle me-2"></i>
        <span>需要在扩展屏给客户签名时，按 Win + Shift + →</span>
      </div>
      <div class="footer-actions">
        <button type="button" class="btn btn-warning" @click="openSignaturePad" :disabled="!pdfUrl || submitting">
          <span v-if="submitting" class="spinner-border spinner-border-sm me-2"></span>
          <i v-else class="fas fa-signature me-2"></i>
          {{ submitting ? (t('common.submitting') || '提交中...') : (t('amlo.signature.sign') || '签名') }}
        </button>
        <button type="button" class="btn btn-secondary" @click="cancelAndCloseWindow">
          <i class="fas fa-times me-2"></i>{{ t('common.cancel') || '取消' }}
        </button>
        <button type="button" class="btn btn-success" @click="closeWindow">
          <i class="fas fa-check-circle me-2"></i>{{ t('reservation.submit_reservation') || '提交预约' }}
        </button>
      </div>
    </div>

    <div v-if="showSignaturePad" class="signature-overlay">
      <div class="signature-modal-content">
        <div class="signature-header">
          <h5><i class="fas fa-pen me-2"></i>{{ t('amlo.signature.title') || '签名' }}</h5>
          <button type="button" class="btn-close" @click="closeSignaturePad"></button>
        </div>
        <div class="signature-body">
          <SignaturePad ref="signaturePadRef" :width="700" :height="320" :lineWidth="2" lineColor="#000000" />
        </div>
        <div class="signature-footer">
          <button type="button" class="btn btn-outline-secondary" @click="clearSignature">
            <i class="fas fa-undo me-2"></i>{{ t('common.reset') || '重新签名' }}
          </button>
          <button type="button" class="btn btn-primary" @click="saveSignature">
            <i class="fas fa-check me-2"></i>{{ t('common.confirm') || '确定' }}
          </button>
        </div>
      </div>
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
  components: { SignaturePad },
  setup () {
    const { t } = useI18n()
    const route = useRoute()

    const loading = ref(false)
    const error = ref(null)
    const pdfUrl = ref(null)
    const showSignaturePad = ref(false)
    const signatureData = ref(null)
    const signaturePadRef = ref(null)
    const submitting = ref(false)

    const title = ref('')
    const reportType = ref('')
    const reservationId = ref(null)

    const loadPDF = async (forceGenerated = false) => {
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
        const timestamp = Date.now()

        // 如果不是强制加载生成的PDF，优先尝试加载用户上传的PDF
        if (!forceGenerated) {
          try {
            console.log('[PDFViewerWindow] 尝试加载上传的PDF...')
            const uploadedResponse = await api.get(`/amlo/reservations/${reservationId.value}/uploaded-pdf?cache=${timestamp}`, {
              responseType: 'blob'
            })

            if (uploadedResponse.data && uploadedResponse.data.size > 0) {
              console.log('[PDFViewerWindow] ✅ 找到上传的PDF，使用上传的版本')
              const blob = new Blob([uploadedResponse.data], { type: 'application/pdf' })
              if (pdfUrl.value) {
                URL.revokeObjectURL(pdfUrl.value)
              }
              pdfUrl.value = URL.createObjectURL(blob)
              loading.value = false
              return
            }
          } catch (uploadErr) {
            console.log('[PDFViewerWindow] 没有找到上传的PDF，使用生成的PDF:', uploadErr.response?.status)
          }
        }

        // 加载生成的PDF（签名后的版本）
        console.log('[PDFViewerWindow] 加载生成的PDF...')
        const response = await api.get(`/amlo/reservations/${reservationId.value}/generate-pdf?refresh=${timestamp}`, {
          responseType: 'blob'
        })
        const blob = new Blob([response.data], { type: 'application/pdf' })
        if (pdfUrl.value) {
          URL.revokeObjectURL(pdfUrl.value)
        }
        pdfUrl.value = URL.createObjectURL(blob)
      } catch (err) {
        console.error('[PDFViewerWindow] Failed to load PDF:', err)
        error.value = t('amlo.pdfViewer.loadError') + ': ' + (err.response?.data?.message || err.message)
      } finally {
        loading.value = false
      }
    }

    const openSignaturePad = async () => {
      if (!pdfUrl.value) return

      // 🔧 先进入全屏模式，然后再显示签名窗口
      try {
        if (!document.fullscreenElement) {
          await document.documentElement.requestFullscreen?.()
          console.log('[PDFViewerWindow] ✅ 已进入全屏模式')
        }
      } catch (err) {
        console.warn('[PDFViewerWindow] 全屏请求失败，继续显示签名窗口:', err)
      }

      // 延迟一下再显示签名窗口，确保全屏动画完成
      setTimeout(() => {
        showSignaturePad.value = true
        setTimeout(() => {
          signaturePadRef.value?.clear()
          signatureData.value = null
        }, 50)
      }, 100)
    }

    const closeSignaturePad = () => {
      showSignaturePad.value = false
    }

    const clearSignature = () => {
      signaturePadRef.value?.clear()
      signatureData.value = null
    }

    const saveSignature = async () => {
      if (!signaturePadRef.value) return
      signatureData.value = signaturePadRef.value.toDataURL()
      showSignaturePad.value = false

      // 🔧 签名确认后自动提交并刷新PDF
      if (signatureData.value && reservationId.value) {
        submitting.value = true
        try {
          const now = new Date()
          const reporterDate = `${String(now.getDate()).padStart(2, '0')}/${String(now.getMonth() + 1).padStart(2, '0')}/${now.getFullYear()}`

          console.log('[PDFViewerWindow] 自动提交签名...')
          await api.post(`/amlo/reservations/${reservationId.value}/signature`, {
            signature: signatureData.value,
            reporter_date: reporterDate
          })

          console.log('[PDFViewerWindow] ✅ 签名提交成功，刷新PDF...')
          // 签名提交成功后，强制加载生成的PDF（包含签名的版本）
          await loadPDF(true)
          signatureData.value = null

          console.log('[PDFViewerWindow] ✅ PDF已刷新，签名已显示')

          // 🔧 通知父窗口：签名提交成功，可以显示"预约已提交"消息了
          try {
            if (window.opener && !window.opener.closed) {
              console.log('[PDFViewerWindow] 通知父窗口签名提交成功...')
              window.opener.postMessage({
                type: 'SIGNATURE_SUBMITTED',
                reservation_id: reservationId.value,
                report_type: reportType.value
              }, '*')
            }
          } catch (notifyErr) {
            console.warn('[PDFViewerWindow] 无法通知父窗口:', notifyErr)
          }
        } catch (err) {
          console.error('[PDFViewerWindow] 自动提交签名失败:', err)
          alert(t('amlo.signature.submitFailed') || err.response?.data?.message || err.message)
        } finally {
          submitting.value = false
        }
      }
    }

    const cancelAndCloseWindow = () => {
      console.log('[PDFViewerWindow] 取消并关闭PDF窗口（不关闭父窗口）...')
      // 只关闭PDF窗口，不通知父窗口关闭ReservationModal
      window.close()
    }

    const closeWindow = () => {
      console.log('[PDFViewerWindow] 提交预约并关闭所有窗口...')

      // 🔧 通知父窗口关闭ReservationModal
      try {
        if (window.opener && !window.opener.closed) {
          console.log('[PDFViewerWindow] 通知父窗口关闭ReservationModal...')
          // 通过postMessage发送关闭消息给父窗口
          window.opener.postMessage({ type: 'CLOSE_RESERVATION_MODAL' }, '*')
        }
      } catch (err) {
        console.warn('[PDFViewerWindow] 无法访问父窗口:', err)
      }

      // 关闭当前PDF窗口
      window.close()
    }

    const maximizeWindow = () => {
      try {
        console.log('[PDFViewerWindow] 尝试最大化窗口...')

        // 方法1: 使用resizeTo和moveTo（可能被浏览器限制）
        const screenWidth = window.screen.availWidth
        const screenHeight = window.screen.availHeight
        console.log('[PDFViewerWindow] 屏幕尺寸:', { width: screenWidth, height: screenHeight })

        window.resizeTo(screenWidth, screenHeight)
        window.moveTo(0, 0)

        // 方法2: 如果支持，尝试使用maximize（仅某些浏览器支持）
        if (window.maximize) {
          window.maximize()
        }

        // 方法3: 设置窗口外观尺寸
        if (window.outerWidth < screenWidth || window.outerHeight < screenHeight) {
          console.log('[PDFViewerWindow] 当前窗口尺寸:', {
            width: window.outerWidth,
            height: window.outerHeight
          })
          window.resizeTo(screenWidth, screenHeight)
        }

        console.log('[PDFViewerWindow] ✅ 窗口最大化完成')
      } catch (err) {
        console.warn('[PDFViewerWindow] 窗口最大化失败:', err)
      }
    }

    onMounted(() => {
      loadPDF()
      setTimeout(maximizeWindow, 200)
    })

    return {
      t,
      loading,
      error,
      pdfUrl,
      showSignaturePad,
      signaturePadRef,
      signatureData,
      submitting,
      title,
      reportType,
      loadPDF,
      openSignaturePad,
      closeSignaturePad,
      clearSignature,
      saveSignature,
      cancelAndCloseWindow,
      closeWindow
    }
  }
}
</script>

<style scoped>
/* PDF查看器窗口 - 全屏自适应 */
.pdf-viewer-window {
  display: flex;
  flex-direction: column;
  width: 100vw;
  height: 100vh;
  margin: 0;
  padding: 0;
  overflow: hidden;
  background-color: #2c3e50;
}

/* PDF头部 */
.pdf-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 20px;
  background-color: #34495e;
  color: white;
  border-bottom: 2px solid #1abc9c;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: 500;
}

/* PDF内容区域 - 占据剩余空间 */
.pdf-content {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
  background-color: #34495e;
  position: relative;
}

/* 加载和错误容器 */
.loading-container,
.error-container,
.empty-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: white;
  padding: 40px;
}

/* PDF显示区域 - 100%填充 */
.pdf-display {
  width: 100%;
  height: 100%;
  display: flex;
  background-color: #34495e;
}

.pdf-iframe {
  width: 100%;
  height: 100%;
  border: none;
  background-color: white;
}

/* PDF底部 */
.pdf-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background-color: #2c3e50;
  border-top: 1px solid #34495e;
  flex-shrink: 0;
}

.footer-hint {
  color: #bdc3c7;
  font-size: 14px;
  display: flex;
  align-items: center;
}

.footer-actions {
  display: flex;
  gap: 10px;
}

.footer-actions .btn {
  padding: 8px 20px;
  font-size: 14px;
  font-weight: 500;
}

/* 签名覆盖层 */
.signature-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.75);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10000;
}

.signature-modal-content {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.signature-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.signature-header h5 {
  margin: 0;
  font-size: 20px;
  font-weight: 500;
  display: flex;
  align-items: center;
}

.signature-body {
  padding: 20px;
  flex: 1;
  overflow-y: auto;
}

.signature-footer {
  padding: 20px;
  border-top: 1px solid #e0e0e0;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .pdf-header,
  .pdf-footer {
    padding: 10px;
  }

  .header-left {
    font-size: 14px;
  }

  .footer-hint {
    font-size: 12px;
  }

  .footer-actions .btn {
    padding: 6px 12px;
    font-size: 12px;
  }

  .signature-modal-content {
    width: 95%;
  }
}
</style>


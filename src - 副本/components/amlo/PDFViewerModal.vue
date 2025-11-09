<template>
  <div class="modal fade" :id="modalId" tabindex="-1" ref="modalRef">
    <div class="modal-dialog modal-fullscreen">
      <div class="modal-content">
        <div class="modal-header bg-primary text-white">
          <h5 class="modal-title d-flex align-items-center">
            <i class="fas fa-file-pdf me-2"></i>
            {{ title || t('amlo.pdfViewer.title') }}
            <span v-if="reportType" class="badge bg-light text-dark ms-2">{{ reportType }}</span>
          </h5>
          <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body p-0">
          <!-- 加载状态 -->
          <div v-if="loading" class="loading-container">
            <div class="spinner-border text-primary" role="status">
              <span class="visually-hidden">{{ t('common.loading') }}</span>
            </div>
            <p class="mt-3 text-muted">{{ t('amlo.pdfViewer.loadingPDF') }}</p>
          </div>

          <!-- 错误状态 -->
          <div v-else-if="error" class="error-container">
            <div class="alert alert-danger m-4">
              <i class="fas fa-exclamation-triangle me-2"></i>
              {{ error }}
            </div>
            <button class="btn btn-primary" @click="retry">
              <i class="fas fa-redo me-2"></i>{{ t('common.retry') }}
            </button>
          </div>

          <!-- PDF显示区域 -->
          <div v-else-if="pdfUrl" class="pdf-container">
            <iframe
              :src="pdfUrl"
              class="pdf-iframe"
              :title="title || t('amlo.pdfViewer.pdfDocument')"
            ></iframe>

            <!-- 签名覆盖层 -->
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
                  <button type="button" class="btn btn-secondary" @click="closeSignaturePad">
                    <i class="fas fa-times me-2"></i>{{ t('common.cancel') }}
                  </button>
                  <button type="button" class="btn btn-primary" @click="saveSignature">
                    <i class="fas fa-check me-2"></i>{{ t('common.confirm') }}
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- 空状态 -->
          <div v-else class="empty-container">
            <i class="fas fa-file-pdf fa-4x text-muted mb-3"></i>
            <p class="text-muted">{{ t('amlo.pdfViewer.noPDFLoaded') }}</p>
          </div>
        </div>
        <div class="modal-footer bg-light d-flex justify-content-between">
          <div>
            <button
              v-if="pdfUrl && allowSignature"
              type="button"
              class="btn btn-warning"
              @click="openSignaturePad"
              :disabled="signatureSaved"
            >
              <i class="fas fa-signature me-2"></i>
              {{ signatureSaved ? (t('amlo.signature.signed') || '已签名') : (t('amlo.signature.sign') || '签名') }}
            </button>
            <button
              v-if="pdfUrl"
              type="button"
              class="btn btn-success ms-2"
              @click="downloadPDF"
              :disabled="downloading"
            >
              <span v-if="downloading" class="spinner-border spinner-border-sm me-2"></span>
              <i v-else class="fas fa-download me-2"></i>
              {{ downloading ? t('common.downloading') : t('common.download') }}
            </button>
            <button
              v-if="pdfUrl && allowPrint"
              type="button"
              class="btn btn-outline-primary ms-2"
              @click="printPDF"
            >
              <i class="fas fa-print me-2"></i>{{ t('common.print') }}
            </button>
          </div>
          <div>
            <button
              v-if="pdfUrl && allowSignature && signatureSaved"
              type="button"
              class="btn btn-primary me-2"
              @click="submitSignature"
              :disabled="submitting"
            >
              <span v-if="submitting" class="spinner-border spinner-border-sm me-2"></span>
              <i v-else class="fas fa-paper-plane me-2"></i>
              {{ submitting ? (t('common.submitting') || '提交中') : (t('common.submit') || '提交') }}
            </button>
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
              <i class="fas fa-times me-2"></i>{{ t('common.close') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Modal } from 'bootstrap'
import SignaturePad from './SignaturePad.vue'

export default {
  name: 'PDFViewerModal',
  components: {
    SignaturePad
  },
  props: {
    modalId: {
      type: String,
      default: 'pdfViewerModal'
    },
    title: {
      type: String,
      default: ''
    },
    reportType: {
      type: String,
      default: ''
    },
    pdfSource: {
      type: [String, Blob],
      default: null
    },
    allowPrint: {
      type: Boolean,
      default: true
    },
    allowDownload: {
      type: Boolean,
      default: true
    },
    allowSignature: {
      type: Boolean,
      default: true
    },
    reservationId: {
      type: [Number, String],
      default: null
    }
  },
  emits: ['opened', 'closed', 'download', 'print', 'signature-submitted'],
  setup(props, { emit }) {
    const { t } = useI18n()
    const modalRef = ref(null)
    const signaturePadRef = ref(null)
    const loading = ref(false)
    const error = ref(null)
    const pdfUrl = ref(null)
    const downloading = ref(false)
    const showSignaturePad = ref(false)
    const signatureSaved = ref(false)
    const signatureData = ref(null)
    const submitting = ref(false)
    let modal = null

    // 监听pdfSource变化，生成Blob URL
    watch(() => props.pdfSource, async (newSource) => {
      error.value = null
      pdfUrl.value = null

      if (!newSource) return

      try {
        loading.value = true

        if (typeof newSource === 'string') {
          // 如果是URL字符串，直接使用
          pdfUrl.value = newSource
        } else if (newSource instanceof Blob) {
          // 如果是Blob对象，创建Blob URL
          pdfUrl.value = URL.createObjectURL(newSource)
        } else {
          throw new Error('Invalid PDF source type')
        }
      } catch (err) {
        console.error('[PDFViewerModal] Error loading PDF:', err)
        error.value = t('amlo.pdfViewer.loadError') + ': ' + err.message
      } finally {
        loading.value = false
      }
    }, { immediate: true })

    const open = async () => {
      if (!modal && modalRef.value) {
        modal = new Modal(modalRef.value)
      }
      modal.show()
      emit('opened')

      // 等待Modal完全显示后再检测扩展屏幕并全屏
      setTimeout(async () => {
        await detectAndFullscreen()
      }, 1000)  // 增加延迟到1秒，确保Modal完全渲染
    }

    /**
     * 检测扩展笔屏并在其上全屏显示PDF
     */
    const detectAndFullscreen = async () => {
      try {
        console.log('[PDFViewerModal] Starting screen detection...')

        // 🔧 方法1: 使用Screen Management API (Chrome 93+)
        if ('getScreenDetails' in window) {
          try {
            console.log('[PDFViewerModal] Screen Management API available, requesting permission...')
            const screenDetails = await window.getScreenDetails()
            const screens = screenDetails.screens

            console.log('[PDFViewerModal] Total screens detected:', screens.length)
            screens.forEach((screen, index) => {
              console.log(`[PDFViewerModal] Screen ${index}:`, {
                label: screen.label,
                isPrimary: screen.isPrimary,
                width: screen.width,
                height: screen.height,
                left: screen.left,
                top: screen.top
              })
            })

            // 查找非主屏幕（扩展屏幕2）
            const externalScreen = screens.find(screen => !screen.isPrimary)

            if (externalScreen) {
              console.log('[PDFViewerModal] Found external screen:', externalScreen.label)

              // 等待下一个渲染帧
              await new Promise(resolve => requestAnimationFrame(resolve))

              // 尝试在modal根元素上全屏
              const modalElement = modalRef.value
              if (modalElement) {
                try {
                  await modalElement.requestFullscreen({ screen: externalScreen })
                  console.log('[PDFViewerModal] ✓ Fullscreen activated on external screen!')
                  return // 成功，提前返回
                } catch (fsError) {
                  console.warn('[PDFViewerModal] requestFullscreen failed:', fsError)
                  console.log('[PDFViewerModal] Error details:', {
                    name: fsError.name,
                    message: fsError.message
                  })
                }
              }
            } else {
              console.log('[PDFViewerModal] No external screen found - all screens are primary')
            }
          } catch (apiError) {
            console.warn('[PDFViewerModal] Screen Management API error:', apiError)
          }
        } else {
          console.log('[PDFViewerModal] Screen Management API not supported in this browser')
        }

        // 🔧 方法2: 降级 - 检测多屏幕环境并打开新窗口
        if (window.screen.availWidth > window.screen.width ||
            window.screen.availHeight > window.screen.height) {
          console.log('[PDFViewerModal] Multiple monitors detected via screen metrics')
          console.log('[PDFViewerModal] Consider opening in new window to allow user to drag to second screen')
        }

        // 🔧 方法3: 最终降级 - 当前窗口全屏
        console.log('[PDFViewerModal] Falling back to regular fullscreen on current screen')
        await tryRegularFullscreen()

      } catch (error) {
        console.error('[PDFViewerModal] Fullscreen detection error:', error)
      }
    }

    /**
     * 降级方案：普通全屏模式
     */
    const tryRegularFullscreen = async () => {
      try {
        const modalElement = modalRef.value?.querySelector('.modal-dialog')
        if (modalElement && modalElement.requestFullscreen) {
          await modalElement.requestFullscreen()
          console.log('[PDFViewerModal] Regular fullscreen activated')
        }
      } catch (error) {
        console.log('[PDFViewerModal] Regular fullscreen not available:', error.message)
      }
    }

    const close = () => {
      if (modal) {
        modal.hide()
        emit('closed')
      }
    }

    const retry = () => {
      // 重新触发加载
      const source = props.pdfSource
      pdfUrl.value = null
      error.value = null

      // 延迟后重新加载
      setTimeout(() => {
        if (source instanceof Blob) {
          pdfUrl.value = URL.createObjectURL(source)
        } else if (typeof source === 'string') {
          pdfUrl.value = source
        }
      }, 100)
    }

    const downloadPDF = async () => {
      if (!pdfUrl.value) return

      downloading.value = true
      try {
        const response = await fetch(pdfUrl.value)
        const blob = await response.blob()

        const link = document.createElement('a')
        link.href = URL.createObjectURL(blob)
        link.download = `${props.reportType || 'AMLO'}_${new Date().getTime()}.pdf`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(link.href)

        emit('download')
      } catch (err) {
        console.error('[PDFViewerModal] Download failed:', err)
        alert(t('amlo.pdfViewer.downloadError'))
      } finally {
        downloading.value = false
      }
    }

    const printPDF = () => {
      if (!pdfUrl.value) return

      const printWindow = window.open(pdfUrl.value, '_blank')
      if (printWindow) {
        printWindow.onload = () => {
          printWindow.print()
        }
        emit('print')
      } else {
        alert(t('amlo.pdfViewer.printError'))
      }
    }

    const openSignaturePad = () => {
      showSignaturePad.value = true
    }

    const closeSignaturePad = () => {
      showSignaturePad.value = false
    }

    const saveSignature = () => {
      if (signaturePadRef.value) {
        const data = signaturePadRef.value.toDataURL()
        signatureData.value = data
        signatureSaved.value = true
        showSignaturePad.value = false
      }
    }

    const submitSignature = async () => {
      if (!signatureData.value || !props.reservationId) return

      submitting.value = true
      try {
        const api = (await import('../../services/api')).default
        await api.post(`/amlo/reservations/${props.reservationId}/signature`, {
          signature: signatureData.value,
          reporter_date: new Date().toLocaleDateString('en-GB')
        })

        emit('signature-submitted', { reservationId: props.reservationId })
        alert(t('amlo.signature.submitSuccess') || '签名提交成功')

        // 签名提交成功后，刷新页面以重新加载PDF
        setTimeout(() => {
          window.location.reload()
        }, 1000)
      } catch (error) {
        console.error('[PDFViewerModal] Submit signature error:', error)
        alert(t('amlo.signature.submitFailed') || '签名提交失败')
      } finally {
        submitting.value = false
      }
    }

    return {
      t,
      modalRef,
      signaturePadRef,
      loading,
      error,
      pdfUrl,
      downloading,
      showSignaturePad,
      signatureSaved,
      submitting,
      open,
      close,
      retry,
      downloadPDF,
      printPDF,
      openSignaturePad,
      closeSignaturePad,
      saveSignature,
      submitSignature
    }
  }
}
</script>

<style scoped>
.loading-container,
.error-container,
.empty-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  padding: 2rem;
}

.pdf-container {
  width: 100%;
  height: calc(100vh - 120px);
  overflow: hidden;
}

.pdf-iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.modal-fullscreen .modal-body {
  overflow: auto;
}

.btn-close-white {
  filter: brightness(0) invert(1);
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
</style>

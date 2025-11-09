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
              v-if="pdfUrl"
              type="button"
              class="btn btn-success"
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
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
            <i class="fas fa-times me-2"></i>{{ t('common.close') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Modal } from 'bootstrap'

export default {
  name: 'PDFViewerModal',
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
    }
  },
  emits: ['opened', 'closed', 'download', 'print'],
  setup(props, { emit }) {
    const { t } = useI18n()
    const modalRef = ref(null)
    const loading = ref(false)
    const error = ref(null)
    const pdfUrl = ref(null)
    const downloading = ref(false)
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

    const open = () => {
      if (!modal && modalRef.value) {
        modal = new Modal(modalRef.value)
      }
      modal.show()
      emit('opened')
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

    return {
      t,
      modalRef,
      loading,
      error,
      pdfUrl,
      downloading,
      open,
      close,
      retry,
      downloadPDF,
      printPDF
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
</style>

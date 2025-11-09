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
      <button
        v-if="pdfUrl && allowSignature && signatureSaved"
        type="button"
        class="btn btn-warning btn-lg"
        @click="submitSignature"
        :disabled="submitting"
      >
        <span v-if="submitting" class="spinner-border spinner-border-sm me-2"></span>
        <i v-else class="fas fa-paper-plane me-2"></i>
        {{ submitting ? (t('common.submitting') || '提交中') : (t('common.submit') || '提交') }}
      </button>
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

    const saveSignature = () => {
      if (signaturePadRef.value) {
        const data = signaturePadRef.value.toDataURL()
        signatureData.value = data
        signatureSaved.value = true
        showSignaturePad.value = false
        console.log('[PDFViewerWindow] Signature saved')
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

        alert(t('amlo.signature.submitSuccess') || '签名提交成功')

        // Force PDF regeneration by reloading with new timestamp
        console.log('[PDFViewerWindow] Reloading PDF to show signature...')
        await loadPDF()

        // Notify user
        alert(t('amlo.signature.pdfReloaded') || 'PDF已更新，请查看签名区域')
      } catch (error) {
        console.error('[PDFViewerWindow] Submit signature error:', error)
        alert(t('amlo.signature.submitFailed') || '签名提交失败: ' + (error.response?.data?.message || error.message))
      } finally {
        submitting.value = false
      }
    }

    const closeWindow = () => {
      window.close()
    }

    onMounted(() => {
      loadPDF()
      console.log('[PDFViewerWindow] Window opened at:', new Date().toISOString())
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
      closeWindow
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
</style>

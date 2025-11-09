<template>
  <div class="pdfjs-viewer-container">
    <!-- Loading State -->
    <div v-if="loading" class="loading-overlay">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">{{ t('common.loading') }}</span>
      </div>
      <p class="mt-3 text-muted">{{ t('amlo.pdfViewer.loadingPDF') }}</p>
    </div>

    <!-- Error State -->
    <div v-if="error" class="error-overlay">
      <div class="alert alert-danger">
        <i class="fas fa-exclamation-triangle me-2"></i>
        {{ error }}
      </div>
      <button class="btn btn-primary" @click="loadDocument">
        <i class="fas fa-redo me-2"></i>{{ t('common.retry') }}
      </button>
    </div>

    <!-- PDF Canvas Container -->
    <div v-show="!loading && !error" class="pdf-canvas-container" ref="canvasContainer">
      <!-- Canvases will be dynamically created here -->

      <!-- Form Field Overlays (for editable mode) - Inside canvas container for correct positioning -->
      <div v-show="editable" class="form-field-overlays" ref="overlayContainer">
        <!-- Form field inputs will be positioned absolutely over PDF -->
      </div>
    </div>
  </div>
</template>

<script>
import { ref, shallowRef, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import * as pdfjsLib from 'pdfjs-dist/legacy/build/pdf'

export default {
  name: 'PDFJSViewer',
  props: {
    pdfUrl: {
      type: String,
      required: true
    },
    editable: {
      type: Boolean,
      default: false
    },
    scale: {
      type: Number,
      default: 1.5
    }
  },
  emits: ['loaded', 'error', 'field-change'],
  setup(props, { emit }) {
    const { t } = useI18n()

    // State
    const loading = ref(true)
    const error = ref(null)
    const canvasContainer = ref(null)
    const overlayContainer = ref(null)
    const pdfDocument = shallowRef(null) // Use shallowRef to avoid proxying PDF.js internal properties
    const formFields = ref({}) // Store form field data: { fieldName: { value, type, rect, pageNum } }

    // PDF.js Worker Setup
    const setupWorker = () => {
      // Use CDN for worker (compatible with Node 18)
      pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js`
      console.log('[PDFJSViewer] PDF.js worker configured')
    }

    /**
     * Load PDF document from URL
     */
    const loadDocument = async () => {
      loading.value = true
      error.value = null

      // Destroy previous PDF document if exists
      if (pdfDocument.value) {
        try {
          // shallowRef ensures no Proxy wrapping, safe to call destroy directly
          if (typeof pdfDocument.value.destroy === 'function') {
            pdfDocument.value.destroy()
          }
        } catch (e) {
          console.log('[PDFJSViewer] Previous PDF auto-cleanup')
        }
        pdfDocument.value = null
      }

      try {
        console.log('[PDFJSViewer] Loading PDF from:', props.pdfUrl)

        // Fetch PDF as array buffer
        const response = await fetch(props.pdfUrl)
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }

        const arrayBuffer = await response.arrayBuffer()

        // Load PDF document
        const loadingTask = pdfjsLib.getDocument({
          data: arrayBuffer,
          enableXfa: true, // Enable XFA form support
          disableAutoFetch: false,
          disableStream: false
        })

        pdfDocument.value = await loadingTask.promise
        console.log(`[PDFJSViewer] PDF loaded: ${pdfDocument.value.numPages} pages`)

        // Clear previous content
        if (canvasContainer.value) {
          canvasContainer.value.innerHTML = ''
        }
        if (overlayContainer.value) {
          overlayContainer.value.innerHTML = ''
        }

        // Render all pages
        for (let pageNum = 1; pageNum <= pdfDocument.value.numPages; pageNum++) {
          await renderPage(pageNum)
        }

        // Extract form fields if editable
        if (props.editable) {
          await extractFormFields()
        }

        loading.value = false
        emit('loaded', pdfDocument.value)

        // Render form field inputs AFTER loading is false and DOM is updated
        if (props.editable) {
          await nextTick() // Wait for v-show to update and canvasContainer to become visible
          renderFormFieldInputs()
        }

      } catch (err) {
        console.error('[PDFJSViewer] Failed to load PDF:', err)
        error.value = t('amlo.pdfViewer.loadError') + ': ' + err.message
        loading.value = false
        emit('error', err)
      }
    }

    /**
     * Render a single PDF page to canvas
     */
    const renderPage = async (pageNum) => {
      const page = await pdfDocument.value.getPage(pageNum)

      // Calculate viewport
      const viewport = page.getViewport({ scale: props.scale })

      // Create canvas element
      const canvas = document.createElement('canvas')
      canvas.className = 'pdf-page-canvas'
      canvas.dataset.pageNumber = pageNum

      const context = canvas.getContext('2d')
      canvas.height = viewport.height
      canvas.width = viewport.width

      // Append to container
      if (canvasContainer.value) {
        canvasContainer.value.appendChild(canvas)
      }

      // Render PDF page
      const renderContext = {
        canvasContext: context,
        viewport: viewport
      }

      await page.render(renderContext).promise
      console.log(`[PDFJSViewer] Rendered page ${pageNum}`)
    }

    /**
     * Extract form fields from PDF using annotations
     */
    const extractFormFields = async () => {
      formFields.value = {}

      for (let pageNum = 1; pageNum <= pdfDocument.value.numPages; pageNum++) {
        const page = await pdfDocument.value.getPage(pageNum)
        const annotations = await page.getAnnotations()
        const viewport = page.getViewport({ scale: props.scale })

        annotations.forEach(annot => {
          // Only process form fields (widget annotations)
          if (annot.subtype === 'Widget' && annot.fieldName) {
            const fieldName = annot.fieldName

            // Determine field type
            let fieldType = 'text'
            if (annot.fieldType === 'Tx') {
              fieldType = annot.multiLine ? 'textarea' : 'text'
            } else if (annot.fieldType === 'Btn') {
              fieldType = annot.checkBox ? 'checkbox' : (annot.radioButton ? 'radio' : 'button')
            } else if (annot.fieldType === 'Ch') {
              fieldType = 'select'
            }

            // Get field value
            let fieldValue = annot.fieldValue || annot.buttonValue || ''
            if (fieldType === 'checkbox') {
              fieldValue = annot.fieldValue === 'Yes' || annot.buttonValue === 'Yes'
            }

            // Get field rectangle (convert PDF coordinates to canvas coordinates)
            const rect = annot.rect
            const canvasRect = {
              left: rect[0],
              bottom: rect[1],
              right: rect[2],
              top: rect[3]
            }

            // Convert to viewport coordinates
            const [x1, y1, x2, y2] = viewport.convertToViewportRectangle([
              canvasRect.left,
              canvasRect.bottom,
              canvasRect.right,
              canvasRect.top
            ])

            formFields.value[fieldName] = {
              name: fieldName,
              type: fieldType,
              value: fieldValue,
              rect: {
                x: Math.min(x1, x2),
                y: Math.min(y1, y2),
                width: Math.abs(x2 - x1),
                height: Math.abs(y2 - y1)
              },
              pageNum: pageNum,
              readOnly: annot.readOnly || false,
              options: annot.options || [] // For select/dropdown fields
            }
          }
        })
      }

      console.log(`[PDFJSViewer] Extracted ${Object.keys(formFields.value).length} form fields`)
    }

    /**
     * Render HTML input overlays for form fields
     */
    const renderFormFieldInputs = () => {
      if (!overlayContainer.value) {
        console.warn('[PDFJSViewer] overlayContainer not found, cannot render form inputs')
        return
      }

      // Force overlayContainer styles with inline styles (workaround for CSS not loading)
      overlayContainer.value.style.position = 'absolute'
      overlayContainer.value.style.top = '0'
      overlayContainer.value.style.left = '0'
      overlayContainer.value.style.width = '100%'
      overlayContainer.value.style.height = '100%'
      overlayContainer.value.style.zIndex = '10'
      overlayContainer.value.style.pointerEvents = 'none'

      overlayContainer.value.innerHTML = ''

      // Get all canvas elements
      const canvases = canvasContainer.value?.querySelectorAll('.pdf-page-canvas') || []

      let fieldCount = 0
      Object.values(formFields.value).forEach((field, index) => {
        // Find the canvas for this field's page
        const canvas = Array.from(canvases).find(c => parseInt(c.dataset.pageNumber) === field.pageNum)
        if (!canvas) {
          console.warn(`[PDFJSViewer] Canvas not found for page ${field.pageNum}`)
          return
        }

        // Calculate offset
        const offsetX = canvas.offsetLeft
        const offsetY = canvas.offsetTop

        const input = createInputElement(field, offsetX, offsetY)
        if (input) {
          overlayContainer.value.appendChild(input)
          fieldCount++

          // Debug: Log first 3 fields with their styles
          if (index < 3) {
            console.log(`[PDFJSViewer] Field ${index}:`, {
              name: field.name,
              type: field.type,
              pageNum: field.pageNum,
              canvasOffset: { x: offsetX, y: offsetY },
              fieldRect: field.rect,
              finalPosition: {
                left: input.style.left,
                top: input.style.top,
                width: input.style.width,
                height: input.style.height
              },
              zIndex: window.getComputedStyle(input).zIndex,
              pointerEvents: window.getComputedStyle(input).pointerEvents
            })
          }
        }
      })

      console.log(`[PDFJSViewer] Successfully rendered ${fieldCount} input fields`)

      const overlayStyles = window.getComputedStyle(overlayContainer.value)
      console.log('[PDFJSViewer] overlayContainer computed styles:')
      console.log('  position:', overlayStyles.position)
      console.log('  zIndex:', overlayStyles.zIndex)
      console.log('  pointerEvents:', overlayStyles.pointerEvents)
      console.log('  top:', overlayStyles.top)
      console.log('  left:', overlayStyles.left)
      console.log('  width:', overlayStyles.width)
      console.log('  height:', overlayStyles.height)
      console.log('  display:', overlayStyles.display)

      console.log('[PDFJSViewer] canvasContainer info:')
      console.log('  width:', canvasContainer.value?.offsetWidth)
      console.log('  height:', canvasContainer.value?.offsetHeight)
      console.log('  scrollWidth:', canvasContainer.value?.scrollWidth)
      console.log('  scrollHeight:', canvasContainer.value?.scrollHeight)

      // Debug: Check first canvas dimensions
      if (canvases.length > 0) {
        const firstCanvas = canvases[0]
        console.log('[PDFJSViewer] First canvas info:')
        console.log('  width:', firstCanvas.width)
        console.log('  height:', firstCanvas.height)
        console.log('  offsetLeft:', firstCanvas.offsetLeft)
        console.log('  offsetTop:', firstCanvas.offsetTop)
        console.log('  offsetParent:', firstCanvas.offsetParent?.className)
      }

      // Debug: Check if inputs are in DOM
      const inputsInDOM = overlayContainer.value?.querySelectorAll('.pdf-form-field')
      console.log('[PDFJSViewer] Inputs found in DOM:', inputsInDOM?.length)
      if (inputsInDOM && inputsInDOM.length > 0) {
        const firstInput = inputsInDOM[0]
        console.log('[PDFJSViewer] First input element:')
        console.log('  tagName:', firstInput.tagName)
        console.log('  className:', firstInput.className)
        console.log('  style.left:', firstInput.style.left)
        console.log('  style.top:', firstInput.style.top)
        console.log('  style.width:', firstInput.style.width)
        console.log('  style.height:', firstInput.style.height)
        console.log('  style.border:', firstInput.style.border)
        console.log('  style.backgroundColor:', firstInput.style.backgroundColor)
        console.log('  style.zIndex:', firstInput.style.zIndex)
        console.log('  offsetWidth:', firstInput.offsetWidth)
        console.log('  offsetHeight:', firstInput.offsetHeight)
        const computedInput = window.getComputedStyle(firstInput)
        console.log('  computed display:', computedInput.display)
        console.log('  computed visibility:', computedInput.visibility)
      }

      console.log('[PDFJSViewer] Rendered form field inputs')
    }

    /**
     * Create an HTML input element for a form field
     */
    const createInputElement = (field, offsetX, offsetY) => {
      let element

      if (field.type === 'text' || field.type === 'textarea') {
        element = document.createElement(field.type === 'textarea' ? 'textarea' : 'input')
        if (field.type === 'text') {
          element.type = 'text'
        }
        element.value = field.value || ''
      } else if (field.type === 'checkbox') {
        element = document.createElement('input')
        element.type = 'checkbox'
        element.checked = Boolean(field.value)
      } else if (field.type === 'select') {
        element = document.createElement('select')
        field.options.forEach(option => {
          const opt = document.createElement('option')
          opt.value = option
          opt.textContent = option
          if (option === field.value) {
            opt.selected = true
          }
          element.appendChild(opt)
        })
      } else {
        // Unsupported field type
        return null
      }

      // Style the element to overlay on PDF
      element.className = 'pdf-form-field'
      element.dataset.fieldName = field.name
      element.style.position = 'absolute'
      element.style.display = 'block' // Ensure element is visible
      element.style.left = `${field.rect.x + offsetX}px`
      element.style.top = `${field.rect.y + offsetY}px`
      element.style.width = `${field.rect.width}px`
      element.style.height = `${field.rect.height}px`
      element.style.border = '3px solid red' // Make it VERY visible for debugging
      element.style.backgroundColor = 'rgba(255, 0, 0, 0.3)' // Red semi-transparent background
      element.style.padding = '2px'
      element.style.fontSize = '12px'
      element.style.boxSizing = 'border-box'
      element.style.zIndex = '9999' // Very high z-index
      element.style.cursor = 'pointer' // Show it's interactive
      element.style.pointerEvents = 'auto' // Explicitly enable pointer events

      if (field.readOnly) {
        element.disabled = true
        element.style.backgroundColor = 'rgba(240, 240, 240, 0.9)'
      }

      // Add change event listener
      element.addEventListener('change', (e) => {
        const newValue = field.type === 'checkbox' ? e.target.checked : e.target.value
        formFields.value[field.name].value = newValue
        emit('field-change', { fieldName: field.name, value: newValue, type: field.type })
        console.log(`[PDFJSViewer] Field changed: ${field.name} = ${newValue}`)
      })

      // Add input event for real-time updates
      element.addEventListener('input', (e) => {
        const newValue = field.type === 'checkbox' ? e.target.checked : e.target.value
        formFields.value[field.name].value = newValue
      })

      return element
    }

    /**
     * Get current form field values
     * @returns {Object} Field name → value mapping
     */
    const getFormData = () => {
      const data = {}
      Object.entries(formFields.value).forEach(([fieldName, field]) => {
        data[fieldName] = field.value
      })
      console.log(`[PDFJSViewer] getFormData() returning ${Object.keys(data).length} fields`)
      return data
    }

    /**
     * Set form field values programmatically
     * @param {Object} data - Field name → value mapping
     */
    const setFormData = (data) => {
      Object.entries(data).forEach(([fieldName, value]) => {
        if (formFields.value[fieldName]) {
          formFields.value[fieldName].value = value

          // Update the corresponding input element
          const inputElement = overlayContainer.value?.querySelector(`[data-field-name="${fieldName}"]`)
          if (inputElement) {
            if (formFields.value[fieldName].type === 'checkbox') {
              inputElement.checked = Boolean(value)
            } else {
              inputElement.value = value || ''
            }
          }
        }
      })
      console.log(`[PDFJSViewer] setFormData() updated ${Object.keys(data).length} fields`)
    }

    // Watch for URL changes
    watch(() => props.pdfUrl, (newUrl) => {
      if (newUrl) {
        loadDocument()
      }
    })

    // Setup on mount
    onMounted(() => {
      setupWorker()
      if (props.pdfUrl) {
        loadDocument()
      }
    })

    // Cleanup on unmount
    onUnmounted(() => {
      if (pdfDocument.value) {
        try {
          // Try to destroy PDF document
          // shallowRef ensures no Proxy wrapping, safe to call destroy directly
          if (typeof pdfDocument.value.destroy === 'function') {
            pdfDocument.value.destroy()
          }
        } catch (e) {
          // Ignore any unexpected errors during cleanup
          // Browser will handle garbage collection automatically
          console.log('[PDFJSViewer] PDF document auto-cleanup')
        }
        pdfDocument.value = null
      }
    })

    // Expose methods to parent
    return {
      t,
      loading,
      error,
      canvasContainer,
      overlayContainer,
      loadDocument,
      getFormData,
      setFormData
    }
  }
}
</script>

<style>
.pdfjs-viewer-container {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: auto;
  background-color: #525252;
}

.loading-overlay,
.error-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background-color: #ecf0f1;
}

.pdf-canvas-container {
  position: relative;
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.pdf-page-canvas {
  position: relative;
  z-index: 1;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
  background: white;
}

.form-field-overlays {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 10; /* Ensure overlay is above PDF canvas */
  pointer-events: none; /* Allow clicks to pass through the container */
}

.pdf-form-field {
  pointer-events: auto; /* Enable clicks on individual fields */
  transition: border-color 0.2s;
}

.pdf-form-field:focus {
  outline: none;
  border-color: #0a58ca;
  box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
}

.pdf-form-field:disabled {
  cursor: not-allowed;
}
</style>

<template>
  <div class="pdf-viewer-window">
    <!-- Header with Edit Mode Toggle -->
    <div class="pdf-header">
      <div class="header-left">
        <i class="fas fa-file-pdf me-2"></i>
        <span>{{ title }}</span>
        <span v-if="reportType" class="badge bg-light text-dark ms-2">{{ reportType }}</span>
        <span v-if="isEditMode" class="badge bg-warning text-dark ms-2">
          <i class="fas fa-edit me-1"></i>{{ t('amlo.pdfViewer.editMode') || '编辑模式' }}
        </span>
      </div>
      <div class="header-right" v-if="pdfUrl && !readonly">
        <button
          class="btn btn-sm btn-outline-light me-2"
          @click="toggleEditMode"
          :title="isEditMode ? '切换到预览模式' : '切换到编辑模式'"
        >
          <i :class="isEditMode ? 'fas fa-eye' : 'fas fa-edit'" class="me-1"></i>
          {{ isEditMode ? (t('amlo.pdfViewer.previewMode') || '预览模式') : (t('amlo.pdfViewer.editMode') || '编辑模式') }}
        </button>
      </div>
    </div>

    <!-- Main Content Area -->
    <div class="pdf-content" :class="{ 'with-edit-panel': isEditMode }">
      <!-- PDF Preview -->
      <div class="pdf-preview" :class="{ 'edit-mode': isEditMode }">
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

        <!-- PDF Display -->
        <div v-else-if="pdfUrl" class="pdf-display">
          <!-- PDF.js Viewer for direct editing -->
          <PDFJSViewer
            ref="pdfViewerRef"
            :pdf-url="pdfUrl"
            :editable="!readonly"
            :scale="1.5"
            @loaded="onPdfLoaded"
            @field-change="onPdfFieldChange"
            @error="onPdfError"
          />
        </div>

        <!-- Empty State -->
        <div v-else class="empty-container">
          <i class="fas fa-file-pdf fa-4x text-muted mb-3"></i>
          <p class="text-muted">{{ t('amlo.pdfViewer.noPDFLoaded') }}</p>
        </div>
      </div>

      <!-- Edit Panel (shown when isEditMode is true) -->
      <div v-if="isEditMode" class="edit-panel">
        <div class="panel-header">
          <h5>
            <i class="fas fa-edit me-2"></i>
            {{ t('amlo.pdfViewer.editReportContent') || '编辑报告内容' }}
          </h5>
          <button
            v-if="hasModifications"
            class="btn btn-sm btn-link text-warning"
            @click="resetChanges"
            :title="t('amlo.pdfViewer.resetAllChanges') || '重置所有修改'"
          >
            <i class="fas fa-undo me-1"></i>
            {{ t('amlo.pdfViewer.reset') || '重置' }}
          </button>
        </div>

        <div class="panel-body">
          <!-- Modification Warning -->
          <div v-if="hasModifications" class="alert alert-warning">
            <i class="fas fa-exclamation-triangle me-2"></i>
            {{ t('amlo.pdfViewer.modificationWarning', { count: modifiedFieldsCount }) || `您已修改 ${modifiedFieldsCount} 个字段` }}
          </div>

          <!-- Loading Fields -->
          <div v-if="loadingFields" class="text-center py-4">
            <div class="spinner-border spinner-border-sm text-primary" role="status"></div>
            <p class="text-muted mt-2">{{ t('amlo.pdfViewer.loadingFields') || '加载字段配置...' }}</p>
          </div>

          <!-- Form Fields -->
          <div v-else class="form-fields">
            <!-- Report Number (Read-only) -->
            <div class="form-group">
              <label class="form-label">
                {{ t('amlo.form.reportNo') || '报告编号' }}
                <span class="badge bg-secondary ms-2">{{ t('common.readonly') || '只读' }}</span>
              </label>
              <input
                type="text"
                class="form-control"
                :value="formData.report_no"
                readonly
                disabled
              />
            </div>

            <!-- Customer Name (Editable) -->
            <div class="form-group">
              <label class="form-label">
                {{ t('amlo.form.customerName') || '客户姓名' }}
                <span v-if="isFieldModified('customer_name')" class="badge bg-warning text-dark ms-2">
                  {{ t('common.modified') || '已修改' }}
                </span>
              </label>
              <input
                type="text"
                class="form-control"
                v-model="formData.customer_name"
                @input="onPanelFieldChange('customer_name', formData.customer_name)"
                :class="{ 'is-modified': isFieldModified('customer_name') }"
              />
              <small v-if="isFieldModified('customer_name')" class="text-muted">
                {{ t('amlo.pdfViewer.originalValue') || '原值' }}: {{ originalData.customer_name }}
              </small>
            </div>

            <!-- Customer ID (Editable) -->
            <div class="form-group">
              <label class="form-label">
                {{ t('amlo.form.customerId') || '客户证件号' }}
                <span v-if="isFieldModified('customer_id')" class="badge bg-warning text-dark ms-2">
                  {{ t('common.modified') || '已修改' }}
                </span>
              </label>
              <input
                type="text"
                class="form-control"
                v-model="formData.customer_id"
                @input="markFieldAsModified('customer_id')"
                :class="{ 'is-modified': isFieldModified('customer_id') }"
              />
              <small v-if="isFieldModified('customer_id')" class="text-muted">
                {{ t('amlo.pdfViewer.originalValue') || '原值' }}: {{ originalData.customer_id }}
              </small>
            </div>

            <!-- Local Amount (Editable) -->
            <div class="form-group">
              <label class="form-label">
                {{ t('amlo.form.localAmount') || '交易金额（本币）' }}
                <span v-if="isFieldModified('local_amount')" class="badge bg-warning text-dark ms-2">
                  {{ t('common.modified') || '已修改' }}
                </span>
              </label>
              <input
                type="number"
                step="0.01"
                class="form-control"
                v-model.number="formData.local_amount"
                @input="markFieldAsModified('local_amount')"
                :class="{ 'is-modified': isFieldModified('local_amount') }"
              />
              <small v-if="isFieldModified('local_amount')" class="text-muted">
                {{ t('amlo.pdfViewer.originalValue') || '原值' }}: {{ formatAmount(originalData.local_amount) }}
              </small>
            </div>

            <!-- Foreign Amount (Editable) -->
            <div class="form-group">
              <label class="form-label">
                {{ t('amlo.form.amount') || '外币金额' }}
                <span v-if="isFieldModified('amount')" class="badge bg-warning text-dark ms-2">
                  {{ t('common.modified') || '已修改' }}
                </span>
              </label>
              <input
                type="number"
                step="0.01"
                class="form-control"
                v-model.number="formData.amount"
                @input="markFieldAsModified('amount')"
                :class="{ 'is-modified': isFieldModified('amount') }"
              />
              <small v-if="isFieldModified('amount')" class="text-muted">
                {{ t('amlo.pdfViewer.originalValue') || '原值' }}: {{ formatAmount(originalData.amount) }}
              </small>
            </div>

            <!-- Dynamic Fields from form_data -->
            <div
              v-for="field in editableFields"
              :key="field.name"
              :class="field.type === 'group_header' ? 'field-group-header' : 'form-group'"
            >
              <!-- Group Header -->
              <h6 v-if="field.type === 'group_header'" class="group-title">
                <i class="fas fa-folder-open me-2"></i>{{ field.label }}
              </h6>

              <!-- Editable Fields -->
              <template v-else>
                <label class="form-label">
                  {{ field.label }}
                  <span v-if="isFieldModified(field.name)" class="badge bg-warning text-dark ms-2">
                    {{ t('common.modified') || '已修改' }}
                  </span>
                </label>

                <!-- Text Input -->
                <input
                  v-if="field.type === 'text'"
                  type="text"
                  class="form-control"
                  v-model="formData.form_data[field.name]"
                  @input="onPanelFieldChange(field.name, formData.form_data[field.name])"
                  :class="{ 'is-modified': isFieldModified(field.name) }"
                />

                <!-- Date Input -->
                <input
                  v-else-if="field.type === 'date'"
                  type="date"
                  class="form-control"
                  v-model="formData.form_data[field.name]"
                  @input="onPanelFieldChange(field.name, formData.form_data[field.name])"
                  :class="{ 'is-modified': isFieldModified(field.name) }"
                />

                <!-- Checkbox Input -->
                <div v-else-if="field.type === 'checkbox'" class="form-check">
                  <input
                    type="checkbox"
                    class="form-check-input"
                    v-model="formData.form_data[field.name]"
                    @change="onPanelFieldChange(field.name, formData.form_data[field.name])"
                    :class="{ 'is-modified': isFieldModified(field.name) }"
                  />
                  <label class="form-check-label">
                    {{ formData.form_data[field.name] ? t('amlo.fields.checked') : t('amlo.fields.unchecked') }}
                  </label>
                </div>

                <!-- Textarea -->
                <textarea
                  v-else-if="field.type === 'textarea'"
                  class="form-control"
                  rows="3"
                  v-model="formData.form_data[field.name]"
                  @input="onPanelFieldChange(field.name, formData.form_data[field.name])"
                  :class="{ 'is-modified': isFieldModified(field.name) }"
                ></textarea>

                <small v-if="isFieldModified(field.name)" class="text-muted">
                  {{ t('amlo.pdfViewer.originalValue') || '原值' }}: {{ getOriginalValue(field.name) }}
                </small>
              </template>
            </div>
          </div>
        </div>

        <!-- Modification Summary (Expandable) -->
        <div class="panel-footer" v-if="hasModifications">
          <button
            class="btn btn-sm btn-link w-100"
            @click="toggleModificationSummary"
          >
            <i :class="showSummary ? 'fas fa-chevron-up' : 'fas fa-chevron-down'" class="me-2"></i>
            {{ showSummary ? (t('amlo.pdfViewer.hideSummary') || '收起修改摘要') : (t('amlo.pdfViewer.viewSummary') || '查看修改摘要') }}
          </button>

          <div v-if="showSummary" class="modification-summary">
            <h6>{{ t('amlo.pdfViewer.modificationSummary') || '修改摘要' }}</h6>
            <table class="table table-sm">
              <thead>
                <tr>
                  <th>{{ t('amlo.pdfViewer.field') || '字段' }}</th>
                  <th>{{ t('amlo.pdfViewer.originalValue') || '原值' }}</th>
                  <th>{{ t('amlo.pdfViewer.newValue') || '新值' }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="field in Array.from(modifiedFields)" :key="field">
                  <td>{{ getFieldLabel(field) }}</td>
                  <td class="text-muted">{{ getOriginalValue(field) }}</td>
                  <td class="text-primary fw-bold">{{ getCurrentValue(field) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
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

    <!-- Action Buttons Footer -->
    <div class="pdf-footer">
      <!-- Extended Screen Hint -->
      <div v-if="showSecondScreenHint" class="extended-screen-hint">
        <i class="fas fa-tv me-2"></i>
        <span>按 <kbd>Win</kbd>+<kbd>Shift</kbd>+<kbd>→</kbd> 移动到副屏</span>
        <button type="button" class="btn-close-hint" @click="closeHint">
          <i class="fas fa-times"></i>
        </button>
      </div>

      <!-- Fullscreen Button -->
      <button
        type="button"
        class="btn btn-success btn-lg fullscreen-btn"
        @click="toggleFullscreen"
        :title="'全屏显示 (F11)'"
      >
        <i class="fas fa-expand me-2"></i>全屏 <kbd class="ms-2">F11</kbd>
      </button>

      <!-- Signature Button (only when edit mode is off and not readonly) -->
      <button
        v-if="pdfUrl && allowSignature && !isEditMode"
        type="button"
        class="btn btn-warning btn-lg"
        @click="openSignaturePad"
        :disabled="signatureSaved"
      >
        <i class="fas fa-signature me-2"></i>
        {{ signatureSaved ? (t('amlo.signature.signed') || '已签名') : (t('amlo.signature.sign') || '签名') }}
      </button>

      <!-- Submit Modifications Button (only in edit mode with changes) -->
      <button
        v-if="isEditMode && hasModifications"
        type="button"
        class="btn btn-primary btn-lg"
        @click="submitModifications"
        :disabled="submittingModifications"
      >
        <i class="fas fa-save me-2"></i>
        <span v-if="submittingModifications">
          <span class="spinner-border spinner-border-sm me-2"></span>
          {{ t('amlo.pdfViewer.submitting') || '提交中...' }}
        </span>
        <span v-else>
          {{ t('amlo.pdfViewer.submitModifications') || '提交修改' }}
        </span>
      </button>

      <!-- Close Button -->
      <button type="button" class="btn btn-warning btn-lg" @click="closeWindow">
        <i class="fas fa-times me-2"></i>{{ t('common.close') }}
      </button>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import api from '@/services/api'
import amloService from '@/services/api/amloService'
import SignaturePad from '@/components/amlo/SignaturePad.vue'
import PDFJSViewer from '@/components/amlo/PDFJSViewer.vue'
import { pdfFieldToDbField, dbFieldToPdfField, pdfDataToDbData, dbDataToPdfData } from '@/utils/amloFieldMapping'

export default {
  name: 'PDFViewerWindow',
  components: {
    SignaturePad,
    PDFJSViewer
  },
  setup() {
    const { t } = useI18n()
    const route = useRoute()

    // Basic state
    const loading = ref(false)
    const error = ref(null)
    const pdfUrl = ref(null)
    const downloading = ref(false)
    const showSignaturePad = ref(false)
    const signatureSaved = ref(false)
    const signatureData = ref(null)
    const submitting = ref(false)
    const signaturePadRef = ref(null)
    const showSecondScreenHint = ref(false)
    const positionCheckTimer = ref(null)
    const pdfViewerRef = ref(null) // PDF.js viewer component reference
    const pdfSyncEnabled = ref(true) // Enable/disable two-way sync

    const title = ref('')
    const reportType = ref('')
    const reservationId = ref(null)
    const allowPrint = ref(true)
    const allowSignature = ref(true)
    const readonly = ref(false)

    // Edit mode state
    const isEditMode = ref(false)
    const loadingFields = ref(false)
    const editableFields = ref([])
    const originalData = ref({})
    const formData = ref({
      report_no: '',
      customer_name: '',
      customer_id: '',
      local_amount: 0,
      amount: 0,
      form_data: {}
    })
    const modifiedFields = ref(new Set())
    const showSummary = ref(false)
    const submittingModifications = ref(false)

    // Computed properties
    const hasModifications = computed(() => modifiedFields.value.size > 0)
    const modifiedFieldsCount = computed(() => modifiedFields.value.size)

    // Toggle edit mode
    const toggleEditMode = async () => {
      const wasInEditMode = isEditMode.value

      if (!isEditMode.value) {
        // Entering edit mode - load reservation data and editable PDF
        await loadReservationData()

        // 🆕 Reload PDF as editable when entering edit mode
        isEditMode.value = true
        await loadPDF(true) // Force load editable PDF
      } else {
        // Exiting edit mode - reload final PDF
        isEditMode.value = false
        await loadPDF(false) // Load final flattened PDF
      }

      console.log(`[PDFViewerWindow] Toggled edit mode: ${wasInEditMode ? 'ON' : 'OFF'} → ${isEditMode.value ? 'ON' : 'OFF'}`)
    }

    // Load reservation data for editing
    const loadReservationData = async () => {
      if (!reservationId.value) return

      loadingFields.value = true
      try {
        console.log('[PDFViewerWindow] Loading reservation data for editing:', reservationId.value)

        // Load reservation detail
        const response = await amloService.getReservationDetail(reservationId.value)

        if (response.data.success) {
          const data = response.data.data

          // Set original data (immutable)
          originalData.value = {
            report_no: data.report_no,
            customer_name: data.customer_name,
            customer_id: data.customer_id,
            local_amount: data.local_amount,
            amount: data.amount,
            form_data: data.form_data || {}
          }

          // Copy to current form data
          formData.value = JSON.parse(JSON.stringify(originalData.value))

          // Load editable fields configuration
          if (data.report_type) {
            await loadEditableFields(data.report_type)
          }

          console.log('[PDFViewerWindow] Reservation data loaded successfully')
        }
      } catch (err) {
        console.error('[PDFViewerWindow] Failed to load reservation data:', err)
        alert(t('amlo.pdfViewer.loadDataError') || '加载数据失败')
      } finally {
        loadingFields.value = false
      }
    }

    // Load editable fields configuration
    const loadEditableFields = async (reportType) => {
      try {
        console.log('[PDFViewerWindow] Loading editable fields for:', reportType)

        // Generate editable fields from ALL keys in form_data
        const allFields = []
        const formDataObj = formData.value.form_data || {}

        // Group fields by category for better organization
        const fieldGroups = {
          basic: { title: t('common.basicInfo') || '基本信息', fields: [] },
          reporter: { title: t('amlo.report.reporter') + t('common.infoSuffix') || '报告人信息', fields: [] },
          branch: { title: t('common.branchInfo') || '机构信息', fields: [] },
          customer: { title: t('amlo.reservation.customerInfo') || '客户信息', fields: [] },
          transactor: { title: t('exchange.transactor') + t('common.infoSuffix') || '交易方信息', fields: [] },
          transaction: { title: t('common.transactionInfo') || '交易信息', fields: [] },
          checkbox: { title: t('common.checkboxes') || '勾选项', fields: [] },
          comb: { title: t('common.combFields') || '框格字段', fields: [] },
          other: { title: t('common.otherFields') || '其他字段', fields: [] }
        }

        // Categorize each field
        Object.keys(formDataObj).forEach(fieldName => {
          const fieldValue = formDataObj[fieldName]
          // Try to get field label from i18n, fallback to field name
          const label = t(`amlo.fields.${fieldName}`) !== `amlo.fields.${fieldName}`
            ? t(`amlo.fields.${fieldName}`)
            : fieldName

          // Determine field type based on name and value
          let fieldType = 'text'
          let groupKey = 'other'

          if (fieldName.startsWith('check_')) {
            fieldType = 'checkbox'
            groupKey = 'checkbox'
          } else if (fieldName.startsWith('comb_')) {
            fieldType = 'text'
            groupKey = 'comb'
          } else if (fieldName.includes('date') || fieldName.includes('Date')) {
            fieldType = 'date'
            if (fieldName.startsWith('transactor_')) groupKey = 'transactor'
            else if (fieldName.startsWith('fill_6') || fieldName.startsWith('fill_7') || fieldName.startsWith('fill_8')) groupKey = 'reporter'
            else groupKey = 'transaction'
          } else if (fieldName.startsWith('fill_1') || fieldName.startsWith('fill_2') || fieldName.startsWith('fill_3') || fieldName.startsWith('fill_4') || fieldName.startsWith('fill_5')) {
            groupKey = 'reporter'
          } else if (fieldName.startsWith('fill_9') || fieldName.startsWith('fill_10') || fieldName.startsWith('fill_11')) {
            groupKey = 'branch'
          } else if (fieldName.startsWith('fill_20') || fieldName.startsWith('fill_21') || fieldName.startsWith('fill_22') || fieldName.startsWith('fill_23') || fieldName.startsWith('fill_24') || fieldName.startsWith('fill_25')) {
            groupKey = 'customer'
          } else if (fieldName.startsWith('transactor_')) {
            groupKey = 'transactor'
          } else if (fieldName.startsWith('fill_30') || fieldName.startsWith('fill_31') || fieldName.startsWith('fill_32') || fieldName.startsWith('fill_33') || fieldName.startsWith('fill_34') || fieldName.startsWith('fill_35') || fieldName === 'amount' || fieldName === 'local_amount' || fieldName === 'exchange_rate' || fieldName === 'currency_code' || fieldName === 'purpose') {
            groupKey = 'transaction'
          } else if (fieldName === 'report_no' || fieldName === 'fill_52') {
            groupKey = 'basic'
          }

          // Check if value is long text (should use textarea)
          if (typeof fieldValue === 'string' && fieldValue.length > 100) {
            fieldType = 'textarea'
          }

          fieldGroups[groupKey].fields.push({
            name: fieldName,
            label: label,
            type: fieldType,
            is_editable: true,
            group: groupKey
          })
        })

        // Flatten all fields from groups (preserving group order)
        const groupOrder = ['basic', 'reporter', 'branch', 'customer', 'transactor', 'transaction', 'checkbox', 'comb', 'other']
        groupOrder.forEach(groupKey => {
          if (fieldGroups[groupKey].fields.length > 0) {
            // Add group header marker
            allFields.push({
              name: `__group_${groupKey}__`,
              label: fieldGroups[groupKey].title,
              type: 'group_header',
              is_editable: false,
              group: groupKey
            })
            allFields.push(...fieldGroups[groupKey].fields)
          }
        })

        editableFields.value = allFields
        console.log('[PDFViewerWindow] Generated', editableFields.value.length, 'editable fields from form_data keys')
        console.log('[PDFViewerWindow] Field groups:', Object.keys(fieldGroups).map(k => `${k}: ${fieldGroups[k].fields.length}`).join(', '))
      } catch (err) {
        console.error('[PDFViewerWindow] Failed to load editable fields:', err)
      }
    }

    // Mark field as modified
    const markFieldAsModified = (fieldName) => {
      const currentValue = getFieldValue(formData.value, fieldName)
      const originalValue = getFieldValue(originalData.value, fieldName)

      if (currentValue !== originalValue) {
        modifiedFields.value.add(fieldName)
      } else {
        modifiedFields.value.delete(fieldName)
      }
    }

    // Check if field is modified
    const isFieldModified = (fieldName) => {
      return modifiedFields.value.has(fieldName)
    }

    // Reset all changes
    const resetChanges = () => {
      if (confirm(t('amlo.pdfViewer.confirmReset') || '确定要重置所有修改吗？')) {
        formData.value = JSON.parse(JSON.stringify(originalData.value))
        modifiedFields.value.clear()
      }
    }

    // Toggle modification summary
    const toggleModificationSummary = () => {
      showSummary.value = !showSummary.value
    }

    // Get modification summary
    const getModificationsSummary = () => {
      const summary = []
      for (const field of modifiedFields.value) {
        summary.push({
          field_name: field,
          field_label: getFieldLabel(field),
          old_value: getOriginalValue(field),
          new_value: getCurrentValue(field)
        })
      }
      return summary
    }

    // Submit modifications
    const submitModifications = async () => {
      // Confirmation
      if (hasModifications.value) {
        const confirmed = confirm(
          t('amlo.pdfViewer.confirmSubmit', { count: modifiedFieldsCount.value }) ||
          `您已修改了 ${modifiedFieldsCount.value} 个字段。\n提交后将保存所有修改并生成最终PDF。\n确定要继续吗？`
        )
        if (!confirmed) return
      }

      submittingModifications.value = true

      try {
        console.log('[PDFViewerWindow] Submitting modifications...')

        // 🆕 Extract PDF field values first (in case user edited PDF directly)
        console.log('[PDFViewerWindow] Extracting PDF field values...')
        const pdfExtractedData = extractPdfFormData()

        if (pdfExtractedData && Object.keys(pdfExtractedData).length > 0) {
          console.log(`[PDFViewerWindow] Extracted ${Object.keys(pdfExtractedData).length} fields from PDF`)

          // Merge PDF data into formData
          if (!formData.value.form_data) {
            formData.value.form_data = {}
          }

          Object.keys(pdfExtractedData).forEach(fieldName => {
            const structuredFields = ['customer_name', 'customer_id', 'local_amount', 'amount', 'report_no']
            if (structuredFields.includes(fieldName)) {
              formData.value[fieldName] = pdfExtractedData[fieldName]
            } else {
              formData.value.form_data[fieldName] = pdfExtractedData[fieldName]
            }
          })

          console.log('[PDFViewerWindow] ✅ PDF data merged into formData')
        }

        // Prepare final form data by merging structured fields and form_data
        const dbFormData = {
          ...formData.value.form_data,
          report_no: formData.value.report_no,
          customer_name: formData.value.customer_name,
          customer_id: formData.value.customer_id,
          amount: formData.value.amount,
          local_amount: formData.value.local_amount
        }

        console.log(`[submitModifications] 数据库字段数据准备完成: ${Object.keys(dbFormData).length} 个字段`)

        // 🔄 转换：数据库字段名 → PDF字段名
        console.log('[submitModifications] 🔄 转换数据库字段名到PDF字段名...')
        const pdfFormData = dbDataToPdfData(dbFormData)
        console.log(`[submitModifications] ✅ 转换完成: ${Object.keys(dbFormData).length} DB字段 → ${Object.keys(pdfFormData).length} PDF字段`)
        console.log('[submitModifications] PDF字段示例:', Object.keys(pdfFormData).slice(0, 10))

        // Call flatten-pdf endpoint to save final PDF
        console.log('[submitModifications] 📤 调用 flatten-pdf API...')
        await api.post(`/amlo/reservations/${reservationId.value}/flatten-pdf`, {
          form_data: pdfFormData,  // ✅ 使用PDF字段名
          signature_data: {
            reporter_signature: signatureData.value
          }
        }, {
          responseType: 'blob' // Expecting PDF file
        })

        console.log('[PDFViewerWindow] Flatten PDF response received')

        // Success - PDF has been flattened and saved
        alert(t('amlo.pdfViewer.submitSuccess') || '提交成功！PDF已保存。')

        // Clear modification tracking
        modifiedFields.value.clear()
        originalData.value = JSON.parse(JSON.stringify(formData.value))

        // Exit edit mode and reload final PDF
        isEditMode.value = false
        await loadPDF(false) // Load flattened PDF

        console.log('[PDFViewerWindow] ✅ Modifications submitted successfully')
      } catch (error) {
        console.error('[PDFViewerWindow] Submit modifications error:', error)
        alert(t('amlo.pdfViewer.submitFailed') || '提交失败：' + (error.response?.data?.message || error.message))
      } finally {
        submittingModifications.value = false
      }
    }

    // Helper: Get field value
    const getFieldValue = (data, fieldName) => {
      if (fieldName in data) {
        return data[fieldName]
      } else if (data.form_data && fieldName in data.form_data) {
        return data.form_data[fieldName]
      }
      return null
    }

    // Helper: Get field label
    const getFieldLabel = (fieldName) => {
      // Check structured fields
      const structuredLabels = {
        'customer_name': t('amlo.form.customerName') || '客户姓名',
        'customer_id': t('amlo.form.customerId') || '客户证件号',
        'local_amount': t('amlo.form.localAmount') || '本币金额',
        'amount': t('amlo.form.amount') || '外币金额'
      }

      if (structuredLabels[fieldName]) {
        return structuredLabels[fieldName]
      }

      // Check dynamic fields
      const field = editableFields.value.find(f => f.name === fieldName)
      return field ? field.label : fieldName
    }

    // Helper: Get original value
    const getOriginalValue = (fieldName) => {
      return getFieldValue(originalData.value, fieldName)
    }

    // Helper: Get current value
    const getCurrentValue = (fieldName) => {
      return getFieldValue(formData.value, fieldName)
    }

    // Helper: Format amount
    const formatAmount = (value) => {
      if (value === null || value === undefined) return 'N/A'
      return parseFloat(value).toFixed(2)
    }

    // Load PDF (existing functionality)
    const loadPDF = async (forceEditable = false) => {
      reservationId.value = route.query.id
      title.value = route.query.title || 'AMLO Report'
      reportType.value = route.query.reportType || ''
      readonly.value = route.query.readonly === 'true'

      if (readonly.value) {
        allowSignature.value = false
        console.log('[PDFViewerWindow] 只读模式已启用')
      }

      if (!reservationId.value) {
        error.value = 'Invalid reservation ID'
        return
      }

      loading.value = true
      error.value = null

      try {
        console.log('[PDFViewerWindow] Loading PDF for reservation:', reservationId.value)

        const timestamp = new Date().getTime()

        // 🆕 Choose endpoint based on edit mode or forceEditable flag
        // In edit mode, load editable PDF with AcroForm fields
        // In preview mode, load final flattened PDF
        const shouldLoadEditable = isEditMode.value || forceEditable
        const endpoint = shouldLoadEditable
          ? `/amlo/reservations/${reservationId.value}/editable-pdf?refresh=${timestamp}`
          : `/amlo/reservations/${reservationId.value}/generate-pdf?refresh=${timestamp}`

        console.log(`[PDFViewerWindow] Loading ${shouldLoadEditable ? 'EDITABLE' : 'FINAL'} PDF from:`, endpoint)

        const response = await api.get(endpoint, { responseType: 'blob' })

        console.log('[PDFViewerWindow] PDF loaded successfully, size:', response.data.size)

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

    // PDF.js Event Handlers

    /**
     * Called when PDF.js successfully loads the PDF
     */
    const onPdfLoaded = (pdfDoc) => {
      console.log(`[PDFViewerWindow] ✅ PDF.js loaded PDF: ${pdfDoc.numPages} pages`)
      loading.value = false
    }

    /**
     * Called when a field changes in the PDF (event from PDFJSViewer component)
     */
    const onPdfFieldChange = ({ fieldName, value, type }) => {
      if (!pdfSyncEnabled.value || !isEditMode.value) return

      // TRANSLATE: PDF field name → Database field name
      const dbFieldName = pdfFieldToDbField(fieldName) || fieldName

      console.log(`[PDFViewerWindow] PDF field changed: ${fieldName} (DB: ${dbFieldName}) = ${value}`)

      // Sync to right panel formData
      const structuredFields = ['customer_name', 'customer_id', 'local_amount', 'amount', 'report_no']

      if (structuredFields.includes(dbFieldName)) {
        // Update structured field
        if (formData.value[dbFieldName] !== value) {
          formData.value[dbFieldName] = value
          markFieldAsModified(dbFieldName)
        }
      } else {
        // Update form_data field
        if (!formData.value.form_data) {
          formData.value.form_data = {}
        }

        // Handle different field types
        let processedValue = value
        if (type === 'checkbox') {
          processedValue = Boolean(value)
        }

        if (formData.value.form_data[dbFieldName] !== processedValue) {
          formData.value.form_data[dbFieldName] = processedValue
          markFieldAsModified(dbFieldName)
        }
      }

      console.log(`[PDFViewerWindow] ✅ Panel synced from PDF: ${dbFieldName}`)
    }

    /**
     * Called when PDF.js encounters an error
     */
    const onPdfError = (err) => {
      console.error('[PDFViewerWindow] PDF.js error:', err)
      error.value = t('amlo.pdfViewer.loadError') + ': ' + err.message
      loading.value = false
    }

    /**
     * Panel field change handler - syncs to PDF using PDF.js API
     */
    const onPanelFieldChange = (fieldName, value) => {
      console.log(`[PDFViewerWindow] Panel field changed: ${fieldName} = ${value}`)

      // Mark as modified
      markFieldAsModified(fieldName)

      // Sync to PDF using PDF.js API
      if (pdfSyncEnabled.value && isEditMode.value && pdfViewerRef.value) {
        // TRANSLATE: Database field name → PDF field name
        const pdfFieldName = dbFieldToPdfField(fieldName) || fieldName

        console.log(`[PDFViewerWindow] Syncing Panel → PDF: ${fieldName} (PDF: ${pdfFieldName}) = ${value}`)

        // Update PDF viewer using setFormData method
        const updateData = { [pdfFieldName]: value }
        pdfViewerRef.value.setFormData(updateData)

        console.log(`[PDFViewerWindow] ✅ PDF synced from panel: ${pdfFieldName}`)
      }
    }

    // Signature functions (existing)
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
        await submitSignature()
      }
    }

    // Extract all current field values from PDF using PDF.js viewer API
    const extractPdfFormData = () => {
      console.log('[PDFViewerWindow] 🔍 开始提取PDF字段数据 (PDF.js API)...')
      console.log('[PDFViewerWindow] - pdfViewerRef存在:', !!pdfViewerRef.value)

      if (!pdfViewerRef.value) {
        console.warn('[PDFViewerWindow] ❌ PDF.js viewer引用不存在，无法提取数据')
        return null
      }

      try {
        // ✅ Use PDF.js viewer's getFormData() method to extract field values
        const extractedPdfData = pdfViewerRef.value.getFormData()

        console.log(`[PDFViewerWindow] 提取到 ${Object.keys(extractedPdfData).length} 个PDF字段`)
        console.log('[PDFViewerWindow] 有值的字段数:', Object.values(extractedPdfData).filter(v => v).length)

        // Log sample of extracted data
        const sampleFields = Object.entries(extractedPdfData).slice(0, 5)
        sampleFields.forEach(([key, value]) => {
          console.log(`[PDFViewerWindow] - ✓ [${key}] = "${value}"`)
        })

        // TRANSLATE: PDF field names → Database field names
        console.log('[PDFViewerWindow] 🔄 开始转换: PDF字段名 → 数据库字段名...')
        const extractedDbData = pdfDataToDbData(extractedPdfData)

        console.log(`[PDFViewerWindow] ✅ 转换完成: ${Object.keys(extractedPdfData).length} PDF字段 → ${Object.keys(extractedDbData).length} 数据库字段`)
        console.log('[PDFViewerWindow] 数据库字段列表 (前10个):', Object.keys(extractedDbData).slice(0, 10).join(', '))

        return extractedDbData
      } catch (error) {
        console.error('[PDFViewerWindow] ❌ 提取PDF表单数据时出错:', error)
        console.error('[PDFViewerWindow] 错误堆栈:', error.stack)
        return null
      }
    }

    const submitSignature = async () => {
      console.log('========================================')
      console.log('[submitSignature] 🚀 开始签名提交流程...')
      console.log('[submitSignature] - 预约ID:', reservationId.value)
      console.log('[submitSignature] - 有签名数据:', !!signatureData.value)
      console.log('========================================')

      if (!signatureData.value || !reservationId.value) {
        console.warn('[submitSignature] ⚠️ 缺少签名数据或预约ID，提交取消')
        return
      }

      submitting.value = true
      try {
        // 步骤0: 从PDF提取当前所有字段值（防止同步失败导致数据丢失）
        console.log('[submitSignature] 📋 步骤0: 从PDF提取当前字段值...')
        const pdfExtractedData = extractPdfFormData()

        console.log('[submitSignature] 提取结果:', pdfExtractedData ? `成功，${Object.keys(pdfExtractedData).length}个字段` : '失败或无数据')

        if (pdfExtractedData && Object.keys(pdfExtractedData).length > 0) {
          console.log('[submitSignature] 🔄 合并PDF数据到formData...')
          console.log('[submitSignature] formData当前状态:', JSON.stringify(formData.value, null, 2))

          // 合并提取的PDF数据到formData
          if (!formData.value.form_data) {
            formData.value.form_data = {}
          }

          let mergedCount = 0
          Object.keys(pdfExtractedData).forEach(fieldName => {
            const structuredFields = ['customer_name', 'customer_id', 'local_amount', 'amount', 'report_no']
            if (structuredFields.includes(fieldName)) {
              formData.value[fieldName] = pdfExtractedData[fieldName]
              console.log(`[submitSignature]   - 结构化字段: ${fieldName} = "${pdfExtractedData[fieldName]}"`)
            } else {
              formData.value.form_data[fieldName] = pdfExtractedData[fieldName]
              console.log(`[submitSignature]   - 表单字段: ${fieldName} = "${pdfExtractedData[fieldName]}"`)
            }
            mergedCount++
          })

          console.log(`[submitSignature] ✅ PDF数据已合并到formData (${mergedCount}个字段)`)
          console.log('[submitSignature] formData合并后:', JSON.stringify(formData.value, null, 2))
        } else {
          console.warn('[submitSignature] ⚠️ 未提取到PDF数据，将使用现有formData')
        }

        // 步骤1: 如果有表单修改，先保存表单数据
        const hasModifications = modifiedFields.value.size > 0 || (pdfExtractedData && Object.keys(pdfExtractedData).length > 0)
        console.log('[submitSignature] 📝 步骤1: 检查是否需要保存表单数据...')
        console.log('[submitSignature] - 修改的字段数:', modifiedFields.value.size)
        console.log('[submitSignature] - PDF提取的字段数:', pdfExtractedData ? Object.keys(pdfExtractedData).length : 0)
        console.log('[submitSignature] - 需要保存:', hasModifications)

        if (hasModifications) {
          console.log('[submitSignature] 💾 保存表单数据到后端...')

          try {
            const submitData = {
              reservation_id: reservationId.value,
              modified_data: formData.value,
              modified_fields: Array.from(modifiedFields.value),
              modifications_summary: getModificationsSummary()
            }

            console.log('[submitSignature] 提交数据:', JSON.stringify(submitData, null, 2))

            const modResponse = await amloService.submitModifiedReport(submitData)

            console.log('[submitSignature] 后端响应:', modResponse.data)

            if (modResponse.data.success) {
              console.log('[submitSignature] ✅ 表单修改保存成功')
              // 清除修改标记
              modifiedFields.value.clear()
              originalData.value = JSON.parse(JSON.stringify(formData.value))
            } else {
              throw new Error(modResponse.data.message || '表单修改保存失败')
            }
          } catch (modError) {
            console.error('[submitSignature] ❌ 表单修改保存失败:', modError)
            console.error('[submitSignature] 错误详情:', modError.response?.data || modError.message)
            alert('表单修改保存失败: ' + (modError.response?.data?.message || modError.message) + '\n签名提交已取消。')
            submitting.value = false
            return
          }
        } else {
          console.log('[submitSignature] ⏭️ 无修改，跳过保存步骤')
        }

        // 步骤2: 提交签名
        console.log('[submitSignature] ✍️ 步骤2: 提交签名到后端...')
        const now = new Date()
        const day = String(now.getDate()).padStart(2, '0')
        const month = String(now.getMonth() + 1).padStart(2, '0')
        const year = now.getFullYear()
        const reporterDate = `${day}/${month}/${year}`

        console.log('[submitSignature] - 签名日期:', reporterDate)
        console.log('[submitSignature] - 签名数据长度:', signatureData.value.length, '字符')

        const signaturePayload = {
          signature: signatureData.value,
          reporter_date: reporterDate
        }

        console.log('[submitSignature] 发送签名请求到:', `/amlo/reservations/${reservationId.value}/signature`)

        const signatureResponse = await api.post(`/amlo/reservations/${reservationId.value}/signature`, signaturePayload)

        console.log('[submitSignature] 签名API响应:', signatureResponse.data)
        console.log('[submitSignature] ✅ 签名提交成功')

        // 步骤3: 重新加载PDF
        console.log('[submitSignature] 🔄 步骤3: 重新加载PDF以显示更新内容...')
        await loadPDF()
        console.log('[submitSignature] ✅ PDF重新加载完成')

        maximizeWindow()
        console.log('[submitSignature] ✅ 窗口已最大化')

        console.log('========================================')
        console.log('[submitSignature] 🎉 签名提交流程完成！')
        console.log('========================================')

        // 显示成功消息
        alert(t('amlo.signature.submitSuccess') || '提交成功！表单内容和签名已保存。')
      } catch (error) {
        console.error('========================================')
        console.error('[submitSignature] ❌ 签名提交流程失败')
        console.error('[submitSignature] 错误:', error)
        console.error('[submitSignature] 错误消息:', error.message)
        console.error('[submitSignature] 响应数据:', error.response?.data)
        console.error('[submitSignature] 错误堆栈:', error.stack)
        console.error('========================================')
        alert(t('amlo.signature.submitFailed') || '签名提交失败: ' + (error.response?.data?.message || error.message))
      } finally {
        submitting.value = false
        console.log('[submitSignature] 提交状态重置，submitting =', submitting.value)
      }
    }

    // Window management functions (existing)
    const maximizeWindow = () => {
      try {
        console.log('[PDFViewerWindow] 尝试最大化窗口...')
        const screenWidth = window.screen.availWidth
        const screenHeight = window.screen.availHeight
        window.resizeTo(screenWidth, screenHeight)
        window.moveTo(0, 0)
        console.log('[PDFViewerWindow] 最大化完成')
      } catch (e) {
        console.error('[PDFViewerWindow] 最大化失败:', e)
      }
    }

    const closeWindow = () => {
      window.close()
    }

    const closeHint = () => {
      showSecondScreenHint.value = false
      stopPositionMonitoring()
    }

    const isOnExtendedScreen = () => {
      const currentLeft = window.screenX || window.screenLeft
      const primaryScreenWidth = 1620
      return currentLeft >= primaryScreenWidth
    }

    const startPositionMonitoring = () => {
      if (positionCheckTimer.value) {
        clearInterval(positionCheckTimer.value)
      }
      console.log('[PDFViewerWindow] 启动窗口位置监控')
      positionCheckTimer.value = setInterval(() => {
        if (isOnExtendedScreen()) {
          console.log('[PDFViewerWindow] 检测到窗口已移动到扩展屏，自动隐藏提示')
          showSecondScreenHint.value = false
          stopPositionMonitoring()
        }
      }, 2000)
    }

    const stopPositionMonitoring = () => {
      if (positionCheckTimer.value) {
        console.log('[PDFViewerWindow] 停止窗口位置监控')
        clearInterval(positionCheckTimer.value)
        positionCheckTimer.value = null
      }
    }

    const toggleFullscreen = async () => {
      try {
        if (!document.fullscreenElement) {
          console.log('[PDFViewerWindow] 进入全屏模式')
          await document.documentElement.requestFullscreen()
          console.log('[PDFViewerWindow] ✅ 已进入全屏模式')

          if (!readonly.value && !isOnExtendedScreen() && !showSecondScreenHint.value) {
            setTimeout(() => {
              showSecondScreenHint.value = true
              console.log('[PDFViewerWindow] 显示扩展屏提示')
              startPositionMonitoring()
            }, 1000)
          }
        } else {
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

      setTimeout(() => {
        maximizeWindow()
      }, 100)

      setTimeout(() => {
        if (readonly.value) {
          console.log('[PDFViewerWindow] 只读模式，不显示扩展屏提示')
          return
        }

        if (!isOnExtendedScreen()) {
          console.log('[PDFViewerWindow] 窗口在主屏幕上，显示扩展显示器提示')
          showSecondScreenHint.value = true
          startPositionMonitoring()
        }
      }, 1000)

      const handleKeyPress = (e) => {
        if (e.key === 'F11') {
          e.preventDefault()
          toggleFullscreen()
        }
      }
      window.addEventListener('keydown', handleKeyPress)

      return () => {
        window.removeEventListener('keydown', handleKeyPress)
      }
    })

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
      pdfViewerRef,
      showSecondScreenHint,
      title,
      reportType,
      allowPrint,
      allowSignature,
      readonly,
      isEditMode,
      loadingFields,
      editableFields,
      formData,
      hasModifications,
      modifiedFieldsCount,
      showSummary,
      submittingModifications,
      toggleEditMode,
      markFieldAsModified,
      isFieldModified,
      resetChanges,
      toggleModificationSummary,
      submitModifications,
      getFieldLabel,
      getOriginalValue,
      getCurrentValue,
      formatAmount,
      loadPDF,
      onPdfLoaded,
      onPdfFieldChange,
      onPdfError,
      onPanelFieldChange,
      openSignaturePad,
      closeSignaturePad,
      saveSignature,
      closeWindow,
      closeHint,
      toggleFullscreen,
      modifiedFields,
      originalData
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
  justify-content: space-between;
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

.header-right {
  display: flex;
  align-items: center;
}

.pdf-content {
  flex: 1;
  display: flex;
  overflow: hidden;
  position: relative;
  padding-bottom: 80px;
}

.pdf-content.with-edit-panel {
  padding-bottom: 80px;
}

.pdf-preview {
  flex: 1;
  display: flex;
  transition: all 0.3s ease;
}

.pdf-preview.edit-mode {
  flex: 0 0 60%;
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

/* Edit Panel */
.edit-panel {
  flex: 0 0 40%;
  background: white;
  border-left: 1px solid #dee2e6;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  padding: 1rem;
  border-bottom: 1px solid #dee2e6;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #f8f9fa;
}

.panel-header h5 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.form-fields {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  margin-bottom: 0;
}

.form-label {
  margin-bottom: 0.5rem;
  font-weight: 500;
  font-size: 0.9rem;
}

.form-control.is-modified {
  border-color: #ffc107;
  background-color: #fff3cd;
}

/* Group Header */
.field-group-header {
  margin-top: 1.5rem;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid #0d6efd;
}

.field-group-header:first-child {
  margin-top: 0;
}

.group-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: #0d6efd;
}

.panel-footer {
  border-top: 1px solid #dee2e6;
  background-color: #f8f9fa;
}

.modification-summary {
  padding: 1rem;
  background: white;
}

.modification-summary h6 {
  margin-bottom: 0.5rem;
  font-weight: 600;
}

.modification-summary .table {
  font-size: 0.85rem;
  margin-bottom: 0;
}

/* Signature Overlay */
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

/* Footer */
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

/* Extended Screen Hint */
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

/* Print styles */
@media print {
  .pdf-header,
  .pdf-footer,
  .edit-panel {
    display: none;
  }

  .pdf-content {
    height: 100vh;
    padding-bottom: 0;
  }

  .pdf-preview {
    flex: 1;
  }

  .pdf-iframe {
    height: 100vh;
  }
}
</style>

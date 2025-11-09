<template>
  <div class="signature-field-wrapper">
    <SignaturePad
      :model-value="value"
      :width="field.width || '100%'"
      :height="field.height || 200"
      :line-color="field.lineColor || '#000000'"
      :line-width="field.lineWidth || 2"
      :placeholder="field.placeholder || $t('amlo.form.signature.placeholder')"
      :show-device-status="true"
      :use-pressure="true"
      :allow-undo="true"
      :show-device-info="false"
      @update:modelValue="handleUpdate"
      @change="handleChange"
      @deviceDetected="handleDeviceDetected"
    />
    <small v-if="field.help" class="form-text text-muted d-block mt-1">
      {{ field.help }}
    </small>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import SignaturePad from '@/components/amlo/SignaturePad.vue'

export default {
  name: 'SignatureField',
  components: {
    SignaturePad
  },
  props: {
    field: {
      type: Object,
      required: true
    },
    value: {
      type: String,
      default: null
    }
  },
  emits: ['update:value'],
  setup(props, { emit }) {
    const { t } = useI18n()
    const deviceDetected = ref(false)

    const handleUpdate = (newValue) => {
      emit('update:value', newValue)
    }

    const handleChange = (signatureData) => {
      console.log('[SignatureField] Signature changed:', signatureData ? `${(signatureData.length / 1024).toFixed(2)} KB` : 'null')
    }

    const handleDeviceDetected = (device) => {
      deviceDetected.value = true
      console.log('[SignatureField] Pen device detected:', device)
    }

    return {
      handleUpdate,
      handleChange,
      handleDeviceDetected,
      deviceDetected,
      t
    }
  }
}
</script>

<style scoped>
.signature-field-wrapper {
  width: 100%;
}
</style>

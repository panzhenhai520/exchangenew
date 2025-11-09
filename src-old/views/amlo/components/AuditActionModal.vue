<template>
  <a-modal
    v-model:visible="modalVisible"
    :title="$t('amlo.reservation.audit')"
    :confirm-loading="loading"
    @ok="handleSubmit"
  >
    <a-form
      ref="formRef"
      :model="auditData"
      :label-col="{ span: 6 }"
      :wrapper-col="{ span: 16 }"
    >
      <a-form-item :label="$t('amlo.reservation.auditAction')" required>
        <a-radio-group v-model:value="auditData.action">
          <a-radio value="approve">{{ $t('amlo.reservation.approve') }}</a-radio>
          <a-radio value="reject">{{ $t('amlo.reservation.reject') }}</a-radio>
        </a-radio-group>
      </a-form-item>

      <a-form-item :label="$t('common.remarks')">
        <a-textarea
          v-model:value="auditData.remarks"
          :rows="4"
          :placeholder="$t('common.pleaseInput')"
        />
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script>
import { ref, computed, watch } from 'vue'

export default {
  name: 'AuditActionModal',
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    reservation: {
      type: Object,
      default: null
    }
  },
  emits: ['update:visible', 'submit'],
  setup(props, { emit }) {
    const loading = ref(false)
    const auditData = ref({
      action: 'approve',
      remarks: ''
    })

    const modalVisible = computed({
      get: () => props.visible,
      set: (value) => emit('update:visible', value)
    })

    const handleSubmit = () => {
      emit('submit', { ...auditData.value })
      // 重置表单
      auditData.value = {
        action: 'approve',
        remarks: ''
      }
    }

    // 监听visible变化，重置表单
    watch(() => props.visible, (newVal) => {
      if (newVal) {
        auditData.value = {
          action: 'approve',
          remarks: ''
        }
      }
    })

    return {
      loading,
      modalVisible,
      auditData,
      handleSubmit
    }
  }
}
</script>

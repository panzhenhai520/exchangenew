<template>
  <div class="transactor-type-radio">
    <a-radio-group :value="selectedValue" @change="handleChange">
      <a-radio :value="'person'">
        {{ $t('amlo.form.transactorType.person') }}
      </a-radio>
      <a-radio :value="'juristic'">
        {{ $t('amlo.form.transactorType.juristic') }}
      </a-radio>
    </a-radio-group>
  </div>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'TransactorTypeRadio',
  props: {
    // 两个布尔字段的值
    personValue: {
      type: Boolean,
      default: true
    },
    juristicValue: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:personValue', 'update:juristicValue'],
  setup(props, { emit }) {
    // 计算当前选中的值
    const selectedValue = computed(() => {
      if (props.juristicValue) {
        return 'juristic'
      }
      return 'person' // 默认个人
    })

    // 处理变更
    const handleChange = (e) => {
      const value = e.target.value
      if (value === 'person') {
        // 选择个人: person=true, juristic=false
        emit('update:personValue', true)
        emit('update:juristicValue', false)
      } else if (value === 'juristic') {
        // 选择法人: person=false, juristic=true
        emit('update:personValue', false)
        emit('update:juristicValue', true)
      }
    }

    return {
      selectedValue,
      handleChange
    }
  }
}
</script>

<style scoped>
.transactor-type-radio {
  padding: 8px 0;
}

.transactor-type-radio :deep(.ant-radio-group) {
  display: flex;
  gap: 24px;
}

.transactor-type-radio :deep(.ant-radio-wrapper) {
  font-size: 14px;
  font-weight: 500;
}
</style>

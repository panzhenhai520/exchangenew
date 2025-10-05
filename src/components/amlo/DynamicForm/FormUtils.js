/**
 * 表单工具函数
 * 提供表单数据构建、重置等辅助功能
 */

/**
 * 根据字段定义构建表单数据对象
 * @param {Array} formFields - 字段定义数组
 * @param {Object} initialData - 初始数据
 * @returns {Object} 表单数据对象
 */
export function buildFormData(formFields, initialData = {}) {
  const formData = {}

  formFields.forEach(field => {
    const fieldName = field.field_name

    // 优先使用初始数据中的值
    if (initialData[fieldName] !== undefined) {
      formData[fieldName] = initialData[fieldName]
      return
    }

    // 根据字段类型设置默认值
    switch (field.field_type) {
      case 'number':
        formData[fieldName] = null
        break
      case 'checkbox':
        formData[fieldName] = false
        break
      case 'select':
        // 检查是否多选
        if (field.validation_rules) {
          try {
            const rules = JSON.parse(field.validation_rules)
            formData[fieldName] = rules.multiple ? [] : null
          } catch (e) {
            formData[fieldName] = null
          }
        } else {
          formData[fieldName] = null
        }
        break
      case 'date':
        formData[fieldName] = ''
        break
      case 'text':
      case 'textarea':
      default:
        formData[fieldName] = ''
        break
    }
  })

  return formData
}

/**
 * 重置表单数据
 * @param {Array} formFields - 字段定义数组
 * @returns {Object} 重置后的表单数据
 */
export function resetFormData(formFields) {
  return buildFormData(formFields, {})
}

/**
 * 提取表单变更的字段
 * @param {Object} formData - 当前表单数据
 * @param {Object} originalData - 原始数据
 * @returns {Object} 变更的字段
 */
export function extractChangedFields(formData, originalData) {
  const changedFields = {}

  Object.keys(formData).forEach(key => {
    if (formData[key] !== originalData[key]) {
      changedFields[key] = formData[key]
    }
  })

  return changedFields
}

/**
 * 格式化表单数据用于提交
 * @param {Object} formData - 表单数据
 * @param {Array} formFields - 字段定义数组
 * @returns {Object} 格式化后的数据
 */
export function formatFormDataForSubmit(formData, formFields) {
  const formattedData = {}

  formFields.forEach(field => {
    const fieldName = field.field_name
    const value = formData[fieldName]

    // 跳过空值（根据字段类型判断）
    if (value === null || value === undefined || value === '') {
      if (!field.is_required) {
        return // 非必填字段且为空，跳过
      }
    }

    // 根据字段类型格式化
    switch (field.field_type) {
      case 'number':
        formattedData[fieldName] = value !== null ? Number(value) : null
        break
      case 'checkbox':
        formattedData[fieldName] = Boolean(value)
        break
      case 'select':
        // 多选返回数组，单选返回字符串
        formattedData[fieldName] = value
        break
      default:
        formattedData[fieldName] = value
        break
    }
  })

  return formattedData
}

/**
 * 深拷贝对象
 * @param {Object} obj - 要拷贝的对象
 * @returns {Object} 拷贝后的对象
 */
export function deepClone(obj) {
  if (obj === null || typeof obj !== 'object') {
    return obj
  }

  if (Array.isArray(obj)) {
    return obj.map(item => deepClone(item))
  }

  const cloned = {}
  Object.keys(obj).forEach(key => {
    cloned[key] = deepClone(obj[key])
  })

  return cloned
}

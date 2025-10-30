import { readValidationRules } from './fieldHelpers.js'

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
    const rules = readValidationRules(field)
    const fieldType = (field.field_type || '').toUpperCase()

    // 优先使用初始数据中的值
    if (
      initialData &&
      Object.prototype.hasOwnProperty.call(initialData, fieldName) &&
      initialData[fieldName] !== undefined
    ) {
      formData[fieldName] = initialData[fieldName]
      return
    }

    // 根据字段类型设置默认值
    switch (fieldType) {
      case 'NUMBER':
      case 'DECIMAL':
      case 'FLOAT':
      case 'DOUBLE':
      case 'INT':
        formData[fieldName] = null
        break
      case 'CHECKBOX':
      case 'BOOLEAN':
        formData[fieldName] = rules.default_value ?? false
        break
      case 'ENUM':
        if (rules.multiple) {
          formData[fieldName] = Array.isArray(rules.default_value)
            ? rules.default_value
            : []
        } else {
          formData[fieldName] = rules.default_value ?? null
        }
        break
      case 'DATE':
      case 'DATETIME':
        formData[fieldName] = rules.default_value || ''
        break
      case 'TEXT':
      case 'VARCHAR':
      case 'TEXTAREA':
      default:
        formData[fieldName] = rules.default_value ?? ''
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
    const fieldType = (field.field_type || '').toUpperCase()
    switch (fieldType) {
      case 'NUMBER':
      case 'DECIMAL':
      case 'FLOAT':
      case 'DOUBLE':
      case 'INT':
        formattedData[fieldName] =
          value !== null && value !== '' ? Number(value) : null
        break
      case 'CHECKBOX':
      case 'BOOLEAN':
        formattedData[fieldName] = Boolean(value)
        break
      case 'ENUM':
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

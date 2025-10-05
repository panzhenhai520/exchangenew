/**
 * 表单验证逻辑
 * 支持5种验证类型：type, length, range, pattern, enum
 */

/**
 * 验证单个字段
 * @param {*} value - 字段值
 * @param {Object} field - 字段定义
 * @returns {Array} 错误消息数组
 */
export function validateField(value, field) {
  const errors = []

  // 必填验证
  if (field.is_required && (value === null || value === undefined || value === '')) {
    errors.push(`${field.field_label} 是必填项`)
    return errors // 必填验证失败，不再进行其他验证
  }

  // 如果字段为空且非必填，跳过其他验证
  if (value === null || value === undefined || value === '') {
    return errors
  }

  // 解析验证规则
  let rules = {}
  if (field.validation_rules) {
    try {
      rules = JSON.parse(field.validation_rules)
    } catch (e) {
      console.error('解析验证规则失败:', e)
      return errors
    }
  }

  // 1. 类型验证
  const typeError = validateType(value, field.field_type, field.field_label)
  if (typeError) {
    errors.push(typeError)
  }

  // 2. 长度验证
  if (field.field_type === 'text' || field.field_type === 'textarea') {
    const lengthError = validateLength(value, rules, field.field_label)
    if (lengthError) {
      errors.push(lengthError)
    }
  }

  // 3. 范围验证
  if (field.field_type === 'number') {
    const rangeError = validateRange(value, rules, field.field_label)
    if (rangeError) {
      errors.push(rangeError)
    }
  }

  // 4. 正则验证
  if (rules.pattern) {
    const patternError = validatePattern(value, rules.pattern, field.field_label)
    if (patternError) {
      errors.push(patternError)
    }
  }

  // 5. 枚举验证
  if (rules.enum_values && Array.isArray(rules.enum_values)) {
    const enumError = validateEnum(value, rules.enum_values, field.field_label)
    if (enumError) {
      errors.push(enumError)
    }
  }

  return errors
}

/**
 * 类型验证
 */
function validateType(value, fieldType, fieldLabel) {
  switch (fieldType) {
    case 'number':
      if (typeof value !== 'number' || isNaN(value)) {
        return `${fieldLabel} 必须是数字`
      }
      break
    case 'checkbox':
      if (typeof value !== 'boolean') {
        return `${fieldLabel} 必须是布尔值`
      }
      break
    case 'date':
      // 日期格式验证（DD/MM/YYYY）
      if (typeof value !== 'string' || !/^\d{2}\/\d{2}\/\d{4}$/.test(value)) {
        return `${fieldLabel} 日期格式不正确（应为 DD/MM/YYYY）`
      }
      break
  }
  return null
}

/**
 * 长度验证
 */
function validateLength(value, rules, fieldLabel) {
  const strValue = String(value)

  if (rules.min_length && strValue.length < rules.min_length) {
    return `${fieldLabel} 长度不能少于 ${rules.min_length} 个字符`
  }

  if (rules.max_length && strValue.length > rules.max_length) {
    return `${fieldLabel} 长度不能超过 ${rules.max_length} 个字符`
  }

  return null
}

/**
 * 范围验证
 */
function validateRange(value, rules, fieldLabel) {
  if (rules.min_value !== undefined && value < rules.min_value) {
    return `${fieldLabel} 不能小于 ${rules.min_value}`
  }

  if (rules.max_value !== undefined && value > rules.max_value) {
    return `${fieldLabel} 不能大于 ${rules.max_value}`
  }

  return null
}

/**
 * 正则验证
 */
function validatePattern(value, pattern, fieldLabel) {
  try {
    const regex = new RegExp(pattern)
    if (!regex.test(String(value))) {
      return `${fieldLabel} 格式不正确`
    }
  } catch (e) {
    console.error('正则表达式错误:', e)
    return `${fieldLabel} 验证规则配置错误`
  }
  return null
}

/**
 * 枚举验证
 */
function validateEnum(value, enumValues, fieldLabel) {
  // 支持单选和多选
  if (Array.isArray(value)) {
    // 多选：检查所有值是否都在枚举中
    const invalidValues = value.filter(v => !enumValues.includes(v))
    if (invalidValues.length > 0) {
      return `${fieldLabel} 包含无效选项`
    }
  } else {
    // 单选：检查值是否在枚举中
    if (!enumValues.includes(value)) {
      return `${fieldLabel} 不是有效选项`
    }
  }
  return null
}

/**
 * 验证整个表单
 * @param {Object} formData - 表单数据
 * @param {Array} formFields - 表单字段定义
 * @returns {Object} { valid: boolean, errors: {} }
 */
export function validateForm(formData, formFields) {
  const errors = {}
  let valid = true

  formFields.forEach(field => {
    const fieldValue = formData[field.field_name]
    const fieldErrors = validateField(fieldValue, field)

    if (fieldErrors.length > 0) {
      errors[field.field_name] = fieldErrors
      valid = false
    }
  })

  return { valid, errors }
}

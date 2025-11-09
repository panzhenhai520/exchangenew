/**
 * 格式化日期时间
 * @param {string} datetime - 日期时间字符串
 * @returns {string} 格式化后的日期时间
 */
export function formatDateTime(datetime) {
  if (!datetime) return '';
  const date = new Date(datetime);
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  }).format(date);
}

/**
 * 格式化交易时间 - 支持不同的输入格式
 * @param {string|Object} dateInput - 日期输入（可以是字符串或包含date/time的对象）
 * @param {string} timeInput - 时间输入（可选）
 * @returns {string} 格式化后的日期时间
 */
export function formatTransactionTime(dateInput, timeInput = null) {
  try {
    // 情况1: 如果dateInput已经是完整的日期时间字符串
    if (typeof dateInput === 'string' && !timeInput) {
      // 检查是否包含时间部分
      if (dateInput.includes(' ') || dateInput.includes('T')) {
        return formatDateTime(dateInput);
      } else {
        // 只有日期，返回日期格式
        return formatDate(dateInput);
      }
    }
    
    // 情况2: 分开的日期和时间
    if (dateInput && timeInput) {
      // 组合日期和时间
      const dateStr = typeof dateInput === 'string' ? dateInput : dateInput.toString();
      const combinedDateTime = `${dateStr} ${timeInput}`;
      return formatDateTime(combinedDateTime);
    }
    
    // 情况3: 对象输入 {date: 'YYYY-MM-DD', time: 'HH:MM:SS'}
    if (typeof dateInput === 'object' && dateInput.date) {
      const timeStr = dateInput.time || '00:00:00';
      return formatDateTime(`${dateInput.date} ${timeStr}`);
    }
    
    // 默认情况：尝试直接格式化
    return formatDateTime(dateInput);
    
  } catch (error) {
    console.error('格式化交易时间出错:', error, { dateInput, timeInput });
    return dateInput ? dateInput.toString() : '';
  }
}

/**
 * 格式化时间为票据显示格式
 * @param {string} dateInput - 日期
 * @param {string} timeInput - 时间
 * @returns {string} 格式化后的票据时间（例如：2025-07-04 17:13:54）
 */
export function formatReceiptTime(dateInput, timeInput = null) {
  try {
    let fullDateTime;
    
    if (dateInput && timeInput) {
      fullDateTime = `${dateInput} ${timeInput}`;
    } else if (typeof dateInput === 'string' && (dateInput.includes(' ') || dateInput.includes('T'))) {
      fullDateTime = dateInput;
    } else {
      fullDateTime = dateInput;
    }
    
    const date = new Date(fullDateTime);
    // 改为ISO格式：YYYY-MM-DD HH:MM:SS
    return date.toISOString().replace('T', ' ').substring(0, 19);
    
  } catch (error) {
    console.error('格式化票据时间出错:', error);
    return `${dateInput} ${timeInput || ''}`.trim();
  }
}

/**
 * 格式化金额
 * @param {number} amount - 金额
 * @param {number} decimals - 小数位数
 * @returns {string} 格式化后的金额
 */
export function formatAmount(amount, decimals = 2) {
  if (amount === null || amount === undefined) return '';
  return new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  }).format(amount);
}

/**
 * 格式化日期
 * @param {string} date - 日期字符串
 * @returns {string} 格式化后的日期
 */
export function formatDate(date) {
  if (!date) return '';
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  }).format(new Date(date));
}

/**
 * 格式化时间（只显示时间部分）
 * @param {string} time - 时间字符串 (HH:MM:SS)
 * @returns {string} 格式化后的时间
 */
export function formatTime(time) {
  if (!time) return '';
  // 如果包含日期部分，提取时间部分
  if (time.includes(' ')) {
    time = time.split(' ')[1] || time;
  }
  return time;
} 
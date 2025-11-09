/**
 * 格式化金额显示
 * @param {number} amount 金额
 * @param {number} decimals 小数位数，默认2位
 * @returns {string} 格式化后的金额字符串
 */
export function formatAmount(amount, decimals = 2) {
  if (amount === null || amount === undefined) {
    return '-';
  }
  
  const num = Number(amount);
  if (isNaN(num)) {
    return '-';
  }
  
  return num.toLocaleString('zh-CN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  });
}

/**
 * 格式化汇率显示
 * @param {number} rate 汇率
 * @param {number} decimals 小数位数，默认4位
 * @returns {string} 格式化后的汇率字符串
 */
export function formatRate(rate, decimals = 4) {
  if (rate === null || rate === undefined) {
    return '-';
  }
  
  const num = Number(rate);
  if (isNaN(num)) {
    return '-';
  }
  
  return num.toLocaleString('zh-CN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  });
} 
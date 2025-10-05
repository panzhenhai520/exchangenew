/**
 * 格式化日期为 YYYY-MM-DD 格式
 * @param {Date} date - 要格式化的日期对象
 * @returns {string} 格式化后的日期字符串
 */
export function formatDate(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * 格式化日期时间为 YYYY-MM-DD HH:mm:ss 格式
 * @param {Date} date - 要格式化的日期对象
 * @returns {string} 格式化后的日期时间字符串
 */
export function formatDateTime(date) {
  const dateStr = formatDate(date);
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  const seconds = String(date.getSeconds()).padStart(2, '0');
  return `${dateStr} ${hours}:${minutes}:${seconds}`;
}

/**
 * 解析日期字符串为 Date 对象
 * @param {string} dateStr - 日期字符串 (YYYY-MM-DD 格式)
 * @returns {Date} 日期对象
 */
export function parseDate(dateStr) {
  return new Date(dateStr);
}

/**
 * 获取今天的日期字符串 (YYYY-MM-DD 格式)
 * @returns {string} 今天的日期字符串
 */
export function getToday() {
  return formatDate(new Date());
}

/**
 * 获取指定天数前后的日期
 * @param {number} days - 天数，正数表示之后，负数表示之前
 * @param {Date} [date] - 基准日期，默认为今天
 * @returns {Date} 计算后的日期
 */
export function addDays(days, date = new Date()) {
  const result = new Date(date);
  result.setDate(result.getDate() + days);
  return result;
} 
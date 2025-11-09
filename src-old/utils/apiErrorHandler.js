/**
 * API错误处理工具
 * 专门处理AMLO审核金额超额等特殊错误
 */

import { message } from 'ant-design-vue';

/**
 * 检查是否为AMLO审核金额超额错误
 * @param {Object} error - axios错误对象
 * @returns {boolean}
 */
export function isApprovalAmountExceededError(error) {
  return (
    error.response?.status === 403 &&
    error.response?.data?.error_type === 'amount_exceeded'
  );
}

/**
 * 提取错误数据
 * @param {Object} error - axios错误对象
 * @returns {Object} 错误数据对象
 */
export function extractErrorData(error) {
  if (isApprovalAmountExceededError(error)) {
    return {
      message: error.response.data.message || '交易金额超过审核限额',
      approved_amount: error.response.data.approved_amount || 0,
      actual_amount: error.response.data.actual_amount || 0,
      reservation_id: error.response.data.reservation_id,
      reservation_no: error.response.data.reservation_no || '',
      report_type: error.response.data.report_type || ''
    };
  }
  return null;
}

/**
 * 处理交易API错误
 * @param {Object} error - axios错误对象
 * @param {Function} onAmountExceeded - 金额超额回调函数
 * @param {Function} onOtherError - 其他错误回调函数
 */
export function handleTransactionError(error, onAmountExceeded, onOtherError) {
  if (isApprovalAmountExceededError(error)) {
    const errorData = extractErrorData(error);
    if (onAmountExceeded && typeof onAmountExceeded === 'function') {
      onAmountExceeded(errorData);
    }
  } else {
    // 处理其他类型的错误
    const errorMessage = error.response?.data?.message || error.message || '交易失败';
    if (onOtherError && typeof onOtherError === 'function') {
      onOtherError(errorMessage);
    } else {
      message.error(errorMessage);
    }
  }
}

/**
 * 创建标准错误处理配置
 * @param {Object} options - 配置选项
 * @returns {Object} 错误处理配置
 */
export function createErrorHandlerConfig(options = {}) {
  const {
    onAmountExceeded,
    onOtherError,
    showMessage = true
  } = options;

  return {
    handleError: (error) => {
      if (isApprovalAmountExceededError(error)) {
        const errorData = extractErrorData(error);
        if (onAmountExceeded) {
          onAmountExceeded(errorData);
        }
        return { type: 'amount_exceeded', data: errorData };
      } else {
        const errorMessage = error.response?.data?.message || error.message || '操作失败';
        if (showMessage) {
          message.error(errorMessage);
        }
        if (onOtherError) {
          onOtherError(errorMessage);
        }
        return { type: 'other', message: errorMessage };
      }
    }
  };
}

export default {
  isApprovalAmountExceededError,
  extractErrorData,
  handleTransactionError,
  createErrorHandlerConfig
};

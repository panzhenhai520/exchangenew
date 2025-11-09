/**
 * 权限检查工具
 */

/**
 * 检查用户是否拥有指定权限
 * @param {string} permission 权限名称
 * @returns {boolean} 是否拥有权限
 */
export function hasPermission(permission) {
  try {
    console.log(`🔍 权限检查开始: ${permission}`);
    
    const userStr = localStorage.getItem('user');
    if (!userStr) {
      console.log('❌ 用户信息不存在');
      return false;
    }
    
    const user = JSON.parse(userStr);
    console.log('👤 当前用户:', user);
    
    // admin用户拥有所有权限
    if (user.login_code === 'admin' || user.username === 'admin' || user.name === 'admin') {
      console.log('✅ admin用户，允许所有权限');
      return true;
    }
    
    // 检查用户权限 - 使用正确的localStorage键名
    const userPermissions = JSON.parse(localStorage.getItem('userPermissions') || '[]');
    console.log('🔑 用户权限列表:', userPermissions);
    
    // 支持多种权限格式
    const hasPerm = userPermissions.some(p => 
      p === permission || 
      p.name === permission || 
      p.permission_name === permission
    );
    
    console.log(`📊 权限检查结果: ${permission} -> ${hasPerm}`);
    return hasPerm;
  } catch (e) {
    console.error('权限检查出错:', e);
    return false;
  }
}

/**
 * 检查用户是否拥有任意一个权限
 * @param {string[]} permissions 权限名称数组
 * @returns {boolean} 是否拥有任意一个权限
 */
export function hasAnyPermission(permissions) {
  return permissions.some(permission => hasPermission(permission));
}

/**
 * 检查用户是否拥有所有权限
 * @param {string[]} permissions 权限名称数组
 * @returns {boolean} 是否拥有所有权限
 */
export function hasAllPermissions(permissions) {
  return permissions.every(permission => hasPermission(permission));
}

/**
 * 获取用户所有权限
 * @returns {string[]} 权限列表
 */
export function getUserPermissions() {
  try {
    const userPermissions = JSON.parse(localStorage.getItem('userPermissions') || '[]');
    return userPermissions.map(p => p.name || p.permission_name || p);
  } catch (e) {
    console.error('获取用户权限出错:', e);
    return [];
  }
}

/**
 * 权限错误处理
 * @param {string} action 操作名称
 * @returns {string} 统一的错误消息
 */
export function getPermissionErrorMessage(action = '执行此操作') {
  return `抱歉，您没有权限${action}。如需帮助，请联系系统管理员。`;
}

/**
 * 权限定义映射
 */
export const PERMISSIONS = {
  // 系统管理
  SYSTEM_MANAGE: 'system_manage',
  USER_MANAGE: 'user_manage',
  ROLE_MANAGE: 'role_manage',
  BRANCH_MANAGE: 'branch_manage',
  CURRENCY_MANAGE: 'currency_manage',
  
  // 业务操作
  EXCHANGE_OPERATE: 'exchange_operate',
  RATE_MANAGE: 'rate_manage',
  BALANCE_MANAGE: 'balance_manage',
  END_OF_DAY: 'end_of_day',
  TRANSACTION_EXECUTE: 'transaction_execute',
  REVERSE_TRANSACTION: 'reverse_transaction',
  
  // 查询权限
  VIEW_TRANSACTIONS: 'view_transactions',
  VIEW_BALANCES: 'view_balances',
  LOG_VIEW: 'log_view',
  REPORT_VIEW: 'report_view',
  EXPORT_DATA: 'export_data'
}; 
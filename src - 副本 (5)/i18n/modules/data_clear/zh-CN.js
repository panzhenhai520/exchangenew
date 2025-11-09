export default {
  data_clear: {
    title: '清空数据',
    subtitle: '危险操作区域 - 需要系统管理权限',
    permission_denied: '权限不足：您没有系统管理权限，无法执行此操作。',
    clear_success: '清空成功！营业数据已成功清空，您可以重新进行期初设置。',
    clear_time: '清空时间',
    current_branch: '当前网点',
    branch_status: '网点状态',
    clear_reason: '清空原因',
    security_password: '安全密码',
    final_confirm: '我确认理解此操作的风险，并同意清空所有营业数据',
    confirm_clear: '确认清空',
    important_notes: '重要说明',
    danger_warning: '⚠️ 危险操作警告',
    danger_description: '此操作将永久删除以下数据：',
    data_to_clear: [
      '所有交易记录',
      '所有余额调节记录',
      '所有日结历史数据',
      '所有相关的业务数据'
    ],
    operation_irreversible: '此操作不可逆转，请慎重考虑！',
    usage_scenarios: '使用场景',
    scenarios: [
      '系统初始化',
      '测试数据清理',
      '重大错误修复',
      '网点重新开业'
    ],
    operation_consequences: '操作后果',
    consequences: [
      '网点状态重置为期初状态',
      '可以重新进行期初设置',
      '所有业务数据归零',
      '操作记录保留在系统日志中'
    ],
    warning_message: '您即将清空当前网点 {branch} 的所有营业数据！',
    clear_history: '清空历史记录',
    form: {
      reason_required: '请输入清空原因（至少10个字符）',
      reason_placeholder: '请详细说明清空营业数据的原因（至少10个字符）',
      password_required: '请输入安全密码',
      password_placeholder: '请输入安全密码',
      password_help: '请输入正确的安全密码以继续操作',
      confirm_required: '请确认清空操作',
      reason_too_short: '原因说明至少需要10个字符'
    },
    messages: {
      clear_success: '当前网点营业数据清空成功！',
      clear_failed: '清空营业数据失败',
      invalid_password: '安全密码不正确',
      reason_too_short: '原因说明至少需要10个字符'
    },
    data_clear_operation: '数据清空操作',
    current_branch_info: '当前网点信息',
    clear_status: '清空状态',
    can_clear: '可清空',
    cannot_clear: '不可清空',
    data_stats: '数据统计',
    transactions: '交易记录',
    adjustments: '余额调节',
    eod_reports: '日结记录',
    blocking_reason: '无法清空原因',
    clearing: '正在清空...',
    clear_current_branch: '清空当前网点营业数据',
    clear_test_users_roles: '清理测试用户和角色',
    clear_test_users_roles_desc: '删除所有除了admin之外的用户，除了系统管理员、分行管理员、窗口操作员之外的角色',
    clear_test_users_roles_warning: '此操作将删除测试用户和角色，请确认',
    clear_test_users_roles_confirm: '我确认删除测试用户和角色',
    clear_test_users_roles_success: '测试用户和角色清理成功',
    clear_test_users_roles_failed: '清理测试用户和角色失败',
    clear_test_users_roles_stats: '清理统计',
    deleted_users: '删除用户',
    deleted_roles: '删除角色',
    clear_both: '清空营业数据 + 清理测试用户和角色',
    clear_options: '清理选项'
  }
} 
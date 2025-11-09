export default {
  data_clear: {
    title: 'Clear Data',
    subtitle: 'Danger Zone - System Management Permission Required',
    permission_denied: 'Permission Denied: You do not have system management permission to perform this operation.',
    clear_success: 'Clear Successful! Business data has been successfully cleared. You can now perform initial setup again.',
    clear_time: 'Clear Time',
    current_branch: 'Current Branch',
    branch_status: 'Branch Status',
    clear_reason: 'Clear Reason',
    security_password: 'Security Password',
    final_confirm: 'I confirm that I understand the risks of this operation and agree to clear all business data',
    confirm_clear: 'Confirm Clear',
    important_notes: 'Important Notes',
    danger_warning: '⚠️ Dangerous Operation Warning',
    danger_description: 'This operation will permanently delete the following data:',
    data_to_clear: [
      'All transaction records',
      'All balance adjustment records',
      'All end-of-day history data',
      'All related business data'
    ],
    operation_irreversible: 'This operation is irreversible. Please consider carefully!',
    usage_scenarios: 'Usage Scenarios',
    scenarios: [
      'System initialization',
      'Test data cleanup',
      'Major error fixes',
      'Branch reopening'
    ],
    operation_consequences: 'Operation Consequences',
    consequences: [
      'Branch status reset to initial state',
      'Can perform initial setup again',
      'All business data reset to zero',
      'Operation records retained in system logs'
    ],
    warning_message: 'You are about to clear all business data for the current branch {branch}!',
    clear_history: 'Clear History',
    form: {
      reason_required: 'Please enter clear reason (at least 10 characters)',
      reason_placeholder: 'Please explain in detail the reason for clearing business data (at least 10 characters)',
      password_required: 'Please enter security password',
      password_placeholder: 'Please enter security password',
      password_help: 'Please enter the correct security password to continue',
      confirm_required: 'Please confirm clear operation',
      reason_too_short: 'Reason must be at least 10 characters'
    },
    messages: {
      clear_success: 'Current branch business data cleared successfully!',
      clear_failed: 'Failed to clear business data',
      invalid_password: 'Security password is incorrect',
      reason_too_short: 'Reason must be at least 10 characters'
    },
    data_clear_operation: 'Data Clear Operation',
    current_branch_info: 'Current Branch Information',
    clear_status: 'Clear Status',
    can_clear: 'Can Clear',
    cannot_clear: 'Cannot Clear',
    data_stats: 'Data Statistics',
    transactions: 'Transactions',
    adjustments: 'Adjustments',
    eod_reports: 'EOD Reports',
    blocking_reason: 'Cannot Clear Reason',
    clearing: 'Clearing...',
    clear_current_branch: 'Clear Current Branch Business Data',
    clear_test_users_roles: 'Clear Test Users and Roles',
    clear_test_users_roles_desc: 'Delete all users except admin, and all roles except System Administrator, Branch Manager, Window Operator',
    clear_test_users_roles_warning: 'This operation will delete test users and roles, please confirm',
    clear_test_users_roles_confirm: 'I confirm deleting test users and roles',
    clear_test_users_roles_success: 'Test users and roles cleared successfully',
    clear_test_users_roles_failed: 'Failed to clear test users and roles',
    clear_test_users_roles_stats: 'Clear Statistics',
    deleted_users: 'Deleted Users',
    deleted_roles: 'Deleted Roles',
    clear_both: 'Clear Business Data + Clear Test Users and Roles',
    clear_options: 'Clear Options'
  }
} 
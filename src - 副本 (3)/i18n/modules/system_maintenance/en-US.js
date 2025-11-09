export default {
  // System Maintenance Page
  system_maintenance: {
    title: 'System Maintenance',
    subtitle: 'Manage system configuration and basic data',
    
    // User Management
    user_management: {
      title: 'User Management',
      subtitle: 'Manage system users, roles and permissions',
      user_list: 'User List',
      add_user: 'Add User',
      edit_user: 'Edit User',
      user_info: 'User Information',
      login_code: 'Login Code',
      name: 'Name',
      role: 'Role',
      role_names: {
        '系统管理员': 'System Administrator',
        '网点管理员': 'Branch Manager',
        '分行管理员': 'Branch Administrator',
        '窗口操作员': 'Window Operator',
        'TEST Role': 'TEST Role',
        'unassigned': 'Unassigned'
      },
      branch: 'Branch',
      status: 'Status',
      password: 'Password',
      id_card_number: 'ID Card Number',
      phone_number: 'Phone Number',
      mobile_number: 'Mobile Number',
      address: 'Address',
      email: 'Email',
      status_options: {
        active: 'Active',
        inactive: 'Inactive',
        locked: 'Locked',
        suspended: 'Suspended'
      },
      actions: {
        edit: 'Edit',
        reset_password: 'Reset Password',
        disable: 'Disable',
        enable: 'Enable',
        delete: 'Delete User',
        view_permissions: 'View Permissions',
        hide_permissions: 'Hide Permissions'
      },
      permission_restrictions: {
        app_role_no_edit: 'App role users cannot be edited',
        app_role_no_reset_password: 'App role users cannot reset password',
        app_role_no_status_change: 'App role users cannot change status',
        app_role_no_delete: 'App role users cannot be deleted'
      },
      form: {
        login_code_required: 'Please enter username',
        name_required: 'Please enter name',
        role_required: 'Please select user role',
        branch_required: 'Please select branch',
        password_required: 'Please set initial password',
        password_min_length: 'Password must be at least 6 characters',
        email_invalid: 'Invalid email format',
        phone_invalid: 'Invalid phone number format',
        mobile_invalid: 'Invalid mobile number format',
        id_card_invalid: 'Invalid ID card number format'
      },
      messages: {
        create_success: 'User created successfully',
        update_success: 'User updated successfully',
        delete_success: 'User deleted successfully',
        reset_password_success: 'Password reset successfully',
        operation_failed: 'Operation failed',
        business_check_failed: 'Failed to check user business'
      },
      no_permissions: 'This user has no permissions',
      personal_info: 'Personal Information',
      no_personal_info: 'No personal information',
      never_login: 'Never logged in',
      no_users_found: 'No users found',
      permissions: 'Permissions',
      account_status: 'Account Status',
      initial_password: 'Initial Password',
      optional: 'Optional',
      current_branch: 'Current Branch',
      can_only_create_for_current_branch: 'You can only create users for the current branch',
      confirm_delete: 'Confirm Delete',
      confirm_delete_message: 'Are you sure you want to delete user {user}? This action cannot be undone.',
      delete_check_title: 'Pre-deletion Check',
      delete_check_description: 'The system will check if this user has exchange business, reversal business, balance adjustment business, or balance initialization business. If there are any business transactions, deletion will not be allowed, and it is recommended to deactivate the user.',
      reset_password: 'Reset Password',
      confirm_reset_password: 'Confirm Reset Password',
      reset_password_for_user: 'You are resetting the password for user {name} ({code}).',
      password_will_be_reset_to: 'Password will be reset to',
      recommend_change_password: 'Recommend user to change password immediately after first login',
      confirm_reset: 'Confirm Reset',
      status_update_success: 'User status updated successfully',
      status_update_failed: 'Status update failed',
      password_reset_success: 'Password for user {name} has been reset to 123456',
      placeholder: {
        login_code: 'Please enter username',
        name: 'Please enter real name',
        select_role: 'Please select role',
        select_branch: 'Please select branch',
        set_initial_password: 'Please set initial password',
        id_card_number: 'Please enter ID card number',
        email: 'Please enter email address',
        phone_number: 'Please enter phone number',
        mobile_number: 'Please enter mobile number',
        address: 'Please enter address'
      },
      validation: {
        fill_username_and_name: 'Please fill in username and name',
        select_role: 'Please select user role',
        select_branch: 'Please select branch',
        branch_info_error: 'Branch information error, please refresh page and try again',
        set_initial_password: 'Please set initial password',
        password_min_length: 'Password must be at least 6 characters'
      }
    },
    
    // Branch Management
    branch_management: {
      title: 'Branch Management',
      subtitle: 'Manage system branches and subsidiaries',
      branch_list: 'Branch List',
      branch_info: 'Branch Information Management',
      current_branch: 'Current Branch',
      add_branch: 'Add Branch',
      edit_branch: 'Edit Branch',
      branch_code: 'Branch Code',
      branch_name: 'Branch Name',
      address: 'Address',
      manager_name: 'Manager',
      phone_number: 'Phone Number',
      base_currency: 'Base Currency',
      is_active: 'Is Active',
      company_full_name: 'Company Full Name',
      company_full_name_placeholder: 'Enter company full name (for receipts)',
      company_full_name_help: 'This name will be displayed on transaction receipts',
      tax_registration_number: 'Tax Registration Number',
      tax_registration_number_placeholder: 'Enter tax registration number',
      tax_registration_number_help: 'This number will be displayed on transaction receipts',
      institution_type: 'Institution Type',
      institution_type_help: 'This type is used for AMLO anti-money laundering reports',
      institution_types: {
        money_changer: 'Money Changer',
        bank: 'Bank',
        financial_institution: 'Financial Institution',
        other: 'Other'
      },
      website: 'Company Website',
      website_placeholder: 'Enter company website',
      website_help: 'e.g., www.example.com',
      license_number: 'License Number',
      license_number_placeholder: 'Enter license number',
      license_number_help: 'Business license or operating license number',
      amlo_institution_code: 'AMLO Institution Code',
      amlo_institution_code_help: 'Three-digit code assigned by the central bank for AMLO forms (first box group)',
      amlo_branch_code: 'AMLO Branch Code',
      amlo_branch_code_help: 'Three-digit branch code used in AMLO forms (second box group)',
      bot_sender_code: 'BOT Data Sender Code',
      bot_sender_code_help: 'Value for BOT template field “รหัสสถาบันผู้ส่งข้อมูล”, typically a 13-digit number',
      bot_branch_area_code: 'BOT Location Code',
      bot_branch_area_code_help: 'Maps to BOT template “เลขที่ หรือรหัสพื้นที่ของสถานประกอบการ”',
      bot_license_number: 'BOT License Number',
      bot_license_number_help: 'Dedicated BOT license value if different from the general license number',
      status: {
        active: 'Active',
        inactive: 'Inactive'
      },
      actions: {
        edit: 'Edit',
        delete: 'Delete',
        view: 'View'
      },
      form: {
        branch_code_required: 'Please enter branch code',
        branch_name_required: 'Please enter branch name',
        address_required: 'Please enter address',
        manager_required: 'Please enter manager name',
        phone_required: 'Please enter phone number',
        base_currency_required: 'Please select base currency'
      },
      messages: {
        save_success: 'Branch saved successfully',
        save_failed: 'Failed to save branch',
        delete_success: 'Branch deleted successfully',
        delete_failed: 'Failed to delete branch',
        code_exists: 'Branch code already exists',
        invalid_code: 'Invalid branch code format'
      }
    },
    
    // Role Management
    role_management: {
      title: 'Role Permission Management',
      subtitle: 'Manage system roles and permission assignments',
      role_list: 'Role List',
      add_role: 'Add Role',
      edit_role: 'Edit Role',
      role_name: 'Role Name',
      description: 'Description',
      permissions: 'Permissions',
      permission_count: 'Permission Count',
      permission_preview: 'Permission Preview',
      protected_role: 'Protected',
      system_admin: 'System Administrator',
      system_admin_description: 'Has all system permissions',
      total_roles: 'Total {count} roles',
      branch_admin: 'Branch Manager',
      branch_admin_description: 'Manage branch business and operators',
      window_operator: 'Window Operator',
      no_description: 'No description',
      actions: {
        edit: 'Edit',
        delete: 'Delete',
        view: 'View',
        create: 'Create'
      },
      form: {
        role_name_required: 'Please enter role name',
        role_name_max_length: 'Role name cannot exceed 50 characters',
        no_permissions_warning: 'No permissions selected. Are you sure you want to create this role?',
        protected_role_name: 'System administrator role name cannot be modified',
        select_all: 'Select All',
        clear_all: 'Clear All',
        selected_count: 'Selected {count} permissions'
      },
      messages: {
        create_success: 'Role created successfully',
        update_success: 'Role updated successfully',
        delete_success: 'Role deleted successfully',
        delete_failed: 'Delete failed',
        protected_role_delete: 'System administrator role is protected and cannot be deleted',
        confirm_delete: 'Are you sure you want to delete role "{name}"?',
        load_data_failed: 'Failed to load data',
        load_roles_failed: 'Failed to load roles',
        load_permissions_failed: 'Failed to load permissions',
        save_role_failed: 'Failed to save role',
        delete_role_failed: 'Failed to delete role',
        network_error: 'Network connection failed. Please check your network connection',
        server_error: 'Server internal error. Please try again later',
        permission_denied: 'You do not have sufficient permissions to perform this operation',
        login_expired: 'Login has expired. Please log in again',
        request_error: 'Request parameter error',
        unknown_error: 'Unknown error'
      }
    },
    
    // Table related
    table: {
      serial_number: 'No.',
      actions: 'Actions',
      loading: 'Loading...',
      no_data: 'No data available',
      cannot_load: 'Cannot load data',
      cannot_get_branch: 'Cannot get current branch information',
      edit_only: 'Edit only',
      has_business_data: 'This branch has business data and cannot be deleted',
      delete_branch: 'Delete branch'
    },
    
    // Form related
    form: {
      required: 'Required',
      select_currency: 'Please select base currency',
      enable_status: 'Enable status',
      cancel: 'Cancel',
      save: 'Save',
      saving: 'Saving...',
      understand: 'Got it'
    },
    
    // Branch code help
    branch_code_help: {
      title: 'Branch Code Instructions',
      existing_codes: 'Existing branch codes:',
      code_rules: 'Code rules:',
      head_office: 'Head office uses HO prefix, e.g.: HO001',
      branch_office: 'Branch offices use city pinyin initials, e.g.:',
      sub_branch: 'Sub-branches add sequence numbers to branch codes, e.g.:',
      examples: {
        beijing: 'Beijing Branch: BJ001',
        shanghai: 'Shanghai Branch: SH001',
        guangzhou: 'Guangzhou Branch: GZ001',
        beijing_sub1: 'Beijing Branch 1st Sub: BJ101',
        beijing_sub2: 'Beijing Branch 2nd Sub: BJ102'
      },
      code_format: 'Suggested format: Region code + 3 digits, e.g.: BJ001'
    },
    
    // Permissions
    permissions: {
      no_branch_manage: 'You do not have permission to access branch management. Requires branch_manage or system_manage permission',
      no_branch_info: 'Cannot get current branch information. Please contact system administrator to check user configuration'
    },
    
    // Operation messages
    messages: {
      branch_update_success: 'Branch updated successfully',
      branch_add_success: 'Branch added successfully',
      branch_delete_success: 'Branch deleted successfully',
      fetch_branches_failed: 'Failed to fetch branch list',
      fetch_currencies_failed: 'Failed to fetch currency list',
      save_failed: 'Save failed',
      delete_failed: 'Delete failed',
      check_branch_data_failed: 'Failed to check branch data',
      cannot_delete_branch: 'Cannot delete this branch. Reasons:',
      confirm_delete: 'Are you sure you want to delete branch "{name}"?\n\nNote: This action cannot be undone. Please proceed with caution!'
    }
  },

  // Data Clear (top-level)
  data_clear: {
    title: 'Clear Business Data',
    subtitle: 'Dangerous Operation Area - System Management Permission Required',
    permission_denied: 'Insufficient permissions: You do not have system management permissions to perform this operation.',
    clear_success: 'Clear successful! Business data has been successfully cleared, you can re-perform initial setup.',
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
      'All end-of-day historical data',
      'All related business data'
    ],
    operation_irreversible: 'This operation is irreversible, please consider carefully!',
    usage_scenarios: 'Usage Scenarios',
    scenarios: [
      'System initialization',
      'Test data cleanup',
      'Major error repair',
      'Branch reopening'
    ],
    operation_consequences: 'Operation Consequences',
    consequences: [
      'Branch status reset to initial state',
      'Can re-perform initial setup',
      'All business data reset to zero',
      'Operation records retained in system logs'
    ],
    warning_message: 'You are about to clear all business data for branch {branch}!',
    clear_history: 'Clear History',
    form: {
      reason_required: 'Please enter clear reason (at least 10 characters)',
      reason_placeholder: 'Please explain in detail the reason for clearing business data (at least 10 characters)',
      password_required: 'Please enter security password',
      password_placeholder: 'Please enter security password',
      password_help: 'Please enter the correct security password to continue',
      confirm_required: 'Please confirm clear operation'
    },
    messages: {
      clear_success: 'Current branch business data cleared successfully!',
      clear_failed: 'Failed to clear business data',
      invalid_password: 'Security password is incorrect',
      reason_too_short: 'Reason description requires at least 10 characters'
    },
    data_clear_operation: 'Data Clear Operation',
    current_branch_info: 'Current Branch Information',
    clear_status: 'Clear Status',
    can_clear: 'Can Clear',
    cannot_clear: 'Cannot Clear',
    blocking_reason: 'Blocking Reason',
    data_stats: 'Data Statistics',
    transactions: 'Transactions',
    adjustments: 'Adjustments',
    eod_reports: 'EOD Reports',
    clearing: 'Clearing...',
    clear_current_branch: 'Clear Current Branch'
  },

  // Currency Maintenance
  currency_maintenance: {
    title: 'Currency Maintenance',
    subtitle: 'Manage system supported currency types',
    currency_list: 'Currency List',
    add_currency: 'Add Currency',
    edit_currency: 'Edit Currency',
    currency_code: 'Currency Code',
    currency_name: 'Currency Name',
    symbol: 'Symbol',
    is_base: 'Is Base Currency',
    is_active: 'Is Active',
    actions: {
      edit: 'Edit',
      delete: 'Delete',
      view: 'View'
    },
    form: {
      currency_code_required: 'Please enter currency code',
      currency_name_required: 'Please enter currency name',
      symbol_required: 'Please enter currency symbol'
    },
    messages: {
      save_success: 'Currency saved successfully',
      save_failed: 'Failed to save currency',
      delete_success: 'Currency deleted successfully',
      delete_failed: 'Failed to delete currency',
      code_exists: 'Currency code already exists'
    }
  }
} 

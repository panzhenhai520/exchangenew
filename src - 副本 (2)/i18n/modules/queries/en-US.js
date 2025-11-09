export default {
  queries: {
    // Log Query
    log_query: {
    title: 'Log Query',
    subtitle: 'Query system operation logs and activity records',
    start_date: 'Start Date',
    end_date: 'End Date',
    log_type: 'Log Type',
    operator: 'Operator',
    enter_operator_name: 'Enter operator name',
    search: 'Search',
    reset: 'Reset',
    log_types: {
      all: 'All',
      system: 'System',
      login: 'Login',
      exchange: 'Exchange',
      rate: 'Rate',
      balance: 'Balance',
      end_of_day: 'End of Day',
      branch_management: 'Branch Management',
      system_manage: 'System Management'
    },
    table: {
      time: 'Time',
      operator: 'Operator',
      action: 'Action',
      details: 'Details',
      ip_address: 'IP Address',
      user_agent: 'User Agent'
    },
    messages: {
      get_logs_failed: 'Failed to get logs',
      no_permission: 'No permission to view logs'
    }
  },

  // System Logs
  system_logs: {
    title: 'System Logs',
    subtitle: 'View system operation logs and error information',
    log_level: 'Log Level',
    log_levels: {
      all: 'All',
      debug: 'Debug',
      info: 'Info',
      warning: 'Warning',
      error: 'Error',
      critical: 'Critical'
    },
    file_size: 'File Size',
    last_modified: 'Last Modified',
    download: 'Download',
    view_content: 'View Content',
    clear_logs: 'Clear Logs',
    retention_days: 'Retention Days',
    max_size_mb: 'Max Size (MB)'
  },

  // Transaction Query
  transaction_query: {
    title: 'Transaction Query',
    subtitle: 'Query foreign exchange transaction records and details',
    transaction_no: 'Transaction No',
    transaction_type: 'Transaction Type',
    currency: 'Currency',
    amount: 'Amount',
    customer_name: 'Customer Name',
    operator: 'Operator',
    date_range: 'Date Range',
    status: 'Status',
    transaction_types: {
      all: 'All',
      buy: 'Buy',
      sell: 'Sell',
      reversal: 'Reversal',
      adjust_balance: 'Balance Adjustment',
      initial_balance: 'Initial Balance'
    },
    status_options: {
      all: 'All',
      completed: 'Completed',
      cancelled: 'Cancelled',
      reversed: 'Reversed'
    },
    table: {
      transaction_no: 'Transaction No',
      date: 'Date',
      time: 'Time',
      type: 'Type',
      currency: 'Currency',
      amount: 'Amount',
      rate: 'Rate',
      customer: 'Customer',
      operator: 'Operator',
      status: 'Status',
      actions: 'Actions'
    },
    actions: {
      view: 'View',
      print: 'Print',
      reverse: 'Reverse'
    }
  },

  // Balance Query
  balance_query: {
    title: 'Balance Query',
    subtitle: 'Query currency balances and changes',
    errors: {
      no_permission_view_other_branch_balance: 'No permission to view other branch balances'
    },
    currency: 'Currency',
    balance_type: 'Balance Type',
    date: 'Date',
    balance_types: {
      all: 'All',
      current: 'Current Balance',
      opening: 'Opening Balance',
      adjusted: 'Adjusted Balance'
    },
    table: {
      currency: 'Currency',
      currency_name: 'Currency Name',
      opening_balance: 'Opening Balance',
      current_balance: 'Current Balance',
      adjusted_balance: 'Adjusted Balance',
      last_update: 'Last Update'
    },
    chart: {
      title: 'Balance Trend Chart',
      opening: 'Opening',
      current: 'Current',
      adjusted: 'Adjusted'
    }
  },

  // Void Query
  void_query: {
    title: 'Void Query',
    subtitle: 'Query transaction void and reversal records',
    original_transaction: 'Original Transaction No',
    void_reason: 'Void Reason',
    void_types: {
      all: 'All',
      reversal: 'Reversal',
      cancellation: 'Cancellation',
      error_correction: 'Error Correction'
    },
    table: {
      void_no: 'Void No',
      original_no: 'Original No',
      void_date: 'Void Date',
      void_type: 'Void Type',
      reason: 'Reason',
      operator: 'Operator',
      original_amount: 'Original Amount',
      void_amount: 'Void Amount'
    }
  },

  // Balance Adjustment Query
  balance_adjust_query: {
    title: 'Balance Adjustment Query',
    subtitle: 'Query balance adjustment records and reasons',
    adjust_type: 'Adjustment Type',
    reason: 'Adjustment Reason',
    adjust_types: {
      all: 'All',
      manual: 'Manual Adjustment',
      system: 'System Adjustment',
      correction: 'Error Correction'
    },
    table: {
      adjust_no: 'Adjustment No',
      date: 'Date',
      currency: 'Currency',
      original_balance: 'Original Balance',
      adjusted_balance: 'Adjusted Balance',
      difference: 'Difference',
      reason: 'Reason',
      operator: 'Operator',
      status: 'Status'
    }
  },

  // Transaction Reversal
  transaction_reversal: {
    title: 'Transaction Reversal',
    subtitle: 'Reverse completed transactions',
    original_transaction: 'Original Transaction No',
    reversal_reason: 'Reversal Reason',
    reversal_amount: 'Reversal Amount',
    confirm_reversal: 'Confirm Reversal',
    reversal_rules: 'Reversal Rules',
    rules: [
      'Only same-day transactions can be reversed',
      'Already reversed transactions cannot be reversed again',
      'Reversal operations cannot be undone',
      'Sufficient reversal reason must be provided'
    ],
    table: {
      transaction_no: 'Transaction No',
      original_date: 'Original Date',
      type: 'Transaction Type',
      currency: 'Currency',
      amount: 'Amount',
      can_reverse: 'Can Reverse',
      actions: 'Actions'
    },
    form: {
      reason_required: 'Please enter reversal reason',
      amount_required: 'Please enter reversal amount',
      confirm_required: 'Please confirm reversal operation'
    },
    messages: {
      reversal_success: 'Transaction reversed successfully',
      reversal_failed: 'Transaction reversal failed',
      invalid_transaction: 'Invalid transaction number',
      already_reversed: 'This transaction has already been reversed',
      not_reversible: 'This transaction cannot be reversed'
    }
  },

  // Initial Balance
  initial_balance: {
    title: 'Initial Balance',
    subtitle: 'Set initial balances for each currency',
    currency_balance_setting: 'Branch Currency Balance Setting',
    select_all_pending: 'Select All Pending Currencies',
    clear_selection: 'Clear Selection',
    set_to_zero: 'Set to Zero',
    selected_count: 'Selected {count} currencies / Total {total} pending currencies',
    operation_instructions: 'Operation Instructions',
    instructions: [
      'Initial balance setting is used to set the initial balance for each currency, usually done when the system is first enabled.',
      'Operation steps:',
      '1. Select currencies: Check the currencies to operate on',
      '2. Enter balance: Enter balance values for selected currencies',
      '3. Execute operation:',
      '   - Click "Save Initial Setting" for formal initialization (irreversible)',
      '   - Click "Batch Set to Zero" for quick clearing (repeatable)',
      '   - Click "Set to Zero" to only set input box values',
      '4. Confirm result: System will display processing results'
    ],
    status_legend: 'Status Legend',
    status: {
      initialized: 'Initialized',
      pending: 'Pending'
    },
    important_notes: 'Important Notes',
    notes: [
      'Each currency can only be initialized once, please ensure balance values are accurate',
      'Already initialized currencies will be automatically skipped',
      'To reset, please use the "Clear Business Data" function'
    ],
    actions: {
      save_initial: 'Save Initial Setting',
      batch_set_zero: 'Batch Set to Zero',
      confirm_set_zero: 'Confirm Set to Zero'
    },
    form: {
      no_currencies_selected: 'No currencies selected for initial setting, or selected currencies have already been initialized',
      confirm_set_zero_message: 'Confirm to set the balance of the following {count} currencies to 0?\n\nCurrencies: {currencies}\n\nNote: This operation will directly save to database but will not mark as initialized status.'
    },
    messages: {
      save_success: 'Initial setting saved successfully',
      set_zero_success: 'Successfully set {count} currencies to zero',
      operation_failed: 'Operation failed',
      no_branch_info: 'Branch information not found',
      no_currencies: 'No currencies to set',
      transaction_success: 'Transaction Successful',
      balance_set_success: 'Initial Balance Setting Successful!',
      currencies_updated: 'Total {count} currency balances updated',
      operation_summary: 'Operation Summary',
      setting_time: 'Setting Time',
      operator: 'Operator',
      currency_count: 'Currency Count',
      updated_currencies: 'Updated Currencies',
      more_currencies: 'And {count} more currencies...',
      close: 'Close',
      print_voucher: 'Print Voucher'
    },
    transaction_records_generated: 'Generated {count} transaction records, can print receipts.',
    table: {
      select: 'Select',
      currency: 'Currency',
      status: 'Status',
      initial_balance: 'Initial Balance',
      last_modified: 'Last Modified',
      base_currency: 'Base Currency',
      initialized: 'Initialized',
      pending: 'Pending',
      cannot_modify: 'Initialized, cannot modify',
      no_modification_record: 'No modification record',
      unknown_operator: 'Unknown'
    },
    buttons: {
      save_initial_setting: 'Save Initial Setting',
      batch_set_to_zero: 'Batch Set to Zero',
      reset: 'Reset',
      please_select_currency: 'Please select the currency to operate on',
      saving: 'Saving initial setting...',
      setting_zero: 'Setting to zero...',
      batch_setting_zero: 'Batch Set to Zero'
    },
    instructions_detail: {
      title: 'Operation Instructions',
      description: 'Initial balance setting is used to set the initial balance for each currency, usually done when the system is first enabled.',
      steps: {
        title: 'Operation steps:',
        step1: 'Select currency: Check the currency to operate on',
        step2: 'Enter balance: Enter balance value for selected currency',
        step3: 'Execute operation:',
        step3_1: 'Click "Save Initial Setting" for formal initialization (irreversible)',
        step3_2: 'Click "Batch Set to Zero" for quick clearing (repeatable)',
        step3_3: 'Click "Set to Zero" to only set input box value',
        step4: 'Confirm result: System will display processing result'
      }
    },
    status_description: {
      title: 'Status Description:',
      initialized_desc: 'This currency has completed initial setting, cannot be set again',
      pending_desc: 'This currency has not been initialized, can be set'
    },
    important_reminder: {
      title: 'Important Reminder:',
      note1: 'Each currency can only be initialized once, please ensure balance value is accurate',
      note2: 'Initialized currencies will be automatically skipped',
      note3: 'To reset, please use',
      clear_business_data: 'Clear Business Data function'
    },
    set_zero_function: {
      title: 'Set to Zero Function Description:',
      set_to_zero_desc: 'Only set to 0 in input box, not saved to database',
      batch_set_to_zero_desc: 'Directly saved to database, but not marked as initialized',
      note1: 'After setting to 0, you can repeatedly modify and adjust balance',
      note2: 'Applicable for quick clearing or preparing for initial balance settings'
    }
  },

  // Common Query Functions
  common: {
    search: 'Search',
    reset: 'Reset',
    export: 'Export',
    print: 'Print',
    view: 'View',
    edit: 'Edit',
    delete: 'Delete',
    confirm: 'Confirm',
    cancel: 'Cancel',
    save: 'Save',
    loading: 'Loading...',
    no_data: 'No Data',
    total: 'Total',
    page: 'Page',
    of: 'of',
    items_per_page: 'Items per page',
    previous: 'Previous',
    next: 'Next',
    first: 'First',
    last: 'Last',
    date_format: 'YYYY-MM-DD',
    time_format: 'HH:mm:ss',
    datetime_format: 'YYYY-MM-DD HH:mm:ss',
    all: 'All',
    actions: 'Actions'
  }
  }
} 
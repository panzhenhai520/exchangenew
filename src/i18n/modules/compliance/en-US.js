export default {
  compliance: {
    // Field Management
    fieldManagement: 'Field Management',
    fieldManagementDesc: 'Manage custom field definitions for AMLO and BOT reports',

    // Trigger Rule Configuration
    triggerRuleConfig: 'Trigger Rule Configuration',
    triggerRuleConfigDesc: 'Unified management of automatic trigger rules for AMLO and BOT compliance reports',

    // Report Types
    reportType: 'Report Type',
    selectReportType: 'Select Report Type',
    amloReports: 'AMLO Reports',
    botReports: 'BOT Reports',

    // Rules
    ruleName: 'Rule Name',
    ruleNameChinese: 'Rule Name (Chinese)',
    ruleNameEnglish: 'Rule Name (English)',
    ruleNameThai: 'Rule Name (Thai)',
    ruleNamePlaceholder: 'Enter rule name',
    ruleNameRequired: 'Please enter rule name',
    reportTypeRequired: 'Please select report type',
    priority: 'Priority',
    priorityRequired: 'Please enter priority',
    priorityHelp: 'Higher number means higher priority',
    allowContinue: 'Allow Continue',
    allowContinueYes: 'Allow transaction to continue',
    allowContinueNo: 'Block transaction, require reservation',
    description: 'Description',
    descriptionPlaceholder: 'Enter rule description',
    warningMessage: 'Warning Message',
    warningMessagePlaceholder: 'Enter warning message when triggered',
    ruleExpression: 'Rule Expression',
    ruleExpressionHelp: 'Define trigger conditions, supports multiple conditions (AND logic)',

    // Rule Builder
    selectField: 'Select Field',
    logicOperator: 'Logic Operator',
    direction: 'Direction',
    directionHelp: 'Buy = branch buys foreign currency, Sell = branch sells foreign currency',
    amount: 'Amount',
    useFCD: 'Use FCD',
    currencyCode: 'Currency Code',
    currencyCodeHelp: 'Three-letter currency code',
    paymentMethod: 'Payment Method',
    customerCountry: 'Customer Country',
    customerIdHelp: 'Used to look up historical transactions',
    value: 'Value',
    addCondition: 'Add Condition',
    jsonPreview: 'JSON Preview',
    pleaseAddCondition: 'Please add at least one condition',

    // Field Groups
    commonFields: 'Common Fields',
    amountFields: 'Amount Fields',
    specialFields: 'Special Fields',
    fieldGroupLabels: 'Field Group Labels',
    groupChinese: 'Chinese Group Name',
    groupEnglish: 'English Group Name',
    groupThai: 'Thai Group Name',

    // Amount Fields
    verificationAmount: 'Verification Amount',
    verificationAmountHelp: 'Local currency amount used for AMLO evaluation',
    usdEquivalent: 'USD Equivalent',
    usdEquivalentHelp: 'USD equivalent amount used for BOT evaluation',
    foreignAmount: 'Foreign Currency Amount',
    localAmount: 'Local Currency Amount',

    // Placeholders
    enterAmount: 'Please enter amount',
    enterCurrencyCode: 'Enter currency code (e.g. USD)',
    enterCountryCode: 'Enter country code (e.g. TH)',
    enterValue: 'Enter value',
    enterAge: 'Enter age',
    pleaseFillRequired: 'Please fill required fields',
    pleaseSelect: 'Please select',

    // Actions
    createRule: 'Create Rule',
    editRule: 'Edit Rule',
    confirmDeleteRule: 'Are you sure to disable/enable this rule?',
    confirmToggleStatus: 'Are you sure you want to toggle this status?',
    createField: 'Create Field',
    editField: 'Edit Field',

    // Status
    selectStatus: 'Select Status',
    status: 'Status',
    allStatus: 'All Statuses',
    activeRule: 'Active Rule',

    // Messages
    loadRulesFailed: 'Failed to load rules',
    loadFieldsFailed: 'Failed to load fields',
    noRulesFound: 'No rules found',
    noFieldsFound: 'No fields found',
    createSuccess: 'Created successfully',
    updateSuccess: 'Updated successfully',
    operationFailed: 'Operation failed',

    // Field Management Specific
    fieldName: 'Field Name',
    fieldNamePlaceholder: 'English field name, e.g. customer_name',
    fieldNameHelp: 'Only English letters, numbers and underscores allowed, cannot be modified',
    fieldNameRequired: 'Please enter field name',
    fieldLabel: 'Field Label',
    fieldLabelRequired: 'Please enter field label',
    fieldType: 'Field Type',
    fieldTypeRequired: 'Please select field type',
    selectFieldType: 'Select field type',
    fieldGroup: 'Field Group',
    fieldGroupPlaceholder: 'e.g. Transaction Info, Transaction Facts, etc.',
    fillOrder: 'Display Order',
    fillOrderRequired: 'Please enter display order',
    fillOrderHelp: 'Smaller number appears first',
    fillPos: 'PDF Fill Position',
    fillPosPlaceholder: 'e.g. fill_42 or Check Box5',
    fillPosHelp: 'Match the interactive PDF field name to automatically populate the template',
    isRequired: 'Is Required',

    // Multilingual Labels
    basicInfo: 'Basic Info',
    multilingualLabels: 'Multilingual Labels',
    labelChinese: 'Chinese Label',
    labelEnglish: 'English Label',
    labelThai: 'Thai Label',

    // Hint Texts
    hintTexts: 'Hint Texts',
    placeholders: 'Placeholders',
    placeholderHelp: 'Hint text displayed inside the input before typing',
    placeholderChinese: 'Chinese Placeholder',
    placeholderEnglish: 'English Placeholder',
    placeholderThai: 'Thai Placeholder',
    helpTexts: 'Help Texts',
    helpTextChinese: 'Chinese Help Text',
    helpTextEnglish: 'English Help Text',
    helpTextThai: 'Thai Help Text',

    // Validation Rules
    validationRules: 'Validation Rules',
    validationRulesHelp: 'Configure validation rules based on field type',
    validationRule: 'Validation Rule',
    minLength: 'Min Length',
    maxLength: 'Max Length',
    minValue: 'Min Value',
    maxValue: 'Max Value',
    pattern: 'Regular Expression',
    patternHelp: 'e.g. ^[A-Za-z0-9]+$ allows only letters and numbers',
    enumOptions: 'Enum Options',
    option: 'Option',
    addOption: 'Add Option',

    // Filters & Lists
    allReportTypes: 'All Report Types',

    // Test Trigger
    testTriggerHelp: 'How the trigger testing works',
    testTriggerDesc: 'Simulate transaction data, verify trigger rules, preview dynamic forms, and generate a test PDF',
    testConfiguration: 'Test Configuration',
    autoDetect: 'Auto detect',
    selectTriggerRule: 'Select Trigger Rule',
    testDataInput: 'Test Data Input',
    testTriggerCheck: 'Trigger Check',
    testResult: 'Test Result',
    triggerSuccess: 'Trigger succeeded',
    triggerNotMet: 'Trigger not met',
    triggerNotMetDesc: 'Current data does not satisfy any trigger conditions',
    triggerRule: 'Trigger Rule',
    previewForm: 'Preview Form',
    generateTestPDF: 'Generate Test PDF',
    dynamicFormPreview: 'Dynamic Form Preview',
    testFailed: 'Test failed',
    loadFormFailed: 'Failed to load form definition',
    pdfGenerateSuccess: 'PDF generated successfully',
    pdfPath: 'PDF Path',
    pdfGenerateFailed: 'Failed to generate PDF',
    testFormSubmitSuccess: 'Test form submitted successfully',

    // Customer Age
    customerAge: 'Customer Age',
    customerAgeHelp: 'Used for age-related trigger rules',

    // Funding Source
    fundingSource: 'Funding Source',
    propertyMortgage: 'Property mortgage',
    landSale: 'Land sale',
    salary: 'Salary income',
    businessIncome: 'Business income',
    other: 'Other',

    // Report Type Descriptions
    ctrDesc: 'Cash Transaction Report',
    atrDesc: 'Asset Transaction Report',
    strDesc: 'Suspicious Transaction Report',
    botBuyDesc: 'BOT Foreign Currency Purchase Report',
    botSellDesc: 'BOT Foreign Currency Sale Report',
    botFcdDesc: 'BOT FCD Account Report',
    botProviderDesc: 'BOT Provider Report',
    botReportGenerated: 'BOT report generated: {type}',
    botTriggered: 'BOT report trigger conditions satisfied',

    // CTR/ATR/STR labels
    ctr: 'Cash Transaction Report (CTR)',
    atr: 'Asset Transaction Report (ATR)',
    str: 'Suspicious Transaction Report (STR)',

    // Reservation related
    reservationRequired: 'Please fill in necessary information',
    triggerAlertTitle: 'Trigger Alert',
    transactionSummary: 'Transaction Summary',
    foreignCurrency: 'Foreign Currency',
    exchangeRate: 'Exchange Rate',
    customerId: 'Customer ID',
    customerName: 'Customer Name',
    fillRequiredInfo: 'Please fill in necessary information',
    loadingForm: 'Loading form...',
    generatingReportNumber: 'Generating report number...',
    submitting: 'Submitting...',
    submitReservation: 'Submit Reservation',
    saveFailed: 'Save Failed',

    // Customer History
    customerHistory: 'Customer Transaction History',
    customerStats: 'Customer Statistics',
    transactions: 'Transactions',
    totalTransactions: 'Total Transactions',
    cumulativeAmount: 'Cumulative Amount',
    lastTransactionDate: 'Last Transaction Date',
    transactionHistory: 'Transaction History',
    noTransactionHistory: 'No transaction history',
    date: 'Date',
    currency: 'Currency',
    type: 'Type',
    completed: 'Completed',
    currentRate: 'Current Rate'
  }
}

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
    allowContinue: 'Allow Continue',
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
    amount: 'Amount',
    useFCD: 'Use FCD',
    currencyCode: 'Currency Code',
    paymentMethod: 'Payment Method',
    customerCountry: 'Customer Country',
    value: 'Value',
    addCondition: 'Add Condition',
    jsonPreview: 'JSON Preview',

    // Field Groups
    commonFields: 'Common Fields',
    amountFields: 'Amount Fields',
    specialFields: 'Special Fields',

    // Amount Fields
    verificationAmount: 'Verification Amount',
    usdEquivalent: 'USD Equivalent',
    foreignAmount: 'Foreign Currency Amount',
    localAmount: 'Local Currency Amount',

    // Placeholders
    enterAmount: 'Please enter amount',
    enterCurrencyCode: 'Enter currency code (e.g. USD)',
    enterCountryCode: 'Enter country code (e.g. TH)',
    enterValue: 'Enter value',

    // Actions
    createRule: 'Create Rule',
    editRule: 'Edit Rule',
    confirmDeleteRule: 'Are you sure to disable/enable this rule?',

    // Status
    selectStatus: 'Select Status',
    status: 'Status',

    // Messages
    loadRulesFailed: 'Failed to load rules',
    loadFieldsFailed: 'Failed to load fields',
    createSuccess: 'Created successfully',
    updateSuccess: 'Updated successfully',
    operationFailed: 'Operation failed',

    // Field Management Specific
    createField: 'Create Field',
    editField: 'Edit Field',
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
    pattern: 'Regular Expression',
    patternHelp: 'e.g. ^[A-Za-z0-9]+$ allows only letters and numbers',
    minValue: 'Min Value',
    maxValue: 'Max Value',
    enumOptions: 'Enum Options',
    option: 'Option',
    addOption: 'Add Option',

    // Confirmation Messages
    confirmDisableField: 'Are you sure to disable this field? It will not be displayed in the form',
    confirmEnableField: 'Are you sure to enable this field?',
    
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
    saveFailed: 'Save Failed'
  }
}

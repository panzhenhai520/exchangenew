export default {
  compliance: {
    // 字段管理
    fieldManagement: '字段管理',
    fieldManagementDesc: '管理AMLO和BOT报告的自定义字段定义',

    // 触发规则配置
    triggerRuleConfig: '触发规则配置',
    triggerRuleConfigDesc: '统一管理AMLO和BOT合规报告的自动触发规�?,

    // 报告类型
    reportType: '报告类型',
    selectReportType: '选择报告类型',
    amloReports: 'AMLO报告',
    botReports: 'BOT报告',

    // 规则相关
    ruleName: '规则名称',
    ruleNameChinese: '规则名称（中文）',
    ruleNameEnglish: '规则名称（英文）',
    ruleNameThai: '规则名称（泰文）',
    ruleNamePlaceholder: '请输入规则名�?,
    ruleNameRequired: '请输入规则名�?,
    reportTypeRequired: '请选择报告类型',
    priority: '优先�?,
    priorityRequired: '请输入优先级',
    allowContinue: '允许继续交易',
    description: '规则描述',
    descriptionPlaceholder: '请输入规则描�?,
    warningMessage: '警告消息',
    warningMessagePlaceholder: '请输入触发时的警告消�?,
    ruleExpression: '规则表达�?,
    ruleExpressionHelp: '定义触发条件，支持多个条件组合（AND逻辑�?,

    // 规则构建�?    selectField: '选择字段',
    logicOperator: '逻辑运算�?,
    direction: '交易方向',
    amount: '金额',
    useFCD: '使用FCD',
    currencyCode: '币种代码',
    paymentMethod: '支付方式',
    customerCountry: '客户国籍',
    value: '�?,
    addCondition: '添加条件',
    jsonPreview: 'JSON预览',

    // 字段分组
    commonFields: '通用字段',
    amountFields: '金额字段',
    specialFields: '特殊字段',

    // 金额字段
    verificationAmount: '验证金额',
    usdEquivalent: 'USD等�?,
    foreignAmount: '外币金额',
    localAmount: '本币金额',

    // 占位�?    enterAmount: '请输入金�?,
    enterCurrencyCode: '请输入币种代码（如：USD�?,
    enterCountryCode: '请输入国家代码（如：TH�?,
    enterValue: '请输入�?,

    // 操作
    createRule: '创建规则',
    editRule: '编辑规则',
    confirmDeleteRule: '确定要禁�?启用此规则吗�?,

    // 状�?    selectStatus: '选择状�?,
    status: '状�?,

    // 消息
    loadRulesFailed: '加载规则列表失败',
    loadFieldsFailed: '加载字段列表失败',
    createSuccess: '创建成功',
    updateSuccess: '更新成功',
    operationFailed: '操作失败',

    // 字段管理专用
    createField: '创建字段',
    editField: '编辑字段',
    fieldName: '字段名称',
    fieldNamePlaceholder: '英文字段名，�?customer_name',
    fieldNameHelp: '只能使用英文、数字和下划线，不可修改',
    fieldNameRequired: '请输入字段名�?,
    fieldLabel: '字段标签',
    fieldLabelRequired: '请输入字段标�?,
    fieldType: '字段类型',
    fieldTypeRequired: '请选择字段类型',
    selectFieldType: '选择字段类型',
    fieldGroup: '字段分组',
    fieldGroupPlaceholder: '如：交易人信息、交易事实等',
    fillOrder: '显示顺序',
    fillOrderRequired: '请输入显示顺�?,
    fillOrderHelp: '数字越小越靠�?,
    isRequired: '是否必填',

    // 多语言标签
    basicInfo: '基本信息',
    multilingualLabels: '多语言标签',
    labelChinese: '中文标签',
    labelEnglish: '英文标签',
    labelThai: '泰文标签',

    // 提示文本
    hintTexts: '提示文本',
    placeholders: '输入框占位符',
    placeholderHelp: '用户在输入框中看到的提示文字（输入前显示�?,
    placeholderChinese: '中文占位�?,
    placeholderEnglish: '英文占位�?,
    placeholderThai: '泰文占位�?,
    helpTexts: '帮助文本',
    helpTextChinese: '中文帮助文本',
    helpTextEnglish: '英文帮助文本',
    helpTextThai: '泰文帮助文本',

    // 验证规则
    validationRules: '验证规则',
    validationRulesHelp: '根据字段类型配置相应的验证规�?,
    validationRule: '验证规则',
    minLength: '最小长�?,
    maxLength: '最大长�?,
    pattern: '正则表达�?,
    patternHelp: '如：^[A-Za-z0-9]+$ 只允许字母和数字',
    minValue: '最小�?,
    maxValue: '最大�?,
    enumOptions: '枚举选项',
    option: '选项',
    addOption: '添加选项',

    // 确认消息
    confirmDisableField: '确定要禁用此字段吗？禁用后不会在表单中显�?,
    confirmEnableField: '确定要启用此字段吗？',
    confirmToggleStatus: '确定要切换状态吗�?,

    // 新增翻译�?    allReportTypes: '全部报告类型',
    allStatus: '全部状�?,
    noFieldsFound: '未找到字�?,
    noRulesFound: '未找到规�?,
    activeRule: '启用规则',
    fieldGroupLabels: '字段分组标签',
    groupChinese: '中文分组',
    groupEnglish: '英文分组',
    groupThai: '泰文分组',
    priorityHelp: '数字越大优先级越�?,
    allowContinueYes: '允许继续交易',
    allowContinueNo: '阻止交易，需要预�?,
    pleaseFillRequired: '请填写必填字�?,
    pleaseAddCondition: '请至少添加一个条�?,
    
    // 测试触发
    testTriggerHelp: '测试触发功能说明',
    testTriggerDesc: '在此页面可以模拟交易数据，测试触发规则是否正确，预览动态表单，生成测试PDF',
    testConfiguration: '测试配置',
    pleaseSelect: '请选择',
    autoDetect: '自动检�?,
    selectTriggerRule: '选择触发规则',
    testDataInput: '测试数据输入',
    testTriggerCheck: '测试触发检�?,
    testResult: '测试结果',
    triggerSuccess: '触发成功',
    triggerNotMet: '未触�?,
    triggerNotMetDesc: '当前测试数据不满足任何触发条�?,
    triggerRule: '触发规则',
    previewForm: '预览表单',
    generateTestPDF: '生成测试PDF',
    dynamicFormPreview: '动态表单预�?,
    testFailed: '测试失败',
    loadFormFailed: '加载表单定义失败',
    pdfGenerateSuccess: 'PDF生成成功',
    pdfPath: 'PDF路径',
    pdfGenerateFailed: 'PDF生成失败',
    testFormSubmitSuccess: '测试表单提交成功',
    
    // 客户年龄
    customerAge: '客户年龄',
    enterAge: '请输入年�?,
    customerAgeHelp: '用于年龄相关的触发规�?,
    
    // 资金来源
    fundingSource: '资金来源',
    propertyMortgage: '抵押房产',
    landSale: '变卖土地',
    salary: '工资收入',
    businessIncome: '经营收入',
    other: '其他',
    
    // 方向和汇�?    directionHelp: '买入=网点买入外币，卖�?网点卖出外币',
    currencyCodeHelp: '3位币种代�?,
    verificationAmountHelp: '本币金额，用于AMLO规则判断',
    usdEquivalentHelp: '美元等值金额，用于BOT规则判断',
    customerIdHelp: '用于查询客户历史交易',
    currentRate: '当前汇率',
    
    // 报告类型描述
    ctrDesc: '现金交易报告',
    atrDesc: '资产交易报告',
    strDesc: '可疑交易报告',
    botBuyDesc: '买入外币报告',
    botSellDesc: '卖出外币报告',
    botFcdDesc: 'FCD账户报告',
    botProviderDesc: '供应商报�?,
    
    // CTR/ATR/STR
    ctr: '现金交易报告(CTR)',
    atr: '资产交易报告(ATR)',
    str: '可疑交易报告(STR)',
    
    // 预约相关
    reservationRequired: '需要预约兑�?,
    triggerAlertTitle: '触发合规报告',
    transactionSummary: '交易摘要',
    foreignCurrency: '外币',
    exchangeRate: '汇率',
    customerId: '客户证件�?,
    customerName: '客户姓名',
    fillRequiredInfo: '请填写必要信�?,
    loadingForm: '正在加载表单...',
    generatingReportNumber: '生成报告编号�?..',
    submitting: '提交�?..',
    submitReservation: '提交预约',
    saveFailed: '保存失败',
    
    // 客户历史
    customerHistory: '客户历史交易',
    customerStats: '客户统计',
    transactions: '交易次数',
    total: '累计金额',
    totalTransactions: '总交易次�?,
    cumulativeAmount: '累计金额',
    lastTransactionDate: '最近交易日�?,
    transactionHistory: '交易历史',
    noTransactionHistory: '暂无交易历史',
    date: '日期',
    currency: '币种',
    type: '类型',
    completed: '已完�?,
    
    // BOT报表提示
    botReportGenerated: 'BOT报表已生成：{type}',
    botTriggered: 'BOT报表触发条件已满�?
  }
}

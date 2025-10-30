export default {
  compliance: {
    // 字段管理
    fieldManagement: '字段管理',
    fieldManagementDesc: '管理 AMLO 和 BOT 报告的自定义字段定义',

    // 触发规则配置
    triggerRuleConfig: '触发规则配置',
    triggerRuleConfigDesc: '统一管理 AMLO 与 BOT 合规报告的自动触发规则',

    // 报告类型
    reportType: '报告类型',
    selectReportType: '选择报告类型',
    amloReports: 'AMLO 报告',
    botReports: 'BOT 报告',

    // 规则
    ruleName: '规则名称',
    ruleNameChinese: '规则名称（中文）',
    ruleNameEnglish: '规则名称（英文）',
    ruleNameThai: '规则名称（泰文）',
    ruleNamePlaceholder: '请输入规则名称',
    ruleNameRequired: '请输入规则名称',
    reportTypeRequired: '请选择报告类型',
    priority: '优先级',
    priorityRequired: '请输入优先级',
    priorityHelp: '数字越大优先级越高',
    allowContinue: '允许继续',
    allowContinueYes: '允许继续交易',
    allowContinueNo: '阻止交易，需要预约',
    description: '规则描述',
    descriptionPlaceholder: '请输入规则描述',
    warningMessage: '警告消息',
    warningMessagePlaceholder: '请输入触发时的警告消息',
    ruleExpression: '规则表达式',
    ruleExpressionHelp: '定义触发条件，支持多个条件组合（AND 逻辑）',

    // 规则构建器
    selectField: '选择字段',
    logicOperator: '逻辑运算符',
    direction: '交易方向',
    directionHelp: '买入 = 网点买入外币，卖出 = 网点卖出外币',
    amount: '金额',
    useFCD: '使用 FCD',
    currencyCode: '币种代码',
    currencyCodeHelp: '三位币种代码',
    paymentMethod: '支付方式',
    customerCountry: '客户国籍',
    customerIdHelp: '用于查询客户历史交易',
    value: '数值',
    addCondition: '添加条件',
    jsonPreview: 'JSON 预览',
    pleaseAddCondition: '请至少添加一个条件',

    // 字段分组
    commonFields: '通用字段',
    amountFields: '金额字段',
    specialFields: '特殊字段',
    fieldGroupLabels: '字段分组标签',
    groupChinese: '中文分组名称',
    groupEnglish: '英文分组名称',
    groupThai: '泰文分组名称',

    // 金额字段
    verificationAmount: '验证金额',
    verificationAmountHelp: '本币金额，用于 AMLO 判断',
    usdEquivalent: 'USD 等值',
    usdEquivalentHelp: 'USD 等值金额，用于 BOT 判断',
    foreignAmount: '外币金额',
    localAmount: '本币金额',

    // 占位提示
    enterAmount: '请输入金额',
    enterCurrencyCode: '请输入币种代码（如 USD）',
    enterCountryCode: '请输入国家代码（如 TH）',
    enterValue: '请输入数值',
    enterAge: '请输入年龄',
    pleaseFillRequired: '请填写必填信息',
    pleaseSelect: '请选择',

    // 操作
    createRule: '创建规则',
    editRule: '编辑规则',
    confirmDeleteRule: '确定要禁用/启用该规则吗？',
    confirmToggleStatus: '确定要切换该状态吗？',
    createField: '创建字段',
    editField: '编辑字段',

    // 状态
    selectStatus: '选择状态',
    status: '状态',
    allStatus: '所有状态',
    activeRule: '启用规则',

    // 消息
    loadRulesFailed: '加载规则列表失败',
    loadFieldsFailed: '加载字段列表失败',
    noRulesFound: '未找到规则',
    noFieldsFound: '未找到字段',
    createSuccess: '创建成功',
    updateSuccess: '更新成功',
    operationFailed: '操作失败',

    // 字段管理相关
    fieldName: '字段名称',
    fieldNamePlaceholder: '英文字段名，如 customer_name',
    fieldNameHelp: '只能使用英文、数字和下划线，创建后不可修改',
    fieldNameRequired: '请输入字段名称',
    fieldLabel: '字段标签',
    fieldLabelRequired: '请输入字段标签',
    fieldType: '字段类型',
    fieldTypeRequired: '请选择字段类型',
    selectFieldType: '选择字段类型',
    fieldGroup: '字段分组',
    fieldGroupPlaceholder: '如：交易人信息、交易事实等',
    fillOrder: '显示顺序',
    fillOrderRequired: '请输入显示顺序',
    fillOrderHelp: '数字越小越靠前',
    fillPos: 'PDF 填充位置',
    fillPosPlaceholder: '如 fill_42 或 Check Box5',
    fillPosHelp: '匹配交互式 PDF 的字段名称以自动填充模板',
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
    placeholderHelp: '在输入前显示的提示文字',
    placeholderChinese: '中文占位符',
    placeholderEnglish: '英文占位符',
    placeholderThai: '泰文占位符',
    helpTexts: '帮助文本',
    helpTextChinese: '中文帮助文本',
    helpTextEnglish: '英文帮助文本',
    helpTextThai: '泰文帮助文本',

    // 校验规则
    validationRules: '校验规则',
    validationRulesHelp: '依据字段类型配置校验规则',
    validationRule: '校验规则',
    minLength: '最小长度',
    maxLength: '最大长度',
    minValue: '最小值',
    maxValue: '最大值',
    pattern: '正则表达式',
    patternHelp: '例如 ^[A-Za-z0-9]+$ 仅允许字母和数字',
    enumOptions: '枚举选项',
    option: '选项',
    addOption: '添加选项',

    // 过滤条件与列表
    allReportTypes: '全部报告类型',

    // 测试触发
    testTriggerHelp: '测试触发功能说明',
    testTriggerDesc: '在此模拟交易数据，校验触发规则是否生效，预览动态表单并生成测试 PDF',
    testConfiguration: '测试配置',
    autoDetect: '自动检测',
    selectTriggerRule: '选择触发规则',
    testDataInput: '测试数据输入',
    testTriggerCheck: '触发校验',
    testResult: '测试结果',
    triggerSuccess: '触发成功',
    triggerNotMet: '未满足触发条件',
    triggerNotMetDesc: '当前数据不满足任何触发条件',
    triggerRule: '触发规则',
    previewForm: '预览表单',
    generateTestPDF: '生成测试 PDF',
    dynamicFormPreview: '动态表单预览',
    testFailed: '测试失败',
    loadFormFailed: '加载表单定义失败',
    pdfGenerateSuccess: 'PDF 生成成功',
    pdfPath: 'PDF 路径',
    pdfGenerateFailed: 'PDF 生成失败',
    testFormSubmitSuccess: '测试表单提交成功',

    // 客户年龄
    customerAge: '客户年龄',
    customerAgeHelp: '用于年龄相关的触发规则',

    // 资金来源
    fundingSource: '资金来源',
    propertyMortgage: '房产抵押',
    landSale: '出售土地',
    salary: '工资收入',
    businessIncome: '经营收入',
    other: '其他',

    // 报告类型描述
    ctrDesc: '现金交易报告',
    atrDesc: '资产交易报告',
    strDesc: '可疑交易报告',
    botBuyDesc: 'BOT 外币买入报告',
    botSellDesc: 'BOT 外币卖出报告',
    botFcdDesc: 'BOT FCD 账户报告',
    botProviderDesc: 'BOT 服务提供者报告',
    botReportGenerated: 'BOT 报告已生成：{type}',
    botTriggered: 'BOT 报告触发条件已满足',

    // CTR/ATR/STR 标签
    ctr: '现金交易报告 (CTR)',
    atr: '资产交易报告 (ATR)',
    str: '可疑交易报告 (STR)',

    // 预约及提醒
    reservationRequired: '请填写必要信息',
    triggerAlertTitle: '触发告警',
    transactionSummary: '交易摘要',
    foreignCurrency: '外币',
    exchangeRate: '汇率',
    customerId: '客户编号',
    customerName: '客户姓名',
    fillRequiredInfo: '请填写必要信息',
    loadingForm: '正在加载表单...',
    generatingReportNumber: '正在生成报告编号...',
    submitting: '提交中...',
    submitReservation: '提交预约',
    saveFailed: '保存失败',

    // 客户历史
    customerHistory: '客户历史交易',
    customerStats: '客户统计',
    transactions: '交易次数',
    totalTransactions: '总交易次数',
    cumulativeAmount: '累计金额',
    lastTransactionDate: '最近交易日期',
    transactionHistory: '交易历史',
    noTransactionHistory: '暂无交易历史',
    date: '日期',
    currency: '币种',
    type: '类型',
    completed: '已完成',
    currentRate: '当前汇率'
  }
}

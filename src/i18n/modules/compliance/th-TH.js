export default {
  compliance: {
    // การจัดการฟิลด์
    fieldManagement: 'การจัดการฟิลด์',
    fieldManagementDesc: 'จัดการคำจำกัดความฟิลด์ที่กำหนดเองสำหรับรายงาน AMLO และ BOT',

    // การกำหนดค่ากฎทริกเกอร์
    triggerRuleConfig: 'การกำหนดค่ากฎการทริกเกอร์',
    triggerRuleConfigDesc: 'ศูนย์กลางการจัดการกฎการทริกเกอร์อัตโนมัติสำหรับรายงานการปฏิบัติตาม AMLO และ BOT',

    // ประเภทรายงาน
    reportType: 'ประเภทรายงาน',
    selectReportType: 'เลือกประเภทรายงาน',
    amloReports: 'รายงาน AMLO',
    botReports: 'รายงาน BOT',

    // กฎ
    ruleName: 'ชื่อกฎ',
    ruleNameChinese: 'ชื่อกฎ (ภาษาจีน)',
    ruleNameEnglish: 'ชื่อกฎ (ภาษาอังกฤษ)',
    ruleNameThai: 'ชื่อกฎ (ภาษาไทย)',
    ruleNamePlaceholder: 'กรอกชื่อกฎ',
    ruleNameRequired: 'กรุณากรอกชื่อกฎ',
    reportTypeRequired: 'กรุณาเลือกประเภทรายงาน',
    priority: 'ลำดับความสำคัญ',
    priorityRequired: 'กรุณากรอกลำดับความสำคัญ',
    priorityHelp: 'ตัวเลขมากหมายถึงลำดับความสำคัญสูงกว่า',
    allowContinue: 'อนุญาตให้ทำต่อ',
    allowContinueYes: 'อนุญาตให้ทำธุรกรรมต่อ',
    allowContinueNo: 'หยุดธุรกรรม ต้องทำการจอง',
    description: 'คำอธิบาย',
    descriptionPlaceholder: 'กรอกคำอธิบายของกฎ',
    warningMessage: 'ข้อความเตือน',
    warningMessagePlaceholder: 'กรอกข้อความเตือนเมื่อกฎถูกทริกเกอร์',
    ruleExpression: 'นิพจน์กฎ',
    ruleExpressionHelp: 'กำหนดเงื่อนไขการทริกเกอร์ รองรับหลายเงื่อนไข (ตรรกะ AND)',

    // ตัวสร้างกฎ
    selectField: 'เลือกฟิลด์',
    logicOperator: 'ตัวดำเนินการเชิงตรรกะ',
    direction: 'ทิศทางการทำรายการ',
    directionHelp: 'ซื้อ = สาขาซื้อเงินตราต่างประเทศ, ขาย = สาขาขายเงินตราต่างประเทศ',
    amount: 'จำนวนเงิน',
    useFCD: 'ใช้ FCD',
    currencyCode: 'รหัสสกุลเงิน',
    currencyCodeHelp: 'รหัสสกุลเงิน 3 ตัวอักษร',
    paymentMethod: 'วิธีการชำระเงิน',
    customerCountry: 'สัญชาติของลูกค้า',
    customerIdHelp: 'ใช้สำหรับค้นประวัติการทำธุรกรรมของลูกค้า',
    value: 'ค่า',
    addCondition: 'เพิ่มเงื่อนไข',
    jsonPreview: 'ดูตัวอย่าง JSON',
    pleaseAddCondition: 'กรุณาเพิ่มอย่างน้อยหนึ่งเงื่อนไข',

    // กลุ่มฟิลด์
    commonFields: 'ฟิลด์ทั่วไป',
    amountFields: 'ฟิลด์จำนวนเงิน',
    specialFields: 'ฟิลด์พิเศษ',
    fieldGroupLabels: 'ป้ายชื่อกลุ่มฟิลด์',
    groupChinese: 'ชื่อกลุ่มภาษาจีน',
    groupEnglish: 'ชื่อกลุ่มภาษาอังกฤษ',
    groupThai: 'ชื่อกลุ่มภาษาไทย',

    // ฟิลด์จำนวนเงิน
    verificationAmount: 'จำนวนเงินตรวจสอบ',
    verificationAmountHelp: 'จำนวนเงินสกุลท้องถิ่น ใช้สำหรับประเมินกฎ AMLO',
    usdEquivalent: 'มูลค่าเทียบเท่า USD',
    usdEquivalentHelp: 'มูลค่าเทียบเท่า USD ใช้สำหรับประเมินกฎ BOT',
    foreignAmount: 'จำนวนเงินตราต่างประเทศ',
    localAmount: 'จำนวนเงินสกุลท้องถิ่น',

    // ตัวยึดตำแหน่ง
    enterAmount: 'กรอกจำนวนเงิน',
    enterCurrencyCode: 'กรอกรหัสสกุลเงิน (เช่น USD)',
    enterCountryCode: 'กรอกรหัสประเทศ (เช่น TH)',
    enterValue: 'กรอกค่า',
    enterAge: 'กรอกอายุ',
    pleaseFillRequired: 'กรุณากรอกข้อมูลที่จำเป็น',
    pleaseSelect: 'โปรดเลือก',

    // การดำเนินการ
    createRule: 'สร้างกฎ',
    editRule: 'แก้ไขกฎ',
    confirmDeleteRule: 'ยืนยันการเปิด/ปิดใช้งานกฎนี้หรือไม่?',
    confirmToggleStatus: 'ยืนยันการสลับสถานะนี้หรือไม่?',
    createField: 'สร้างฟิลด์',
    editField: 'แก้ไขฟิลด์',

    // สถานะ
    selectStatus: 'เลือกสถานะ',
    status: 'สถานะ',
    allStatus: 'ทุกสถานะ',
    activeRule: 'กฎที่ใช้งานอยู่',

    // ข้อความแจ้ง
    loadRulesFailed: 'โหลดรายการกฎไม่สำเร็จ',
    loadFieldsFailed: 'โหลดรายการฟิลด์ไม่สำเร็จ',
    noRulesFound: 'ไม่พบกฎ',
    noFieldsFound: 'ไม่พบฟิลด์',
    createSuccess: 'สร้างสำเร็จ',
    updateSuccess: 'อัปเดตสำเร็จ',
    operationFailed: 'ดำเนินการไม่สำเร็จ',

    // รายละเอียดการจัดการฟิลด์
    fieldName: 'ชื่อฟิลด์',
    fieldNamePlaceholder: 'ชื่อฟิลด์ภาษาอังกฤษ เช่น customer_name',
    fieldNameHelp: 'ใช้ได้เฉพาะอักษรภาษาอังกฤษ ตัวเลข และขีดล่าง ไม่สามารถแก้ไขได้',
    fieldNameRequired: 'กรุณากรอกชื่อฟิลด์',
    fieldLabel: 'ป้ายกำกับฟิลด์',
    fieldLabelRequired: 'กรุณากรอกป้ายกำกับฟิลด์',
    fieldType: 'ประเภทฟิลด์',
    fieldTypeRequired: 'กรุณาเลือกประเภทฟิลด์',
    selectFieldType: 'เลือกประเภทฟิลด์',
    fieldGroup: 'กลุ่มฟิลด์',
    fieldGroupPlaceholder: 'เช่น ข้อมูลธุรกรรม ข้อเท็จจริงธุรกรรม ฯลฯ',
    fillOrder: 'ลำดับการแสดงผล',
    fillOrderRequired: 'กรุณากรอกลำดับการแสดงผล',
    fillOrderHelp: 'ตัวเลขน้อยกว่าจะถูกแสดงก่อน',
    fillPos: 'ตำแหน่งเติมใน PDF',
    fillPosPlaceholder: 'เช่น fill_42 หรือ Check Box5',
    fillPosHelp: 'จับคู่ชื่อฟิลด์ใน PDF แบบโต้ตอบเพื่อกรอกอัตโนมัติ',
    isRequired: 'จำเป็นต้องกรอก',

    // ป้ายกำกับหลายภาษา
    basicInfo: 'ข้อมูลพื้นฐาน',
    multilingualLabels: 'ป้ายกำกับหลายภาษา',
    labelChinese: 'ป้ายกำกับภาษาจีน',
    labelEnglish: 'ป้ายกำกับภาษาอังกฤษ',
    labelThai: 'ป้ายกำกับภาษาไทย',

    // ข้อความคำแนะนำ
    hintTexts: 'ข้อความแนะนำ',
    placeholders: 'ข้อความในช่องกรอก',
    placeholderHelp: 'ข้อความแนะนำที่แสดงในช่องก่อนพิมพ์',
    placeholderChinese: 'ตัวยึดตำแหน่งภาษาจีน',
    placeholderEnglish: 'ตัวยึดตำแหน่งภาษาอังกฤษ',
    placeholderThai: 'ตัวยึดตำแหน่งภาษาไทย',
    helpTexts: 'ข้อความช่วยเหลือ',
    helpTextChinese: 'ข้อความช่วยเหลือภาษาจีน',
    helpTextEnglish: 'ข้อความช่วยเหลือภาษาอังกฤษ',
    helpTextThai: 'ข้อความช่วยเหลือภาษาไทย',

    // กฎการตรวจสอบ
    validationRules: 'กฎการตรวจสอบ',
    validationRulesHelp: 'กำหนดกฎการตรวจสอบตามประเภทฟิลด์',
    validationRule: 'กฎการตรวจสอบ',
    minLength: 'ความยาวขั้นต่ำ',
    maxLength: 'ความยาวสูงสุด',
    minValue: 'ค่าต่ำสุด',
    maxValue: 'ค่าสูงสุด',
    pattern: 'นิพจน์ทั่วไป',
    patternHelp: 'เช่น ^[A-Za-z0-9]+$ อนุญาตเฉพาะตัวอักษรและตัวเลข',
    enumOptions: 'ตัวเลือกแบบแจงนับ',
    option: 'ตัวเลือก',
    addOption: 'เพิ่มตัวเลือก',

    // ตัวกรองและรายการ
    allReportTypes: 'ทุกรายงาน',

    // การทดสอบกฎทริกเกอร์
    testTriggerHelp: 'คำอธิบายการทดสอบการทริกเกอร์',
    testTriggerDesc: 'จำลองข้อมูลการทำรายการ ทดสอบความถูกต้องของกฎ ดูตัวอย่างฟอร์มแบบไดนามิก และสร้าง PDF ทดสอบ',
    testConfiguration: 'การตั้งค่าการทดสอบ',
    autoDetect: 'ตรวจจับอัตโนมัติ',
    selectTriggerRule: 'เลือกกฎทริกเกอร์',
    testDataInput: 'ข้อมูลสำหรับทดสอบ',
    testTriggerCheck: 'ตรวจสอบการทริกเกอร์',
    testResult: 'ผลการทดสอบ',
    triggerSuccess: 'ทริกเกอร์สำเร็จ',
    triggerNotMet: 'ไม่เข้าเงื่อนไขทริกเกอร์',
    triggerNotMetDesc: 'ข้อมูลปัจจุบันไม่ตรงตามเงื่อนไขทริกเกอร์ใด ๆ',
    triggerRule: 'กฎทริกเกอร์',
    previewForm: 'ดูตัวอย่างฟอร์ม',
    generateTestPDF: 'สร้าง PDF ทดสอบ',
    dynamicFormPreview: 'ดูตัวอย่างฟอร์มแบบไดนามิก',
    testFailed: 'การทดสอบล้มเหลว',
    loadFormFailed: 'โหลดแบบฟอร์มไม่สำเร็จ',
    pdfGenerateSuccess: 'สร้าง PDF สำเร็จ',
    pdfPath: 'เส้นทางไฟล์ PDF',
    pdfGenerateFailed: 'สร้าง PDF ไม่สำเร็จ',
    testFormSubmitSuccess: 'ส่งแบบฟอร์มทดสอบสำเร็จ',

    // อายุของลูกค้า
    customerAge: 'อายุลูกค้า',
    customerAgeHelp: 'ใช้สำหรับกฎที่เกี่ยวข้องกับอายุ',

    // แหล่งที่มาของเงิน
    fundingSource: 'แหล่งที่มาของเงิน',
    propertyMortgage: 'จำนองทรัพย์สิน',
    landSale: 'ขายที่ดิน',
    salary: 'รายได้จากเงินเดือน',
    businessIncome: 'รายได้จากธุรกิจ',
    other: 'อื่น ๆ',

    // รายละเอียดประเภทของรายงาน
    ctrDesc: 'รายงานธุรกรรมเงินสด',
    atrDesc: 'รายงานธุรกรรมสินทรัพย์',
    strDesc: 'รายงานธุรกรรมที่น่าสงสัย',
    botBuyDesc: 'รายงาน BOT ซื้อเงินตราต่างประเทศ',
    botSellDesc: 'รายงาน BOT ขายเงินตราต่างประเทศ',
    botFcdDesc: 'รายงานบัญชี FCD ของ BOT',
    botProviderDesc: 'รายงานผู้ให้บริการ BOT',
    botReportGenerated: 'สร้างรายงาน BOT เรียบร้อย: {type}',
    botTriggered: 'เงื่อนไขรายงาน BOT ครบถ้วนแล้ว',

    // ป้ายกำกับ CTR/ATR/STR
    ctr: 'รายงานธุรกรรมเงินสด (CTR)',
    atr: 'รายงานธุรกรรมสินทรัพย์ (ATR)',
    str: 'รายงานธุรกรรมที่น่าสงสัย (STR)',

    // การจองและแจ้งเตือน
    reservationRequired: 'กรุณากรอกข้อมูลที่จำเป็น',
    triggerAlertTitle: 'แจ้งเตือนการทริกเกอร์',
    transactionSummary: 'สรุปการทำรายการ',
    foreignCurrency: 'สกุลเงินต่างประเทศ',
    exchangeRate: 'อัตราแลกเปลี่ยน',
    customerId: 'รหัสลูกค้า',
    customerName: 'ชื่อลูกค้า',
    fillRequiredInfo: 'กรุณากรอกข้อมูลที่จำเป็น',
    loadingForm: 'กำลังโหลดแบบฟอร์ม...',
    generatingReportNumber: 'กำลังสร้างหมายเลขรายงาน...',
    submitting: 'กำลังส่ง...',
    submitReservation: 'ส่งการจอง',
    saveFailed: 'บันทึกไม่สำเร็จ',

    // ประวัติการทำรายการของลูกค้า
    customerHistory: 'ประวัติการทำธุรกรรมของลูกค้า',
    customerStats: 'สถิติลูกค้า',
    transactions: 'จำนวนธุรกรรม',
    totalTransactions: 'ธุรกรรมทั้งหมด',
    cumulativeAmount: 'ยอดรวมสะสม',
    lastTransactionDate: 'วันที่ทำรายการล่าสุด',
    transactionHistory: 'ประวัติการทำรายการ',
    noTransactionHistory: 'ไม่มีประวัติการทำรายการ',
    date: 'วันที่',
    currency: 'สกุลเงิน',
    type: 'ประเภท',
    completed: 'เสร็จสมบูรณ์',
    currentRate: 'อัตราปัจจุบัน'
  }
}

-- ========================================
-- Complete Report Fields Initialization
-- Based on Standard AMLO/BOT Report Forms
-- ========================================

-- Clear existing fields
DELETE FROM report_fields WHERE report_type IN ('AMLO-1-01', 'AMLO-1-02', 'AMLO-1-03', 'BOT-T1-BUY', 'BOT-T1-SELL');

-- ========================================
-- AMLO-1-01: Cash Transaction Report
-- (Based on standard form image analysis)
-- ========================================

-- Form Header Section
INSERT INTO report_fields (field_name, field_type, field_length, field_cn_name, field_en_name, field_th_name, report_type, field_group, fill_order, is_required, is_active) VALUES
('report_number', 'VARCHAR', 50, '报告编号', 'Report Number', 'เลขที่รายงาน', 'AMLO-1-01', '表头信息', 1, 1, 1),
('report_date_day', 'INT', NULL, '报告日期-日', 'Report Date - Day', 'วันที่', 'AMLO-1-01', '表头信息', 2, 1, 1),
('report_date_month', 'INT', NULL, '报告日期-月', 'Report Date - Month', 'เดือน', 'AMLO-1-01', '表头信息', 3, 1, 1),
('report_date_year', 'INT', NULL, '报告日期-年', 'Report Date - Year', 'พ.ศ.', 'AMLO-1-01', '表头信息', 4, 1, 1),
('origin_report_number', 'VARCHAR', 100, '原报告编号', 'Origin Report Number', 'เลขที่ต้นทางรายงาน', 'AMLO-1-01', '表头信息', 5, 0, 1),

-- Report Type Selection
('is_first_report', 'BOOLEAN', NULL, '是否首次报告', 'Is First Report', 'รายงานฉบับแรก', 'AMLO-1-01', '报告类型', 10, 1, 1),
('is_amendment_report', 'BOOLEAN', NULL, '是否修改报告', 'Is Amendment Report', 'รายงานฉบับแก้ไข', 'AMLO-1-01', '报告类型', 11, 0, 1),
('reference_report_number', 'VARCHAR', 100, '参考报告编号', 'Reference Report Number', 'ที่อ้างถึงรายงานฉบับแรก เลขที่', 'AMLO-1-01', '报告类型', 12, 0, 1),

-- Section 1: Transaction Maker (ส่วนที่ ๑ ผู้ทำธุรกรรม)
('maker_type_person', 'BOOLEAN', NULL, '交易者类型-个人', 'Maker Type - Person', 'ชื่อ-นามสกุล', 'AMLO-1-01', 'ส่วนที่ ๑ ผู้ทำธุรกรรม', 20, 1, 1),
('maker_type_juristic', 'BOOLEAN', NULL, '交易者类型-法人', 'Maker Type - Juristic', 'ทำธุรกรรมด้วยตนเอง', 'AMLO-1-01', 'ส่วนที่ ๑ ผู้ทำธุรกรรม', 21, 0, 1),
('maker_name_title', 'VARCHAR', 50, '交易者姓名-称谓', 'Maker Name Title', 'ชื่อ (ข้างหน้านามสกุล)', 'AMLO-1-01', 'ส่วนที่ ๑ ผู้ทำธุรกรรม', 22, 0, 1),
('maker_firstname', 'VARCHAR', 100, '交易者名字', 'Maker First Name', 'ชื่อ', 'AMLO-1-01', 'ส่วนที่ ๑ ผู้ทำธุรกรรม', 23, 1, 1),
('maker_lastname', 'VARCHAR', 100, '交易者姓氏', 'Maker Last Name', 'นามสกุล', 'AMLO-1-01', 'ส่วนที่ ๑ ผู้ทำธุรกรรม', 24, 1, 1),
('maker_company_name', 'VARCHAR', 200, '交易者法人名称', 'Maker Company Name', 'ชื่อนิติบุคคล', 'AMLO-1-01', 'ส่วนที่ ๑ ผู้ทำธุรกรรม', 25, 0, 1),

-- Maker ID/Passport Number
('maker_id_type_national', 'BOOLEAN', NULL, 'ID类型-身份证', 'ID Type - National ID', 'เลขประจำตัวประชาชน', 'AMLO-1-01', 'ส่วนที่ ๑ ผู้ทำธุรกรรม', 30, 1, 1),
('maker_id_type_passport', 'BOOLEAN', NULL, 'ID类型-护照', 'ID Type - Passport', 'หนังสือเดินทาง เลขที่', 'AMLO-1-01', 'ส่วนที่ ๑ ผู้ทำธุรกรรม', 31, 0, 1),
('maker_id_type_company', 'BOOLEAN', NULL, 'ID类型-法人注册号', 'ID Type - Company Registration', 'เลขทะเบียนนิติบุคคล', 'AMLO-1-01', 'ส่วนที่ ๑ ผู้ทำธุรกรรม', 32, 0, 1),
('maker_id_number', 'VARCHAR', 20, '身份证号码', 'ID Number', 'เลขประจำตัว', 'AMLO-1-01', 'ส่วนที่ ๑ ผู้ทำธุรกรรม', 33, 1, 1),

-- Maker Address
('maker_address_number', 'VARCHAR', 20, '地址-号码', 'Address Number', 'ที่อยู่ เลขที่', 'AMLO-1-01', 'ส่วนที่ ๑ ผู้ทำธุรกรรม', 40, 1, 1),
('maker_address_village', 'VARCHAR', 100, '地址-村/大楼', 'Address Village/Building', 'หมู่บ้าน/อาคาร', 'AMLO-1-01', 'ส่วนที่ ๑ ผู้ทำธุรกรรม', 41, 0, 1),
('maker_address_lane', 'VARCHAR', 100, '地址-巷', 'Address Lane', 'ซอย', 'AMLO-1-01', 'ส่วนที่ ๑ ผู้ทำธุรกรรม', 42, 0, 1),
('maker_address_road', 'VARCHAR', 100, '地址-路', 'Address Road', 'ถนน', 'AMLO-1-01', 'ส่วนที่ ๑ ผู้ทำธุรกรรม', 43, 0, 1),
('maker_address_subdistrict', 'VARCHAR', 100, '地址-分区', 'Address Subdistrict', 'ตำบล/แขวง', 'AMLO-1-01', 'ส่วนที่ ๑ ผู้ทำธุรกรรม', 44, 1, 1),
('maker_address_district', 'VARCHAR', 100, '地址-区', 'Address District', 'อำเภอ/เขต', 'AMLO-1-01', 'ส่วนที่ ๑ ผู้ทำธุรกรรม', 45, 1, 1),
('maker_address_province', 'VARCHAR', 100, '地址-省', 'Address Province', 'จังหวัด', 'AMLO-1-01', 'ส่วนที่ ๑ ผู้ทำธุรกรรม', 46, 1, 1),
('maker_address_postalcode', 'VARCHAR', 10, '地址-邮编', 'Address Postal Code', 'รหัสไปรษณีย์', 'AMLO-1-01', 'ส่วนที่ ๑ ผู้ทำธุรกรรม', 47, 0, 1),
('maker_phone', 'VARCHAR', 20, '电话号码', 'Phone Number', 'หมายเลขโทรศัพท์', 'AMLO-1-01', 'ส่วนที่ ๑ ผู้ทำธุรกรรม', 48, 0, 1),

-- Maker Birthplace/Registration
('maker_birthplace_province', 'VARCHAR', 100, '出生地/注册地-省', 'Birthplace Province', 'สถานที่เกิดหรือที่จดทะเบียน จังหวัด', 'AMLO-1-01', 'ส่วนที่ ๑ ผู้ทำธุรกรรม', 50, 0, 1),
('maker_birthplace_country', 'VARCHAR', 100, '出生地/注册地-国家', 'Birthplace Country', 'ประเทศ', 'AMLO-1-01', 'ส่วนที่ ๑ ผู้ทำธุรกรรม', 51, 0, 1),
('maker_birthdate_day', 'INT', NULL, '出生日期-日', 'Birth Date - Day', 'วันเกิด วันที่', 'AMLO-1-01', 'ส่วนที่ ๑ ผู้ทำธุรกรรม', 52, 0, 1),
('maker_birthdate_month', 'INT', NULL, '出生日期-月', 'Birth Date - Month', 'เดือน', 'AMLO-1-01', 'ส่วนที่ ๑ ผู้ทำธุรกรรม', 53, 0, 1),
('maker_birthdate_year', 'INT', NULL, '出生日期-年', 'Birth Date - Year', 'พ.ศ.', 'AMLO-1-01', 'ส่วนที่ ๑ ผู้ทำธุรกรรม', 54, 0, 1),

-- Maker Occupation
('maker_occupation_type', 'VARCHAR', 100, '职业类型', 'Occupation Type', 'อาชีพ', 'AMLO-1-01', 'ส่วนที่ ๑ ผู้ทำธุรกรรม', 60, 0, 1),
('maker_occupation_business_type', 'VARCHAR', 200, '业务类型', 'Business Type', 'ประเภทธุรกิจหรือประเภทงาน', 'AMLO-1-01', 'ส่วนที่ ๑ ผู้ทำธุรกรรม', 61, 0, 1),
('maker_occupation_employer', 'VARCHAR', 200, '雇主/公司名', 'Employer Name', 'ชื่อนายจ้าง/สถานประกอบการ', 'AMLO-1-01', 'ส่วนที่ ๑ ผู้ทำธุรกรรม', 62, 0, 1),

-- Section 2: Joint Party / Authorized Person (ส่วนที่ ๒)
('joint_party_exists', 'BOOLEAN', NULL, '是否有共同交易者', 'Has Joint Party', 'มีผู้ร่วมทำธุรกรรม', 'AMLO-1-01', 'ส่วนที่ ๒ ผู้ร่วมทำธุรกรรม', 100, 0, 1),
('joint_party_type', 'VARCHAR', 20, '共同方类型', 'Joint Party Type', 'ประเภท', 'AMLO-1-01', 'ส่วนที่ ๒ ผู้ร่วมทำธุรกรรม', 101, 0, 1),
('joint_party_firstname', 'VARCHAR', 100, '共同方名字', 'Joint Party First Name', 'ชื่อ', 'AMLO-1-01', 'ส่วนที่ ๒ ผู้ร่วมทำธุรกรรม', 102, 0, 1),
('joint_party_lastname', 'VARCHAR', 100, '共同方姓氏', 'Joint Party Last Name', 'นามสกุล', 'AMLO-1-01', 'ส่วนที่ ๒ ผู้ร่วมทำธุรกรรม', 103, 0, 1),
('joint_party_company_name', 'VARCHAR', 200, '共同方法人名称', 'Joint Party Company Name', 'ชื่อนิติบุคคล', 'AMLO-1-01', 'ส่วนที่ ๒ ผู้ร่วมทำธุรกรรม', 104, 0, 1),
('joint_party_id_number', 'VARCHAR', 20, '共同方身份证号', 'Joint Party ID Number', 'เลขประจำตัว', 'AMLO-1-01', 'ส่วนที่ ๒ ผู้ร่วมทำธุรกรรม', 105, 0, 1),
('joint_party_address', 'VARCHAR', 500, '共同方地址', 'Joint Party Address', 'ที่อยู่', 'AMLO-1-01', 'ส่วนที่ ๒ ผู้ร่วมทำธุรกรรม', 106, 0, 1),
('joint_party_phone', 'VARCHAR', 20, '共同方电话', 'Joint Party Phone', 'หมายเลขโทรศัพท์', 'AMLO-1-01', 'ส่วนที่ ๒ ผู้ร่วมทำธุรกรรม', 107, 0, 1),

-- Section 3: Transaction Facts (ส่วนที่ ๓ ข้อเท็จจริงเกี่ยวกับธุรกรรม)
('transaction_date_day', 'INT', NULL, '交易日期-日', 'Transaction Date - Day', 'วันที่ทำธุรกรรม วันที่', 'AMLO-1-01', 'ส่วนที่ ๓ ธุรกรรม', 200, 1, 1),
('transaction_date_month', 'INT', NULL, '交易日期-月', 'Transaction Date - Month', 'เดือน', 'AMLO-1-01', 'ส่วนที่ ๓ ธุรกรรม', 201, 1, 1),
('transaction_date_year', 'INT', NULL, '交易日期-年', 'Transaction Date - Year', 'พ.ศ.', 'AMLO-1-01', 'ส่วนที่ ๓ ธุรกรรม', 202, 1, 1),

-- Currency Transaction Details - Left Column (Deposit/Buy)
('deposit_cash', 'BOOLEAN', NULL, '存款-现金', 'Deposit Cash', 'เงินฝาก เงินสด', 'AMLO-1-01', 'ส่วนที่ ๓ ธุรกรรม', 210, 0, 1),
('deposit_travelers_check', 'BOOLEAN', NULL, '存款-旅行支票', 'Deposit Travelers Check', 'เช็คเดินทาง', 'AMLO-1-01', 'ส่วนที่ ๓ ธุรกรรม', 211, 0, 1),
('deposit_draft', 'BOOLEAN', NULL, '存款-汇票', 'Deposit Draft', 'ตั๋วแลกเงิน', 'AMLO-1-01', 'ส่วนที่ ๓ ธุรกรรม', 212, 0, 1),
('deposit_cashiers_check', 'BOOLEAN', NULL, '存款-本票', 'Deposit Cashiers Check', 'เช็คธนาคาร', 'AMLO-1-01', 'ส่วนที่ ๓ ธุรกรรม', 213, 0, 1),
('deposit_currency_code', 'VARCHAR', 10, '存款-货币代码', 'Deposit Currency Code', 'สกุลเงินต่างประเทศ (เงินฝาก)', 'AMLO-1-01', 'ส่วนที่ ๓ ธุรกรรม', 214, 0, 1),
('deposit_currency_amount', 'DECIMAL', NULL, '存款-外币金额', 'Deposit Currency Amount', 'จำนวนเงินสกุลต่างประเทศ', 'AMLO-1-01', 'ส่วนที่ ๓ ธุรกรรม', 215, 0, 1),
('deposit_thb_amount', 'DECIMAL', NULL, '存款-泰铢金额', 'Deposit THB Amount', 'จำนวน (บาท) เงินฝาก', 'AMLO-1-01', 'ส่วนที่ ๓ ธุรกรรม', 216, 0, 1),

-- Currency Transaction Details - Right Column (Withdrawal/Sell)
('withdrawal_cash', 'BOOLEAN', NULL, '取款-现金', 'Withdrawal Cash', 'ถอนเงิน เงินสด', 'AMLO-1-01', 'ส่วนที่ ๓ ธุรกรรม', 220, 0, 1),
('withdrawal_travelers_check', 'BOOLEAN', NULL, '取款-旅行支票', 'Withdrawal Travelers Check', 'เช็คเดินทาง', 'AMLO-1-01', 'ส่วนที่ ๓ ธุรกรรม', 221, 0, 1),
('withdrawal_draft', 'BOOLEAN', NULL, '取款-汇票', 'Withdrawal Draft', 'ตั๋วแลกเงิน', 'AMLO-1-01', 'ส่วนที่ ๓ ธุรกรรม', 222, 0, 1),
('withdrawal_cashiers_check', 'BOOLEAN', NULL, '取款-本票', 'Withdrawal Cashiers Check', 'เช็คธนาคาร', 'AMLO-1-01', 'ส่วนที่ ๓ ธุรกรรม', 223, 0, 1),
('withdrawal_currency_code', 'VARCHAR', 10, '取款-货币代码', 'Withdrawal Currency Code', 'สกุลเงินต่างประเทศ (ถอนเงิน)', 'AMLO-1-01', 'ส่วนที่ ๓ ธุรกรรม', 224, 0, 1),
('withdrawal_currency_amount', 'DECIMAL', NULL, '取款-外币金额', 'Withdrawal Currency Amount', 'จำนวนเงินสกุลต่างประเทศ', 'AMLO-1-01', 'ส่วนที่ ๓ ธุรกรรม', 225, 0, 1),
('withdrawal_thb_amount', 'DECIMAL', NULL, '取款-泰铢金额', 'Withdrawal THB Amount', 'จำนวน (บาท) ถอนเงิน', 'AMLO-1-01', 'ส่วนที่ ๓ ธุรกรรม', 226, 0, 1),

-- Exchange Foreign Currency
('exchange_currency_exists', 'BOOLEAN', NULL, '是否兑换外币', 'Has Currency Exchange', 'แลกเปลี่ยนเงินตราต่างประเทศ', 'AMLO-1-01', 'ส่วนที่ ๓ ธุรกรรม', 230, 0, 1),
('exchange_other_transaction', 'BOOLEAN', NULL, '其他交易', 'Other Transaction', 'อื่น ๆ (ระบุ)', 'AMLO-1-01', 'ส่วนที่ ๓ ธุรกรรม', 231, 0, 1),
('exchange_other_description', 'VARCHAR', 200, '其他交易说明', 'Other Transaction Description', 'ระบุ', 'AMLO-1-01', 'ส่วนที่ ๓ ธุรกรรม', 232, 0, 1),

-- Transaction Purpose/Source
('transaction_purpose', 'VARCHAR', 500, '交易目的', 'Transaction Purpose', 'วัตถุประสงค์ในการทำธุรกรรม (ถ้ามี)', 'AMLO-1-01', 'ส่วนที่ ๓ ธุรกรรม', 240, 0, 1),
('transaction_source', 'VARCHAR', 500, '资金来源', 'Source of Funds', 'ที่มาของเงิน (ถ้ามี)', 'AMLO-1-01', 'ส่วนที่ ๓ ธุรกรรม', 241, 0, 1),

-- Section 4: Reporter (ส่วนที่ ๔)
('reporter_institution_type', 'VARCHAR', 100, '报告机构类型', 'Reporter Institution Type', 'ประเภทสถาบันการเงิน', 'AMLO-1-01', 'ส่วนที่ ๔ ผู้รายงาน', 300, 1, 1),
('reporter_institution_name', 'VARCHAR', 200, '报告机构名称', 'Reporter Institution Name', 'ชื่อสถาบันการเงิน', 'AMLO-1-01', 'ส่วนที่ ๔ ผู้รายงาน', 301, 1, 1),
('reporter_branch_name', 'VARCHAR', 200, '报告分支名称', 'Reporter Branch Name', 'สาขา', 'AMLO-1-01', 'ส่วนที่ ๔ ผู้รายงาน', 302, 0, 1),
('reporter_signature_date_day', 'INT', NULL, '签名日期-日', 'Signature Date - Day', 'ลายมือชื่อผู้รายงาน วันที่', 'AMLO-1-01', 'ส่วนที่ ๔ ผู้รายงาน', 303, 1, 1),
('reporter_signature_date_month', 'INT', NULL, '签名日期-月', 'Signature Date - Month', 'เดือน', 'AMLO-1-01', 'ส่วนที่ ๔ ผู้รายงาน', 304, 1, 1),
('reporter_signature_date_year', 'INT', NULL, '签名日期-年', 'Signature Date - Year', 'พ.ศ.', 'AMLO-1-01', 'ส่วนที่ ๔ ผู้รายงาน', 305, 1, 1);

-- ========================================
-- AMLO-1-02: Asset Transaction Report
-- ========================================

INSERT INTO report_fields (field_name, field_type, field_length, field_cn_name, field_en_name, field_th_name, report_type, field_group, fill_order, is_required, is_active) VALUES
-- Form Header
('report_number', 'VARCHAR', 50, '报告编号', 'Report Number', 'เลขที่รายงาน', 'AMLO-1-02', '表头信息', 1, 1, 1),
('report_date_day', 'INT', NULL, '报告日期-日', 'Report Date - Day', 'วันที่', 'AMLO-1-02', '表头信息', 2, 1, 1),
('report_date_month', 'INT', NULL, '报告日期-月', 'Report Date - Month', 'เดือน', 'AMLO-1-02', '表头信息', 3, 1, 1),
('report_date_year', 'INT', NULL, '报告日期-年', 'Report Date - Year', 'พ.ศ.', 'AMLO-1-02', '表头信息', 4, 1, 1),
('origin_report_number', 'VARCHAR', 100, '原报告编号', 'Origin Report Number', 'เลขที่ต้นทางรายงาน', 'AMLO-1-02', '表头信息', 5, 0, 1),

-- Report Type
('is_first_report', 'BOOLEAN', NULL, '是否首次报告', 'Is First Report', 'รายงานฉบับแรก', 'AMLO-1-02', '报告类型', 10, 1, 1),
('is_amendment_report', 'BOOLEAN', NULL, '是否修改报告', 'Is Amendment Report', 'รายงานฉบับแก้ไข', 'AMLO-1-02', '报告类型', 11, 0, 1),
('reference_report_number', 'VARCHAR', 100, '参考报告编号', 'Reference Report Number', 'เลขที่อ้างถึง', 'AMLO-1-02', '报告类型', 12, 0, 1),

-- Section 1: Transaction Maker
('maker_type_person', 'BOOLEAN', NULL, '交易者类型-个人', 'Maker Type - Person', 'ชื่อ-นามสกุล', 'AMLO-1-02', 'ส่วนที่ ๑ ผู้ทำธุรกรรม', 20, 1, 1),
('maker_type_juristic', 'BOOLEAN', NULL, '交易者类型-法人', 'Maker Type - Juristic', 'นิติบุคคล', 'AMLO-1-02', 'ส่วนที่ ๑ ผู้ทำธุรกรรม', 21, 0, 1),
('maker_firstname', 'VARCHAR', 100, '交易者名字', 'Maker First Name', 'ชื่อ', 'AMLO-1-02', 'ส่วนที่ ๑ ผู้ทำธุรกรรม', 22, 1, 1),
('maker_lastname', 'VARCHAR', 100, '交易者姓氏', 'Maker Last Name', 'นามสกุล', 'AMLO-1-02', 'ส่วนที่ ๑ ผู้ทำธุรกรรม', 23, 1, 1),
('maker_id_number', 'VARCHAR', 20, '身份证号码', 'ID Number', 'เลขประจำตัว', 'AMLO-1-02', 'ส่วนที่ ๑ ผู้ทำธุรกรรม', 24, 1, 1),
('maker_address', 'VARCHAR', 500, '地址', 'Address', 'ที่อยู่', 'AMLO-1-02', 'ส่วนที่ ๑ ผู้ทำธุรกรรม', 25, 1, 1),
('maker_phone', 'VARCHAR', 20, '电话', 'Phone', 'โทรศัพท์', 'AMLO-1-02', 'ส่วนที่ ๑ ผู้ทำธุรกรรม', 26, 0, 1),

-- Section 2: Joint Party
('joint_party_firstname', 'VARCHAR', 100, '共同方名字', 'Joint Party First Name', 'ชื่อ', 'AMLO-1-02', 'ส่วนที่ ๒ ผู้ร่วมทำธุรกรรม', 30, 0, 1),
('joint_party_lastname', 'VARCHAR', 100, '共同方姓氏', 'Joint Party Last Name', 'นามสกุล', 'AMLO-1-02', 'ส่วนที่ ๒ ผู้ร่วมทำธุรกรรม', 31, 0, 1),
('joint_party_id_number', 'VARCHAR', 20, '共同方身份证', 'Joint Party ID', 'เลขประจำตัว', 'AMLO-1-02', 'ส่วนที่ ๒ ผู้ร่วมทำธุรกรรม', 32, 0, 1),
('joint_party_address', 'VARCHAR', 500, '共同方地址', 'Joint Party Address', 'ที่อยู่', 'AMLO-1-02', 'ส่วนที่ ๒ ผู้ร่วมทำธุรกรรม', 33, 0, 1),

-- Section 3: Asset Transaction Details
('transaction_date_day', 'INT', NULL, '交易日期-日', 'Transaction Date - Day', 'วันที่ทำธุรกรรม วันที่', 'AMLO-1-02', 'ส่วนที่ ๓ ธุรกรรม', 40, 1, 1),
('transaction_date_month', 'INT', NULL, '交易日期-月', 'Transaction Date - Month', 'เดือน', 'AMLO-1-02', 'ส่วนที่ ๓ ธุรกรรม', 41, 1, 1),
('transaction_date_year', 'INT', NULL, '交易日期-年', 'Transaction Date - Year', 'พ.ศ.', 'AMLO-1-02', 'ส่วนที่ ๓ ธุรกรรม', 42, 1, 1),

('transaction_type_mortgage', 'BOOLEAN', NULL, '交易类型-抵押', 'Transaction Type - Mortgage', 'จำนอง', 'AMLO-1-02', 'ส่วนที่ ๓ ธุรกรรม', 50, 0, 1),
('transaction_type_sale', 'BOOLEAN', NULL, '交易类型-出售', 'Transaction Type - Sale', 'ขาย', 'AMLO-1-02', 'ส่วนที่ ๓ ธุรกรรม', 51, 0, 1),
('transaction_type_transfer', 'BOOLEAN', NULL, '交易类型-转让', 'Transaction Type - Transfer', 'โอนกรรมสิทธิ์', 'AMLO-1-02', 'ส่วนที่ ๓ ธุรกรรม', 52, 0, 1),
('transaction_type_lease', 'BOOLEAN', NULL, '交易类型-租赁', 'Transaction Type - Lease', 'เช่า', 'AMLO-1-02', 'ส่วนที่ ๓ ธุรกรรม', 53, 0, 1),
('transaction_type_other', 'BOOLEAN', NULL, '交易类型-其他', 'Transaction Type - Other', 'อื่น ๆ', 'AMLO-1-02', 'ส่วนที่ ๓ ธุรกรรม', 54, 0, 1),

('asset_type_land', 'BOOLEAN', NULL, '资产类型-土地', 'Asset Type - Land', 'ที่ดิน', 'AMLO-1-02', 'ส่วนที่ ๓ ธุรกรรม', 60, 0, 1),
('asset_type_building', 'BOOLEAN', NULL, '资产类型-建筑', 'Asset Type - Building', 'สิ่งปลูกสร้าง', 'AMLO-1-02', 'ส่วนที่ ๓ ธุรกรรม', 61, 0, 1),
('asset_type_condominium', 'BOOLEAN', NULL, '资产类型-公寓', 'Asset Type - Condominium', 'ห้องชุด', 'AMLO-1-02', 'ส่วนที่ ๓ ธุรกรรม', 62, 0, 1),
('asset_type_other', 'BOOLEAN', NULL, '资产类型-其他', 'Asset Type - Other', 'อื่น ๆ', 'AMLO-1-02', 'ส่วนที่ ๓ ธุรกรรม', 63, 0, 1),

('asset_value_thb', 'DECIMAL', NULL, '资产价值(泰铢)', 'Asset Value (THB)', 'มูลค่าทรัพย์สิน (บาท)', 'AMLO-1-02', 'ส่วนที่ ๓ ธุรกรรม', 70, 1, 1),
('asset_location', 'VARCHAR', 500, '资产位置', 'Asset Location', 'ที่ตั้งทรัพย์สิน', 'AMLO-1-02', 'ส่วนที่ ๓ ธุรกรรม', 71, 0, 1),
('asset_deed_number', 'VARCHAR', 100, '地契号码', 'Deed Number', 'เลขที่โฉนด', 'AMLO-1-02', 'ส่วนที่ ๓ ธุรกรรม', 72, 0, 1),
('asset_area', 'VARCHAR', 100, '资产面积', 'Asset Area', 'เนื้อที่', 'AMLO-1-02', 'ส่วนที่ ๓ ธุรกรรม', 73, 0, 1),

-- Section 4: Reporter
('reporter_institution_name', 'VARCHAR', 200, '报告机构名称', 'Reporter Institution Name', 'ชื่อผู้รายงาน', 'AMLO-1-02', 'ส่วนที่ ๔ ผู้รายงาน', 80, 1, 1),
('reporter_branch_name', 'VARCHAR', 200, '报告分支名称', 'Reporter Branch Name', 'สาขา', 'AMLO-1-02', 'ส่วนที่ ๔ ผู้รายงาน', 81, 0, 1),
('reporter_signature_date_day', 'INT', NULL, '签名日期-日', 'Signature Date - Day', 'วันที่', 'AMLO-1-02', 'ส่วนที่ ๔ ผู้รายงาน', 82, 1, 1),
('reporter_signature_date_month', 'INT', NULL, '签名日期-月', 'Signature Date - Month', 'เดือน', 'AMLO-1-02', 'ส่วนที่ ๔ ผู้รายงาน', 83, 1, 1),
('reporter_signature_date_year', 'INT', NULL, '签名日期-年', 'Signature Date - Year', 'พ.ศ.', 'AMLO-1-02', 'ส่วนที่ ๔ ผู้รายงาน', 84, 1, 1);

-- ========================================
-- AMLO-1-03: Suspicious Transaction Report
-- ========================================

INSERT INTO report_fields (field_name, field_type, field_length, field_cn_name, field_en_name, field_th_name, report_type, field_group, fill_order, is_required, is_active) VALUES
-- Form Header
('report_number', 'VARCHAR', 50, '报告编号', 'Report Number', 'เลขที่รายงาน', 'AMLO-1-03', '表头信息', 1, 1, 1),
('report_date_day', 'INT', NULL, '报告日期-日', 'Report Date - Day', 'วันที่', 'AMLO-1-03', '表头信息', 2, 1, 1),
('report_date_month', 'INT', NULL, '报告日期-月', 'Report Date - Month', 'เดือน', 'AMLO-1-03', '表头信息', 3, 1, 1),
('report_date_year', 'INT', NULL, '报告日期-年', 'Report Date - Year', 'พ.ศ.', 'AMLO-1-03', '表头信息', 4, 1, 1),

-- Report Type
('is_first_report', 'BOOLEAN', NULL, '是否首次报告', 'Is First Report', 'รายงานฉบับแรก', 'AMLO-1-03', '报告类型', 10, 1, 1),
('is_amendment_report', 'BOOLEAN', NULL, '是否修改报告', 'Is Amendment Report', 'รายงานฉบับแก้ไข', 'AMLO-1-03', '报告类型', 11, 0, 1),
('reference_report_number', 'VARCHAR', 100, '参考报告编号', 'Reference Report Number', 'เลขที่อ้างถึง', 'AMLO-1-03', '报告类型', 12, 0, 1),

-- Section 1: Transaction Maker
('maker_firstname', 'VARCHAR', 100, '交易者名字', 'Maker First Name', 'ชื่อ-นามสกุล', 'AMLO-1-03', 'ส่วนที่ ๑ ผู้ทำธุรกรรม', 20, 1, 1),
('maker_lastname', 'VARCHAR', 100, '交易者姓氏', 'Maker Last Name', 'นามสกุล', 'AMLO-1-03', 'ส่วนที่ ๑ ผู้ทำธุรกรรม', 21, 0, 1),
('maker_id_number', 'VARCHAR', 20, '身份证号码', 'ID Number', 'เลขประจำตัว', 'AMLO-1-03', 'ส่วนที่ ๑ ผู้ทำธุรกรรม', 22, 1, 1),
('maker_address', 'VARCHAR', 500, '地址', 'Address', 'ที่อยู่', 'AMLO-1-03', 'ส่วนที่ ๑ ผู้ทำธุรกรรม', 23, 0, 1),
('maker_birthdate', 'DATE', NULL, '出生日期', 'Birth Date', 'วันเกิด', 'AMLO-1-03', 'ส่วนที่ ๑ ผู้ทำธุรกรรม', 24, 0, 1),

-- Section 2: Joint Party
('joint_party_firstname', 'VARCHAR', 100, '共同方名字', 'Joint Party First Name', 'ชื่อผู้ร่วมทำธุรกรรม', 'AMLO-1-03', 'ส่วนที่ ๒ ผู้ร่วมทำธุรกรรม', 30, 0, 1),
('joint_party_lastname', 'VARCHAR', 100, '共同方姓氏', 'Joint Party Last Name', 'นามสกุล', 'AMLO-1-03', 'ส่วนที่ ๒ ผู้ร่วมทำธุรกรรม', 31, 0, 1),
('joint_party_id_number', 'VARCHAR', 20, '共同方身份证', 'Joint Party ID', 'เลขประจำตัว', 'AMLO-1-03', 'ส่วนที่ ๒ ผู้ร่วมทำธุรกรรม', 32, 0, 1),
('joint_party_address', 'VARCHAR', 500, '共同方地址', 'Joint Party Address', 'ที่อยู่', 'AMLO-1-03', 'ส่วนที่ ๒ ผู้ร่วมทำธุรกรรม', 33, 0, 1),

-- Section 3: Transaction Details
('transaction_date_day', 'INT', NULL, '交易日期-日', 'Transaction Date - Day', 'วันที่ทำธุรกรรม', 'AMLO-1-03', 'ส่วนที่ ๓ ธุรกรรม', 40, 1, 1),
('transaction_date_month', 'INT', NULL, '交易日期-月', 'Transaction Date - Month', 'เดือน', 'AMLO-1-03', 'ส่วนที่ ๓ ธุรกรรม', 41, 1, 1),
('transaction_date_year', 'INT', NULL, '交易日期-年', 'Transaction Date - Year', 'พ.ศ.', 'AMLO-1-03', 'ส่วนที่ ๓ ธุรกรรม', 42, 1, 1),
('transaction_amount_thb', 'DECIMAL', NULL, '交易金额(泰铢)', 'Transaction Amount (THB)', 'จำนวนเงิน (บาท)', 'AMLO-1-03', 'ส่วนที่ ๓ ธุรกรรม', 43, 0, 1),

-- Section 4: Suspicion Details
('has_filed_ctr_atr', 'BOOLEAN', NULL, '是否已提交CTR/ATR', 'Has Filed CTR/ATR', 'ได้ยื่นแบบ ปปง.๑-๐๑ หรือ ปปง.๑-๐๒', 'AMLO-1-03', 'ส่วนที่ ๔ เหตุสงสัย', 50, 0, 1),
('previous_report_number', 'VARCHAR', 100, '之前报告编号', 'Previous Report Number', 'เลขที่รายงาน ปปง.๑-๐๑/๑-๐๒', 'AMLO-1-03', 'ส่วนที่ ๔ เหตุสงสัย', 51, 0, 1),
('suspicion_reasons', 'TEXT', NULL, '可疑原因', 'Suspicion Reasons', 'เหตุอันควรสงสัย', 'AMLO-1-03', 'ส่วนที่ ๔ เหตุสงสัย', 52, 1, 1),

-- Section 5: Reporter
('reporter_institution_name', 'VARCHAR', 200, '报告机构名称', 'Reporter Institution Name', 'ชื่อผู้รายงาน', 'AMLO-1-03', 'ส่วนที่ ๕ ผู้รายงาน', 60, 1, 1),
('reporter_position', 'VARCHAR', 100, '报告人职位', 'Reporter Position', 'ตำแหน่ง', 'AMLO-1-03', 'ส่วนที่ ๕ ผู้รายงาน', 61, 0, 1),
('reporter_signature_date_day', 'INT', NULL, '签名日期-日', 'Signature Date - Day', 'วันที่', 'AMLO-1-03', 'ส่วนที่ ๕ ผู้รายงาน', 62, 1, 1),
('reporter_signature_date_month', 'INT', NULL, '签名日期-月', 'Signature Date - Month', 'เดือน', 'AMLO-1-03', 'ส่วนที่ ๕ ผู้รายงาน', 63, 1, 1),
('reporter_signature_date_year', 'INT', NULL, '签名日期-年', 'Signature Date - Year', 'พ.ศ.', 'AMLO-1-03', 'ส่วนที่ ๕ ผู้รายงาน', 64, 1, 1);

-- ========================================
-- BOT T+1 Buy FX Report
-- ========================================

INSERT INTO report_fields (field_name, field_type, field_length, field_cn_name, field_en_name, field_th_name, report_type, field_group, fill_order, is_required, is_active) VALUES
('report_date', 'DATE', NULL, '报告日期', 'Report Date', 'วันที่รายงาน', 'BOT-T1-BUY', '报告基本信息', 1, 1, 1),
('transaction_number', 'VARCHAR', 50, '交易编号', 'Transaction Number', 'เลขที่ธุรกรรม', 'BOT-T1-BUY', '交易信息', 10, 1, 1),
('transaction_date', 'DATE', NULL, '交易日期', 'Transaction Date', 'วันที่ทำธุรกรรม', 'BOT-T1-BUY', '交易信息', 11, 1, 1),
('customer_id', 'VARCHAR', 20, '客户证件号', 'Customer ID', 'เลขประจำตัวลูกค้า', 'BOT-T1-BUY', '客户信息', 20, 1, 1),
('customer_name', 'VARCHAR', 200, '客户姓名', 'Customer Name', 'ชื่อลูกค้า', 'BOT-T1-BUY', '客户信息', 21, 1, 1),
('customer_type', 'VARCHAR', 50, '客户类型', 'Customer Type', 'ประเภทลูกค้า', 'BOT-T1-BUY', '客户信息', 22, 1, 1),
('currency_code', 'VARCHAR', 10, '货币代码', 'Currency Code', 'สกุลเงิน', 'BOT-T1-BUY', '货币信息', 30, 1, 1),
('foreign_amount', 'DECIMAL', NULL, '外币金额', 'Foreign Amount', 'จำนวนเงินต่างประเทศ', 'BOT-T1-BUY', '货币信息', 31, 1, 1),
('exchange_rate', 'DECIMAL', NULL, '汇率', 'Exchange Rate', 'อัตราแลกเปลี่ยน', 'BOT-T1-BUY', '货币信息', 32, 1, 1),
('thb_amount', 'DECIMAL', NULL, '泰铢金额', 'THB Amount', 'จำนวนเงินบาท', 'BOT-T1-BUY', '货币信息', 33, 1, 1),
('transaction_purpose', 'VARCHAR', 200, '交易目的', 'Transaction Purpose', 'วัตถุประสงค์', 'BOT-T1-BUY', '交易信息', 40, 0, 1),
('funding_source', 'VARCHAR', 200, '资金来源', 'Funding Source', 'ที่มาของเงิน', 'BOT-T1-BUY', '交易信息', 41, 0, 1);

-- ========================================
-- BOT T+1 Sell FX Report
-- ========================================

INSERT INTO report_fields (field_name, field_type, field_length, field_cn_name, field_en_name, field_th_name, report_type, field_group, fill_order, is_required, is_active) VALUES
('report_date', 'DATE', NULL, '报告日期', 'Report Date', 'วันที่รายงาน', 'BOT-T1-SELL', '报告基本信息', 1, 1, 1),
('transaction_number', 'VARCHAR', 50, '交易编号', 'Transaction Number', 'เลขที่ธุรกรรม', 'BOT-T1-SELL', '交易信息', 10, 1, 1),
('transaction_date', 'DATE', NULL, '交易日期', 'Transaction Date', 'วันที่ทำธุรกรรม', 'BOT-T1-SELL', '交易信息', 11, 1, 1),
('customer_id', 'VARCHAR', 20, '客户证件号', 'Customer ID', 'เลขประจำตัวลูกค้า', 'BOT-T1-SELL', '客户信息', 20, 1, 1),
('customer_name', 'VARCHAR', 200, '客户姓名', 'Customer Name', 'ชื่อลูกค้า', 'BOT-T1-SELL', '客户信息', 21, 1, 1),
('customer_type', 'VARCHAR', 50, '客户类型', 'Customer Type', 'ประเภทลูกค้า', 'BOT-T1-SELL', '客户信息', 22, 1, 1),
('currency_code', 'VARCHAR', 10, '货币代码', 'Currency Code', 'สกุลเงิน', 'BOT-T1-SELL', '货币信息', 30, 1, 1),
('foreign_amount', 'DECIMAL', NULL, '外币金额', 'Foreign Amount', 'จำนวนเงินต่างประเทศ', 'BOT-T1-SELL', '货币信息', 31, 1, 1),
('exchange_rate', 'DECIMAL', NULL, '汇率', 'Exchange Rate', 'อัตราแลกเปลี่ยน', 'BOT-T1-SELL', '货币信息', 32, 1, 1),
('thb_amount', 'DECIMAL', NULL, '泰铢金额', 'THB Amount', 'จำนวนเงินบาท', 'BOT-T1-SELL', '货币信息', 33, 1, 1),
('transaction_purpose', 'VARCHAR', 200, '交易目的', 'Transaction Purpose', 'วัตถุประสงค์', 'BOT-T1-SELL', '交易信息', 40, 0, 1),
('payment_destination', 'VARCHAR', 200, '收款目的地', 'Payment Destination', 'จุดหมายปลายทาง', 'BOT-T1-SELL', '交易信息', 41, 0, 1);

-- Update timestamp
UPDATE report_fields SET created_at = NOW() WHERE created_at IS NULL;

-- ============================================================
-- AMLO和BOT合规报告系统 - 初始化数据脚本
-- 版本: v1.0
-- 创建日期: 2025-10-02
-- 说明: 初始化report_fields、trigger_rules、funding_sources数据
-- ============================================================

SET NAMES utf8mb4;

-- ============================================================
-- 1. report_fields初始化数据 - AMLO-1-01报告字段
-- ============================================================

-- 第1部分：交易人信息
INSERT INTO `report_fields` VALUES
(NULL, 'customer_name', 'VARCHAR', 100, NULL, NULL, '姓名-名字', 'Name-Surname', 'ชื่อ-นามสกุล', 1, TRUE, NULL, '{"min_length": 2, "max_length": 100}', '请输入客户姓名', 'Enter customer name', 'กรอกชื่อลูกคา', '客户的完整姓名', 'Full name of customer', 'ชื่อเต็มของลูกคา', '交易人信息', 'AMLO-1-01', TRUE, NOW(), NOW()),

(NULL, 'transaction_method', 'ENUM', NULL, NULL, NULL, '交易方式', 'Transaction Method', 'วิธีการทำธุรกรรม', 2, TRUE, 'self', '{"options": ["self", "agent"]}', '选择交易方式', 'Select method', 'เลือกวิธี', '本人办理或代理', 'Self or agent', 'ด้วยตนเองหรือตัวแทน', '交易人信息', 'AMLO-1-01', TRUE, NOW(), NOW()),

(NULL, 'customer_address', 'TEXT', NULL, NULL, NULL, '住址', 'Address', 'ที่อยู่', 3, TRUE, NULL, '{"min_length": 10}', '请输入详细地址', 'Enter full address', 'กรอกที่อยู่', '客户的详细居住地址', 'Full residential address', 'ที่อยู่เต็ม', '交易人信息', 'AMLO-1-01', TRUE, NOW(), NOW()),

(NULL, 'customer_phone', 'VARCHAR', 20, NULL, NULL, '电话', 'Phone', 'โทรศัพท์', 4, FALSE, NULL, '{"pattern": "^[0-9\\\\-\\\\+\\\\s]+$"}', '电话号码', 'Phone number', 'เบอร์โทร', '联系电话', 'Contact phone', 'เบอร์ติดต่อ', '交易人信息', 'AMLO-1-01', FALSE, NOW(), NOW()),

(NULL, 'customer_fax', 'VARCHAR', 20, NULL, NULL, '传真', 'Fax', 'โทรสาร', 5, FALSE, NULL, NULL, '传真号码', 'Fax number', 'เบอร์แฟกซ์', '传真号码（如有）', 'Fax number if any', 'หมายเลขแฟกซ์', '交易人信息', 'AMLO-1-01', FALSE, NOW(), NOW()),

(NULL, 'customer_occupation', 'VARCHAR', 100, NULL, NULL, '职业', 'Occupation', 'อาชีพ', 6, TRUE, NULL, NULL, '请输入职业', 'Enter occupation', 'กรอกอาชีพ', '客户的职业', 'Customer occupation', 'อาชีพของลูกคา', '交易人信息', 'AMLO-1-01', TRUE, NOW(), NOW()),

(NULL, 'customer_workplace', 'VARCHAR', 200, NULL, NULL, '工作单位', 'Workplace', 'สถานที่ทำงาน', 7, FALSE, NULL, NULL, '工作单位名称', 'Workplace name', 'ชื่อที่ทำงาน', '客户的工作单位', 'Customer workplace', 'สถานที่ทำงาน', '交易人信息', 'AMLO-1-01', FALSE, NOW(), NOW()),

(NULL, 'customer_work_phone', 'VARCHAR', 20, NULL, NULL, '工作电话', 'Work Phone', 'โทรศัพท์ที่ทำงาน', 8, FALSE, NULL, NULL, '工作电话', 'Work phone', 'เบอร์ที่ทำงาน', '工作单位电话', 'Work phone number', 'เบอร์ที่ทำงาน', '交易人信息', 'AMLO-1-01', FALSE, NOW(), NOW()),

(NULL, 'contact_address', 'TEXT', NULL, NULL, NULL, '便于联系的地址', 'Contact Address', 'ที่อยู่ติดต่อ', 9, FALSE, NULL, NULL, '联系地址', 'Contact address', 'ที่อยู่ติดต่อ', '便于联系的地址（如与住址不同）', 'Contact address if different', 'ที่อยู่สะดวกติดต่อ', '交易人信息', 'AMLO-1-01', FALSE, NOW(), NOW()),

(NULL, 'id_type', 'ENUM', NULL, NULL, NULL, '证件类型', 'ID Type', 'ประเภทบัตร', 10, TRUE, 'national_id', '{"options": ["national_id", "passport", "foreigner_cert", "other"]}', '选择证件类型', 'Select ID type', 'เลือกประเภท', '身份证明文件类型', 'Identity document type', 'ประเภทเอกสาร', '交易人信息', 'AMLO-1-01', TRUE, NOW(), NOW()),

(NULL, 'id_number', 'VARCHAR', 50, NULL, NULL, '证件号码', 'ID Number', 'เลขที่บัตร', 11, TRUE, NULL, '{"min_length": 5}', '证件号码', 'ID number', 'เลขที่', '证件上的号码', 'ID number', 'เลขประจำตัว', '交易人信息', 'AMLO-1-01', TRUE, NOW(), NOW()),

(NULL, 'id_issuer', 'VARCHAR', 100, NULL, NULL, '签发机构', 'Issuer', 'ออกให้โดย', 12, TRUE, NULL, NULL, '签发机构', 'Issuer', 'หน่วยออก', '证件签发机构', 'Issuing authority', 'หน่วยงานออก', '交易人信息', 'AMLO-1-01', TRUE, NOW(), NOW()),

(NULL, 'id_issue_date', 'DATE', NULL, NULL, NULL, '签发日期', 'Issue Date', 'วันที่ออก', 13, FALSE, NULL, NULL, 'YYYY-MM-DD', 'YYYY-MM-DD', 'YYYY-MM-DD', '证件签发日期', 'Issue date', 'วันออกบัตร', '交易人信息', 'AMLO-1-01', FALSE, NOW(), NOW()),

(NULL, 'id_expiry_date', 'DATE', NULL, NULL, NULL, '证件有效期', 'Expiry Date', 'วันหมดอายุ', 14, TRUE, NULL, NULL, 'YYYY-MM-DD', 'YYYY-MM-DD', 'YYYY-MM-DD', '证件有效期截止日期', 'Expiry date', 'วันหมดอายุ', '交易人信息', 'AMLO-1-01', TRUE, NOW(), NOW());

-- 第3部分：交易事实
INSERT INTO `report_fields` VALUES
(NULL, 'transaction_date', 'DATE', NULL, NULL, NULL, '交易日期', 'Transaction Date', 'วันที่ทำธุรกรรม', 20, TRUE, NULL, NULL, 'YYYY-MM-DD', 'YYYY-MM-DD', 'YYYY-MM-DD', '交易发生日期', 'Date of transaction', 'วันทำธุรกรรม', '交易事实', 'AMLO-1-01', TRUE, NOW(), NOW()),

(NULL, 'buy_foreign_currency', 'BOOLEAN', NULL, NULL, NULL, '购买外币', 'Buy Foreign Currency', 'ซื้อเงินตราต่างประเทศ', 25, FALSE, NULL, NULL, NULL, NULL, NULL, '是否购买外币', 'Buy foreign currency', 'ซื้อเงินต่างประเทศ', '交易事实-存入', 'AMLO-1-01', FALSE, NOW(), NOW()),

(NULL, 'buy_currency_code', 'VARCHAR', 3, NULL, NULL, '购买币种', 'Currency Code', 'สกุลเงิน', 26, FALSE, NULL, NULL, 'USD', 'USD', 'USD', '购买的外币币种代码', 'Currency code', 'สกุลเงิน', '交易事实-存入', 'AMLO-1-01', FALSE, NOW(), NOW()),

(NULL, 'buy_currency_amount', 'DECIMAL', NULL, 15, 2, '购买外币金额', 'Buy Amount', 'จำนวนซื้อ', 27, FALSE, NULL, '{"min": 0}', '金额', 'Amount', 'จำนวน', '购买外币金额', 'Buy amount', 'จำนวนซื้อ', '交易事实-存入', 'AMLO-1-01', FALSE, NOW(), NOW()),

(NULL, 'sell_foreign_currency', 'BOOLEAN', NULL, NULL, NULL, '出售外币', 'Sell Foreign Currency', 'ขายเงินตราต่างประเทศ', 35, FALSE, NULL, NULL, NULL, NULL, NULL, '是否出售外币', 'Sell foreign currency', 'ขายเงินต่างประเทศ', '交易事实-支出', 'AMLO-1-01', FALSE, NOW(), NOW()),

(NULL, 'total_amount', 'DECIMAL', NULL, 15, 2, '总金额', 'Total Amount', 'รวมเงิน', 40, TRUE, NULL, '{"min": 0}', '总金额', 'Total', 'รวม', '交易总金额（泰铢）', 'Total amount (THB)', 'รวมเงิน (บาท)', '交易事实', 'AMLO-1-01', TRUE, NOW(), NOW()),

(NULL, 'transaction_purpose', 'TEXT', NULL, NULL, NULL, '交易目的', 'Transaction Purpose', 'วัตถุประสงค์', 44, TRUE, NULL, '{"min_length": 10}', '请描述交易目的', 'Describe purpose', 'อธิบายวัตถุประสงค์', '交易的具体目的或用途', 'Purpose of transaction', 'วัตถุประสงค์ของธุรกรรม', '交易事实', 'AMLO-1-01', TRUE, NOW(), NOW());

-- ============================================================
-- 2. report_fields初始化数据 - AMLO-1-02报告特有字段
-- ============================================================

INSERT INTO `report_fields` VALUES
(NULL, 'asset_transaction_type', 'ENUM', NULL, NULL, NULL, '交易类型', 'Transaction Type', 'ประเภทธุรกรรม', 21, TRUE, NULL, '{"options": ["mortgage", "sale", "transfer", "other"]}', '选择类型', 'Select type', 'เลือกประเภท', '资产交易类型', 'Asset transaction type', 'ประเภทธุรกรรม', '交易事实', 'AMLO-1-02', TRUE, NOW(), NOW()),

(NULL, 'asset_type', 'ENUM', NULL, NULL, NULL, '资产类型', 'Asset Type', 'ประเภททรัพย์สิน', 22, TRUE, NULL, '{"options": ["land", "land_building", "building", "other"]}', '选择类型', 'Select type', 'เลือกประเภท', '资产类型', 'Asset type', 'ประเภททรัพย์สิน', '交易事实', 'AMLO-1-02', TRUE, NOW(), NOW()),

(NULL, 'asset_details', 'TEXT', NULL, NULL, NULL, '资产详情', 'Asset Details', 'รายละเอียดทรัพย์สิน', 23, TRUE, NULL, '{"min_length": 20}', '请详细描述资产', 'Describe asset', 'อธิบายทรัพย์สิน', '资产的详细描述（地址、面积等）', 'Detailed asset description', 'รายละเอียดทรัพย์สิน', '交易事实', 'AMLO-1-02', TRUE, NOW(), NOW()),

(NULL, 'asset_value', 'DECIMAL', NULL, 15, 2, '资产价值', 'Asset Value', 'มูลค่าทรัพย์สิน', 24, TRUE, NULL, '{"min": 0}', '价值（泰铢）', 'Value (THB)', 'มูลค่า (บาท)', '资产的总价值', 'Total asset value', 'มูลค่าทรัพย์สิน', '交易事实', 'AMLO-1-02', TRUE, NOW(), NOW());

-- ============================================================
-- 3. report_fields初始化数据 - AMLO-1-03报告特有字段
-- ============================================================

INSERT INTO `report_fields` VALUES
(NULL, 'suspicious_reason', 'TEXT', NULL, NULL, NULL, '可疑原因', 'Suspicious Reason', 'เหตุอันควรสงสัย', 50, TRUE, NULL, '{"min_length": 50}', '请详细说明可疑原因', 'Explain suspicion', 'อธิบายเหตุสงสัย', '详细说明为何认为此交易可疑', 'Detailed explanation of suspicion', 'เหตุผลที่สงสัย', '可疑信息', 'AMLO-1-03', TRUE, NOW(), NOW()),

(NULL, 'related_report_number', 'VARCHAR', 50, NULL, NULL, '关联报告编号', 'Related Report No', 'เลขที่รายงานที่เกี่ยวข้อง', 51, FALSE, NULL, NULL, '报告编号', 'Report number', 'เลขรายงาน', '如已报告1-01或1-02，填写编号', 'Related report number', 'เลขรายงานที่เกี่ยวข้อง', '可疑信息', 'AMLO-1-03', FALSE, NOW(), NOW());

-- ============================================================
-- 4. trigger_rules初始化数据
-- ============================================================

-- AMLO-1-01：现金交易 >= 500万泰铢
INSERT INTO `trigger_rules` VALUES
(NULL, 'AMLO-1-01-200万THB', 'AMLO-1-01',
 '{"logic": "AND", "conditions": [{"field": "total_amount", "operator": ">=", "value": 2000000}]}',
 '单笔现金交易金额 >= 200万泰铢',
 'Cash transaction >= 2 million THB',
 'ธุรกรรมเงินสด >= 2 ล้านบาท',
 100, TRUE, FALSE,
 '该交易金额达到200万泰铢，需填写AMLO-1-01报告',
 'Transaction amount reached 2M THB, AMLO-1-01 report required',
 'ยอดธุรกรรม >= 2 ล้านบาท ต้องรายงาน AMLO-1-01',
 NULL, 1, NOW(), NOW());

-- AMLO-1-02：资产交易 >= 800万泰铢
INSERT INTO `trigger_rules` VALUES
(NULL, 'AMLO-1-02-800万THB', 'AMLO-1-02',
 '{"logic": "AND", "conditions": ['
  '{"field": "total_amount", "operator": ">=", "value": 8000000},'
  '{"field": "exchange_type", "operator": "=", "value": "asset_mortgage"}'
 ]}',
 '资产交易金额 >= 800万泰铢',
 'Asset transaction >= 8 million THB',
 'ธุรกรรมทรัพย์สิน >= 8 ล้านบาท',
 100, TRUE, FALSE,
 '该资产交易金额达到800万泰铢，需填写AMLO-1-02报告',
 'Asset transaction amount reached 8M THB, AMLO-1-02 report required',
 'มูลค่าทรัพย์สิน >= 8 ล้านบาท ต้องรายงาน AMLO-1-02',
 NULL, 1, NOW(), NOW());

-- AMLO-1-03：可疑交易（累计金额 + 频率）
INSERT INTO `trigger_rules` VALUES
(NULL, 'AMLO-1-03-累计200万+频率', 'AMLO-1-03',
 '{"logic": "AND", "conditions": [
   {"field": "cumulative_amount_1month", "operator": ">=", "value": 2000000},
   {"field": "transaction_count_1month", "operator": ">=", "value": 10}
 ]}',
 '1个月内累计交易 >= 200万泰铢 且 交易次数 >= 10次',
 'Cumulative 1-month >= 2M THB AND >= 10 transactions',
 'ยอดรวม 1 เดือน >= 2 ล้านบาท และ >= 10 ครั้ง',
 90, TRUE, FALSE,
 '该客户1个月内累计交易达到200万泰铢且交易10次以上，需填写AMLO-1-03可疑交易报告',
 'Customer cumulative 1-month transaction >= 2M THB with >= 10 times, STR report required',
 'ลูกค้ายอดรวม 1 เดือน >= 2 ล้านบาท และ >= 10 ครั้ง ต้องรายงาน STR',
 NULL, 1, NOW(), NOW());

-- AMLO-1-03：资金来源可疑
INSERT INTO `trigger_rules` VALUES
(NULL, 'AMLO-1-03-资金来源', 'AMLO-1-03',
 '{"logic": "OR", "conditions": [
   {"field": "funding_source", "operator": "=", "value": "property_mortgage"},
   {"field": "funding_source", "operator": "=", "value": "land_sale"}
 ]}',
 '资金来源为房产抵押或变卖土地',
 'Funding source: property mortgage or land sale',
 'แหล่งเงิน: จำนองบ้านหรือขายที่ดิน',
 80, TRUE, TRUE,
 '资金来源为房产抵押或变卖土地，可能需要填写STR报告',
 'Funding source indicates potential risk, may need STR report',
 'แหล่งเงินอาจมีความเสี่ยง อาจต้องรายงาน STR',
 NULL, 1, NOW(), NOW());

-- BOT_BuyFX：买入外币 > 2万美元等值
INSERT INTO `trigger_rules` VALUES
(NULL, 'BOT-BuyFX-2万USD等值', 'BOT_BuyFX',
 '{"logic": "AND", "conditions": [
   {"field": "usd_equivalent", "operator": ">", "value": 20000}
 ]}',
 '买入外币金额 > 2万美元等值',
 'Buy FX > USD 20,000 equivalent',
 'ซื้อเงินตรา > 20,000 USD',
 100, TRUE, TRUE,
 '买入外币金额超过2万美元等值，需生成BOT报告',
 'Buy FX amount > USD 20K equivalent, BOT report required',
 'ซื้อเงินตรา > 20,000 USD ต้องรายงาน BOT',
 NULL, 1, NOW(), NOW());

-- BOT_SellFX：卖出外币 > 2万美元等值
INSERT INTO `trigger_rules` VALUES
(NULL, 'BOT-SellFX-2万USD等值', 'BOT_SellFX',
 '{"logic": "AND", "conditions": [
   {"field": "usd_equivalent", "operator": ">", "value": 20000}
 ]}',
 '卖出外币金额 > 2万美元等值',
 'Sell FX > USD 20,000 equivalent',
 'ขายเงินตรา > 20,000 USD',
 100, TRUE, TRUE,
 '卖出外币金额超过2万美元等值，需生成BOT报告',
 'Sell FX amount > USD 20K equivalent, BOT report required',
 'ขายเงินตรา > 20,000 USD ต้องรายงาน BOT',
 NULL, 1, NOW(), NOW());

-- BOT_FCD：FCD账户交易 > 5万美元
INSERT INTO `trigger_rules` VALUES
(NULL, 'BOT-FCD-5万USD', 'BOT_FCD',
 '{"logic": "AND", "conditions": [
   {"field": "use_fcd", "operator": "=", "value": true},
   {"field": "usd_equivalent", "operator": ">", "value": 50000}
 ]}',
 'FCD账户交易 > 5万美元等值',
 'FCD account transaction > USD 50,000',
 'ธุรกรรม FCD > 50,000 USD',
 100, TRUE, TRUE,
 'FCD账户交易金额超过5万美元，需生成FCD报告',
 'FCD transaction > USD 50K, FCD report required',
 'ธุรกรรม FCD > 50,000 USD ต้องรายงาน',
 NULL, 1, NOW(), NOW());

-- ============================================================
-- 5. funding_sources初始化数据
-- ============================================================

INSERT INTO `funding_sources` VALUES
(NULL, 'property_mortgage', '房产抵押', 'Property Mortgage', 'จำนองอสังหาริมทรัพย์', TRUE, 1, TRUE, NOW()),
(NULL, 'land_sale', '变卖土地', 'Land Sale', 'ขายที่ดิน', TRUE, 2, TRUE, NOW()),
(NULL, 'salary', '工资收入', 'Salary', 'เงินเดือน', FALSE, 3, TRUE, NOW()),
(NULL, 'business_income', '经营收入', 'Business Income', 'รายได้ธุรกิจ', FALSE, 4, TRUE, NOW()),
(NULL, 'investment', '投资收益', 'Investment', 'การลงทุน', FALSE, 5, TRUE, NOW()),
(NULL, 'savings', '储蓄', 'Savings', 'เงินออม', FALSE, 6, TRUE, NOW()),
(NULL, 'other', '其他', 'Other', 'อื่นๆ', FALSE, 99, TRUE, NOW());

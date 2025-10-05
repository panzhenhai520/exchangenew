-- ========================================
-- BOT Report Fields Initialization
-- ========================================

-- Clear existing BOT fields
DELETE FROM report_fields WHERE report_type LIKE 'BOT%';

-- ========================================
-- BOT Buy FX Report (Shortened name)
-- ========================================

INSERT INTO report_fields (field_name, field_type, field_length, field_cn_name, field_en_name, field_th_name, report_type, field_group, fill_order, is_required, is_active) VALUES
('report_date', 'DATE', NULL, '报告日期', 'Report Date', 'วันที่รายงาน', 'BOT-BUY-FX', '报告信息', 1, 1, 1),
('transaction_number', 'VARCHAR', 50, '交易编号', 'Transaction Number', 'เลขที่ธุรกรรม', 'BOT-BUY-FX', '交易信息', 10, 1, 1),
('transaction_date', 'DATE', NULL, '交易日期', 'Transaction Date', 'วันที่ทำธุรกรรม', 'BOT-BUY-FX', '交易信息', 11, 1, 1),
('transaction_time', 'TIME', NULL, '交易时间', 'Transaction Time', 'เวลา', 'BOT-BUY-FX', '交易信息', 12, 0, 1),
('customer_id', 'VARCHAR', 20, '客户证件号', 'Customer ID', 'เลขประจำตัว', 'BOT-BUY-FX', '客户信息', 20, 1, 1),
('customer_name', 'VARCHAR', 200, '客户姓名', 'Customer Name', 'ชื่อลูกค้า', 'BOT-BUY-FX', '客户信息', 21, 1, 1),
('customer_type', 'VARCHAR', 50, '客户类型', 'Customer Type', 'ประเภทลูกค้า', 'BOT-BUY-FX', '客户信息', 22, 1, 1),
('currency_code', 'VARCHAR', 10, '货币代码', 'Currency Code', 'สกุลเงิน', 'BOT-BUY-FX', '货币信息', 30, 1, 1),
('currency_name', 'VARCHAR', 100, '货币名称', 'Currency Name', 'ชื่อสกุลเงิน', 'BOT-BUY-FX', '货币信息', 31, 0, 1),
('foreign_amount', 'DECIMAL', NULL, '外币金额', 'Foreign Amount', 'จำนวนเงินต่างประเทศ', 'BOT-BUY-FX', '货币信息', 32, 1, 1),
('exchange_rate', 'DECIMAL', NULL, '汇率', 'Exchange Rate', 'อัตราแลกเปลี่ยน', 'BOT-BUY-FX', '货币信息', 33, 1, 1),
('thb_amount', 'DECIMAL', NULL, '泰铢金额', 'THB Amount', 'จำนวนเงินบาท', 'BOT-BUY-FX', '货币信息', 34, 1, 1),
('exchange_type', 'VARCHAR', 50, '兑换类型', 'Exchange Type', 'ประเภทการแลกเปลี่ยน', 'BOT-BUY-FX', '交易信息', 40, 0, 1),
('transaction_purpose', 'VARCHAR', 200, '交易目的', 'Transaction Purpose', 'วัตถุประสงค์', 'BOT-BUY-FX', '交易信息', 41, 0, 1),
('funding_source', 'VARCHAR', 200, '资金来源', 'Funding Source', 'ที่มาของเงิน', 'BOT-BUY-FX', '交易信息', 42, 0, 1),
('operator_id', 'VARCHAR', 20, '操作员ID', 'Operator ID', 'รหัสผู้ทำรายการ', 'BOT-BUY-FX', '操作信息', 50, 0, 1),
('operator_name', 'VARCHAR', 100, '操作员姓名', 'Operator Name', 'ชื่อผู้ทำรายการ', 'BOT-BUY-FX', '操作信息', 51, 0, 1),
('branch_id', 'VARCHAR', 20, '分行代码', 'Branch ID', 'รหัสสาขา', 'BOT-BUY-FX', '分行信息', 60, 1, 1),
('branch_name', 'VARCHAR', 200, '分行名称', 'Branch Name', 'ชื่อสาขา', 'BOT-BUY-FX', '分行信息', 61, 0, 1);

-- ========================================
-- BOT Sell FX Report
-- ========================================

INSERT INTO report_fields (field_name, field_type, field_length, field_cn_name, field_en_name, field_th_name, report_type, field_group, fill_order, is_required, is_active) VALUES
('report_date', 'DATE', NULL, '报告日期', 'Report Date', 'วันที่รายงาน', 'BOT-SELL-FX', '报告信息', 1, 1, 1),
('transaction_number', 'VARCHAR', 50, '交易编号', 'Transaction Number', 'เลขที่ธุรกรรม', 'BOT-SELL-FX', '交易信息', 10, 1, 1),
('transaction_date', 'DATE', NULL, '交易日期', 'Transaction Date', 'วันที่ทำธุรกรรม', 'BOT-SELL-FX', '交易信息', 11, 1, 1),
('transaction_time', 'TIME', NULL, '交易时间', 'Transaction Time', 'เวลา', 'BOT-SELL-FX', '交易信息', 12, 0, 1),
('customer_id', 'VARCHAR', 20, '客户证件号', 'Customer ID', 'เลขประจำตัว', 'BOT-SELL-FX', '客户信息', 20, 1, 1),
('customer_name', 'VARCHAR', 200, '客户姓名', 'Customer Name', 'ชื่อลูกค้า', 'BOT-SELL-FX', '客户信息', 21, 1, 1),
('customer_type', 'VARCHAR', 50, '客户类型', 'Customer Type', 'ประเภทลูกค้า', 'BOT-SELL-FX', '客户信息', 22, 1, 1),
('currency_code', 'VARCHAR', 10, '货币代码', 'Currency Code', 'สกุลเงิน', 'BOT-SELL-FX', '货币信息', 30, 1, 1),
('currency_name', 'VARCHAR', 100, '货币名称', 'Currency Name', 'ชื่อสกุลเงิน', 'BOT-SELL-FX', '货币信息', 31, 0, 1),
('foreign_amount', 'DECIMAL', NULL, '外币金额', 'Foreign Amount', 'จำนวนเงินต่างประเทศ', 'BOT-SELL-FX', '货币信息', 32, 1, 1),
('exchange_rate', 'DECIMAL', NULL, '汇率', 'Exchange Rate', 'อัตราแลกเปลี่ยน', 'BOT-SELL-FX', '货币信息', 33, 1, 1),
('thb_amount', 'DECIMAL', NULL, '泰铢金额', 'THB Amount', 'จำนวนเงินบาท', 'BOT-SELL-FX', '货币信息', 34, 1, 1),
('exchange_type', 'VARCHAR', 50, '兑换类型', 'Exchange Type', 'ประเภทการแลกเปลี่ยน', 'BOT-SELL-FX', '交易信息', 40, 0, 1),
('transaction_purpose', 'VARCHAR', 200, '交易目的', 'Transaction Purpose', 'วัตถุประสงค์', 'BOT-SELL-FX', '交易信息', 41, 0, 1),
('payment_destination', 'VARCHAR', 200, '收款目的地', 'Payment Destination', 'จุดหมายปลายทาง', 'BOT-SELL-FX', '交易信息', 42, 0, 1),
('operator_id', 'VARCHAR', 20, '操作员ID', 'Operator ID', 'รหัสผู้ทำรายการ', 'BOT-SELL-FX', '操作信息', 50, 0, 1),
('operator_name', 'VARCHAR', 100, '操作员姓名', 'Operator Name', 'ชื่อผู้ทำรายการ', 'BOT-SELL-FX', '操作信息', 51, 0, 1),
('branch_id', 'VARCHAR', 20, '分行代码', 'Branch ID', 'รหัสสาขา', 'BOT-SELL-FX', '分行信息', 60, 1, 1),
('branch_name', 'VARCHAR', 200, '分行名称', 'Branch Name', 'ชื่อสาขา', 'BOT-SELL-FX', '分行信息', 61, 0, 1);

-- Update timestamp
UPDATE report_fields SET created_at = NOW() WHERE created_at IS NULL;

-- Migration 008: Create report_fields table for dynamic AMLO/BOT report configuration
-- Created: 2025-10-18
-- Purpose: Support dynamic field configuration for AMLO-1-01/1-02/1-03 and BOT reports

CREATE TABLE IF NOT EXISTS report_fields (
    id INT PRIMARY KEY AUTO_INCREMENT,
    report_type VARCHAR(50) NOT NULL COMMENT '报告类型(AMLO-1-01/AMLO-1-02/AMLO-1-03/BOT_BuyFX等)',
    field_name VARCHAR(100) NOT NULL COMMENT '字段名称',
    field_name_cn VARCHAR(200) COMMENT '字段中文名',
    field_name_en VARCHAR(200) COMMENT '字段英文名',
    field_name_th VARCHAR(200) COMMENT '字段泰文名',
    field_type VARCHAR(50) DEFAULT 'text' COMMENT '字段类型(text/number/date/select/textarea/checkbox等)',
    field_length INT COMMENT '字段长度',
    field_options TEXT COMMENT '字段选项(JSON格式,用于select/radio/checkbox)',
    display_order INT DEFAULT 0 COMMENT '填写顺序',
    display_section VARCHAR(100) COMMENT '显示分组(basic_info/transaction_detail/compliance等)',
    is_required BOOLEAN DEFAULT FALSE COMMENT '是否必填',
    is_readonly BOOLEAN DEFAULT FALSE COMMENT '是否只读',
    default_value VARCHAR(500) COMMENT '默认值',
    validation_rule VARCHAR(500) COMMENT '验证规则(正则表达式或JSON)',
    help_text_cn TEXT COMMENT '帮助文本中文',
    help_text_en TEXT COMMENT '帮助文本英文',
    help_text_th TEXT COMMENT '帮助文本泰文',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_report_type (report_type),
    INDEX idx_display_order (display_order),
    UNIQUE KEY unique_report_field (report_type, field_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='报告字段定义表';

-- Insert initial field definitions for AMLO-1-01 (CTR - Cash Transaction Report)
INSERT INTO report_fields (report_type, field_name, field_name_cn, field_name_en, field_name_th, field_type, display_order, display_section, is_required) VALUES
('AMLO-1-01', 'customer_id', '客户证件号', 'Customer ID', 'หมายเลขบัตรประชาชน', 'text', 1, 'basic_info', TRUE),
('AMLO-1-01', 'customer_name', '客户姓名', 'Customer Name', 'ชื่อลูกค้า', 'text', 2, 'basic_info', TRUE),
('AMLO-1-01', 'transaction_date', '交易日期', 'Transaction Date', 'วันที่ทำรายการ', 'date', 3, 'transaction_detail', TRUE),
('AMLO-1-01', 'transaction_amount', '交易金额', 'Transaction Amount', 'จำนวนเงิน', 'number', 4, 'transaction_detail', TRUE),
('AMLO-1-01', 'currency_code', '币种', 'Currency', 'สกุลเงิน', 'select', 5, 'transaction_detail', TRUE),
('AMLO-1-01', 'exchange_type', '兑换类型', 'Exchange Type', 'ประเภทการแลกเปลี่ยน', 'select', 6, 'transaction_detail', TRUE),
('AMLO-1-01', 'purpose', '兑换目的', 'Purpose', 'วัตถุประสงค์', 'textarea', 7, 'transaction_detail', FALSE),
('AMLO-1-01', 'branch_name', '网点名称', 'Branch Name', 'ชื่อสาขา', 'text', 8, 'basic_info', TRUE),
('AMLO-1-01', 'operator_name', '操作员', 'Operator', 'ผู้ดำเนินการ', 'text', 9, 'basic_info', TRUE);

-- Insert initial field definitions for AMLO-1-02 (ATR - Asset Transaction Report)
INSERT INTO report_fields (report_type, field_name, field_name_cn, field_name_en, field_name_th, field_type, display_order, display_section, is_required) VALUES
('AMLO-1-02', 'customer_id', '客户证件号', 'Customer ID', 'หมายเลขบัตรประชาชน', 'text', 1, 'basic_info', TRUE),
('AMLO-1-02', 'customer_name', '客户姓名', 'Customer Name', 'ชื่อลูกค้า', 'text', 2, 'basic_info', TRUE),
('AMLO-1-02', 'transaction_date', '交易日期', 'Transaction Date', 'วันที่ทำรายการ', 'date', 3, 'transaction_detail', TRUE),
('AMLO-1-02', 'transaction_amount', '交易金额', 'Transaction Amount', 'จำนวนเงิน', 'number', 4, 'transaction_detail', TRUE),
('AMLO-1-02', 'asset_type', '资产类型', 'Asset Type', 'ประเภททรัพย์สิน', 'select', 5, 'asset_detail', TRUE),
('AMLO-1-02', 'asset_description', '资产描述', 'Asset Description', 'คำอธิบายทรัพย์สิน', 'textarea', 6, 'asset_detail', TRUE),
('AMLO-1-02', 'asset_value', '资产估值', 'Asset Value', 'มูลค่าทรัพย์สิน', 'number', 7, 'asset_detail', TRUE),
('AMLO-1-02', 'branch_name', '网点名称', 'Branch Name', 'ชื่อสาขา', 'text', 8, 'basic_info', TRUE),
('AMLO-1-02', 'operator_name', '操作员', 'Operator', 'ผู้ดำเนินการ', 'text', 9, 'basic_info', TRUE);

-- Insert initial field definitions for AMLO-1-03 (STR - Suspicious Transaction Report)
INSERT INTO report_fields (report_type, field_name, field_name_cn, field_name_en, field_name_th, field_type, display_order, display_section, is_required) VALUES
('AMLO-1-03', 'customer_id', '客户证件号', 'Customer ID', 'หมายเลขบัตรประชาชน', 'text', 1, 'basic_info', TRUE),
('AMLO-1-03', 'customer_name', '客户姓名', 'Customer Name', 'ชื่อลูกค้า', 'text', 2, 'basic_info', TRUE),
('AMLO-1-03', 'suspicious_pattern', '可疑模式', 'Suspicious Pattern', 'รูปแบบที่น่าสงสัย', 'select', 3, 'suspicious_detail', TRUE),
('AMLO-1-03', 'cumulative_amount', '累计金额(30天)', 'Cumulative Amount (30 days)', 'ยอดรวม (30 วัน)', 'number', 4, 'transaction_detail', TRUE),
('AMLO-1-03', 'transaction_count', '交易次数', 'Transaction Count', 'จำนวนรายการ', 'number', 5, 'transaction_detail', TRUE),
('AMLO-1-03', 'suspicious_reason', '可疑原因', 'Reason for Suspicion', 'เหตุผลที่น่าสงสัย', 'textarea', 6, 'suspicious_detail', TRUE),
('AMLO-1-03', 'investigation_notes', '调查备注', 'Investigation Notes', 'บันทึกการสอบสวน', 'textarea', 7, 'suspicious_detail', FALSE),
('AMLO-1-03', 'branch_name', '网点名称', 'Branch Name', 'ชื่อสาขา', 'text', 8, 'basic_info', TRUE),
('AMLO-1-03', 'operator_name', '操作员', 'Operator', 'ผู้ดำเนินการ', 'text', 9, 'basic_info', TRUE);

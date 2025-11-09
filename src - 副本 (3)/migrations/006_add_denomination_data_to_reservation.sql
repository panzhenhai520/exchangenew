-- Migration: 006 Add denomination_data field to Reserved_Transaction
-- Purpose: Store denomination combinations for reservations
-- Date: 2025-01-03

-- Add denomination_data field to store face value combinations
ALTER TABLE Reserved_Transaction
ADD COLUMN denomination_data TEXT COMMENT '面值组合数据(JSON格式)' AFTER form_data;

-- Add previous_report_number for tracking amendments
ALTER TABLE Reserved_Transaction
ADD COLUMN previous_report_number VARCHAR(100) COMMENT '原报告编号（修改/重新提交时）' AFTER denomination_data;

-- Add remarks for additional notes
ALTER TABLE Reserved_Transaction
ADD COLUMN remarks TEXT COMMENT '备注信息' AFTER previous_report_number;

-- Add updated_at timestamp
ALTER TABLE Reserved_Transaction
ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间' AFTER created_at;

-- Verify the changes
DESCRIBE Reserved_Transaction;

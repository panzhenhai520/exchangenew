-- Migration: 005 - Add receipt, payment method and country fields
-- Date: 2025-10-01
-- Description:
-- 1. Add company_full_name and tax_registration_number to branches table
-- 2. Add payment_method and payment_method_note to exchange_transactions table
-- 3. Create countries table with multi-language support (zh-CN, en-US, th-TH)

-- Step 1: Add receipt information fields to branches table
ALTER TABLE `branches`
ADD COLUMN `company_full_name` VARCHAR(255) NULL COMMENT 'Company full name for receipts' AFTER `base_currency_id`,
ADD COLUMN `tax_registration_number` VARCHAR(100) NULL COMMENT 'Tax registration number' AFTER `company_full_name`;

-- Step 2: Add payment method fields to exchange_transactions table
ALTER TABLE `exchange_transactions`
ADD COLUMN `payment_method` VARCHAR(50) NOT NULL DEFAULT 'cash' COMMENT 'Payment method: cash, instrument_cheque, instrument_draft, instrument_other, other' AFTER `remarks`,
ADD COLUMN `payment_method_note` VARCHAR(200) NULL COMMENT 'Additional note for payment method (especially for "other")' AFTER `payment_method`;

-- Step 3: Create countries table with multi-language support
CREATE TABLE IF NOT EXISTS `countries` (
  `id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `country_code` VARCHAR(2) NOT NULL COMMENT 'ISO 3166-1 alpha-2 country code',
  `country_name_zh` VARCHAR(100) NOT NULL COMMENT 'Country name in Chinese',
  `country_name_en` VARCHAR(100) NOT NULL COMMENT 'Country name in English',
  `country_name_th` VARCHAR(100) NULL COMMENT 'Country name in Thai',
  `phone_code` VARCHAR(10) NULL COMMENT 'International phone code',
  `currency_code` VARCHAR(3) NULL COMMENT 'Primary currency code (ISO 4217)',
  `is_active` TINYINT(1) NOT NULL DEFAULT 1 COMMENT 'Is country active for selection',
  `sort_order` INT NOT NULL DEFAULT 0 COMMENT 'Display order (smaller numbers first)',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY `uk_country_code` (`country_code`),
  KEY `idx_is_active` (`is_active`),
  KEY `idx_sort_order` (`sort_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Countries table with multi-language support';

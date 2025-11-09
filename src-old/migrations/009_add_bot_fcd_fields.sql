-- Migration 009: Add BOT/FCD tracking fields to exchange_transactions
-- Created: 2025-10-18
-- Purpose: Support BOT reporting requirements and FCD account tracking

-- Check if columns exist before adding them (to make migration idempotent)
SET @db_name = DATABASE();

-- Add bot_flag field (BOT报告标记)
SET @column_exists = (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = @db_name
        AND TABLE_NAME = 'exchange_transactions'
        AND COLUMN_NAME = 'bot_flag'
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE exchange_transactions ADD COLUMN bot_flag INT DEFAULT 0 COMMENT ''BOT报告标记: 0=未生成, 1=已生成, 2=已上报''',
    'SELECT ''Column bot_flag already exists'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add fcd_flag field (FCD报告标记)
SET @column_exists = (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = @db_name
        AND TABLE_NAME = 'exchange_transactions'
        AND COLUMN_NAME = 'fcd_flag'
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE exchange_transactions ADD COLUMN fcd_flag INT DEFAULT 0 COMMENT ''FCD报告标记: 0=非FCD, 1=涉及FCD账户''',
    'SELECT ''Column fcd_flag already exists'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add seqno field (当日交易序列号)
SET @column_exists = (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = @db_name
        AND TABLE_NAME = 'exchange_transactions'
        AND COLUMN_NAME = 'seqno'
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE exchange_transactions ADD COLUMN seqno INT DEFAULT 0 COMMENT ''当日交易序列号(每日重置)''',
    'SELECT ''Column seqno already exists'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add use_fcd field (是否使用FCD账户)
SET @column_exists = (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = @db_name
        AND TABLE_NAME = 'exchange_transactions'
        AND COLUMN_NAME = 'use_fcd'
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE exchange_transactions ADD COLUMN use_fcd BOOLEAN DEFAULT FALSE COMMENT ''是否使用FCD账户: 买入时是否存入FCD/卖出时是否从FCD支付''',
    'SELECT ''Column use_fcd already exists'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add exchange_type field if it doesn't exist (大额兑换 vs 资产抵押兑换)
SET @column_exists = (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = @db_name
        AND TABLE_NAME = 'exchange_transactions'
        AND COLUMN_NAME = 'exchange_type'
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE exchange_transactions ADD COLUMN exchange_type VARCHAR(50) DEFAULT ''normal'' COMMENT ''兑换类型: normal=大额兑换, asset_backed=资产抵押兑换''',
    'SELECT ''Column exchange_type already exists'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Create indexes for better query performance
SET @index_exists = (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.STATISTICS
    WHERE TABLE_SCHEMA = @db_name
        AND TABLE_NAME = 'exchange_transactions'
        AND INDEX_NAME = 'idx_bot_flag'
);

SET @sql = IF(@index_exists = 0,
    'CREATE INDEX idx_bot_flag ON exchange_transactions(bot_flag, transaction_date)',
    'SELECT ''Index idx_bot_flag already exists'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @index_exists = (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.STATISTICS
    WHERE TABLE_SCHEMA = @db_name
        AND TABLE_NAME = 'exchange_transactions'
        AND INDEX_NAME = 'idx_fcd_flag'
);

SET @sql = IF(@index_exists = 0,
    'CREATE INDEX idx_fcd_flag ON exchange_transactions(fcd_flag, transaction_date)',
    'SELECT ''Index idx_fcd_flag already exists'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @index_exists = (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.STATISTICS
    WHERE TABLE_SCHEMA = @db_name
        AND TABLE_NAME = 'exchange_transactions'
        AND INDEX_NAME = 'idx_seqno'
);

SET @sql = IF(@index_exists = 0,
    'CREATE INDEX idx_seqno ON exchange_transactions(transaction_date, seqno)',
    'SELECT ''Index idx_seqno already exists'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Verify columns were added
SELECT
    'exchange_transactions columns added/verified:' AS status,
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
     WHERE TABLE_SCHEMA = @db_name AND TABLE_NAME = 'exchange_transactions' AND COLUMN_NAME = 'bot_flag') AS bot_flag,
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
     WHERE TABLE_SCHEMA = @db_name AND TABLE_NAME = 'exchange_transactions' AND COLUMN_NAME = 'fcd_flag') AS fcd_flag,
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
     WHERE TABLE_SCHEMA = @db_name AND TABLE_NAME = 'exchange_transactions' AND COLUMN_NAME = 'seqno') AS seqno,
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
     WHERE TABLE_SCHEMA = @db_name AND TABLE_NAME = 'exchange_transactions' AND COLUMN_NAME = 'use_fcd') AS use_fcd,
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
     WHERE TABLE_SCHEMA = @db_name AND TABLE_NAME = 'exchange_transactions' AND COLUMN_NAME = 'exchange_type') AS exchange_type;

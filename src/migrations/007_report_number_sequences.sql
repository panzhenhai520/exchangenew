-- ============================================================
-- 报告编号序列表迁移脚本
-- 创建时间: 2025-10-15
-- 描述: 添加AMLO和BOT报告编号序列表，支持并发安全的唯一编号生成
-- ============================================================

-- 1. AMLO报告编号序列表
DROP TABLE IF EXISTS `amlo_report_sequences`;
CREATE TABLE `amlo_report_sequences` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '序列ID',
    `branch_id` INT NOT NULL COMMENT '网点ID',
    `currency_code` VARCHAR(3) NOT NULL COMMENT '币种代码(ISO 4217)',
    `year_month` VARCHAR(7) NOT NULL COMMENT '年月(YYYY-MM)',
    `current_sequence` INT NOT NULL DEFAULT 0 COMMENT '当前序列号',
    `last_used_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '最后使用时间',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 唯一约束：每个网点+币种+年月只能有一个序列
    UNIQUE KEY `uk_branch_currency_month` (`branch_id`, `currency_code`, `year_month`),
    KEY `idx_branch_currency_month` (`branch_id`, `currency_code`, `year_month`),
    KEY `idx_year_month` (`year_month`),
    
    -- 外键约束
    FOREIGN KEY (`branch_id`) REFERENCES `branch`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AMLO报告编号序列表';

-- 2. BOT报告编号序列表
DROP TABLE IF EXISTS `bot_report_sequences`;
CREATE TABLE `bot_report_sequences` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '序列ID',
    `branch_id` INT NOT NULL COMMENT '网点ID',
    `report_type` VARCHAR(20) NOT NULL COMMENT '报告类型(BuyFX/SellFX/FCD)',
    `year_month` VARCHAR(7) NOT NULL COMMENT '年月(YYYY-MM)',
    `current_sequence` INT NOT NULL DEFAULT 0 COMMENT '当前序列号',
    `last_used_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '最后使用时间',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 唯一约束：每个网点+报告类型+年月只能有一个序列
    UNIQUE KEY `uk_branch_type_month` (`branch_id`, `report_type`, `year_month`),
    KEY `idx_branch_type_month` (`branch_id`, `report_type`, `year_month`),
    KEY `idx_year_month` (`year_month`),
    
    -- 外键约束
    FOREIGN KEY (`branch_id`) REFERENCES `branch`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='BOT报告编号序列表';

-- 3. 报告编号使用日志表
DROP TABLE IF EXISTS `report_number_logs`;
CREATE TABLE `report_number_logs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '日志ID',
    `report_number` VARCHAR(50) NOT NULL COMMENT '生成的报告编号',
    `report_type` VARCHAR(20) NOT NULL COMMENT '报告类型(AMLO/BOT)',
    `branch_id` INT NOT NULL COMMENT '网点ID',
    `currency_code` VARCHAR(3) NULL COMMENT '币种代码(仅AMLO报告)',
    `sequence_id` INT NOT NULL COMMENT '关联的序列记录ID',
    `transaction_id` INT NULL COMMENT '关联的交易ID',
    `operator_id` INT NOT NULL COMMENT '操作员ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    -- 索引
    KEY `idx_report_number` (`report_number`),
    KEY `idx_branch_date` (`branch_id`, `created_at`),
    KEY `idx_sequence_id` (`sequence_id`),
    
    -- 外键约束
    FOREIGN KEY (`branch_id`) REFERENCES `branch`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`operator_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='报告编号使用日志表';

-- 4. 为现有网点初始化AMLO代码（如果为空）
UPDATE `branch` 
SET `amlo_institution_code` = '001' 
WHERE `amlo_institution_code` IS NULL OR `amlo_institution_code` = '';

UPDATE `branch` 
SET `amlo_branch_code` = '001' 
WHERE `amlo_branch_code` IS NULL OR `amlo_branch_code` = '';

-- 5. 创建存储过程：清理过期的序列记录（可选）
DELIMITER $$

CREATE PROCEDURE CleanupExpiredSequences()
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- 删除6个月前的序列记录
    DELETE FROM `amlo_report_sequences` 
    WHERE `year_month` < DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL 6 MONTH), '%Y-%m');
    
    DELETE FROM `bot_report_sequences` 
    WHERE `year_month` < DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL 6 MONTH), '%Y-%m');
    
    -- 删除6个月前的日志记录
    DELETE FROM `report_number_logs` 
    WHERE `created_at` < DATE_SUB(CURDATE(), INTERVAL 6 MONTH);
    
    COMMIT;
    
    SELECT 'Expired sequences cleaned up successfully' AS result;
END$$

DELIMITER ;

-- 6. 创建事件调度器：每月自动清理过期记录（可选）
-- 注意：需要确保MySQL的事件调度器已启用 (SET GLOBAL event_scheduler = ON;)

/*
CREATE EVENT IF NOT EXISTS `cleanup_expired_sequences`
ON SCHEDULE EVERY 1 MONTH
STARTS '2025-11-01 02:00:00'
DO
    CALL CleanupExpiredSequences();
*/

-- 7. 插入测试数据（可选）
-- 为测试网点A005插入一些初始序列记录
INSERT INTO `amlo_report_sequences` (`branch_id`, `currency_code`, `year_month`, `current_sequence`) 
SELECT 
    b.id,
    'USD',
    DATE_FORMAT(CURDATE(), '%Y-%m'),
    0
FROM `branch` b 
WHERE b.branch_code = 'A005'
ON DUPLICATE KEY UPDATE `current_sequence` = `current_sequence`;

INSERT INTO `amlo_report_sequences` (`branch_id`, `currency_code`, `year_month`, `current_sequence`) 
SELECT 
    b.id,
    'EUR',
    DATE_FORMAT(CURDATE(), '%Y-%m'),
    0
FROM `branch` b 
WHERE b.branch_code = 'A005'
ON DUPLICATE KEY UPDATE `current_sequence` = `current_sequence`;

-- 完成
SELECT 'Report number sequences tables created successfully' AS result;




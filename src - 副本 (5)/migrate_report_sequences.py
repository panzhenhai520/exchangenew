#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报告编号序列表迁移脚本
"""

import sys
import os
sys.path.append('.')

from services.db_service import DatabaseService
from sqlalchemy import text

def create_report_sequence_tables():
    """创建报告编号序列表"""
    session = DatabaseService.get_session()
    
    try:
        # 创建AMLO报告编号序列表
        session.execute(text('''
            CREATE TABLE IF NOT EXISTS amlo_report_sequences (
                id INT AUTO_INCREMENT PRIMARY KEY COMMENT '序列ID',
                branch_id INT NOT NULL COMMENT '网点ID',
                currency_code VARCHAR(3) NOT NULL COMMENT '币种代码(ISO 4217)',
                year_month VARCHAR(7) NOT NULL COMMENT '年月(YYYY-MM)',
                current_sequence INT NOT NULL DEFAULT 0 COMMENT '当前序列号',
                last_used_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '最后使用时间',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                UNIQUE KEY uk_branch_currency_month (branch_id, currency_code, year_month),
                KEY idx_branch_currency_month (branch_id, currency_code, year_month),
                KEY idx_year_month (year_month)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AMLO报告编号序列表'
        '''))
        print('AMLO报告编号序列表创建成功')
        
        # 创建BOT报告编号序列表
        session.execute(text('''
            CREATE TABLE IF NOT EXISTS bot_report_sequences (
                id INT AUTO_INCREMENT PRIMARY KEY COMMENT '序列ID',
                branch_id INT NOT NULL COMMENT '网点ID',
                report_type VARCHAR(20) NOT NULL COMMENT '报告类型(BuyFX/SellFX/FCD)',
                year_month VARCHAR(7) NOT NULL COMMENT '年月(YYYY-MM)',
                current_sequence INT NOT NULL DEFAULT 0 COMMENT '当前序列号',
                last_used_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '最后使用时间',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                UNIQUE KEY uk_branch_type_month (branch_id, report_type, year_month),
                KEY idx_branch_type_month (branch_id, report_type, year_month),
                KEY idx_year_month (year_month)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='BOT报告编号序列表'
        '''))
        print('BOT报告编号序列表创建成功')
        
        # 创建报告编号使用日志表
        session.execute(text('''
            CREATE TABLE IF NOT EXISTS report_number_logs (
                id INT AUTO_INCREMENT PRIMARY KEY COMMENT '日志ID',
                report_number VARCHAR(50) NOT NULL COMMENT '生成的报告编号',
                report_type VARCHAR(20) NOT NULL COMMENT '报告类型(AMLO/BOT)',
                branch_id INT NOT NULL COMMENT '网点ID',
                currency_code VARCHAR(3) NULL COMMENT '币种代码(仅AMLO报告)',
                sequence_id INT NOT NULL COMMENT '关联的序列记录ID',
                transaction_id INT NULL COMMENT '关联的交易ID',
                operator_id INT NOT NULL COMMENT '操作员ID',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                KEY idx_report_number (report_number),
                KEY idx_branch_date (branch_id, created_at),
                KEY idx_sequence_id (sequence_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='报告编号使用日志表'
        '''))
        print('报告编号使用日志表创建成功')
        
        # 初始化网点AMLO代码（如果为空）
        session.execute(text('''
            UPDATE branch 
            SET amlo_institution_code = '001' 
            WHERE amlo_institution_code IS NULL OR amlo_institution_code = ''
        '''))
        
        session.execute(text('''
            UPDATE branch 
            SET amlo_branch_code = '001' 
            WHERE amlo_branch_code IS NULL OR amlo_branch_code = ''
        '''))
        print('网点AMLO代码初始化完成')
        
        session.commit()
        print('所有表创建完成！')
        
    except Exception as e:
        session.rollback()
        print(f'创建表失败: {e}')
        raise e
    finally:
        session.close()

if __name__ == '__main__':
    create_report_sequence_tables()

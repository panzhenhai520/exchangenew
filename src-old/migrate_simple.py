#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append('.')

from services.db_service import DatabaseService
from sqlalchemy import text

def create_tables():
    session = DatabaseService.get_session()
    
    try:
        # Create AMLO report sequences table
        session.execute(text('''
            CREATE TABLE IF NOT EXISTS amlo_report_sequences (
                id INT AUTO_INCREMENT PRIMARY KEY,
                branch_id INT NOT NULL,
                currency_code VARCHAR(3) NOT NULL,
                `year_month` VARCHAR(7) NOT NULL,
                current_sequence INT NOT NULL DEFAULT 0,
                last_used_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uk_branch_currency_month (branch_id, currency_code, `year_month`),
                KEY idx_branch_currency_month (branch_id, currency_code, `year_month`),
                KEY idx_year_month (`year_month`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        '''))
        print('AMLO report sequences table created')
        
        # Create BOT report sequences table
        session.execute(text('''
            CREATE TABLE IF NOT EXISTS bot_report_sequences (
                id INT AUTO_INCREMENT PRIMARY KEY,
                branch_id INT NOT NULL,
                report_type VARCHAR(20) NOT NULL,
                `year_month` VARCHAR(7) NOT NULL,
                current_sequence INT NOT NULL DEFAULT 0,
                last_used_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uk_branch_type_month (branch_id, report_type, `year_month`),
                KEY idx_branch_type_month (branch_id, report_type, `year_month`),
                KEY idx_year_month (`year_month`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        '''))
        print('BOT report sequences table created')
        
        # Create report number logs table
        session.execute(text('''
            CREATE TABLE IF NOT EXISTS report_number_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                report_number VARCHAR(50) NOT NULL,
                report_type VARCHAR(20) NOT NULL,
                branch_id INT NOT NULL,
                currency_code VARCHAR(3) NULL,
                sequence_id INT NOT NULL,
                transaction_id INT NULL,
                operator_id INT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                KEY idx_report_number (report_number),
                KEY idx_branch_date (branch_id, created_at),
                KEY idx_sequence_id (sequence_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        '''))
        print('Report number logs table created')
        
        # Skip branch initialization for now
        print('Branch AMLO codes initialization skipped')
        
        session.commit()
        print('All tables created successfully!')
        
    except Exception as e:
        session.rollback()
        print(f'Error: {e}')
        raise e
    finally:
        session.close()

if __name__ == '__main__':
    create_tables()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加交易报警事件表
创建时间: 2025-01-05
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from services.db_service import engine

def upgrade():
    """添加transaction_alerts表"""
    try:
        # 创建transaction_alerts表
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS transaction_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            branch_id INTEGER NOT NULL,
            currency_id INTEGER NOT NULL,
            operator_id INTEGER NOT NULL,
            alert_type VARCHAR(50) NOT NULL,
            alert_level VARCHAR(20) NOT NULL,
            current_balance DECIMAL(15,2) NOT NULL,
            threshold_value DECIMAL(15,2),
            transaction_amount DECIMAL(15,2) NOT NULL,
            transaction_type VARCHAR(20) NOT NULL,
            after_balance DECIMAL(15,2) NOT NULL,
            message TEXT NOT NULL,
            is_resolved BOOLEAN DEFAULT 0 NOT NULL,
            resolved_at DATETIME,
            resolved_by INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (branch_id) REFERENCES branches(id),
            FOREIGN KEY (currency_id) REFERENCES currencies(id),
            FOREIGN KEY (operator_id) REFERENCES operators(id),
            FOREIGN KEY (resolved_by) REFERENCES operators(id)
        );
        """
        
        with engine.begin() as conn:  # 使用事务
            conn.execute(text(create_table_sql))
            print("✅ transaction_alerts表创建成功")
            
        # 添加索引以提高查询性能
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_transaction_alerts_branch_id ON transaction_alerts(branch_id);",
            "CREATE INDEX IF NOT EXISTS idx_transaction_alerts_currency_id ON transaction_alerts(currency_id);", 
            "CREATE INDEX IF NOT EXISTS idx_transaction_alerts_operator_id ON transaction_alerts(operator_id);",
            "CREATE INDEX IF NOT EXISTS idx_transaction_alerts_created_at ON transaction_alerts(created_at);",
            "CREATE INDEX IF NOT EXISTS idx_transaction_alerts_is_resolved ON transaction_alerts(is_resolved);",
            "CREATE INDEX IF NOT EXISTS idx_transaction_alerts_alert_level ON transaction_alerts(alert_level);"
        ]
        
        with engine.begin() as conn:  # 使用事务
            for index_sql in indexes:
                conn.execute(text(index_sql))
            print("✅ 索引创建成功")
            
    except Exception as e:
        print(f"❌ 创建transaction_alerts表失败: {e}")
        raise

def downgrade():
    """删除transaction_alerts表"""
    try:
        with engine.begin() as conn:  # 使用事务
            conn.execute(text("DROP TABLE IF EXISTS transaction_alerts;"))
            print("✅ transaction_alerts表删除成功")
            
    except Exception as e:
        print(f"❌ 删除transaction_alerts表失败: {e}")
        raise

if __name__ == '__main__':
    print("开始添加交易报警事件表...")
    upgrade()
    print("迁移完成！") 
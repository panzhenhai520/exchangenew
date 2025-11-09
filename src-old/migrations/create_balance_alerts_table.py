#!/usr/bin/env python3
"""
创建网点余额报警设置表
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from models.exchange_models import Base, BranchBalanceAlert
from sqlalchemy import text

def create_balance_alerts_table():
    """创建余额报警设置表"""
    session = DatabaseService.get_session()
    
    try:
        # 检查表是否已存在
        result = session.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='branch_balance_alerts'
        """)).fetchone()
        
        if result:
            print("✅ branch_balance_alerts 表已存在，跳过创建")
            return True
        
        # 创建表
        print("🔄 创建 branch_balance_alerts 表...")
        
        # 使用原始SQL创建表以确保精确控制
        create_table_sql = """
        CREATE TABLE branch_balance_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            branch_id INTEGER NOT NULL,
            currency_id INTEGER NOT NULL,
            min_threshold DECIMAL(15, 2),
            max_threshold DECIMAL(15, 2),
            is_active BOOLEAN DEFAULT 1 NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (branch_id) REFERENCES branches(id),
            FOREIGN KEY (currency_id) REFERENCES currencies(id),
            UNIQUE(branch_id, currency_id)
        )
        """
        
        session.execute(text(create_table_sql))
        DatabaseService.commit_session(session)
        
        print("✅ branch_balance_alerts 表创建成功")
        
        # 验证表结构
        columns = session.execute(text("PRAGMA table_info(branch_balance_alerts)")).fetchall()
        print("📋 表结构:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        return True
        
    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        DatabaseService.rollback_session(session)
        return False
    finally:
        DatabaseService.close_session(session)

if __name__ == "__main__":
    print("=== 创建网点余额报警设置表 ===")
    success = create_balance_alerts_table()
    if success:
        print("✅ 迁移完成")
    else:
        print("❌ 迁移失败")
        sys.exit(1) 
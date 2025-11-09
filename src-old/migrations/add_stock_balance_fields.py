#!/usr/bin/env python3
"""
数据库迁移：为daily_foreign_stock表添加库存统计字段
运行方式：python migrations/add_stock_balance_fields.py
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.db_service import DatabaseService
from sqlalchemy import text

def upgrade():
    """添加新字段"""
    session = DatabaseService.get_session()
    try:
        print("开始为daily_foreign_stock表添加新字段...")
        
        # 检查字段是否已存在
        result = session.execute(text("PRAGMA table_info(daily_foreign_stock)")).fetchall()
        existing_columns = [col[1] for col in result]
        
        # 添加期初余额字段
        if 'opening_balance' not in existing_columns:
            session.execute(text("""
                ALTER TABLE daily_foreign_stock 
                ADD COLUMN opening_balance DECIMAL(15,2) NOT NULL DEFAULT 0
            """))
            print("✓ 添加字段：opening_balance")
        else:
            print("- 字段已存在：opening_balance")
        
        # 添加变动金额字段
        if 'change_amount' not in existing_columns:
            session.execute(text("""
                ALTER TABLE daily_foreign_stock 
                ADD COLUMN change_amount DECIMAL(15,2) NOT NULL DEFAULT 0
            """))
            print("✓ 添加字段：change_amount")
        else:
            print("- 字段已存在：change_amount")
        
        # 添加当前余额字段
        if 'current_balance' not in existing_columns:
            session.execute(text("""
                ALTER TABLE daily_foreign_stock 
                ADD COLUMN current_balance DECIMAL(15,2) NOT NULL DEFAULT 0
            """))
            print("✓ 添加字段：current_balance")
        else:
            print("- 字段已存在：current_balance")
        
        session.commit()
        print("✅ 数据库迁移完成！")
        
    except Exception as e:
        session.rollback()
        print(f"❌ 迁移失败: {str(e)}")
        raise e
    finally:
        DatabaseService.close_session(session)

def downgrade():
    """回滚字段（SQLite不支持DROP COLUMN，仅显示提示）"""
    print("⚠️ SQLite不支持DROP COLUMN操作")
    print("如需回滚，请手动重建表或使用数据库管理工具")

if __name__ == "__main__":
    print("=== 数据库迁移：daily_foreign_stock表字段添加 ===")
    try:
        upgrade()
    except Exception as e:
        print(f"迁移失败: {str(e)}")
        sys.exit(1) 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为BOT表添加上报相关字段
- is_reported: 是否已上报
- report_time: 上报时间
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from sqlalchemy import text

def add_reporting_fields():
    """为BOT表添加上报字段"""
    session = DatabaseService.get_session()
    
    try:
        print("="*80)
        print("为BOT表添加上报相关字段")
        print("="*80)
        
        # 检查字段是否已存在
        tables = ['BOT_BuyFX', 'BOT_SellFX', 'BOT_FCD', 'BOT_Provider']
        
        for table in tables:
            print(f"\n[{table}] 检查并添加字段...")
            
            # 检查表是否存在
            result = session.execute(text(f"SHOW TABLES LIKE '{table}'"))
            if not result.fetchone():
                print(f"  [SKIP] 表不存在")
                continue
            
            # 获取现有列
            result = session.execute(text(f"DESCRIBE {table}"))
            columns = [row[0] for row in result]
            
            # 添加is_reported字段
            if 'is_reported' not in columns:
                session.execute(text(f"""
                    ALTER TABLE {table}
                    ADD COLUMN is_reported BOOLEAN DEFAULT FALSE 
                    COMMENT '是否已上报' AFTER created_at
                """))
                print(f"  [OK] 添加is_reported字段")
            else:
                print(f"  [SKIP] is_reported字段已存在")
            
            # 添加report_time字段
            if 'report_time' not in columns:
                session.execute(text(f"""
                    ALTER TABLE {table}
                    ADD COLUMN report_time DATETIME DEFAULT NULL 
                    COMMENT '上报时间' AFTER is_reported
                """))
                print(f"  [OK] 添加report_time字段")
            else:
                print(f"  [SKIP] report_time字段已存在")
            
            # 添加reported_by字段（上报人）
            if 'reported_by' not in columns:
                session.execute(text(f"""
                    ALTER TABLE {table}
                    ADD COLUMN reported_by INT DEFAULT NULL 
                    COMMENT '上报人ID' AFTER report_time
                """))
                print(f"  [OK] 添加reported_by字段")
            else:
                print(f"  [SKIP] reported_by字段已存在")
        
        session.commit()
        
        print("\n" + "="*80)
        print("[完成] 所有BOT表字段添加完成")
        print("="*80)
        print("\n添加的字段:")
        print("  - is_reported BOOLEAN DEFAULT FALSE")
        print("  - report_time DATETIME DEFAULT NULL")
        print("  - reported_by INT DEFAULT NULL")
        
    except Exception as e:
        session.rollback()
        print(f"\n[ERROR] 添加字段失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        DatabaseService.close_session(session)

if __name__ == "__main__":
    add_reporting_fields()


#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复BOT表的缺失字段
"""

from services.db_service import DatabaseService
from sqlalchemy import text

def main():
    print("Fixing BOT Tables...")
    print("="*80)
    
    db = DatabaseService()
    session = db.get_session()
    
    try:
        # 1. 为BOT_BuyFX添加is_reported字段
        print("\n[1] Adding is_reported to BOT_BuyFX...")
        try:
            session.execute(text("""
                ALTER TABLE BOT_BuyFX 
                ADD COLUMN is_reported TINYINT(1) DEFAULT 0
            """))
            session.commit()
            print("  [OK] Field added")
        except Exception as e:
            if 'Duplicate column name' in str(e):
                print("  [SKIP] Field already exists")
            else:
                raise
        
        # 2. 为BOT_SellFX添加is_reported字段
        print("\n[2] Adding is_reported to BOT_SellFX...")
        try:
            session.execute(text("""
                ALTER TABLE BOT_SellFX 
                ADD COLUMN is_reported TINYINT(1) DEFAULT 0
            """))
            session.commit()
            print("  [OK] Field added")
        except Exception as e:
            if 'Duplicate column name' in str(e):
                print("  [SKIP] Field already exists")
            else:
                raise
        
        # 3. 为BOT_FCD添加is_reported字段
        print("\n[3] Adding is_reported to BOT_FCD...")
        try:
            session.execute(text("""
                ALTER TABLE BOT_FCD 
                ADD COLUMN is_reported TINYINT(1) DEFAULT 0
            """))
            session.commit()
            print("  [OK] Field added")
        except Exception as e:
            if 'Duplicate column name' in str(e):
                print("  [SKIP] Field already exists")
            else:
                raise
        
        # 4. 为BOT_Provider添加is_reported字段
        print("\n[4] Adding is_reported to BOT_Provider...")
        try:
            session.execute(text("""
                ALTER TABLE BOT_Provider 
                ADD COLUMN is_reported TINYINT(1) DEFAULT 0
            """))
            session.commit()
            print("  [OK] Field added")
        except Exception as e:
            if 'Duplicate column name' in str(e):
                print("  [SKIP] Field already exists")
            else:
                raise
        
        # 5. 为BOT_Provider添加adjustment相关字段
        print("\n[5] Adding adjustment fields to BOT_Provider...")
        
        fields_to_add = [
            ('adjustment_amount', 'DECIMAL(15,2)', 'Adjustment amount'),
            ('adjustment_currency', 'VARCHAR(10)', 'Currency code'),
            ('adjustment_reason', 'TEXT', 'Adjustment reason'),
            ('usd_equivalent', 'DECIMAL(15,2)', 'USD equivalent'),
            ('transaction_no', 'VARCHAR(30)', 'Transaction number')
        ]
        
        for field_name, field_type, description in fields_to_add:
            try:
                session.execute(text(f"""
                    ALTER TABLE BOT_Provider 
                    ADD COLUMN {field_name} {field_type} COMMENT '{description}'
                """))
                session.commit()
                print(f"  [OK] Added {field_name}")
            except Exception as e:
                if 'Duplicate column name' in str(e):
                    print(f"  [SKIP] {field_name} already exists")
                else:
                    print(f"  [WARN] Failed to add {field_name}: {str(e)}")
        
        print("\n" + "="*80)
        print("Fix completed!")
        print("="*80)
        
    except Exception as e:
        session.rollback()
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        session.close()
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())


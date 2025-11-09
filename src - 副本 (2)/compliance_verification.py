#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AMLO & BOT 合规功能全面验证脚本
"""

from services.db_service import DatabaseService
from sqlalchemy import text
import os

def check_all():
    print("AMLO & BOT Compliance Verification")
    print("="*80)
    
    db = DatabaseService()
    session = db.get_session()
    
    passed = 0
    failed = 0
    
    try:
        # 1. 检查触发规则
        print("\n[1] Trigger Rules Check:")
        report_types = ['AMLO-1-01', 'AMLO-1-02', 'AMLO-1-03', 
                       'BOT_BuyFX', 'BOT_SellFX', 'BOT_FCD', 'BOT_Provider']
        
        for report_type in report_types:
            result = session.execute(
                text("SELECT COUNT(*), SUM(is_active) FROM trigger_rules WHERE report_type = :report_type"),
                {'report_type': report_type}
            )
            row = result.fetchone()
            total = row[0] if row else 0
            active = row[1] if row and row[1] else 0
            
            if total > 0 and active > 0:
                print(f"  [OK] {report_type}: {active} active rule(s)")
                passed += 1
            else:
                print(f"  [X] {report_type}: No active rules")
                failed += 1
        
        # 2. 检查字段定义
        print("\n[2] Field Definitions Check:")
        for report_type in report_types:
            result = session.execute(
                text("SELECT COUNT(*) FROM report_fields WHERE report_type = :report_type"),
                {'report_type': report_type}
            )
            count = result.fetchone()[0]
            
            if count > 0:
                print(f"  [OK] {report_type}: {count} fields")
                passed += 1
            else:
                print(f"  [X] {report_type}: No fields")
                failed += 1
        
        # 3. 检查数据表
        print("\n[3] Database Tables Check:")
        tables = ['Reserved_Transaction', 'AMLOReport', 'BOT_BuyFX', 
                 'BOT_SellFX', 'BOT_Provider', 'BOT_FCD']
        
        for table in tables:
            result = session.execute(text(f"SHOW TABLES LIKE '{table}'"))
            if result.fetchone():
                # 检查branch_id字段
                result = session.execute(text(f"DESCRIBE {table}"))
                columns = {row[0] for row in result}
                if 'branch_id' in columns:
                    print(f"  [OK] {table}: Exists with branch_id")
                    passed += 1
                else:
                    print(f"  [!] {table}: Exists but no branch_id")
                    failed += 1
            else:
                print(f"  [X] {table}: Does NOT exist")
                failed += 1
        
        # 4. 检查exchange_transactions字段
        print("\n[4] Exchange Transactions Fields Check:")
        result = session.execute(text("DESCRIBE exchange_transactions"))
        columns = {row[0] for row in result}
        
        required_fields = ['bot_flag', 'fcd_flag', 'use_fcd', 'seqno', 'exchange_type']
        for field in required_fields:
            if field in columns:
                print(f"  [OK] {field}: Exists")
                passed += 1
            else:
                print(f"  [X] {field}: Missing")
                failed += 1
        
        # 5. 检查API文件
        print("\n[5] API Files Check:")
        api_files = [
            'routes/app_balance.py',
            'routes/app_amlo.py',
            'routes/app_bot.py',
            'routes/app_repform.py'
        ]
        
        for api_file in api_files:
            if os.path.exists(api_file):
                # 特别检查app_balance.py中的BOT_Provider集成
                if 'app_balance' in api_file:
                    with open(api_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'BOT_Provider' in content and 'check_triggers' in content:
                            print(f"  [OK] {api_file}: BOT_Provider integrated")
                            passed += 1
                        else:
                            print(f"  [X] {api_file}: BOT_Provider NOT integrated")
                            failed += 1
                else:
                    print(f"  [OK] {api_file}: Exists")
                    passed += 1
            else:
                print(f"  [X] {api_file}: Missing")
                failed += 1
        
        # 6. 检查前端组件
        print("\n[6] Frontend Components Check:")
        vue_files = [
            '../src/views/ExchangeView.vue',
            '../src/components/exchange/ReservationModal.vue',
            '../src/views/amlo/ReservationAuditView.vue',
            '../src/views/amlo/ReportListView.vue',
            '../src/views/bot/BOTReportView.vue'
        ]
        
        for vue_file in vue_files:
            if os.path.exists(vue_file):
                print(f"  [OK] {vue_file.split('/')[-1]}: Exists")
                passed += 1
            else:
                print(f"  [X] {vue_file.split('/')[-1]}: Missing")
                failed += 1
        
        # 总结
        print("\n" + "="*80)
        print("Summary:")
        total = passed + failed
        print(f"  Total: {total} checks")
        print(f"  Passed: {passed} ({passed/total*100:.1f}%)")
        print(f"  Failed: {failed} ({failed/total*100:.1f}%)")
        
        completion_rate = (passed / total * 100) if total > 0 else 0
        print(f"\nOverall Compliance: {completion_rate:.1f}%")
        
        if completion_rate >= 85:
            print("Status: ✓ Excellent")
        elif completion_rate >= 70:
            print("Status: ⚠ Good - Most features implemented")
        else:
            print("Status: ✗ Needs work")
        
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        session.close()
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(check_all())


#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库合规性验证
检查所有表结构、字段、触发规则是否符合监管要求
"""

from services.db_service import DatabaseService
from sqlalchemy import text

def main():
    print("Database Compliance Verification")
    print("="*80)
    
    db = DatabaseService()
    session = db.get_session()
    
    passed = []
    failed = []
    
    try:
        # 1. 触发规则完整性
        print("\n[1] Trigger Rules Completeness:")
        result = session.execute(text("""
            SELECT report_type, COUNT(*) as total, SUM(is_active) as active
            FROM trigger_rules
            GROUP BY report_type
            ORDER BY report_type
        """))
        
        for row in result:
            report_type, total, active = row
            print(f"  {report_type}: {active or 0}/{total} active")
            if active and active > 0:
                passed.append(f"{report_type} trigger rules")
            else:
                failed.append(f"{report_type} has no active rules")
        
        # 2. 字段定义完整性
        print("\n[2] Field Definitions Completeness:")
        result = session.execute(text("""
            SELECT report_type, COUNT(*) as total,
                   SUM(CASE WHEN field_cn_name IS NOT NULL THEN 1 ELSE 0 END) as cn,
                   SUM(CASE WHEN field_en_name IS NOT NULL THEN 1 ELSE 0 END) as en,
                   SUM(CASE WHEN field_th_name IS NOT NULL THEN 1 ELSE 0 END) as th
            FROM report_fields
            GROUP BY report_type
            ORDER BY report_type
        """))
        
        for row in result:
            report_type, total, cn, en, th = row
            multilang = "Full" if (cn == total and en == total and th == total) else "Partial"
            print(f"  {report_type}: {total} fields, {multilang} multilingual")
            
            if total > 0:
                passed.append(f"{report_type} field definitions")
                if multilang == "Full":
                    passed.append(f"{report_type} multilingual support")
                else:
                    failed.append(f"{report_type} incomplete multilingual")
            else:
                failed.append(f"{report_type} has no field definitions")
        
        # 3. 数据表结构
        print("\n[3] Database Tables Structure:")
        tables_to_check = [
            ('Reserved_Transaction', ['status', 'audit_time', 'branch_id']),
            ('AMLOReport', ['report_type', 'pdf_filename', 'branch_id']),
            ('BOT_BuyFX', ['transaction_id', 'branch_id', 'is_reported']),
            ('BOT_SellFX', ['transaction_id', 'branch_id', 'is_reported']),
            ('BOT_Provider', ['branch_id', 'adjustment_amount']),
            ('BOT_FCD', ['transaction_id', 'branch_id', 'is_reported']),
            ('exchange_transactions', ['bot_flag', 'fcd_flag', 'use_fcd', 'seqno'])
        ]
        
        for table_name, required_fields in tables_to_check:
            result = session.execute(text(f"SHOW TABLES LIKE '{table_name}'"))
            if not result.fetchone():
                print(f"  [X] {table_name}: Table missing")
                failed.append(f"{table_name} table")
                continue
            
            result = session.execute(text(f"DESCRIBE {table_name}"))
            columns = {row[0] for row in result}
            
            missing_fields = [f for f in required_fields if f not in columns]
            
            if not missing_fields:
                print(f"  [OK] {table_name}: All required fields present")
                passed.append(f"{table_name} structure")
            else:
                print(f"  [X] {table_name}: Missing fields: {', '.join(missing_fields)}")
                failed.append(f"{table_name} missing {len(missing_fields)} field(s)")
        
        # 4. 服务类检查
        print("\n[4] Service Classes Check:")
        services_to_check = [
            ('services.repform.rule_engine', 'RuleEngine'),
            ('services.repform.field_manager', 'FieldManager'),
            ('services.bot_report_service', 'BOTReportService'),
        ]
        
        for module_path, class_name in services_to_check:
            try:
                module = __import__(module_path, fromlist=[class_name])
                cls = getattr(module, class_name)
                print(f"  [OK] {class_name}: Importable")
                passed.append(f"{class_name} service")
            except Exception as e:
                print(f"  [X] {class_name}: Import failed - {str(e)}")
                failed.append(f"{class_name} service")
        
        # 5. BOT_Provider特定检查
        print("\n[5] BOT_Provider Specific Checks:")
        
        # 5.1 检查触发规则
        result = session.execute(text("""
            SELECT rule_name, rule_expression, is_active
            FROM trigger_rules
            WHERE report_type = 'BOT_Provider'
        """))
        
        rule = result.fetchone()
        if rule:
            print(f"  [OK] Trigger rule: {rule[0]}")
            print(f"  [OK] Status: {'Active' if rule[2] else 'Inactive'}")
            passed.append("BOT_Provider trigger rule")
        else:
            print(f"  [X] No trigger rule configured")
            failed.append("BOT_Provider trigger rule")
        
        # 5.2 检查字段数量
        result = session.execute(text("""
            SELECT COUNT(*) FROM report_fields WHERE report_type = 'BOT_Provider'
        """))
        count = result.fetchone()[0]
        
        if count >= 10:
            print(f"  [OK] Field definitions: {count} fields")
            passed.append("BOT_Provider field definitions")
        else:
            print(f"  [X] Insufficient fields: {count} (expected >= 10)")
            failed.append("BOT_Provider field definitions")
        
        # 5.3 检查BOT_Provider表
        result = session.execute(text("DESCRIBE BOT_Provider"))
        columns = {row[0] for row in result}
        
        provider_fields = ['branch_id', 'adjustment_amount', 'created_at']
        missing = [f for f in provider_fields if f not in columns]
        
        if not missing:
            print(f"  [OK] BOT_Provider table: All key fields present")
            passed.append("BOT_Provider table structure")
        else:
            print(f"  [X] BOT_Provider table: Missing {', '.join(missing)}")
            failed.append("BOT_Provider table structure")
        
        # 总结
        print("\n" + "="*80)
        print("Verification Summary")
        print("="*80)
        
        total = len(passed) + len(failed)
        print(f"\nTotal Checks: {total}")
        print(f"Passed: {len(passed)} ({len(passed)/total*100:.1f}%)")
        print(f"Failed: {len(failed)} ({len(failed)/total*100:.1f}%)")
        
        if failed:
            print("\nFailed Items:")
            for item in failed:
                print(f"  - {item}")
        
        completion_rate = (len(passed) / total * 100) if total > 0 else 0
        
        print(f"\nDatabase Compliance Rate: {completion_rate:.1f}%")
        
        if completion_rate >= 95:
            print("Status: ✓ Excellent - Database fully compliant")
            return 0
        elif completion_rate >= 80:
            print("Status: ⚠ Good - Minor issues to fix")
            return 0
        else:
            print("Status: ✗ Poor - Significant issues found")
            return 1
        
    except Exception as e:
        print(f"\n[ERROR] Verification failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 2
    finally:
        session.close()

if __name__ == "__main__":
    import sys
    sys.exit(main())


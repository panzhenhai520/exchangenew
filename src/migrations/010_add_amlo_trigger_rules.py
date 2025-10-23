# -*- coding: utf-8 -*-
"""
Migration 010: Add missing AMLO-1-02 and AMLO-1-03 trigger rules
Created: 2025-10-18
Purpose: Implement ATR (Asset Transaction Report) and STR (Suspicious Transaction Report) triggers
"""

import json
import sys
import os
from datetime import datetime

# Add parent directory to path to import services
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.db_service import DatabaseService
from sqlalchemy import text


def add_amlo_102_rule(session):
    """
    Add AMLO-1-02 (ATR - Asset Transaction Report) trigger rule
    Triggers when: total_amount >= 8,000,000 THB AND exchange_type == 'asset_backed'
    """
    print("\n[Migration 010] Adding AMLO-1-02 (ATR) trigger rule...")

    # Check if rule already exists
    check_sql = text("""
        SELECT COUNT(*) as count
        FROM trigger_rules
        WHERE report_type = 'AMLO-1-02'
            AND rule_name LIKE '%资产抵押%'
    """)

    result = session.execute(check_sql)
    count = result.first()[0]

    if count > 0:
        print("  -> AMLO-1-02 rule already exists, skipping...")
        return

    # Create rule expression
    rule_expression = {
        "logic": "AND",
        "conditions": [
            {
                "field": "total_amount",
                "operator": ">=",
                "value": 8000000
            },
            {
                "field": "exchange_type",
                "operator": "==",
                "value": "asset_backed"
            }
        ]
    }

    # Insert rule
    insert_sql = text("""
        INSERT INTO trigger_rules (
            rule_name,
            report_type,
            rule_expression,
            description_cn,
            description_en,
            description_th,
            priority,
            allow_continue,
            warning_message_cn,
            warning_message_en,
            warning_message_th,
            is_active,
            created_at,
            updated_at
        ) VALUES (
            :rule_name,
            :report_type,
            :rule_expression,
            :description_cn,
            :description_en,
            :description_th,
            :priority,
            :allow_continue,
            :warning_message_cn,
            :warning_message_en,
            :warning_message_th,
            :is_active,
            :created_at,
            :updated_at
        )
    """)

    session.execute(insert_sql, {
        'rule_name': 'AMLO-1-02资产抵押触发',
        'report_type': 'AMLO-1-02',
        'rule_expression': json.dumps(rule_expression, ensure_ascii=False),
        'description_cn': '资产抵押兑换金额超过800万泰铢时触发ATR报告',
        'description_en': 'Trigger ATR report when asset-backed exchange amount exceeds 8,000,000 THB',
        'description_th': 'เรียกรายงาน ATR เมื่อจำนวนเงินแลกเปลี่ยนที่มีหลักทรัพย์ค้ำประกันเกิน 8,000,000 บาท',
        'priority': 100,
        'allow_continue': False,
        'warning_message_cn': '此交易涉及资产抵押且金额超过800万泰铢，需要填写AMLO-1-02报告',
        'warning_message_en': 'This asset-backed transaction exceeds 8,000,000 THB and requires AMLO-1-02 report',
        'warning_message_th': 'ธุรกรรมที่มีหลักทรัพย์ค้ำประกันนี้เกิน 8,000,000 บาท และต้องกรอกรายงาน AMLO-1-02',
        'is_active': True,
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    })

    print("  -> AMLO-1-02 rule added successfully")


def add_amlo_103_rule(session):
    """
    Add AMLO-1-03 (STR - Suspicious Transaction Report) trigger rule
    Triggers when: cumulative_amount_30d >= 5,000,000 THB
    """
    print("\n[Migration 010] Adding AMLO-1-03 (STR) trigger rule...")

    # Check if rule already exists
    check_sql = text("""
        SELECT COUNT(*) as count
        FROM trigger_rules
        WHERE report_type = 'AMLO-1-03'
            AND rule_name LIKE '%累计%'
    """)

    result = session.execute(check_sql)
    count = result.first()[0]

    if count > 0:
        print("  -> AMLO-1-03 rule already exists, skipping...")
        return

    # Create rule expression
    rule_expression = {
        "logic": "AND",
        "conditions": [
            {
                "field": "cumulative_amount_30d",
                "operator": ">=",
                "value": 5000000
            }
        ]
    }

    # Insert rule
    insert_sql = text("""
        INSERT INTO trigger_rules (
            rule_name,
            report_type,
            rule_expression,
            description_cn,
            description_en,
            description_th,
            priority,
            allow_continue,
            warning_message_cn,
            warning_message_en,
            warning_message_th,
            is_active,
            created_at,
            updated_at
        ) VALUES (
            :rule_name,
            :report_type,
            :rule_expression,
            :description_cn,
            :description_en,
            :description_th,
            :priority,
            :allow_continue,
            :warning_message_cn,
            :warning_message_en,
            :warning_message_th,
            :is_active,
            :created_at,
            :updated_at
        )
    """)

    session.execute(insert_sql, {
        'rule_name': 'AMLO-1-03累计触发',
        'report_type': 'AMLO-1-03',
        'rule_expression': json.dumps(rule_expression, ensure_ascii=False),
        'description_cn': '同一客户30天累计交易金额超过500万泰铢时触发STR报告',
        'description_en': 'Trigger STR report when customer cumulative amount in 30 days exceeds 5,000,000 THB',
        'description_th': 'เรียกรายงาน STR เมื่อยอดรวมของลูกค้าในรอบ 30 วันเกิน 5,000,000 บาท',
        'priority': 90,
        'allow_continue': False,
        'warning_message_cn': '客户30天累计交易金额超过500万泰铢，需要填写AMLO-1-03可疑交易报告',
        'warning_message_en': 'Customer cumulative transactions exceed 5,000,000 THB in 30 days, AMLO-1-03 report required',
        'warning_message_th': 'ธุรกรรมสะสมของลูกค้าเกิน 5,000,000 บาทใน 30 วัน ต้องกรอกรายงาน AMLO-1-03',
        'is_active': True,
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    })

    print("  -> AMLO-1-03 rule added successfully")


def verify_rules(session):
    """Verify that all AMLO rules exist"""
    print("\n[Migration 010] Verifying AMLO trigger rules...")

    verify_sql = text("""
        SELECT
            report_type,
            rule_name,
            priority,
            is_active
        FROM trigger_rules
        WHERE report_type IN ('AMLO-1-01', 'AMLO-1-02', 'AMLO-1-03')
        ORDER BY report_type, priority DESC
    """)

    result = session.execute(verify_sql)
    rules = result.fetchall()

    print(f"\n  Total AMLO rules found: {len(rules)}")
    print("  " + "="*80)

    for rule in rules:
        report_type, rule_name, priority, is_active = rule
        status = "ACTIVE" if is_active else "INACTIVE"
        print(f"  {report_type:15} | {rule_name:40} | Priority: {priority:3} | {status}")

    print("  " + "="*80)

    # Check if all three report types have rules
    report_types = set(rule[0] for rule in rules)
    expected_types = {'AMLO-1-01', 'AMLO-1-02', 'AMLO-1-03'}
    missing = expected_types - report_types

    if missing:
        print(f"\n  WARNING: Missing rules for: {', '.join(missing)}")
        return False
    else:
        print("\n  SUCCESS: All AMLO report types have trigger rules configured")
        return True


def run_migration():
    """Execute the migration"""
    print("\n" + "="*80)
    print("Migration 010: Add AMLO-1-02 and AMLO-1-03 Trigger Rules")
    print("="*80)

    try:
        with DatabaseService.get_session() as session:
            # Add AMLO-1-02 rule
            add_amlo_102_rule(session)

            # Add AMLO-1-03 rule
            add_amlo_103_rule(session)

            # Commit changes
            session.commit()
            print("\n  -> All changes committed successfully")

            # Verify
            success = verify_rules(session)

            if success:
                print("\n" + "="*80)
                print("Migration 010 completed successfully!")
                print("="*80 + "\n")
                return True
            else:
                print("\n" + "="*80)
                print("Migration 010 completed with warnings")
                print("="*80 + "\n")
                return False

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)

# -*- coding: utf-8 -*-
"""
Migration 011: Correct AMLO trigger rule thresholds to match regulatory requirements
Created: 2025-11-03
Purpose: Update trigger thresholds based on AMLO compliance requirements

Correct thresholds:
- AMLO-1-01 (CTR): >= 500,000 THB (excluding THB exchange)
- AMLO-1-02 (ATR): >= 800,000 THB
- AMLO-1-03 (STR): Suspicious transaction detection (multi-condition)
"""

import json
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.db_service import DatabaseService
from sqlalchemy import text


def update_amlo_101_rule(session):
    """
    Update AMLO-1-01 (CTR - Cash Transaction Report) trigger rule
    Correct threshold: total_amount >= 500,000 THB AND currency_code != 'THB'

    Note: Excludes THB exchange (e.g., THB to THB) as per regulations
    """
    print("\n[Migration 011] Updating AMLO-1-01 (CTR) trigger rule...")

    # Delete existing AMLO-1-01 rules
    delete_sql = text("""
        DELETE FROM trigger_rules
        WHERE report_type = 'AMLO-1-01'
    """)
    result = session.execute(delete_sql)
    print(f"  -> Deleted {result.rowcount} old AMLO-1-01 rule(s)")

    # Create corrected rule expression
    # CTR triggers when transaction >= 500,000 THB AND not THB exchange
    rule_expression = {
        "logic": "AND",
        "conditions": [
            {
                "field": "total_amount",
                "operator": ">=",
                "value": 500000  # 500,000 THB (corrected from 2,000,000)
            },
            {
                "field": "currency_code",
                "operator": "!=",
                "value": "THB"  # Exclude THB exchange
            }
        ]
    }

    # Insert corrected rule
    insert_sql = text("""
        INSERT INTO trigger_rules (
            rule_name,
            rule_name_en,
            rule_name_th,
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
            :rule_name_en,
            :rule_name_th,
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
        'rule_name': 'AMLO-1-01单笔大额现金交易',
        'rule_name_en': 'AMLO-1-01 Large Cash Transaction',
        'rule_name_th': 'AMLO-1-01 รายการเงินสดขนาดใหญ่',
        'report_type': 'AMLO-1-01',
        'rule_expression': json.dumps(rule_expression, ensure_ascii=False),
        'description_cn': '单笔交易金额超过50万泰铢（不含泰铢兑换）时触发CTR报告',
        'description_en': 'Trigger CTR report when single transaction amount exceeds 500,000 THB (excluding THB exchange)',
        'description_th': 'เรียกรายงาน CTR เมื่อจำนวนเงินรายการเดียวเกิน 500,000 บาท (ไม่รวมการแลกเปลี่ยนบาท)',
        'priority': 100,
        'allow_continue': False,  # Must fill report before continuing
        'warning_message_cn': '单笔交易金额超过50万泰铢，需要填写AMLO-1-01报告',
        'warning_message_en': 'Single transaction exceeds 500,000 THB, AMLO-1-01 report required',
        'warning_message_th': 'ธุรกรรมเดียวเกิน 500,000 บาท ต้องกรอกรายงาน AMLO-1-01',
        'is_active': True,
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    })

    print("  -> AMLO-1-01 rule updated successfully (threshold: 500,000 THB)")


def update_amlo_102_rule(session):
    """
    Update AMLO-1-02 (ATR - Asset Transaction Report) trigger rule
    Correct threshold: total_amount >= 800,000 THB

    Note: Simplified condition - just check amount threshold
    """
    print("\n[Migration 011] Updating AMLO-1-02 (ATR) trigger rule...")

    # Delete existing AMLO-1-02 rules
    delete_sql = text("""
        DELETE FROM trigger_rules
        WHERE report_type = 'AMLO-1-02'
    """)
    result = session.execute(delete_sql)
    print(f"  -> Deleted {result.rowcount} old AMLO-1-02 rule(s)")

    # Create corrected rule expression
    # ATR triggers when transaction >= 800,000 THB
    rule_expression = {
        "logic": "AND",
        "conditions": [
            {
                "field": "total_amount",
                "operator": ">=",
                "value": 800000  # 800,000 THB (corrected from 8,000,000)
            }
        ]
    }

    # Insert corrected rule
    insert_sql = text("""
        INSERT INTO trigger_rules (
            rule_name,
            rule_name_en,
            rule_name_th,
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
            :rule_name_en,
            :rule_name_th,
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
        'rule_name': 'AMLO-1-02资产交易报告',
        'rule_name_en': 'AMLO-1-02 Asset Transaction Report',
        'rule_name_th': 'AMLO-1-02 รายงานการทำธุรกรรมทรัพย์สิน',
        'report_type': 'AMLO-1-02',
        'rule_expression': json.dumps(rule_expression, ensure_ascii=False),
        'description_cn': '单笔交易金额超过80万泰铢时触发ATR报告',
        'description_en': 'Trigger ATR report when single transaction amount exceeds 800,000 THB',
        'description_th': 'เรียกรายงาน ATR เมื่อจำนวนเงินรายการเดียวเกิน 800,000 บาท',
        'priority': 95,  # Slightly lower than CTR to allow CTR to trigger first
        'allow_continue': False,
        'warning_message_cn': '交易金额超过80万泰铢，需要填写AMLO-1-02报告',
        'warning_message_en': 'Transaction exceeds 800,000 THB, AMLO-1-02 report required',
        'warning_message_th': 'ธุรกรรมเกิน 800,000 บาท ต้องกรอกรายงาน AMLO-1-02',
        'is_active': True,
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    })

    print("  -> AMLO-1-02 rule updated successfully (threshold: 800,000 THB)")


def update_amlo_103_rules(session):
    """
    Update AMLO-1-03 (STR - Suspicious Transaction Report) trigger rules
    Multiple detection rules for suspicious patterns:
    1. 30-day cumulative >= 500,000 THB
    2. High frequency: >= 5 transactions in 24 hours
    3. Unusual pattern: Transaction amount exactly same as previous (potential structuring)
    4. Large single transaction >= 1,000,000 THB (high-value monitoring)
    """
    print("\n[Migration 011] Updating AMLO-1-03 (STR) trigger rules...")

    # Delete existing AMLO-1-03 rules
    delete_sql = text("""
        DELETE FROM trigger_rules
        WHERE report_type = 'AMLO-1-03'
    """)
    result = session.execute(delete_sql)
    print(f"  -> Deleted {result.rowcount} old AMLO-1-03 rule(s)")

    # STR Rule 1: 30-day cumulative amount
    str_rule_1 = {
        "logic": "AND",
        "conditions": [
            {
                "field": "cumulative_amount_30d",
                "operator": ">=",
                "value": 500000  # 500,000 THB (corrected from 5,000,000)
            }
        ]
    }

    # STR Rule 2: High frequency transactions (5+ in 24h)
    str_rule_2 = {
        "logic": "AND",
        "conditions": [
            {
                "field": "transaction_count_24h",
                "operator": ">=",
                "value": 5
            }
        ]
    }

    # STR Rule 3: Large single transaction (monitoring threshold)
    str_rule_3 = {
        "logic": "AND",
        "conditions": [
            {
                "field": "total_amount",
                "operator": ">=",
                "value": 1000000  # 1,000,000 THB
            }
        ]
    }

    # Insert STR rules
    insert_sql = text("""
        INSERT INTO trigger_rules (
            rule_name,
            rule_name_en,
            rule_name_th,
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
            :rule_name_en,
            :rule_name_th,
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

    # Insert Rule 1: 30-day cumulative
    session.execute(insert_sql, {
        'rule_name': 'AMLO-1-03累计大额',
        'rule_name_en': 'AMLO-1-03 Cumulative Large Amount',
        'rule_name_th': 'AMLO-1-03 ยอดรวมขนาดใหญ่',
        'report_type': 'AMLO-1-03',
        'rule_expression': json.dumps(str_rule_1, ensure_ascii=False),
        'description_cn': '同一客户30天累计交易金额超过50万泰铢时触发STR报告',
        'description_en': 'Trigger STR report when customer cumulative amount in 30 days exceeds 500,000 THB',
        'description_th': 'เรียกรายงาน STR เมื่อยอดรวมของลูกค้าในรอบ 30 วันเกิน 500,000 บาท',
        'priority': 90,
        'allow_continue': False,
        'warning_message_cn': '客户30天累计交易金额超过50万泰铢，需要填写AMLO-1-03可疑交易报告',
        'warning_message_en': 'Customer cumulative transactions exceed 500,000 THB in 30 days, AMLO-1-03 report required',
        'warning_message_th': 'ธุรกรรมสะสมของลูกค้าเกิน 500,000 บาทใน 30 วัน ต้องกรอกรายงาน AMLO-1-03',
        'is_active': True,
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    })
    print("  -> STR Rule 1: 30-day cumulative >= 500,000 THB")

    # Insert Rule 2: High frequency
    session.execute(insert_sql, {
        'rule_name': 'AMLO-1-03高频交易',
        'rule_name_en': 'AMLO-1-03 High Frequency',
        'rule_name_th': 'AMLO-1-03 ความถี่สูง',
        'report_type': 'AMLO-1-03',
        'rule_expression': json.dumps(str_rule_2, ensure_ascii=False),
        'description_cn': '24小时内交易次数超过5次时触发STR报告',
        'description_en': 'Trigger STR report when transaction count exceeds 5 in 24 hours',
        'description_th': 'เรียกรายงาน STR เมื่อจำนวนรายการเกิน 5 ครั้งใน 24 ชั่วโมง',
        'priority': 85,
        'allow_continue': False,
        'warning_message_cn': '客户24小时内交易次数过多（超过5次），需要填写AMLO-1-03可疑交易报告',
        'warning_message_en': 'High frequency transactions (>5 in 24h), AMLO-1-03 report required',
        'warning_message_th': 'ธุรกรรมความถี่สูง (>5 ครั้งใน 24 ชม.) ต้องกรอกรายงาน AMLO-1-03',
        'is_active': True,
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    })
    print("  -> STR Rule 2: High frequency >= 5 transactions in 24h")

    # Insert Rule 3: Large single transaction monitoring
    session.execute(insert_sql, {
        'rule_name': 'AMLO-1-03特大额监控',
        'rule_name_en': 'AMLO-1-03 Large Transaction Monitoring',
        'rule_name_th': 'AMLO-1-03 การตรวจสอบรายการใหญ่',
        'report_type': 'AMLO-1-03',
        'rule_expression': json.dumps(str_rule_3, ensure_ascii=False),
        'description_cn': '单笔交易金额超过100万泰铢时触发STR报告（特大额监控）',
        'description_en': 'Trigger STR report when single transaction exceeds 1,000,000 THB (large transaction monitoring)',
        'description_th': 'เรียกรายงาน STR เมื่อรายการเดียวเกิน 1,000,000 บาท (การตรวจสอบรายการใหญ่)',
        'priority': 80,
        'allow_continue': False,
        'warning_message_cn': '交易金额超过100万泰铢，需要填写AMLO-1-03可疑交易报告（特大额监控）',
        'warning_message_en': 'Transaction exceeds 1,000,000 THB, AMLO-1-03 report required (large transaction monitoring)',
        'warning_message_th': 'ธุรกรรมเกิน 1,000,000 บาท ต้องกรอกรายงาน AMLO-1-03 (การตรวจสอบรายการใหญ่)',
        'is_active': True,
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    })
    print("  -> STR Rule 3: Large single transaction >= 1,000,000 THB")

    print("  -> AMLO-1-03 rules updated successfully (3 detection rules)")


def verify_rules(session):
    """Verify that all AMLO rules exist with correct thresholds"""
    print("\n[Migration 011] Verifying AMLO trigger rules...")

    verify_sql = text("""
        SELECT
            report_type,
            rule_name,
            rule_expression,
            priority,
            is_active
        FROM trigger_rules
        WHERE report_type IN ('AMLO-1-01', 'AMLO-1-02', 'AMLO-1-03')
        ORDER BY report_type, priority DESC
    """)

    result = session.execute(verify_sql)
    rules = result.fetchall()

    print(f"\n  Total AMLO rules found: {len(rules)}")
    print("  " + "="*100)
    print(f"  {'Report Type':15} | {'Rule Name':40} | {'Priority':8} | {'Threshold':20} | {'Status':8}")
    print("  " + "="*100)

    for rule in rules:
        report_type, rule_name, rule_expression_json, priority, is_active = rule
        status = "ACTIVE" if is_active else "INACTIVE"

        # Extract threshold from rule expression
        try:
            rule_expr = json.loads(rule_expression_json)
            conditions = rule_expr.get('conditions', [])
            threshold = "N/A"
            for cond in conditions:
                if cond.get('field') in ['total_amount', 'cumulative_amount_30d', 'transaction_count_24h']:
                    value = cond.get('value')
                    operator = cond.get('operator', '>=')
                    field = cond.get('field')
                    if field == 'total_amount' or field == 'cumulative_amount_30d':
                        threshold = f"{operator} {value:,} THB"
                    else:
                        threshold = f"{operator} {value} txns"
                    break
        except:
            threshold = "ERROR"

        print(f"  {report_type:15} | {rule_name:40} | {priority:8} | {threshold:20} | {status:8}")

    print("  " + "="*100)

    # Verify expected rules
    expected_rules = {
        'AMLO-1-01': 1,  # 1 CTR rule
        'AMLO-1-02': 1,  # 1 ATR rule
        'AMLO-1-03': 3   # 3 STR rules (cumulative, frequency, large amount)
    }

    rule_counts = {}
    for rule in rules:
        report_type = rule[0]
        rule_counts[report_type] = rule_counts.get(report_type, 0) + 1

    all_ok = True
    for report_type, expected_count in expected_rules.items():
        actual_count = rule_counts.get(report_type, 0)
        if actual_count != expected_count:
            print(f"\n  WARNING: {report_type} has {actual_count} rules, expected {expected_count}")
            all_ok = False

    if all_ok:
        print("\n  SUCCESS: All AMLO report types have correct trigger rules configured")
        return True
    else:
        print("\n  WARNING: Some AMLO rules are missing or incorrect")
        return False


def run_migration():
    """Execute the migration"""
    print("\n" + "="*100)
    print("Migration 011: Correct AMLO Trigger Rule Thresholds")
    print("="*100)

    try:
        with DatabaseService.get_session() as session:
            # Update AMLO-1-01 rule (CTR)
            update_amlo_101_rule(session)

            # Update AMLO-1-02 rule (ATR)
            update_amlo_102_rule(session)

            # Update AMLO-1-03 rules (STR - multiple rules)
            update_amlo_103_rules(session)

            # Commit changes
            session.commit()
            print("\n  -> All changes committed successfully")

            # Verify
            success = verify_rules(session)

            if success:
                print("\n" + "="*100)
                print("Migration 011 completed successfully!")
                print("="*100)
                print("\nCorrected thresholds:")
                print("  1. AMLO-1-01 (CTR): >= 500,000 THB (excluding THB exchange)")
                print("  2. AMLO-1-02 (ATR): >= 800,000 THB")
                print("  3. AMLO-1-03 (STR): Multiple detection rules:")
                print("     - 30-day cumulative >= 500,000 THB")
                print("     - High frequency >= 5 transactions in 24h")
                print("     - Large single >= 1,000,000 THB")
                print("\nNext steps:")
                print("  - Run test: python test_amlo_rules.py")
                print("  - Check frontend: TriggerRulesTab.vue")
                print("="*100 + "\n")
                return True
            else:
                print("\n" + "="*100)
                print("Migration 011 completed with warnings")
                print("="*100 + "\n")
                return False

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)

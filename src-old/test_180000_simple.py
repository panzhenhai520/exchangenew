# -*- coding: utf-8 -*-
"""
Test 180,000 USD sell transaction AMLO trigger
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.db_service import SessionLocal
from services.repform.rule_engine import RuleEngine
import json

def test_180000_usd():
    """Test selling 180,000 USD"""
    print("=" * 80)
    print("Testing: Sell 180,000 USD (approx 5,844,600 THB)")
    print("=" * 80)

    session = SessionLocal()

    try:
        # USD rate 32.47 THB (180,000 * 32.47 = 5,844,600)
        usd_amount = 180000
        usd_rate = 32.47
        thb_amount = usd_amount * usd_rate

        print(f"\nTransaction Data:")
        print(f"  Sell Currency: USD")
        print(f"  Sell Amount: {usd_amount:,.2f} USD")
        print(f"  Rate: {usd_rate}")
        print(f"  THB Amount: {thb_amount:,.2f} THB")

        data = {
            "customer_id": "1234567890123",
            "customer_name": "Test Customer",
            "customer_country": "TH",
            "transaction_type": "exchange",
            "transaction_amount_thb": thb_amount,
            "total_amount": thb_amount,
            "payment_method": "cash",
            "customer_age": None,
            "exchange_type": "normal"
        }

        print(f"\nCheck Data:")
        print(json.dumps(data, indent=2, ensure_ascii=False))

        # Get branch_id
        from sqlalchemy import text
        branch_sql = text("SELECT id, branch_code FROM branches LIMIT 1")
        branch = session.execute(branch_sql).fetchone()
        branch_id = branch[0] if branch else 1

        print(f"\nBranch Info:")
        print(f"  branch_id: {branch_id}")
        print(f"  branch_code: {branch[1] if branch else 'N/A'}")

        # Test AMLO-1-01
        print("\n" + "=" * 80)
        print("Testing AMLO-1-01 Trigger")
        print("=" * 80)

        result_101 = RuleEngine.check_triggers(
            db_session=session,
            report_type='AMLO-1-01',
            data=data,
            branch_id=branch_id
        )

        print(f"\nAMLO-1-01 Result:")
        print(f"  triggered: {result_101['triggered']}")

        if result_101['triggered']:
            print(f"  SUCCESS: AMLO-1-01 Triggered")
            print(f"  Rule Name: {result_101['highest_priority_rule']['rule_name']}")
            print(f"  Priority: {result_101['highest_priority_rule']['priority']}")
            print(f"  Message: {result_101['message_cn']}")

            if 'matched_conditions' in result_101:
                print(f"\n  Matched Conditions:")
                for cond in result_101['matched_conditions']:
                    if 'field' in cond:
                        print(f"    - {cond['field']} {cond['operator']} {cond['expected_value']}")
                        print(f"      Actual: {cond['actual_value']}")
        else:
            print(f"  FAILED: AMLO-1-01 Not Triggered - This is abnormal!")

            # Check why not triggered
            print(f"\n  Diagnosis: Checking rule matching:")

            rules_sql = text("""
                SELECT id, rule_name, rule_expression, is_active, priority, branch_id
                FROM trigger_rules
                WHERE report_type = 'AMLO-1-01'
                    AND is_active = TRUE
                    AND (branch_id IS NULL OR branch_id = :branch_id)
                ORDER BY priority DESC
            """)
            rules = session.execute(rules_sql, {"branch_id": branch_id}).fetchall()

            print(f"\n  Found {len(rules)} active AMLO-1-01 rules")

            for rule in rules:
                rule_id, rule_name, rule_expr_str, is_active, priority, rule_branch_id = rule
                rule_expr = json.loads(rule_expr_str)

                print(f"\n  [Rule {rule_id}] {rule_name}")
                print(f"    Priority: {priority}")
                print(f"    branch_id: {rule_branch_id}")
                print(f"    Expression: {json.dumps(rule_expr, ensure_ascii=False)}")

                is_matched, details = RuleEngine.evaluate_rule_with_details(rule_expr, data)
                print(f"    Match Result: {'MATCHED' if is_matched else 'NOT MATCHED'}")

                if not is_matched:
                    print(f"    Reason for no match:")
                    for cond in details.get('unmatched', []):
                        if 'field' in cond:
                            print(f"      - {cond['field']}: expected {cond['operator']} {cond['expected_value']}, actual {cond['actual_value']}")

        # Test AMLO-1-02
        print("\n" + "=" * 80)
        print("Testing AMLO-1-02 Trigger")
        print("=" * 80)

        result_102 = RuleEngine.check_triggers(
            db_session=session,
            report_type='AMLO-1-02',
            data=data,
            branch_id=branch_id
        )

        print(f"\nAMLO-1-02 Result:")
        print(f"  triggered: {result_102['triggered']}")
        if result_102['triggered']:
            print(f"  SUCCESS: AMLO-1-02 Triggered")
        else:
            print(f"  NOT TRIGGERED (Normal - exchange_type is not asset_mortgage)")

        # Test AMLO-1-03
        print("\n" + "=" * 80)
        print("Testing AMLO-1-03 Trigger")
        print("=" * 80)

        result_103 = RuleEngine.check_triggers(
            db_session=session,
            report_type='AMLO-1-03',
            data=data,
            branch_id=branch_id
        )

        print(f"\nAMLO-1-03 Result:")
        print(f"  triggered: {result_103['triggered']}")
        if result_103['triggered']:
            print(f"  SUCCESS: AMLO-1-03 Triggered")
        else:
            print(f"  NOT TRIGGERED (Normal - no 30-day cumulative data)")

        print("\n" + "=" * 80)
        print("Summary")
        print("=" * 80)
        print(f"AMLO-1-01: {'TRIGGERED' if result_101['triggered'] else 'NOT TRIGGERED'}")
        print(f"AMLO-1-02: {'TRIGGERED' if result_102['triggered'] else 'NOT TRIGGERED'}")
        print(f"AMLO-1-03: {'TRIGGERED' if result_103['triggered'] else 'NOT TRIGGERED'}")

    finally:
        session.close()

if __name__ == '__main__':
    test_180000_usd()

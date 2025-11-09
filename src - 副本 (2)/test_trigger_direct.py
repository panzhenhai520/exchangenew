# -*- coding: utf-8 -*-
"""
直接测试触发规则引擎，不通过HTTP API
"""

from services.db_service import SessionLocal
from services.repform import RuleEngine
import json

def main():
    print("=" * 80)
    print("[测试] 直接测试RuleEngine.check_triggers")
    print("=" * 80)

    session = SessionLocal()

    try:
        # 测试场景1: 180,000 USD = 5,844,600 THB
        print("\n[场景1] 180,000 USD = 5,844,600 THB")
        print("-" * 80)

        data1 = {
            "customer_id": "1234567890123",
            "customer_name": "Test Customer",
            "customer_country": "TH",
            "transaction_type": "exchange",
            "transaction_amount_thb": 5844600,
            "total_amount": 5844600,
            "payment_method": "cash",
            "customer_age": None,
            "exchange_type": "normal"
        }

        print("Transaction Data:", json.dumps(data1, indent=2, ensure_ascii=False))

        result1 = RuleEngine.check_triggers(
            db_session=session,
            report_type='AMLO-1-01',
            data=data1,
            branch_id=1
        )

        print("\n[Result]")
        print(f"  Triggered: {result1['triggered']}")
        if result1['triggered']:
            print(f"  Report Type: AMLO-1-01")
            print(f"  Rule Name: {result1['highest_priority_rule']['rule_name']}")
            print(f"  Priority: {result1['highest_priority_rule']['priority']}")
            print(f"  Message CN: {result1['message_cn']}")
            print(f"  Allow Continue: {result1['allow_continue']}")
        else:
            print("  [ERROR] Should trigger but did not!")

        # 测试场景2: 99,900 USD = 3,243,753 THB
        print("\n\n[场景2] 99,900 USD = 3,243,753 THB")
        print("-" * 80)

        data2 = {
            "customer_id": "1234567890123",
            "customer_name": "Test Customer",
            "total_amount": 3243753,
            "transaction_amount_thb": 3243753,
            "payment_method": "cash"
        }

        result2 = RuleEngine.check_triggers(
            db_session=session,
            report_type='AMLO-1-01',
            data=data2,
            branch_id=1
        )

        print(f"\n[Result]")
        print(f"  Triggered: {result2['triggered']}")
        if not result2['triggered']:
            print("  [CORRECT] Did not trigger (amount < 5,000,000 THB)")
        else:
            print("  [ERROR] Should not trigger but triggered!")

    finally:
        session.close()

if __name__ == '__main__':
    main()

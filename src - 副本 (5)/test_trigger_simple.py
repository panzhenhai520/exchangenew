# -*- coding: utf-8 -*-
"""
简单的AMLO触发测试脚本
测试：卖出200,000 USD获得6,494,000 THB是否触发AMLO-1-01
"""

from services.db_service import SessionLocal
from services.repform import RuleEngine

def test_trigger():
    session = SessionLocal()

    try:
        # 模拟用户的交易数据
        transaction_data = {
            'customer_id': '1234567890123',
            'customer_name': 'Test Customer',
            'total_amount': 6494000,  # 6,494,000 THB
            'transaction_amount_thb': 6494000
        }

        print("Testing AMLO trigger with data:")
        print(f"  total_amount: {transaction_data['total_amount']}")
        print(f"  Expected: Should trigger (>= 2,000,000)")
        print()

        # 调用触发检查
        result = RuleEngine.check_triggers(
            db_session=session,
            report_type='AMLO-1-01',
            data=transaction_data,
            branch_id=6
        )

        print(f"Result: triggered = {result['triggered']}")

        if result['triggered']:
            print("SUCCESS: Trigger works correctly!")
            print(f"  Matched rule: {result['highest_priority_rule']['rule_name']}")
            print(f"  Message: {result['message_cn']}")
        else:
            print("FAILURE: Trigger did NOT work!")
            print("This means there is a configuration or logic issue.")

        return result['triggered']

    finally:
        session.close()

if __name__ == '__main__':
    test_trigger()

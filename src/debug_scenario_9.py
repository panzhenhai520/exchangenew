# -*- coding: utf-8 -*-
"""
调试场景9：1,400,000 THB + 非现金支付应该不触发
"""

from services.db_service import SessionLocal
from services.repform import RuleEngine
import json

session = SessionLocal()

try:
    transaction_data = {
        'customer_id': '1234567890123',
        'customer_name': 'Card Customer',
        'total_amount': 1400000,
        'transaction_amount_thb': 1400000,
        'payment_method': 'card',  # 非现金
        'customer_age': 50  # 年龄不够65
    }

    print("测试数据:")
    print(json.dumps(transaction_data, indent=2, ensure_ascii=False))

    result = RuleEngine.check_triggers(
        db_session=session,
        report_type='AMLO-1-01',
        data=transaction_data,
        branch_id=6
    )

    print(f"\n触发结果: {result['triggered']}")

    if result['triggered']:
        print(f"\n匹配的规则:")
        for rule in result['trigger_rules']:
            print(f"\n规则ID: {rule['id']}")
            print(f"规则名: {rule['rule_name']}")
            print(f"优先级: {rule['priority']}")
            print(f"表达式: {json.dumps(rule['rule_expression_parsed'], indent=2, ensure_ascii=False)}")

            print(f"\n匹配的条件:")
            for cond in rule['condition_details']['matched']:
                print(f"  {cond}")

            print(f"\n未匹配的条件:")
            for cond in rule['condition_details']['unmatched']:
                print(f"  {cond}")

finally:
    session.close()

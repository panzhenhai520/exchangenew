# -*- coding: utf-8 -*-
"""
精确模拟浏览器的API请求
用于调试为什么浏览器中AMLO不触发
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.db_service import SessionLocal
from services.repform import RuleEngine
import json

def test_exact_data():
    """使用与浏览器完全相同的数据测试"""
    print("=" * 80)
    print("[测试] 使用浏览器相同的数据结构")
    print("=" * 80)

    session = SessionLocal()

    try:
        # 与浏览器完全相同的数据
        data = {
            "customer_id": "1234567890123",
            "customer_name": "Test",
            "customer_country": "TH",
            "transaction_type": "exchange",
            "transaction_amount_thb": 5844600,
            "total_amount": 5844600,
            "payment_method": "cash",
            "customer_age": None,  # 注意：Python中的None
            "exchange_type": "normal"
        }

        print("\n[数据]")
        print(json.dumps(data, indent=2, ensure_ascii=False))

        # 调用规则引擎
        result = RuleEngine.check_triggers(
            db_session=session,
            report_type='AMLO-1-01',
            data=data,
            branch_id=1
        )

        print("\n[结果]")
        print(f"triggered: {result['triggered']}")

        if result['triggered']:
            print("\n[OK] AMLO已触发!")
            print(f"  report_type: AMLO-1-01")
            print(f"  rule_name: {result['highest_priority_rule']['rule_name']}")
            print(f"  priority: {result['highest_priority_rule']['priority']}")
            print(f"  message_cn: {result['message_cn']}")
            print(f"  allow_continue: {result['allow_continue']}")

            # 显示匹配的条件
            if 'matched_conditions' in result and result['matched_conditions']:
                print("\n[匹配的条件]")
                for idx, cond in enumerate(result['matched_conditions'], 1):
                    if 'field' in cond:
                        print(f"  {idx}. {cond['field']} {cond['operator']} {cond['expected_value']}")
                        print(f"     实际值: {cond['actual_value']}")

            # 显示未匹配的条件
            if 'unmatched_conditions' in result and result['unmatched_conditions']:
                print("\n[未匹配的条件]")
                for idx, cond in enumerate(result['unmatched_conditions'], 1):
                    if 'field' in cond:
                        print(f"  {idx}. {cond['field']} {cond['operator']} {cond['expected_value']}")
                        print(f"     实际值: {cond['actual_value']}")
        else:
            print("\n[FAIL] AMLO未触发 - 这不正常!")
            print("检查规则配置...")

            # 查看所有规则
            from sqlalchemy import text
            sql = text("""
                SELECT id, rule_name, rule_expression, is_active, priority
                FROM trigger_rules
                WHERE report_type = 'AMLO-1-01'
                ORDER BY priority DESC
            """)
            rules = session.execute(sql).fetchall()

            print(f"\n找到 {len(rules)} 条AMLO-1-01规则:")
            for rule in rules:
                rule_expr = json.loads(rule[2])
                print(f"\n  规则 {rule[0]}: {rule[1]}")
                print(f"    启用: {rule[3]}")
                print(f"    优先级: {rule[4]}")
                print(f"    条件: {json.dumps(rule_expr, ensure_ascii=False)}")

                # 手动测试这个规则
                is_matched, details = RuleEngine.evaluate_rule_with_details(rule_expr, data)
                print(f"    匹配结果: {is_matched}")

                if not is_matched:
                    print(f"    未匹配原因:")
                    for cond in details.get('unmatched', []):
                        if 'field' in cond:
                            print(f"      - {cond['field']}: 期望 {cond['operator']} {cond['expected_value']}, 实际 {cond['actual_value']}")
                        elif 'nested_logic' in cond:
                            print(f"      - 嵌套条件未匹配")

    finally:
        session.close()

if __name__ == '__main__':
    test_exact_data()

# -*- coding: utf-8 -*-
"""
测试180,000 USD卖出交易是否触发AMLO
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.db_service import SessionLocal
from services.repform.rule_engine import RuleEngine
import json

def test_180000_usd_sell():
    """测试卖出180,000 USD的场景"""
    print("=" * 80)
    print("[测试] 卖出180,000 USD (约5,844,600 THB) 是否触发AMLO")
    print("=" * 80)

    session = SessionLocal()

    try:
        # 假设USD汇率为32.47 THB (180,000 * 32.47 = 5,844,600)
        usd_amount = 180000
        usd_rate = 32.47
        thb_amount = usd_amount * usd_rate

        print(f"\n[交易数据]")
        print(f"  卖出币种: USD")
        print(f"  卖出金额: {usd_amount:,.2f} USD")
        print(f"  汇率: {usd_rate}")
        print(f"  泰铢金额: {thb_amount:,.2f} THB")

        # 构建测试数据
        data = {
            "customer_id": "1234567890123",
            "customer_name": "测试客户",
            "customer_country": "TH",
            "transaction_type": "exchange",
            "transaction_amount_thb": thb_amount,
            "total_amount": thb_amount,
            "payment_method": "cash",
            "customer_age": None,
            "exchange_type": "normal"
        }

        print(f"\n[检查数据]")
        print(json.dumps(data, indent=2, ensure_ascii=False))

        # 获取正确的branch_id
        from sqlalchemy import text
        branch_sql = text("SELECT id, branch_code FROM branches LIMIT 1")
        branch = session.execute(branch_sql).fetchone()
        branch_id = branch[0] if branch else 1

        print(f"\n[Branch信息]")
        print(f"  branch_id: {branch_id}")
        print(f"  branch_code: {branch[1] if branch else 'N/A'}")

        # 测试AMLO-1-01
        print("\n" + "=" * 80)
        print("[测试] AMLO-1-01 触发检查")
        print("=" * 80)

        result_101 = RuleEngine.check_triggers(
            db_session=session,
            report_type='AMLO-1-01',
            data=data,
            branch_id=branch_id
        )

        print(f"\n[AMLO-1-01 结果]")
        print(f"  triggered: {result_101['triggered']}")

        if result_101['triggered']:
            print(f"  ✓ 已触发 AMLO-1-01")
            print(f"  规则名称: {result_101['highest_priority_rule']['rule_name']}")
            print(f"  优先级: {result_101['highest_priority_rule']['priority']}")
            print(f"  消息: {result_101['message_cn']}")

            if 'matched_conditions' in result_101:
                print(f"\n  [匹配的条件]")
                for cond in result_101['matched_conditions']:
                    if 'field' in cond:
                        print(f"    - {cond['field']} {cond['operator']} {cond['expected_value']}")
                        print(f"      实际值: {cond['actual_value']}")
        else:
            print(f"  ✗ 未触发 AMLO-1-01 - 这不正常!")

            # 详细分析为什么没触发
            print(f"\n  [诊断] 检查规则匹配情况:")

            # 手动获取所有AMLO-1-01规则
            rules_sql = text("""
                SELECT id, rule_name, rule_expression, is_active, priority, branch_id
                FROM trigger_rules
                WHERE report_type = 'AMLO-1-01'
                    AND is_active = TRUE
                    AND (branch_id IS NULL OR branch_id = :branch_id)
                ORDER BY priority DESC
            """)
            rules = session.execute(rules_sql, {"branch_id": branch_id}).fetchall()

            print(f"\n  找到 {len(rules)} 条活跃的AMLO-1-01规则")

            for rule in rules:
                rule_id, rule_name, rule_expr_str, is_active, priority, rule_branch_id = rule
                rule_expr = json.loads(rule_expr_str)

                print(f"\n  [规则 {rule_id}] {rule_name}")
                print(f"    优先级: {priority}")
                print(f"    branch_id: {rule_branch_id}")
                print(f"    表达式: {json.dumps(rule_expr, ensure_ascii=False)}")

                # 手动评估规则
                is_matched, details = RuleEngine.evaluate_rule_with_details(rule_expr, data)
                print(f"    匹配结果: {'✓ 匹配' if is_matched else '✗ 不匹配'}")

                if not is_matched:
                    print(f"    未匹配原因:")
                    for cond in details.get('unmatched', []):
                        if 'field' in cond:
                            print(f"      - {cond['field']}: 期望 {cond['operator']} {cond['expected_value']}, 实际 {cond['actual_value']}")

        # 测试AMLO-1-02
        print("\n" + "=" * 80)
        print("[测试] AMLO-1-02 触发检查")
        print("=" * 80)

        result_102 = RuleEngine.check_triggers(
            db_session=session,
            report_type='AMLO-1-02',
            data=data,
            branch_id=branch_id
        )

        print(f"\n[AMLO-1-02 结果]")
        print(f"  triggered: {result_102['triggered']}")
        if result_102['triggered']:
            print(f"  ✓ 已触发 AMLO-1-02")
        else:
            print(f"  ✗ 未触发 AMLO-1-02 (正常，因为exchange_type不是asset_mortgage)")

        # 测试AMLO-1-03
        print("\n" + "=" * 80)
        print("[测试] AMLO-1-03 触发检查")
        print("=" * 80)

        result_103 = RuleEngine.check_triggers(
            db_session=session,
            report_type='AMLO-1-03',
            data=data,
            branch_id=branch_id
        )

        print(f"\n[AMLO-1-03 结果]")
        print(f"  triggered: {result_103['triggered']}")
        if result_103['triggered']:
            print(f"  ✓ 已触发 AMLO-1-03")
        else:
            print(f"  ✗ 未触发 AMLO-1-03 (正常，因为没有30天累计数据)")

        print("\n" + "=" * 80)
        print("[总结]")
        print("=" * 80)
        print(f"AMLO-1-01: {'✓ 触发' if result_101['triggered'] else '✗ 未触发'}")
        print(f"AMLO-1-02: {'✓ 触发' if result_102['triggered'] else '✗ 未触发'}")
        print(f"AMLO-1-03: {'✓ 触发' if result_103['triggered'] else '✗ 未触发'}")

    finally:
        session.close()

if __name__ == '__main__':
    test_180000_usd_sell()

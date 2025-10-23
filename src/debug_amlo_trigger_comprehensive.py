# -*- coding: utf-8 -*-
"""
AMLO触发条件综合调试工具
用于诊断用户报告的问题：卖出200,000 USD获得6,494,000 THB应该触发AMLO-1-01但未触发

执行方式：
cd src && python debug_amlo_trigger_comprehensive.py
"""

from services.db_service import SessionLocal
from services.repform import RuleEngine
from sqlalchemy import text
import json

def main():
    print("=" * 80)
    print("AMLO触发条件综合诊断工具")
    print("=" * 80)

    session = SessionLocal()

    try:
        # 步骤1: 查询AMLO-1-01的触发规则
        print("\n[步骤1] 查询AMLO-1-01触发规则配置")
        print("-" * 80)

        sql = text("""
            SELECT id, rule_name, report_type, rule_expression, priority,
                   is_active, allow_continue, warning_message_cn, branch_id
            FROM trigger_rules
            WHERE report_type = 'AMLO-1-01'
            ORDER BY priority DESC, id ASC
        """)

        result = session.execute(sql)
        rules = result.fetchall()

        if not rules:
            print("❌ 错误：未找到AMLO-1-01的触发规则！")
            return

        print(f"✅ 找到 {len(rules)} 条AMLO-1-01触发规则：\n")

        for rule in rules:
            print(f"规则ID: {rule[0]}")
            print(f"规则名: {rule[1]}")
            print(f"优先级: {rule[4]}")
            print(f"启用状态: {'启用' if rule[5] else '禁用'}")
            print(f"网点ID: {rule[8] if rule[8] else '全局规则'}")
            print(f"规则表达式: {rule[3]}")

            # 解析规则表达式
            try:
                expr = json.loads(rule[3])
                print(f"  逻辑运算符: {expr.get('logic', 'AND')}")
                print(f"  条件列表:")
                for i, cond in enumerate(expr.get('conditions', [])):
                    # 检查是否是嵌套条件
                    if 'logic' in cond and 'conditions' in cond:
                        print(f"    {i+1}. [嵌套条件] 逻辑={cond['logic']}")
                        for j, nested_cond in enumerate(cond.get('conditions', [])):
                            print(f"       {j+1}. {nested_cond.get('field')} {nested_cond.get('operator')} {nested_cond.get('value')}")
                    else:
                        print(f"    {i+1}. {cond.get('field')} {cond.get('operator')} {cond.get('value')}")
            except Exception as e:
                print(f"  ⚠️ 解析规则表达式失败: {e}")

            print()

        # 步骤2: 模拟用户报告的交易数据
        print("\n[步骤2] 模拟用户交易数据")
        print("-" * 80)
        print("用户报告：卖出 200,000 USD 获得 6,494,000 THB")
        print("应该触发：AMLO-1-01 (金额 >= 2,000,000 THB)")
        print()

        # 模拟前端发送的数据
        transaction_data = {
            'customer_id': '1234567890123',
            'customer_name': '测试客户',
            'customer_country': 'TH',
            'transaction_type': 'exchange',
            'transaction_amount_thb': 6494000,  # 前端发送的字段名
            'total_amount': 6494000,            # 后端期望的字段名
            'payment_method': 'cash'
        }

        print("交易数据:")
        for key, value in transaction_data.items():
            print(f"  {key}: {value}")
        print()

        # 步骤3: 使用RuleEngine检查触发
        print("\n[步骤3] 调用RuleEngine.check_triggers检查触发")
        print("-" * 80)

        try:
            trigger_result = RuleEngine.check_triggers(
                db_session=session,
                report_type='AMLO-1-01',
                data=transaction_data,
                branch_id=6  # 用户的网点ID
            )

            print("触发检查结果:")
            print(f"  triggered: {trigger_result['triggered']}")
            print(f"  allow_continue: {trigger_result['allow_continue']}")
            print(f"  匹配的规则数量: {len(trigger_result['trigger_rules'])}")

            if trigger_result['triggered']:
                print(f"\n✅ 成功触发AMLO-1-01!")
                print(f"  最高优先级规则: {trigger_result['highest_priority_rule']['rule_name']}")
                print(f"  警告消息(中文): {trigger_result['message_cn']}")

                # 显示匹配的条件
                if 'matched_conditions' in trigger_result:
                    print(f"\n  匹配的条件:")
                    for cond in trigger_result['matched_conditions']:
                        print(f"    ✓ {cond['field']} {cond['operator']} {cond['expected_value']}")
                        print(f"      实际值: {cond['actual_value']}")

                # 显示未匹配的条件
                if 'unmatched_conditions' in trigger_result:
                    print(f"\n  未匹配的条件:")
                    for cond in trigger_result['unmatched_conditions']:
                        print(f"    ✗ {cond['field']} {cond['operator']} {cond['expected_value']}")
                        print(f"      实际值: {cond['actual_value']}")
            else:
                print(f"\n❌ 未触发AMLO-1-01 - 这不符合预期！")
                print("\n诊断原因:")

                # 手动检查规则
                for rule in rules:
                    if not rule[5]:  # is_active
                        print(f"  - 规则 '{rule[1]}' (ID:{rule[0]}) 未启用")
                        continue

                    try:
                        expr = json.loads(rule[3])
                        is_matched, details = RuleEngine.evaluate_rule_with_details(expr, transaction_data)

                        print(f"\n  规则 '{rule[1]}' (ID:{rule[0]}) 评估结果: {'匹配' if is_matched else '不匹配'}")

                        # 显示匹配的条件
                        if details['matched']:
                            print(f"    匹配的条件:")
                            for cond in details['matched']:
                                print(f"      ✓ {cond['field']} {cond['operator']} {cond['expected_value']}")
                                print(f"        实际值: {cond['actual_value']}")

                        # 显示未匹配的条件
                        if details['unmatched']:
                            print(f"    未匹配的条件:")
                            for cond in details['unmatched']:
                                print(f"      ✗ {cond['field']} {cond['operator']} {cond['expected_value']}")
                                print(f"        实际值: {cond['actual_value']}")

                                # 诊断未匹配的原因
                                if cond['actual_value'] is None:
                                    print(f"        ⚠️ 字段 '{cond['field']}' 在交易数据中不存在或为None")
                                else:
                                    print(f"        ⚠️ 实际值类型: {type(cond['actual_value'])}, 期望值类型: {type(cond['expected_value'])}")

                    except Exception as e:
                        print(f"    ⚠️ 评估规则失败: {e}")
                        import traceback
                        traceback.print_exc()

        except Exception as e:
            print(f"❌ 调用RuleEngine.check_triggers失败: {e}")
            import traceback
            traceback.print_exc()

        # 步骤4: 测试不同的字段名
        print("\n\n[步骤4] 测试不同的字段名")
        print("-" * 80)

        test_cases = [
            {'field_name': 'total_amount', 'value': 6494000},
            {'field_name': 'transaction_amount_thb', 'value': 6494000},
            {'field_name': 'local_amount', 'value': 6494000},
            {'field_name': 'amount_thb', 'value': 6494000},
        ]

        for test_case in test_cases:
            test_data = {
                'customer_id': '1234567890123',
                test_case['field_name']: test_case['value']
            }

            print(f"\n测试字段名: '{test_case['field_name']}'")
            print(f"  数据: {test_data}")

            try:
                result = RuleEngine.check_triggers(
                    db_session=session,
                    report_type='AMLO-1-01',
                    data=test_data,
                    branch_id=6
                )

                if result['triggered']:
                    print(f"  ✅ 触发成功！")
                else:
                    print(f"  ❌ 未触发")
            except Exception as e:
                print(f"  ❌ 错误: {e}")

        # 步骤5: 给出修复建议
        print("\n\n[步骤5] 修复建议")
        print("=" * 80)
        print("""
如果以上测试显示规则正确配置但未触发，可能的原因包括：

1. **字段名不匹配**:
   - 规则配置中使用的字段名（如 'total_amount'）
   - 前端发送的字段名（如 'transaction_amount_thb'）
   - 这两者必须完全一致

2. **数据类型不匹配**:
   - 规则期望数值类型，但前端发送了字符串
   - 检查前端是否使用 parseInt() 或 parseFloat()

3. **规则未启用**:
   - 检查 trigger_rules 表中 is_active 字段是否为 TRUE

4. **网点过滤**:
   - 规则的 branch_id 字段如果不为 NULL，则只对特定网点生效
   - 检查用户的 branch_id=6 是否匹配规则的 branch_id

5. **前端逻辑错误**:
   - 前端可能在某些条件下跳过了触发检查
   - 检查前端代码中的 if 条件

建议的修复步骤：
1. 确认规则配置中的字段名
2. 修改前端发送数据时使用正确的字段名
3. 确保数值类型正确（不要发送字符串）
4. 添加调试日志到后端 RuleEngine.check_triggers 方法
5. 在前端添加 console.log 记录发送给后端的完整数据
""")

    finally:
        session.close()

if __name__ == '__main__':
    main()

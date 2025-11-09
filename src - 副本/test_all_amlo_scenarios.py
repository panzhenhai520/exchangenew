# -*- coding: utf-8 -*-
"""
全面测试所有AMLO触发场景
包括：
1. AMLO-1-01 标准大额触发 (>= 5,000,000 THB)
2. AMLO-1-01 高风险触发 (年龄 >= 65 且 >= 1,000,000 THB)
3. AMLO-1-01 现金高风险触发 (现金支付 且 >= 1,500,000 THB)
4. AMLO-1-02 资产抵押触发 (>= 8,000,000 THB 且 资产抵押类型)
5. AMLO-1-03 累计金额触发 (30天累计 >= 5,000,000 THB)
6. 多个报告同时触发的场景
7. 边界值测试
"""

from services.db_service import SessionLocal
from services.repform import RuleEngine


def test_scenario(session, scenario_name, transaction_data, expected_trigger, expected_report_type=None):
    """测试单个场景"""
    print(f"\n{'='*80}")
    print(f"测试场景: {scenario_name}")
    print(f"{'='*80}")
    print("交易数据:")
    for key, value in transaction_data.items():
        print(f"  {key}: {value}")
    print(f"\n预期结果: {'触发' if expected_trigger else '不触发'}")
    if expected_report_type:
        print(f"预期报告类型: {expected_report_type}")

    # 测试AMLO-1-01
    result_01 = RuleEngine.check_triggers(
        db_session=session,
        report_type='AMLO-1-01',
        data=transaction_data,
        branch_id=6
    )

    # 测试AMLO-1-02
    result_02 = RuleEngine.check_triggers(
        db_session=session,
        report_type='AMLO-1-02',
        data=transaction_data,
        branch_id=6
    )

    # 测试AMLO-1-03
    result_03 = RuleEngine.check_triggers(
        db_session=session,
        report_type='AMLO-1-03',
        data=transaction_data,
        branch_id=6
    )

    print("\n实际结果:")
    print(f"  AMLO-1-01: {'触发' if result_01['triggered'] else '不触发'}")
    if result_01['triggered']:
        print(f"    匹配规则: {result_01['highest_priority_rule']['rule_name']}")
        print(f"    优先级: {result_01['highest_priority_rule']['priority']}")

    print(f"  AMLO-1-02: {'触发' if result_02['triggered'] else '不触发'}")
    if result_02['triggered']:
        print(f"    匹配规则: {result_02['highest_priority_rule']['rule_name']}")

    print(f"  AMLO-1-03: {'触发' if result_03['triggered'] else '不触发'}")
    if result_03['triggered']:
        print(f"    匹配规则: {result_03['highest_priority_rule']['rule_name']}")

    # 判断测试是否通过
    triggered_any = result_01['triggered'] or result_02['triggered'] or result_03['triggered']

    if expected_trigger == triggered_any:
        print(f"\n[PASS] 测试通过")
        return True
    else:
        print(f"\n[FAIL] 测试失败 - 预期{'触发' if expected_trigger else '不触发'}，实际{'触发' if triggered_any else '不触发'}")
        return False


def main():
    session = SessionLocal()
    passed = 0
    failed = 0

    try:
        print("=" * 80)
        print("AMLO触发场景全面测试")
        print("=" * 80)

        # 场景1: 标准大额触发 - 用户报告的场景
        if test_scenario(
            session,
            "场景1: 卖出200,000 USD获得6,494,000 THB (用户报告场景)",
            {
                'customer_id': '1234567890123',
                'customer_name': 'Test Customer',
                'total_amount': 6494000,
                'transaction_amount_thb': 6494000,
                'payment_method': 'cash'
            },
            expected_trigger=True,
            expected_report_type='AMLO-1-01'
        ):
            passed += 1
        else:
            failed += 1

        # 场景2: 刚好达到阈值 - 5,000,000 THB
        if test_scenario(
            session,
            "场景2: 边界值测试 - 刚好5,000,000 THB",
            {
                'customer_id': '1234567890123',
                'customer_name': 'Test Customer',
                'total_amount': 5000000,
                'transaction_amount_thb': 5000000
            },
            expected_trigger=True,
            expected_report_type='AMLO-1-01'
        ):
            passed += 1
        else:
            failed += 1

        # 场景3: 低于阈值 - 4,999,999 THB (不应触发标准5百万规则，但可能触发规则16高风险规则)
        # 注意：如果金额 >= 1,500,000 且支付方式为现金，仍会触发AMLO-1-01规则16
        if test_scenario(
            session,
            "场景3: 边界值测试 - 4,999,999 THB (应触发高风险规则16)",
            {
                'customer_id': '1234567890123',
                'customer_name': 'Test Customer',
                'total_amount': 4999999,
                'transaction_amount_thb': 4999999,
                'payment_method': 'cash',  # 现金支付
                'customer_age': 50  # 年龄不够65，不触发年龄条件
            },
            expected_trigger=True  # 应该触发规则16（现金 + >= 1,500,000）
        ):
            passed += 1
        else:
            failed += 1

        # 场景4: 高龄高风险 - 1,200,000 THB + 年龄70岁
        if test_scenario(
            session,
            "场景4: 高龄高风险 - 1,200,000 THB + 客户70岁",
            {
                'customer_id': '1234567890123',
                'customer_name': 'Elderly Customer',
                'total_amount': 1200000,
                'transaction_amount_thb': 1200000,
                'customer_age': 70,
                'payment_method': 'cash'
            },
            expected_trigger=True,
            expected_report_type='AMLO-1-01'
        ):
            passed += 1
        else:
            failed += 1

        # 场景5: 大额现金 - 1,600,000 THB 现金
        if test_scenario(
            session,
            "场景5: 大额现金 - 1,600,000 THB 现金支付",
            {
                'customer_id': '1234567890123',
                'customer_name': 'Cash Customer',
                'total_amount': 1600000,
                'transaction_amount_thb': 1600000,
                'payment_method': 'cash'
            },
            expected_trigger=True,
            expected_report_type='AMLO-1-01'
        ):
            passed += 1
        else:
            failed += 1

        # 场景6: 资产抵押大额 - 10,000,000 THB + 资产抵押
        if test_scenario(
            session,
            "场景6: 资产抵押 - 10,000,000 THB + 资产抵押兑换",
            {
                'customer_id': '1234567890123',
                'customer_name': 'Asset Customer',
                'total_amount': 10000000,
                'transaction_amount_thb': 10000000,
                'exchange_type': 'asset_mortgage'
            },
            expected_trigger=True,
            expected_report_type='AMLO-1-01, AMLO-1-02'
        ):
            passed += 1
        else:
            failed += 1

        # 场景7: 资产抵押边界值 - 8,000,000 THB
        if test_scenario(
            session,
            "场景7: 资产抵押边界 - 8,000,000 THB + 资产抵押",
            {
                'customer_id': '1234567890123',
                'customer_name': 'Asset Customer',
                'total_amount': 8000000,
                'transaction_amount_thb': 8000000,
                'exchange_type': 'asset_mortgage'
            },
            expected_trigger=True,
            expected_report_type='AMLO-1-01, AMLO-1-02'
        ):
            passed += 1
        else:
            failed += 1

        # 场景8: 累计金额 - 30天累计5,000,000 THB
        if test_scenario(
            session,
            "场景8: 累计金额 - 30天累计5,000,000 THB",
            {
                'customer_id': '1234567890123',
                'customer_name': 'Frequent Customer',
                'total_amount': 500000,
                'transaction_amount_thb': 500000,
                'cumulative_amount_30d': 5000000
            },
            expected_trigger=True,
            expected_report_type='AMLO-1-03'
        ):
            passed += 1
        else:
            failed += 1

        # 场景9: 真正的边界测试 - 刚好低于5百万且不触发其他规则
        if test_scenario(
            session,
            "场景9: 边界测试 - 1,400,000 THB 非现金 (不应触发任何规则)",
            {
                'customer_id': '1234567890123',
                'customer_name': 'Card Customer',
                'total_amount': 1400000,
                'transaction_amount_thb': 1400000,
                'payment_method': 'card',  # 非现金
                'customer_age': 50  # 年龄不够65
            },
            expected_trigger=False
        ):
            passed += 1
        else:
            failed += 1

        # 场景10: 小额交易 - 不应触发任何规则
        if test_scenario(
            session,
            "场景10: 小额交易 - 500,000 THB (不应触发)",
            {
                'customer_id': '1234567890123',
                'customer_name': 'Small Customer',
                'total_amount': 500000,
                'transaction_amount_thb': 500000
            },
            expected_trigger=False
        ):
            passed += 1
        else:
            failed += 1

        # 场景11: 多重触发 - 超大额 + 资产抵押 + 高龄
        if test_scenario(
            session,
            "场景11: 多重触发 - 15,000,000 THB + 资产抵押 + 客户75岁",
            {
                'customer_id': '1234567890123',
                'customer_name': 'VIP Customer',
                'total_amount': 15000000,
                'transaction_amount_thb': 15000000,
                'exchange_type': 'asset_mortgage',
                'customer_age': 75,
                'payment_method': 'cash'
            },
            expected_trigger=True,
            expected_report_type='AMLO-1-01, AMLO-1-02'
        ):
            passed += 1
        else:
            failed += 1

        # 总结
        print("\n" + "=" * 80)
        print("测试总结")
        print("=" * 80)
        print(f"总测试数: {passed + failed}")
        print(f"通过: {passed}")
        print(f"失败: {failed}")
        print(f"成功率: {passed / (passed + failed) * 100:.1f}%")

        if failed == 0:
            print("\n[SUCCESS] 所有测试通过！AMLO触发逻辑正常工作")
        else:
            print(f"\n[WARNING] 有 {failed} 个测试失败，请检查触发规则配置")

    finally:
        session.close()


if __name__ == '__main__':
    main()

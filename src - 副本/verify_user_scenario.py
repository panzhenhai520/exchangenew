# -*- coding: utf-8 -*-
"""
验证用户报告的场景: 卖出200,000 USD获得6,494,000 THB
应该触发AMLO-1-01报告

执行方式:
cd src && python verify_user_scenario.py
"""

from services.db_service import SessionLocal
from services.repform import RuleEngine
import json

def main():
    print("=" * 80)
    print("验证用户场景: 卖出200,000 USD获得6,494,000 THB")
    print("=" * 80)

    session = SessionLocal()

    try:
        # 模拟用户交易数据
        transaction_data = {
            'customer_id': '1234567890123',
            'customer_name': '测试客户',
            'customer_country': 'TH',
            'transaction_type': 'exchange',
            'total_amount': 6494000,  # 6,494,000 THB
            'transaction_amount_thb': 6494000,
            'payment_method': 'cash',
            'from_currency': 'USD',
            'from_amount': 200000,
            'to_currency': 'THB',
            'to_amount': 6494000,
            'rate': 32.47
        }

        print("\n交易数据:")
        print(f"  方向: 卖出外币")
        print(f"  外币: {transaction_data['from_amount']:,.2f} USD")
        print(f"  本币: {transaction_data['total_amount']:,.2f} THB")
        print(f"  汇率: {transaction_data['rate']}")
        print(f"  客户: {transaction_data['customer_name']} ({transaction_data['customer_id']})")

        print("\n检查AMLO触发...")

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

        print("\n" + "=" * 80)
        print("触发结果:")
        print("=" * 80)

        if result_01['triggered']:
            print(f"\n[SUCCESS] AMLO-1-01 已触发！")
            print(f"  匹配规则: {result_01['highest_priority_rule']['rule_name']}")
            print(f"  规则优先级: {result_01['highest_priority_rule']['priority']}")
            print(f"  警告消息: {result_01['message_cn']}")
            print(f"  允许继续: {'是' if result_01['allow_continue'] else '否'}")
        else:
            print(f"\n[FAIL] AMLO-1-01 未触发")
            print("  这不符合预期！6,494,000 THB应该触发AMLO-1-01")

        if result_02['triggered']:
            print(f"\nAMLO-1-02 也触发了")
            print(f"  匹配规则: {result_02['highest_priority_rule']['rule_name']}")

        if result_03['triggered']:
            print(f"\nAMLO-1-03 也触发了")
            print(f"  匹配规则: {result_03['highest_priority_rule']['rule_name']}")

        print("\n" + "=" * 80)

        if result_01['triggered']:
            print("结论: 用户场景验证通过！AMLO触发系统工作正常。")
            print("\n下一步操作:")
            print("1. 重启后端服务: python src/main.py")
            print("2. 在前端测试相同的交易")
            print("3. 确认弹出AMLO预约表单")
            print("4. 检查报告编号是否包含币种代码（如: XXX-XXX-XX-XXXXXXUSD）")
        else:
            print("结论: AMLO触发系统仍有问题，请检查:")
            print("1. 数据库trigger_rules表是否已更新")
            print("2. 规则引擎代码是否已修改")
            print("3. 是否重启了Python进程")

        print("=" * 80)

    finally:
        session.close()

if __name__ == '__main__':
    main()

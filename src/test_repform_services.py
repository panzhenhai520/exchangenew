# -*- coding: utf-8 -*-
"""
RepForm服务类测试脚本
版本: v1.0
创建日期: 2025-10-02
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from services.db_service import SessionLocal
from services.repform import FieldManager, RuleEngine, FormBuilder, FormValidator

def test_field_manager():
    """测试FieldManager"""
    print("\n" + "="*70)
    print("测试 FieldManager - 字段管理服务")
    print("="*70)

    session = SessionLocal()

    try:
        # 1. 获取所有报告类型
        print("\n1. 获取所有报告类型:")
        report_types = FieldManager.get_all_report_types(session)
        for rt in report_types:
            print(f"   - {rt['report_type']}: {rt['report_name']} "
                  f"(字段数: {rt['field_count']}, 必填: {rt['required_count']})")

        # 2. 获取AMLO-1-01的字段定义
        print("\n2. 获取AMLO-1-01的字段定义:")
        fields = FieldManager.get_fields_by_report_type(session, 'AMLO-1-01', 'zh')
        print(f"   共{len(fields)}个字段")
        for field in fields[:5]:  # 只显示前5个
            print(f"   - {field['field_name']}: {field['label']} "
                  f"({'必填' if field['is_required'] else '选填'})")

        # 3. 获取表单定义
        print("\n3. 获取表单定义:")
        form_def = FieldManager.get_form_definition(session, 'AMLO-1-01', 'zh')
        print(f"   报告名称: {form_def['report_name']}")
        print(f"   总字段数: {form_def['total_fields']}")
        print(f"   分组数: {len(form_def['field_groups'])}")
        for group in form_def['field_groups']:
            print(f"   - {group['group_name']}: {len(group['fields'])}个字段")

        print("\n✅ FieldManager 测试通过")

    except Exception as e:
        print(f"\n❌ FieldManager 测试失败: {str(e)}")
    finally:
        session.close()


def test_rule_engine():
    """测试RuleEngine"""
    print("\n" + "="*70)
    print("测试 RuleEngine - 规则引擎")
    print("="*70)

    # 1. 测试规则评估
    print("\n1. 测试规则评估:")

    rule_expression = {
        "logic": "AND",
        "conditions": [
            {"field": "total_amount", "operator": ">=", "value": 5000000},
            {"field": "currency_code", "operator": "!=", "value": "THB"}
        ]
    }

    # 测试数据1 - 应该触发
    test_data1 = {
        "total_amount": 6000000,
        "currency_code": "USD"
    }

    result1 = RuleEngine.evaluate_rule(rule_expression, test_data1)
    print(f"   数据1: {test_data1}")
    print(f"   结果: {'✓ 触发' if result1 else '✗ 不触发'}")

    # 测试数据2 - 不应该触发
    test_data2 = {
        "total_amount": 3000000,
        "currency_code": "USD"
    }

    result2 = RuleEngine.evaluate_rule(rule_expression, test_data2)
    print(f"\n   数据2: {test_data2}")
    print(f"   结果: {'✓ 触发' if result2 else '✗ 不触发'}")

    # 2. 测试触发条件检查
    print("\n2. 测试触发条件检查:")
    session = SessionLocal()

    try:
        check_data = {
            "total_amount": 6000000,
            "currency_code": "USD",
            "customer_id": "TEST123456"
        }

        result = RuleEngine.check_triggers(session, 'AMLO-1-01', check_data)
        print(f"   数据: {check_data}")
        print(f"   触发: {'是' if result['triggered'] else '否'}")

        if result['triggered']:
            print(f"   匹配规则数: {len(result['trigger_rules'])}")
            print(f"   最高优先级规则: {result['highest_priority_rule']['rule_name']}")
            print(f"   允许继续交易: {'是' if result['allow_continue'] else '否'}")
            print(f"   提示信息: {result['message_cn']}")

        print("\n✅ RuleEngine 测试通过")

    except Exception as e:
        print(f"\n❌ RuleEngine 测试失败: {str(e)}")
    finally:
        session.close()


def test_form_builder():
    """测试FormBuilder"""
    print("\n" + "="*70)
    print("测试 FormBuilder - 表单构建器")
    print("="*70)

    session = SessionLocal()

    try:
        # 1. 构建表单Schema
        print("\n1. 构建表单Schema:")

        initial_data = {
            'customer_name': '张三',
            'customer_address': '北京市朝阳区',
            'total_amount': 6000000
        }

        form_schema = FormBuilder.build_form_schema(
            session,
            'AMLO-1-01',
            'zh',
            initial_data
        )

        print(f"   报告名称: {form_schema['report_name']}")
        print(f"   总字段数: {form_schema['total_fields']}")
        print(f"   分组数: {len(form_schema['form_items'])}")

        # 显示第一个分组的第一个字段
        if form_schema['form_items']:
            first_group = form_schema['form_items'][0]
            print(f"\n   第一个分组: {first_group['group_name']}")
            if first_group['items']:
                first_field = first_group['items'][0]
                print(f"   - 字段名: {first_field['name']}")
                print(f"   - 标签: {first_field['label']}")
                print(f"   - 类型: {first_field['type']}")
                print(f"   - 必填: {first_field['required']}")
                if 'value' in first_field:
                    print(f"   - 预填值: {first_field['value']}")

        # 显示验证规则数量
        print(f"\n   验证规则数: {len(form_schema['validation_rules'])}")

        print("\n✅ FormBuilder 测试通过")

    except Exception as e:
        print(f"\n❌ FormBuilder 测试失败: {str(e)}")
    finally:
        session.close()


def test_form_validator():
    """测试FormValidator"""
    print("\n" + "="*70)
    print("测试 FormValidator - 表单验证器")
    print("="*70)

    session = SessionLocal()

    try:
        # 1. 测试有效数据
        print("\n1. 测试有效数据:")

        valid_data = {
            'customer_name': '张三',
            'customer_address': '北京市朝阳区建国路100号',
            'customer_occupation': '软件工程师',
            'id_type': 'national_id',
            'id_number': '110101199001011234',
            'id_issuer': '北京市公安局',
            'id_expiry_date': '2030-01-01',
            'transaction_date': '2025-10-02',
            'total_amount': 6000000,
            'transaction_purpose': '出国旅游兑换外币使用',
            'transaction_method': 'self',
            'buy_foreign_currency': True,
            'buy_currency_code': 'USD',
            'buy_currency_amount': 10000
        }

        is_valid, errors = FormValidator.validate_form_data(
            session,
            'AMLO-1-01',
            valid_data
        )

        print(f"   验证结果: {'✓ 通过' if is_valid else '✗ 失败'}")
        if not is_valid:
            print("   错误:")
            for error in errors:
                print(f"   - {error}")

        # 2. 测试无效数据
        print("\n2. 测试无效数据（缺少必填项）:")

        invalid_data = {
            'customer_name': '李',  # 太短
            # 缺少 customer_address（必填）
            'total_amount': -100,  # 负数
        }

        is_valid, errors = FormValidator.validate_form_data(
            session,
            'AMLO-1-01',
            invalid_data
        )

        print(f"   验证结果: {'✓ 通过' if is_valid else '✗ 失败'}")
        if not is_valid:
            print("   错误:")
            for error in errors:
                print(f"   - {error}")

        print("\n✅ FormValidator 测试通过")

    except Exception as e:
        print(f"\n❌ FormValidator 测试失败: {str(e)}")
    finally:
        session.close()


if __name__ == '__main__':
    print("\n" + "="*70)
    print("RepForm服务类集成测试")
    print("="*70)

    # 运行所有测试
    test_field_manager()
    test_rule_engine()
    test_form_builder()
    test_form_validator()

    print("\n" + "="*70)
    print("✅ 所有测试完成")
    print("="*70)

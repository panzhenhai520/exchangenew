# -*- coding: utf-8 -*-
"""检查CTR(AMLO-1-01)触发规则"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from services.db_service import DatabaseService
from sqlalchemy import text
import json

def check_ctr_rules():
    session = DatabaseService.get_session()

    try:
        print("="*80)
        print("CTR (AMLO-1-01) 触发规则检查")
        print("="*80)

        # 查询AMLO-1-01规则
        result = session.execute(text("""
            SELECT id, rule_name, rule_expression, is_active, priority,
                   warning_message_cn
            FROM trigger_rules
            WHERE report_type = 'AMLO-1-01'
            ORDER BY priority DESC, id
        """))

        rules = result.fetchall()

        if not rules:
            print("\n⚠️  警告: 数据库中没有AMLO-1-01 (CTR) 触发规则！")
            print("   需要运行: python src/migrations/configure_amlo_trigger_rules.py")
            return

        print(f"\n找到 {len(rules)} 条AMLO-1-01 (CTR) 规则:\n")

        for i, rule in enumerate(rules, 1):
            print(f"【规则 {i}】")
            print(f"  ID: {rule.id}")
            print(f"  规则名称: {rule.rule_name}")
            print(f"  激活状态: {'✅ 激活' if rule.is_active else '❌ 未激活'}")
            print(f"  优先级: {rule.priority}")
            print(f"  警告信息: {rule.warning_message_cn}")

            # 解析规则表达式
            try:
                expr = json.loads(rule.rule_expression)
                print(f"  规则表达式:")
                print(f"    逻辑: {expr.get('logic', 'AND')}")

                conditions = expr.get('conditions', [])
                for j, cond in enumerate(conditions, 1):
                    field = cond.get('field', '?')
                    operator = cond.get('operator', '?')
                    value = cond.get('value', '?')

                    # 格式化金额显示
                    if field == 'total_amount' and isinstance(value, (int, float)):
                        value_display = f"{value:,.0f} THB ({value/10000:.0f}万THB)"
                    else:
                        value_display = str(value)

                    print(f"    条件{j}: {field} {operator} {value_display}")

            except json.JSONDecodeError:
                print(f"  ⚠️  规则表达式格式错误: {rule.rule_expression}")

            print()

        print("="*80)
        print("分析结果:")
        print("="*80)

        # 检查标准规则是否存在
        standard_threshold = 2000000  # 200万THB

        has_standard_rule = False
        for rule in rules:
            try:
                expr = json.loads(rule.rule_expression)
                conditions = expr.get('conditions', [])
                for cond in conditions:
                    if (cond.get('field') == 'total_amount' and
                        cond.get('operator') == '>=' and
                        cond.get('value') == standard_threshold):
                        has_standard_rule = True
                        break
            except:
                pass

        if has_standard_rule:
            print(f"✅ 标准CTR规则存在: total_amount >= {standard_threshold:,} THB (200万THB)")
        else:
            print(f"⚠️  警告: 未找到标准CTR规则 (>=200万THB)")

        # 分析用户提到的金额
        test_amount = 1948299
        print(f"\n📊 测试金额: {test_amount:,} THB ({test_amount/10000:.2f}万THB)")
        print(f"   标准阈值: {standard_threshold:,} THB (200万THB)")
        print(f"   差距: {test_amount - standard_threshold:,} THB")

        if test_amount >= standard_threshold:
            print("   ✅ 应该触发CTR报告")
        else:
            print("   ❌ 不应触发CTR报告（低于阈值）")

        # 检查所有激活规则是否会触发
        print(f"\n🔍 检查激活规则匹配情况:")
        triggered = False
        for rule in rules:
            if not rule.is_active:
                continue

            try:
                expr = json.loads(rule.rule_expression)
                conditions = expr.get('conditions', [])

                match = True
                for cond in conditions:
                    field = cond.get('field')
                    operator = cond.get('operator')
                    value = cond.get('value')

                    if field == 'total_amount':
                        if operator == '>=':
                            if test_amount < value:
                                match = False
                                print(f"   [{rule.id}] {rule.rule_name}: ❌ 不匹配 ({test_amount} < {value})")
                            else:
                                print(f"   [{rule.id}] {rule.rule_name}: ✅ 匹配 ({test_amount} >= {value})")
                        elif operator == '>':
                            if test_amount <= value:
                                match = False
                                print(f"   [{rule.id}] {rule.rule_name}: ❌ 不匹配 ({test_amount} <= {value})")
                            else:
                                print(f"   [{rule.id}] {rule.rule_name}: ✅ 匹配 ({test_amount} > {value})")

                if match:
                    triggered = True

            except Exception as e:
                print(f"   [{rule.id}] {rule.rule_name}: ⚠️  解析失败 ({e})")

        print("\n" + "="*80)
        print("结论:")
        print("="*80)

        if triggered:
            print(f"✅ 金额 {test_amount:,} THB 会触发CTR报告")
        else:
            print(f"❌ 金额 {test_amount:,} THB 不会触发CTR报告")
            print("   可能原因:")
            print("   1. 阈值设置过高")
            print("   2. 规则未激活")
            print("   3. 规则条件不匹配")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        DatabaseService.close_session(session)

if __name__ == "__main__":
    check_ctr_rules()

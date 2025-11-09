# -*- coding: utf-8 -*-
"""检查数据库规则和PDF填写逻辑"""
import sys
import os

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from services.db_service import DatabaseService
from sqlalchemy import text
import json

def check_trigger_rules():
    """检查数据库中的触发规则"""
    session = DatabaseService.get_session()

    try:
        print("="*80)
        print("1. 检查数据库中的AMLO触发规则配置")
        print("="*80)

        result = session.execute(text("""
            SELECT
                id,
                report_type,
                rule_name,
                rule_expression,
                is_active,
                priority,
                warning_message_cn,
                created_at
            FROM trigger_rules
            WHERE report_type LIKE 'AMLO%'
            ORDER BY report_type, priority DESC, id
        """))

        rules = result.fetchall()

        if not rules:
            print("\n⚠️  警告: 数据库中没有AMLO触发规则！")
            print("   需要运行: python src/migrations/configure_amlo_trigger_rules.py\n")
            return

        print(f"\n找到 {len(rules)} 条AMLO触发规则\n")

        # 按报告类型分组
        by_type = {}
        for rule in rules:
            rt = rule.report_type
            if rt not in by_type:
                by_type[rt] = []
            by_type[rt].append(rule)

        for report_type in ['AMLO-1-01', 'AMLO-1-02', 'AMLO-1-03']:
            if report_type not in by_type:
                print(f"⚠️  {report_type}: 无规则")
                continue

            type_rules = by_type[report_type]
            print(f"{'='*80}")
            print(f"{report_type} - 共 {len(type_rules)} 条规则")
            print(f"{'='*80}")

            for i, rule in enumerate(type_rules, 1):
                print(f"\n【规则 {i}】")
                print(f"  ID: {rule.id}")
                print(f"  规则名称: {rule.rule_name}")
                print(f"  激活状态: {'✅ 激活' if rule.is_active else '❌ 未激活'}")
                print(f"  优先级: {rule.priority}")
                print(f"  警告信息: {rule.warning_message_cn}")
                print(f"  创建时间: {rule.created_at}")

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

                        # 格式化显示
                        if isinstance(value, (int, float)) and field in ['total_amount', 'cumulative_amount_30d']:
                            value_display = f"{value:,.0f} THB ({value/10000:.1f}万THB)"
                        else:
                            value_display = str(value)

                        print(f"    条件{j}: {field} {operator} {value_display}")

                except json.JSONDecodeError as e:
                    print(f"  ⚠️  规则表达式格式错误: {e}")
                    print(f"     原始数据: {rule.rule_expression}")

            print()

        # 分析问题
        print("\n" + "="*80)
        print("分析: 1,948,299 THB 是否会触发CTR?")
        print("="*80)

        test_amount = 1948299
        print(f"\n测试金额: {test_amount:,} THB ({test_amount/10000:.2f}万THB)\n")

        if 'AMLO-1-01' not in by_type:
            print("❌ 无AMLO-1-01规则，不会触发")
            return

        triggered = False
        for rule in by_type['AMLO-1-01']:
            if not rule.is_active:
                print(f"[{rule.id}] {rule.rule_name}: ⏭️  跳过（未激活）")
                continue

            try:
                expr = json.loads(rule.rule_expression)
                conditions = expr.get('conditions', [])

                all_match = True
                for cond in conditions:
                    field = cond.get('field')
                    operator = cond.get('operator')
                    value = cond.get('value')

                    if field == 'total_amount':
                        if operator == '>=':
                            match = (test_amount >= value)
                        elif operator == '>':
                            match = (test_amount > value)
                        elif operator == '<=':
                            match = (test_amount <= value)
                        elif operator == '<':
                            match = (test_amount < value)
                        elif operator == '==':
                            match = (test_amount == value)
                        else:
                            match = False

                        if match:
                            print(f"[{rule.id}] {rule.rule_name}: ✅ 匹配 ({test_amount:,} {operator} {value:,})")
                        else:
                            print(f"[{rule.id}] {rule.rule_name}: ❌ 不匹配 ({test_amount:,} {operator} {value:,})")
                            all_match = False

                if all_match and len(conditions) > 0:
                    triggered = True

            except Exception as e:
                print(f"[{rule.id}] {rule.rule_name}: ⚠️  解析错误 ({e})")

        print("\n" + "="*80)
        print("结论:")
        print("="*80)

        if triggered:
            print(f"✅ 金额 {test_amount:,} THB 会触发AMLO-1-01 (CTR)")
            print(f"   ⚠️  警告: 这不符合标准（标准阈值应为 2,000,000 THB）")
            print(f"   建议: 运行 python src/migrations/configure_amlo_trigger_rules.py 重置规则")
        else:
            print(f"❌ 金额 {test_amount:,} THB 不会触发AMLO-1-01 (CTR)")
            print(f"   ✅ 这是正确的（低于标准阈值 2,000,000 THB）")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        DatabaseService.close_session(session)

if __name__ == "__main__":
    check_trigger_rules()

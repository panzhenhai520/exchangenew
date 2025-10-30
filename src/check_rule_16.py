# -*- coding: utf-8 -*-
"""检查规则16的详细内容"""
import sys
import os

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from services.db_service import DatabaseService
from sqlalchemy import text
import json

session = DatabaseService.get_session()

try:
    result = session.execute(text('SELECT id, rule_name, rule_expression FROM trigger_rules WHERE id=16')).fetchone()

    print("="*80)
    print("规则16详情:")
    print("="*80)
    print(f'ID: {result.id}')
    print(f'名称: {result.rule_name}')
    print(f'\n原始表达式:\n{result.rule_expression}')

    expr = json.loads(result.rule_expression)
    print(f'\n解析后的JSON:')
    print(json.dumps(expr, indent=2, ensure_ascii=False))

    # 分析规则
    print("\n" + "="*80)
    print("规则分析:")
    print("="*80)

    logic = expr.get('logic', 'AND')
    conditions = expr.get('conditions', [])

    print(f"逻辑: {logic}")
    print(f"条件数量: {len(conditions)}\n")

    for i, cond in enumerate(conditions, 1):
        print(f"条件{i}:")
        for key, value in cond.items():
            print(f"  {key}: {value}")
        print()

    # 测试1,948,299是否匹配
    print("="*80)
    print("测试: 1,948,299 THB 是否匹配规则16?")
    print("="*80)

    test_amount = 1948299

    if logic == 'OR':
        print(f"\n逻辑: OR - 任一条件满足即触发\n")

        any_match = False
        for i, cond in enumerate(conditions, 1):
            field = cond.get('field')
            operator = cond.get('operator')
            value = cond.get('value')

            print(f"条件{i}: {field} {operator} {value}")

            if field == 'total_amount':
                if operator == '>=':
                    match = (test_amount >= value)
                elif operator == '>':
                    match = (test_amount > value)
                else:
                    match = False

                if match:
                    print(f"  ✅ 匹配! ({test_amount:,} {operator} {value:,})")
                    any_match = True
                else:
                    print(f"  ❌ 不匹配 ({test_amount:,} < {value:,})")
            else:
                print(f"  ⏭️  跳过（字段不是total_amount）")

        if any_match:
            print(f"\n🚨 结论: 规则16会触发! (OR逻辑，至少一个条件满足)")
        else:
            print(f"\n✅ 结论: 规则16不会触发")

finally:
    DatabaseService.close_session(session)

# -*- coding: utf-8 -*-
"""
检查AMLO触发规则配置
"""
from services.db_service import DatabaseService
from sqlalchemy import text
import json

def main():
    with DatabaseService.get_session() as session:
        # 查询AMLO触发规则
        result = session.execute(text("""
            SELECT report_type, rule_name, is_active, priority, rule_expression
            FROM trigger_rules
            WHERE report_type IN ('AMLO-1-01', 'AMLO-1-02', 'AMLO-1-03')
            ORDER BY report_type, priority DESC
        """))

        rules = list(result)

        # 按报告类型分组
        amlo_101 = [r for r in rules if r[0] == 'AMLO-1-01']
        amlo_102 = [r for r in rules if r[0] == 'AMLO-1-02']
        amlo_103 = [r for r in rules if r[0] == 'AMLO-1-03']

        print('\n' + '=' * 100)
        print('AMLO 触发规则配置')
        print('=' * 100)

        # AMLO-1-01
        print(f'\n【AMLO-1-01 现金交易报告 (CTR)】: {len(amlo_101)} 条规则')
        for rule in amlo_101:
            status = '启用' if rule[2] else '禁用'
            print(f'\n  规则名称: {rule[1]}')
            print(f'  状态: {status} | 优先级: {rule[3]}')
            try:
                expr = json.loads(rule[4])
                print(f'  触发条件:')
                print_rule_expression(expr, indent=4)
            except:
                print(f'  触发条件: {rule[4][:100]}')

        # AMLO-1-02
        print(f'\n\n【AMLO-1-02 资产交易报告 (ATR)】: {len(amlo_102)} 条规则')
        for rule in amlo_102:
            status = '启用' if rule[2] else '禁用'
            print(f'\n  规则名称: {rule[1]}')
            print(f'  状态: {status} | 优先级: {rule[3]}')
            try:
                expr = json.loads(rule[4])
                print(f'  触发条件:')
                print_rule_expression(expr, indent=4)
            except:
                print(f'  触发条件: {rule[4][:100]}')

        # AMLO-1-03
        print(f'\n\n【AMLO-1-03 可疑交易报告 (STR)】: {len(amlo_103)} 条规则')
        for rule in amlo_103:
            status = '启用' if rule[2] else '禁用'
            print(f'\n  规则名称: {rule[1]}')
            print(f'  状态: {status} | 优先级: {rule[3]}')
            try:
                expr = json.loads(rule[4])
                print(f'  触发条件:')
                print_rule_expression(expr, indent=4)
            except:
                print(f'  触发条件: {rule[4][:100]}')

        print('\n' + '=' * 100)
        print('总结:')
        print(f'  AMLO-1-01: {len([r for r in amlo_101 if r[2]])} 条启用规则')
        print(f'  AMLO-1-02: {len([r for r in amlo_102 if r[2]])} 条启用规则')
        print(f'  AMLO-1-03: {len([r for r in amlo_103 if r[2]])} 条启用规则')
        print('=' * 100 + '\n')

def print_rule_expression(expr, indent=0):
    """打印规则表达式"""
    prefix = ' ' * indent
    logic = expr.get('logic', 'AND')
    conditions = expr.get('conditions', [])

    if logic in ['AND', 'OR']:
        print(f'{prefix}逻辑关系: {logic}')
        for i, cond in enumerate(conditions, 1):
            if 'field' in cond:
                # 单个条件
                field = cond.get('field', '')
                operator = cond.get('operator', '')
                value = cond.get('value', '')
                print(f'{prefix}  条件{i}: {field} {operator} {format_value(value)}')
            elif 'logic' in cond:
                # 嵌套逻辑
                print(f'{prefix}  嵌套条件{i}:')
                print_rule_expression(cond, indent + 4)

def format_value(value):
    """格式化值显示"""
    if isinstance(value, (int, float)):
        if value >= 1000000:
            return f'{value:,.0f} ({value/1000000:.1f}M)'
        elif value >= 1000:
            return f'{value:,.0f} ({value/1000:.0f}K)'
        return f'{value:,.0f}'
    return str(value)

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""调试规则引擎"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Windows UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from services.db_service import DatabaseService
from services.repform.rule_engine import RuleEngine
from sqlalchemy import text
import json

session = DatabaseService.get_session()

try:
    print("="*80)
    print("规则引擎调试")
    print("="*80)
    
    # 测试数据
    test_data = {
        'customer_id': '1234567890123',
        'total_amount': 2130000,
        'amount': 60000,
        'currency_code': 'USD',
        'direction': 'buy',
        'branch_id': 1
    }
    
    print(f"\n测试数据:")
    for key, value in test_data.items():
        print(f"  {key}: {value}")
    
    # 获取AMLO-1-01规则
    result = session.execute(text("""
        SELECT id, rule_name, rule_expression, is_active
        FROM trigger_rules
        WHERE report_type = 'AMLO-1-01'
        AND is_active = 1
        ORDER BY priority DESC
        LIMIT 1
    """))
    
    rule = result.fetchone()
    
    if not rule:
        print("\n[ERROR] 未找到启用的AMLO-1-01规则")
    else:
        print(f"\n找到规则:")
        print(f"  ID: {rule[0]}")
        print(f"  名称: {rule[1]}")
        print(f"  表达式: {rule[2]}")
        print(f"  启用: {'是' if rule[3] else '否'}")
        
        # 解析规则
        expr = json.loads(rule[2])
        print(f"\n解析后的规则:")
        print(f"  逻辑: {expr['logic']}")
        print(f"  条件数: {len(expr['conditions'])}")
        
        for i, cond in enumerate(expr['conditions'], 1):
            print(f"\n  条件{i}:")
            print(f"    字段: {cond['field']}")
            print(f"    操作符: {cond['operator']}")
            print(f"    值: {cond['value']}")
            
            # 检查字段是否存在
            field_name = cond['field']
            if field_name in test_data:
                actual_value = test_data[field_name]
                print(f"    实际值: {actual_value}")
                
                # 评估条件
                operator = cond['operator']
                expected_value = cond['value']
                
                if operator == '>=':
                    match = actual_value >= expected_value
                elif operator == '==':
                    match = actual_value == expected_value
                else:
                    match = False
                
                print(f"    匹配: {'是' if match else '否'}")
            else:
                print(f"    [WARN] 字段不存在于测试数据中")
        
        # 调用规则引擎
        print(f"\n调用规则引擎...")
        result = RuleEngine.check_triggers(session, 'AMLO-1-01', test_data, 1)
        
        print(f"\n规则引擎返回:")
        print(f"  triggered: {result.get('triggered')}")
        print(f"  triggered_reports: {result.get('triggered_reports', [])}")
        
        if result.get('triggered'):
            print(f"\n[OK] 规则触发成功!")
        else:
            print(f"\n[ERROR] 规则未触发")
            print(f"  原因可能:")
            print(f"    1. 字段名不匹配")
            print(f"    2. 规则表达式解析错误")
            print(f"    3. RuleEngine逻辑问题")

except Exception as e:
    print(f"\n[ERROR] 测试异常: {e}")
    import traceback
    traceback.print_exc()
finally:
    DatabaseService.close_session(session)


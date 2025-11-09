#!/usr/bin/env python3
"""
测试嵌套条件
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.repform.rule_engine import RuleEngine
import json

def test_nested_conditions():
    print("=== 测试嵌套条件 ===")
    
    # 测试数据
    test_data = {
        'customer_id': '1233123',
        'total_amount': 6690000,
        'payment_method': 'cash',
        'customer_age': 30  # 小于65
    }
    
    print(f"测试数据: {test_data}")
    
    # 测试规则16的第二个条件
    rule16_second_condition = {
        "logic": "AND",
        "conditions": [
            {"field": "total_amount", "operator": ">=", "value": 1500000},
            {"field": "payment_method", "operator": "==", "value": "cash"}
        ]
    }
    
    print(f"\n测试规则16的第二个条件:")
    print(f"表达式: {rule16_second_condition}")
    
    result = RuleEngine.evaluate_rule(rule16_second_condition, test_data)
    print(f"结果: {result}")
    
    # 测试完整的规则16
    rule16_full = {
        "logic": "OR",
        "conditions": [
            {
                "logic": "AND",
                "conditions": [
                    {"field": "total_amount", "operator": ">=", "value": 1000000},
                    {"field": "customer_age", "operator": ">=", "value": 65}
                ]
            },
            {
                "logic": "AND",
                "conditions": [
                    {"field": "total_amount", "operator": ">=", "value": 1500000},
                    {"field": "payment_method", "operator": "==", "value": "cash"}
                ]
            }
        ]
    }
    
    print(f"\n测试完整的规则16:")
    print(f"表达式: {rule16_full}")
    
    result = RuleEngine.evaluate_rule(rule16_full, test_data)
    print(f"结果: {result}")
    
    # 期望结果: True，因为第二个条件应该匹配

if __name__ == "__main__":
    test_nested_conditions()

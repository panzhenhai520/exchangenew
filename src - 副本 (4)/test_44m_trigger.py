#!/usr/bin/env python3
"""
测试44,600,000 THB的AMLO触发
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.repform.rule_engine import RuleEngine

def test_44m_trigger():
    print("=== 测试44,600,000 THB的AMLO触发 ===")
    
    # 测试数据（与用户截图一致）
    test_data = {
        'customer_id': '1233123',
        'customer_name': 'Panython',
        'customer_country': 'BD', 
        'transaction_type': 'exchange',
        'transaction_amount_thb': 44600000,
        'total_amount': 44600000,
        'payment_method': 'cash'
    }
    
    print(f"交易金额: {test_data['total_amount']:,} THB")
    print(f"AMLO阈值: 2,000,000 THB")
    print(f"是否超过阈值: {test_data['total_amount'] >= 2000000}")
    
    # 测试规则13
    rule13 = {
        'logic': 'AND', 
        'conditions': [
            {'field': 'total_amount', 'operator': '>=', 'value': 2000000}
        ]
    }
    
    result13 = RuleEngine.evaluate_rule(rule13, test_data)
    print(f"规则13触发结果: {result13}")
    
    # 测试规则16
    rule16 = {
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
    
    result16 = RuleEngine.evaluate_rule(rule16, test_data)
    print(f"规则16触发结果: {result16}")
    
    print("\n=== 总结 ===")
    if result13 or result16:
        print("[SUCCESS] AMLO报告应该被触发！")
        print("[SUCCESS] 应该弹出预约表单！")
    else:
        print("[FAILED] AMLO报告不会被触发")

if __name__ == "__main__":
    test_44m_trigger()
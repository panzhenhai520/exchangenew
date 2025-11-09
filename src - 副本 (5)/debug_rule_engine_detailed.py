#!/usr/bin/env python3
"""
详细调试规则引擎
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from services.repform.rule_engine import RuleEngine
from sqlalchemy import text
import json

def debug_rule_engine():
    session = DatabaseService.get_session()
    try:
        print("=== 详细调试规则引擎 ===")
        
        # 测试数据
        test_data = {
            'customer_id': '1233123',
            'customer_name': 'Panython',
            'customer_country': 'BD',
            'transaction_type': 'exchange',
            'transaction_amount_thb': 6690000,
            'total_amount': 6690000,
            'payment_method': 'cash'
        }
        
        print(f"测试数据: {test_data}")
        print()
        
        # 获取规则
        rules = session.execute(text("""
            SELECT id, rule_name, rule_expression, is_active
            FROM trigger_rules 
            WHERE report_type = 'AMLO-1-01' AND is_active = TRUE
            ORDER BY id
        """)).fetchall()
        
        for rule in rules:
            rule_id, rule_name, rule_expression, is_active = rule
            print(f"\n=== 规则 {rule_id}: {rule_name} ===")
            print(f"原始表达式: {rule_expression}")
            
            # 解析JSON表达式
            try:
                expression = json.loads(rule_expression)
                print(f"解析后表达式: {expression}")
                
                logic = expression.get('logic', 'AND')
                conditions = expression.get('conditions', [])
                
                print(f"逻辑操作符: {logic}")
                print(f"条件数量: {len(conditions)}")
                
                # 逐个检查条件
                for i, condition in enumerate(conditions):
                    print(f"\n  条件 {i+1}: {condition}")
                    
                    field_name = condition.get('field')
                    operator = condition.get('operator')
                    expected_value = condition.get('value')
                    actual_value = test_data.get(field_name)
                    
                    print(f"    字段名: {field_name}")
                    print(f"    操作符: {operator}")
                    print(f"    期望值: {expected_value} (类型: {type(expected_value)})")
                    print(f"    实际值: {actual_value} (类型: {type(actual_value)})")
                    
                    # 手动执行比较
                    try:
                        result = RuleEngine._compare_values(actual_value, operator, expected_value)
                        print(f"    比较结果: {result}")
                        
                        if operator == '>=':
                            print(f"    详细: {actual_value} >= {expected_value} = {float(actual_value) >= float(expected_value)}")
                        elif operator == '==':
                            print(f"    详细: {actual_value} == {expected_value} = {str(actual_value) == str(expected_value)}")
                            
                    except Exception as e:
                        print(f"    比较失败: {e}")
                
                # 使用规则引擎评估
                print(f"\n  使用规则引擎评估:")
                try:
                    result = RuleEngine.evaluate_rule(expression, test_data)
                    print(f"    规则引擎结果: {result}")
                    
                    # 使用详细评估
                    detailed_result, details = RuleEngine.evaluate_rule_with_details(expression, test_data)
                    print(f"    详细评估结果: {detailed_result}")
                    print(f"    匹配的条件: {len(details['matched'])}")
                    print(f"    未匹配的条件: {len(details['unmatched'])}")
                    
                    for matched in details['matched']:
                        print(f"      匹配: {matched}")
                    for unmatched in details['unmatched']:
                        print(f"      未匹配: {unmatched}")
                        
                except Exception as e:
                    print(f"    规则引擎评估失败: {e}")
                    import traceback
                    traceback.print_exc()
                    
            except Exception as e:
                print(f"解析规则表达式失败: {e}")
                
    except Exception as e:
        print(f"调试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    debug_rule_engine()

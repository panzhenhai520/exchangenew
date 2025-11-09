#!/usr/bin/env python3
"""
调试AMLO触发逻辑
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from services.repform.rule_engine import RuleEngine
from sqlalchemy import text

def test_amlo_trigger():
    session = DatabaseService.get_session()
    try:
        print("=== AMLO触发逻辑测试 ===")
        
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
        
        # 检查触发规则
        rules = session.execute(text("""
            SELECT id, rule_name, rule_expression, is_active
            FROM trigger_rules 
            WHERE report_type = 'AMLO-1-01' AND is_active = TRUE
            ORDER BY id
        """)).fetchall()
        
        print(f"AMLO-1-01规则数量: {len(rules)}")
        
        # 测试每个规则
        rule_engine = RuleEngine()
        
        for rule in rules:
            rule_id, rule_name, rule_expression, is_active = rule
            print(f"\n规则 {rule_id}: {rule_name}")
            print(f"  表达式: {rule_expression}")
            print(f"  状态: {'启用' if is_active else '禁用'}")
            
            if is_active:
                try:
                    # 打印测试数据中的字段
                    print(f"  测试数据字段: {list(test_data.keys())}")
                    print(f"  total_amount值: {test_data.get('total_amount')}")
                    print(f"  transaction_amount_thb值: {test_data.get('transaction_amount_thb')}")
                    
                    # 直接调用规则引擎检查
                    result = rule_engine.evaluate_rule(rule_expression, test_data)
                    print(f"  触发结果: {result}")
                    
                    if result:
                        print(f"  [SUCCESS] 规则 {rule_id} 被触发！")
                    else:
                        print(f"  [FAILED] 规则 {rule_id} 未触发")
                        
                except Exception as e:
                    print(f"  [ERROR] 规则 {rule_id} 执行失败: {e}")
                    import traceback
                    traceback.print_exc()
        
        # 测试完整的触发检查
        print(f"\n=== 完整触发检查测试 ===")
        try:
            # 模拟API调用
            trigger_result = rule_engine.check_triggers('AMLO-1-01', test_data, branch_id=1)
            print(f"完整触发检查结果: {trigger_result}")
            
            if trigger_result.get('triggered'):
                print("[SUCCESS] AMLO报告应该被触发！")
            else:
                print("[FAILED] AMLO报告不会被触发")
                
        except Exception as e:
            print(f"[ERROR] 完整触发检查失败: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_amlo_trigger()

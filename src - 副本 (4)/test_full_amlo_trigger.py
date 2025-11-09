#!/usr/bin/env python3
"""
测试完整的AMLO触发检查
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from services.repform.rule_engine import RuleEngine
from sqlalchemy import text

def test_full_amlo_trigger():
    session = DatabaseService.get_session()
    try:
        print("=== 测试完整的AMLO触发检查 ===")
        
        # 测试数据（与用户截图一致）
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
        
        # 获取所有AMLO-1-01规则
        rules = session.execute(text("""
            SELECT id, rule_name, rule_expression, is_active
            FROM trigger_rules 
            WHERE report_type = 'AMLO-1-01' AND is_active = TRUE
            ORDER BY id
        """)).fetchall()
        
        print(f"AMLO-1-01规则数量: {len(rules)}")
        
        # 检查每个规则
        triggered_rules = []
        for rule in rules:
            rule_id, rule_name, rule_expression, is_active = rule
            print(f"\n规则 {rule_id}: {rule_name}")
            
            if is_active:
                try:
                    import json
                    expression = json.loads(rule_expression)
                    result = RuleEngine.evaluate_rule(expression, test_data)
                    print(f"  触发结果: {result}")
                    
                    if result:
                        triggered_rules.append(rule_id)
                        print(f"  [TRIGGERED] 规则 {rule_id} 被触发！")
                    else:
                        print(f"  [NOT TRIGGERED] 规则 {rule_id} 未触发")
                        
                except Exception as e:
                    print(f"  [ERROR] 规则 {rule_id} 执行失败: {e}")
        
        print(f"\n=== 总结 ===")
        if triggered_rules:
            print(f"[SUCCESS] 有 {len(triggered_rules)} 个规则被触发: {triggered_rules}")
            print(f"[SUCCESS] AMLO报告应该被生成！")
        else:
            print(f"[FAILED] 没有规则被触发")
            print(f"[FAILED] AMLO报告不会被生成")
            
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_full_amlo_trigger()

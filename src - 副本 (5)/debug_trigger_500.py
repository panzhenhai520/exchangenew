#!/usr/bin/env python3
"""
调试AMLO触发检查500错误
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from services.repform.rule_engine import RuleEngine
from sqlalchemy import text
import json

def test_trigger_check():
    """测试触发检查"""
    session = DatabaseService.get_session()
    
    try:
        print("="*60)
        print("调试AMLO触发检查500错误")
        print("="*60)
        
        # 模拟前端发送的数据
        trigger_data = {
            'customer_id': '1231231',
            'customer_name': '测试客户',
            'customer_country': 'TH',
            'transaction_type': 'exchange',
            'transaction_amount_thb': 13380000,
            'total_amount': 13380000,
            'current_branch_id': '6'  # TEST网点
        }
        
        print("\n1. 测试数据:")
        print(f"   客户ID: {trigger_data['customer_id']}")
        print(f"   交易金额: {trigger_data['total_amount']} THB")
        print(f"   网点ID: {trigger_data['current_branch_id']}")
        
        # 2. 检查触发规则
        print("\n2. 检查AMLO-1-01触发规则:")
        rules = session.execute(text("""
            SELECT 
                id, rule_name, rule_expression, is_active
            FROM trigger_rules 
            WHERE report_type = 'AMLO-1-01'
            AND is_active = TRUE
            ORDER BY priority DESC
        """)).fetchall()
        
        if rules:
            print(f"   找到 {len(rules)} 条规则\n")
            for rule in rules:
                print(f"   规则 ID {rule[0]}: {rule[1]}")
                print(f"   是否启用: {rule[3]}")
                
                try:
                    rule_expr = json.loads(rule[2])
                    print(f"   规则表达式: {json.dumps(rule_expr, ensure_ascii=False, indent=6)}")
                    
                    # 测试规则评估
                    print(f"\n   测试评估:")
                    try:
                        result = RuleEngine.evaluate_rule(rule_expr, trigger_data)
                        print(f"   评估结果: {result}")
                    except Exception as eval_error:
                        print(f"   [错误] 评估失败: {eval_error}")
                        import traceback
                        traceback.print_exc()
                    
                except Exception as e:
                    print(f"   [错误] 解析规则表达式失败: {e}")
                print()
        else:
            print("   [错误] 没有找到AMLO-1-01规则")
        
        # 3. 测试RuleEngine.check_triggers方法
        print("\n3. 测试RuleEngine.check_triggers方法:")
        try:
            triggers = RuleEngine.check_triggers(
                report_type='AMLO-1-01',
                data=trigger_data,
                branch_id=6
            )
            print(f"   触发结果: {triggers}")
        except Exception as e:
            print(f"   [错误] check_triggers失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 4. 检查branch_id类型
        print("\n4. 检查branch_id:")
        print(f"   current_branch_id类型: {type(trigger_data['current_branch_id'])} = {trigger_data['current_branch_id']}")
        print(f"   转换为int: {int(trigger_data['current_branch_id'])}")
        
        # 5. 建议
        print("\n5. 可能的问题:")
        print("   a) branch_id类型不匹配（字符串 vs 整数）")
        print("   b) RuleEngine.check_triggers方法内部错误")
        print("   c) 规则表达式评估失败")
        print("   d) 数据库查询异常")
        
        print("\n6. 建议检查:")
        print("   - 查看后端控制台的详细错误堆栈")
        print("   - 检查 src/routes/app_repform.py 的 check-trigger 端点")
        print("   - 检查 src/services/repform/rule_engine.py 的 check_triggers 方法")
        
    except Exception as e:
        print(f"\n[错误] 测试过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        DatabaseService.close_session(session)

if __name__ == "__main__":
    test_trigger_check()


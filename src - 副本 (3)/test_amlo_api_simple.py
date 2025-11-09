#!/usr/bin/env python3
"""
简单测试AMLO API
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from services.repform.rule_engine import RuleEngine

def test_amlo_api_simple():
    session = DatabaseService.get_session()
    try:
        print("=== 简单测试AMLO API逻辑 ===")
        
        # 测试数据
        test_data = {
            'customer_id': '123',
            'customer_name': 'Panython',
            'customer_country': 'BD',
            'transaction_type': 'exchange',
            'transaction_amount_thb': 4460000,
            'total_amount': 4460000,
            'payment_method': 'cash'
        }
        
        print(f"测试数据: {test_data}")
        
        # 直接调用RuleEngine.check_triggers
        try:
            result = RuleEngine.check_triggers(
                db_session=session,
                report_type='AMLO-1-01',
                data=test_data,
                branch_id=1
            )
            print(f"RuleEngine.check_triggers结果: {result}")
            
            if result.get('triggered'):
                print("[SUCCESS] AMLO触发检查成功！")
            else:
                print("[INFO] AMLO触发检查未触发")
                
        except Exception as e:
            print(f"[ERROR] RuleEngine.check_triggers失败: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_amlo_api_simple()

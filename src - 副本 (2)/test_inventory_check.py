#!/usr/bin/env python3
"""
测试库存检查
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from sqlalchemy import text
from decimal import Decimal

def test_inventory_check():
    session = DatabaseService.get_session()
    try:
        print("测试库存检查:")
        
        # 检查TEST网点的余额
        balances = session.execute(text("""
            SELECT 
                b.branch_name, 
                c.currency_code, 
                cb.balance
            FROM currency_balances cb
            JOIN branches b ON cb.branch_id = b.id
            JOIN currencies c ON cb.currency_id = c.id
            WHERE b.branch_code = 'A005'
            ORDER BY c.currency_code
        """)).fetchall()
        
        print("\nA005网点余额:")
        for balance in balances:
            print(f"  币种: {balance[1]}, 余额: {balance[2]}")
        
        # 检查用户交易的币种余额
        # 用户交易: 100 USD -> 3,233 THB
        # 需要检查USD库存是否足够
        
        usd_balance = session.execute(text("""
            SELECT cb.balance 
            FROM currency_balances cb
            JOIN branches b ON cb.branch_id = b.id
            JOIN currencies c ON cb.currency_id = c.id
            WHERE b.branch_code = 'A005' AND c.currency_code = 'USD'
        """)).fetchone()
        
        if usd_balance:
            current_usd = float(usd_balance[0])
            required_usd = 100.0  # 用户需要100 USD
            
            print(f"\nUSD库存检查:")
            print(f"  当前USD余额: {current_usd}")
            print(f"  需要USD数量: {required_usd}")
            print(f"  余额是否足够: {'是' if current_usd >= required_usd else '否'}")
            
            if current_usd < required_usd:
                print(f"  ❌ 库存不足！缺少: {required_usd - current_usd} USD")
            else:
                print(f"  ✅ 库存充足")
        else:
            print("\n❌ 未找到USD余额记录")
        
        # 检查THB余额（本币）
        thb_balance = session.execute(text("""
            SELECT cb.balance 
            FROM currency_balances cb
            JOIN branches b ON cb.branch_id = b.id
            JOIN currencies c ON cb.currency_id = c.id
            WHERE b.branch_code = 'A005' AND c.currency_code = 'THB'
        """)).fetchone()
        
        if thb_balance:
            current_thb = float(thb_balance[0])
            print(f"\nTHB余额:")
            print(f"  当前THB余额: {current_thb}")
            if current_thb < 0:
                print(f"  ⚠️ THB余额为负数！")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_inventory_check()

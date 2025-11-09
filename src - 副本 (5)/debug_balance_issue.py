#!/usr/bin/env python3
"""
余额问题调试脚本
用于检查负余额的原因和提供修复方案
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from models.exchange_models import CurrencyBalance, ExchangeTransaction, Currency, Branch
from sqlalchemy import func, desc
from decimal import Decimal

def check_balance_issues():
    """检查余额问题"""
    session = DatabaseService.get_session()
    
    try:
        print("=== 余额问题诊断报告 ===")
        
        # 1. 检查所有负余额
        print("\n1. 检查负余额记录:")
        negative_balances = session.query(CurrencyBalance).filter(
            CurrencyBalance.balance < 0
        ).all()
        
        if negative_balances:
            for balance in negative_balances:
                currency = session.query(Currency).get(balance.currency_id)
                branch = session.query(Branch).get(balance.branch_id)
                print(f"  - 网点: {branch.branch_name if branch else 'Unknown'}")
                print(f"    币种: {currency.currency_code if currency else 'Unknown'}")
                print(f"    余额: {balance.balance}")
                print(f"    更新时间: {balance.updated_at}")
                print()
        else:
            print("  ✅ 没有发现负余额记录")
        
        # 2. 检查交易记录统计
        print("\n2. 检查交易记录统计:")
        for balance in negative_balances:
            if not balance:
                continue
                
            currency = session.query(Currency).get(balance.currency_id)
            branch = session.query(Branch).get(balance.branch_id)
            
            if not currency or not branch:
                continue
                
            print(f"\n  网点: {branch.branch_name} ({branch.branch_code})")
            print(f"  币种: {currency.currency_code} ({currency.currency_name})")
            
            # 统计该币种的交易记录
            transactions = session.query(ExchangeTransaction).filter(
                ExchangeTransaction.currency_id == balance.currency_id,
                ExchangeTransaction.branch_id == balance.branch_id
            ).all()
            
            print(f"  总交易数: {len(transactions)}")
            
            if transactions:
                # 按类型统计
                buy_transactions = [t for t in transactions if t.type == 'buy']
                sell_transactions = [t for t in transactions if t.type == 'sell']
                
                buy_total = sum(float(t.amount) for t in buy_transactions)
                sell_total = sum(float(t.amount) for t in sell_transactions)
                
                print(f"  买入交易: {len(buy_transactions)} 笔, 总额: {buy_total}")
                print(f"  卖出交易: {len(sell_transactions)} 笔, 总额: {sell_total}")
                
                # 检查本币交易
                base_currency_id = branch.base_currency_id
                if base_currency_id:
                    base_transactions = session.query(ExchangeTransaction).filter(
                        ExchangeTransaction.currency_id == base_currency_id,
                        ExchangeTransaction.branch_id == balance.branch_id
                    ).all()
                    
                    if base_transactions:
                        base_buy_total = sum(float(t.local_amount) for t in base_transactions if t.local_amount > 0)
                        base_sell_total = sum(float(t.local_amount) for t in base_transactions if t.local_amount < 0)
                        
                        print(f"  本币买入: {base_buy_total}")
                        print(f"  本币卖出: {abs(base_sell_total)}")
        
        # 3. 提供修复建议
        print("\n3. 修复建议:")
        if negative_balances:
            print("  发现负余额，建议采取以下措施:")
            print("  a) 检查交易记录是否正确")
            print("  b) 使用余额调节功能修正余额")
            print("  c) 如果确认是测试数据，可以重置余额")
            print("  d) 检查日结过程是否正确执行")
            
            # 提供具体的重置命令
            print("\n  重置命令示例:")
            for balance in negative_balances:
                currency = session.query(Currency).get(balance.currency_id)
                branch = session.query(Branch).get(balance.branch_id)
                if currency and branch:
                    print(f"    # 重置 {branch.branch_name} 的 {currency.currency_code} 余额")
                    print(f"    UPDATE currency_balances SET balance = 0 WHERE branch_id = {balance.branch_id} AND currency_id = {balance.currency_id};")
        else:
            print("  ✅ 余额正常，无需修复")
            
    except Exception as e:
        print(f"检查过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        DatabaseService.close_session(session)

def reset_negative_balances():
    """重置负余额（谨慎使用）"""
    session = DatabaseService.get_session()
    
    try:
        print("=== 重置负余额 ===")
        print("⚠️  警告：此操作将重置所有负余额为0，请确认这是测试环境！")
        
        response = input("确认继续？(yes/no): ")
        if response.lower() != 'yes':
            print("操作已取消")
            return
        
        negative_balances = session.query(CurrencyBalance).filter(
            CurrencyBalance.balance < 0
        ).all()
        
        if not negative_balances:
            print("没有发现负余额记录")
            return
        
        for balance in negative_balances:
            currency = session.query(Currency).get(balance.currency_id)
            branch = session.query(Branch).get(balance.branch_id)
            
            print(f"重置 {branch.branch_name if branch else 'Unknown'} 的 {currency.currency_code if currency else 'Unknown'} 余额: {balance.balance} -> 0")
            balance.balance = Decimal('0')
            balance.updated_at = func.now()
        
        session.commit()
        print(f"✅ 成功重置 {len(negative_balances)} 个负余额记录")
        
    except Exception as e:
        session.rollback()
        print(f"重置过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        DatabaseService.close_session(session)

if __name__ == "__main__":
    print("余额问题调试工具")
    print("1. 检查余额问题")
    print("2. 重置负余额（谨慎使用）")
    
    choice = input("请选择操作 (1/2): ")
    
    if choice == "1":
        check_balance_issues()
    elif choice == "2":
        reset_negative_balances()
    else:
        print("无效选择")

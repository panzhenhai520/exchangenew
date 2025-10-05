#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试基于交易记录的币种使用状态判断逻辑
验证币种是否在交易记录中被使用过
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from models.exchange_models import Currency, CurrencyTemplate, ExchangeTransaction, Branch

def test_currency_transaction_logic():
    """测试基于交易记录的币种使用状态判断逻辑"""
    session = DatabaseService.get_session()
    try:
        print("=== 基于交易记录的币种使用状态判断测试 ===")
        
        # 1. 检查所有交易记录
        all_transactions = session.query(ExchangeTransaction).all()
        print(f"✅ 总交易记录数量: {len(all_transactions)}")
        
        # 2. 获取所有在交易记录中使用过的币种ID
        used_currency_ids = session.query(ExchangeTransaction.currency_id).distinct().all()
        used_currency_id_set = {row[0] for row in used_currency_ids}
        print(f"✅ 在交易记录中使用过的币种ID数量: {len(used_currency_id_set)}")
        
        # 3. 获取使用过的币种代码
        used_currencies = session.query(Currency.currency_code).filter(
            Currency.id.in_(used_currency_id_set)
        ).all()
        used_currency_codes = {row[0] for row in used_currencies}
        print(f"✅ 在交易记录中使用过的币种代码: {used_currency_codes}")
        
        # 4. 检查每个币种的使用情况
        print(f"\n=== 各币种交易记录统计 ===")
        for currency_id in used_currency_id_set:
            currency = session.query(Currency).filter_by(id=currency_id).first()
            if currency:
                transaction_count = session.query(ExchangeTransaction).filter_by(
                    currency_id=currency_id
                ).count()
                print(f"✅ {currency.currency_code}: {transaction_count} 笔交易")
        
        # 5. 检查币种模板的使用状态
        templates = session.query(CurrencyTemplate).filter_by(is_active=True).all()
        print(f"\n=== 币种模板使用状态 ===")
        
        used_templates = []
        unused_templates = []
        
        for template in templates:
            is_used = template.currency_code in used_currency_codes
            if is_used:
                used_templates.append(template)
                print(f"✅ {template.currency_code}: 已使用（在交易记录中）")
            else:
                unused_templates.append(template)
                print(f"❌ {template.currency_code}: 未使用（无交易记录）")
        
        print(f"\n=== 统计 ===")
        print(f"✅ 已使用的币种模板: {len(used_templates)}")
        print(f"❌ 未使用的币种模板: {len(unused_templates)}")
        
        # 6. 对比不同判断逻辑
        print(f"\n=== 不同判断逻辑对比 ===")
        
        # 逻辑1：基于Currency表判断
        all_currencies = session.query(Currency.currency_code).all()
        all_currency_codes = {row[0] for row in all_currencies}
        
        # 逻辑2：基于交易记录判断
        transaction_used_codes = used_currency_codes
        
        print(f"✅ 基于Currency表判断的已使用币种: {len(all_currency_codes)}")
        print(f"✅ 基于交易记录判断的已使用币种: {len(transaction_used_codes)}")
        
        # 找出差异
        currency_only = all_currency_codes - transaction_used_codes
        transaction_only = transaction_used_codes - all_currency_codes
        
        if currency_only:
            print(f"⚠️  只在Currency表中存在但无交易记录的币种: {currency_only}")
        
        if transaction_only:
            print(f"⚠️  有交易记录但Currency表中不存在的币种: {transaction_only}")
        
        return {
            'all_transactions': all_transactions,
            'used_currency_ids': used_currency_id_set,
            'used_currency_codes': used_currency_codes,
            'templates': templates,
            'used_templates': used_templates,
            'unused_templates': unused_templates,
            'all_currency_codes': all_currency_codes,
            'transaction_used_codes': transaction_used_codes
        }
        
    except Exception as e:
        print(f"❌ 测试基于交易记录的币种使用状态判断时出错: {e}")
        return None
    finally:
        DatabaseService.close_session(session)

def test_specific_currency_transactions(currency_code):
    """测试特定币种的交易记录"""
    session = DatabaseService.get_session()
    try:
        print(f"=== 测试币种 {currency_code} 的交易记录 ===")
        
        # 查找币种
        currency = session.query(Currency).filter_by(currency_code=currency_code.upper()).first()
        if not currency:
            print(f"❌ 币种 {currency_code} 不存在")
            return False
        
        print(f"✅ 币种存在: {currency.currency_code} - {currency.currency_name}")
        
        # 查找该币种的交易记录
        transactions = session.query(ExchangeTransaction).filter_by(
            currency_id=currency.id
        ).all()
        
        print(f"✅ 该币种的交易记录数量: {len(transactions)}")
        
        if transactions:
            print(f"✅ 交易记录详情:")
            for tx in transactions[:5]:  # 只显示前5条
                print(f"   - 交易号: {tx.transaction_no}, 类型: {tx.type}, 金额: {tx.amount}, 日期: {tx.transaction_date}")
            
            if len(transactions) > 5:
                print(f"   ... 还有 {len(transactions) - 5} 条交易记录")
            
            print(f"   ❌ 不能删除：币种在交易记录中被使用过")
            return False
        else:
            print(f"✅ 该币种没有交易记录")
            print(f"   ✅ 可以删除")
            return True
        
    except Exception as e:
        print(f"❌ 测试币种 {currency_code} 的交易记录时出错: {e}")
        return False
    finally:
        DatabaseService.close_session(session)

def main():
    """主函数"""
    if len(sys.argv) > 1:
        currency_code = sys.argv[1]
        test_specific_currency_transactions(currency_code)
    else:
        result = test_currency_transaction_logic()
        
        if result:
            print(f"\n=== 最终结论 ===")
            print(f"✅ 应该基于交易记录判断币种使用状态")
            print(f"✅ 有交易记录的币种不能删除")
            print(f"✅ 无交易记录的币种可以删除")
            print(f"✅ 币种模板使用状态应该基于交易记录显示")
            
            if len(result['used_templates']) > 0:
                print(f"⚠️  注意：有 {len(result['used_templates'])} 个币种模板在交易记录中被使用过，不能删除")

if __name__ == "__main__":
    main() 
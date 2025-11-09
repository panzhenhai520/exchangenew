#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试币种使用状态判断逻辑
验证不同场景下币种的使用状态
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from models.exchange_models import Currency, CurrencyTemplate, ExchangeRate, Branch
from datetime import date

def test_currency_usage_status():
    """测试币种使用状态判断逻辑"""
    session = DatabaseService.get_session()
    try:
        print("=== 币种使用状态判断测试 ===")
        
        # 1. 检查当前网点信息
        branch = session.query(Branch).filter_by(id=1).first()  # 假设网点ID为1
        if not branch:
            print("❌ 网点不存在")
            return
        
        print(f"✅ 当前网点: {branch.branch_name} (ID: {branch.id})")
        
        # 2. 检查当前网点的币种
        current_currencies = session.query(Currency).filter_by(branch_id=branch.id).all()
        print(f"✅ 当前网点币种数量: {len(current_currencies)}")
        for currency in current_currencies:
            print(f"   - {currency.currency_code}: {currency.currency_name}")
        
        # 3. 检查所有币种模板
        templates = session.query(CurrencyTemplate).filter_by(is_active=True).all()
        print(f"✅ 币种模板数量: {len(templates)}")
        
        # 4. 测试不同判断逻辑
        print("\n=== 不同判断逻辑对比 ===")
        
        # 逻辑1：全局判断（原来的逻辑）
        all_used_currencies = session.query(Currency.currency_code).all()
        all_used_codes = {row[0] for row in all_used_currencies}
        
        # 逻辑2：当前网点判断（修复后的逻辑）
        current_used_currencies = session.query(Currency.currency_code).filter_by(branch_id=branch.id).all()
        current_used_codes = {row[0] for row in current_used_currencies}
        
        # 逻辑3：基于汇率记录判断
        today = date.today()
        rates_currencies = session.query(ExchangeRate.currency_id).filter(
            ExchangeRate.branch_id == branch.id,
            ExchangeRate.rate_date == today
        ).all()
        rates_currency_ids = {row[0] for row in rates_currencies}
        
        print(f"✅ 全局已使用币种数量: {len(all_used_codes)}")
        print(f"✅ 当前网点已使用币种数量: {len(current_used_codes)}")
        print(f"✅ 当前网点有汇率记录的币种数量: {len(rates_currency_ids)}")
        
        # 5. 对比差异
        print("\n=== 判断逻辑差异 ===")
        
        # 全局有但当前网点没有的币种
        global_only = all_used_codes - current_used_codes
        if global_only:
            print(f"⚠️  全局有但当前网点没有的币种: {global_only}")
        
        # 当前网点有但全局没有的币种（理论上不应该有）
        current_only = current_used_codes - all_used_codes
        if current_only:
            print(f"⚠️  当前网点有但全局没有的币种: {current_only}")
        
        # 有Currency记录但没有汇率记录的币种
        currency_without_rates = set()
        for currency in current_currencies:
            if currency.id not in rates_currency_ids:
                currency_without_rates.add(currency.currency_code)
        
        if currency_without_rates:
            print(f"⚠️  有Currency记录但没有汇率记录的币种: {currency_without_rates}")
        
        # 6. 推荐判断逻辑
        print("\n=== 推荐判断逻辑 ===")
        print("✅ 方案1：基于当前网点Currency表判断（推荐）")
        print("   - 优点：准确反映当前网点状态")
        print("   - 缺点：可能包含已删除但未清理的币种")
        
        print("✅ 方案2：基于汇率记录判断")
        print("   - 优点：准确反映实际使用情况")
        print("   - 缺点：需要额外的数据库查询")
        
        print("✅ 方案3：基于今日汇率列表判断")
        print("   - 优点：与用户界面一致")
        print("   - 缺点：需要实时计算")
        
        return {
            'branch': branch,
            'current_currencies': current_currencies,
            'templates': templates,
            'all_used_codes': all_used_codes,
            'current_used_codes': current_used_codes,
            'rates_currency_ids': rates_currency_ids
        }
        
    except Exception as e:
        print(f"❌ 测试币种使用状态时出错: {e}")
        return None
    finally:
        DatabaseService.close_session(session)

def main():
    """主函数"""
    result = test_currency_usage_status()
    
    if result:
        print(f"\n=== 总结 ===")
        print(f"✅ 当前网点币种数量: {len(result['current_currencies'])}")
        print(f"✅ 全局已使用币种数量: {len(result['all_used_codes'])}")
        print(f"✅ 当前网点已使用币种数量: {len(result['current_used_codes'])}")
        print(f"✅ 有汇率记录的币种数量: {len(result['rates_currency_ids'])}")
        
        # 判断逻辑建议
        if len(result['current_used_codes']) != len(result['rates_currency_ids']):
            print("⚠️  建议：使用基于汇率记录的判断逻辑，更准确反映实际使用情况")
        else:
            print("✅ 当前网点的Currency记录与汇率记录一致")

if __name__ == "__main__":
    main() 
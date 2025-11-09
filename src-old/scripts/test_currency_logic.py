#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试币种管理逻辑脚本
验证删除币种后是否可以重新添加
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from models.exchange_models import Currency, CurrencyTemplate, ExchangeRate, Branch

def test_currency_logic():
    """测试币种管理逻辑"""
    session = DatabaseService.get_session()
    try:
        print("=== 币种管理逻辑测试 ===")
        
        # 1. 检查当前网点信息
        branch = session.query(Branch).filter_by(id=1).first()  # 假设网点ID为1
        if not branch:
            print("❌ 网点不存在")
            return
        
        print(f"✅ 当前网点: {branch.branch_name} (ID: {branch.id})")
        
        # 2. 检查币种模板
        templates = session.query(CurrencyTemplate).filter_by(is_active=True).all()
        print(f"✅ 币种模板数量: {len(templates)}")
        
        # 3. 检查当前网点使用的币种
        current_currencies = session.query(Currency).filter_by(branch_id=branch.id).all()
        print(f"✅ 当前网点使用的币种数量: {len(current_currencies)}")
        for currency in current_currencies:
            print(f"   - {currency.currency_code}: {currency.currency_name}")
        
        # 4. 检查可添加的币种
        current_currency_codes = {c.currency_code for c in current_currencies}
        available_templates = [t for t in templates if t.currency_code not in current_currency_codes]
        print(f"✅ 可添加的币种数量: {len(available_templates)}")
        for template in available_templates[:5]:  # 只显示前5个
            print(f"   - {template.currency_code}: {template.currency_name}")
        
        # 5. 检查汇率记录
        rates = session.query(ExchangeRate).filter_by(branch_id=branch.id).all()
        print(f"✅ 当前网点汇率记录数量: {len(rates)}")
        
        return {
            'branch': branch,
            'templates': templates,
            'current_currencies': current_currencies,
            'available_templates': available_templates,
            'rates': rates
        }
        
    except Exception as e:
        print(f"❌ 测试币种管理逻辑时出错: {e}")
        return None
    finally:
        DatabaseService.close_session(session)

def simulate_delete_currency(currency_code):
    """模拟删除币种"""
    session = DatabaseService.get_session()
    try:
        print(f"\n=== 模拟删除币种 {currency_code} ===")
        
        # 1. 检查删除前的状态
        currency = session.query(Currency).filter_by(
            currency_code=currency_code.upper(),
            branch_id=1
        ).first()
        
        if not currency:
            print(f"❌ 币种 {currency_code} 在当前网点不存在")
            return False
        
        print(f"✅ 删除前 - 币种存在: {currency.currency_code}")
        
        # 2. 检查汇率记录
        rates = session.query(ExchangeRate).filter_by(
            currency_id=currency.id,
            branch_id=1
        ).all()
        print(f"✅ 删除前 - 汇率记录数量: {len(rates)}")
        
        # 3. 检查是否被其他网点使用
        other_rates = session.query(ExchangeRate).filter(
            ExchangeRate.currency_id == currency.id,
            ExchangeRate.branch_id != 1
        ).all()
        print(f"✅ 删除前 - 其他网点使用记录: {len(other_rates)}")
        
        # 4. 模拟删除（不实际删除，只是检查逻辑）
        can_delete_currency = len(other_rates) == 0
        print(f"✅ 是否可以删除币种本身: {can_delete_currency}")
        
        return True
        
    except Exception as e:
        print(f"❌ 模拟删除币种时出错: {e}")
        return False
    finally:
        DatabaseService.close_session(session)

def main():
    """主函数"""
    # 测试基本逻辑
    result = test_currency_logic()
    
    if result and result['current_currencies']:
        # 选择第一个币种进行模拟删除
        test_currency = result['current_currencies'][0]
        simulate_delete_currency(test_currency.currency_code)

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
检查币种状态脚本
用于诊断删除币种后的问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from models.exchange_models import Currency, CurrencyTemplate, ExchangeRate

def check_currency_status(currency_code):
    """检查指定币种的状态"""
    session = DatabaseService.get_session()
    try:
        print(f"=== 检查币种 {currency_code} 的状态 ===")
        
        # 1. 检查Currency表中是否存在
        currency = session.query(Currency).filter_by(currency_code=currency_code.upper()).first()
        if currency:
            print(f"✅ Currency表中存在币种: {currency.currency_code}")
            print(f"   - ID: {currency.id}")
            print(f"   - 名称: {currency.currency_name}")
            print(f"   - 网点ID: {currency.branch_id}")
        else:
            print(f"❌ Currency表中不存在币种: {currency_code}")
        
        # 2. 检查CurrencyTemplate表中是否存在
        template = session.query(CurrencyTemplate).filter_by(currency_code=currency_code.upper()).first()
        if template:
            print(f"✅ CurrencyTemplate表中存在模板: {template.currency_code}")
            print(f"   - 名称: {template.currency_name}")
            print(f"   - 是否激活: {template.is_active}")
        else:
            print(f"❌ CurrencyTemplate表中不存在模板: {currency_code}")
        
        # 3. 检查ExchangeRate表中是否有记录
        rates = session.query(ExchangeRate).filter_by(currency_id=currency.id if currency else 0).all()
        if rates:
            print(f"✅ ExchangeRate表中有 {len(rates)} 条记录")
            for rate in rates:
                print(f"   - 网点ID: {rate.branch_id}, 日期: {rate.rate_date}")
        else:
            print(f"❌ ExchangeRate表中没有记录")
        
        # 4. 检查是否被其他网点使用
        if currency:
            other_rates = session.query(ExchangeRate).filter(
                ExchangeRate.currency_id == currency.id,
                ExchangeRate.branch_id != 1  # 假设当前网点ID为1
            ).all()
            if other_rates:
                print(f"⚠️  币种被其他网点使用: {len(other_rates)} 条记录")
                for rate in other_rates:
                    print(f"   - 网点ID: {rate.branch_id}, 日期: {rate.rate_date}")
            else:
                print(f"✅ 币种没有被其他网点使用")
        
        return currency is not None, template is not None, len(rates) > 0
        
    except Exception as e:
        print(f"❌ 检查币种状态时出错: {e}")
        return False, False, False
    finally:
        DatabaseService.close_session(session)

def list_all_currencies():
    """列出所有币种的状态"""
    session = DatabaseService.get_session()
    try:
        print("=== 所有币种状态 ===")
        
        # 获取所有Currency表中的币种
        currencies = session.query(Currency).all()
        print(f"Currency表中的币种数量: {len(currencies)}")
        for currency in currencies:
            rates_count = session.query(ExchangeRate).filter_by(currency_id=currency.id).count()
            print(f"  - {currency.currency_code}: {currency.currency_name} (汇率记录: {rates_count}条)")
        
        # 获取所有CurrencyTemplate表中的模板
        templates = session.query(CurrencyTemplate).filter_by(is_active=True).all()
        print(f"CurrencyTemplate表中的激活模板数量: {len(templates)}")
        for template in templates:
            currency = session.query(Currency).filter_by(currency_code=template.currency_code).first()
            is_in_use = currency is not None
            print(f"  - {template.currency_code}: {template.currency_name} (已使用: {is_in_use})")
        
    except Exception as e:
        print(f"❌ 列出币种状态时出错: {e}")
    finally:
        DatabaseService.close_session(session)

def main():
    """主函数"""
    if len(sys.argv) > 1:
        currency_code = sys.argv[1]
        check_currency_status(currency_code)
    else:
        list_all_currencies()

if __name__ == "__main__":
    main() 
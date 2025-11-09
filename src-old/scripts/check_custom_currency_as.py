#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
检查自定义币种AS的状态
验证为什么AS币种在今日汇率列表和新增币种列表中不显示
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from models.exchange_models import Currency, CurrencyTemplate, ExchangeRate, ExchangeTransaction

def check_custom_currency_as():
    """检查自定义币种AS的状态"""
    session = DatabaseService.get_session()
    try:
        print("=== 检查自定义币种AS的状态 ===")
        
        # 1. 检查CurrencyTemplate表中的AS币种
        as_template = session.query(CurrencyTemplate).filter_by(currency_code='AS').first()
        if as_template:
            print(f"✅ CurrencyTemplate表中存在AS币种:")
            print(f"   - ID: {as_template.id}")
            print(f"   - 代码: {as_template.currency_code}")
            print(f"   - 名称: {as_template.currency_name}")
            print(f"   - 国家: {as_template.country}")
            print(f"   - 国旗代码: {as_template.flag_code}")
            print(f"   - 自定义图标: {as_template.custom_flag_filename}")
            print(f"   - 是否激活: {as_template.is_active}")
        else:
            print(f"❌ CurrencyTemplate表中不存在AS币种")
            return
        
        # 2. 检查Currency表中的AS币种
        as_currency = session.query(Currency).filter_by(currency_code='AS').first()
        if as_currency:
            print(f"\n✅ Currency表中存在AS币种:")
            print(f"   - ID: {as_currency.id}")
            print(f"   - 代码: {as_currency.currency_code}")
            print(f"   - 名称: {as_currency.currency_name}")
            print(f"   - 国家: {as_currency.country}")
            print(f"   - 国旗代码: {as_currency.flag_code}")
            print(f"   - 自定义图标: {as_currency.custom_flag_filename}")
            print(f"   - 网点ID: {as_currency.branch_id}")
        else:
            print(f"\n❌ Currency表中不存在AS币种")
        
        # 3. 检查ExchangeRate表中的AS币种记录
        as_rates = session.query(ExchangeRate).filter_by(currency_id=as_currency.id if as_currency else 0).all()
        print(f"\n✅ ExchangeRate表中AS币种的汇率记录数量: {len(as_rates)}")
        for rate in as_rates:
            print(f"   - 网点ID: {rate.branch_id}, 日期: {rate.rate_date}, 买入: {rate.buy_rate}, 卖出: {rate.sell_rate}")
        
        # 4. 检查ExchangeTransaction表中的AS币种交易记录
        as_transactions = session.query(ExchangeTransaction).filter_by(currency_id=as_currency.id if as_currency else 0).all()
        print(f"\n✅ ExchangeTransaction表中AS币种的交易记录数量: {len(as_transactions)}")
        for tx in as_transactions[:3]:  # 只显示前3条
            print(f"   - 交易号: {tx.transaction_no}, 类型: {tx.type}, 金额: {tx.amount}, 日期: {tx.transaction_date}")
        
        # 5. 模拟get_currency_templates的逻辑
        print(f"\n=== 模拟get_currency_templates逻辑 ===")
        
        # 获取所有激活的币种模板
        all_templates = session.query(CurrencyTemplate).filter_by(is_active=True).all()
        print(f"✅ 所有激活的币种模板数量: {len(all_templates)}")
        
        # 获取Currency表中存在的币种代码
        existing_currencies = session.query(Currency.currency_code).all()
        existing_currency_codes = {row[0] for row in existing_currencies}
        print(f"✅ Currency表中存在的币种代码: {existing_currency_codes}")
        
        # 检查AS是否被排除
        if 'AS' in existing_currency_codes:
            print(f"⚠️  AS币种在Currency表中存在，会被get_currency_templates排除")
        else:
            print(f"✅ AS币种在Currency表中不存在，不会被排除")
        
        # 6. 检查AS币种是否应该显示在新增列表中
        available_templates = []
        for template in all_templates:
            if template.currency_code not in existing_currency_codes:
                available_templates.append(template)
        
        print(f"\n✅ 可添加到今日汇率的币种模板数量: {len(available_templates)}")
        for template in available_templates:
            print(f"   - {template.currency_code}: {template.currency_name}")
        
        # 7. 检查AS币种是否在可添加列表中
        as_in_available = any(t.currency_code == 'AS' for t in available_templates)
        if as_in_available:
            print(f"✅ AS币种在可添加列表中")
        else:
            print(f"❌ AS币种不在可添加列表中")
        
        # 8. 建议解决方案
        print(f"\n=== 建议解决方案 ===")
        if as_currency:
            print(f"✅ AS币种在Currency表中存在，这是正常的")
            print(f"✅ 如果要从今日汇率列表中删除AS币种，需要删除Currency表中的记录")
            print(f"✅ 删除后，AS币种会重新出现在新增币种列表中")
        else:
            print(f"❌ AS币种在Currency表中不存在，应该出现在新增币种列表中")
            print(f"✅ 检查是否有其他逻辑阻止了AS币种的显示")
        
        return {
            'as_template': as_template,
            'as_currency': as_currency,
            'as_rates': as_rates,
            'as_transactions': as_transactions,
            'existing_currency_codes': existing_currency_codes,
            'available_templates': available_templates
        }
        
    except Exception as e:
        print(f"❌ 检查自定义币种AS状态时出错: {e}")
        return None
    finally:
        DatabaseService.close_session(session)

def main():
    """主函数"""
    result = check_custom_currency_as()
    
    if result:
        print(f"\n=== 总结 ===")
        if result['as_currency']:
            print(f"✅ AS币种在Currency表中存在，这是正常的")
            print(f"✅ 要从今日汇率列表中删除AS币种，需要删除Currency表中的记录")
            print(f"✅ 删除后，AS币种会重新出现在新增币种列表中")
        else:
            print(f"❌ AS币种在Currency表中不存在，应该出现在新增币种列表中")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试自定义币种的处理逻辑
验证自定义币种在今日汇率列表和新增币种列表中的显示
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from models.exchange_models import Currency, CurrencyTemplate, ExchangeRate, ExchangeTransaction

def test_custom_currency_logic():
    """测试自定义币种的处理逻辑"""
    session = DatabaseService.get_session()
    try:
        print("=== 测试自定义币种的处理逻辑 ===")
        
        # 1. 检查所有自定义币种
        custom_currencies = session.query(Currency).filter(
            Currency.custom_flag_filename.isnot(None),
            Currency.custom_flag_filename != ''
        ).all()
        
        print(f"✅ 自定义币种数量: {len(custom_currencies)}")
        for currency in custom_currencies:
            print(f"   - {currency.currency_code}: {currency.currency_name} (自定义图标: {currency.custom_flag_filename})")
        
        # 2. 检查所有币种模板
        all_templates = session.query(CurrencyTemplate).filter_by(is_active=True).all()
        print(f"\n✅ 所有激活的币种模板数量: {len(all_templates)}")
        
        # 3. 检查Currency表中存在的币种
        existing_currencies = session.query(Currency.currency_code).all()
        existing_currency_codes = {row[0] for row in existing_currencies}
        print(f"✅ Currency表中存在的币种代码: {existing_currency_codes}")
        
        # 4. 获取自定义币种代码
        custom_currency_codes = {currency.currency_code for currency in custom_currencies}
        print(f"✅ 自定义币种代码: {custom_currency_codes}")
        
        # 5. 模拟修复后的get_currency_templates逻辑
        print(f"\n=== 模拟修复后的get_currency_templates逻辑 ===")
        
        # 排除非自定义币种，但保留自定义币种
        non_custom_existing_codes = existing_currency_codes - custom_currency_codes
        print(f"✅ 非自定义币种代码（会被排除）: {non_custom_existing_codes}")
        
        # 检查哪些币种模板会被返回
        available_templates = []
        for template in all_templates:
            if template.currency_code not in non_custom_existing_codes:
                available_templates.append(template)
        
        print(f"✅ 可添加到今日汇率的币种模板数量: {len(available_templates)}")
        for template in available_templates:
            is_custom = template.currency_code in custom_currency_codes
            status = "自定义" if is_custom else "标准"
            print(f"   - {template.currency_code}: {template.currency_name} ({status})")
        
        # 6. 检查AS币种的状态
        print(f"\n=== 检查AS币种状态 ===")
        
        as_template = session.query(CurrencyTemplate).filter_by(currency_code='AS').first()
        as_currency = session.query(Currency).filter_by(currency_code='AS').first()
        
        if as_template:
            print(f"✅ AS币种模板存在: {as_template.currency_name}")
        else:
            print(f"❌ AS币种模板不存在")
        
        if as_currency:
            print(f"✅ AS币种在Currency表中存在")
            print(f"   - 自定义图标: {as_currency.custom_flag_filename}")
            print(f"   - 是否会被排除: {'否' if as_currency.custom_flag_filename else '是'}")
        else:
            print(f"❌ AS币种在Currency表中不存在")
        
        # 检查AS是否在可添加列表中
        as_in_available = any(t.currency_code == 'AS' for t in available_templates)
        if as_in_available:
            print(f"✅ AS币种在可添加列表中")
        else:
            print(f"❌ AS币种不在可添加列表中")
        
        # 7. 检查AS币种的汇率记录
        if as_currency:
            as_rates = session.query(ExchangeRate).filter_by(currency_id=as_currency.id).all()
            print(f"✅ AS币种的汇率记录数量: {len(as_rates)}")
            
            if as_rates:
                print(f"✅ AS币种有汇率记录，应该在今日汇率列表中显示")
            else:
                print(f"⚠️  AS币种没有汇率记录，可能不在今日汇率列表中显示")
        
        # 8. 建议操作
        print(f"\n=== 建议操作 ===")
        if as_currency and as_currency.custom_flag_filename:
            print(f"✅ AS币种是自定义币种，应该能够重新添加到今日汇率列表中")
            print(f"✅ 如果AS币种不在今日汇率列表中，可以尝试重新添加")
        elif as_currency and not as_currency.custom_flag_filename:
            print(f"⚠️  AS币种在Currency表中存在但不是自定义币种")
            print(f"✅ 需要为AS币种设置custom_flag_filename字段")
        else:
            print(f"❌ AS币种在Currency表中不存在")
            print(f"✅ 需要先添加AS币种到Currency表中")
        
        return {
            'custom_currencies': custom_currencies,
            'all_templates': all_templates,
            'existing_currency_codes': existing_currency_codes,
            'custom_currency_codes': custom_currency_codes,
            'non_custom_existing_codes': non_custom_existing_codes,
            'available_templates': available_templates,
            'as_template': as_template,
            'as_currency': as_currency
        }
        
    except Exception as e:
        print(f"❌ 测试自定义币种处理逻辑时出错: {e}")
        return None
    finally:
        DatabaseService.close_session(session)

def main():
    """主函数"""
    result = test_custom_currency_logic()
    
    if result:
        print(f"\n=== 总结 ===")
        if result['as_currency'] and result['as_currency'].custom_flag_filename:
            print(f"✅ AS币种是自定义币种，修复后的逻辑应该能正确处理")
            print(f"✅ AS币种应该出现在新增币种列表中")
            print(f"✅ 如果AS币种不在今日汇率列表中，可以重新添加")
        else:
            print(f"❌ AS币种需要进一步处理")

if __name__ == "__main__":
    main() 
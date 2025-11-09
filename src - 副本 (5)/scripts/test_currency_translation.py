#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试币种翻译问题
验证SSS等不存在的币种代码是否还会产生翻译警告
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from models.exchange_models import Currency, CurrencyTemplate, ExchangeRate
from datetime import date

def test_currency_translation_issue():
    """测试币种翻译问题"""
    session = DatabaseService.get_session()
    try:
        print("=== 测试币种翻译问题 ===")
        
        # 1. 检查是否有SSS币种在数据库中
        sss_currency = session.query(Currency).filter_by(currency_code='SSS').first()
        if sss_currency:
            print(f"❌ 发现SSS币种在Currency表中:")
            print(f"   - ID: {sss_currency.id}")
            print(f"   - 代码: {sss_currency.currency_code}")
            print(f"   - 名称: {sss_currency.currency_name}")
            print(f"   - 自定义图标: {sss_currency.custom_flag_filename}")
        else:
            print(f"✅ SSS币种在Currency表中不存在")
        
        # 2. 检查是否有SSS币种模板
        sss_template = session.query(CurrencyTemplate).filter_by(currency_code='SSS').first()
        if sss_template:
            print(f"❌ 发现SSS币种模板:")
            print(f"   - ID: {sss_template.id}")
            print(f"   - 代码: {sss_template.currency_code}")
            print(f"   - 名称: {sss_template.currency_name}")
        else:
            print(f"✅ SSS币种模板不存在")
        
        # 3. 检查是否有SSS币种的汇率记录
        today = date.today()
        sss_rates = []
        if sss_currency:
            sss_rates = session.query(ExchangeRate).filter(
                ExchangeRate.currency_id == sss_currency.id,
                ExchangeRate.rate_date == today
            ).all()
        
        if sss_rates:
            print(f"❌ 发现SSS币种今日汇率记录: {len(sss_rates)} 条")
            for rate in sss_rates:
                print(f"   - 网点ID: {rate.branch_id}, 买入: {rate.buy_rate}, 卖出: {rate.sell_rate}")
        else:
            print(f"✅ SSS币种无今日汇率记录")
        
        # 4. 检查其他可能不存在的币种代码
        problematic_codes = ['SSS', 'XXX', 'YYY', 'ZZZ']
        print(f"\n=== 检查其他可能的问题币种代码 ===")
        
        for code in problematic_codes:
            currency = session.query(Currency).filter_by(currency_code=code).first()
            template = session.query(CurrencyTemplate).filter_by(currency_code=code).first()
            
            if currency or template:
                print(f"❌ 发现币种代码 {code} 在数据库中存在")
                if currency:
                    print(f"   - Currency表: {currency.currency_name}")
                if template:
                    print(f"   - CurrencyTemplate表: {template.currency_name}")
            else:
                print(f"✅ 币种代码 {code} 在数据库中不存在")
        
        # 5. 建议解决方案
        print(f"\n=== 建议解决方案 ===")
        if sss_currency or sss_template or sss_rates:
            print(f"✅ 发现SSS币种相关数据，需要清理:")
            if sss_currency:
                print(f"   - 删除Currency表中的SSS记录")
            if sss_template:
                print(f"   - 删除CurrencyTemplate表中的SSS记录")
            if sss_rates:
                print(f"   - 删除ExchangeRate表中的SSS汇率记录")
        else:
            print(f"✅ 数据库中没有SSS币种相关数据")
            print(f"✅ 翻译警告应该已经通过代码修复解决")
        
        return {
            'sss_currency': sss_currency,
            'sss_template': sss_template,
            'sss_rates': sss_rates
        }
        
    except Exception as e:
        print(f"❌ 测试币种翻译问题时出错: {e}")
        return None
    finally:
        DatabaseService.close_session(session)

def clean_sss_currency_data():
    """清理SSS币种相关数据"""
    session = DatabaseService.get_session()
    try:
        print(f"\n=== 清理SSS币种相关数据 ===")
        
        # 1. 删除SSS币种的汇率记录
        sss_currency = session.query(Currency).filter_by(currency_code='SSS').first()
        if sss_currency:
            deleted_rates = session.query(ExchangeRate).filter_by(
                currency_id=sss_currency.id
            ).delete()
            print(f"✅ 删除了 {deleted_rates} 条SSS币种汇率记录")
        
        # 2. 删除SSS币种记录
        if sss_currency:
            session.delete(sss_currency)
            print(f"✅ 删除了SSS币种记录")
        
        # 3. 删除SSS币种模板
        sss_template = session.query(CurrencyTemplate).filter_by(currency_code='SSS').first()
        if sss_template:
            session.delete(sss_template)
            print(f"✅ 删除了SSS币种模板")
        
        DatabaseService.commit_session(session)
        print(f"✅ 清理完成！")
        
    except Exception as e:
        DatabaseService.rollback_session(session)
        print(f"❌ 清理SSS币种数据时出错: {e}")
    finally:
        DatabaseService.close_session(session)

def main():
    """主函数"""
    result = test_currency_translation_issue()
    
    if result:
        print(f"\n=== 总结 ===")
        if result['sss_currency'] or result['sss_template'] or result['sss_rates']:
            print(f"✅ 发现SSS币种相关数据，建议清理")
            
            response = input("是否清理SSS币种相关数据？(y/n): ")
            if response.lower() == 'y':
                clean_sss_currency_data()
        else:
            print(f"✅ 数据库中没有SSS币种相关数据")
            print(f"✅ 翻译警告应该已经通过代码修复解决")
            print(f"✅ 现在可以测试前端，应该不会再出现SSS的翻译警告")

if __name__ == "__main__":
    main() 
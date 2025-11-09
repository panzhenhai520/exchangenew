#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试修复后的正确币种逻辑
验证：币种模板 = 今日汇率列表 + 今日汇率新增币种页待增加币种
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from models.exchange_models import Currency, CurrencyTemplate, ExchangeRate, ExchangeTransaction
from datetime import date

def test_correct_currency_logic():
    """测试修复后的正确币种逻辑"""
    session = DatabaseService.get_session()
    try:
        print("=== 测试修复后的正确币种逻辑 ===")
        
        # 1. 获取所有币种模板
        all_templates = session.query(CurrencyTemplate).filter_by(is_active=True).all()
        template_codes = {template.currency_code for template in all_templates}
        print(f"✅ 币种模板总数: {len(all_templates)}")
        print(f"✅ 币种模板代码: {template_codes}")
        
        # 2. 获取今日汇率列表中的币种（基于ExchangeRate表）
        today = date.today()
        today_rates = session.query(ExchangeRate).filter(
            ExchangeRate.rate_date == today
        ).all()
        
        today_currency_ids = {rate.currency_id for rate in today_rates}
        today_currency_codes = set()
        
        if today_currency_ids:
            today_currencies = session.query(Currency.currency_code).filter(
                Currency.id.in_(today_currency_ids)
            ).all()
            today_currency_codes = {row[0] for row in today_currencies}
        
        print(f"\n✅ 今日汇率列表中的币种:")
        print(f"   - 汇率记录数量: {len(today_rates)}")
        print(f"   - 币种ID: {today_currency_ids}")
        print(f"   - 币种代码: {today_currency_codes}")
        
        # 3. 计算今日汇率新增币种页待增加币种
        available_codes = template_codes - today_currency_codes
        print(f"\n✅ 今日汇率新增币种页待增加币种:")
        print(f"   - 币种代码: {available_codes}")
        print(f"   - 数量: {len(available_codes)}")
        
        # 4. 验证逻辑：币种模板 = 今日汇率列表 + 今日汇率新增币种页待增加币种
        left_side = template_codes
        right_side = today_currency_codes | available_codes
        
        print(f"\n=== 验证逻辑 ===")
        print(f"✅ 币种模板: {len(left_side)} 个")
        print(f"✅ 今日汇率列表: {len(today_currency_codes)} 个")
        print(f"✅ 待增加币种: {len(available_codes)} 个")
        print(f"✅ 今日汇率列表 + 待增加币种: {len(right_side)} 个")
        
        if left_side == right_side:
            print(f"✅ 逻辑验证通过：币种模板 = 今日汇率列表 + 待增加币种")
        else:
            print(f"❌ 逻辑验证失败")
            print(f"   币种模板: {left_side}")
            print(f"   今日汇率列表: {today_currency_codes}")
            print(f"   待增加币种: {available_codes}")
            print(f"   今日汇率列表 + 待增加币种: {right_side}")
        
        # 5. 检查AS币种的状态
        print(f"\n=== 检查AS币种状态 ===")
        
        as_template = session.query(CurrencyTemplate).filter_by(currency_code='AS').first()
        as_currency = session.query(Currency).filter_by(currency_code='AS').first()
        as_in_today_rates = 'AS' in today_currency_codes
        as_in_available = 'AS' in available_codes
        
        if as_template:
            print(f"✅ AS币种模板存在: {as_template.currency_name}")
        else:
            print(f"❌ AS币种模板不存在")
        
        if as_currency:
            print(f"✅ AS币种在Currency表中存在")
            print(f"   - 自定义图标: {as_currency.custom_flag_filename}")
        else:
            print(f"❌ AS币种在Currency表中不存在")
        
        print(f"✅ AS币种在今日汇率列表中: {as_in_today_rates}")
        print(f"✅ AS币种在待增加币种中: {as_in_available}")
        
        # 6. 检查AS币种的汇率记录
        if as_currency:
            as_rates = session.query(ExchangeRate).filter_by(
                currency_id=as_currency.id,
                rate_date=today
            ).all()
            print(f"✅ AS币种今日汇率记录数量: {len(as_rates)}")
            
            for rate in as_rates:
                print(f"   - 网点ID: {rate.branch_id}, 买入: {rate.buy_rate}, 卖出: {rate.sell_rate}")
        
        # 7. 总结
        print(f"\n=== 总结 ===")
        if as_in_today_rates:
            print(f"✅ AS币种在今日汇率列表中，不应该出现在待增加币种中")
            print(f"✅ 如果要重新添加AS币种，需要先删除今日汇率记录")
        elif as_in_available:
            print(f"✅ AS币种在待增加币种中，可以添加到今日汇率列表")
            print(f"✅ 可以直接调用add_currency API添加")
        else:
            print(f"❌ AS币种既不在今日汇率列表中，也不在待增加币种中")
            print(f"❌ 这表示AS币种模板不存在或未激活")
        
        return {
            'all_templates': all_templates,
            'template_codes': template_codes,
            'today_rates': today_rates,
            'today_currency_codes': today_currency_codes,
            'available_codes': available_codes,
            'as_template': as_template,
            'as_currency': as_currency,
            'as_in_today_rates': as_in_today_rates,
            'as_in_available': as_in_available
        }
        
    except Exception as e:
        print(f"❌ 测试修复后的正确币种逻辑时出错: {e}")
        return None
    finally:
        DatabaseService.close_session(session)

def main():
    """主函数"""
    result = test_correct_currency_logic()
    
    if result:
        print(f"\n=== 最终结论 ===")
        if result['as_in_today_rates']:
            print(f"✅ AS币种在今日汇率列表中")
            print(f"✅ 如果要重新添加，需要先删除今日汇率记录")
        elif result['as_in_available']:
            print(f"✅ AS币种在待增加币种中")
            print(f"✅ 可以直接添加")
        else:
            print(f"❌ AS币种需要检查模板状态")

if __name__ == "__main__":
    main() 
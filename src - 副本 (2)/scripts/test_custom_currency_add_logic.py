#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试自定义币种重新添加的逻辑
验证自定义币种能够重新添加到今日汇率列表中
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from models.exchange_models import Currency, CurrencyTemplate, ExchangeRate, ExchangeTransaction
from datetime import date

def test_custom_currency_add_logic():
    """测试自定义币种重新添加的逻辑"""
    session = DatabaseService.get_session()
    try:
        print("=== 测试自定义币种重新添加的逻辑 ===")
        
        # 1. 检查AS币种的状态
        as_currency = session.query(Currency).filter_by(currency_code='AS').first()
        if not as_currency:
            print(f"❌ AS币种在Currency表中不存在")
            return
        
        print(f"✅ AS币种在Currency表中存在:")
        print(f"   - ID: {as_currency.id}")
        print(f"   - 代码: {as_currency.currency_code}")
        print(f"   - 名称: {as_currency.currency_name}")
        print(f"   - 自定义图标: {as_currency.custom_flag_filename}")
        print(f"   - 是否自定义币种: {'是' if as_currency.custom_flag_filename else '否'}")
        
        # 2. 检查AS币种的汇率记录
        today = date.today()
        as_rates = session.query(ExchangeRate).filter_by(
            currency_id=as_currency.id,
            rate_date=today
        ).all()
        
        print(f"\n✅ AS币种今日汇率记录数量: {len(as_rates)}")
        for rate in as_rates:
            print(f"   - 网点ID: {rate.branch_id}, 买入: {rate.buy_rate}, 卖出: {rate.sell_rate}")
        
        # 3. 模拟添加自定义币种的逻辑
        print(f"\n=== 模拟添加自定义币种的逻辑 ===")
        
        # 检查是否是自定义币种
        is_custom_currency = bool(as_currency.custom_flag_filename)
        print(f"✅ 是否自定义币种: {is_custom_currency}")
        
        if is_custom_currency:
            print(f"✅ AS是自定义币种，检查是否有今日汇率记录")
            
            if as_rates:
                print(f"❌ AS币种今日已有汇率记录，不能重新添加")
                print(f"   建议：删除今日汇率记录后重新添加")
            else:
                print(f"✅ AS币种今日无汇率记录，可以重新添加")
                print(f"   可以调用add_currency API重新添加汇率")
        else:
            print(f"❌ AS不是自定义币种，不能重新添加")
        
        # 4. 检查所有自定义币种的状态
        print(f"\n=== 检查所有自定义币种的状态 ===")
        
        custom_currencies = session.query(Currency).filter(
            Currency.custom_flag_filename.isnot(None),
            Currency.custom_flag_filename != ''
        ).all()
        
        print(f"✅ 自定义币种总数: {len(custom_currencies)}")
        
        for currency in custom_currencies:
            # 检查今日汇率记录
            today_rates = session.query(ExchangeRate).filter_by(
                currency_id=currency.id,
                rate_date=today
            ).all()
            
            status = "有汇率记录" if today_rates else "无汇率记录"
            can_add = "可以重新添加" if not today_rates else "不能重新添加"
            
            print(f"   - {currency.currency_code}: {currency.currency_name} ({status}, {can_add})")
        
        # 5. 建议操作
        print(f"\n=== 建议操作 ===")
        
        if as_currency.custom_flag_filename:
            if as_rates:
                print(f"✅ AS币种是自定义币种，但今日已有汇率记录")
                print(f"✅ 要重新添加AS币种，需要先删除今日汇率记录")
                print(f"✅ 删除后，AS币种会重新出现在新增币种列表中")
            else:
                print(f"✅ AS币种是自定义币种，今日无汇率记录")
                print(f"✅ 可以直接调用add_currency API重新添加")
        else:
            print(f"❌ AS币种不是自定义币种")
            print(f"✅ 需要为AS币种设置custom_flag_filename字段")
        
        return {
            'as_currency': as_currency,
            'as_rates': as_rates,
            'is_custom_currency': is_custom_currency,
            'custom_currencies': custom_currencies,
            'today': today
        }
        
    except Exception as e:
        print(f"❌ 测试自定义币种重新添加逻辑时出错: {e}")
        return None
    finally:
        DatabaseService.close_session(session)

def test_delete_as_rates():
    """测试删除AS币种的汇率记录"""
    session = DatabaseService.get_session()
    try:
        print(f"\n=== 测试删除AS币种的汇率记录 ===")
        
        # 查找AS币种
        as_currency = session.query(Currency).filter_by(currency_code='AS').first()
        if not as_currency:
            print(f"❌ AS币种不存在")
            return
        
        # 查找今日汇率记录
        today = date.today()
        today_rates = session.query(ExchangeRate).filter_by(
            currency_id=as_currency.id,
            rate_date=today
        ).all()
        
        print(f"✅ AS币种今日汇率记录数量: {len(today_rates)}")
        
        if today_rates:
            print(f"✅ 将删除 {len(today_rates)} 条今日汇率记录")
            
            for rate in today_rates:
                print(f"   - 删除汇率记录: 网点ID {rate.branch_id}, 买入 {rate.buy_rate}, 卖出 {rate.sell_rate}")
                session.delete(rate)
            
            DatabaseService.commit_session(session)
            print(f"✅ 成功删除AS币种的今日汇率记录")
            print(f"✅ 现在可以重新添加AS币种到今日汇率列表")
        else:
            print(f"✅ AS币种今日无汇率记录，无需删除")
        
    except Exception as e:
        DatabaseService.rollback_session(session)
        print(f"❌ 删除AS币种汇率记录时出错: {e}")
    finally:
        DatabaseService.close_session(session)

def main():
    """主函数"""
    result = test_custom_currency_add_logic()
    
    if result:
        print(f"\n=== 总结 ===")
        if result['is_custom_currency']:
            if result['as_rates']:
                print(f"✅ AS币种是自定义币种，但今日已有汇率记录")
                print(f"✅ 需要删除今日汇率记录后才能重新添加")
                
                # 询问是否删除汇率记录
                response = input("是否删除AS币种的今日汇率记录？(y/n): ")
                if response.lower() == 'y':
                    test_delete_as_rates()
            else:
                print(f"✅ AS币种是自定义币种，今日无汇率记录")
                print(f"✅ 可以直接重新添加")
        else:
            print(f"❌ AS币种不是自定义币种，需要设置custom_flag_filename")

if __name__ == "__main__":
    main() 
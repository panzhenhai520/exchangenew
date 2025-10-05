#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
同步CurrencyTemplate的修改到Currency表
当CurrencyTemplate中的自定义币种信息被修改后，同步更新Currency表中的对应记录
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from models.exchange_models import Currency, CurrencyTemplate, ExchangeRate
from datetime import date

def sync_currency_template_changes():
    """同步CurrencyTemplate的修改到Currency表"""
    session = DatabaseService.get_session()
    try:
        print("=== 同步CurrencyTemplate的修改到Currency表 ===")
        
        # 1. 获取所有有自定义图标的CurrencyTemplate
        custom_templates = session.query(CurrencyTemplate).filter(
            CurrencyTemplate.custom_flag_filename.isnot(None),
            CurrencyTemplate.custom_flag_filename != ''
        ).all()
        
        print(f"✅ 找到 {len(custom_templates)} 个自定义币种模板")
        
        updated_count = 0
        for template in custom_templates:
            print(f"\n--- 检查币种模板: {template.currency_code} ---")
            
            # 查找对应的Currency记录
            currency = session.query(Currency).filter_by(
                currency_code=template.currency_code
            ).first()
            
            if not currency:
                print(f"   ❌ Currency表中不存在币种 {template.currency_code}")
                continue
            
            print(f"   ✅ 找到Currency记录: {currency.currency_code}")
            print(f"   - 模板名称: {template.currency_name}")
            print(f"   - 币种名称: {currency.currency_name}")
            print(f"   - 模板图标: {template.custom_flag_filename}")
            print(f"   - 币种图标: {currency.custom_flag_filename}")
            
            # 检查是否需要更新
            needs_update = False
            update_fields = []
            
            if template.currency_name != currency.currency_name:
                needs_update = True
                update_fields.append(f"名称: {currency.currency_name} -> {template.currency_name}")
            
            if template.custom_flag_filename != currency.custom_flag_filename:
                needs_update = True
                update_fields.append(f"图标: {currency.custom_flag_filename} -> {template.custom_flag_filename}")
            
            if template.flag_code != currency.flag_code:
                needs_update = True
                update_fields.append(f"国旗代码: {currency.flag_code} -> {template.flag_code}")
            
            if template.country != currency.country:
                needs_update = True
                update_fields.append(f"国家: {currency.country} -> {template.country}")
            
            if template.symbol != currency.symbol:
                needs_update = True
                update_fields.append(f"符号: {currency.symbol} -> {template.symbol}")
            
            if needs_update:
                print(f"   ⚠️  需要更新以下字段:")
                for field in update_fields:
                    print(f"      - {field}")
                
                # 询问是否更新
                response = input(f"   是否更新币种 {template.currency_code}？(y/n): ")
                if response.lower() == 'y':
                    # 更新Currency记录
                    currency.currency_name = template.currency_name
                    currency.custom_flag_filename = template.custom_flag_filename
                    currency.flag_code = template.flag_code
                    currency.country = template.country
                    currency.symbol = template.symbol
                    
                    DatabaseService.commit_session(session)
                    updated_count += 1
                    print(f"   ✅ 已更新币种 {template.currency_code}")
                else:
                    print(f"   ❌ 跳过更新币种 {template.currency_code}")
            else:
                print(f"   ✅ 币种 {template.currency_code} 数据已同步")
        
        print(f"\n=== 同步完成 ===")
        print(f"✅ 总共检查了 {len(custom_templates)} 个自定义币种模板")
        print(f"✅ 更新了 {updated_count} 个币种记录")
        
        return {
            'total_templates': len(custom_templates),
            'updated_count': updated_count
        }
        
    except Exception as e:
        print(f"❌ 同步CurrencyTemplate修改时出错: {e}")
        return None
    finally:
        DatabaseService.close_session(session)

def check_as_currency_status():
    """检查AS币种的当前状态"""
    session = DatabaseService.get_session()
    try:
        print(f"\n=== 检查AS币种状态 ===")
        
        # 检查CurrencyTemplate
        as_template = session.query(CurrencyTemplate).filter_by(currency_code='AS').first()
        if as_template:
            print(f"✅ AS币种模板:")
            print(f"   - 名称: {as_template.currency_name}")
            print(f"   - 图标: {as_template.custom_flag_filename}")
            print(f"   - 国旗代码: {as_template.flag_code}")
        else:
            print(f"❌ AS币种模板不存在")
        
        # 检查Currency
        as_currency = session.query(Currency).filter_by(currency_code='AS').first()
        if as_currency:
            print(f"✅ AS币种:")
            print(f"   - 名称: {as_currency.currency_name}")
            print(f"   - 图标: {as_currency.custom_flag_filename}")
            print(f"   - 国旗代码: {as_currency.flag_code}")
        else:
            print(f"❌ AS币种不存在")
        
        # 检查今日汇率记录
        today = date.today()
        as_rates = session.query(ExchangeRate).filter(
            ExchangeRate.currency_id == as_currency.id if as_currency else 0,
            ExchangeRate.rate_date == today
        ).all()
        
        print(f"✅ AS币种今日汇率记录: {len(as_rates)} 条")
        for rate in as_rates:
            print(f"   - 网点ID: {rate.branch_id}, 买入: {rate.buy_rate}, 卖出: {rate.sell_rate}")
        
    except Exception as e:
        print(f"❌ 检查AS币种状态时出错: {e}")
    finally:
        DatabaseService.close_session(session)

def main():
    """主函数"""
    print("=== CurrencyTemplate与Currency表同步工具 ===")
    print("1. 检查AS币种状态")
    print("2. 同步CurrencyTemplate修改到Currency表")
    print("3. 退出")
    
    while True:
        choice = input("\n请选择操作 (1-3): ")
        
        if choice == '1':
            check_as_currency_status()
        elif choice == '2':
            result = sync_currency_template_changes()
            if result:
                print(f"\n同步完成！更新了 {result['updated_count']} 个币种")
        elif choice == '3':
            print("退出程序")
            break
        else:
            print("无效选择，请重新输入")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试币种图标显示问题
验证自定义币种在添加前后的图标显示情况
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from models.exchange_models import Currency, CurrencyTemplate, ExchangeRate, ExchangeTransaction
from datetime import date

def test_currency_icon_display():
    """测试币种图标显示问题"""
    session = DatabaseService.get_session()
    try:
        print("=== 测试币种图标显示问题 ===")
        
        # 1. 检查AS币种在CurrencyTemplate中的信息
        as_template = session.query(CurrencyTemplate).filter_by(currency_code='AS').first()
        if as_template:
            print(f"✅ AS币种模板信息:")
            print(f"   - ID: {as_template.id}")
            print(f"   - 代码: {as_template.currency_code}")
            print(f"   - 名称: {as_template.currency_name}")
            print(f"   - 自定义图标: {as_template.custom_flag_filename}")
            print(f"   - 国旗代码: {as_template.flag_code}")
        else:
            print(f"❌ AS币种模板不存在")
            return None
        
        # 2. 检查AS币种在Currency表中的信息
        as_currency = session.query(Currency).filter_by(currency_code='AS').first()
        if as_currency:
            print(f"\n✅ AS币种在Currency表中的信息:")
            print(f"   - ID: {as_currency.id}")
            print(f"   - 代码: {as_currency.currency_code}")
            print(f"   - 名称: {as_currency.currency_name}")
            print(f"   - 自定义图标: {as_currency.custom_flag_filename}")
            print(f"   - 国旗代码: {as_currency.flag_code}")
        else:
            print(f"\n❌ AS币种在Currency表中不存在")
        
        # 3. 检查AS币种在今日汇率列表中的信息
        today = date.today()
        as_rates = session.query(ExchangeRate).filter_by(
            currency_id=as_currency.id if as_currency else 0,
            rate_date=today
        ).all()
        
        print(f"\n✅ AS币种今日汇率记录:")
        print(f"   - 汇率记录数量: {len(as_rates)}")
        for rate in as_rates:
            print(f"   - 网点ID: {rate.branch_id}, 买入: {rate.buy_rate}, 卖出: {rate.sell_rate}")
        
        # 4. 模拟get_all_exchange_rates API的返回数据
        print(f"\n=== 模拟get_all_exchange_rates API返回数据 ===")
        if as_currency and as_rates:
            # 模拟API返回的数据结构
            api_data = {
                'id': as_rates[0].id,
                'currency_id': as_currency.id,
                'currency_code': as_currency.currency_code,
                'currency_name': as_currency.currency_name,
                'flag_code': as_currency.flag_code,
                'custom_flag_filename': as_currency.custom_flag_filename,
                'country': as_currency.country,
                'symbol': as_currency.symbol,
                'buy_rate': as_rates[0].buy_rate,
                'sell_rate': as_rates[0].sell_rate,
                'rate_date': as_rates[0].rate_date.strftime('%Y-%m-%d'),
                'created_at': as_rates[0].created_at.strftime('%Y-%m-%d %H:%M:%S') if as_rates[0].created_at else None,
                'updated_at': as_rates[0].updated_at.strftime('%Y-%m-%d %H:%M:%S') if as_rates[0].updated_at else None,
                'created_by': as_rates[0].created_by,
                'editor_name': '测试用户',
                'sort_order': as_rates[0].sort_order,
                'is_published': False,
                'batch_saved': getattr(as_rates[0], 'batch_saved', 0),
                'batch_saved_time': getattr(as_rates[0], 'batch_saved_time', None),
                'batch_saved_by': getattr(as_rates[0], 'batch_saved_by', None)
            }
            
            print(f"✅ API返回的数据:")
            print(f"   - currency_code: {api_data['currency_code']}")
            print(f"   - currency_name: {api_data['currency_name']}")
            print(f"   - flag_code: {api_data['flag_code']}")
            print(f"   - custom_flag_filename: {api_data['custom_flag_filename']}")
            print(f"   - country: {api_data['country']}")
            print(f"   - symbol: {api_data['symbol']}")
            
            # 检查图标显示所需的关键字段
            print(f"\n✅ 图标显示检查:")
            print(f"   - flag_code存在: {'是' if api_data['flag_code'] else '否'}")
            print(f"   - custom_flag_filename存在: {'是' if api_data['custom_flag_filename'] else '否'}")
            
            if api_data['custom_flag_filename']:
                print(f"   ✅ 自定义图标文件: {api_data['custom_flag_filename']}")
                print(f"   ✅ 图标路径: /flags/{api_data['custom_flag_filename']}")
            elif api_data['flag_code']:
                print(f"   ✅ 标准图标文件: {api_data['flag_code']}")
                print(f"   ✅ 图标路径: /flags/{api_data['flag_code'].lower()}.svg")
            else:
                print(f"   ❌ 无图标信息")
        else:
            print(f"❌ AS币种无今日汇率记录")
        
        # 5. 模拟get_currency_templates API的返回数据
        print(f"\n=== 模拟get_currency_templates API返回数据 ===")
        template_data = as_template.to_dict()
        print(f"✅ 模板API返回的数据:")
        print(f"   - currency_code: {template_data['currency_code']}")
        print(f"   - currency_name: {template_data['currency_name']}")
        print(f"   - flag_code: {template_data['flag_code']}")
        print(f"   - custom_flag_filename: {template_data['custom_flag_filename']}")
        print(f"   - country: {template_data['country']}")
        print(f"   - symbol: {template_data['symbol']}")
        
        # 6. 对比两个API的数据
        print(f"\n=== 数据对比 ===")
        if as_currency and as_template:
            print(f"✅ CurrencyTemplate vs Currency:")
            print(f"   - 自定义图标一致: {as_template.custom_flag_filename == as_currency.custom_flag_filename}")
            print(f"   - 国旗代码一致: {as_template.flag_code == as_currency.flag_code}")
            print(f"   - 币种名称一致: {as_template.currency_name == as_currency.currency_name}")
            
            if as_template.custom_flag_filename != as_currency.custom_flag_filename:
                print(f"   ⚠️  自定义图标不一致!")
                print(f"      - 模板: {as_template.custom_flag_filename}")
                print(f"      - 币种: {as_currency.custom_flag_filename}")
        
        # 7. 建议解决方案
        print(f"\n=== 建议解决方案 ===")
        if as_currency and as_template:
            if as_template.custom_flag_filename != as_currency.custom_flag_filename:
                print(f"✅ 问题：Currency表中的custom_flag_filename与CurrencyTemplate不一致")
                print(f"✅ 解决方案：更新Currency表中的custom_flag_filename")
                print(f"✅ 执行SQL: UPDATE currencies SET custom_flag_filename = '{as_template.custom_flag_filename}' WHERE currency_code = 'AS'")
            else:
                print(f"✅ 数据一致，图标应该正常显示")
        else:
            print(f"❌ 数据不完整，需要检查")
        
        # 8. 保存需要的数据（在会话关闭前）
        result = {
            'as_template': {
                'id': as_template.id,
                'currency_code': as_template.currency_code,
                'currency_name': as_template.currency_name,
                'custom_flag_filename': as_template.custom_flag_filename,
                'flag_code': as_template.flag_code
            },
            'as_currency': {
                'id': as_currency.id if as_currency else None,
                'currency_code': as_currency.currency_code if as_currency else None,
                'currency_name': as_currency.currency_name if as_currency else None,
                'custom_flag_filename': as_currency.custom_flag_filename if as_currency else None,
                'flag_code': as_currency.flag_code if as_currency else None
            },
            'as_rates': [{
                'id': rate.id,
                'branch_id': rate.branch_id,
                'buy_rate': rate.buy_rate,
                'sell_rate': rate.sell_rate
            } for rate in as_rates],
            'template_data': template_data
        }
        
        return result
        
    except Exception as e:
        print(f"❌ 测试币种图标显示问题时出错: {e}")
        return None
    finally:
        DatabaseService.close_session(session)

def fix_currency_custom_flag():
    """修复Currency表中的custom_flag_filename"""
    session = DatabaseService.get_session()
    try:
        print(f"\n=== 修复Currency表中的custom_flag_filename ===")
        
        # 查找AS币种
        as_currency = session.query(Currency).filter_by(currency_code='AS').first()
        as_template = session.query(CurrencyTemplate).filter_by(currency_code='AS').first()
        
        if not as_currency:
            print(f"❌ AS币种在Currency表中不存在")
            return
        
        if not as_template:
            print(f"❌ AS币种模板不存在")
            return
        
        print(f"✅ 修复前:")
        print(f"   - Currency.custom_flag_filename: {as_currency.custom_flag_filename}")
        print(f"   - CurrencyTemplate.custom_flag_filename: {as_template.custom_flag_filename}")
        
        if as_currency.custom_flag_filename != as_template.custom_flag_filename:
            # 更新Currency表中的custom_flag_filename
            as_currency.custom_flag_filename = as_template.custom_flag_filename
            DatabaseService.commit_session(session)
            
            print(f"✅ 修复后:")
            print(f"   - Currency.custom_flag_filename: {as_currency.custom_flag_filename}")
            print(f"   - CurrencyTemplate.custom_flag_filename: {as_template.custom_flag_filename}")
            print(f"✅ 修复完成！")
        else:
            print(f"✅ 数据已一致，无需修复")
        
    except Exception as e:
        DatabaseService.rollback_session(session)
        print(f"❌ 修复Currency表中的custom_flag_filename时出错: {e}")
    finally:
        DatabaseService.close_session(session)

def main():
    """主函数"""
    result = test_currency_icon_display()
    
    if result:
        print(f"\n=== 总结 ===")
        if result['as_template'] and result['as_currency']:
            template_filename = result['as_template']['custom_flag_filename']
            currency_filename = result['as_currency']['custom_flag_filename']
            
            if template_filename != currency_filename:
                print(f"✅ 发现问题：Currency表中的custom_flag_filename与CurrencyTemplate不一致")
                print(f"   - 模板: {template_filename}")
                print(f"   - 币种: {currency_filename}")
                print(f"✅ 需要修复Currency表中的数据")
                
                # 询问是否修复
                response = input("是否修复Currency表中的custom_flag_filename？(y/n): ")
                if response.lower() == 'y':
                    fix_currency_custom_flag()
            else:
                print(f"✅ 数据一致，图标应该正常显示")
        else:
            print(f"❌ 数据不完整，需要检查")

if __name__ == "__main__":
    main() 
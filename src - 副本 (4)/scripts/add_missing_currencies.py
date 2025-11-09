#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
批量添加截图1中的币种到系统中
确保所有汇率牌上的币种都可以在系统中使用
"""

import os
import sys
from datetime import datetime, date

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from services.db_service import DatabaseService
from models.exchange_models import Currency, ExchangeRate, Branch, SystemLog
from data.iso_countries import get_currency_by_code

def add_missing_currencies():
    """添加截图1中缺失的币种"""
    
    # 截图1中的所有币种及其汇率（以THB为基准）
    currencies_to_add = [
        {'code': 'USD', 'buy': 30.54, 'sell': 33.99},
        {'code': 'EUR', 'buy': 32.27, 'sell': 37.74},
        {'code': 'CNY', 'buy': 4.10, 'sell': 4.83},
        {'code': 'JPY', 'buy': 0.1894, 'sell': 0.2402},
        {'code': 'HKD', 'buy': 3.83, 'sell': 4.46},
        {'code': 'NZD', 'buy': 17.69, 'sell': 20.24},
        {'code': 'RUB', 'buy': 0.00, 'sell': 0.00},  # 暂停交易
        {'code': 'SEK', 'buy': 0.00, 'sell': 3.48},  # 只卖出
        {'code': 'SAR', 'buy': 6.70, 'sell': 9.81},
        {'code': 'NOK', 'buy': 0.00, 'sell': 3.40},  # 只卖出
        {'code': 'DKK', 'buy': 0.00, 'sell': 4.98},  # 只卖出
        {'code': 'ZAR', 'buy': 1.14, 'sell': 2.08},
        {'code': 'BND', 'buy': 23.34, 'sell': 25.61},
        {'code': 'BHD', 'buy': 65.17, 'sell': 95.90},
        # 补充其他常见币种
        {'code': 'GBP', 'buy': 36.85, 'sell': 43.12},
        {'code': 'CHF', 'buy': 32.18, 'sell': 37.61},
        {'code': 'CAD', 'buy': 22.14, 'sell': 25.93},
        {'code': 'SGD', 'buy': 21.85, 'sell': 25.59},
        {'code': 'AUD', 'buy': 19.67, 'sell': 23.03},
        {'code': 'KRW', 'buy': 0.0208, 'sell': 0.0268},
        {'code': 'INR', 'buy': 0.33, 'sell': 0.42}
    ]
    
    session = DatabaseService.get_session()
    
    try:
        # 获取A005网点信息
        branch = session.query(Branch).filter_by(branch_code='A005').first()
        if not branch:
            print("错误：找不到A005网点")
            return
        
        # 确认本币是THB
        if branch.base_currency_id != 13:  # THB的ID应该是13
            print(f"警告：A005网点的本币不是THB (当前base_currency_id: {branch.base_currency_id})")
        
        added_currencies = 0
        updated_rates = 0
        skipped_currencies = 0
        
        for currency_data in currencies_to_add:
            currency_code = currency_data['code']
            
            # 跳过本币THB
            if currency_code == 'THB':
                continue
                
            print(f"\n处理币种: {currency_code}")
            
            # 检查币种是否已存在
            existing_currency = session.query(Currency).filter_by(
                currency_code=currency_code
            ).first()
            
            if not existing_currency:
                # 从ISO数据获取币种信息
                iso_data = get_currency_by_code(currency_code)
                if not iso_data:
                    print(f"  警告：未找到 {currency_code} 的ISO数据，跳过")
                    skipped_currencies += 1
                    continue
                
                # 添加新币种
                new_currency = Currency(
                    currency_code=currency_code,
                    currency_name=iso_data['currency_name_zh'],
                    country=iso_data['country_name_zh'],
                    flag_code=iso_data['country_code'],
                    symbol=iso_data['currency_symbol'],
                    created_at=datetime.now()
                )
                session.add(new_currency)
                session.flush()  # 获取ID
                
                print(f"  ✓ 添加币种: {currency_code} - {iso_data['currency_name_zh']}")
                added_currencies += 1
                
                currency_id = new_currency.id
            else:
                print(f"  币种 {currency_code} 已存在")
                currency_id = existing_currency.id
            
            # 检查是否已有汇率记录
            existing_rate = session.query(ExchangeRate).filter_by(
                branch_id=branch.id,
                currency_id=currency_id
            ).first()
            
            if existing_rate:
                # 更新汇率
                existing_rate.buy_rate = currency_data['buy']
                existing_rate.sell_rate = currency_data['sell']
                existing_rate.updated_at = datetime.now()
                print(f"  ✓ 更新汇率: 买入 {currency_data['buy']}, 卖出 {currency_data['sell']}")
                updated_rates += 1
            else:
                # 添加新汇率记录
                new_rate = ExchangeRate(
                    branch_id=branch.id,
                    currency_id=currency_id,
                    rate_date=date.today(),
                    buy_rate=currency_data['buy'],
                    sell_rate=currency_data['sell'],
                    created_by=1,  # 系统管理员ID
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                session.add(new_rate)
                print(f"  ✓ 添加汇率: 买入 {currency_data['buy']}, 卖出 {currency_data['sell']}")
                updated_rates += 1
        
        # 记录操作日志
        log = SystemLog(
            operation='BATCH_ADD_CURRENCIES',
            operator_id=1,  # 系统管理员ID
            log_type='currency_management',
            action=f"批量添加币种和汇率",
            details=f"添加币种: {added_currencies}个, 更新汇率: {updated_rates}个, 跳过: {skipped_currencies}个",
            ip_address='127.0.0.1'
        )
        session.add(log)
        
        session.commit()
        
        print(f"\n=== 批量添加完成 ===")
        print(f"新增币种: {added_currencies}个")
        print(f"更新汇率: {updated_rates}个")
        print(f"跳过币种: {skipped_currencies}个")
        print(f"总计处理: {len(currencies_to_add)}个币种")
        
        # 验证结果
        total_currencies = session.query(Currency).count()
        total_rates = session.query(ExchangeRate).filter_by(branch_id=branch.id).count()
        print(f"\n系统中现有币种总数: {total_currencies}")
        print(f"A005网点汇率记录总数: {total_rates}")
        
    except Exception as e:
        session.rollback()
        print(f"错误：批量添加币种失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        DatabaseService.close_session(session)

if __name__ == '__main__':
    print("开始批量添加截图1中的币种...")
    add_missing_currencies()
    print("批量添加完成！") 
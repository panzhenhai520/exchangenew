#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查AS币种在数据库中的状态
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import get_db_url
from sqlalchemy import create_engine, text

def check_as_currency_status():
    """检查AS币种在数据库中的状态"""
    
    # 获取数据库连接
    database_url = get_db_url()
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as connection:
            # 检查currencies表中的AS币种
            currencies_sql = """
            SELECT id, currency_code, currency_name, flag_code, custom_flag_filename
            FROM currencies 
            WHERE currency_code = 'AS'
            """
            
            currencies_result = connection.execute(text(currencies_sql))
            currencies = currencies_result.fetchall()
            
            print("📋 currencies表中的AS币种：")
            for currency in currencies:
                print(f"  - ID: {currency[0]}, 代码: {currency[1]}, 名称: {currency[2]}, 国旗代码: {currency[3]}, 自定义图标: {currency[4]}")
            
            # 检查currency_templates表中的AS币种
            templates_sql = """
            SELECT id, currency_code, currency_name, flag_code, custom_flag_filename
            FROM currency_templates 
            WHERE currency_code = 'AS'
            """
            
            templates_result = connection.execute(text(templates_sql))
            templates = templates_result.fetchall()
            
            print("\n📋 currency_templates表中的AS币种：")
            for template in templates:
                print(f"  - ID: {template[0]}, 代码: {template[1]}, 名称: {template[2]}, 国旗代码: {template[3]}, 自定义图标: {template[4]}")
            
            # 检查exchange_rates表中的AS币种
            rates_sql = """
            SELECT er.id, er.currency_id, er.branch_id, er.buy_rate, er.sell_rate, er.rate_date
            FROM exchange_rates er
            INNER JOIN currencies c ON er.currency_id = c.id
            WHERE c.currency_code = 'AS'
            """
            
            rates_result = connection.execute(text(rates_sql))
            rates = rates_result.fetchall()
            
            print("\n📋 exchange_rates表中的AS币种汇率：")
            for rate in rates:
                print(f"  - 汇率ID: {rate[0]}, 币种ID: {rate[1]}, 网点ID: {rate[2]}, 买入价: {rate[3]}, 卖出价: {rate[4]}, 日期: {rate[5]}")
                
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("开始检查AS币种状态...")
    success = check_as_currency_status()
    if success:
        print("✅ 检查完成")
    else:
        print("❌ 检查失败")
        sys.exit(1) 
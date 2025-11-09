#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查AS币种在CurrencyTemplate表中的数据
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import get_db_url
from sqlalchemy import create_engine, text

def check_currency_template_as():
    """检查AS币种在CurrencyTemplate表中的数据"""
    
    # 获取数据库连接
    database_url = get_db_url()
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as connection:
            # 检查currency_templates表中的AS币种
            templates_sql = """
            SELECT id, currency_code, currency_name, country, flag_code, custom_flag_filename
            FROM currency_templates 
            WHERE currency_code = 'AS'
            """
            
            templates_result = connection.execute(text(templates_sql))
            templates = templates_result.fetchall()
            
            print("📋 currency_templates表中的AS币种：")
            for template in templates:
                print(f"  - ID: {template[0]}, 代码: {template[1]}, 名称: {template[2]}, 国家: {template[3]}, 国旗代码: {template[4]}, 自定义图标: {template[5]}")
            
            # 检查currencies表中的AS币种
            currencies_sql = """
            SELECT id, currency_code, currency_name, country, flag_code, custom_flag_filename
            FROM currencies 
            WHERE currency_code = 'AS'
            """
            
            currencies_result = connection.execute(text(currencies_sql))
            currencies = currencies_result.fetchall()
            
            print("\n📋 currencies表中的AS币种：")
            for currency in currencies:
                print(f"  - ID: {currency[0]}, 代码: {currency[1]}, 名称: {currency[2]}, 国家: {currency[3]}, 国旗代码: {currency[4]}, 自定义图标: {currency[5]}")
                
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("开始检查AS币种在CurrencyTemplate表中的数据...")
    success = check_currency_template_as()
    if success:
        print("✅ 检查完成")
    else:
        print("❌ 检查失败")
        sys.exit(1) 
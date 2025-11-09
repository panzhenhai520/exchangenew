#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from datetime import datetime

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from iso_countries import ISO_COUNTRIES_CURRENCIES
from services.db_service import DatabaseService

# 导入模型
try:
    from models.exchange_models import CurrencyTemplate
except ImportError:
    from src.models.exchange_models import CurrencyTemplate

def init_currency_templates():
    """初始化币种模板数据"""
    session = None
    
    try:
        session = DatabaseService.get_session()
        
        # 检查是否已有数据
        count = session.query(CurrencyTemplate).count()
        
        if count > 0:
            print(f"币种模板表已有 {count} 条记录，跳过初始化")
            return
        
        # 从currencies表获取已有的币种（如果存在）
        try:
            from models.exchange_models import Currency
            existing_currencies = session.query(Currency.currency_code).distinct().all()
            existing_currencies = [row[0] for row in existing_currencies]
        except Exception:
            existing_currencies = []
        
        templates_added = 0
        
        # 为已有币种创建模板
        for currency_code in existing_currencies:
            # 查找对应的ISO数据
            iso_data = None
            for country in ISO_COUNTRIES_CURRENCIES:
                if country['currency_code'] == currency_code:
                    iso_data = country
                    break
            
            if iso_data:
                template = CurrencyTemplate(
                    currency_code=currency_code,
                    currency_name=iso_data['currency_name_zh'],
                    country=iso_data['country_name_zh'],
                    flag_code=iso_data['country_code'],
                    symbol=iso_data['currency_symbol'],
                    description=f"基于ISO标准自动生成的{iso_data['currency_name_zh']}模板",
                    is_active=True
                )
                session.add(template)
                templates_added += 1
        
        # 添加所有ISO标准货币模板（去重）
        added_currencies = set(existing_currencies)
        for country in ISO_COUNTRIES_CURRENCIES:
            currency_code = country['currency_code']
            if currency_code not in added_currencies:
                template = CurrencyTemplate(
                    currency_code=currency_code,
                    currency_name=country['currency_name_zh'],
                    country=country['country_name_zh'],
                    flag_code=country['country_code'],
                    symbol=country['currency_symbol'],
                    description=f"ISO 3166-1标准{country['currency_name_zh']}模板",
                    is_active=True
                )
                session.add(template)
                added_currencies.add(currency_code)
                templates_added += 1
        
        DatabaseService.commit_session(session)
        print(f"成功初始化 {templates_added} 个币种模板")
        
        # 显示初始化结果
        total_count = session.query(CurrencyTemplate).count()
        print(f"币种模板表现在共有 {total_count} 条记录")
        
    except Exception as e:
        if session:
            DatabaseService.rollback_session(session)
        print(f"初始化币种模板失败: {e}")
    finally:
        if session:
            DatabaseService.close_session(session)

if __name__ == '__main__':
    init_currency_templates()
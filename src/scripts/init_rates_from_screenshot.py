#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
根据截图汇率数据初始化项目汇率
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, datetime
from models.exchange_models import CurrencyTemplate, Currency, ExchangeRate, Branch, Operator
from services.db_service import DatabaseService

# 从截图中提取的汇率数据 (2025-01-20, 1:50 PM, Page 2/2)
SCREENSHOT_RATES = [
    {"code": "USD", "name": "美元", "country": "美国", "flag": "us", "buy": 30.54, "sell": 33.99, "symbol": "$"},
    {"code": "EUR", "name": "欧元", "country": "欧盟", "flag": "eu", "buy": 32.27, "sell": 37.74, "symbol": "€"},
    {"code": "CNY", "name": "人民币", "country": "中国", "flag": "cn", "buy": 4.10, "sell": 4.83, "symbol": "¥"},
    {"code": "JPY", "name": "日元", "country": "日本", "flag": "jp", "buy": 0.1894, "sell": 0.2402, "symbol": "¥"},
    {"code": "HKD", "name": "港币", "country": "香港", "flag": "hk", "buy": 3.83, "sell": 4.46, "symbol": "HK$"},
    {"code": "NZD", "name": "新西兰元", "country": "新西兰", "flag": "nz", "buy": 17.69, "sell": 20.24, "symbol": "NZ$"},
    {"code": "SEK", "name": "瑞典克朗", "country": "瑞典", "flag": "se", "buy": 0.00, "sell": 3.18, "symbol": "kr"},
    {"code": "SAR", "name": "沙特里亚尔", "country": "沙特阿拉伯", "flag": "sa", "buy": 6.70, "sell": 9.81, "symbol": "﷼"},
    {"code": "NOK", "name": "挪威克朗", "country": "挪威", "flag": "no", "buy": 0.00, "sell": 3.40, "symbol": "kr"},
    {"code": "DKK", "name": "丹麦克朗", "country": "丹麦", "flag": "dk", "buy": 0.00, "sell": 4.98, "symbol": "kr"},
    {"code": "ZAR", "name": "南非兰特", "country": "南非", "flag": "za", "buy": 1.14, "sell": 2.08, "symbol": "R"},
    {"code": "BND", "name": "文莱元", "country": "文莱", "flag": "bn", "buy": 23.34, "sell": 25.61, "symbol": "B$"},
    {"code": "BHD", "name": "巴林第纳尔", "country": "巴林", "flag": "bh", "buy": 65.17, "sell": 95.90, "symbol": "BD"},
]

def ensure_currency_template_exists(session, currency_data):
    """确保币种模板存在"""
    template = session.query(CurrencyTemplate).filter_by(currency_code=currency_data["code"]).first()
    
    if not template:
        print(f"创建币种模板: {currency_data['code']} - {currency_data['name']}")
        template = CurrencyTemplate(
            currency_code=currency_data["code"],
            currency_name=currency_data["name"],
            country=currency_data["country"],
            flag_code=currency_data["flag"],
            symbol=currency_data["symbol"],
            description=f"{currency_data['name']} ({currency_data['country']})",
            is_active=True
        )
        session.add(template)
        session.flush()
    
    return template

def ensure_currency_exists(session, template):
    """确保币种存在于currencies表"""
    currency = session.query(Currency).filter_by(currency_code=template.currency_code).first()
    
    if not currency:
        print(f"创建币种: {template.currency_code} - {template.currency_name}")
        currency = Currency(
            currency_code=template.currency_code,
            currency_name=template.currency_name,
            country=template.country,
            flag_code=template.flag_code,
            symbol=template.symbol
        )
        session.add(currency)
        session.flush()
    
    return currency

def clear_existing_rates(session, today):
    """清空今日汇率数据"""
    existing_rates = session.query(ExchangeRate).filter_by(rate_date=today).all()
    if existing_rates:
        print(f"清空现有的 {len(existing_rates)} 条今日汇率记录...")
        for rate in existing_rates:
            session.delete(rate)

def create_exchange_rate(session, branch_id, currency_id, rate_data, operator_id, today):
    """创建汇率记录"""
    if rate_data["buy"] == 0 and rate_data["sell"] == 0:
        print(f"跳过 {rate_data['code']} (买入价和卖出价都为0)")
        return None
    
    print(f"创建汇率: {rate_data['code']} - 买入: {rate_data['buy']}, 卖出: {rate_data['sell']}")
    
    rate = ExchangeRate(
        branch_id=branch_id,
        currency_id=currency_id,
        rate_date=today,
        buy_rate=rate_data["buy"],
        sell_rate=rate_data["sell"],
        created_by=operator_id,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    session.add(rate)
    return rate

def main():
    print("开始根据截图汇率数据初始化项目...")
    print("=" * 50)
    
    session = DatabaseService.get_session()
    
    try:
        today = date.today()
        print(f"初始化日期: {today}")
        
        branch = session.query(Branch).first()
        if not branch:
            print("错误: 未找到网点，请先创建网点")
            return
        
        operator = session.query(Operator).first()
        if not operator:
            print("错误: 未找到操作员，请先创建操作员")
            return
            
        print(f"使用网点: {branch.branch_name} (ID: {branch.id})")
        print(f"使用操作员: {operator.name} (ID: {operator.id})")
        print()
        
        clear_existing_rates(session, today)
        
        created_count = 0
        skipped_count = 0
        
        for rate_data in SCREENSHOT_RATES:
            print(f"处理币种: {rate_data['code']}...")
            
            template = ensure_currency_template_exists(session, rate_data)
            currency = ensure_currency_exists(session, template)
            rate = create_exchange_rate(session, branch.id, currency.id, rate_data, operator.id, today)
            if rate:
                created_count += 1
            else:
                skipped_count += 1
            
            print()
        
        DatabaseService.commit_session(session)
        
        print("=" * 50)
        print("汇率初始化完成!")
        print(f"成功创建: {created_count} 条汇率记录")
        print(f"跳过记录: {skipped_count} 条")
        print()
        
        total_rates = session.query(ExchangeRate).filter_by(rate_date=today).count()
        print(f"当前今日汇率总数: {total_rates}")
        
        rates = session.query(ExchangeRate, Currency).join(Currency).filter(
            ExchangeRate.rate_date == today
        ).all()
        
        print("\n当前汇率列表:")
        print("-" * 60)
        print(f"{'币种':<8} {'币种名称':<12} {'买入价':<10} {'卖出价':<10}")
        print("-" * 60)
        for rate, currency in rates:
            print(f"{currency.currency_code:<8} {currency.currency_name:<12} {rate.buy_rate:<10.4f} {rate.sell_rate:<10.4f}")
        
    except Exception as e:
        print(f"发生错误: {str(e)}")
        DatabaseService.rollback_session(session)
        raise
    finally:
        DatabaseService.close_session(session)

if __name__ == "__main__":
    main() 
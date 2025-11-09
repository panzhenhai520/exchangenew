#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清空exchange_rates表并重新写入正确的汇率数据
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, datetime
from models.exchange_models import CurrencyTemplate, Currency, ExchangeRate, Branch, Operator
from services.db_service import DatabaseService

# 截图中的汇率数据 (完整的14个币种)
SCREENSHOT_RATES = [
    {"code": "USD", "name": "美元", "buy": 30.54, "sell": 33.99},
    {"code": "EUR", "name": "欧元", "buy": 32.27, "sell": 37.74},
    {"code": "CNY", "name": "人民币", "buy": 4.10, "sell": 4.83},
    {"code": "JPY", "name": "日元", "buy": 0.1894, "sell": 0.2402},
    {"code": "HKD", "name": "港币", "buy": 3.83, "sell": 4.46},
    {"code": "NZD", "name": "新西兰元", "buy": 17.69, "sell": 20.24},
    {"code": "RUB", "name": "俄罗斯卢布", "buy": 0.00, "sell": 0.00},
    {"code": "SEK", "name": "瑞典克朗", "buy": 0.00, "sell": 3.48},
    {"code": "SAR", "name": "沙特里亚尔", "buy": 6.70, "sell": 9.81},
    {"code": "NOK", "name": "挪威克朗", "buy": 0.00, "sell": 3.40},
    {"code": "DKK", "name": "丹麦克朗", "buy": 0.00, "sell": 4.98},
    {"code": "ZAR", "name": "南非兰特", "buy": 1.14, "sell": 2.08},
    {"code": "BND", "name": "文莱元", "buy": 23.34, "sell": 25.61},
    {"code": "BHD", "name": "巴林第纳尔", "buy": 65.17, "sell": 95.90},
]

def clear_exchange_rates(session):
    """清空exchange_rates表"""
    try:
        deleted_count = session.query(ExchangeRate).delete()
        print(f"已清空exchange_rates表，删除了 {deleted_count} 条记录")
        return deleted_count
    except Exception as e:
        print(f"清空exchange_rates表时发生错误: {e}")
        raise

def find_or_create_currency(session, rate_data):
    """查找或创建币种"""
    # 首先通过currency_templates表查找
    template = session.query(CurrencyTemplate).filter_by(currency_code=rate_data["code"]).first()
    
    if not template:
        print(f"在currency_templates中未找到 {rate_data['code']}，创建模板...")
        # 根据币种代码推断国家和标志
        country_map = {
            "USD": {"country": "美国", "flag": "us", "symbol": "$"},
            "EUR": {"country": "欧盟", "flag": "eu", "symbol": "€"},
            "CNY": {"country": "中国", "flag": "cn", "symbol": "¥"},
            "JPY": {"country": "日本", "flag": "jp", "symbol": "¥"},
            "HKD": {"country": "香港", "flag": "hk", "symbol": "HK$"},
            "NZD": {"country": "新西兰", "flag": "nz", "symbol": "NZ$"},
            "RUB": {"country": "俄罗斯", "flag": "ru", "symbol": "₽"},
            "SEK": {"country": "瑞典", "flag": "se", "symbol": "kr"},
            "SAR": {"country": "沙特阿拉伯", "flag": "sa", "symbol": "﷼"},
            "NOK": {"country": "挪威", "flag": "no", "symbol": "kr"},
            "DKK": {"country": "丹麦", "flag": "dk", "symbol": "kr"},
            "ZAR": {"country": "南非", "flag": "za", "symbol": "R"},
            "BND": {"country": "文莱", "flag": "bn", "symbol": "B$"},
            "BHD": {"country": "巴林", "flag": "bh", "symbol": "BD"},
        }
        
        info = country_map.get(rate_data["code"], {"country": "未知", "flag": "xx", "symbol": ""})
        
        template = CurrencyTemplate(
            currency_code=rate_data["code"],
            currency_name=rate_data["name"],
            country=info["country"],
            flag_code=info["flag"],
            symbol=info["symbol"],
            description=f"{rate_data['name']} ({info['country']})",
            is_active=True
        )
        session.add(template)
        session.flush()
    
    # 查找或创建currencies表中的记录
    currency = session.query(Currency).filter_by(currency_code=rate_data["code"]).first()
    
    if not currency:
        print(f"在currencies中未找到 {rate_data['code']}，创建币种...")
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

def create_exchange_rates(session):
    """创建汇率记录"""
    # 获取网点和操作员
    branch = session.query(Branch).first()
    operator = session.query(Operator).first()
    
    if not branch or not operator:
        raise Exception("未找到网点或操作员信息，请先初始化基础数据")
    
    today = date.today()
    created_count = 0
    
    print(f"开始创建汇率记录，日期: {today}")
    print(f"使用网点: {branch.branch_name} (ID: {branch.id})")
    print(f"使用操作员: {operator.name} (ID: {operator.id})")
    print("-" * 60)
    
    for rate_data in SCREENSHOT_RATES:
        print(f"处理币种: {rate_data['code']} - {rate_data['name']}")
        
        # 查找或创建币种
        currency = find_or_create_currency(session, rate_data)
        
        # 创建汇率记录
        exchange_rate = ExchangeRate(
            branch_id=branch.id,
            currency_id=currency.id,
            rate_date=today,
            buy_rate=rate_data["buy"],
            sell_rate=rate_data["sell"],
            created_by=operator.id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        session.add(exchange_rate)
        
        print(f"  -> 创建汇率: 买入 {rate_data['buy']}, 卖出 {rate_data['sell']}")
        created_count += 1
    
    return created_count

def main():
    print("开始重建exchange_rates表...")
    print("=" * 60)
    
    session = DatabaseService.get_session()
    
    try:
        # 第1步：清空exchange_rates表
        print("第1步：清空exchange_rates表")
        deleted_count = clear_exchange_rates(session)
        print()
        
        # 第2步：重新创建汇率记录
        print("第2步：重新创建汇率记录")
        created_count = create_exchange_rates(session)
        print()
        
        # 提交事务
        DatabaseService.commit_session(session)
        
        print("=" * 60)
        print("exchange_rates表重建完成！")
        print(f"删除记录数: {deleted_count}")
        print(f"创建记录数: {created_count}")
        print()
        
        # 验证结果
        today = date.today()
        rates = session.query(ExchangeRate, Currency).join(Currency).filter(
            ExchangeRate.rate_date == today
        ).order_by(Currency.currency_code).all()
        
        print(f"验证结果 - 当前今日汇率总数: {len(rates)}")
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
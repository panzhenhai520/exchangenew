#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
生成历史汇率数据脚本
用于测试汇率趋势图功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, date, timedelta
import random
from decimal import Decimal
from models.exchange_models import ExchangeRate, Currency, Branch, Operator
from services.db_service import DatabaseService

# 基础汇率配置（作为基准值）
BASE_RATES = {
    'USD': {'buy': 30.54, 'sell': 33.99},
    'EUR': {'buy': 32.27, 'sell': 37.74},
    'JPY': {'buy': 0.1894, 'sell': 0.2402},
    'GBP': {'buy': 11.00, 'sell': 11.00},
    'CHF': {'buy': 12.00, 'sell': 12.00},
    'HKD': {'buy': 3.83, 'sell': 4.46},
    'CAD': {'buy': 22.00, 'sell': 22.00},
    'NZD': {'buy': 17.69, 'sell': 20.24},
    'AUD': {'buy': 1.00, 'sell': 2.00},
    'SAR': {'buy': 6.70, 'sell': 9.81},
    'ZAR': {'buy': 1.14, 'sell': 2.08},
    'BND': {'buy': 23.34, 'sell': 25.01},
    'CNY': {'buy': 4.10, 'sell': 4.83}
}

def generate_rate_with_fluctuation(base_rate, day_offset, volatility=0.02):
    """
    生成带随机波动的汇率
    
    Args:
        base_rate: 基础汇率
        day_offset: 天数偏移（0=今天，-1=昨天...）
        volatility: 波动率（默认2%）
    
    Returns:
        float: 调整后的汇率
    """
    # 基于天数的趋势因子（模拟市场趋势）
    trend_factor = 1 + (day_offset * 0.001)  # 每天0.1%的轻微趋势
    
    # 随机波动因子
    random_factor = 1 + random.uniform(-volatility, volatility)
    
    # 应用因子
    adjusted_rate = base_rate * trend_factor * random_factor
    
    # 保持合理精度
    return round(adjusted_rate, 4)

def main():
    print("🔄 开始生成历史汇率数据...")
    
    session = DatabaseService.get_session()
    
    try:
        # 获取默认网点和操作员信息
        branch = session.query(Branch).filter_by(branch_code='A005').first()
        if not branch:
            # 如果没有A005，获取第一个网点
            branch = session.query(Branch).first()
        
        if not branch:
            print("❌ 未找到网点信息")
            return
            
        operator = session.query(Operator).filter_by(login_code='admin').first()
        if not operator:
            operator = session.query(Operator).first()
            
        if not operator:
            print("❌ 未找到操作员信息")
            return
            
        print(f"📍 使用网点: {branch.branch_name} ({branch.branch_code})")
        print(f"👤 使用操作员: {operator.name}")
        
        # 获取所有币种（排除本币）
        currencies = session.query(Currency).filter(
            Currency.id != branch.base_currency_id
        ).all()
        
        if not currencies:
            print("❌ 未找到可用币种")
            return
            
        print(f"💰 找到 {len(currencies)} 个币种")
        
        # 生成过去7天的日期（不包括今天）
        today = date.today()
        historical_dates = [today - timedelta(days=i) for i in range(1, 8)]
        historical_dates.reverse()  # 从最早日期开始
        
        print(f"📅 生成日期范围: {historical_dates[0]} 到 {historical_dates[-1]}")
        
        generated_count = 0
        skipped_count = 0
        
        for target_date in historical_dates:
            print(f"\n📊 处理日期: {target_date}")
            day_offset = (target_date - today).days
            
            for currency in currencies:
                # 检查该日期是否已有汇率记录
                existing_rate = session.query(ExchangeRate).filter_by(
                    branch_id=branch.id,
                    currency_id=currency.id,
                    rate_date=target_date
                ).first()
                
                if existing_rate:
                    print(f"  ⏭️  {currency.currency_code}: 已存在汇率记录，跳过")
                    skipped_count += 1
                    continue
                
                # 获取基础汇率
                base_rates = BASE_RATES.get(currency.currency_code)
                if not base_rates:
                    print(f"  ⚠️  {currency.currency_code}: 未配置基础汇率，跳过")
                    continue
                
                # 生成随机波动的汇率
                buy_rate = generate_rate_with_fluctuation(
                    base_rates['buy'], 
                    day_offset, 
                    volatility=0.015  # 1.5% 波动率
                )
                sell_rate = generate_rate_with_fluctuation(
                    base_rates['sell'], 
                    day_offset, 
                    volatility=0.015
                )
                
                # 确保卖出价 >= 买入价（银行利润）
                if sell_rate < buy_rate:
                    sell_rate = buy_rate * 1.02  # 至少2%利差
                
                # 创建汇率记录
                rate_record = ExchangeRate(
                    branch_id=branch.id,
                    currency_id=currency.id,
                    rate_date=target_date,
                    buy_rate=buy_rate,
                    sell_rate=sell_rate,
                    created_by=operator.id,
                    created_at=datetime.combine(target_date, datetime.min.time()),
                    updated_at=datetime.combine(target_date, datetime.min.time())
                )
                
                session.add(rate_record)
                generated_count += 1
                
                print(f"  ✅ {currency.currency_code}: 买入={buy_rate:.4f}, 卖出={sell_rate:.4f}")
        
        # 提交所有更改
        DatabaseService.commit_session(session)
        
        print(f"\n🎉 历史汇率数据生成完成！")
        print(f"📈 生成记录数: {generated_count}")
        print(f"⏭️  跳过记录数: {skipped_count}")
        print(f"📅 覆盖日期: {len(historical_dates)} 天")
        print(f"💰 涉及币种: {len([c for c in currencies if c.currency_code in BASE_RATES])} 个")
        
        # 显示生成的数据统计
        print(f"\n📊 数据概览:")
        for currency in currencies:
            if currency.currency_code in BASE_RATES:
                count = session.query(ExchangeRate).filter(
                    ExchangeRate.currency_id == currency.id,
                    ExchangeRate.branch_id == branch.id,
                    ExchangeRate.rate_date.in_(historical_dates)
                ).count()
                print(f"  {currency.currency_code}: {count} 条记录")
                
    except Exception as e:
        print(f"❌ 生成历史汇率数据失败: {e}")
        DatabaseService.rollback_session(session)
        import traceback
        traceback.print_exc()
    finally:
        DatabaseService.close_session(session)

if __name__ == '__main__':
    main() 
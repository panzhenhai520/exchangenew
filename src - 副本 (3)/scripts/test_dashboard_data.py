#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试Dashboard数据获取逻辑
验证币种列表和汇率数据是否正确获取
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from models.exchange_models import Currency, CurrencyTemplate, ExchangeRate, Branch, RatePublishRecord, RatePublishDetail
from datetime import date

def test_dashboard_data():
    """测试Dashboard数据获取逻辑"""
    session = DatabaseService.get_session()
    try:
        print("=== Dashboard数据获取测试 ===")
        
        # 1. 检查当前网点信息
        branch = session.query(Branch).filter_by(id=1).first()  # 假设网点ID为1
        if not branch:
            print("❌ 网点不存在")
            return
        
        print(f"✅ 当前网点: {branch.branch_name} (ID: {branch.id})")
        print(f"✅ 本币ID: {branch.base_currency_id}")
        
        # 2. 检查当前网点的币种
        current_currencies = session.query(Currency).filter_by(branch_id=branch.id).all()
        print(f"✅ 当前网点币种数量: {len(current_currencies)}")
        for currency in current_currencies:
            print(f"   - {currency.currency_code}: {currency.currency_name}")
        
        # 3. 检查当前网点的汇率记录
        today = date.today()
        current_rates = session.query(ExchangeRate).filter(
            ExchangeRate.branch_id == branch.id,
            ExchangeRate.rate_date == today
        ).all()
        print(f"✅ 当前网点今日汇率记录数量: {len(current_rates)}")
        for rate in current_rates:
            currency = session.query(Currency).filter_by(id=rate.currency_id).first()
            if currency:
                print(f"   - {currency.currency_code}: 买入={rate.buy_rate}, 卖出={rate.sell_rate}")
        
        # 4. 检查发布记录
        publish_record = session.query(RatePublishRecord).filter(
            RatePublishRecord.branch_id == branch.id,
            RatePublishRecord.publish_date == today
        ).first()
        
        if publish_record:
            print(f"✅ 今日发布记录: ID={publish_record.id}, 时间={publish_record.publish_time}")
            published_details = session.query(RatePublishDetail).filter(
                RatePublishDetail.publish_record_id == publish_record.id
            ).all()
            print(f"✅ 已发布币种数量: {len(published_details)}")
            for detail in published_details:
                currency = session.query(Currency).filter_by(id=detail.currency_id).first()
                if currency:
                    print(f"   - {currency.currency_code}")
        else:
            print("⚠️  今日无发布记录")
        
        # 5. 模拟API调用结果
        print("\n=== 模拟API调用结果 ===")
        
        # 模拟 /rates/available_currencies?published_only=false
        available_currencies = session.query(Currency).filter(
            Currency.id != branch.base_currency_id,
            Currency.branch_id == branch.id
        ).all()
        print(f"✅ /rates/available_currencies (published_only=false): {len(available_currencies)} 个币种")
        
        # 模拟 /rates/all?published_only=false
        all_rates = session.query(ExchangeRate).filter(
            ExchangeRate.branch_id == branch.id,
            ExchangeRate.rate_date == today
        ).all()
        print(f"✅ /rates/all (published_only=false): {len(all_rates)} 条汇率记录")
        
        return {
            'branch': branch,
            'currencies': current_currencies,
            'rates': current_rates,
            'publish_record': publish_record,
            'available_currencies': available_currencies,
            'all_rates': all_rates
        }
        
    except Exception as e:
        print(f"❌ 测试Dashboard数据时出错: {e}")
        return None
    finally:
        DatabaseService.close_session(session)

def main():
    """主函数"""
    result = test_dashboard_data()
    
    if result:
        print(f"\n=== 总结 ===")
        print(f"✅ 币种数量: {len(result['currencies'])}")
        print(f"✅ 汇率记录数量: {len(result['rates'])}")
        print(f"✅ 可获取币种数量: {len(result['available_currencies'])}")
        print(f"✅ 可获取汇率记录数量: {len(result['all_rates'])}")
        
        if len(result['available_currencies']) == 0:
            print("⚠️  警告: 没有可获取的币种，Dashboard可能无法显示币种列表")
        if len(result['all_rates']) == 0:
            print("⚠️  警告: 没有可获取的汇率记录，Dashboard可能无法显示汇率卡片")

if __name__ == "__main__":
    main() 
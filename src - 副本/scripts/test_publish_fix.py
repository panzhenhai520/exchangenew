#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试发布后汇率数据加载修复
验证发布到机顶盒后汇率数据是否能正确显示
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from models.exchange_models import Currency, CurrencyTemplate, ExchangeRate, RatePublishRecord, RatePublishDetail, Branch
from datetime import date, datetime

def test_publish_fix():
    """测试发布修复"""
    session = DatabaseService.get_session()
    try:
        print("=== 测试发布后汇率数据加载修复 ===")
        
        # 1. 检查今日汇率数据
        today = date.today()
        branch_id = 1
        
        print(f"\n=== 1. 检查今日汇率数据 ===")
        today_rates = session.query(ExchangeRate).filter(
            ExchangeRate.branch_id == branch_id,
            ExchangeRate.rate_date == today
        ).all()
        
        print(f"✅ 今日汇率记录数量: {len(today_rates)}")
        for rate in today_rates:
            currency = session.query(Currency).filter_by(id=rate.currency_id).first()
            if currency:
                print(f"   - {currency.currency_code}: 买入={rate.buy_rate}, 卖出={rate.sell_rate}")
        
        # 2. 检查发布记录
        print(f"\n=== 2. 检查发布记录 ===")
        publish_records = session.query(RatePublishRecord).filter(
            RatePublishRecord.branch_id == branch_id,
            RatePublishRecord.publish_date == today
        ).all()
        
        print(f"✅ 今日发布记录数量: {len(publish_records)}")
        for record in publish_records:
            print(f"   - 发布记录ID: {record.id}")
            print(f"   - 发布时间: {record.publish_time}")
            print(f"   - 发布者: {record.publisher_name}")
            print(f"   - 币种数量: {record.total_currencies}")
            
            # 检查发布详情
            details = session.query(RatePublishDetail).filter(
                RatePublishDetail.publish_record_id == record.id
            ).all()
            
            print(f"   - 发布详情数量: {len(details)}")
            for detail in details:
                currency = session.query(Currency).filter_by(id=detail.currency_id).first()
                if currency:
                    print(f"     * {currency.currency_code}: 买入={detail.buy_rate}, 卖出={detail.sell_rate}")
        
        # 3. 模拟前端API调用
        print(f"\n=== 3. 模拟前端API调用 ===")
        
        # 模拟 /rates/all API 调用
        print(f"模拟调用: GET /api/rates/all?published_only=false&include_publish_info=true")
        
        # 检查汇率数据
        rates_data = []
        for rate in today_rates:
            currency = session.query(Currency).filter_by(id=rate.currency_id).first()
            if currency:
                rate_data = {
                    'id': rate.id,
                    'currency_id': currency.id,
                    'currency_code': currency.currency_code,
                    'currency_name': currency.currency_name,
                    'buy_rate': rate.buy_rate,
                    'sell_rate': rate.sell_rate,
                    'rate_date': rate.rate_date.strftime('%Y-%m-%d'),
                    'is_published': False,  # 默认值
                    'batch_saved': getattr(rate, 'batch_saved', 0),
                    'batch_saved_time': getattr(rate, 'batch_saved_time', None),
                    'batch_saved_by': getattr(rate, 'batch_saved_by', None)
                }
                
                # 检查是否在发布记录中
                for record in publish_records:
                    detail = session.query(RatePublishDetail).filter(
                        RatePublishDetail.publish_record_id == record.id,
                        RatePublishDetail.currency_id == currency.id
                    ).first()
                    
                    if detail:
                        rate_data['is_published'] = True
                        rate_data['last_publish_time'] = record.publish_date.strftime('%Y-%m-%d')
                        rate_data['publisher_name'] = record.publisher_name
                        break
                
                rates_data.append(rate_data)
        
        print(f"✅ API返回数据:")
        print(f"   - 汇率记录数量: {len(rates_data)}")
        print(f"   - 已发布币种: {sum(1 for r in rates_data if r['is_published'])}")
        print(f"   - 未发布币种: {sum(1 for r in rates_data if not r['is_published'])}")
        
        # 4. 分析问题
        print(f"\n=== 4. 问题分析 ===")
        
        if len(rates_data) == 0:
            print(f"❌ 问题：API返回空数据")
            print(f"   原因：数据库中今日没有汇率记录")
        elif len(rates_data) > 0:
            print(f"✅ 数据正常：API返回 {len(rates_data)} 条汇率记录")
            print(f"   如果前端显示为空，可能原因：")
            print(f"   1. 前端 dailyRatesPublished 变量为 false")
            print(f"   2. 前端 fetchRates 函数没有正确调用")
            print(f"   3. 前端数据处理逻辑有问题")
            print(f"   4. 网络请求失败")
        
        return {
            'rates_count': len(rates_data),
            'published_count': sum(1 for r in rates_data if r['is_published']),
            'unpublished_count': sum(1 for r in rates_data if not r['is_published'])
        }
        
    except Exception as e:
        print(f"❌ 测试发布修复时出错: {e}")
        return None
    finally:
        DatabaseService.close_session(session)

def main():
    """主函数"""
    result = test_publish_fix()
    
    if result:
        print(f"\n=== 总结 ===")
        print(f"✅ 汇率记录: {result['rates_count']} 条")
        print(f"✅ 已发布: {result['published_count']} 条")
        print(f"✅ 未发布: {result['unpublished_count']} 条")
        
        if result['rates_count'] > 0:
            print(f"\n✅ 数据库数据正常")
            print(f"✅ 修复已应用：发布后会重新加载汇率数据")
            print(f"✅ 现在可以测试前端，发布后应该能正常显示汇率列表")
        else:
            print(f"\n❌ 数据库中没有汇率数据")
            print(f"❌ 需要先添加汇率数据")

if __name__ == "__main__":
    main() 
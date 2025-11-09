#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试发布后汇率数据消失的问题
诊断发布到机顶盒后为什么今日汇率列表会清空
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from models.exchange_models import Currency, CurrencyTemplate, ExchangeRate, RatePublishRecord, RatePublishDetail, Branch
from datetime import date, datetime

def test_publish_issue():
    """测试发布问题"""
    session = DatabaseService.get_session()
    try:
        print("=== 测试发布后汇率数据消失问题 ===")
        
        # 1. 检查今日汇率数据
        today = date.today()
        branch_id = 1  # 假设当前网点ID为1
        
        print(f"\n=== 1. 检查今日汇率数据 ===")
        today_rates = session.query(ExchangeRate).filter(
            ExchangeRate.branch_id == branch_id,
            ExchangeRate.rate_date == today
        ).all()
        
        print(f"✅ 今日汇率记录数量: {len(today_rates)}")
        for rate in today_rates:
            currency = session.query(Currency).filter_by(id=rate.currency_id).first()
            if currency:
                print(f"   - {currency.currency_code}: 买入={rate.buy_rate}, 卖出={rate.sell_rate}, 排序={rate.sort_order}")
        
        # 2. 检查发布记录
        print(f"\n=== 2. 检查今日发布记录 ===")
        publish_record = session.query(RatePublishRecord).filter(
            RatePublishRecord.branch_id == branch_id,
            RatePublishRecord.publish_date == today
        ).first()
        
        if publish_record:
            print(f"✅ 找到今日发布记录:")
            print(f"   - ID: {publish_record.id}")
            print(f"   - 发布时间: {publish_record.publish_time}")
            print(f"   - 发布者: {publish_record.publisher_name}")
            print(f"   - 币种数量: {publish_record.total_currencies}")
            
            # 检查发布详情
            publish_details = session.query(RatePublishDetail).filter(
                RatePublishDetail.publish_record_id == publish_record.id
            ).all()
            
            print(f"   - 发布详情数量: {len(publish_details)}")
            for detail in publish_details:
                currency = session.query(Currency).filter_by(id=detail.currency_id).first()
                if currency:
                    print(f"     * {currency.currency_code}: 买入={detail.buy_rate}, 卖出={detail.sell_rate}")
        else:
            print(f"❌ 今日没有发布记录")
        
        # 3. 检查币种模板
        print(f"\n=== 3. 检查币种模板 ===")
        templates = session.query(CurrencyTemplate).filter_by(is_active=True).all()
        print(f"✅ 活跃币种模板数量: {len(templates)}")
        for template in templates:
            print(f"   - {template.currency_code}: {template.currency_name}")
        
        # 4. 检查Currency表
        print(f"\n=== 4. 检查Currency表 ===")
        currencies = session.query(Currency).all()
        print(f"✅ Currency表记录数量: {len(currencies)}")
        for currency in currencies:
            print(f"   - {currency.currency_code}: {currency.currency_name}")
        
        # 5. 检查网点信息
        print(f"\n=== 5. 检查网点信息 ===")
        branch = session.query(Branch).filter_by(id=branch_id).first()
        if branch:
            print(f"✅ 网点信息:")
            print(f"   - 网点代码: {branch.branch_code}")
            print(f"   - 网点名称: {branch.branch_name}")
            print(f"   - 本币ID: {branch.base_currency_id}")
            
            if branch.base_currency_id:
                base_currency = session.query(Currency).filter_by(id=branch.base_currency_id).first()
                if base_currency:
                    print(f"   - 本币代码: {base_currency.currency_code}")
        else:
            print(f"❌ 网点不存在")
        
        # 6. 分析问题
        print(f"\n=== 6. 问题分析 ===")
        
        if len(today_rates) == 0:
            print(f"❌ 问题确认：今日没有汇率记录")
            print(f"   可能原因：")
            print(f"   1. 发布过程中意外删除了汇率记录")
            print(f"   2. 自动初始化功能没有正常工作")
            print(f"   3. 数据库事务回滚导致数据丢失")
        else:
            print(f"✅ 今日有 {len(today_rates)} 条汇率记录")
            print(f"   如果前端显示为空，可能是：")
            print(f"   1. API返回数据格式问题")
            print(f"   2. 前端数据处理逻辑问题")
            print(f"   3. 网络请求失败")
        
        return {
            'today_rates_count': len(today_rates),
            'publish_record_exists': publish_record is not None,
            'templates_count': len(templates),
            'currencies_count': len(currencies)
        }
        
    except Exception as e:
        print(f"❌ 测试发布问题时出错: {e}")
        return None
    finally:
        DatabaseService.close_session(session)

def fix_empty_rates():
    """修复空汇率数据"""
    session = DatabaseService.get_session()
    try:
        print(f"\n=== 修复空汇率数据 ===")
        
        today = date.today()
        branch_id = 1
        
        # 检查今日汇率记录
        today_rates = session.query(ExchangeRate).filter(
            ExchangeRate.branch_id == branch_id,
            ExchangeRate.rate_date == today
        ).all()
        
        if len(today_rates) == 0:
            print(f"❌ 今日没有汇率记录，开始修复...")
            
            # 获取所有非本币的货币
            branch = session.query(Branch).filter_by(id=branch_id).first()
            if not branch:
                print(f"❌ 网点不存在")
                return
            
            base_currency_id = branch.base_currency_id
            currencies = session.query(Currency).filter(
                Currency.id != base_currency_id
            ).all()
            
            print(f"✅ 找到 {len(currencies)} 个非本币货币")
            
            # 为每个货币创建今日汇率记录
            created_count = 0
            for currency in currencies:
                # 检查是否已有记录
                existing_rate = session.query(ExchangeRate).filter(
                    ExchangeRate.currency_id == currency.id,
                    ExchangeRate.branch_id == branch_id,
                    ExchangeRate.rate_date == today
                ).first()
                
                if not existing_rate:
                    # 创建新的汇率记录
                    new_rate = ExchangeRate(
                        currency_id=currency.id,
                        branch_id=branch_id,
                        rate_date=today,
                        buy_rate=0.0,
                        sell_rate=0.0,
                        created_by=1,
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                        sort_order=currency.id
                    )
                    session.add(new_rate)
                    created_count += 1
                    print(f"   + 创建 {currency.currency_code} 的汇率记录")
            
            DatabaseService.commit_session(session)
            print(f"✅ 成功创建 {created_count} 条汇率记录")
        else:
            print(f"✅ 今日已有 {len(today_rates)} 条汇率记录，无需修复")
        
    except Exception as e:
        DatabaseService.rollback_session(session)
        print(f"❌ 修复汇率数据时出错: {e}")
    finally:
        DatabaseService.close_session(session)

def main():
    """主函数"""
    result = test_publish_issue()
    
    if result:
        print(f"\n=== 总结 ===")
        print(f"✅ 今日汇率记录: {result['today_rates_count']} 条")
        print(f"✅ 发布记录存在: {result['publish_record_exists']}")
        print(f"✅ 币种模板: {result['templates_count']} 个")
        print(f"✅ Currency记录: {result['currencies_count']} 条")
        
        if result['today_rates_count'] == 0:
            print(f"\n❌ 发现问题：今日没有汇率记录")
            response = input("是否修复空汇率数据？(y/n): ")
            if response.lower() == 'y':
                fix_empty_rates()
        else:
            print(f"\n✅ 汇率数据正常，问题可能在前端或API调用")

if __name__ == "__main__":
    main() 
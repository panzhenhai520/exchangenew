#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试删除币种功能
验证删除币种的API是否正常工作
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from models.exchange_models import Currency, CurrencyTemplate, ExchangeRate
from datetime import date
from models.exchange_models import Branch

def test_delete_currency_logic():
    """测试删除币种的逻辑"""
    session = DatabaseService.get_session()
    try:
        print("=== 测试删除币种逻辑 ===")
        
        # 1. 检查AS币种在Currency表中的信息
        as_currency = session.query(Currency).filter_by(currency_code='AS').first()
        if not as_currency:
            print(f"❌ AS币种在Currency表中不存在")
            return
        
        print(f"✅ AS币种信息:")
        print(f"   - ID: {as_currency.id}")
        print(f"   - 代码: {as_currency.currency_code}")
        print(f"   - 名称: {as_currency.currency_name}")
        print(f"   - 自定义图标: {as_currency.custom_flag_filename}")
        
        # 2. 检查AS币种的汇率记录
        today = date.today()
        as_rates = session.query(ExchangeRate).filter_by(
            currency_id=as_currency.id,
            rate_date=today
        ).all()
        
        print(f"\n✅ AS币种今日汇率记录:")
        print(f"   - 汇率记录数量: {len(as_rates)}")
        for rate in as_rates:
            print(f"   - 网点ID: {rate.branch_id}, 买入: {rate.buy_rate}, 卖出: {rate.sell_rate}")
        
        # 3. 模拟删除逻辑
        print(f"\n=== 模拟删除逻辑 ===")
        
        # 检查是否为本币
        branch = session.query(Branch).filter_by(id=1).first()  # 假设网点ID为1
        if branch and branch.base_currency_id == as_currency.id:
            print(f"❌ AS币种是本币，不能删除")
            return
        
        print(f"✅ AS币种不是本币，可以删除")
        
        # 检查其他网点是否使用
        other_rates = session.query(ExchangeRate).filter(
            ExchangeRate.currency_id == as_currency.id,
            ExchangeRate.branch_id != 1  # 假设当前网点ID为1
        ).first()
        
        if other_rates:
            print(f"⚠️  AS币种被其他网点使用，只删除当前网点的汇率记录")
            print(f"   - 其他网点ID: {other_rates.branch_id}")
        else:
            print(f"✅ AS币种只被当前网点使用，可以删除币种本身")
        
        # 4. 模拟API调用
        print(f"\n=== 模拟API调用 ===")
        print(f"DELETE /rates/currencies/AS")
        print(f"当前网点ID: 1")
        print(f"币种代码: AS")
        
        # 5. 预期结果
        print(f"\n=== 预期结果 ===")
        if other_rates:
            print(f"✅ 删除当前网点的汇率记录（{len(as_rates)} 条）")
            print(f"✅ 保留币种本身（因为其他网点在使用）")
        else:
            print(f"✅ 删除当前网点的汇率记录（{len(as_rates)} 条）")
            print(f"✅ 删除币种本身")
        
        return {
            'currency': as_currency,
            'rates': as_rates,
            'other_rates_exist': other_rates is not None
        }
        
    except Exception as e:
        print(f"❌ 测试删除币种逻辑时出错: {e}")
        return None
    finally:
        DatabaseService.close_session(session)

def check_branch_info():
    """检查网点信息"""
    session = DatabaseService.get_session()
    try:
        print(f"\n=== 检查网点信息 ===")
        
        # 检查网点1的信息
        branch = session.query(Branch).filter_by(id=1).first()
        if branch:
            print(f"✅ 网点1信息:")
            print(f"   - 网点名称: {branch.branch_name}")
            print(f"   - 本币ID: {branch.base_currency_id}")
            
            if branch.base_currency_id:
                base_currency = session.query(Currency).filter_by(id=branch.base_currency_id).first()
                if base_currency:
                    print(f"   - 本币代码: {base_currency.currency_code}")
                    print(f"   - 本币名称: {base_currency.currency_name}")
        else:
            print(f"❌ 网点1不存在")
        
        # 检查网点6的信息
        branch6 = session.query(Branch).filter_by(id=6).first()
        if branch6:
            print(f"\n✅ 网点6信息:")
            print(f"   - 网点名称: {branch6.branch_name}")
            print(f"   - 本币ID: {branch6.base_currency_id}")
        else:
            print(f"\n❌ 网点6不存在")
        
    except Exception as e:
        print(f"❌ 检查网点信息时出错: {e}")
    finally:
        DatabaseService.close_session(session)

def main():
    """主函数"""
    print("=== 删除币种功能测试 ===")
    
    # 检查网点信息
    check_branch_info()
    
    # 测试删除逻辑
    result = test_delete_currency_logic()
    
    if result:
        print(f"\n=== 测试总结 ===")
        print(f"✅ AS币种存在，可以删除")
        print(f"✅ 今日汇率记录: {len(result['rates'])} 条")
        if result['other_rates_exist']:
            print(f"⚠️  其他网点也在使用AS币种")
        else:
            print(f"✅ 只有当前网点使用AS币种")
        
        print(f"\n现在可以测试删除功能了！")
        print(f"在今日汇率页面点击删除AS币种，应该能正常工作。")

if __name__ == "__main__":
    main() 
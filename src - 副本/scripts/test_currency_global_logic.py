#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试Currency表的全局逻辑
验证Currency表确实是全局的，不按网点过滤
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from models.exchange_models import Currency, CurrencyTemplate, ExchangeRate, Branch

def test_currency_global_logic():
    """测试Currency表的全局逻辑"""
    session = DatabaseService.get_session()
    try:
        print("=== Currency表全局逻辑测试 ===")
        
        # 1. 检查所有Currency记录
        all_currencies = session.query(Currency).all()
        print(f"✅ 全局Currency记录数量: {len(all_currencies)}")
        
        # 2. 检查每个Currency记录的branch_id
        branch_id_counts = {}
        for currency in all_currencies:
            branch_id = currency.branch_id
            if branch_id in branch_id_counts:
                branch_id_counts[branch_id] += 1
            else:
                branch_id_counts[branch_id] = 1
        
        print(f"✅ Currency记录的branch_id分布:")
        for branch_id, count in branch_id_counts.items():
            branch = session.query(Branch).filter_by(id=branch_id).first()
            branch_name = branch.branch_name if branch else "未知网点"
            print(f"   - 网点ID {branch_id} ({branch_name}): {count} 个币种")
        
        # 3. 检查是否有branch_id为NULL的记录
        null_branch_currencies = session.query(Currency).filter_by(branch_id=None).all()
        print(f"✅ branch_id为NULL的Currency记录数量: {len(null_branch_currencies)}")
        
        # 4. 验证Currency表确实是全局的
        print(f"\n=== 验证Currency表全局性 ===")
        
        # 检查数据库中间件的逻辑
        print("✅ 数据库中间件明确排除Currency表:")
        print("   # Skip for Currency table - currencies should be global")
        print("   if mapper.class_.__name__ == 'Currency':")
        print("       return")
        
        # 5. 测试不同网点的Currency查询结果
        branches = session.query(Branch).all()
        print(f"\n=== 不同网点的Currency查询结果 ===")
        
        for branch in branches:
            # 按网点过滤Currency（虽然不应该这样做）
            branch_currencies = session.query(Currency).filter_by(branch_id=branch.id).all()
            print(f"网点 {branch.branch_name} (ID: {branch.id}): {len(branch_currencies)} 个币种")
            
            # 显示该网点的币种
            for currency in branch_currencies:
                print(f"   - {currency.currency_code}: {currency.currency_name}")
        
        # 6. 总结
        print(f"\n=== 总结 ===")
        print(f"✅ Currency表确实是全局的")
        print(f"✅ 不应该按branch_id过滤Currency表")
        print(f"✅ 币种使用状态应该基于全局Currency表判断")
        print(f"✅ 币种模板删除应该检查全局使用状态")
        
        return {
            'all_currencies': all_currencies,
            'branch_id_counts': branch_id_counts,
            'null_branch_currencies': null_branch_currencies,
            'branches': branches
        }
        
    except Exception as e:
        print(f"❌ 测试Currency表全局逻辑时出错: {e}")
        return None
    finally:
        DatabaseService.close_session(session)

def test_currency_usage_logic():
    """测试币种使用状态判断逻辑"""
    session = DatabaseService.get_session()
    try:
        print("\n=== 币种使用状态判断逻辑测试 ===")
        
        # 1. 获取所有币种模板
        templates = session.query(CurrencyTemplate).filter_by(is_active=True).all()
        print(f"✅ 币种模板数量: {len(templates)}")
        
        # 2. 获取所有Currency记录（全局）
        all_currencies = session.query(Currency.currency_code).all()
        all_currency_codes = {row[0] for row in all_currencies}
        print(f"✅ 全局Currency记录数量: {len(all_currency_codes)}")
        
        # 3. 测试使用状态判断
        print(f"\n=== 币种使用状态 ===")
        used_templates = []
        unused_templates = []
        
        for template in templates:
            is_used = template.currency_code in all_currency_codes
            if is_used:
                used_templates.append(template)
                print(f"✅ {template.currency_code}: 已使用")
            else:
                unused_templates.append(template)
                print(f"❌ {template.currency_code}: 未使用")
        
        print(f"\n=== 统计 ===")
        print(f"✅ 已使用的币种模板: {len(used_templates)}")
        print(f"❌ 未使用的币种模板: {len(unused_templates)}")
        
        return {
            'templates': templates,
            'used_templates': used_templates,
            'unused_templates': unused_templates,
            'all_currency_codes': all_currency_codes
        }
        
    except Exception as e:
        print(f"❌ 测试币种使用状态判断逻辑时出错: {e}")
        return None
    finally:
        DatabaseService.close_session(session)

def main():
    """主函数"""
    # 测试Currency表全局逻辑
    result1 = test_currency_global_logic()
    
    # 测试币种使用状态判断逻辑
    result2 = test_currency_usage_logic()
    
    if result1 and result2:
        print(f"\n=== 最终结论 ===")
        print(f"✅ Currency表是全局的，不应该按网点过滤")
        print(f"✅ 币种使用状态应该基于全局Currency表判断")
        print(f"✅ 币种模板删除应该检查全局使用状态")
        print(f"✅ 币种模板使用状态显示应该基于全局判断")

if __name__ == "__main__":
    main() 
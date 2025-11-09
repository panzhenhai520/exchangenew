#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试币种模板删除逻辑
验证币种模板是否可以安全删除
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from models.exchange_models import Currency, CurrencyTemplate, ExchangeRate, Branch

def test_currency_template_deletion():
    """测试币种模板删除逻辑"""
    session = DatabaseService.get_session()
    try:
        print("=== 币种模板删除逻辑测试 ===")
        
        # 1. 检查所有币种模板
        templates = session.query(CurrencyTemplate).filter_by(is_active=True).all()
        print(f"✅ 币种模板数量: {len(templates)}")
        
        # 2. 检查每个模板的使用情况
        for template in templates:
            print(f"\n--- 币种模板: {template.currency_code} ---")
            
            # 检查是否在任何网点使用
            using_currencies = session.query(Currency).filter_by(
                currency_code=template.currency_code
            ).all()
            
            if using_currencies:
                print(f"⚠️  币种 {template.currency_code} 正在被使用")
                print(f"   使用网点数量: {len(using_currencies)}")
                
                # 获取使用该币种的网点信息
                for currency in using_currencies:
                    branch = session.query(Branch).filter_by(id=currency.branch_id).first()
                    if branch:
                        print(f"   - 网点: {branch.branch_name} (ID: {branch.id})")
                    else:
                        print(f"   - 网点ID: {currency.branch_id} (网点信息不存在)")
                
                # 检查是否可以删除
                print(f"   ❌ 不能删除：币种正在被使用")
            else:
                print(f"✅ 币种 {template.currency_code} 未被使用")
                print(f"   ✅ 可以删除")
        
        # 3. 统计可删除和不可删除的模板
        deletable_templates = []
        non_deletable_templates = []
        
        for template in templates:
            using_currencies = session.query(Currency).filter_by(
                currency_code=template.currency_code
            ).first()
            
            if using_currencies:
                non_deletable_templates.append(template)
            else:
                deletable_templates.append(template)
        
        print(f"\n=== 删除状态统计 ===")
        print(f"✅ 可删除的模板数量: {len(deletable_templates)}")
        print(f"❌ 不可删除的模板数量: {len(non_deletable_templates)}")
        
        if deletable_templates:
            print(f"\n可删除的模板:")
            for template in deletable_templates:
                print(f"   - {template.currency_code}: {template.currency_name}")
        
        if non_deletable_templates:
            print(f"\n不可删除的模板:")
            for template in non_deletable_templates:
                using_currencies = session.query(Currency).filter_by(
                    currency_code=template.currency_code
                ).all()
                branch_names = []
                for currency in using_currencies:
                    branch = session.query(Branch).filter_by(id=currency.branch_id).first()
                    if branch:
                        branch_names.append(branch.branch_name)
                branch_list = ", ".join(branch_names) if branch_names else "未知网点"
                print(f"   - {template.currency_code}: {template.currency_name} (使用网点: {branch_list})")
        
        return {
            'templates': templates,
            'deletable_templates': deletable_templates,
            'non_deletable_templates': non_deletable_templates
        }
        
    except Exception as e:
        print(f"❌ 测试币种模板删除逻辑时出错: {e}")
        return None
    finally:
        DatabaseService.close_session(session)

def test_specific_currency_template(currency_code):
    """测试特定币种模板的删除状态"""
    session = DatabaseService.get_session()
    try:
        print(f"=== 测试币种模板 {currency_code} 的删除状态 ===")
        
        # 检查模板是否存在
        template = session.query(CurrencyTemplate).filter_by(
            currency_code=currency_code.upper()
        ).first()
        
        if not template:
            print(f"❌ 币种模板 {currency_code} 不存在")
            return False
        
        print(f"✅ 币种模板存在: {template.currency_code} - {template.currency_name}")
        
        # 检查是否被使用
        using_currencies = session.query(Currency).filter_by(
            currency_code=template.currency_code
        ).all()
        
        if using_currencies:
            print(f"⚠️  币种 {currency_code} 正在被使用")
            print(f"   使用网点数量: {len(using_currencies)}")
            
            for currency in using_currencies:
                branch = session.query(Branch).filter_by(id=currency.branch_id).first()
                if branch:
                    print(f"   - 网点: {branch.branch_name} (ID: {branch.id})")
                else:
                    print(f"   - 网点ID: {currency.branch_id} (网点信息不存在)")
            
            print(f"   ❌ 不能删除：币种正在被使用")
            return False
        else:
            print(f"✅ 币种 {currency_code} 未被使用")
            print(f"   ✅ 可以删除")
            return True
        
    except Exception as e:
        print(f"❌ 测试币种模板 {currency_code} 时出错: {e}")
        return False
    finally:
        DatabaseService.close_session(session)

def main():
    """主函数"""
    if len(sys.argv) > 1:
        currency_code = sys.argv[1]
        test_specific_currency_template(currency_code)
    else:
        result = test_currency_template_deletion()
        
        if result:
            print(f"\n=== 总结 ===")
            print(f"✅ 总模板数量: {len(result['templates'])}")
            print(f"✅ 可删除数量: {len(result['deletable_templates'])}")
            print(f"❌ 不可删除数量: {len(result['non_deletable_templates'])}")
            
            if len(result['non_deletable_templates']) > 0:
                print("⚠️  注意：有币种模板正在被使用，无法删除")

if __name__ == "__main__":
    main() 
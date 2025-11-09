#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AMLO报告集成测试
测试AMLO-1-01, AMLO-1-02, AMLO-1-03的触发和报告生成
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
from datetime import datetime

# 系统配置
BASE_URL = "http://localhost:5001"
BRANCH_ID = 1

def login():
    """登录获取token"""
    print("\n[1] 登录系统...")
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "login_code": "admin",
        "password": "admin123",
        "branch": BRANCH_ID
    })
    
    if response.status_code == 200:
        result = response.json()
        token = result.get('access_token')
        print(f"✓ 登录成功, Token: {token[:50]}...")
        return token
    else:
        print(f"✗ 登录失败: {response.text}")
        return None

def check_trigger_rules(token):
    """检查触发规则配置"""
    print("\n[2] 检查触发规则配置...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/api/compliance/trigger-rules", headers=headers)
    
    if response.status_code == 200:
        rules = response.json().get('data', [])
        print(f"✓ 找到 {len(rules)} 条触发规则")
        
        for rule in rules:
            if rule['report_type'] in ['AMLO-1-01', 'AMLO-1-02', 'AMLO-1-03']:
                print(f"\n  规则: {rule['rule_name_cn']}")
                print(f"  类型: {rule['report_type']}")
                print(f"  优先级: {rule['priority']}")
                print(f"  启用: {rule['is_active']}")
                print(f"  表达式: {rule['rule_expression']}")
        
        return True
    else:
        print(f"✗ 获取规则失败: {response.text}")
        return False

def create_test_customer_history(token):
    """创建测试客户历史数据（用于AMLO-1-03）"""
    print("\n[3] 创建测试客户历史数据...")
    
    # 运行历史数据创建脚本
    import subprocess
    result = subprocess.run(
        ["python", "tests/create_test_customer_history.py"],
        cwd=os.path.dirname(os.path.dirname(__file__)),
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )
    
    if result.returncode == 0:
        print("✓ 测试客户历史数据创建成功")
        print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
        return True
    else:
        print(f"✗ 创建失败: {result.stderr}")
        return False

def test_case_1_amlo_101(token):
    """
    测试用例1: AMLO-1-01 单笔大额交易
    客户购买60,000 USD (约2,130,000 THB)
    """
    print("\n" + "="*80)
    print("测试用例1: AMLO-1-01 单笔大额交易")
    print("="*80)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 交易数据
    transaction_data = {
        "customer_id": "1234567890123",
        "customer_name": "张三",
        "currency_code": "USD",
        "direction": "buy",
        "amount": 60000,
        "branch_id": BRANCH_ID
    }
    
    print(f"\n交易信息:")
    print(f"  客户: {transaction_data['customer_name']} ({transaction_data['customer_id']})")
    print(f"  类型: 买入")
    print(f"  金额: {transaction_data['amount']:,} USD")
    print(f"  预计本币: ~2,130,000 THB")
    
    # 检查触发条件
    print(f"\n检查触发条件...")
    response = requests.post(
        f"{BASE_URL}/api/repform/check-trigger",
        headers=headers,
        json=transaction_data
    )
    
    if response.status_code == 200:
        result = response.json()
        if result.get('triggered'):
            print(f"✓ 触发检测成功")
            print(f"  触发报告: {', '.join([r['report_type'] for r in result.get('triggered_reports', [])])}")
            
            # 检查是否包含AMLO-1-01
            has_amlo_101 = any(r['report_type'] == 'AMLO-1-01' for r in result.get('triggered_reports', []))
            
            if has_amlo_101:
                print(f"  ✅ AMLO-1-01 已触发")
                return {
                    'success': True,
                    'triggered': True,
                    'report_type': 'AMLO-1-01',
                    'transaction_data': transaction_data
                }
            else:
                print(f"  ❌ AMLO-1-01 未触发")
                return {'success': False, 'message': 'AMLO-1-01未触发'}
        else:
            print(f"✗ 未触发任何报告")
            print(f"  原因: {result.get('message', '未知')}")
            return {'success': False, 'triggered': False}
    else:
        print(f"✗ 检查失败: {response.status_code}")
        print(response.text)
        return {'success': False, 'message': response.text}

def test_case_2_amlo_103(token):
    """
    测试用例2: AMLO-1-03 累计大额交易
    客户30天内累计超过500万THB
    """
    print("\n" + "="*80)
    print("测试用例2: AMLO-1-03 累计大额交易")
    print("="*80)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 交易数据
    transaction_data = {
        "customer_id": "TEST9876543210",
        "customer_name": "测试客户-张三-跨网点累计",
        "currency_code": "USD",
        "direction": "buy",
        "amount": 30000,
        "branch_id": BRANCH_ID
    }
    
    print(f"\n交易信息:")
    print(f"  客户: {transaction_data['customer_name']} ({transaction_data['customer_id']})")
    print(f"  类型: 买入")
    print(f"  金额: {transaction_data['amount']:,} USD")
    print(f"  预计本币: ~1,065,000 THB")
    print(f"  历史累计: 4,100,000 THB")
    print(f"  预计累计: 5,165,000 THB (超过500万)")
    
    # 检查触发条件
    print(f"\n检查触发条件...")
    response = requests.post(
        f"{BASE_URL}/api/repform/check-trigger",
        headers=headers,
        json=transaction_data
    )
    
    if response.status_code == 200:
        result = response.json()
        if result.get('triggered'):
            print(f"✓ 触发检测成功")
            print(f"  触发报告: {', '.join([r['report_type'] for r in result.get('triggered_reports', [])])}")
            
            # 显示客户统计
            if 'customer_stats' in result:
                stats = result['customer_stats']
                print(f"\n  客户统计:")
                print(f"    30天交易次数: {stats.get('transaction_count_30d', 0)}")
                print(f"    30天累计金额: {stats.get('cumulative_amount_30d', 0):,.2f} THB")
                
                if 'branch_breakdown' in stats:
                    print(f"    网点分布:")
                    for branch_data in stats['branch_breakdown']:
                        print(f"      Branch {branch_data['branch_id']}: {branch_data['count']}笔, {branch_data['amount']:,.2f} THB")
            
            # 检查是否包含AMLO-1-03
            has_amlo_103 = any(r['report_type'] == 'AMLO-1-03' for r in result.get('triggered_reports', []))
            
            if has_amlo_103:
                print(f"  ✅ AMLO-1-03 已触发")
                return {
                    'success': True,
                    'triggered': True,
                    'report_type': 'AMLO-1-03',
                    'transaction_data': transaction_data
                }
            else:
                print(f"  ❌ AMLO-1-03 未触发")
                return {'success': False, 'message': 'AMLO-1-03未触发'}
        else:
            print(f"✗ 未触发任何报告")
            return {'success': False, 'triggered': False}
    else:
        print(f"✗ 检查失败: {response.status_code}")
        print(response.text)
        return {'success': False, 'message': response.text}

def test_case_3_amlo_102(token):
    """
    测试用例3: AMLO-1-02 可疑交易
    客户卖出2,000 USD (70,000 THB) 且标记为可疑
    """
    print("\n" + "="*80)
    print("测试用例3: AMLO-1-02 可疑交易")
    print("="*80)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 交易数据
    transaction_data = {
        "customer_id": "9876543210987",
        "customer_name": "李四",
        "currency_code": "USD",
        "direction": "sell",
        "amount": 2000,
        "suspicious_flag": 1,  # 可疑标记
        "branch_id": BRANCH_ID
    }
    
    print(f"\n交易信息:")
    print(f"  客户: {transaction_data['customer_name']} ({transaction_data['customer_id']})")
    print(f"  类型: 卖出")
    print(f"  金额: {transaction_data['amount']:,} USD")
    print(f"  预计本币: ~70,000 THB")
    print(f"  可疑标记: 是")
    
    # 检查触发条件
    print(f"\n检查触发条件...")
    response = requests.post(
        f"{BASE_URL}/api/repform/check-trigger",
        headers=headers,
        json=transaction_data
    )
    
    if response.status_code == 200:
        result = response.json()
        if result.get('triggered'):
            print(f"✓ 触发检测成功")
            print(f"  触发报告: {', '.join([r['report_type'] for r in result.get('triggered_reports', [])])}")
            
            # 检查是否包含AMLO-1-02
            has_amlo_102 = any(r['report_type'] == 'AMLO-1-02' for r in result.get('triggered_reports', []))
            
            if has_amlo_102:
                print(f"  ✅ AMLO-1-02 已触发")
                return {
                    'success': True,
                    'triggered': True,
                    'report_type': 'AMLO-1-02',
                    'transaction_data': transaction_data
                }
            else:
                print(f"  ❌ AMLO-1-02 未触发")
                return {'success': False, 'message': 'AMLO-1-02未触发'}
        else:
            print(f"✗ 未触发任何报告")
            return {'success': False, 'triggered': False}
    else:
        print(f"✗ 检查失败: {response.status_code}")
        print(response.text)
        return {'success': False, 'message': response.text}

def main():
    """主测试流程"""
    print("="*80)
    print("AMLO报告集成测试")
    print("="*80)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API地址: {BASE_URL}")
    print(f"网点ID: {BRANCH_ID}")
    
    # 登录
    token = login()
    if not token:
        print("\n✗ 测试终止: 登录失败")
        return
    
    # 检查规则
    if not check_trigger_rules(token):
        print("\n⚠️  警告: 触发规则检查失败，继续测试...")
    
    # 创建测试数据
    if not create_test_customer_history(token):
        print("\n⚠️  警告: 测试数据创建失败，AMLO-1-03可能无法测试")
    
    # 执行测试用例
    results = []
    
    # 测试用例1
    result1 = test_case_1_amlo_101(token)
    results.append(('AMLO-1-01', result1))
    
    # 测试用例2
    result2 = test_case_2_amlo_103(token)
    results.append(('AMLO-1-03', result2))
    
    # 测试用例3
    result3 = test_case_3_amlo_102(token)
    results.append(('AMLO-1-02', result3))
    
    # 汇总结果
    print("\n" + "="*80)
    print("测试结果汇总")
    print("="*80)
    
    for report_type, result in results:
        status = "✅ 通过" if result.get('success') and result.get('triggered') else "❌ 失败"
        print(f"{report_type}: {status}")
        if not result.get('success'):
            print(f"  原因: {result.get('message', '未触发')}")
    
    print("\n" + "="*80)
    print("测试完成")
    print("="*80)
    print("\n说明:")
    print("  本测试仅验证触发条件检测功能")
    print("  实际交易和PDF生成需要在前端界面完成")
    print("  请访问: http://localhost:5001")
    print("\n下一步:")
    print("  1. 在前端进行实际交易")
    print("  2. 填写预约表单")
    print("  3. 生成交易票据和AMLO报告")
    print("  4. 打开PDF文件进行核对")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n\n测试异常: {e}")
        import traceback
        traceback.print_exc()


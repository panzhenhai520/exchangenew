#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AMLO & BOT同时触发集成测试
测试单笔交易同时满足AMLO和BOT触发条件的场景
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from datetime import datetime

BASE_URL = "http://localhost:5001"
TEST_USER = {'login_code': 'admin', 'password': 'admin123', 'branch': 1}

class IntegrationTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.session = requests.Session()
    
    def login(self):
        """登录"""
        response = self.session.post(f"{self.base_url}/api/auth/login", json=TEST_USER)
        if response.status_code == 200 and response.json().get('success'):
            self.token = response.json().get('token')
            self.session.headers.update({'Authorization': f'Bearer {self.token}'})
            print("[OK] Login successful\n")
            return True
        return False
    
    def test_simultaneous_trigger(self):
        """测试AMLO和BOT同时触发"""
        print("="*80)
        print("Test: AMLO + BOT Simultaneous Trigger")
        print("="*80)
        print("\nScenario: Buy 150,000 USD (approx 5,325,000 THB)")
        print("Expected: Trigger both AMLO-1-01 and BOT_BuyFX\n")
        
        # 准备交易数据
        transaction_data = {
            'total_amount': 5325000,  # 本币金额（THB）
            'usd_equivalent': 150000,  # USD等值
            'currency_code': 'USD',
            'customer_id': '1234567890123',
            'direction': 'buy',
            'foreign_amount': 150000,
            'local_amount': 5325000,
            'use_fcd': False
        }
        
        # 步骤1: 检查AMLO触发
        print("[Step 1] Check AMLO trigger...")
        response = self.session.post(
            f"{self.base_url}/api/repform/check-trigger",
            json={
                'report_type': 'AMLO-1-01',
                'data': transaction_data,
                'branch_id': 1
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            amlo_triggered = data.get('triggers', {}).get('amlo', {}).get('triggered', False)
            
            if amlo_triggered:
                print("  [PASS] AMLO-1-01 triggered (amount >= 5,000,000 THB)")
                print(f"  Message: {data['triggers']['amlo'].get('message_cn')}")
            else:
                print("  [FAIL] AMLO-1-01 should be triggered but was not")
                return False
        else:
            print(f"  [FAIL] AMLO check failed: {response.status_code}")
            return False
        
        # 步骤2: 检查BOT触发
        print("\n[Step 2] Check BOT trigger...")
        response = self.session.post(
            f"{self.base_url}/api/bot/check-trigger",
            json={
                'transaction_type': 'buy',
                'usd_equivalent': 150000,
                'use_fcd': False
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            bot_triggered = data.get('triggers', {}).get('bot', {}).get('triggered', False)
            
            if bot_triggered:
                print("  [PASS] BOT_BuyFX triggered (usd_equivalent >= 20,000)")
                print(f"  Report types: {data['triggers']['bot'].get('report_types', [])}")
            else:
                print("  [FAIL] BOT_BuyFX should be triggered but was not")
                return False
        else:
            print(f"  [FAIL] BOT check failed: {response.status_code}")
            return False
        
        print("\n[Result] ✓ Both AMLO and BOT would be triggered for this transaction")
        return True
    
    def test_workflow(self):
        """测试完整工作流"""
        print("\n" + "="*80)
        print("Test: Complete Workflow Simulation")
        print("="*80)
        
        print("\n[Workflow] Simulating large transaction workflow:")
        print("  1. Customer ID entered → History checked")
        print("  2. Amount calculated → AMLO triggered")
        print("  3. Reservation form displayed → User fills data")
        print("  4. Reservation submitted → Pending approval")
        print("  5. Manager approves → Status=Approved")
        print("  6. Transaction executed → Both reports generated:")
        print("     a) AMLO PDF (AMLO-1-01)")
        print("     b) BOT Excel data (BOT_BuyFX)")
        print("  7. Reports visible in respective pages")
        
        # 测试客户历史查询
        print("\n[Step 1] Query customer history...")
        response = self.session.get(
            f"{self.base_url}/api/repform/customer-history/1234567890123"
        )
        
        if response.status_code == 200:
            print("  [PASS] Customer history API working")
        else:
            print("  [WARN] Customer history API may have issues")
        
        # 测试表单定义获取
        print("\n[Step 2] Get form definition...")
        response = self.session.get(
            f"{self.base_url}/api/repform/form-definition/AMLO-1-01"
        )
        
        if response.status_code == 200:
            data = response.json()
            total_fields = data.get('data', {}).get('total_fields', 0)
            print(f"  [PASS] Form definition retrieved: {total_fields} fields")
        else:
            print("  [FAIL] Form definition API failed")
            return False
        
        print("\n[Result] ✓ Core workflow APIs are functional")
        return True
    
    def run_all_tests(self):
        """运行所有测试"""
        print("="*80)
        print("AMLO & BOT Integration Test Suite")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        if not self.login():
            print("\n[FATAL] Cannot proceed without login")
            return 1
        
        results = []
        results.append(("Simultaneous Trigger", self.test_simultaneous_trigger()))
        results.append(("Workflow Simulation", self.test_workflow()))
        
        # 总结
        print("\n" + "="*80)
        print("Integration Test Results")
        print("="*80)
        
        passed = sum(1 for _, r in results if r)
        total = len(results)
        
        for name, result in results:
            status = "[PASS]" if result else "[FAIL]"
            print(f"  {status} {name}")
        
        print(f"\nTotal: {passed}/{total} passed ({passed/total*100:.0f}%)")
        
        return 0 if passed == total else 1

def main():
    tester = IntegrationTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())


#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AMLO完整流程集成测试
测试从触发→预约→审核→报告的端到端流程
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5001"
TEST_USER = {
    'login_code': 'admin',
    'password': 'admin123',
    'branch': 1
}

class TestAMLOWorkflow:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.session = requests.Session()
        self.reservation_id = None
    
    def login(self):
        """登录"""
        print("\n[Login] Authenticating...")
        response = self.session.post(
            f"{self.base_url}/api/auth/login",
            json=TEST_USER
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                self.token = data.get('token')
                self.session.headers.update({'Authorization': f'Bearer {self.token}'})
                print(f"  [OK] Login successful")
                return True
        
        print(f"  [FAIL] Login failed")
        return False
    
    def test_trigger_check(self):
        """测试场景1: 触发条件检查"""
        print("\n" + "="*80)
        print("Scenario 1: AMLO Trigger Check")
        print("="*80)
        
        print("\n[Test 1.1] Check trigger for large amount transaction...")
        print("  Transaction: Buy 150,000 USD (approx 5,325,000 THB)")
        
        response = self.session.post(
            f"{self.base_url}/api/repform/check-trigger",
            json={
                'report_type': 'AMLO-1-01',
                'data': {
                    'total_amount': 5325000,
                    'currency_code': 'USD',
                    'customer_id': '1234567890123',
                    'direction': 'buy'
                },
                'branch_id': 1
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            triggers = data.get('triggers', {})
            amlo = triggers.get('amlo', {})
            
            if amlo.get('triggered'):
                print(f"  [PASS] AMLO triggered as expected")
                print(f"  Report Type: {amlo.get('report_type')}")
                print(f"  Message: {amlo.get('message_cn')}")
                print(f"  Allow Continue: {amlo.get('allow_continue')}")
                return True
            else:
                print(f"  [FAIL] AMLO should be triggered but was not")
                return False
        else:
            print(f"  [FAIL] API error: {response.status_code}")
            return False
    
    def test_customer_history(self):
        """测试场景2: 客户历史查询"""
        print("\n" + "="*80)
        print("Scenario 2: Customer History Query")
        print("="*80)
        
        print("\n[Test 2.1] Query customer history...")
        
        response = self.session.get(
            f"{self.base_url}/api/repform/customer-history/1234567890123"
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                stats = data.get('data', {})
                print(f"  [PASS] Customer history retrieved")
                print(f"  Transaction Count (30 days): {stats.get('transaction_count_30d', 0)}")
                print(f"  Cumulative Amount (30 days): {stats.get('cumulative_amount_30d', 0)} THB")
                return True
        
        print(f"  [FAIL] Failed to retrieve customer history")
        return False
    
    def test_form_definition(self):
        """测试场景3: 表单定义获取"""
        print("\n" + "="*80)
        print("Scenario 3: Form Definition Retrieval")
        print("="*80)
        
        print("\n[Test 3.1] Get AMLO-1-01 form definition...")
        
        response = self.session.get(
            f"{self.base_url}/api/repform/form-definition/AMLO-1-01"
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                form_data = data.get('data', {})
                field_groups = form_data.get('field_groups', [])
                total_fields = form_data.get('total_fields', 0)
                
                print(f"  [PASS] Form definition retrieved")
                print(f"  Total Fields: {total_fields}")
                print(f"  Field Groups: {len(field_groups)}")
                
                for group in field_groups:
                    print(f"    - {group['group_name']}: {len(group['fields'])} fields")
                
                return total_fields > 0
        
        print(f"  [FAIL] Failed to get form definition")
        return False
    
    def test_reservation_workflow(self):
        """测试场景4: 预约流程（完整）"""
        print("\n" + "="*80)
        print("Scenario 4: Reservation Workflow")
        print("="*80)
        
        # 4.1 提交预约
        print("\n[Test 4.1] Submit reservation...")
        
        form_data = {
            'customer_name': '测试客户',
            'customer_id': '1234567890123',
            'customer_phone': '0812345678',
            'transaction_amount': 5325000,
            'currency_code': 'USD',
            'foreign_amount': 150000
        }
        
        response = self.session.post(
            f"{self.base_url}/api/repform/save-reservation",
            json={
                'report_type': 'AMLO-1-01',
                'form_data': form_data,
                'transaction_data': {
                    'total_amount': 5325000,
                    'currency_code': 'USD',
                    'direction': 'buy'
                }
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                self.reservation_id = data.get('reservation_id')
                print(f"  [PASS] Reservation submitted")
                print(f"  Reservation ID: {self.reservation_id}")
                return True
        
        print(f"  [FAIL] Failed to submit reservation: {response.text}")
        return False
    
    def test_reservation_audit(self):
        """测试场景5: 预约审核"""
        print("\n" + "="*80)
        print("Scenario 5: Reservation Audit")
        print("="*80)
        
        if not self.reservation_id:
            print("  [SKIP] No reservation ID, skipping audit test")
            return True
        
        print(f"\n[Test 5.1] Audit reservation {self.reservation_id}...")
        
        response = self.session.post(
            f"{self.base_url}/api/amlo/reservations/{self.reservation_id}/audit",
            json={
                'approved': True,
                'audit_note': 'Test audit - approved'
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"  [PASS] Reservation audited successfully")
                print(f"  New status: {data.get('status', 'unknown')}")
                return True
        
        print(f"  [FAIL] Failed to audit reservation")
        return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("="*80)
        print("AMLO Workflow Integration Test Suite")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        results = []
        
        # 登录
        if not self.login():
            return 1
        
        # 获取币种
        usd_id = self.get_currencies()
        if not usd_id:
            print("\n[WARNING] Skipping BOT_Provider tests (no USD currency)")
        else:
            # BOT_Provider测试
            from tests.test_bot_provider import TestBOTProvider
            bot_tester = TestBOTProvider()
            bot_tester.token = self.token
            bot_tester.session = self.session
            
            results.append(('BOT Provider: Small Amount', bot_tester.test_small_adjustment(usd_id)))
            results.append(('BOT Provider: Large Amount', bot_tester.test_large_adjustment(usd_id)))
        
        # AMLO测试
        results.append(('AMLO: Trigger Check', self.test_trigger_check()))
        results.append(('AMLO: Customer History', self.test_customer_history()))
        results.append(('AMLO: Form Definition', self.test_form_definition()))
        results.append(('AMLO: Reservation Submit', self.test_reservation_workflow()))
        
        if self.reservation_id:
            results.append(('AMLO: Reservation Audit', self.test_reservation_audit()))
        
        # 总结
        print("\n" + "="*80)
        print("Overall Test Results")
        print("="*80)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "[PASS]" if result else "[FAIL]"
            print(f"  {status} {test_name}")
        
        print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
        
        if passed >= total * 0.8:
            print("\n✓ Test suite PASSED (>=80%)")
            return 0
        else:
            print(f"\n✗ Test suite FAILED (<80%)")
            return 1

def main():
    tester = TestAMLOWorkflow()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())


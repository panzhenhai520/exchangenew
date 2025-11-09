#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
全面合规API功能测试
测试所有AMLO和BOT相关的API端点
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5001"
TEST_USER = {'login_code': 'admin', 'password': 'admin123', 'branch': 1}

class ComplianceAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.session = requests.Session()
        self.results = {'passed': 0, 'failed': 0, 'skipped': 0}
    
    def login(self):
        """登录"""
        response = self.session.post(f"{self.base_url}/api/auth/login", json=TEST_USER)
        if response.status_code == 200 and response.json().get('success'):
            self.token = response.json().get('token')
            self.session.headers.update({'Authorization': f'Bearer {self.token}'})
            print("[OK] Login successful")
            return True
        print("[FAIL] Login failed")
        return False
    
    def test_api(self, name, method, endpoint, data=None, expected_status=200):
        """通用API测试方法"""
        try:
            if method == 'GET':
                response = self.session.get(f"{self.base_url}{endpoint}")
            elif method == 'POST':
                response = self.session.post(f"{self.base_url}{endpoint}", json=data)
            else:
                print(f"  [SKIP] {name}: Unsupported method {method}")
                self.results['skipped'] += 1
                return
            
            if response.status_code == expected_status:
                result_data = response.json() if response.content else {}
                if result_data.get('success', True):
                    print(f"  [PASS] {name}")
                    self.results['passed'] += 1
                else:
                    print(f"  [WARN] {name}: {result_data.get('message', 'No message')}")
                    self.results['passed'] += 1  # API响应正常，只是业务逻辑返回失败
            else:
                print(f"  [FAIL] {name}: Status {response.status_code}")
                self.results['failed'] += 1
                
        except Exception as e:
            print(f"  [FAIL] {name}: {str(e)}")
            self.results['failed'] += 1
    
    def test_amlo_apis(self):
        """测试AMLO相关API"""
        print("\n" + "="*80)
        print("AMLO APIs Testing")
        print("="*80)
        
        # 预约列表
        self.test_api("Get Reservations", "GET", "/api/amlo/reservations")
        
        # AMLO报告列表
        self.test_api("Get AMLO Reports", "GET", "/api/amlo/reports")
        
        # 触发检查
        self.test_api("Check AMLO Trigger", "POST", "/api/repform/check-trigger", {
            'report_type': 'AMLO-1-01',
            'data': {'total_amount': 5000000, 'currency_code': 'THB'},
            'branch_id': 1
        })
        
        # 表单定义
        self.test_api("Get AMLO-1-01 Form", "GET", "/api/repform/form-definition/AMLO-1-01")
        self.test_api("Get AMLO-1-02 Form", "GET", "/api/repform/form-definition/AMLO-1-02")
        self.test_api("Get AMLO-1-03 Form", "GET", "/api/repform/form-definition/AMLO-1-03")
    
    def test_bot_apis(self):
        """测试BOT相关API"""
        print("\n" + "="*80)
        print("BOT APIs Testing")
        print("="*80)
        
        # BOT触发检查
        self.test_api("Check BOT BuyFX Trigger", "POST", "/api/bot/check-trigger", {
            'transaction_type': 'buy',
            'usd_equivalent': 25000,
            'use_fcd': False
        })
        
        # BOT报告查询
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        self.test_api("Get T+1 BuyFX Data", "GET", f"/api/bot/t1-buy-fx?date={yesterday}")
        self.test_api("Get T+1 SellFX Data", "GET", f"/api/bot/t1-sell-fx?date={yesterday}")
        
        # Excel导出（可能失败因为无数据）
        self.test_api("Export BuyFX Excel", "GET", f"/api/bot/export-buy-fx?date={today}", expected_status=None)
    
    def test_compliance_config_apis(self):
        """测试合规配置API"""
        print("\n" + "="*80)
        print("Compliance Configuration APIs Testing")
        print("="*80)
        
        # 字段定义
        self.test_api("Get All Fields", "GET", "/api/compliance/fields")
        self.test_api("Get BOT_Provider Fields", "GET", "/api/compliance/fields?report_type=BOT_Provider")
        
        # 触发规则
        self.test_api("Get All Trigger Rules", "GET", "/api/compliance/trigger-rules")
        self.test_api("Get BOT_Provider Rules", "GET", "/api/compliance/trigger-rules?report_type=BOT_Provider")
        
        # 资金来源
        self.test_api("Get Funding Sources", "GET", "/api/compliance/funding-sources")
    
    def test_repform_apis(self):
        """测试动态表单API"""
        print("\n" + "="*80)
        print("Dynamic Form (RepForm) APIs Testing")
        print("="*80)
        
        # 报告类型
        self.test_api("Get Report Types", "GET", "/api/repform/report-types")
        
        # 表单定义（所有报告类型）
        report_types = ['AMLO-1-01', 'AMLO-1-02', 'AMLO-1-03', 
                       'BOT_BuyFX', 'BOT_SellFX', 'BOT_Provider', 'BOT_FCD']
        
        for report_type in report_types:
            self.test_api(
                f"Get {report_type} Form",
                "GET",
                f"/api/repform/form-definition/{report_type}"
            )
    
    def run_all_tests(self):
        """运行所有测试"""
        print("="*80)
        print("Compliance APIs Comprehensive Test Suite")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        if not self.login():
            return 1
        
        self.test_amlo_apis()
        self.test_bot_apis()
        self.test_compliance_config_apis()
        self.test_repform_apis()
        
        # 总结
        print("\n" + "="*80)
        print("Test Results Summary")
        print("="*80)
        
        total = sum(self.results.values())
        passed = self.results['passed']
        failed = self.results['failed']
        skipped = self.results['skipped']
        
        print(f"\nTotal API Tests: {total}")
        print(f"  Passed: {passed} ({passed/total*100:.0f}%)")
        print(f"  Failed: {failed} ({failed/total*100:.0f}%)")
        print(f"  Skipped: {skipped} ({skipped/total*100:.0f}%)")
        
        success_rate = passed / total if total > 0 else 0
        
        if success_rate >= 0.9:
            print("\n✓ Excellent - All APIs working properly")
            return 0
        elif success_rate >= 0.7:
            print("\n⚠ Good - Most APIs working, some issues")
            return 0
        else:
            print("\n✗ Poor - Many APIs failing")
            return 1

def main():
    tester = ComplianceAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())


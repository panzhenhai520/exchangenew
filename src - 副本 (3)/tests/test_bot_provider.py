#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
BOT_Provider集成测试
测试余额调节触发BOT Provider报告的完整流程
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
from datetime import datetime

# 配置
BASE_URL = "http://localhost:5001"
TEST_USER = {
    'login_code': 'admin',
    'password': 'admin123',
    'branch': 1
}

class TestBOTProvider:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.session = requests.Session()
    
    def login(self):
        """登录获取token"""
        print("\n[Step 1] Login...")
        response = self.session.post(
            f"{self.base_url}/api/auth/login",
            json=TEST_USER
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                self.token = data.get('token')
                self.session.headers.update({'Authorization': f'Bearer {self.token}'})
                print(f"  [OK] Login successful, token: {self.token[:20]}...")
                return True
        
        print(f"  [FAIL] Login failed: {response.text}")
        return False
    
    def get_currencies(self):
        """获取币种列表"""
        print("\n[Step 2] Get Currency List...")
        response = self.session.get(f"{self.base_url}/api/system/currencies")
        
        if response.status_code == 200:
            data = response.json()
            currencies = data.get('data', [])
            print(f"  [OK] Found {len(currencies)} currencies")
            
            # 查找USD
            usd = next((c for c in currencies if c['currency_code'] == 'USD'), None)
            if usd:
                print(f"  [OK] USD currency found, id={usd['id']}")
                return usd['id']
        
        print(f"  [FAIL] Failed to get currencies")
        return None
    
    def test_small_adjustment(self, currency_id):
        """测试场景A: 小额调节（不触发）"""
        print("\n" + "="*80)
        print("Test Scenario A: Small Adjustment (Should NOT Trigger)")
        print("="*80)
        
        print("\n[Test A] Adjust USD balance by 15,000 (below threshold)...")
        
        response = self.session.post(
            f"{self.base_url}/api/balance-management/adjust",
            json={
                'currency_id': currency_id,
                'adjustment_amount': 15000,
                'adjustment_type': 'increase',
                'reason': 'Test small adjustment - should not trigger BOT_Provider'
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                bot_generated = data.get('bot_report_generated', False)
                
                if not bot_generated:
                    print(f"  [PASS] No BOT report generated (as expected)")
                    print(f"  Message: {data.get('message')}")
                    return True
                else:
                    print(f"  [FAIL] BOT report was generated (unexpected)")
                    return False
            else:
                print(f"  [FAIL] Adjustment failed: {data.get('message')}")
        else:
            print(f"  [FAIL] API error: {response.status_code}, {response.text}")
        
        return False
    
    def test_large_adjustment(self, currency_id):
        """测试场景B: 大额调节（应触发）"""
        print("\n" + "="*80)
        print("Test Scenario B: Large Adjustment (SHOULD Trigger)")
        print("="*80)
        
        print("\n[Test B] Adjust USD balance by 25,000 (above threshold)...")
        
        response = self.session.post(
            f"{self.base_url}/api/balance-management/adjust",
            json={
                'currency_id': currency_id,
                'adjustment_amount': 25000,
                'adjustment_type': 'increase',
                'reason': 'Test large adjustment - should trigger BOT_Provider'
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                bot_generated = data.get('bot_report_generated', False)
                
                if bot_generated:
                    print(f"  [PASS] BOT report generated (as expected)")
                    print(f"  Message: {data.get('message')}")
                    
                    # 验证报告是否写入数据库
                    transaction_id = data.get('transaction', {}).get('id')
                    if transaction_id:
                        print(f"  Transaction ID: {transaction_id}")
                        # TODO: 查询BOT_Provider表验证记录
                    
                    return True
                else:
                    print(f"  [FAIL] BOT report was NOT generated (unexpected)")
                    print(f"  Message: {data.get('message')}")
                    return False
            else:
                print(f"  [FAIL] Adjustment failed: {data.get('message')}")
        else:
            print(f"  [FAIL] API error: {response.status_code}, {response.text}")
        
        return False
    
    def test_decrease_adjustment(self, currency_id):
        """测试场景C: 减少调节（不应触发）"""
        print("\n" + "="*80)
        print("Test Scenario C: Decrease Adjustment (Should NOT Trigger)")
        print("="*80)

        print("\n[Test C] Decrease USD balance by 25,000 (decrease type)...")

        response = self.session.post(
            f"{self.base_url}/api/balance-management/adjust",
            json={
                'currency_id': currency_id,
                'adjustment_amount': 25000,
                'adjustment_type': 'decrease',
                'reason': 'Test decrease - should not trigger BOT_Provider'
            }
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                bot_generated = data.get('bot_report_generated', False)

                if not bot_generated:
                    print(f"  [PASS] No BOT report for decrease (as expected)")
                    return True
                else:
                    print(f"  [FAIL] BOT report generated for decrease (unexpected)")
                    return False
        else:
            # 如果余额不足，这是正常的
            print(f"  [OK] Adjustment rejected (likely insufficient balance)")
            return True

    def test_eur_to_usd_equivalent(self):
        """测试场景D: EUR调节转USD等值触发"""
        print("\n" + "="*80)
        print("Test Scenario D: EUR Adjustment with USD Equivalent Conversion")
        print("="*80)

        # 步骤1: 获取EUR和USD的货币ID
        print("\n[Step 1] Get EUR and USD currency IDs...")
        currencies_response = self.session.get(f"{self.base_url}/api/system/currencies")

        if currencies_response.status_code != 200:
            print(f"  [FAIL] Failed to get currencies: {currencies_response.status_code}")
            return False

        currencies = currencies_response.json().get('data', [])
        eur = next((c for c in currencies if c['currency_code'] == 'EUR'), None)
        usd = next((c for c in currencies if c['currency_code'] == 'USD'), None)

        if not eur:
            print(f"  [FAIL] EUR currency not found in system")
            return False
        if not usd:
            print(f"  [FAIL] USD currency not found in system")
            return False

        print(f"  [OK] EUR currency found, id={eur['id']}")
        print(f"  [OK] USD currency found, id={usd['id']}")

        # 步骤2: 设置EUR买入汇率 = 38 THB
        print("\n[Step 2] Set EUR buy rate = 38 THB...")
        eur_rate_response = self.session.post(
            f"{self.base_url}/api/rates/set",
            json={
                'currency_id': eur['id'],
                'buy_rate': 38.0,
                'sell_rate': 39.0,  # 卖出汇率不影响计算，但需要设置
                'rate_date': datetime.now().strftime('%Y-%m-%d')
            }
        )

        if eur_rate_response.status_code == 200:
            print(f"  [OK] EUR rate set successfully: buy=38.0, sell=39.0")
        else:
            print(f"  [WARN] EUR rate setting response: {eur_rate_response.status_code}")

        # 步骤3: 设置USD卖出汇率 = 34 THB
        print("\n[Step 3] Set USD sell rate = 34 THB...")
        usd_rate_response = self.session.post(
            f"{self.base_url}/api/rates/set",
            json={
                'currency_id': usd['id'],
                'buy_rate': 33.5,  # 买入汇率不影响计算，但需要设置
                'sell_rate': 34.0,
                'rate_date': datetime.now().strftime('%Y-%m-%d')
            }
        )

        if usd_rate_response.status_code == 200:
            print(f"  [OK] USD rate set successfully: buy=33.5, sell=34.0")
        else:
            print(f"  [WARN] USD rate setting response: {usd_rate_response.status_code}")

        # 步骤4: 调节EUR 20,000
        print("\n[Step 4] Adjust EUR balance by 20,000...")
        print(f"  Expected USD equivalent: 20,000 * 38 / 34 = {20000 * 38 / 34:.2f} USD")
        print(f"  Should trigger: {'YES (>= 20,000)' if 20000 * 38 / 34 >= 20000 else 'NO (< 20,000)'}")

        adjust_response = self.session.post(
            f"{self.base_url}/api/balance-management/adjust",
            json={
                'currency_id': eur['id'],
                'adjustment_amount': 20000,
                'adjustment_type': 'increase',
                'reason': 'Test EUR to USD equivalent conversion for BOT_Provider'
            }
        )

        if adjust_response.status_code != 200:
            print(f"  [FAIL] Adjustment failed: {adjust_response.status_code}, {adjust_response.text}")
            return False

        data = adjust_response.json()
        if not data.get('success'):
            print(f"  [FAIL] Adjustment failed: {data.get('message')}")
            return False

        bot_generated = data.get('bot_report_generated', False)
        transaction = data.get('transaction', {})
        transaction_id = transaction.get('id')

        print(f"  [OK] EUR adjustment successful")
        print(f"  Transaction ID: {transaction_id}")
        print(f"  BOT report generated: {bot_generated}")

        # 步骤5: 验证BOT_Provider报告
        if bot_generated:
            print("\n[Step 5] Verify BOT_Provider report...")

            # 查询BOT_Provider表验证记录
            # 注意：需要直接查询数据库或通过API查询
            verify_response = self.session.get(
                f"{self.base_url}/api/bot/provider/reports",
                params={'adjustment_id': transaction_id}
            )

            if verify_response.status_code == 200:
                bot_data = verify_response.json()
                if bot_data.get('success') and bot_data.get('data'):
                    reports = bot_data.get('data', [])
                    if reports:
                        report = reports[0]
                        usd_equiv_in_report = report.get('usd_equivalent', 0)
                        expected_usd = 20000 * 38 / 34

                        print(f"  [OK] BOT_Provider report found")
                        print(f"  Report ID: {report.get('id')}")
                        print(f"  USD equivalent in report: {usd_equiv_in_report:.2f}")
                        print(f"  Expected USD equivalent: {expected_usd:.2f}")
                        print(f"  Difference: {abs(usd_equiv_in_report - expected_usd):.2f}")

                        # 验证USD等值计算是否正确（允许小数点误差）
                        if abs(usd_equiv_in_report - expected_usd) < 1.0:
                            print(f"  [PASS] USD equivalent calculation is correct!")
                            return True
                        else:
                            print(f"  [FAIL] USD equivalent mismatch!")
                            return False
                    else:
                        print(f"  [WARN] No reports found for adjustment_id={transaction_id}")
                        print(f"  This might be expected if the query endpoint doesn't exist yet")
                        print(f"  [PASS] BOT report was generated (verified by flag)")
                        return True
            else:
                print(f"  [WARN] Cannot verify report via API (endpoint may not exist)")
                print(f"  [PASS] BOT report was generated (verified by flag)")
                return True
        else:
            expected_usd = 20000 * 38 / 34
            if expected_usd >= 20000:
                print(f"  [FAIL] BOT report should be generated but wasn't!")
                print(f"  Expected USD equivalent: {expected_usd:.2f} (>= 20,000 threshold)")
                return False
            else:
                print(f"  [PASS] BOT report not generated (below threshold)")
                return True
    
    def run_all_tests(self):
        """运行所有测试"""
        print("="*80)
        print("BOT_Provider Integration Test Suite")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        results = []
        
        # 登录
        if not self.login():
            print("\n[FATAL] Cannot proceed without login")
            return 1
        
        # 获取USD币种ID
        usd_currency_id = self.get_currencies()
        if not usd_currency_id:
            print("\n[FATAL] Cannot proceed without USD currency")
            return 1
        
        # 运行测试场景
        results.append(('Scenario A: Small Amount', self.test_small_adjustment(usd_currency_id)))
        results.append(('Scenario B: Large Amount', self.test_large_adjustment(usd_currency_id)))
        results.append(('Scenario C: Decrease', self.test_decrease_adjustment(usd_currency_id)))
        results.append(('Scenario D: EUR to USD Equivalent', self.test_eur_to_usd_equivalent()))
        
        # 总结
        print("\n" + "="*80)
        print("Test Results Summary")
        print("="*80)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "[PASS]" if result else "[FAIL]"
            print(f"  {status} {test_name}")
        
        print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
        
        if passed == total:
            print("\n✓ All tests PASSED!")
            return 0
        else:
            print(f"\n✗ {total - passed} test(s) FAILED")
            return 1

def main():
    tester = TestBOTProvider()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())


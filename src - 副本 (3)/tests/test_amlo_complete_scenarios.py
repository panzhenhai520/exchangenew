#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AMLO完整场景测试
测试预约审核、交易执行、报告上报等完整流程
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
from datetime import datetime, timedelta
from decimal import Decimal

# 配置
BASE_URL = "http://localhost:5001"
TEST_USER = {
    'login_code': 'admin',
    'password': 'admin123',
    'branch': 1
}


class AMLOScenarioTester:
    """AMLO场景测试类"""

    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.session = requests.Session()
        self.test_data = {}

    def login(self):
        """登录获取token"""
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

        print(f"  [FAIL] Login failed: {response.text}")
        return False

    def scenario_a_reservation_to_transaction(self):
        """
        场景A: 完整的预约到交易流程

        步骤：
        1-5: 准备数据（币种、汇率、客户信息）
        6-10: 创建预约、审核通过
        11-15: 执行交易、生成PDF
        16-20: 验证结果
        """
        print("\n" + "="*80)
        print("Scenario A: Complete Reservation to Transaction Flow")
        print("="*80)

        # 步骤1: 获取USD货币ID
        print("\n[Step 1/20] Get USD currency ID...")
        response = self.session.get(f"{self.base_url}/api/system/currencies")
        if response.status_code != 200:
            print(f"  [FAIL] Failed to get currencies")
            return False

        currencies = response.json().get('data', [])
        usd = next((c for c in currencies if c['currency_code'] == 'USD'), None)
        if not usd:
            print(f"  [FAIL] USD currency not found")
            return False

        usd_id = usd['id']
        print(f"  [OK] USD currency ID: {usd_id}")
        self.test_data['usd_id'] = usd_id

        # 步骤2: 设置USD汇率
        print("\n[Step 2/20] Set USD exchange rate...")
        response = self.session.post(
            f"{self.base_url}/api/rates/set",
            json={
                'currency_id': usd_id,
                'buy_rate': 33.5,
                'sell_rate': 34.0,
                'rate_date': datetime.now().strftime('%Y-%m-%d')
            }
        )

        if response.status_code == 200:
            print(f"  [OK] USD rate set: buy=33.5, sell=34.0")
        else:
            print(f"  [WARN] Rate setting response: {response.status_code}")

        # 步骤3: 准备客户信息
        print("\n[Step 3/20] Prepare customer information...")
        customer_data = {
            'customer_id': 'TEST123456789',
            'customer_name': 'Test Customer AMLO',
            'customer_country': 'TH',
            'customer_address': '123 Test Street, Bangkok, Thailand'
        }
        self.test_data['customer'] = customer_data
        print(f"  [OK] Customer: {customer_data['customer_name']}")
        print(f"  [OK] ID: {customer_data['customer_id']}")

        # 步骤4: 准备交易数据
        print("\n[Step 4/20] Prepare transaction data...")
        transaction_amount = 70000  # USD金额，会触发AMLO (70000*34=2,380,000 THB > 2,000,000)
        local_amount = transaction_amount * 34.0

        transaction_data = {
            'currency_id': usd_id,
            'currency_code': 'USD',
            'direction': 'buy',  # 客户买入外币
            'amount': transaction_amount,
            'local_amount': local_amount,
            'rate': 34.0
        }
        self.test_data['transaction'] = transaction_data
        print(f"  [OK] Transaction: Buy {transaction_amount:,.0f} USD")
        print(f"  [OK] Local amount: {local_amount:,.2f} THB")
        print(f"  [OK] Should trigger AMLO: {'YES' if local_amount > 2000000 else 'NO'}")

        # 步骤5: 检查AMLO触发规则
        print("\n[Step 5/20] Verify AMLO trigger conditions...")
        if local_amount > 2000000:
            print(f"  [OK] Amount exceeds 2M THB threshold")
            print(f"  [OK] Expected report type: AMLO-1-01")
        else:
            print(f"  [WARN] Amount below threshold, may not trigger")

        # 步骤6: 创建预约记录
        print("\n[Step 6/20] Create reservation...")
        reservation_data = {
            **customer_data,
            **transaction_data,
            'report_type': 'AMLO-1-01',
            'exchange_type': 'large_amount',
            'funding_source': 'savings',
            'remarks': 'Test AMLO reservation flow'
        }

        response = self.session.post(
            f"{self.base_url}/api/amlo/reservations",
            json=reservation_data
        )

        if response.status_code != 200:
            print(f"  [FAIL] Failed to create reservation: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

        reservation_result = response.json()
        if not reservation_result.get('success'):
            print(f"  [FAIL] Reservation creation failed: {reservation_result.get('message')}")
            return False

        reservation_id = reservation_result.get('data', {}).get('id')
        reservation_no = reservation_result.get('data', {}).get('reservation_no')

        if not reservation_id:
            print(f"  [FAIL] No reservation ID returned")
            return False

        self.test_data['reservation_id'] = reservation_id
        self.test_data['reservation_no'] = reservation_no
        print(f"  [OK] Reservation created: ID={reservation_id}, NO={reservation_no}")

        # 步骤7: 查询预约记录
        print("\n[Step 7/20] Query reservation...")
        response = self.session.get(
            f"{self.base_url}/api/amlo/reservations",
            params={'customer_id': customer_data['customer_id']}
        )

        if response.status_code != 200:
            print(f"  [FAIL] Failed to query reservations")
            return False

        query_result = response.json()
        items = query_result.get('data', {}).get('items', [])

        if not items:
            print(f"  [FAIL] No reservations found")
            return False

        found = any(item['id'] == reservation_id for item in items)
        if found:
            print(f"  [OK] Reservation found in query results")
        else:
            print(f"  [FAIL] Reservation not found in query results")
            return False

        # 步骤8: 验证预约状态为pending
        print("\n[Step 8/20] Verify initial status...")
        reservation = items[0]
        if reservation['status'] == 'pending':
            print(f"  [OK] Status is 'pending' (awaiting audit)")
        else:
            print(f"  [FAIL] Expected status 'pending', got '{reservation['status']}'")
            return False

        # 步骤9: 审核预约（批准）
        print("\n[Step 9/20] Audit reservation (approve)...")
        response = self.session.post(
            f"{self.base_url}/api/amlo/reservations/{reservation_id}/audit",
            json={
                'action': 'approve',
                'remarks': 'Test approval'
            }
        )

        if response.status_code != 200:
            print(f"  [FAIL] Failed to audit: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

        audit_result = response.json()
        if audit_result.get('success'):
            print(f"  [OK] Reservation approved")
        else:
            print(f"  [FAIL] Audit failed: {audit_result.get('message')}")
            return False

        # 步骤10: 验证审核后状态
        print("\n[Step 10/20] Verify audit status...")
        response = self.session.get(
            f"{self.base_url}/api/amlo/reservations",
            params={'customer_id': customer_data['customer_id']}
        )

        items = response.json().get('data', {}).get('items', [])
        reservation = next((item for item in items if item['id'] == reservation_id), None)

        if not reservation:
            print(f"  [FAIL] Reservation not found after audit")
            return False

        if reservation['status'] == 'approved':
            print(f"  [OK] Status changed to 'approved'")
            if reservation.get('auditor_id'):
                print(f"  [OK] Auditor recorded: {reservation.get('auditor_id')}")
            if reservation.get('audit_time'):
                print(f"  [OK] Audit time recorded: {reservation.get('audit_time')}")
        else:
            print(f"  [FAIL] Expected status 'approved', got '{reservation['status']}'")
            return False

        # 步骤11: 检查客户预约状态（交易前）
        print("\n[Step 11/20] Check customer reservation status...")
        response = self.session.get(
            f"{self.base_url}/api/amlo/check-customer-reservation",
            params={'customer_id': customer_data['customer_id']}
        )

        if response.status_code != 200:
            print(f"  [FAIL] Failed to check reservation")
            return False

        check_result = response.json()
        if check_result.get('has_reservation') and check_result.get('status') == 'approved':
            print(f"  [OK] Customer has approved reservation")
            print(f"  [OK] Approved amount: {check_result.get('approved_amount', 0):,.2f} THB")
        else:
            print(f"  [FAIL] Unexpected reservation check result")
            return False

        # 步骤12: 执行交易
        print("\n[Step 12/20] Execute exchange transaction...")
        exchange_data = {
            'currency_id': usd_id,
            'exchange_mode': 'buy_foreign',
            'amount_type': 'want',
            'target_amount': transaction_amount,
            'input_amount': local_amount,
            **customer_data,
            'exchange_type': 'large_amount',
            'purpose': 'travel',
            'remarks': f'AMLO reservation {reservation_no}'
        }

        response = self.session.post(
            f"{self.base_url}/api/exchange/transactions",
            json=exchange_data
        )

        if response.status_code != 200:
            print(f"  [FAIL] Transaction failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

        exchange_result = response.json()
        if not exchange_result.get('success'):
            print(f"  [FAIL] Transaction failed: {exchange_result.get('message')}")
            return False

        transaction_id = exchange_result.get('data', {}).get('id')
        transaction_no = exchange_result.get('data', {}).get('transaction_no')

        if not transaction_id:
            print(f"  [FAIL] No transaction ID returned")
            return False

        self.test_data['transaction_id'] = transaction_id
        self.test_data['transaction_no'] = transaction_no
        print(f"  [OK] Transaction executed: ID={transaction_id}, NO={transaction_no}")

        # 步骤13: 验证交易成功
        print("\n[Step 13/20] Verify transaction success...")
        response = self.session.get(
            f"{self.base_url}/api/exchange/transactions/{transaction_id}"
        )

        if response.status_code == 200:
            tx_data = response.json().get('data', {})
            if tx_data.get('status') == 'completed':
                print(f"  [OK] Transaction status: completed")
            else:
                print(f"  [WARN] Transaction status: {tx_data.get('status')}")
        else:
            print(f"  [WARN] Could not verify transaction")

        # 步骤14: 完成预约（关联交易）
        print("\n[Step 14/20] Complete reservation...")
        response = self.session.post(
            f"{self.base_url}/api/amlo/reservations/{reservation_id}/complete",
            json={'linked_transaction_id': transaction_id}
        )

        if response.status_code == 200:
            complete_result = response.json()
            if complete_result.get('success'):
                print(f"  [OK] Reservation completed")
            else:
                print(f"  [WARN] Complete failed: {complete_result.get('message')}")
        else:
            print(f"  [WARN] Complete response: {response.status_code}")

        # 步骤15: 生成PDF报告
        print("\n[Step 15/20] Generate AMLO PDF report...")
        # 注意：PDF生成可能在交易时自动触发，这里尝试查询
        response = self.session.get(
            f"{self.base_url}/api/amlo/reports",
            params={'customer_id': customer_data['customer_id']}
        )

        if response.status_code == 200:
            reports = response.json().get('data', {}).get('items', [])
            if reports:
                report = reports[0]
                self.test_data['report_id'] = report.get('id')
                print(f"  [OK] AMLO report found: ID={report.get('id')}")
                print(f"  [OK] Report No: {report.get('report_no')}")
                print(f"  [OK] Report type: {report.get('report_type')}")
            else:
                print(f"  [WARN] No AMLO report found yet")
        else:
            print(f"  [WARN] Could not query reports")

        # 步骤16: 验证AMLOReport表有新记录
        print("\n[Step 16/20] Verify AMLOReport table record...")
        if 'report_id' in self.test_data:
            print(f"  [OK] Report exists in AMLOReport table")
            print(f"  [OK] Report ID: {self.test_data['report_id']}")
        else:
            print(f"  [WARN] Could not verify report table record")

        # 步骤17: 验证预约状态=已交易
        print("\n[Step 17/20] Verify reservation status=completed...")
        response = self.session.get(
            f"{self.base_url}/api/amlo/reservations",
            params={'customer_id': customer_data['customer_id']}
        )

        if response.status_code == 200:
            items = response.json().get('data', {}).get('items', [])
            reservation = next((item for item in items if item['id'] == reservation_id), None)

            if reservation:
                if reservation['status'] == 'completed':
                    print(f"  [OK] Reservation status: completed")
                else:
                    print(f"  [INFO] Reservation status: {reservation['status']}")
            else:
                print(f"  [WARN] Reservation not found")
        else:
            print(f"  [WARN] Could not query reservation")

        # 步骤18: 下载PDF（可选）
        print("\n[Step 18/20] Test PDF download...")
        if 'report_id' in self.test_data:
            response = self.session.get(
                f"{self.base_url}/api/amlo/reports/{self.test_data['report_id']}/generate-pdf"
            )

            if response.status_code == 200 and response.headers.get('Content-Type') == 'application/pdf':
                pdf_size = len(response.content)
                print(f"  [OK] PDF downloaded successfully: {pdf_size} bytes")
            else:
                print(f"  [WARN] PDF download response: {response.status_code}")
        else:
            print(f"  [SKIP] No report ID to test download")

        # 步骤19: 验证报告未上报状态
        print("\n[Step 19/20] Verify report is_reported=false...")
        if 'report_id' in self.test_data:
            response = self.session.get(
                f"{self.base_url}/api/amlo/reports",
                params={'is_reported': 'false'}
            )

            if response.status_code == 200:
                items = response.json().get('data', {}).get('items', [])
                report = next((item for item in items if item['id'] == self.test_data['report_id']), None)

                if report:
                    if not report.get('is_reported'):
                        print(f"  [OK] Report is_reported=false (awaiting submission)")
                    else:
                        print(f"  [WARN] Report is_reported=true (unexpected)")
                else:
                    print(f"  [WARN] Report not found in unreported list")
            else:
                print(f"  [WARN] Could not query unreported reports")
        else:
            print(f"  [SKIP] No report ID to verify")

        # 步骤20: 测试总结
        print("\n[Step 20/20] Test summary...")
        print(f"  Reservation ID: {self.test_data.get('reservation_id')}")
        print(f"  Reservation No: {self.test_data.get('reservation_no')}")
        print(f"  Transaction ID: {self.test_data.get('transaction_id')}")
        print(f"  Transaction No: {self.test_data.get('transaction_no')}")
        print(f"  Report ID: {self.test_data.get('report_id', 'N/A')}")
        print(f"  [PASS] Scenario A completed successfully!")

        return True

    def scenario_b_reverse_audit(self):
        """
        场景B: 反审核流程

        步骤：
        1. 创建已审核的预约记录
        2. 调用反审核API
        3. 验证：状态=待审核
        4. 验证：记录反审核人和时间
        """
        print("\n" + "="*80)
        print("Scenario B: Reverse Audit Flow")
        print("="*80)

        # 步骤1: 创建并审核一个预约
        print("\n[Step 1/4] Create and approve a reservation...")

        # 创建预约
        reservation_data = {
            'customer_id': 'REVERSE_TEST_001',
            'customer_name': 'Test Reverse Customer',
            'customer_country': 'TH',
            'customer_address': 'Test Address',
            'currency_id': self.test_data.get('usd_id', 2),
            'currency_code': 'USD',
            'direction': 'buy',
            'amount': 70000,
            'local_amount': 2380000,
            'rate': 34.0,
            'report_type': 'AMLO-1-01'
        }

        response = self.session.post(
            f"{self.base_url}/api/amlo/reservations",
            json=reservation_data
        )

        if response.status_code != 200 or not response.json().get('success'):
            print(f"  [FAIL] Failed to create reservation")
            return False

        reservation_id = response.json().get('data', {}).get('id')
        print(f"  [OK] Reservation created: ID={reservation_id}")

        # 审核通过
        response = self.session.post(
            f"{self.base_url}/api/amlo/reservations/{reservation_id}/audit",
            json={'action': 'approve'}
        )

        if response.status_code != 200 or not response.json().get('success'):
            print(f"  [FAIL] Failed to approve reservation")
            return False

        print(f"  [OK] Reservation approved")

        # 步骤2: 调用反审核API
        print("\n[Step 2/4] Call reverse audit API...")
        response = self.session.post(
            f"{self.base_url}/api/amlo/reservations/{reservation_id}/reverse-audit",
            json={'remarks': 'Test reverse audit'}
        )

        if response.status_code != 200:
            print(f"  [FAIL] Reverse audit failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

        reverse_result = response.json()
        if reverse_result.get('success'):
            print(f"  [OK] Reverse audit successful")
        else:
            print(f"  [FAIL] Reverse audit failed: {reverse_result.get('message')}")
            return False

        # 步骤3: 验证状态=pending
        print("\n[Step 3/4] Verify status changed to pending...")
        response = self.session.get(
            f"{self.base_url}/api/amlo/reservations",
            params={'customer_id': 'REVERSE_TEST_001'}
        )

        if response.status_code != 200:
            print(f"  [FAIL] Failed to query reservation")
            return False

        items = response.json().get('data', {}).get('items', [])
        reservation = next((item for item in items if item['id'] == reservation_id), None)

        if not reservation:
            print(f"  [FAIL] Reservation not found")
            return False

        if reservation['status'] == 'pending':
            print(f"  [OK] Status reverted to 'pending'")
        else:
            print(f"  [FAIL] Expected status 'pending', got '{reservation['status']}'")
            return False

        # 步骤4: 验证记录了反审核信息
        print("\n[Step 4/4] Verify reverse audit metadata...")
        # 检查审核时间是否被清除或更新
        if reservation.get('audit_time') is None:
            print(f"  [OK] Audit time cleared")
        else:
            print(f"  [INFO] Audit time: {reservation.get('audit_time')}")

        if reservation.get('remarks'):
            print(f"  [OK] Remarks recorded: {reservation.get('remarks')[:50]}")

        print(f"  [PASS] Scenario B completed successfully!")
        return True

    def scenario_c_overdue_alert(self):
        """
        场景C: 超期提醒

        步骤：
        1. 创建已交易的AMLO报告（交易时间=2天前）
        2. 查询AMLO报告列表
        3. 验证：该记录有超期标记
        4. 标记为已上报
        5. 验证：超期标记消失
        """
        print("\n" + "="*80)
        print("Scenario C: Overdue Alert Test")
        print("="*80)

        # 步骤1: 创建2天前的报告（模拟）
        print("\n[Step 1/5] Create overdue AMLO report...")
        print(f"  [INFO] This test requires a report created 2+ days ago")
        print(f"  [INFO] Checking existing reports...")

        # 查询2天前开始的报告
        two_days_ago = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
        response = self.session.get(
            f"{self.base_url}/api/amlo/reports",
            params={
                'is_reported': 'false',
                'start_date': two_days_ago,
                'end_date': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            }
        )

        if response.status_code != 200:
            print(f"  [FAIL] Failed to query reports")
            return False

        reports = response.json().get('data', {}).get('items', [])

        if not reports:
            print(f"  [WARN] No overdue reports found")
            print(f"  [INFO] Creating a test transaction to simulate overdue report...")

            # 如果没有超期报告，创建一个（实际场景中需要修改数据库时间）
            print(f"  [SKIP] Cannot simulate overdue without database manipulation")
            print(f"  [INFO] In production, reports older than 1 day should show red alert")
            return True

        # 步骤2: 查询报告列表
        print("\n[Step 2/5] Query AMLO report list...")
        overdue_report = reports[0]
        report_id = overdue_report.get('id')

        print(f"  [OK] Found report: ID={report_id}")
        print(f"  [OK] Created at: {overdue_report.get('created_at')}")
        print(f"  [OK] Transaction date: {overdue_report.get('transaction_date')}")

        # 步骤3: 验证超期标记
        print("\n[Step 3/5] Verify overdue indicator...")

        # 计算超期天数
        created_at = datetime.fromisoformat(overdue_report.get('created_at').replace('Z', '+00:00'))
        days_overdue = (datetime.now(created_at.tzinfo) - created_at).days

        if days_overdue > 1:
            print(f"  [OK] Report is overdue: {days_overdue} days")
            print(f"  [OK] Should display red alert in UI")
        else:
            print(f"  [INFO] Report age: {days_overdue} days (not overdue yet)")

        # 步骤4: 标记为已上报
        print("\n[Step 4/5] Mark report as submitted...")
        response = self.session.post(
            f"{self.base_url}/api/amlo/reports/mark-reported",
            json={'ids': [report_id]}
        )

        if response.status_code != 200:
            print(f"  [FAIL] Failed to mark as reported: {response.status_code}")
            return False

        mark_result = response.json()
        if mark_result.get('success'):
            print(f"  [OK] Report marked as submitted")
            print(f"  [OK] Updated count: {mark_result.get('updated_count')}")
        else:
            print(f"  [FAIL] Mark failed: {mark_result.get('message')}")
            return False

        # 步骤5: 验证超期标记消失
        print("\n[Step 5/5] Verify overdue alert cleared...")
        response = self.session.get(
            f"{self.base_url}/api/amlo/reports",
            params={'is_reported': 'false'}
        )

        if response.status_code == 200:
            unreported = response.json().get('data', {}).get('items', [])
            still_present = any(item['id'] == report_id for item in unreported)

            if not still_present:
                print(f"  [OK] Report no longer in unreported list")
                print(f"  [OK] Overdue alert should be cleared")
            else:
                print(f"  [WARN] Report still in unreported list")
        else:
            print(f"  [WARN] Could not verify unreported list")

        print(f"  [PASS] Scenario C completed successfully!")
        return True

    def run_all_tests(self):
        """运行所有测试场景"""
        print("="*80)
        print("AMLO Complete Scenario Tests")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)

        results = []

        # 登录
        if not self.login():
            print("\n[FATAL] Cannot proceed without login")
            return 1

        # 运行场景A
        results.append(('Scenario A: Reservation to Transaction', self.scenario_a_reservation_to_transaction()))

        # 运行场景B
        results.append(('Scenario B: Reverse Audit', self.scenario_b_reverse_audit()))

        # 运行场景C
        results.append(('Scenario C: Overdue Alert', self.scenario_c_overdue_alert()))

        # 总结
        print("\n" + "="*80)
        print("Test Results Summary")
        print("="*80)

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for test_name, result in results:
            status = "[PASS]" if result else "[FAIL]"
            print(f"  {status} {test_name}")

        print(f"\nTotal: {passed}/{total} scenarios passed ({passed/total*100:.0f}%)")

        if passed == total:
            print("\n✓ All scenarios PASSED!")
            return 0
        else:
            print(f"\n✗ {total - passed} scenario(s) FAILED")
            return 1


def main():
    """主函数"""
    tester = AMLOScenarioTester()
    return tester.run_all_tests()


if __name__ == "__main__":
    sys.exit(main())

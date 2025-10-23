# -*- coding: utf-8 -*-
"""
测试带认证的AMLO触发API
模拟真实前端请求
"""

import requests
import json

def get_auth_token():
    """获取认证token"""
    login_url = "http://localhost:5001/api/auth/login"
    login_data = {
        "username": "admin",
        "password": "admin123"
    }

    try:
        response = requests.post(login_url, json=login_data)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data.get('access_token')
        print(f"[ERROR] Login failed: {response.status_code} - {response.text}")
        return None
    except Exception as e:
        print(f"[ERROR] Login exception: {str(e)}")
        return None

def test_trigger_with_auth():
    print("=" * 80)
    print("[测试] 带认证的AMLO触发API测试")
    print("=" * 80)

    # 步骤1: 获取认证token
    print("\n[步骤1] 获取认证token...")
    token = get_auth_token()

    if not token:
        print("[FAIL] 无法获取认证token，测试终止")
        return

    print(f"[OK] 获取到token: {token[:20]}...")

    # 步骤2: 测试场景1 - 5,844,600 THB (应该触发)
    print("\n[步骤2] 测试场景1: 180,000 USD = 5,844,600 THB")
    print("-" * 80)

    trigger_url = "http://localhost:5001/api/repform/check-trigger"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    data1 = {
        "report_type": "AMLO-1-01",
        "data": {
            "customer_id": "1234567890123",
            "customer_name": "Test Customer",
            "customer_country": "TH",
            "transaction_type": "exchange",
            "transaction_amount_thb": 5844600,
            "total_amount": 5844600,
            "payment_method": "cash",
            "customer_age": None,
            "exchange_type": "normal"
        },
        "branch_id": 1
    }

    print(f"Request URL: {trigger_url}")
    print(f"Request Data:")
    print(json.dumps(data1, indent=2, ensure_ascii=False))

    try:
        response1 = requests.post(trigger_url, json=data1, headers=headers)
        print(f"\nResponse Status: {response1.status_code}")
        print(f"Response Data:")
        print(json.dumps(response1.json(), indent=2, ensure_ascii=False))

        if response1.status_code == 200:
            result = response1.json()
            if result.get('success'):
                if result.get('triggers', {}).get('amlo', {}).get('triggered'):
                    print("\n[OK] AMLO触发成功")
                    print(f"    触发规则: {result['triggers']['amlo'].get('report_type')}")
                    print(f"    触发消息: {result['triggers']['amlo'].get('message_cn')}")
                else:
                    print("\n[FAIL] AMLO应该触发但没有触发")
            else:
                print(f"\n[FAIL] API返回失败: {result.get('message')}")
        else:
            print(f"\n[FAIL] API返回错误状态码: {response1.status_code}")
    except Exception as e:
        print(f"\n[FAIL] 请求失败: {str(e)}")

    # 步骤3: 测试场景2 - 3,243,753 THB (应该触发高风险规则)
    print("\n\n[步骤3] 测试场景2: 99,900 USD = 3,243,753 THB (现金支付)")
    print("-" * 80)

    data2 = {
        "report_type": "AMLO-1-01",
        "data": {
            "customer_id": "1234567890123",
            "customer_name": "Test Customer",
            "customer_country": "TH",
            "transaction_type": "exchange",
            "transaction_amount_thb": 3243753,
            "total_amount": 3243753,
            "payment_method": "cash",
            "customer_age": None,
            "exchange_type": "normal"
        },
        "branch_id": 1
    }

    print(f"Request Data:")
    print(json.dumps(data2, indent=2, ensure_ascii=False))

    try:
        response2 = requests.post(trigger_url, json=data2, headers=headers)
        print(f"\nResponse Status: {response2.status_code}")
        print(f"Response Data:")
        print(json.dumps(response2.json(), indent=2, ensure_ascii=False))

        if response2.status_code == 200:
            result = response2.json()
            if result.get('success'):
                if result.get('triggers', {}).get('amlo', {}).get('triggered'):
                    print("\n[OK] AMLO触发成功 (高风险规则: 金额>=1,500,000 + 现金支付)")
                    print(f"    触发规则: {result['triggers']['amlo'].get('report_type')}")
                    print(f"    触发消息: {result['triggers']['amlo'].get('message_cn')}")
                else:
                    print("\n[INFO] AMLO未触发 (预期，因为金额 < 5,000,000)")
            else:
                print(f"\n[FAIL] API返回失败: {result.get('message')}")
        else:
            print(f"\n[FAIL] API返回错误状态码: {response2.status_code}")
    except Exception as e:
        print(f"\n[FAIL] 请求失败: {str(e)}")

    # 步骤4: 测试场景3 - 1,000,000 THB 非现金 (不应该触发)
    print("\n\n[步骤4] 测试场景3: 1,000,000 THB (银行转账，不应该触发)")
    print("-" * 80)

    data3 = {
        "report_type": "AMLO-1-01",
        "data": {
            "customer_id": "1234567890123",
            "customer_name": "Test Customer",
            "customer_country": "TH",
            "transaction_type": "exchange",
            "transaction_amount_thb": 1000000,
            "total_amount": 1000000,
            "payment_method": "bank_transfer",
            "customer_age": None,
            "exchange_type": "normal"
        },
        "branch_id": 1
    }

    print(f"Request Data:")
    print(json.dumps(data3, indent=2, ensure_ascii=False))

    try:
        response3 = requests.post(trigger_url, json=data3, headers=headers)
        print(f"\nResponse Status: {response3.status_code}")
        print(f"Response Data:")
        print(json.dumps(response3.json(), indent=2, ensure_ascii=False))

        if response3.status_code == 200:
            result = response3.json()
            if result.get('success'):
                if not result.get('triggers', {}).get('amlo', {}).get('triggered'):
                    print("\n[OK] AMLO未触发 (正确，金额不足且非现金)")
                else:
                    print("\n[FAIL] AMLO不应该触发但触发了")
                    print(f"    触发规则: {result['triggers']['amlo'].get('report_type')}")
            else:
                print(f"\n[FAIL] API返回失败: {result.get('message')}")
        else:
            print(f"\n[FAIL] API返回错误状态码: {response3.status_code}")
    except Exception as e:
        print(f"\n[FAIL] 请求失败: {str(e)}")

if __name__ == '__main__':
    test_trigger_with_auth()

# -*- coding: utf-8 -*-
"""
测试前端调用的AMLO触发检查API
模拟前端发送的请求，查看后端响应
"""

import requests
import json

def test_trigger_api():
    print("=" * 80)
    print("测试前端触发检查API")
    print("=" * 80)

    # 测试场景1: 180,000 USD = 5,844,600 THB
    print("\n[测试1] 180,000 USD = 5,844,600 THB (应该触发AMLO-1-01)")
    print("-" * 80)

    url = "http://localhost:5001/repform/check-trigger"

    # 模拟前端发送的数据
    data = {
        "report_type": "AMLO-1-01",
        "data": {
            "customer_id": "1234567890123",
            "customer_name": "测试客户",
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

    print(f"请求URL: {url}")
    print(f"请求数据:")
    print(json.dumps(data, indent=2, ensure_ascii=False))

    try:
        response = requests.post(url, json=data)
        print(f"\n响应状态码: {response.status_code}")
        print(f"响应数据:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))

        if response.json().get('success'):
            if response.json().get('triggers', {}).get('amlo', {}).get('triggered'):
                print("\n✓ AMLO触发检查正常 - 已触发")
            else:
                print("\n✗ AMLO触发检查异常 - 应该触发但没有触发")
        else:
            print(f"\n✗ API调用失败: {response.json().get('message')}")

    except requests.exceptions.ConnectionError:
        print("\n✗ 无法连接到后端服务 (http://localhost:5001)")
        print("请确保后端服务正在运行: python src/main.py")
    except Exception as e:
        print(f"\n✗ 请求失败: {str(e)}")

    # 测试场景2: 99,900 USD = 3,243,753 THB
    print("\n\n[测试2] 99,900 USD = 3,243,753 THB (不应该触发)")
    print("-" * 80)

    data2 = {
        "report_type": "AMLO-1-01",
        "data": {
            "customer_id": "1234567890123",
            "customer_name": "测试客户",
            "customer_country": "TH",
            "transaction_type": "exchange",
            "transaction_amount_thb": 3243753,
            "total_amount": 3243753,
            "payment_method": "cash"
        },
        "branch_id": 1
    }

    print(f"请求数据:")
    print(json.dumps(data2, indent=2, ensure_ascii=False))

    try:
        response2 = requests.post(url, json=data2)
        print(f"\n响应状态码: {response2.status_code}")
        print(f"响应数据:")
        print(json.dumps(response2.json(), indent=2, ensure_ascii=False))

        if response2.json().get('success'):
            if not response2.json().get('triggers', {}).get('amlo', {}).get('triggered'):
                print("\n✓ AMLO触发检查正常 - 未触发（正确）")
            else:
                print("\n✗ AMLO触发检查异常 - 不应该触发但触发了")
    except Exception as e:
        print(f"\n✗ 请求失败: {str(e)}")

if __name__ == '__main__':
    test_trigger_api()

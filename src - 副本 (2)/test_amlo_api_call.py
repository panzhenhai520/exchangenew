#!/usr/bin/env python3
"""
测试AMLO触发检查API调用
"""
import requests
import json

def test_amlo_api():
    print("=== 测试AMLO触发检查API ===")
    
    # 测试数据
    test_data = {
        'report_type': 'AMLO-1-01',
        'data': {
            'customer_id': '1233123',
            'customer_name': 'Panython',
            'customer_country': 'BD',
            'transaction_type': 'exchange',
            'transaction_amount_thb': 44600000,
            'total_amount': 44600000,
            'payment_method': 'cash'
        },
        'branch_id': 1
    }
    
    print(f"测试数据: {test_data}")
    
    try:
        # 模拟前端API调用
        url = 'http://localhost:5001/api/repform/check-trigger'
        headers = {'Content-Type': 'application/json'}
        
        print(f"\n发送请求到: {url}")
        response = requests.post(url, json=test_data, headers=headers)
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n解析后的响应:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            if data.get('success') and data.get('triggers', {}).get('amlo', {}).get('triggered'):
                print("\n[SUCCESS] AMLO触发检查成功，应该弹出预约表单！")
            else:
                print("\n[FAILED] AMLO触发检查失败或未触发")
        else:
            print(f"\n[ERROR] API调用失败，状态码: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] 无法连接到后端服务，请确保后端服务正在运行")
    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")

if __name__ == "__main__":
    test_amlo_api()

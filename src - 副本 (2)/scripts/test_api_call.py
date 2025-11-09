#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试API调用
直接调用/rates/all API，检查返回的数据格式
"""

import requests
import json

def test_api_call():
    """测试API调用"""
    print("=== 测试API调用 ===")
    
    # API基础URL
    base_url = "http://localhost:5001"
    
    # 测试1：获取汇率数据
    print(f"\n=== 测试1：获取汇率数据 ===")
    try:
        # 注意：这里需要有效的认证token，我们先测试无认证的情况
        response = requests.get(f"{base_url}/api/rates/all", timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"错误响应: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败：请确保服务器正在运行")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # 测试2：检查服务器状态
    print(f"\n=== 测试2：检查服务器状态 ===")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"服务器状态: {response.status_code}")
    except Exception as e:
        print(f"❌ 服务器连接失败: {e}")

def test_frontend_data():
    """测试前端数据处理"""
    print(f"\n=== 测试前端数据处理 ===")
    
    # 模拟API返回的数据结构
    mock_data = {
        "success": True,
        "rates": [
            {
                "id": 1,
                "currency_id": 2,
                "currency_code": "USD",
                "currency_name": "美元",
                "buy_rate": 30.54,
                "sell_rate": 33.97,
                "is_published": True
            },
            {
                "id": 2,
                "currency_id": 3,
                "currency_code": "EUR",
                "currency_name": "欧元",
                "buy_rate": 0.0,
                "sell_rate": 0.0,
                "is_published": False
            }
        ]
    }
    
    print(f"模拟数据: {json.dumps(mock_data, indent=2, ensure_ascii=False)}")
    
    # 模拟前端处理逻辑
    if mock_data.get('success') and mock_data.get('rates'):
        rates = mock_data['rates']
        print(f"✅ 成功解析到 {len(rates)} 条汇率记录")
        
        for rate in rates:
            print(f"   - {rate['currency_code']}: 买入={rate['buy_rate']}, 卖出={rate['sell_rate']}")
    else:
        print(f"❌ 数据格式不正确")

def main():
    """主函数"""
    print("=== API调用测试 ===")
    
    # 测试API调用
    test_api_call()
    
    # 测试前端数据处理
    test_frontend_data()
    
    print(f"\n=== 建议 ===")
    print(f"1. 检查服务器是否正在运行 (python main.py)")
    print(f"2. 检查浏览器控制台是否有错误信息")
    print(f"3. 检查网络请求是否成功")
    print(f"4. 检查API返回的数据格式")

if __name__ == "__main__":
    main() 
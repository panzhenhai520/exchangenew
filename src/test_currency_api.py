#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试货币API端点
"""

import sys
import os
import io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure stdout/stderr encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import requests
import json

BASE_URL = "http://localhost:5001"

def test_currency_api():
    """测试货币API"""
    print("=" * 80)
    print("测试货币API端点")
    print("=" * 80)

    # 步骤1: 登录获取token
    print("\n[步骤1] 登录...")
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={
            'login_code': 'admin',
            'password': 'admin123',
            'branch': 1
        }
    )

    if response.status_code != 200:
        print(f"❌ 登录失败: {response.status_code}")
        print(f"Response: {response.text}")
        return False

    data = response.json()
    if not data.get('success'):
        print(f"❌ 登录失败: {data.get('message')}")
        return False

    token = data.get('token')
    print(f"✅ 登录成功")
    print(f"Token: {token[:50]}...")

    # 步骤2: 查询货币
    print("\n[步骤2] 查询货币...")
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(
        f"{BASE_URL}/api/system/currencies",
        headers=headers
    )

    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")

    if response.status_code != 200:
        print(f"❌ 查询失败")
        print(f"Response: {response.text}")
        return False

    result = response.json()
    print(f"✅ 查询成功")
    print(f"Response structure: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}")

    # 步骤3: 检查USD和EUR
    print("\n[步骤3] 检查USD和EUR...")
    currencies = result.get('data', [])

    if not isinstance(currencies, list):
        print(f"❌ 响应数据格式错误: 期望列表，得到 {type(currencies)}")
        print(f"Data: {currencies}")
        return False

    print(f"货币数量: {len(currencies)}")

    usd = next((c for c in currencies if c.get('currency_code') == 'USD'), None)
    eur = next((c for c in currencies if c.get('currency_code') == 'EUR'), None)
    thb = next((c for c in currencies if c.get('currency_code') == 'THB'), None)

    print("\n查找结果:")
    if usd:
        print(f"✅ USD找到: ID={usd.get('id')}, Name={usd.get('currency_name')}")
    else:
        print(f"❌ USD未找到")

    if eur:
        print(f"✅ EUR找到: ID={eur.get('id')}, Name={eur.get('currency_name')}")
    else:
        print(f"❌ EUR未找到")

    if thb:
        print(f"✅ THB找到: ID={thb.get('id')}, Name={thb.get('currency_name')}")
    else:
        print(f"❌ THB未找到")

    # 打印前5个货币
    print("\n前5个货币:")
    for i, currency in enumerate(currencies[:5]):
        print(f"  {i+1}. {currency.get('currency_code')}: {currency.get('currency_name')} (ID={currency.get('id')})")

    return True

if __name__ == '__main__':
    test_currency_api()

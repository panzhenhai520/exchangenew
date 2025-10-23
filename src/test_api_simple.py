#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_report_number_api():
    """测试报告编号生成API"""
    base_url = "http://localhost:5001/api"
    
    # 测试健康检查
    try:
        response = requests.get(f"{base_url.replace('/api', '')}/health")
        print(f"健康检查: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"健康检查失败: {e}")
        return
    
    # 测试AMLO报告编号生成（需要认证，这里只是测试连接）
    try:
        response = requests.post(
            f"{base_url}/report-numbers/amlo/generate",
            json={"currency_code": "USD"},
            headers={"Content-Type": "application/json"}
        )
        print(f"AMLO API测试: {response.status_code}")
        if response.status_code != 200:
            print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"AMLO API测试失败: {e}")
    
    # 测试BOT报告编号生成
    try:
        response = requests.post(
            f"{base_url}/report-numbers/bot/generate",
            json={"report_type": "BuyFX"},
            headers={"Content-Type": "application/json"}
        )
        print(f"BOT API测试: {response.status_code}")
        if response.status_code != 200:
            print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"BOT API测试失败: {e}")

if __name__ == '__main__':
    test_report_number_api()




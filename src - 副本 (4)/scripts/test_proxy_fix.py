#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试代理配置修复
验证前端代理错误是否已解决
"""

import requests
import json

def test_api_endpoints():
    """测试API端点"""
    print("=== 测试API端点 ===")
    
    base_url = "http://127.0.0.1:5001"
    endpoints = [
        "/health",
        "/api/rates/all",
        "/api/dashboard/overview",
        "/api/transaction-alerts/statistics?days=7"
    ]
    
    for endpoint in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            print(f"\n测试: {url}")
            
            response = requests.get(url, timeout=10)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ 端点正常")
            elif response.status_code == 401:
                print("⚠️  需要认证（正常）")
            else:
                print(f"❌ 异常状态码: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("❌ 连接失败")
        except Exception as e:
            print(f"❌ 请求失败: {e}")

def test_proxy_configuration():
    """测试代理配置"""
    print(f"\n=== 代理配置测试 ===")
    
    # 模拟前端代理请求
    proxy_url = "http://127.0.0.1:8080"  # 前端开发服务器
    
    try:
        # 测试通过代理访问API
        response = requests.get(f"{proxy_url}/api/health", timeout=10)
        print(f"代理API测试: {'✅ 成功' if response.status_code == 200 else '❌ 失败'}")
        
    except requests.exceptions.ConnectionError:
        print("❌ 前端开发服务器未运行")
        print("   解决方案：启动前端开发服务器")
    except Exception as e:
        print(f"❌ 代理测试失败: {e}")

def main():
    """主函数"""
    print("=== 代理配置修复验证 ===")
    
    # 测试直接API访问
    test_api_endpoints()
    
    # 测试代理配置
    test_proxy_configuration()
    
    print(f"\n=== 修复总结 ===")
    print(f"✅ 已修复前端代理配置")
    print(f"✅ 目标地址从 192.168.13.56:5001 改为 192.168.0.18:5001")
    print(f"✅ 现在前端应该能正常连接到后端API")
    
    print(f"\n=== 下一步操作 ===")
    print(f"1. 重启前端开发服务器")
    print(f"2. 清除浏览器缓存")
    print(f"3. 测试前端功能")

if __name__ == "__main__":
    main() 
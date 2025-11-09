#!/usr/bin/env python3
"""
检查用户登录状态和token
"""
import requests
import json

def check_login_status():
    print("=== 检查用户登录状态 ===")
    
    # 检查本地存储的token（模拟前端）
    try:
        # 这里我们需要检查前端是否存储了token
        # 由于无法直接访问localStorage，我们测试一个需要认证的API
        
        # 测试用户信息API
        url = 'http://localhost:5001/api/auth/user'
        
        print(f"测试API: {url}")
        
        # 不提供token，看是否返回401
        response = requests.get(url)
        print(f"无token响应状态码: {response.status_code}")
        print(f"无token响应内容: {response.text}")
        
        if response.status_code == 401:
            print("\n[INFO] 后端认证正常工作，需要有效token")
            print("[INFO] 前端可能没有有效的登录token")
            print("[SOLUTION] 请重新登录系统")
        else:
            print(f"\n[WARNING] 意外的响应状态码: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] 无法连接到后端服务")
        print("[SOLUTION] 请确保后端服务正在运行")
    except Exception as e:
        print(f"\n[ERROR] 检查失败: {e}")

if __name__ == "__main__":
    check_login_status()

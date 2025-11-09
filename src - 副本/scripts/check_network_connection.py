#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
检查网络连接问题
诊断前端代理错误的原因
"""

import socket
import requests
import subprocess
import platform
import os

def check_port_connection(host, port):
    """检查端口连接"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"❌ 连接检查失败: {e}")
        return False

def check_http_response(host, port):
    """检查HTTP响应"""
    try:
        url = f"http://{host}:{port}/health"
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False
    except Exception as e:
        print(f"❌ HTTP请求失败: {e}")
        return False

def check_process_running(port):
    """检查端口是否有进程在监听"""
    try:
        if platform.system() == "Windows":
            # Windows命令
            cmd = f"netstat -an | findstr :{port}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.returncode == 0 and str(port) in result.stdout
        else:
            # Linux/Mac命令
            cmd = f"lsof -i :{port}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.returncode == 0
    except Exception as e:
        print(f"❌ 进程检查失败: {e}")
        return False

def main():
    """主函数"""
    print("=== 网络连接诊断 ===")
    
    # 配置
    target_host = "192.168.0.18"
    target_port = 5001
    localhost = "127.0.0.1"
    
    print(f"\n=== 1. 检查目标服务器连接 ===")
    print(f"目标: {target_host}:{target_port}")
    
    # 检查端口连接
    port_accessible = check_port_connection(target_host, target_port)
    print(f"端口连接: {'✅ 可访问' if port_accessible else '❌ 不可访问'}")
    
    # 检查HTTP响应
    http_accessible = check_http_response(target_host, target_port)
    print(f"HTTP响应: {'✅ 正常' if http_accessible else '❌ 无响应'}")
    
    print(f"\n=== 2. 检查本地服务器 ===")
    print(f"目标: {localhost}:{target_port}")
    
    # 检查本地端口连接
    local_port_accessible = check_port_connection(localhost, target_port)
    print(f"本地端口连接: {'✅ 可访问' if local_port_accessible else '❌ 不可访问'}")
    
    # 检查本地HTTP响应
    local_http_accessible = check_http_response(localhost, target_port)
    print(f"本地HTTP响应: {'✅ 正常' if local_http_accessible else '❌ 无响应'}")
    
    print(f"\n=== 3. 检查进程状态 ===")
    
    # 检查端口是否有进程监听
    process_running = check_process_running(target_port)
    print(f"端口 {target_port} 进程: {'✅ 有进程监听' if process_running else '❌ 无进程监听'}")
    
    print(f"\n=== 4. 问题分析 ===")
    
    if not process_running:
        print(f"❌ 问题：端口 {target_port} 没有进程监听")
        print(f"   解决方案：启动后端服务器 (python main.py)")
    elif not local_port_accessible:
        print(f"❌ 问题：本地端口 {target_port} 不可访问")
        print(f"   可能原因：服务器配置问题")
    elif not port_accessible:
        print(f"❌ 问题：远程主机 {target_host} 端口 {target_port} 不可访问")
        print(f"   可能原因：")
        print(f"   1. 防火墙阻止了连接")
        print(f"   2. 网络配置问题")
        print(f"   3. 服务器只监听本地地址")
    elif not http_accessible:
        print(f"❌ 问题：HTTP服务无响应")
        print(f"   可能原因：服务器启动异常")
    else:
        print(f"✅ 网络连接正常")
    
    print(f"\n=== 5. 建议解决方案 ===")
    
    if not process_running:
        print(f"1. 启动后端服务器：")
        print(f"   cd src")
        print(f"   python main.py")
    elif not port_accessible:
        print(f"1. 检查防火墙设置")
        print(f"2. 确认服务器监听地址：")
        print(f"   - 当前配置：host='0.0.0.0'")
        print(f"   - 应该监听所有接口")
        print(f"3. 检查网络配置")
    else:
        print(f"1. 检查前端代理配置")
        print(f"2. 确认前端开发服务器正在运行")
        print(f"3. 检查浏览器控制台错误")

if __name__ == "__main__":
    main() 
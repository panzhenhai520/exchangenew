#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from dotenv import load_dotenv

print("=== 环境变量测试 ===")
print(f"Python版本: {sys.version}")
print(f"当前工作目录: {os.getcwd()}")

# 测试环境变量
print(f"\n=== 环境变量 ===")
print(f"CURRENT_IP: {os.getenv('CURRENT_IP', '未设置')}")
print(f"BACKEND_PORT: {os.getenv('BACKEND_PORT', '未设置')}")
print(f"FRONTEND_PORT: {os.getenv('FRONTEND_PORT', '未设置')}")

# 测试.env文件加载
print(f"\n=== .env文件测试 ===")
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
print(f".env文件路径: {dotenv_path}")
print(f".env文件存在: {os.path.exists(dotenv_path)}")

if os.path.exists(dotenv_path):
    print("尝试加载.env文件...")
    load_dotenv(dotenv_path)
    print(f"加载后 CURRENT_IP: {os.getenv('CURRENT_IP', '未设置')}")
    print(f"加载后 BACKEND_PORT: {os.getenv('BACKEND_PORT', '未设置')}")
    print(f"加载后 FRONTEND_PORT: {os.getenv('FRONTEND_PORT', '未设置')}")
else:
    print("❌ .env文件不存在")

# 测试所有环境变量
print(f"\n=== 所有环境变量 ===")
for key, value in os.environ.items():
    if 'IP' in key or 'PORT' in key or 'URL' in key:
        print(f"{key}: {value}")




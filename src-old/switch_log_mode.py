#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日志模式切换脚本
用于快速切换调试模式和生产模式
"""

import os
import sys

def switch_to_debug_mode():
    """切换到调试模式"""
    os.environ['LOG_MODE'] = 'debug'
    print("🔍 已切换到调试模式")
    print("📝 日志级别: DEBUG")
    print("💻 控制台级别: INFO")
    print("📄 文件级别: DEBUG")

def switch_to_production_mode():
    """切换到生产模式"""
    os.environ['LOG_MODE'] = 'production'
    print("🚀 已切换到生产模式")
    print("📝 日志级别: INFO")
    print("💻 控制台级别: WARNING")
    print("📄 文件级别: INFO")

def show_current_mode():
    """显示当前模式"""
    current_mode = os.getenv('LOG_MODE', 'debug')
    print(f"📊 当前日志模式: {current_mode.upper()}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python switch_log_mode.py debug    # 切换到调试模式")
        print("  python switch_log_mode.py production # 切换到生产模式")
        print("  python switch_log_mode.py status   # 显示当前模式")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'debug':
        switch_to_debug_mode()
    elif command == 'production':
        switch_to_production_mode()
    elif command == 'status':
        show_current_mode()
    else:
        print(f"❌ 未知命令: {command}")
        print("支持的命令: debug, production, status")
        sys.exit(1) 
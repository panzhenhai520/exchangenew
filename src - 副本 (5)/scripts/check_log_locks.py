#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日志文件占用检测和解决脚本
用于检测和解决Windows日志文件占用问题
"""

import os
import sys
import time
import psutil
import logging
from pathlib import Path

def find_processes_using_file(file_path):
    """查找正在使用指定文件的进程"""
    processes = []
    
    try:
        file_path = Path(file_path).resolve()
        
        for proc in psutil.process_iter(['pid', 'name', 'open_files']):
            try:
                # 获取进程打开的文件
                open_files = proc.info.get('open_files', [])
                for file_info in open_files:
                    if file_info.path == str(file_path):
                        processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'path': file_info.path
                        })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
                
    except Exception as e:
        print(f"错误: 无法检查文件占用: {e}")
    
    return processes

def check_log_file_locks(log_dir="logs"):
    """检查日志文件占用情况"""
    print("=== 检查日志文件占用情况 ===")
    
    if not os.path.exists(log_dir):
        print(f"日志目录不存在: {log_dir}")
        return
    
    # 检查所有日志文件
    log_files = []
    for file in os.listdir(log_dir):
        if file.endswith('.log'):
            log_files.append(os.path.join(log_dir, file))
    
    if not log_files:
        print("未找到日志文件")
        return
    
    total_locked = 0
    
    for log_file in log_files:
        print(f"\n检查文件: {log_file}")
        
        if not os.path.exists(log_file):
            print("  文件不存在")
            continue
        
        # 检查文件是否被占用
        processes = find_processes_using_file(log_file)
        
        if processes:
            total_locked += 1
            print(f"  ❌ 文件被占用，占用进程:")
            for proc in processes:
                print(f"    - PID: {proc['pid']}, 进程: {proc['name']}")
        else:
            print(f"  ✅ 文件未被占用")
    
    print(f"\n=== 检查结果 ===")
    print(f"总文件数: {len(log_files)}")
    print(f"被占用文件数: {total_locked}")
    
    if total_locked > 0:
        print(f"⚠️  发现 {total_locked} 个文件被占用")
        return True
    else:
        print("✅ 所有日志文件都未被占用")
        return False

def force_close_log_handlers():
    """强制关闭日志处理器"""
    print("\n=== 尝试强制关闭日志处理器 ===")
    
    # 获取根日志记录器
    root_logger = logging.getLogger()
    
    # 查找并关闭文件处理器
    handlers_to_remove = []
    
    for handler in root_logger.handlers:
        if hasattr(handler, 'stream') and handler.stream:
            try:
                print(f"关闭日志处理器: {type(handler).__name__}")
                handler.stream.close()
                handler.stream = None
                handlers_to_remove.append(handler)
            except Exception as e:
                print(f"关闭处理器失败: {e}")
    
    # 移除已关闭的处理器
    for handler in handlers_to_remove:
        try:
            root_logger.removeHandler(handler)
            print(f"已移除处理器: {type(handler).__name__}")
        except Exception as e:
            print(f"移除处理器失败: {e}")

def restart_logging_system():
    """重启日志系统"""
    print("\n=== 重启日志系统 ===")
    
    try:
        # 强制关闭所有日志处理器
        force_close_log_handlers()
        
        # 等待一段时间让文件句柄完全释放
        print("等待文件句柄释放...")
        time.sleep(2)
        
        # 重新配置日志系统
        from config.log_config import LogConfig
        from utils.safe_log_handler import create_safe_file_handler
        
        # 创建新的文件处理器
        file_handler = create_safe_file_handler(
            log_dir=LogConfig.LOG_DIR,
            filename="app.log",
            handler_type="timed",
            when='midnight',
            interval=1,
            backupCount=LogConfig.ROTATION_BACKUP_COUNT,
            encoding='utf-8',
            delay=True
        )
        
        if file_handler:
            # 配置根日志记录器
            root_logger = logging.getLogger()
            root_logger.addHandler(file_handler)
            
            # 设置格式
            from config.log_config import LogConfig
            file_config = LogConfig.get_file_format_config()
            formatter = logging.Formatter(
                file_config['format'],
                datefmt=file_config['datefmt']
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(getattr(logging, file_config['level']))
            
            print("✅ 日志系统重启成功")
            return True
        else:
            print("❌ 无法创建新的日志处理器")
            return False
            
    except Exception as e:
        print(f"❌ 重启日志系统失败: {e}")
        return False

def main():
    """主函数"""
    print("日志文件占用检测和解决工具")
    print("=" * 50)
    
    # 检查日志文件占用情况
    has_locks = check_log_file_locks()
    
    if has_locks:
        print("\n发现日志文件被占用，是否尝试解决？")
        response = input("输入 'y' 继续，其他键退出: ")
        
        if response.lower() == 'y':
            # 尝试重启日志系统
            if restart_logging_system():
                print("\n再次检查文件占用情况...")
                time.sleep(1)
                check_log_file_locks()
            else:
                print("无法解决文件占用问题，请手动检查")
        else:
            print("用户取消操作")
    else:
        print("\n日志文件状态正常")

if __name__ == "__main__":
    main() 
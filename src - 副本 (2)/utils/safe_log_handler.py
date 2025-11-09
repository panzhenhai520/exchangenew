#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
安全的日志处理器
专门处理Windows文件占用问题
"""

import os
import time
import logging
from logging.handlers import TimedRotatingFileHandler
from typing import Optional

class SafeTimedRotatingFileHandler(TimedRotatingFileHandler):
    """安全的定时轮转文件处理器，避免Windows文件占用问题"""
    
    def __init__(self, filename, when='h', interval=1, backupCount=0, encoding=None, delay=False, utc=False, atTime=None):
        super().__init__(filename, when, interval, backupCount, encoding, delay, utc, atTime)
        self._last_rollover_time = 0
        self._rollover_retry_count = 0
        self._max_retry_count = 3
    
    def doRollover(self):
        """重写轮转方法，增加错误处理和重试机制"""
        try:
            # 检查是否需要轮转
            current_time = int(time.time())
            if current_time - self._last_rollover_time < 60:  # 避免频繁轮转
                return
            
            self._last_rollover_time = current_time
            
            # 关闭当前文件句柄
            if self.stream:
                self.stream.close()
                self.stream = None
            
            # 执行轮转逻辑
            super().doRollover()
            
            # 重置重试计数
            self._rollover_retry_count = 0
            
        except PermissionError as e:
            # 文件被占用，尝试重试
            self._rollover_retry_count += 1
            if self._rollover_retry_count <= self._max_retry_count:
                print(f"警告: 日志轮转失败 (文件被占用)，将在5秒后重试 ({self._rollover_retry_count}/{self._max_retry_count}): {e}")
                time.sleep(5)
                # 递归调用，但限制重试次数
                if self._rollover_retry_count < self._max_retry_count:
                    self.doRollover()
            else:
                print(f"错误: 日志轮转失败，已达到最大重试次数: {e}")
                # 尝试重新打开日志文件
                self._reopen_log_file()
                
        except Exception as e:
            print(f"警告: 日志轮转过程中出现错误: {e}")
            # 尝试重新打开日志文件
            self._reopen_log_file()
    
    def _reopen_log_file(self):
        """重新打开日志文件"""
        try:
            if not self.stream:
                self.stream = open(self.baseFilename, 'a', encoding=self.encoding)
                print(f"已重新打开日志文件: {self.baseFilename}")
        except Exception as e:
            print(f"警告: 无法重新打开日志文件: {e}")
    
    def emit(self, record):
        """重写emit方法，增加错误处理"""
        try:
            super().emit(record)
        except Exception as e:
            # 如果写入失败，尝试重新打开文件
            print(f"警告: 写入日志失败: {e}")
            try:
                if self.stream:
                    self.stream.close()
                    self.stream = None
                self._reopen_log_file()
                # 重新尝试写入
                super().emit(record)
            except Exception as retry_error:
                print(f"错误: 重新写入日志失败: {retry_error}")

class SafeRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """安全的大小轮转文件处理器"""
    
    def __init__(self, filename, maxBytes=0, backupCount=0, encoding=None, delay=False):
        super().__init__(filename, maxBytes, backupCount, encoding, delay)
        self._last_rollover_time = 0
    
    def doRollover(self):
        """重写轮转方法，增加错误处理"""
        try:
            # 检查是否需要轮转
            current_time = int(time.time())
            if current_time - self._last_rollover_time < 60:  # 避免频繁轮转
                return
            
            self._last_rollover_time = current_time
            
            # 关闭当前文件句柄
            if self.stream:
                self.stream.close()
                self.stream = None
            
            # 执行轮转逻辑
            super().doRollover()
            
        except PermissionError as e:
            print(f"警告: 日志轮转失败 (文件被占用): {e}")
            # 尝试重新打开日志文件
            self._reopen_log_file()
            
        except Exception as e:
            print(f"警告: 日志轮转过程中出现错误: {e}")
            self._reopen_log_file()
    
    def _reopen_log_file(self):
        """重新打开日志文件"""
        try:
            if not self.stream:
                self.stream = open(self.baseFilename, 'a', encoding=self.encoding)
                print(f"已重新打开日志文件: {self.baseFilename}")
        except Exception as e:
            print(f"警告: 无法重新打开日志文件: {e}")
    
    def emit(self, record):
        """重写emit方法，增加错误处理"""
        try:
            super().emit(record)
        except Exception as e:
            print(f"警告: 写入日志失败: {e}")
            try:
                if self.stream:
                    self.stream.close()
                    self.stream = None
                self._reopen_log_file()
                super().emit(record)
            except Exception as retry_error:
                print(f"错误: 重新写入日志失败: {retry_error}")

def create_safe_file_handler(log_dir: str, filename: str = "app.log", 
                           handler_type: str = "timed", **kwargs) -> Optional[logging.Handler]:
    """
    创建安全的文件处理器
    
    Args:
        log_dir: 日志目录
        filename: 日志文件名
        handler_type: 处理器类型 ("timed" 或 "rotating")
        **kwargs: 其他参数
    
    Returns:
        日志处理器实例，如果创建失败则返回None
    """
    try:
        # 确保日志目录存在
        os.makedirs(log_dir, exist_ok=True)
        
        file_path = os.path.join(log_dir, filename)
        
        if handler_type == "timed":
            # 创建定时轮转处理器
            handler = SafeTimedRotatingFileHandler(
                filename=file_path,
                when=kwargs.get('when', 'midnight'),
                interval=kwargs.get('interval', 1),
                backupCount=kwargs.get('backupCount', 5),
                encoding=kwargs.get('encoding', 'utf-8'),
                delay=kwargs.get('delay', True)
            )
            handler.suffix = kwargs.get('suffix', "%Y-%m-%d")
            
        elif handler_type == "rotating":
            # 创建大小轮转处理器
            handler = SafeRotatingFileHandler(
                filename=file_path,
                maxBytes=kwargs.get('maxBytes', 10 * 1024 * 1024),  # 10MB
                backupCount=kwargs.get('backupCount', 5),
                encoding=kwargs.get('encoding', 'utf-8'),
                delay=kwargs.get('delay', True)
            )
            
        else:
            raise ValueError(f"不支持的处理器类型: {handler_type}")
        
        return handler
        
    except Exception as e:
        print(f"警告: 无法创建安全的日志文件处理器: {e}")
        return None 
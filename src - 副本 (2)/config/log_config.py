#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ExchangeOK 日志配置
集中管理日志轮转、清理等参数
"""

import os
from datetime import timedelta
import logging

class LogConfig:
    """日志配置类"""
    
    # 日志目录
    LOG_DIR = "logs"
    ARCHIVE_DIR = "archive"
    
    # 日志轮转配置
    ROTATION_MAX_SIZE_MB = 10  # 单个日志文件最大大小（MB）
    ROTATION_BACKUP_COUNT = 5  # 保留的轮转文件数量
    
    # 日志清理配置
    CLEANUP_OLD_DAYS = 30      # 清理N天前的日志文件
    CLEANUP_LARGE_SIZE_MB = 100 # 清理超过N MB的日志文件
    COMPRESS_OLD_DAYS = 7      # 压缩N天前的日志文件
    
    # 日志级别 - 调试模式优化
    LOG_LEVEL = "DEBUG"
    CONSOLE_LOG_LEVEL = "INFO"    # 控制台显示信息及以上级别
    FILE_LOG_LEVEL = "DEBUG"      # 文件记录所有详细信息
    
    # 日志格式 - 简化控制台输出
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    CONSOLE_LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'  # 控制台简化格式
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    # 清理任务配置
    CLEANUP_SCHEDULE = {
        'enabled': True,
        'interval_hours': 24,  # 每24小时运行一次清理
        'keep_cleanup_logs_days': 7  # 保留清理日志7天
    }
    
    # 静默第三方库日志 - 调试模式下保留更多信息
    QUIET_LOGGERS = [
        'urllib3.connectionpool',
        'requests.packages.urllib3.connectionpool',
        'werkzeug',  # 静默werkzeug日志
        'sqlalchemy.engine',
        'sqlalchemy.pool'
    ]
    
    # 系统模块日志配置
    SYSTEM_MODULES = {
        'app_auth': 'AUTH',
        'app_exchange': 'EXCHANGE', 
        'app_rates': 'RATES',
        'app_dashboard': 'DASHBOARD',
        'app_balance': 'BALANCE',
        'app_end_of_day': 'EOD',
        'app_user_management': 'USER',
        'app_branches': 'BRANCH'
    }
    
    @classmethod
    def get_log_dir(cls) -> str:
        """获取日志目录的绝对路径"""
        return os.path.abspath(cls.LOG_DIR)
    
    @classmethod
    def get_archive_dir(cls) -> str:
        """获取归档目录的绝对路径"""
        return os.path.abspath(cls.ARCHIVE_DIR)
    
    @classmethod
    def ensure_directories(cls):
        """确保日志和归档目录存在"""
        os.makedirs(cls.LOG_DIR, exist_ok=True)
        os.makedirs(cls.ARCHIVE_DIR, exist_ok=True)
    
    @classmethod
    def get_rotation_config(cls) -> dict:
        """获取日志轮转配置"""
        return {
            'maxBytes': cls.ROTATION_MAX_SIZE_MB * 1024 * 1024,
            'backupCount': cls.ROTATION_BACKUP_COUNT,
            'encoding': 'utf-8'
        }
    
    @classmethod
    def get_cleanup_config(cls) -> dict:
        """获取日志清理配置"""
        return {
            'old_days': cls.CLEANUP_OLD_DAYS,
            'large_size_mb': cls.CLEANUP_LARGE_SIZE_MB,
            'compress_days': cls.COMPRESS_OLD_DAYS
        }
    
    @classmethod
    def get_format_config(cls) -> dict:
        """获取日志格式配置"""
        return {
            'format': cls.LOG_FORMAT,
            'datefmt': cls.LOG_DATE_FORMAT,
            'level': cls.LOG_LEVEL
        }

    @classmethod
    def setup_quiet_logging(cls):
        """设置静默第三方库日志"""
        for logger_name in cls.QUIET_LOGGERS:
            if logger_name.startswith('#'):
                continue  # 跳过被注释的日志器
            logging.getLogger(logger_name).setLevel(logging.WARNING)

    @classmethod
    def enable_debug_mode(cls):
        """启用调试模式 - 设置更详细的日志级别"""
        cls.LOG_LEVEL = "DEBUG"
        cls.CONSOLE_LOG_LEVEL = "INFO"
        cls.FILE_LOG_LEVEL = "DEBUG"
        print("Debug mode enabled - Log level set to DEBUG")
    
    @classmethod
    def enable_production_mode(cls):
        """启用生产模式 - 设置标准日志级别"""
        cls.LOG_LEVEL = "INFO"
        cls.CONSOLE_LOG_LEVEL = "WARNING"
        cls.FILE_LOG_LEVEL = "INFO"
        print("Production mode enabled - Log level set to INFO")
    
    @classmethod
    def get_console_format_config(cls) -> dict:
        """获取控制台日志格式配置"""
        return {
            'format': cls.CONSOLE_LOG_FORMAT,
            'datefmt': cls.LOG_DATE_FORMAT,
            'level': cls.CONSOLE_LOG_LEVEL
        }

    @classmethod
    def get_file_format_config(cls) -> dict:
        """获取文件日志格式配置"""
        return {
            'format': cls.LOG_FORMAT,
            'datefmt': cls.LOG_DATE_FORMAT,
            'level': cls.FILE_LOG_LEVEL
        }

# 预设配置模板
class LogPresets:
    """日志预设配置"""
    
    # 开发环境配置
    DEVELOPMENT = {
        'rotation_max_size_mb': 5,
        'rotation_backup_count': 3,
        'cleanup_old_days': 7,
        'log_level': 'DEBUG'
    }
    
    # 生产环境配置
    PRODUCTION = {
        'rotation_max_size_mb': 50,
        'rotation_backup_count': 10,
        'cleanup_old_days': 90,
        'log_level': 'INFO'
    }
    
    # 测试环境配置
    TESTING = {
        'rotation_max_size_mb': 1,
        'rotation_backup_count': 2,
        'cleanup_old_days': 1,
        'log_level': 'WARNING'
    }
    
    @classmethod
    def apply_preset(cls, preset_name: str):
        """应用预设配置"""
        presets = {
            'development': cls.DEVELOPMENT,
            'production': cls.PRODUCTION,
            'testing': cls.TESTING
        }
        
        if preset_name.lower() not in presets:
            raise ValueError(f"未知的预设配置: {preset_name}")
        
        preset = presets[preset_name.lower()]
        
        # 更新LogConfig的值
        for key, value in preset.items():
            attr_name = key.upper()
            if hasattr(LogConfig, attr_name):
                setattr(LogConfig, attr_name, value)

# 环境变量配置覆盖
def load_config_from_env():
    """从环境变量加载配置"""
    env_mappings = {
        'EXCHANGEOK_LOG_LEVEL': 'LOG_LEVEL',
        'EXCHANGEOK_LOG_MAX_SIZE_MB': 'ROTATION_MAX_SIZE_MB',
        'EXCHANGEOK_LOG_BACKUP_COUNT': 'ROTATION_BACKUP_COUNT',
        'EXCHANGEOK_LOG_CLEANUP_DAYS': 'CLEANUP_OLD_DAYS'
    }
    
    for env_var, config_attr in env_mappings.items():
        env_value = os.getenv(env_var)
        if env_value:
            try:
                # 尝试转换为适当的类型
                if config_attr in ['ROTATION_MAX_SIZE_MB', 'ROTATION_BACKUP_COUNT', 'CLEANUP_OLD_DAYS']:
                    env_value = int(env_value)
                setattr(LogConfig, config_attr, env_value)
            except ValueError:
                print(f"警告: 环境变量 {env_var} 的值 '{env_value}' 无效，使用默认值")

# 初始化时加载环境变量配置
load_config_from_env() 
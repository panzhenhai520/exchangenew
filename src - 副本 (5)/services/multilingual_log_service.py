#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
多语言日志记录服务
支持中文、英文、泰文三种语言的系统日志记录
"""

import logging
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
from services.db_service import DatabaseService
from models.exchange_models import SystemLog

# 配置日志记录器
logger = logging.getLogger(__name__)

class MultilingualLogService:
    """多语言日志服务类"""
    
    # 语言映射
    LANGUAGE_MAP = {
        'zh': 'zh-CN',
        'en': 'en-US', 
        'th': 'th-TH',
        'zh-CN': 'zh-CN',
        'en-US': 'en-US',
        'th-TH': 'th-TH'
    }
    
    # 缓存语言包
    _language_cache = {}
    
    def __init__(self, default_language: str = 'zh-CN'):
        """
        初始化多语言日志服务
        
        Args:
            default_language: 默认语言代码
        """
        self.default_language = default_language
        self._load_language_files()
    
    def _load_language_files(self):
        """加载所有语言包文件"""
        locales_dir = os.path.join(os.path.dirname(__file__), '..', 'locales')
        
        for lang_code in self.LANGUAGE_MAP.values():
            lang_file = os.path.join(locales_dir, f'{lang_code}.json')
            if os.path.exists(lang_file):
                try:
                    with open(lang_file, 'r', encoding='utf-8') as f:
                        self._language_cache[lang_code] = json.load(f)
                except Exception as e:
                    logger.error(f"Failed to load language file {lang_file}: {e}")
    
    def _get_translation(self, key: str, language: str = None) -> str:
        """
        获取指定语言的翻译文本
        
        Args:
            key: 翻译键，支持点号分隔的嵌套键如 'system_logs.user_login'
            language: 语言代码
            
        Returns:
            翻译后的文本，如果找不到则返回原键
        """
        if not language:
            language = self.default_language
        
        # 标准化语言代码
        language = self.LANGUAGE_MAP.get(language, language)
        
        # 获取语言包
        lang_data = self._language_cache.get(language, {})
        
        # 解析嵌套键
        keys = key.split('.')
        current = lang_data
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                # 如果找不到翻译，返回原键
                return key
        
        return current if isinstance(current, str) else key
    
    def log_system_operation(self, 
                           operation_key: str,
                           operator_id: Optional[int] = None,
                           branch_id: Optional[int] = None,
                           details: Optional[str] = None,
                           ip_address: Optional[str] = None,
                           language: Optional[str] = None,
                           **kwargs) -> bool:
        """
        记录系统操作日志（多语言）
        
        Args:
            operation_key: 操作键，如 'user_login', 'exchange_transaction'
            operator_id: 操作员ID
            branch_id: 分支ID
            details: 详细信息
            ip_address: IP地址
            language: 语言代码
            **kwargs: 额外参数，用于格式化消息
            
        Returns:
            是否记录成功
        """
        try:
            # 获取操作名称的翻译
            operation_name = self._get_translation(f'system_logs.{operation_key}', language)
            
            # 构建日志消息
            log_message = operation_name
            if details:
                log_message += f" - {details}"
            
            # 格式化额外参数
            if kwargs:
                for key, value in kwargs.items():
                    log_message += f" | {key}: {value}"
            
            # 记录到文件日志
            logger.info(f"[{operation_name}] 操作员: {operator_id}, 分支: {branch_id}, 详情: {details}")
            
            # 记录到数据库
            return self._save_to_database(
                operation=operation_key,
                operator_id=operator_id,
                branch_id=branch_id,
                details=log_message,
                ip_address=ip_address,
                language=language or self.default_language
            )
            
        except Exception as e:
            logger.error(f"Failed to log system operation {operation_key}: {e}")
            return False
    
    def _save_to_database(self, 
                         operation: str,
                         operator_id: Optional[int] = None,
                         branch_id: Optional[int] = None,
                         details: Optional[str] = None,
                         ip_address: Optional[str] = None,
                         language: str = 'zh-CN') -> bool:
        """
        保存日志到数据库
        
        Returns:
            是否保存成功
        """
        session = DatabaseService.get_session()
        try:
            system_log = SystemLog(
                operation=operation,
                operator_id=operator_id,
                branch_id=branch_id,
                details=details,
                ip_address=ip_address,
                language=language,
                created_at=datetime.now()
            )
            session.add(system_log)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save log to database: {e}")
            return False
        finally:
            DatabaseService.close_session(session)
    
    # 便捷方法：主要功能模块的日志记录
    def log_user_login(self, user_id: int, username: str, branch_id: int, 
                      ip_address: str = None, language: str = None):
        """记录用户登录日志"""
        return self.log_system_operation(
            'user_login',
            operator_id=user_id,
            branch_id=branch_id,
            details=f"用户 {username} 登录系统",
            ip_address=ip_address,
            language=language,
            username=username
        )
    
    def log_user_logout(self, user_id: int, username: str, branch_id: int,
                       ip_address: str = None, language: str = None):
        """记录用户退出日志"""
        return self.log_system_operation(
            'user_logout',
            operator_id=user_id,
            branch_id=branch_id,
            details=f"用户 {username} 退出系统",
            ip_address=ip_address,
            language=language,
            username=username
        )
    
    def log_exchange_transaction(self, operator_id: int, branch_id: int,
                               currency_code: str, amount: float, 
                               transaction_type: str, customer_name: str,
                               ip_address: str = None, language: str = None):
        """记录外币兑换交易日志"""
        return self.log_system_operation(
            'exchange_transaction',
            operator_id=operator_id,
            branch_id=branch_id,
            details=f"{transaction_type} {currency_code} {amount} 客户: {customer_name}",
            ip_address=ip_address,
            language=language,
            currency=currency_code,
            amount=amount,
            transaction_type=transaction_type,
            customer=customer_name
        )
    
    def log_rate_update(self, operator_id: int, branch_id: int,
                       currency_code: str, buy_rate: float, sell_rate: float,
                       ip_address: str = None, language: str = None):
        """记录汇率更新日志"""
        return self.log_system_operation(
            'rate_update',
            operator_id=operator_id,
            branch_id=branch_id,
            details=f"更新 {currency_code} 汇率: 买入 {buy_rate}, 卖出 {sell_rate}",
            ip_address=ip_address,
            language=language,
            currency=currency_code,
            buy_rate=buy_rate,
            sell_rate=sell_rate
        )
    
    def log_balance_adjust(self, operator_id: int, branch_id: int,
                          currency_code: str, amount: float, reason: str,
                          ip_address: str = None, language: str = None):
        """记录余额调整日志"""
        return self.log_system_operation(
            'balance_adjust',
            operator_id=operator_id,
            branch_id=branch_id,
            details=f"调整 {currency_code} 余额: {amount}, 原因: {reason}",
            ip_address=ip_address,
            language=language,
            currency=currency_code,
            amount=amount,
            reason=reason
        )
    
    def log_end_of_day(self, operator_id: int, branch_id: int,
                      summary: str, ip_address: str = None, language: str = None):
        """记录日结操作日志"""
        return self.log_system_operation(
            'end_of_day',
            operator_id=operator_id,
            branch_id=branch_id,
            details=f"执行日结操作: {summary}",
            ip_address=ip_address,
            language=language,
            summary=summary
        )
    
    def log_unauthorized_access(self, user_id: int = None, action: str = "",
                              ip_address: str = None, language: str = None):
        """记录未授权访问日志"""
        return self.log_system_operation(
            'unauthorized_access',
            operator_id=user_id,
            details=f"未授权访问尝试: {action}",
            ip_address=ip_address,
            language=language,
            action=action
        )

# 创建全局实例
multilingual_logger = MultilingualLogService()

# 便捷函数
def log_operation(operation_key: str, **kwargs):
    """便捷的日志记录函数"""
    return multilingual_logger.log_system_operation(operation_key, **kwargs) 
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
        # 从i18n模块目录加载翻译文件
        i18n_dir = os.path.join(os.path.dirname(__file__), '..', 'i18n', 'modules')
        
        # 加载logs模块的翻译文件
        for lang_code in self.LANGUAGE_MAP.values():
            lang_file = os.path.join(i18n_dir, 'logs', f'{lang_code}.js')
            if os.path.exists(lang_file):
                try:
                    with open(lang_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # 简单的JS对象解析，移除export default和分号
                        content = content.replace('export default', '').replace(';', '').strip()
                        # 解析JSON格式的JavaScript对象
                        import re
                        # 提取对象内容
                        match = re.search(r'\{.*\}', content, re.DOTALL)
                        if match:
                            # 将JavaScript对象转换为JSON格式
                            json_content = match.group(0)
                            # 处理JavaScript的字符串格式
                            json_content = re.sub(r'(\w+):', r'"\1":', json_content)
                            self._language_cache[lang_code] = json.loads(json_content)
                except Exception as e:
                    logger.error(f"Failed to load language file {lang_file}: {e}")
                    # 如果加载失败，使用默认翻译
                    self._language_cache[lang_code] = {
                        'system_logs': {
                            'rate_update': 'Rate Update' if lang_code == 'en-US' else '汇率更新' if lang_code == 'zh-CN' else 'อัปเดตอัตราแลกเปลี่ยน',
                            'user_login': 'User Login' if lang_code == 'en-US' else '用户登录' if lang_code == 'zh-CN' else 'เข้าสู่ระบบ',
                            'user_logout': 'User Logout' if lang_code == 'en-US' else '用户退出' if lang_code == 'zh-CN' else 'ออกจากระบบ'
                        }
                    }
    
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
                log_type='system',  # 添加必需的log_type字段
                action=details or operation,  # 添加必需的action字段
                details=details,
                ip_address=ip_address,
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
            language=language
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
            language=language
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
            language=language
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
            language=language
        )
    
    def log_income_query(self, operator_id: int, branch_id: int,
                        query_type: str, date_range: str = None,
                        ip_address: str = None, language: str = None):
        """记录动态收入查询日志"""
        details = f"查询类型: {query_type}"
        if date_range:
            details += f", 日期范围: {date_range}"
        
        return self.log_system_operation(
            'income_query',
            operator_id=operator_id,
            branch_id=branch_id,
            details=details,
            ip_address=ip_address,
            language=language
        )
    
    def log_foreign_stock_query(self, operator_id: int, branch_id: int,
                               currency_codes: list = None, include_warnings: bool = False,
                               ip_address: str = None, language: str = None):
        """记录库存外币查询日志"""
        details = "查询库存外币余额"
        if currency_codes:
            details += f", 币种: {', '.join(currency_codes)}"
        if include_warnings:
            details += ", 包含低库存预警"
            
        return self.log_system_operation(
            'foreign_stock_query',
            operator_id=operator_id,
            branch_id=branch_id,
            details=details,
            ip_address=ip_address,
            language=language
        )
    
    # Web服务和API日志记录方法
    def log_api_request(self, operator_id: int, branch_id: int,
                       api_endpoint: str, method: str, status_code: int,
                       response_time: float = None, user_agent: str = None,
                       ip_address: str = None, language: str = None):
        """记录API请求日志"""
        details = f"API请求: {method} {api_endpoint}, 状态码: {status_code}"
        if response_time:
            details += f", 响应时间: {response_time:.2f}ms"
        if user_agent:
            details += f", 用户代理: {user_agent[:100]}"  # 限制长度
        
        return self.log_system_operation(
            'api_request',
            operator_id=operator_id,
            branch_id=branch_id,
            details=details,
            ip_address=ip_address,
            language=language
        )
    
    def log_web_page_access(self, operator_id: int, branch_id: int,
                           page_url: str, page_title: str = None,
                           session_duration: int = None,
                           ip_address: str = None, language: str = None):
        """记录网页访问日志"""
        details = f"页面访问: {page_url}"
        if page_title:
            details += f", 页面标题: {page_title}"
        if session_duration:
            details += f", 会话时长: {session_duration}秒"
        
        return self.log_system_operation(
            'page_access',
            operator_id=operator_id,
            branch_id=branch_id,
            details=details,
            ip_address=ip_address,
            language=language
        )
    
    def log_security_event(self, operator_id: int, branch_id: int,
                          event_type: str, risk_level: str,
                          description: str, attempted_action: str = None,
                          ip_address: str = None, language: str = None):
        """记录安全事件日志"""
        details = f"安全事件: {event_type}, 风险级别: {risk_level}, 描述: {description}"
        if attempted_action:
            details += f", 尝试操作: {attempted_action}"
        
        return self.log_system_operation(
            'security_event',
            operator_id=operator_id,
            branch_id=branch_id,
            details=details,
            ip_address=ip_address,
            language=language
        )
    
    def log_business_process(self, operator_id: int, branch_id: int,
                           process_name: str, step: str, status: str,
                           duration: float = None, error_message: str = None,
                           ip_address: str = None, language: str = None):
        """记录业务流程日志"""
        details = f"业务流程: {process_name}, 步骤: {step}, 状态: {status}"
        if duration:
            details += f", 耗时: {duration:.2f}秒"
        if error_message and status == "失败":
            details += f", 错误: {error_message}"
        
        return self.log_system_operation(
            'business_process',
            operator_id=operator_id,
            branch_id=branch_id,
            details=details,
            ip_address=ip_address,
            language=language
        )

# 创建全局实例
multilingual_logger = MultilingualLogService()

# 便捷函数
def log_operation(operation_key: str, **kwargs):
    """便捷的日志记录函数"""
    return multilingual_logger.log_system_operation(operation_key, **kwargs) 
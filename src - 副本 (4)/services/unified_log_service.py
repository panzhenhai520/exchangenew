#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统一日志记录服务
自动分类写入操作日志、系统日志、用户活动日志三种类型
支持多语言翻译
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
from services.db_service import DatabaseService
from models.exchange_models import SystemLog, OperatorActivityLog

# 配置日志记录器
logger = logging.getLogger(__name__)

class UnifiedLogService:
    """统一日志记录服务 - 自动分类到操作日志、系统日志、用户活动日志"""
    
    # 日志分类映射 - 定义哪些操作写入哪些日志
    LOG_CATEGORY_MAP = {
        # 操作日志 - 业务操作相关
        'operation': {
            'exchange_transaction',      # 兑换交易
            'reversal_transaction',      # 交易冲正
            'balance_adjustment',        # 余额调节
            'balance_initialization',    # 余额初始化
            'threshold_update',          # 币种阈值修改
            'rate_update',              # 汇率更新
            'transaction_print',        # 交易凭证打印
        },
        
        # 系统日志 - 系统管理相关
        'system': {
            'business_data_cleanup',    # 清空营业数据
            'eod_operation',           # 日结操作
            'user_management',         # 用户管理
            'role_configuration',      # 角色配置
            'branch_management',       # 网点管理
            'system_configuration',    # 系统配置
            'data_import_export',      # 数据导入导出
        },
        
        # 用户活动日志 - 用户行为相关
        'activity': {
            'user_login',              # 用户登录
            'user_logout',             # 用户登出
            'page_access',             # 页面访问
            'api_request',             # API请求
            'session_activity',        # 会话活动
        }
    }
    
    @staticmethod
    def write_log(log_category: str, 
                  operation_key: str,
                  operator_id: Optional[int] = None,
                  branch_id: Optional[int] = None,
                  details: Optional[str] = None,
                  ip_address: Optional[str] = None,
                  user_agent: Optional[str] = None,
                  session_id: Optional[str] = None,
                  language: str = 'zh-CN',  # 添加语言参数
                  **kwargs) -> bool:
        """
        统一日志写入方法
        
        Args:
            log_category: 日志类别 ('operation', 'system', 'activity')
            operation_key: 操作键名
            operator_id: 操作员ID
            branch_id: 网点ID
            details: 自定义详细信息
            ip_address: IP地址
            user_agent: 用户代理
            session_id: 会话ID
            language: 语言设置 ('zh-CN', 'en-US', 'th-TH')
            **kwargs: 其他参数
            
        Returns:
            bool: 是否成功
        """
        try:
            # 生成操作描述文本（支持多语言）
            action_text = details or UnifiedLogService._build_action_text(operation_key, language, **kwargs)
            
            logger.info(f"[{log_category.upper()}] {operation_key}: {action_text} - Operator: {operator_id}, Branch: {branch_id}")
            
            # 写入相应的日志表
            success = True
            
            # 根据日志类别和操作键决定写入哪些表
            # 检查operation_key是否属于指定的日志类别
            operation_keys = UnifiedLogService.LOG_CATEGORY_MAP.get(log_category, set())
            
            if operation_key in operation_keys or log_category == 'system':
                # 写入系统日志表
                success &= UnifiedLogService._write_system_log(
                    log_category, operation_key, operator_id, branch_id, action_text, ip_address, **kwargs
                )
            
            if log_category == 'activity' or operation_key in UnifiedLogService.LOG_CATEGORY_MAP.get('activity', set()):
                # 写入用户活动日志表
                success &= UnifiedLogService._write_activity_log(
                    operation_key, operator_id, branch_id, action_text, ip_address, user_agent, session_id, **kwargs
                )
            
            return success
            
        except Exception as e:
            logger.error(f"统一日志记录失败: {str(e)}")
            return False
    
    @staticmethod
    def _write_system_log(log_category: str,
                         operation_key: str,
                         operator_id: Optional[int],
                         branch_id: Optional[int],
                         action_text: str,
                         ip_address: Optional[str],
                         **kwargs) -> bool:
        """写入系统日志"""
        try:
            session = DatabaseService.get_session()
            
            # 创建系统日志记录
            log_entry = SystemLog(
                operation=operation_key,
                operator_id=operator_id,
                log_type=log_category,
                action=action_text,
                details=action_text,
                ip_address=ip_address,
                created_at=datetime.now()
            )
            
            session.add(log_entry)
            session.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to write system log: {str(e)}")
            if session:
                session.rollback()
            return False
        finally:
            if session:
                DatabaseService.close_session(session)
    
    @staticmethod
    def _write_activity_log(operation_key: str,
                           operator_id: Optional[int],
                           branch_id: Optional[int],
                           action_text: str,
                           ip_address: Optional[str],
                           user_agent: Optional[str],
                           session_id: Optional[str],
                           **kwargs) -> bool:
        """写入用户活动日志"""
        try:
            session = DatabaseService.get_session()
            
            # 创建用户活动日志记录
            log_entry = OperatorActivityLog(
                operator_id=operator_id,
                branch_id=branch_id,
                activity_type=operation_key,
                activity_description=action_text,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                created_at=datetime.now()
            )
            
            session.add(log_entry)
            session.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to write activity log: {str(e)}")
            if session:
                session.rollback()
            return False
        finally:
            if session:
                DatabaseService.close_session(session)
    
    @staticmethod
    def _build_action_text(operation_key: str, language: str = 'zh-CN', **kwargs) -> str:
        """构建操作描述文本 - 支持多语言"""
        
        # 多语言操作名称定义
        operation_names = {
            'zh-CN': {
                'exchange_transaction': '外币兑换',
                'reversal_transaction': '交易冲正',
                'balance_adjustment': '余额调节',
                'balance_initialization': '余额初始化',
                'user_login': '用户登录',
                'user_logout': '用户退出',
                'user_management': '用户管理',
                'role_configuration': '角色配置',
                'threshold_update': '阈值更新',
                'eod_operation': '日结操作',
                'business_data_cleanup': '清空营业数据'
            },
            'en-US': {
                'exchange_transaction': 'Currency Exchange',
                'reversal_transaction': 'Transaction Reversal',
                'balance_adjustment': 'Balance Adjustment',
                'balance_initialization': 'Balance Initialization',
                'user_login': 'User Login',
                'user_logout': 'User Logout',
                'user_management': 'User Management',
                'role_configuration': 'Role Configuration',
                'threshold_update': 'Threshold Update',
                'eod_operation': 'End of Day Operation',
                'business_data_cleanup': 'Business Data Cleanup'
            },
            'th-TH': {
                'exchange_transaction': 'การแลกเปลี่ยนเงินตรา',
                'reversal_transaction': 'การยกเลิกธุรกรรม',
                'balance_adjustment': 'การปรับยอดเงิน',
                'balance_initialization': 'การตั้งค่ายอดเงินเริ่มต้น',
                'user_login': 'การเข้าสู่ระบบ',
                'user_logout': 'การออกจากระบบ',
                'user_management': 'การจัดการผู้ใช้',
                'role_configuration': 'การกำหนดบทบาท',
                'threshold_update': 'การอัพเดตเกณฑ์',
                'eod_operation': 'การดำเนินการปิดวัน',
                'business_data_cleanup': 'การล้างข้อมูลธุรกิจ'
            }
        }
        
        # 获取当前语言的操作名称，如果没有则使用中文
        lang_operation_names = operation_names.get(language, operation_names['zh-CN'])
        base_text = lang_operation_names.get(operation_key, operation_key)
        
        # 多语言文本定义
        text_translations = {
            'zh-CN': {
                'customer': '客户',
                'document_no': '单据号',
                'original_doc_no': '冲正原单据号',
                'reversal_doc_no': '冲正单据号',
                'reason': '原因',
                'init_amount': '初始化金额',
                'user': '用户',
                'operation_id': '操作ID',
                'from_to': '从 {} 变更为 {}',
                'currency': '币种',
                'date': '日期',
                'eod_id': '日结ID',
                'create_user': '创建用户',
                'update_user': '修改用户',
                'delete_user': '删除用户',
                'activate_user': '激活用户',
                'deactivate_user': '停用用户',
                'actions': {
                    'create': '新增',
                    'update': '修改',
                    'delete': '删除',
                    'start': '开始',
                    'complete': '完成',
                    'cancel': '取消',
                    'rollback': '回滚',
                    'delete_completed': '删除已完成',
                    'cash_out': '交款'
                }
            },
            'en-US': {
                'customer': 'Customer',
                'document_no': 'Document No',
                'original_doc_no': 'Original Doc No',
                'reversal_doc_no': 'Reversal Doc No',
                'reason': 'Reason',
                'init_amount': 'Initial Amount',
                'user': 'User',
                'operation_id': 'Operation ID',
                'from_to': 'Changed from {} to {}',
                'currency': 'Currency',
                'date': 'Date',
                'eod_id': 'EOD ID',
                'create_user': 'Create User',
                'update_user': 'Update User',
                'delete_user': 'Delete User',
                'activate_user': 'Activate User',
                'deactivate_user': 'Deactivate User',
                'actions': {
                    'create': 'Create',
                    'update': 'Update',
                    'delete': 'Delete',
                    'start': 'Start',
                    'complete': 'Complete',
                    'cancel': 'Cancel',
                    'rollback': 'Rollback',
                    'delete_completed': 'Delete Completed',
                    'cash_out': 'Cash Out'
                }
            },
            'th-TH': {
                'customer': 'ลูกค้า',
                'document_no': 'เลขที่เอกสาร',
                'original_doc_no': 'เลขที่เอกสารเดิม',
                'reversal_doc_no': 'เลขที่เอกสารยกเลิก',
                'reason': 'เหตุผล',
                'init_amount': 'ยอดเงินเริ่มต้น',
                'user': 'ผู้ใช้',
                'operation_id': 'รหัสการดำเนินการ',
                'from_to': 'เปลี่ยนจาก {} เป็น {}',
                'currency': 'สกุลเงิน',
                'date': 'วันที่',
                'eod_id': 'รหัสปิดวัน',
                'create_user': 'สร้างผู้ใช้',
                'update_user': 'อัปเดตผู้ใช้',
                'delete_user': 'ลบผู้ใช้',
                'activate_user': 'เปิดใช้งานผู้ใช้',
                'deactivate_user': 'ปิดใช้งานผู้ใช้',
                'actions': {
                    'create': 'สร้าง',
                    'update': 'อัปเดต',
                    'delete': 'ลบ',
                    'start': 'เริ่ม',
                    'complete': 'เสร็จสิ้น',
                    'cancel': 'ยกเลิก',
                    'rollback': 'ย้อนกลับ',
                    'delete_completed': 'ลบที่เสร็จสิ้น',
                    'cash_out': 'ส่งมอบเงิน'
                }
            }
        }
        
        # 获取当前语言的文本翻译
        lang_texts = text_translations.get(language, text_translations['zh-CN'])
        
        # 根据不同操作类型添加详细信息
        if operation_key == 'exchange_transaction':
            currency_code = kwargs.get('currency_code', '')
            amount = kwargs.get('amount', '')
            transaction_type = kwargs.get('transaction_type', '')
            customer_name = kwargs.get('customer_name', '')
            transaction_no = kwargs.get('transaction_no', '')
            if currency_code and amount:
                desc = f"{base_text} - {transaction_type} {amount} {currency_code} {lang_texts['customer']}: {customer_name}"
                if transaction_no:
                    desc += f" {lang_texts['document_no']}: {transaction_no}"
                return desc
        
        elif operation_key == 'reversal_transaction':
            original_transaction_no = kwargs.get('original_transaction_no', '')
            currency_code = kwargs.get('currency_code', '')
            amount = kwargs.get('amount', '')
            reversal_transaction_no = kwargs.get('reversal_transaction_no', '')
            if original_transaction_no:
                desc = f"{base_text} - {lang_texts['original_doc_no']}: {original_transaction_no} {amount} {currency_code}"
                if reversal_transaction_no:
                    desc += f" {lang_texts['reversal_doc_no']}: {reversal_transaction_no}"
                return desc
        
        elif operation_key == 'balance_adjustment':
            currency_code = kwargs.get('currency_code', '')
            adjustment_type = kwargs.get('adjustment_type', '')
            amount = kwargs.get('amount', '')
            reason = kwargs.get('reason', '')
            adjustment_no = kwargs.get('adjustment_no', '')
            if currency_code and amount:
                desc = f"{base_text} - {adjustment_type} {currency_code} {amount} {lang_texts['reason']}: {reason}"
                if adjustment_no:
                    desc += f" {lang_texts['document_no']}: {adjustment_no}"
                return desc
        
        elif operation_key == 'balance_initialization':
            currency_code = kwargs.get('currency_code', '')
            amount = kwargs.get('amount', '')
            initialization_no = kwargs.get('initialization_no', '')
            if currency_code and amount:
                desc = f"{base_text} - {currency_code} {lang_texts['init_amount']}: {amount}"
                if initialization_no:
                    desc += f" {lang_texts['document_no']}: {initialization_no}"
                return desc
        
        elif operation_key == 'user_login':
            username = kwargs.get('username', '')
            if username:
                return f"{base_text} - {lang_texts['user']}: {username}"
        
        elif operation_key == 'user_management':
            action_type = kwargs.get('action_type', '')  # 'create', 'update', 'delete'
            target_user = kwargs.get('target_user', '')
            operation_id = kwargs.get('operation_id', '')
            if action_type and target_user:
                # 根据操作类型获取对应的翻译
                if action_type == 'create':
                    action_text = lang_texts.get('create_user', 'Create User')
                elif action_type == 'update':
                    action_text = lang_texts.get('update_user', 'Update User')
                elif action_type == 'delete':
                    action_text = lang_texts.get('delete_user', 'Delete User')
                elif action_type == 'activate':
                    action_text = lang_texts.get('activate_user', 'Activate User')
                elif action_type == 'deactivate':
                    action_text = lang_texts.get('deactivate_user', 'Deactivate User')
                else:
                    action_text = lang_texts['actions'].get(action_type, action_type)
                
                desc = f"{action_text}: {target_user}"
                if operation_id:
                    desc += f" {lang_texts['operation_id']}: {operation_id}"
                return desc
        
        elif operation_key == 'role_configuration':
            target_user = kwargs.get('target_user', '')
            old_role = kwargs.get('old_role', '')
            new_role = kwargs.get('new_role', '')
            operation_id = kwargs.get('operation_id', '')
            if target_user and new_role:
                desc = f"{base_text} - {lang_texts['user']}: {target_user} {lang_texts['from_to'].format(old_role, new_role)}"
                if operation_id:
                    desc += f" {lang_texts['operation_id']}: {operation_id}"
                return desc
        
        elif operation_key == 'threshold_update':
            currency_code = kwargs.get('currency_code', '')
            operation_id = kwargs.get('operation_id', '')
            if currency_code:
                desc = f"{base_text} - {lang_texts['currency']}: {currency_code}"
                if operation_id:
                    desc += f" {lang_texts['operation_id']}: {operation_id}"
                return desc
        
        elif operation_key == 'eod_operation':
            eod_action = kwargs.get('eod_action', '')  # 'start', 'complete', 'cancel', 'delete_completed', 'cash_out'
            eod_date = kwargs.get('eod_date', '')
            eod_id = kwargs.get('eod_id', '')
            if eod_action and eod_date:
                action_name = lang_texts['actions'].get(eod_action, eod_action)
                desc = f"{base_text} - {action_name} {lang_texts['date']}: {eod_date}"
                if eod_id:
                    desc += f" {lang_texts['eod_id']}: {eod_id}"
                
                # 如果是交款操作，添加详细信息
                if eod_action == 'cash_out':
                    cash_out_details = kwargs.get('cash_out_details', {})
                    if cash_out_details:
                        operator_name = cash_out_details.get('cash_out_operator_name', '')
                        receiver_name = cash_out_details.get('cash_receiver_name', '')
                        cash_out_time = cash_out_details.get('cash_out_time', '')
                        total_currencies = cash_out_details.get('total_currencies', 0)
                        
                        if language == 'zh-CN':
                            desc += f", 交款时间: {cash_out_time}, 交款人: {operator_name}, 收款人: {receiver_name}, 币种数: {total_currencies}"
                        elif language == 'en-US':
                            desc += f", Cash Out Time: {cash_out_time}, Cash Out Operator: {operator_name}, Receiver: {receiver_name}, Currencies: {total_currencies}"
                        else:  # th-TH
                            desc += f", เวลาส่งมอบ: {cash_out_time}, ผู้ส่งมอบ: {operator_name}, ผู้รับเงิน: {receiver_name}, สกุลเงิน: {total_currencies}"
                        
                        # 添加币种明细
                        currency_details = cash_out_details.get('currency_details', [])
                        if currency_details:
                            currency_info = []
                            for curr in currency_details:
                                currency_info.append(f"{curr.get('currency_code', '')}: {curr.get('cash_out_amount', 0)}")
                            if language == 'zh-CN':
                                desc += f", 明细: {', '.join(currency_info)}"
                            elif language == 'en-US':
                                desc += f", Details: {', '.join(currency_info)}"
                            else:  # th-TH
                                desc += f", รายละเอียด: {', '.join(currency_info)}"
                
                # 如果是日结完成操作，添加详细信息
                elif eod_action == 'complete':
                    completion_details = kwargs.get('completion_details', {})
                    if completion_details:
                        completion_time = completion_details.get('completion_time', '')
                        cash_out_type = completion_details.get('cash_out_type', '')
                        cash_receiver_name = completion_details.get('cash_receiver_name', '')
                        balance_snapshot_table = completion_details.get('balance_snapshot_table', '')
                        
                        if language == 'zh-CN':
                            desc += f", 完成时间: {completion_time}, 交款类型: {cash_out_type}, 收款人: {cash_receiver_name}, 余额快照表: {balance_snapshot_table}"
                        elif language == 'en-US':
                            desc += f", Completion Time: {completion_time}, Cash Out Type: {cash_out_type}, Receiver: {cash_receiver_name}, Balance Snapshot Table: {balance_snapshot_table}"
                        else:  # th-TH
                            desc += f", เวลาเสร็จสิ้น: {completion_time}, ประเภทการส่งมอบ: {cash_out_type}, ผู้รับเงิน: {cash_receiver_name}, ตารางสแนปช็อตยอดคงเหลือ: {balance_snapshot_table}"
                
                return desc

        # 如果没有特殊处理，返回基础文本加上所有参数
        if kwargs:
            param_str = " | ".join([f"{k}: {v}" for k, v in kwargs.items() if v])
            return f"{base_text} - {param_str}"
        
        return base_text

# 便捷函数：快速记录不同类型的日志
def log_operation(operation_key: str, language: str = 'zh-CN', **kwargs) -> bool:
    """记录操作日志"""
    return UnifiedLogService.write_log('operation', operation_key, language=language, **kwargs)

def log_system(operation_key: str, language: str = 'zh-CN', **kwargs) -> bool:
    """记录系统日志"""
    return UnifiedLogService.write_log('system', operation_key, language=language, **kwargs)

def log_activity(operation_key: str, language: str = 'zh-CN', **kwargs) -> bool:
    """记录用户活动日志"""
    return UnifiedLogService.write_log('activity', operation_key, language=language, **kwargs)

# 具体业务日志记录函数
def log_exchange_transaction(operator_id: int, branch_id: int, currency_code: str, 
                           amount: float, transaction_type: str, customer_name: str,
                           transaction_no: str = None, rate: float = None,
                           ip_address: str = None, language: str = 'zh-CN', **kwargs) -> bool:
    """记录兑换交易日志"""
    return UnifiedLogService.write_log(
        'operation', 'exchange_transaction',
        operator_id=operator_id,
        branch_id=branch_id,
        ip_address=ip_address,
        language=language,
        currency_code=currency_code,
        amount=amount,
        transaction_type=transaction_type,
        customer_name=customer_name,
        transaction_no=transaction_no,
        rate=rate,
        **kwargs
    )

def log_reversal_transaction(operator_id: int, branch_id: int, original_transaction_no: str,
                           currency_code: str, amount: float, rate: float,
                           reversal_transaction_no: str = None,
                           ip_address: str = None, language: str = 'zh-CN', **kwargs) -> bool:
    """记录冲正交易日志"""
    return UnifiedLogService.write_log(
        'operation', 'reversal_transaction',
        operator_id=operator_id,
        branch_id=branch_id,
        ip_address=ip_address,
        language=language,
        original_transaction_no=original_transaction_no,
        currency_code=currency_code,
        amount=amount,
        rate=rate,
        reversal_transaction_no=reversal_transaction_no,
        **kwargs
    )

def log_balance_adjustment(operator_id: int, branch_id: int, currency_code: str,
                         adjustment_type: str, amount: float, reason: str,
                         balance_before: float = None, balance_after: float = None,
                         ip_address: str = None, language: str = 'zh-CN', **kwargs) -> bool:
    """记录余额调节日志"""
    return UnifiedLogService.write_log(
        'operation', 'balance_adjustment',
        operator_id=operator_id,
        branch_id=branch_id,
        ip_address=ip_address,
        language=language,
        currency_code=currency_code,
        adjustment_type=adjustment_type,
        amount=amount,
        reason=reason,
        balance_before=balance_before,
        balance_after=balance_after,
        **kwargs
    )

def log_balance_initialization(operator_id: int, branch_id: int, currency_code: str,
                             amount: float, ip_address: str = None, language: str = 'zh-CN', **kwargs) -> bool:
    """记录余额初始化日志"""
    return UnifiedLogService.write_log(
        'operation', 'balance_initialization',
        operator_id=operator_id,
        branch_id=branch_id,
        ip_address=ip_address,
        language=language,
        currency_code=currency_code,
        amount=amount,
        **kwargs
    )

def log_user_login(operator_id: int, branch_id: int, username: str,
                  ip_address: str = None, user_agent: str = None,
                  session_id: str = None, language: str = 'zh-CN', **kwargs) -> bool:
    """记录用户登录日志"""
    return UnifiedLogService.write_log(
        'activity', 'user_login',
        operator_id=operator_id,
        branch_id=branch_id,
        ip_address=ip_address,
        user_agent=user_agent,
        session_id=session_id,
        language=language,
        username=username,
        **kwargs
    )

def log_user_logout(operator_id: int, branch_id: int, username: str,
                   ip_address: str = None, user_agent: str = None,
                   session_id: str = None, language: str = 'zh-CN', **kwargs) -> bool:
    """记录用户退出日志"""
    return UnifiedLogService.write_log(
        'activity', 'user_logout',
        operator_id=operator_id,
        branch_id=branch_id,
        ip_address=ip_address,
        user_agent=user_agent,
        session_id=session_id,
        language=language,
        username=username,
        **kwargs
    )

def log_user_management(operator_id: int, branch_id: int, action_type: str,
                       target_user: str, target_role: str = None,
                       ip_address: str = None, language: str = 'zh-CN', **kwargs) -> bool:
    """记录用户管理日志"""
    return UnifiedLogService.write_log(
        'system', 'user_management',
        operator_id=operator_id,
        branch_id=branch_id,
        ip_address=ip_address,
        language=language,
        action_type=action_type,
        target_user=target_user,
        target_role=target_role,
        **kwargs
    )

def log_role_configuration(operator_id: int, branch_id: int, target_user: str,
                         old_role: str, new_role: str,
                         ip_address: str = None, language: str = 'zh-CN', **kwargs) -> bool:
    """记录角色配置日志"""
    return UnifiedLogService.write_log(
        'system', 'role_configuration',
        operator_id=operator_id,
        branch_id=branch_id,
        ip_address=ip_address,
        language=language,
        target_user=target_user,
        old_role=old_role,
        new_role=new_role,
        **kwargs
    )

def log_threshold_update(operator_id: int, branch_id: int, currency_code: str,
                        min_threshold: float = None, max_threshold: float = None,
                        ip_address: str = None, language: str = 'zh-CN', **kwargs) -> bool:
    """记录币种阈值修改日志"""
    return UnifiedLogService.write_log(
        'operation', 'threshold_update',
        operator_id=operator_id,
        branch_id=branch_id,
        ip_address=ip_address,
        language=language,
        currency_code=currency_code,
        min_threshold=min_threshold,
        max_threshold=max_threshold,
        **kwargs
    )

def log_business_data_cleanup(operator_id: int, branch_id: int, cleanup_description: str,
                            ip_address: str = None, language: str = 'zh-CN', **kwargs) -> bool:
    """记录清空营业数据日志"""
    return UnifiedLogService.write_log(
        'system', 'business_data_cleanup',
        operator_id=operator_id,
        branch_id=branch_id,
        ip_address=ip_address,
        language=language,
        details=cleanup_description,
        **kwargs
    )

def log_eod_operation(operator_id: int, branch_id: int, eod_action: str,
                     eod_date: str, ip_address: str = None, language: str = 'zh-CN', **kwargs) -> bool:
    """记录日结操作日志"""
    return UnifiedLogService.write_log(
        'system', 'eod_operation',
        operator_id=operator_id,
        branch_id=branch_id,
        ip_address=ip_address,
        language=language,
        eod_action=eod_action,
        eod_date=eod_date,
        **kwargs
    )

def log_currency_threshold_change(operator_id: int, branch_id: int, currency_code: str,
                                min_threshold: float = None, max_threshold: float = None,
                                ip_address: str = None, language: str = 'zh-CN', **kwargs) -> bool:
    """记录货币阈值修改日志 - 与log_threshold_update功能相同"""
    return log_threshold_update(
        operator_id=operator_id,
        branch_id=branch_id,
        currency_code=currency_code,
        min_threshold=min_threshold,
        max_threshold=max_threshold,
        ip_address=ip_address,
        language=language,
        **kwargs
    ) 
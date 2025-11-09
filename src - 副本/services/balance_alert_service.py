"""
余额报警服务
处理余额状态检查、报警通知和阈值管理
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional, List
from enum import Enum

from services.db_service import DatabaseService
from models.exchange_models import (
    BranchBalanceAlert, CurrencyBalance, Currency, 
    Branch, SystemLog, Operator
)

logger = logging.getLogger(__name__)

class BalanceStatus(Enum):
    """余额状态枚举"""
    CRITICAL_LOW = 'critical_low'      # 严重不足：低于最低阈值
    WARNING_LOW = 'warning_low'        # 警告不足：接近最低阈值
    NORMAL = 'normal'                  # 正常范围
    WARNING_HIGH = 'warning_high'      # 警告过多：接近最高阈值
    CRITICAL_HIGH = 'critical_high'    # 严重过多：高于最高阈值

class BalanceAlertService:
    """余额报警服务类"""
    
    # 预警百分比：当余额接近阈值的这个百分比时触发预警
    WARNING_PERCENTAGE = Decimal('0.1')  # 10%
    
    @staticmethod
    def check_balance_status(currency_id: int, current_balance: Decimal, branch_id: int) -> Dict[str, Any]:
        """
        检查余额状态
        
        Args:
            currency_id: 币种ID
            current_balance: 当前余额
            branch_id: 网点ID
            
        Returns:
            包含状态信息的字典
        """
        try:
            session = DatabaseService.get_session()
            try:
                # 获取报警设置
                alert_setting = session.query(BranchBalanceAlert).filter(
                    BranchBalanceAlert.branch_id == branch_id,
                    BranchBalanceAlert.currency_id == currency_id,
                    BranchBalanceAlert.is_active == True
                ).first()
                
                if not alert_setting:
                    return {
                        'status': BalanceStatus.NORMAL.value,
                        'message': '正常',
                        'level': 'normal',
                        'icon': 'check-circle',
                        'color': 'success'
                    }
                
                # 获取币种信息
                currency = session.query(Currency).filter(Currency.id == currency_id).first()
                currency_code = currency.currency_code if currency else 'UNKNOWN'
                
                # 检查余额状态
                status_info = BalanceAlertService._calculate_balance_status(
                    current_balance, 
                    alert_setting.min_threshold, 
                    alert_setting.max_threshold,
                    currency_code
                )
                
                return status_info
                
            finally:
                DatabaseService.close_session(session)
                
        except Exception as e:
            logger.error(f"检查余额状态失败: {e}")
            return {
                'status': BalanceStatus.NORMAL.value,
                'message': '状态检查失败',
                'level': 'error',
                'icon': 'exclamation-triangle',
                'color': 'danger'
            }
    
    @staticmethod
    def _calculate_balance_status(balance: Decimal, min_threshold: Optional[Decimal], 
                                max_threshold: Optional[Decimal], currency_code: str) -> Dict[str, Any]:
        """计算余额状态"""
        
        # 如果没有设置阈值，返回正常状态
        if min_threshold is None and max_threshold is None:
            return {
                'status': BalanceStatus.NORMAL.value,
                'message': '正常',
                'level': 'normal',
                'icon': 'check-circle',
                'color': 'success'
            }
        
        # 检查最低阈值
        if min_threshold is not None:
            if balance < min_threshold:
                return {
                    'status': BalanceStatus.CRITICAL_LOW.value,
                    'message': 'balance_insufficient_below_min_threshold',
                    'message_params': {
                        'currency_code': currency_code,
                        'threshold': float(min_threshold)
                    },
                    'level': 'critical',
                    'icon': 'exclamation-triangle',
                    'color': 'danger',
                    'threshold_type': 'min',
                    'threshold_value': float(min_threshold)
                }
            
            # 检查是否接近最低阈值（阈值+10%范围内）
            warning_threshold = min_threshold * (1 + BalanceAlertService.WARNING_PERCENTAGE)
            if balance <= warning_threshold:
                return {
                    'status': BalanceStatus.WARNING_LOW.value,
                    'message': 'balance_low_near_min_threshold',
                    'message_params': {
                        'currency_code': currency_code,
                        'threshold': float(min_threshold)
                    },
                    'level': 'warning',
                    'icon': 'exclamation-circle',
                    'color': 'warning',
                    'threshold_type': 'min',
                    'threshold_value': float(min_threshold)
                }
        
        # 检查最高阈值
        if max_threshold is not None:
            if balance > max_threshold:
                return {
                    'status': BalanceStatus.CRITICAL_HIGH.value,
                    'message': 'balance_excessive_above_max_threshold',
                    'message_params': {
                        'currency_code': currency_code,
                        'threshold': float(max_threshold)
                    },
                    'level': 'critical',
                    'icon': 'exclamation-triangle',
                    'color': 'primary',
                    'threshold_type': 'max',
                    'threshold_value': float(max_threshold)
                }
            
            # 检查是否接近最高阈值（阈值-10%范围内）
            warning_threshold = max_threshold * (1 - BalanceAlertService.WARNING_PERCENTAGE)
            if balance >= warning_threshold:
                return {
                    'status': BalanceStatus.WARNING_HIGH.value,
                    'message': 'balance_high_near_max_threshold',
                    'message_params': {
                        'currency_code': currency_code,
                        'threshold': float(max_threshold)
                    },
                    'level': 'warning',
                    'icon': 'info-circle',
                    'color': 'info',
                    'threshold_type': 'max',
                    'threshold_value': float(max_threshold)
                }
        
        # 正常范围
        return {
            'status': BalanceStatus.NORMAL.value,
            'message': '正常',
            'level': 'normal',
            'icon': 'check-circle',
            'color': 'success'
        }
    
    @staticmethod
    def get_balance_alert_info(currency_id: int, branch_id: int) -> Dict[str, Any]:
        """
        获取余额报警信息
        
        Args:
            currency_id: 币种ID
            branch_id: 网点ID
            
        Returns:
            包含余额和报警信息的字典
        """
        try:
            session = DatabaseService.get_session()
            try:
                # 获取当前余额
                balance_record = session.query(CurrencyBalance).filter(
                    CurrencyBalance.branch_id == branch_id,
                    CurrencyBalance.currency_id == currency_id
                ).first()
                
                current_balance = Decimal(str(balance_record.balance)) if balance_record and balance_record.balance else Decimal('0')
                
                # 获取报警设置
                alert_setting = session.query(BranchBalanceAlert).filter(
                    BranchBalanceAlert.branch_id == branch_id,
                    BranchBalanceAlert.currency_id == currency_id,
                    BranchBalanceAlert.is_active == True
                ).first()
                
                # 获取币种信息
                currency = session.query(Currency).filter(Currency.id == currency_id).first()
                
                # 检查余额状态
                alert_status = BalanceAlertService.check_balance_status(currency_id, current_balance, branch_id)
                
                return {
                    'current_balance': float(current_balance),
                    'currency_info': {
                        'id': currency.id,
                        'code': currency.currency_code,
                        'name': currency.currency_name
                    } if currency else None,
                    'alert_status': alert_status,
                    'threshold_info': {
                        'min_threshold': float(alert_setting.min_threshold) if alert_setting and alert_setting.min_threshold else None,
                        'max_threshold': float(alert_setting.max_threshold) if alert_setting and alert_setting.max_threshold else None,
                        'is_active': alert_setting.is_active if alert_setting else False
                    } if alert_setting else None,
                    'last_updated': balance_record.updated_at.isoformat() if balance_record and balance_record.updated_at else None
                }
                
            finally:
                DatabaseService.close_session(session)
                
        except Exception as e:
            logger.error(f"获取余额报警信息失败: {e}")
            raise
    
    @staticmethod
    def create_alert_notification(currency_id: int, branch_id: int, operator_id: int, 
                                alert_type: str, message: str) -> bool:
        """
        创建报警通知
        
        Args:
            currency_id: 币种ID
            branch_id: 网点ID
            operator_id: 操作员ID
            alert_type: 报警类型
            message: 报警消息
            
        Returns:
            是否创建成功
        """
        try:
            session = DatabaseService.get_session()
            try:
                # 记录系统日志
                log_entry = SystemLog(
                    operation='余额报警',
                    operator_id=operator_id,
                    log_type='balance_alert',
                    action=f'余额报警触发: {alert_type}',
                    details=f'币种ID: {currency_id}, 网点ID: {branch_id}, 消息: {message}'
                )
                session.add(log_entry)
                DatabaseService.commit_session(session)
                
                return True
                
            except Exception as e:
                DatabaseService.rollback_session(session)
                raise e
            finally:
                DatabaseService.close_session(session)
                
        except Exception as e:
            logger.error(f"创建报警通知失败: {e}")
            return False
    
    @staticmethod
    def get_all_balance_alerts(branch_id: int) -> List[Dict[str, Any]]:
        """
        获取网点所有币种的余额报警状态
        
        Args:
            branch_id: 网点ID
            
        Returns:
            余额报警状态列表
        """
        try:
            session = DatabaseService.get_session()
            try:
                # 获取网点所有币种余额
                balances = session.query(CurrencyBalance, Currency).join(
                    Currency, CurrencyBalance.currency_id == Currency.id
                ).filter(
                    CurrencyBalance.branch_id == branch_id
                ).all()
                
                alert_list = []
                for balance, currency in balances:
                    current_balance = Decimal(str(balance.balance)) if balance.balance else Decimal('0')
                    alert_info = BalanceAlertService.get_balance_alert_info(currency.id, branch_id)
                    alert_list.append(alert_info)
                
                return alert_list
                
            finally:
                DatabaseService.close_session(session)
                
        except Exception as e:
            logger.error(f"获取所有余额报警状态失败: {e}")
            return []
    
    @staticmethod
    def check_transaction_impact(currency_id: int, branch_id: int, transaction_amount: Decimal, 
                               transaction_type: str) -> Dict[str, Any]:
        """
        检查交易对余额的影响
        
        Args:
            currency_id: 币种ID
            branch_id: 网点ID
            transaction_amount: 交易金额
            transaction_type: 交易类型 ('buy' 或 'sell')
            
        Returns:
            交易影响分析
        """
        try:
            # 获取当前余额信息
            alert_info = BalanceAlertService.get_balance_alert_info(currency_id, branch_id)
            current_balance = Decimal(str(alert_info['current_balance']))
            
            # 计算交易后余额
            if transaction_type == 'buy':
                # 买入外币，外币余额增加
                new_balance = current_balance + transaction_amount
            else:
                # 卖出外币，外币余额减少
                new_balance = current_balance - transaction_amount
            
            # 检查新余额状态
            new_status = BalanceAlertService.check_balance_status(currency_id, new_balance, branch_id)
            
            return {
                'current_balance': float(current_balance),
                'transaction_amount': float(transaction_amount),
                'transaction_type': transaction_type,
                'new_balance': float(new_balance),
                'current_status': alert_info['alert_status'],
                'new_status': new_status,
                'will_trigger_alert': new_status['level'] in ['warning', 'critical'],
                'impact_analysis': BalanceAlertService._analyze_impact(
                    alert_info['alert_status'], new_status
                )
            }
            
        except Exception as e:
            logger.error(f"检查交易影响失败: {e}")
            return {
                'error': str(e),
                'will_trigger_alert': False
            }
    
    @staticmethod
    def _analyze_impact(current_status: Dict, new_status: Dict) -> str:
        """分析交易影响"""
        current_level = current_status.get('level', 'normal')
        new_level = new_status.get('level', 'normal')
        
        if current_level == 'normal' and new_level in ['warning', 'critical']:
            return '交易后将触发余额报警'
        elif current_level in ['warning', 'critical'] and new_level == 'normal':
            return '交易后余额将恢复正常'
        elif current_level == 'warning' and new_level == 'critical':
            return '交易后余额报警将升级'
        elif current_level == 'critical' and new_level == 'warning':
            return '交易后余额报警将降级'
        else:
            return '交易对余额状态无显著影响' 